"""Node-key fusion audit: how many grounding spans the `<doc>::<local id>` key has overwritten.

Task `cc_tasks/2026-10-04_node_key_fusion_audit.md`. Measures; changes nothing on the log, the
graph or the record.

DD-020 keys every non-Document node on `<doc_id>::<item_id>`, and `build_projection.py` writes
each `node_asserted` with `MERGE (n:<label> {key}) SET n += props`. The extractor assigns item
ids per chunk, so two chunks of one document that both say `def_1` (or two runs over one
document that were not superseded) land on one node, and the later assertion's grounding span
replaces the earlier one. This script replays the log with the projection's own filters and
reports every span that was replaced.

    python scripts/audit_node_key_fusion.py           write the CSV and the generated block
    python scripts/audit_node_key_fusion.py --check   recompute in memory; exit 1 on drift

The CSV is owned whole by this script. The audit markdown is hand-written around ONE block
between the markers below, and only that block is owned here, so `--check` compares the CSV
byte for byte and the block byte for byte.

Fusion unit. The projection merges on (label, key), not on key alone: a Claim and a Concept
sharing `<doc>::c_1` are two nodes. So an assertion is overwritten only by a later assertion
with the same label AND key. Keys shared across labels are counted apart; they are not span
loss.

Row unit. One CSV row per distinct (normalised span, normalised identity text) pair among a
group's non-surviving assertions. The survivor is the last projected assertion, which is what
`SET n += props` leaves on the node for the span and identity attributes. Every shard:line
that carried the pair is listed on the row.

Classes (task decision 2), by script:
  benign_duplicate         the overwritten span equals the survivor's after `grounding.normalize`
  same_term_lost_evidence  different span; the identity text (IDENTITY_ATTRIBUTE) is equal after
                           `grounding.normalize` and casefold
  collision                different span and different identity text under one id: a wrong
                           node, not a lost span
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import yaml  # noqa: E402

from kg import eventlog  # noqa: E402
from kg.extraction import grounding  # noqa: E402
import build_projection as bp  # noqa: E402

OUT_DIR = REPO / "docs" / "research"
OUT_CSV = OUT_DIR / "2026-10-04_node_key_fusion_audit.csv"
OUT_MD = OUT_DIR / "2026-10-04_node_key_fusion_audit.md"
KG_QUESTIONS = REPO / "docs" / "evidence" / "kg_questions.yaml"
GLOSSARY_CSV = REPO / "docs" / "research" / "2026-10-02_commerce_guidance_glossary_terms.csv"
#: The Definition count the task file cites, quoted from
#: `cc_tasks/2026-10-02_kg_research_questions_RESULT.md` §1 (epoch of 265 documents, before the
#: Commerce admission). A RESULT is prose, so the figure is transcribed here, with its source.
CITED_PRE_COMMERCE_DEFINITIONS = 1975
#: The one document the commerce admission's two-pipelines figure (48/49) is about.
COMMERCE_DOC = "generative-ai-and-open-data-guidelines-and-best-practices-de"

BEGIN = "<!-- BEGIN GENERATED: scripts/audit_node_key_fusion.py -->"
END = "<!-- END GENERATED: scripts/audit_node_key_fusion.py -->"

#: The attribute that says WHAT a node is, per label: "same term or claim text" in task
#: decision 2. Read from `kg/schema.yaml`'s property lists: Definition carries `term`, Claim
#: `claim_text`, Measure and Practice `text`; every other label is a named entity (`name`).
IDENTITY_ATTRIBUTE = {"Definition": "term", "Claim": "claim_text", "Measure": "text",
                      "Practice": "text"}
IDENTITY_DEFAULT = "name"

#: Task decision 1: "both spans' first 80 characters".
PREVIEW_CHARS = 80

CLASSES = ("benign_duplicate", "same_term_lost_evidence", "collision")
#: Where the overwritten assertion came from relative to the survivor. A run is
#: (shard, purpose, model, prompt version): chunk-qualified keys separate the second origin and
#: not the third.
ORIGINS = ("same_chunk", "other_chunk_same_run", "other_run")

#: A local id that is a short prefix and a counter (`d1`, `cl4`, `c_3`, `def-12`): an id the
#: extractor numbers per chunk rather than derives from the item's text, so two chunks of one
#: document mint it independently. Descriptive only; no class depends on it.
POSITIONAL_ID = re.compile(r"[a-z]{1,4}[-_]?\d+")

CSV_FIELDS = ("key", "label", "doc_id", "class", "origin", "positional_id",
              "survivor_shard_line", "survivor_chunk", "survivor_run",
              "overwritten_shard_lines", "overwritten_chunks", "overwritten_runs",
              "identity_contained", "relocation_overlay",
              "survivor_span_80", "overwritten_span_80",
              "survivor_identity", "overwritten_identity")


# ------------------------------------------------------------------------------- helpers

def norm(text) -> str:
    return grounding.normalize(text or "")


def identity_norm(text) -> str:
    return norm(text).casefold()


def preview(text) -> str:
    return norm(text)[:PREVIEW_CHARS]


def span_of(item: dict) -> str:
    """The node's grounding span. Instrument carries `grounding_spans`, a list (schema)."""
    span = item.get("grounding_span")
    if span is None and isinstance(item.get("grounding_spans"), list):
        span = " | ".join(str(s) for s in item["grounding_spans"])
    return span if isinstance(span, str) else ("" if span is None else str(span))


def identity_of(label: str, item: dict) -> str:
    v = item.get(IDENTITY_ATTRIBUTE.get(label, IDENTITY_DEFAULT))
    return v if isinstance(v, str) else ("" if v is None else str(v))


def projected_assertions() -> tuple[list[dict], list[dict], Counter]:
    """Every `node_asserted` the projection writes, in the projection's order, with its
    shard and line. The filters are `build_projection.build`'s own, called, not re-written:
    `is_projectable`, then the whole-extraction and stratum supersession, then the label
    whitelist. `replay()` gives no line numbers, so the shards are read here in the order
    `eventlog.shards()` returns, which is the order `replay()` reads them."""
    superseded, _aliases = bp.read_overlays()
    quarantined = bp.quarantined_batches()
    bulk = bp.bulk_purposes()
    schema = bp._load_schema()
    kg_labels, edge_types = set(schema["node_types"]), set(schema["edge_types"])
    old_instr: dict[tuple, set] = {}
    out, edges, stats = [], [], Counter()
    for shard in eventlog.shards():
        with shard.open(encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line or ('"node_asserted"' not in line
                                 and '"edge_asserted"' not in line):
                    continue
                ev = json.loads(line)
                et = ev.get("event_type")
                if et not in ("node_asserted", "edge_asserted"):
                    continue
                stats[et] += 1
                if not bp.is_projectable(ev, quarantined, bulk):
                    stats["skipped_non_graph" if et == "node_asserted" else "edge_skipped"] += 1
                    continue
                prov = ev.get("provenance") or {}
                skey = (ev.get("doc_id"), prov.get("source_sha256"))
                if skey in superseded:
                    strata = superseded[skey]
                    if strata is None:
                        stats["skipped_superseded" if et == "node_asserted"
                              else "edge_skipped"] += 1
                        continue
                    if et == "node_asserted" and (ev.get("payload") or {}).get("type") == "Instrument":
                        old_instr.setdefault(skey, set()).add(ev["payload"].get("id"))
                    if bp.stratum_superseded(ev, strata, old_instr.get(skey, set())):
                        stats["skipped_superseded" if et == "node_asserted"
                              else "edge_skipped"] += 1
                        continue
                p = ev.get("payload") or {}
                if et == "edge_asserted":
                    # Only the endpoints matter here: an edge whose local endpoint id names a
                    # node that a later chunk's different item took over is attached to it.
                    if p.get("type") in edge_types:
                        edges.append({"doc_id": ev.get("doc_id"), "type": p.get("type"),
                                      "chunk": ev.get("chunk_id") or prov.get("chunk_id") or "",
                                      "ends": (p.get("from_id"), p.get("to_id")),
                                      "where": f"{shard.name}:{lineno}"})
                        stats["edge_projected"] += 1
                    continue
                label = p.get("type")
                if label not in kg_labels:
                    stats["skipped_label"] += 1
                    continue
                item = p.get("item") or {}
                out.append({
                    "key": bp.node_key(ev.get("doc_id"), p["id"]),
                    "label": label, "doc_id": ev.get("doc_id"), "item": item,
                    "where": f"{shard.name}:{lineno}",
                    "chunk": ev.get("chunk_id") or prov.get("chunk_id") or "",
                    "run": "|".join(str(x) for x in (shard.name, ev.get("purpose") or "-",
                                                     prov.get("model_id") or "-",
                                                     prov.get("prompt_version") or "-")),
                    "span": span_of(item), "identity": identity_of(label, item),
                })
                stats["projected"] += 1
    return out, edges, stats


def overlays() -> dict[str, list[dict]]:
    """The projection's repair overlays by node key, in the order `build` applies them: the
    `grounding_relocated` and `attribute_nulled` events of the untagged log in replay order,
    then the `attribute_restored` events of the restoration shard when its class is accepted.
    They are keyed `<doc>::<item>` and applied after every assertion, so one written against
    an earlier assertion lands on the survivor."""
    out = defaultdict(list)
    accepted = set()
    for ev in eventlog.replay():
        et = ev.get("event_type")
        if et == "grounding_relocated":
            out[bp.node_key(ev["doc_id"], ev["item_id"])].append(
                {"op": "relocate", "label": ev.get("label"), "span": ev["new_span"],
                 "old": ev.get("old_span")})
        elif et == "attribute_nulled" and ev.get("attribute") in bp.NULLABLE_ATTRIBUTES:
            out[bp.node_key(ev["doc_id"], ev["item_id"])].append(
                {"op": "null", "attr": ev["attribute"]})
        elif et == "restoration_class_accepted":
            accepted.add(ev.get("restoration_class"))
    if "restoration_v2" in accepted:
        for ev in eventlog.replay(tag="restoration_v2"):
            if (ev.get("event_type") == "attribute_restored"
                    and ev.get("attribute") in bp.NULLABLE_ATTRIBUTES):
                out[bp.node_key(ev["doc_id"], ev["item_id"])].append(
                    {"op": "restore", "attr": ev["attribute"], "value": ev.get("value")})
    return out


def apply_overlays(props: dict, label: str, ops: list[dict]) -> dict:
    out = dict(props)
    for o in ops:
        if o["op"] == "relocate" and o["label"] in (None, label):
            out["grounding_span"] = o["span"]
        elif o["op"] == "null":
            out[o["attr"]] = None
        elif o["op"] == "restore":
            out[o["attr"]] = o["value"]
    return out


def final_props(assertions: list[dict]) -> dict:
    """What `SET n += props` leaves: later assertions win attribute by attribute."""
    props: dict = {}
    for a in assertions:
        props.update(a["item"])
    return props


# ------------------------------------------------------------------------------- the audit

def classify(groups: dict, relocs: dict) -> list[dict]:
    rows = []
    for (label, key), asserts in sorted(groups.items()):
        if len(asserts) < 2:
            continue
        surv = asserts[-1]
        s_span, s_id = norm(surv["span"]), identity_norm(surv["identity"])
        loose: dict[tuple, list] = {}
        for a in asserts[:-1]:
            loose.setdefault((norm(a["span"]), identity_norm(a["identity"])), []).append(a)
        for (o_span, o_id), occ in sorted(loose.items()):
            if o_span == s_span:
                cls = "benign_duplicate"
            elif o_id == s_id:
                cls = "same_term_lost_evidence"
            else:
                cls = "collision"
            # Run first: a whole-document run has no chunk id, so two such runs would
            # otherwise compare equal on chunk and read as `same_chunk`.
            if any(a["run"] != surv["run"] for a in occ):
                origin = "other_run"
            elif all(a["chunk"] == surv["chunk"] for a in occ):
                origin = "same_chunk"
            else:
                origin = "other_chunk_same_run"
            reloc = [o for o in relocs.get(key) or []
                     if o["op"] == "relocate" and o["label"] in (None, label)]
            rows.append({
                "key": key, "label": label, "doc_id": surv["doc_id"], "class": cls,
                "origin": origin,
                "survivor_shard_line": surv["where"], "survivor_chunk": surv["chunk"],
                "survivor_run": surv["run"],
                "overwritten_shard_lines": ";".join(a["where"] for a in occ),
                "overwritten_chunks": ";".join(sorted({a["chunk"] for a in occ})),
                "overwritten_runs": ";".join(sorted({a["run"] for a in occ})),
                "identity_contained": str(bool(o_id and s_id and (o_id in s_id or s_id in o_id))
                                          ).lower(),
                "relocation_overlay": str(bool(reloc)).lower(),
                "survivor_span_80": preview(surv["span"]),
                "overwritten_span_80": preview(occ[-1]["span"]),
                # in full for a collision (task decision 2: "list those in full"); the
                # first PREVIEW_CHARS otherwise, like the spans
                "survivor_identity": (norm(surv["identity"]) if cls == "collision"
                                      else preview(surv["identity"])),
                "overwritten_identity": (norm(occ[-1]["identity"]) if cls == "collision"
                                         else preview(occ[-1]["identity"])),
                "positional_id": str(bool(POSITIONAL_ID.fullmatch(key.split("::", 1)[1]))
                                     ).lower(),
                "lost_span": o_span if cls != "benign_duplicate" else "",
            })
    return rows


def alternative_nodes(asserts: list[dict], label: str,
                      ops: list[dict]) -> dict[str, list[dict]]:
    """The node(s) one (label, key) group becomes under each keying, as final property dicts.

    current  `<doc>::<id>`, last assertion wins attribute by attribute (the projection today).
    chunk    fix (a): `<doc>::<chunk>::<id>`, last-wins within a chunk key, then a merge of the
             chunk nodes whose normalised spans are identical.
    first    fix (b): `<doc>::<id>`, the first assertion stands and a later one with a
             different normalised span is refused to quarantine; an identical one is a no-op.
    """
    by_chunk: dict[str, list] = {}
    for a in asserts:
        by_chunk.setdefault(a["chunk"], []).append(a)
    by_span: dict[str, dict] = {}
    for chunk_asserts in by_chunk.values():
        props = final_props(chunk_asserts)
        by_span.setdefault(norm(span_of(props)), props)
    # The overlays key on `<doc>::<item>` and carry no chunk, so under fix (a) one lands on
    # every chunk node of the item: what `MATCH (n {doc_id, id})` would bind.
    return {k: [apply_overlays(p, label, ops) for p in v] for k, v in
            {"current": [final_props(asserts)], "chunk": list(by_span.values()),
             "first": [dict(asserts[0]["item"])]}.items()}


def record_inputs() -> dict:
    """The selection rules the cited figures were computed with, read from the stored record
    rather than restated here."""
    kq = yaml.safe_load(KG_QUESTIONS.read_text(encoding="utf-8"))
    qs = {q["id"]: q for q in kq["questions"]}
    gloss = list(csv.DictReader(GLOSSARY_CSV.open(encoding="utf-8")))
    return {"q1_rx": qs["Q1"]["selection"]["regex_any"],
            "q1_apart_rx": qs["Q1"]["selection"]["instrument_names_listed_apart"],
            "q1_count": qs["Q1"]["counts"]["definitions"],
            "q1_keys": [r["node_key"] for r in qs["Q1"]["rows"]],
            "q2_stems": qs["Q2"]["vocabulary"]["stems"],
            "q4_rx": qs["Q4"]["selection"]["regex"],
            "q4_count": qs["Q4"]["counts"]["instrument_nodes"],
            "q2_by_construct": qs["Q2"]["by_construct"],
            "epoch_definitions": kq["epoch"]["definitions"],
            "epoch_instruments": kq["epoch"]["instruments"],
            "glossary": gloss}


def impact(groups: dict, rec: dict, ops: dict) -> dict:
    """Task decision 3: the cited figures recomputed from the log under each keying. Each
    `current` value is the positive control: it must reproduce the stored figure, or the
    alternatives are not comparable to it."""
    keyings = ("current", "chunk", "first")
    nodes = {k: Counter() for k in keyings}
    pre_commerce = {k: 0 for k in keyings}   # Definition nodes outside COMMERCE_DOC
    q1 = {k: [] for k in keyings}
    q2 = {k: Counter() for k in keyings}
    q4 = {k: 0 for k in keyings}
    q4_rx = re.compile(rec["q4_rx"])
    gloss_hits = {k: set() for k in keyings}
    labels_gloss = [(g["term"], norm(f"{g['term']}{g['footnote']}:")) for g in rec["glossary"]]
    rx = [re.compile(r) for r in rec["q1_rx"]]
    apart = re.compile(rec["q1_apart_rx"])
    stems = [(n, re.compile(r)) for n, r in rec["q2_stems"].items()]
    for (label, key), asserts in groups.items():
        alt = alternative_nodes(asserts, label, ops.get(key) or [])
        for k in keyings:
            nodes[k][label] += len(alt[k])
            if label == "Instrument":
                q4[k] += sum(1 for p in alt[k] if q4_rx.fullmatch(str(p.get("name") or "").lower()))
            if label != "Definition":
                continue
            if asserts[0]["doc_id"] != COMMERCE_DOC:
                pre_commerce[k] += len(alt[k])
            for props in alt[k]:
                term = str(props.get("term") or "").lower()
                if any(r.fullmatch(term) for r in rx) and not apart.search(term):
                    q1[k].append(key)
                    text = str(props.get("verbatim_text") or "").lower()
                    for n, r in stems:
                        if r.search(text):
                            q2[k][n] += 1
                if asserts[0]["doc_id"] == COMMERCE_DOC:
                    span = norm(span_of(props))
                    for term_name, lab in labels_gloss:
                        if lab in span:
                            gloss_hits[k].add(term_name)
    return {"nodes": nodes, "pre_commerce": pre_commerce, "q1": q1, "q2": q2, "q4": q4, "gloss": gloss_hits,
            "n_gloss": len(rec["glossary"])}


# ------------------------------------------------------------------------------- render

def table(header: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return out


def md_escape(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def render(assertions: list[dict], edges: list[dict], stats: Counter,
           relocs: dict) -> tuple[str, str]:
    groups: dict = defaultdict(list)
    for a in assertions:
        groups[(a["label"], a["key"])].append(a)
    rows = classify(groups, relocs)
    rec = record_inputs()
    imp = impact(groups, rec, relocs)

    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=CSV_FIELDS, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    csv_text = buf.getvalue()

    multi = {g: a for g, a in groups.items() if len(a) > 1}
    lossy = {(r["label"], r["key"]) for r in rows if r["class"] != "benign_duplicate"}
    keys_by_label = defaultdict(set)
    for (label, key) in groups:
        keys_by_label[key].add(label)
    cross_label = sum(1 for v in keys_by_label.values() if len(v) > 1)

    L = [BEGIN, "",
         "### G1. What was read",
         "",
         f"`node_asserted` events on the untagged log: {stats['node_asserted']}; projected "
         f"{stats['projected']} (skipped: non-graph purpose or quarantined batch "
         f"{stats['skipped_non_graph']}, superseded extraction or stratum "
         f"{stats['skipped_superseded']}, label outside `kg/schema.yaml` "
         f"{stats['skipped_label']}). (label, key) groups: {len(groups)}; asserted more than "
         f"once: {len(multi)}; with at least one span lost (a non-benign row): {len(lossy)}. "
         f"Keys carried by two labels (two nodes, not fusion): {cross_label}.",
         ""]

    # G2: label x class
    by_lc = Counter((r["label"], r["class"]) for r in rows)
    labels = sorted({r["label"] for r in rows})
    lost_spans = Counter()
    for (lb, key, sp) in {(r["label"], r["key"], r["lost_span"]) for r in rows
                          if r["lost_span"]}:
        lost_spans[lb] += 1
    trows = []
    for lb in labels:
        cnt = [by_lc[(lb, c)] for c in CLASSES]
        keys_lb = len({r["key"] for r in rows if r["label"] == lb})
        trows.append([lb, keys_lb] + cnt + [cnt[1] + cnt[2], lost_spans[lb]])
    tot = [sum(by_lc[(lb, c)] for lb in labels) for c in CLASSES]
    trows.append(["**all**", len({(r["label"], r["key"]) for r in rows})] + tot
                 + [tot[1] + tot[2], sum(lost_spans.values())])
    L += ["### G2. Overwritten (span, identity) pairs by label and class", "",
          "A row is one distinct (normalised span, normalised identity) pair a later assertion "
          "replaced. The last column counts distinct normalised spans that differ from the "
          "survivor's, per node: the evidence no longer on the graph.", ""]
    L += table(["label", "fused (label, key) groups"] + list(CLASSES)
               + ["non-benign rows", "distinct spans lost"], trows)
    L.append("")

    # G3: origin x class
    by_oc = Counter((r["origin"], r["class"]) for r in rows)
    L += ["### G3. By origin of the overwritten assertion", ""]
    L += table(["origin"] + list(CLASSES),
               [[o] + [by_oc[(o, c)] for c in CLASSES] for o in ORIGINS])
    L.append("")

    # G4: by survivor run
    by_run = defaultdict(Counter)
    docs_run = defaultdict(set)
    for r in rows:
        by_run[r["survivor_run"]][r["class"]] += 1
        docs_run[r["survivor_run"]].add(r["doc_id"])
    L += ["### G4. By extraction run of the survivor (shard | purpose | model | prompt)", ""]
    L += table(["run", "documents"] + list(CLASSES),
               [[f"`{run}`", len(docs_run[run])] + [by_run[run][c] for c in CLASSES]
                for run in sorted(by_run)])
    L.append("")

    # G5: identity-containment within collisions (threshold-free near-miss indicator)
    coll = [r for r in rows if r["class"] == "collision"]
    contained = sum(1 for r in coll if r["identity_contained"] == "true")
    pos = Counter((r["class"], r["positional_id"]) for r in rows)
    # Edges asserted in a chunk whose assertion of the endpoint was overwritten as a
    # collision: the edge is about the lost item and lands on the survivor, a different one.
    collided = {(r["key"], c) for r in coll for c in r["overwritten_chunks"].split(";")
                if c != r["survivor_chunk"]}
    misattached = Counter()
    for e in edges:
        for end in e["ends"]:
            if end and (bp.node_key(e["doc_id"], end), e["chunk"]) in collided:
                misattached[e["type"]] += 1
                break
    # Which assertion each relocation overlay on a fused node was written against: its
    # `old_span` is the survivor's, an overwritten assertion's, or neither.
    stale = Counter()
    for (label, key), asserts in multi.items():
        surv, earlier = norm(asserts[-1]["span"]), {norm(x["span"]) for x in asserts[:-1]}
        for o in relocs.get(key) or []:
            if o["op"] != "relocate" or o["label"] not in (None, label):
                continue
            old = norm(o["old"])
            stale["survivor" if old == surv else
                  "overwritten" if old in earlier else "neither"] += 1
    relocated_lossy = sum(1 for r in rows if r["class"] != "benign_duplicate"
                          and r["relocation_overlay"] == "true")
    L += ["### G5. Two qualifiers on the classes", "",
          f"Collisions where one identity text contains the other (a narrower or wider "
          f"statement of one item rather than two items): {contained} of {len(coll)}. "
          f"Non-benign rows whose node also carries a `grounding_relocated` overlay, which "
          f"the projection applies after every assertion: {relocated_lossy}. The "
          f"`grounding_relocated` overlays on fused nodes were written against the survivor's "
          f"span {stale['survivor']} times, against an overwritten assertion's span "
          f"{stale['overwritten']} times (the overlay then puts that earlier item's relocated "
          f"span onto the survivor), and against neither {stale['neither']} times. Projected "
          f"edges asserted in a chunk whose own assertion of an endpoint was overwritten as a "
          f"collision, so the edge now attaches to a different item: "
          f"{sum(misattached.values())} of {stats['edge_projected']} projectable `edge_asserted` events ("
          + ", ".join(f"`{t}` {n}" for t, n in sorted(misattached.items())) + "). Rows on a "
          f"positional local id (`POSITIONAL_ID`, e.g. `d1`, `cl4`): "
          + "; ".join(f"{c} {pos[(c, 'true')]} of {pos[(c, 'true')] + pos[(c, 'false')]}"
                      for c in CLASSES) + ".", ""]

    # G6: impact under each keying
    n, q1, q2, gl = imp["nodes"], imp["q1"], imp["q2"], imp["gloss"]
    L += ["### G6. Cited figures recomputed from the log under each keying", "",
          "`current` is today's `<doc>::<id>` last-wins and is the positive control: it must "
          "reproduce the stored figure. `chunk` is fix (a), `first` is fix (b).", ""]
    irows = [["Definition nodes", rec["epoch_definitions"], n["current"]["Definition"],
              n["chunk"]["Definition"], n["first"]["Definition"]],
             ["Definition nodes outside the Commerce document (the 1,975 epoch)",
              CITED_PRE_COMMERCE_DEFINITIONS,
              imp["pre_commerce"]["current"], imp["pre_commerce"]["chunk"],
              imp["pre_commerce"]["first"]],
             ["Claim nodes", "—", n["current"]["Claim"], n["chunk"]["Claim"],
              n["first"]["Claim"]],
             ["Instrument nodes", rec["epoch_instruments"], n["current"]["Instrument"],
              n["chunk"]["Instrument"], n["first"]["Instrument"]],
             ["Q1 definitions", rec["q1_count"], len(q1["current"]), len(q1["chunk"]),
              len(q1["first"])],
             ["Q1 documents", "", len({k.split("::")[0] for k in q1["current"]}),
              len({k.split("::")[0] for k in q1["chunk"]}),
              len({k.split("::")[0] for k in q1["first"]})],
             ["Q4 Instrument nodes named for readiness", rec["q4_count"], imp["q4"]["current"],
              imp["q4"]["chunk"], imp["q4"]["first"]],
             [f"Commerce glossary terms with a Definition whose span names `<term><fn>:` "
              f"(of {imp['n_gloss']})", "48 (two-pipelines metric)", len(gl["current"]),
              len(gl["chunk"]), len(gl["first"])]]
    stored_q2 = {c: len(v) for c, v in rec["q2_by_construct"].items()}
    for c in rec["q2_stems"]:
        irows.append([f"Q2 `{c}`", stored_q2.get(c, 0), q2["current"][c], q2["chunk"][c],
                      q2["first"][c]])
    L += table(["figure", "stored", "current", "chunk (a)", "first (b)"], irows)
    L.append("")
    lost_first = sorted(gl["current"] - gl["first"])
    L += [f"Glossary terms the `current` keying finds and fix (b) would lose: "
          f"{len(lost_first)}" + (": " + ", ".join(lost_first) if lost_first else "") + ".",
          ""]
    q1_extra = sorted(set(q1["chunk"]) - set(q1["current"]))
    L += [f"Q1 keys that gain a node under fix (a): "
          + (", ".join(f"`{k}`" for k in q1_extra) if q1_extra else "none") + ".", ""]

    # G7: the stored Q1 rows, one by one
    by_key = defaultdict(list)
    for r in rows:
        if r["label"] == "Definition":
            by_key[r["key"]].append(r["class"])
    L += ["### G7. The stored Q1 rows and their fusion", ""]
    L += table(["Q1 node key", "assertions", "classes of overwritten pairs"],
               [[f"`{k}`", len(groups.get(("Definition", k), [])),
                 ", ".join(f"{c} ×{v}" for c, v in sorted(Counter(by_key[k]).items()))
                 or "not fused"] for k in rec["q1_keys"]])
    L.append("")

    # G8: by document
    by_doc = defaultdict(Counter)
    for r in rows:
        by_doc[r["doc_id"]][r["class"]] += 1
    L += ["### G8. By document (non-benign first)", ""]
    L += table(["document"] + list(CLASSES),
               [[f"`{d}`"] + [by_doc[d][c] for c in CLASSES]
                for d in sorted(by_doc, key=lambda d: (-(by_doc[d]["collision"]
                                                         + by_doc[d]["same_term_lost_evidence"]),
                                                       d))])
    L.append("")

    # G9: collisions, in full
    L += ["### G9. Collisions (task decision 2: a wrong node, not a lost span)", "",
          f"All {len(coll)} are listed in full in the CSV (`class == collision`, both identity "
          f"texts verbatim after normalisation). The Definition collisions are listed in full "
          f"here because the record cites Definition counts; every other label is counted.", ""]
    coll_lab = Counter(r["label"] for r in coll)
    L += table(["label", "collisions"], [[lb, coll_lab[lb]] for lb in sorted(coll_lab)])
    L.append("")
    L += table(["key", "survivor term", "overwritten term", "origin", "overwritten at"],
               [[f"`{r['key']}`", md_escape(r["survivor_identity"]),
                 md_escape(r["overwritten_identity"]), r["origin"],
                 r["overwritten_shard_lines"]] for r in coll if r["label"] == "Definition"])
    L += ["", END]
    return csv_text, "\n".join(L) + "\n"


def splice(md: str, block: str) -> str:
    if BEGIN not in md or END not in md:
        raise SystemExit(f"FATAL: {OUT_MD.relative_to(REPO)} lacks the generated-block markers")
    head, rest = md.split(BEGIN, 1)
    _old, tail = rest.split(END + "\n", 1) if (END + "\n") in rest else rest.split(END, 1)
    return head + block + tail


def stored_block(md: str) -> str:
    if BEGIN not in md or END not in md:
        return ""
    start = md.index(BEGIN)
    end = md.index(END) + len(END) + 1
    return md[start:end]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    assertions, edges, stats = projected_assertions()
    csv_text, block = render(assertions, edges, stats, overlays())
    if a.check:
        drift = []
        if not OUT_CSV.is_file() or OUT_CSV.read_text(encoding="utf-8") != csv_text:
            drift.append(OUT_CSV.relative_to(REPO).as_posix())
        if not OUT_MD.is_file() or stored_block(OUT_MD.read_text(encoding="utf-8")) != block:
            drift.append(OUT_MD.relative_to(REPO).as_posix() + " (generated block)")
        print("DRIFT: " + ", ".join(drift) if drift else "no drift")
        return 1 if drift else 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_CSV.write_text(csv_text, encoding="utf-8")
    md = (OUT_MD.read_text(encoding="utf-8") if OUT_MD.is_file()
          else "# Node-key fusion audit\n\n" + BEGIN + "\n" + END + "\n")
    OUT_MD.write_text(splice(md, block), encoding="utf-8")
    print(f"wrote {OUT_CSV.relative_to(REPO)} and the generated block of "
          f"{OUT_MD.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
