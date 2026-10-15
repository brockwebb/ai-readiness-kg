#!/usr/bin/env python3
"""The readiness diagnostic package's shared data layer: vocabulary, roster, rung-two listing,
and the instrument dictionary read FROM THE RECORD (never the RULE-*.yaml). **Zero spend.**

`cc_tasks/2026-10-15_readiness_diagnostic_package.md` Part B, under DN-016. The renders
(`scripts/diagnostic_package_build.py`, Part D) import this module so there is one source for
each thing the package shows:

* **vocabulary** (DN-016 ruling 1) from `framework/summary_grid_vocab.yaml` `diagnostic_terms`:
  the run is a *readiness diagnostic*, the unit a *check*, the actor the *public client*, the
  four states in plain words. `banned_hits` is the vocabulary test's engine: no rendered product
  contains "scan", "probe", "crawl" or "audit" as a word (code paths keep `scan`).
* **the dictionary** from the framework record's MeasurementSpec nodes (the `rf_*` fields
  Part A wrote), NOT from the YAML — the record is the source of truth and the graph projects it
  (DN-016 ruling 4; the MCP's own rule: framework questions are answered from the record).
* **the roster** (DN-016 §3) from the registered scan-frame DataFile
  `state/scan_targets_fss_2026-09_v5.json` (the frame of record, which `frames/fss16.yaml`
  refers to): body, surface, where we look, in the order `frames/fss16.yaml` holds them; the
  three Tier-C reference hosts are the flagships, marked.
* **the rung-two listing** (DN-016 ruling 3) from the record's AssessmentTool and Precondition
  nodes (task 8f8861ce): per surface that takes a key, whether registration is open to the
  public, with the node that says so. Where the record is silent the cell is "to be confirmed";
  nothing is inferred from the agency's reputation or from a page not in the record.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
VOCAB_FILE = REPO / "framework" / "summary_grid_vocab.yaml"
FRAME_YAML = REPO / "assessment" / "harness" / "scan" / "frames" / "fss16.yaml"
FRAME_DATAFILE = REPO / "state" / "scan_targets_fss_2026-09_v5.json"

#: The four banned stems and the inflections a rendered product might use, matched on word
#: boundaries. "crawler"/"crawlers" is deliberately NOT banned: it is a different word, and the
#: robots.txt vocabulary (A4) names crawler tokens. "scanner" IS banned (a rendered product does
#: not call the public client a scanner). Code paths keep `scan`; this runs over rendered text.
_BANNED = re.compile(
    r"\b(scan|scans|scanned|scanning|scanner|scanners|probe|probes|probed|probing"
    r"|crawl|crawls|crawled|crawling|audit|audits|audited|auditing)\b", re.IGNORECASE)


def banned_hits(text: str) -> list[tuple[str, str]]:
    """Every banned word in `text`, with a little surrounding context. Empty means clean."""
    out = []
    for m in _BANNED.finditer(text or ""):
        a, b = max(0, m.start() - 30), min(len(text), m.end() + 30)
        out.append((m.group(0), text[a:b].replace("\n", " ").strip()))
    return out


#: Whitespace-delimited tokens that carry a slash: file paths, URLs, and the user-agent string
#: `ai-readiness-kg-scanner/0.2 (+https://...)`. These are the "code paths" the vocabulary rule
#: exempts (DN-016 ruling 1 / the task's Part B check): the preface MUST quote the exact
#: user-agent so a security team finds every request in its logs, and that identifier contains
#: "scanner" by construction. A banned word in ordinary prose has no slash and is still caught.
_CODE_PATH_TOKEN = re.compile(r"\S*/\S*")


def banned_hits_prose(text: str) -> list[tuple[str, str]]:
    """`banned_hits` after removing code-path tokens (paths, URLs, the user-agent string). This
    is the vocabulary test over a RENDERED PRODUCT, where those identifiers legitimately appear."""
    return banned_hits(_CODE_PATH_TOKEN.sub(" ", text or ""))


def load_vocab(path: Path = VOCAB_FILE) -> dict:
    v = yaml.safe_load(path.read_text(encoding="utf-8")).get("diagnostic_terms")
    if not v:
        raise SystemExit(f"FATAL: {path} has no diagnostic_terms block (DN-016 ruling 1)")
    return v


def load_framework(path: Path = FRAMEWORK) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


#: The dictionary fields that actually appear in a rendered product, in DN-016 §3's order. The
#: verbatim requirements (rf_requirements) and the DN-015 hypothesis (rf_hypothesis) are stored
#: on the spec for traceability (Part A) but are NOT rendered as plain-language prose — the
#: dictionary names the source in plain words (rf_why_it_matters) instead of quoting it — so the
#: vocabulary test runs over exactly this set, the roster, and the rung-two listing.
RENDERED_DICT_FIELDS = ["rf_question", "rf_where_we_look", "rf_what_client_does",
                        "rf_pass", "rf_partial", "rf_fail", "rf_not_measured",
                        "rf_why_it_matters", "rf_who_else", "rf_rung_two_changes"]


def rendered_plain_name(spec: dict, vocab: dict | None = None) -> str:
    """The plain name the DIAGNOSTIC renders: the vocab override for this leg if one exists
    (A9's instrument name carries the forbidden word "probed"), else the record's rf_plain_name."""
    vocab = vocab or load_vocab()
    ov = (vocab.get("plain_name_overrides") or {}).get(spec.get("leg"))
    return ov or spec.get("rf_plain_name") or ""


# ----------------------------------------------------------------------------- the dictionary

#: The reader-facing fields Part A wrote onto each spec, in DN-016 §3's dictionary order. A ninth
#: labelled line, "what partial, fail and not measured look like", groups the three; the render
#: composes it from rf_partial / rf_fail / rf_not_measured.
DICT_FIELDS = ["rf_plain_name", "rf_question", "rf_where_we_look", "rf_what_client_does",
               "rf_pass", "rf_partial", "rf_fail", "rf_not_measured", "rf_why_it_matters",
               "rf_who_else", "rf_rung_two_changes", "rf_state", "rf_requirements",
               "rf_fix_line", "rf_hypothesis"]


def instrument_specs(g: dict | None = None) -> list[dict]:
    """The sixteen instrument checks from the record, in entry order (`order`, then leg), each a
    dict of its spec id, leg, the `rf_*` fields and its EVIDENCED_BY corpus doc ids."""
    g = g or load_framework()
    by_id = {n["id"]: n for n in g["nodes"]}
    ev = {}
    for e in g["edges"]:
        if e["type"] == "EVIDENCED_BY" and e["from"].startswith("spec:"):
            ev.setdefault(e["from"], []).append((e.get("properties") or {}).get("doc_id"))
    out = []
    for n in g["nodes"]:
        p = n["properties"]
        if "MeasurementSpec" not in n["labels"] or not p.get("instrument_state"):
            continue
        row = {"spec_id": n["id"], "leg": p.get("leg"), "order": p.get("order")}
        for f in DICT_FIELDS:
            row[f] = p.get(f)
        row["requirements"] = json.loads(p.get("rf_requirements") or "[]")
        row["evidenced_by"] = sorted(x for x in ev.get(n["id"], []) if x)
        out.append(row)
    # The record carries no `order` on the spec; use the matrix/leg convention the grid uses.
    leg_order = ["A1", "A2", "A3", "A4", "A5", "A6", "A8", "A9", "A10", "A11-declared",
                 "A12", "A13", "B3", "D1", "D4", "F4"]
    rank = {leg: i for i, leg in enumerate(leg_order)}
    return sorted(out, key=lambda r: rank.get(r["leg"], 999))


# ---------------------------------------------------------------------------------- the roster

def _frame_order() -> list[tuple[str, str]]:
    """(tier, body) in the order `frames/fss16.yaml` holds them: Tier A, then the Tier-C
    reference hosts (the flagships)."""
    f = yaml.safe_load(FRAME_YAML.read_text(encoding="utf-8"))["bodies"]
    return [("A", b) for b in f["tier_a"]] + [("C", b) for b in f["tier_c"]]


def load_frame(path: Path = FRAME_DATAFILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def roster_rows() -> list[dict]:
    """One row per site the frame holds (DN-016 §3), in frame order. Row count equals the frame's
    Tier-A body count plus the three Tier-C flagships. Each row carries the body's surfaces and
    where the diagnostic looks for them (the seeded locations, by selection source)."""
    d = load_frame()
    rows = d["rows"]
    by_body: dict[tuple[str, str], dict] = {}
    for r in rows:
        key = (r.get("tier"), r.get("agency"))
        b = by_body.setdefault(key, {"tier": r.get("tier"), "body": r.get("agency"),
                                      "name": r.get("agency_name"), "host": r.get("host"),
                                      "surfaces": [], "seeded_from": []})
        b["surfaces"].append({"kind": r.get("surface_kind"), "url": r.get("url"),
                              "selected_as": r.get("selected_as"),
                              "selection_source": r.get("selection_source")})
        src = r.get("selection_source")
        if src and src not in b["seeded_from"]:
            b["seeded_from"].append(src)
    out = []
    for tier, body in _frame_order():
        b = by_body.get((tier, body))
        if b is None:
            raise SystemExit(f"FATAL: frame order names {tier}/{body}, absent from the DataFile")
        b["flagship"] = tier == "C"
        b["home"] = next((s["url"] for s in b["surfaces"] if s["kind"] == "home"), None)
        out.append(b)
    want = d["tier_a_agencies"] + d["tier_c_hosts"]
    if len(out) != want:
        raise SystemExit(f"FATAL: roster has {len(out)} rows, frame says {want} "
                         f"({d['tier_a_agencies']} bodies + {d['tier_c_hosts']} flagships)")
    return out


# ----------------------------------------------------------------------------- the rung-two listing

#: The surface kinds a public key could gate. The machine surfaces are the agency data interfaces
#: (API bases and machine entry points); a key, where one is needed, is presented at rung two.
_KEY_BEARING_KINDS = {"machine"}


def rung_two_rows(g: dict | None = None) -> list[dict]:
    """Per roster surface that could take a key (the machine/API surfaces), whether a key is
    required and whether registration is open to the public, from the record's AssessmentTool and
    Precondition nodes. The record holds no per-surface key-and-registration fact today, so every
    cell reads "to be confirmed" with no node to cite — nothing is inferred (DN-016 ruling 3)."""
    g = g or load_framework()
    # Index any Tool/Precondition node that names a specific agency surface by host. (None do
    # today; this is the hook that resolves a cell to a node id once the record carries one.)
    surface_nodes: dict[str, str] = {}
    for n in g["nodes"]:
        if not ({"AssessmentTool", "Precondition"} & set(n["labels"])):
            continue
        p = n["properties"]
        host = p.get("surface_host") or p.get("agency_host")
        if host:
            surface_nodes[host] = n["id"]
    rows = []
    for b in roster_rows():
        for s in b["surfaces"]:
            if s["kind"] not in _KEY_BEARING_KINDS:
                continue
            node = surface_nodes.get(b["host"])
            rows.append({
                "body": b["body"], "name": b["name"], "flagship": b["flagship"],
                "surface": s["url"], "kind": s["kind"],
                "key_required": "to be confirmed" if node is None else "see source",
                "registration_open": "to be confirmed" if node is None else "see source",
                "source": node or "to be confirmed",
            })
    return rows


def rung_two_is_well_formed(rows: list[dict]) -> list[str]:
    """Every row cites a node id OR says 'to be confirmed' (DN-016 ruling 3). Returns offenders."""
    bad = []
    for r in rows:
        src = r.get("source")
        if not (src == "to be confirmed" or (isinstance(src, str) and src.strip())):
            bad.append(f"{r.get('body')} {r.get('surface')}: source {src!r} is neither a node id "
                       "nor 'to be confirmed'")
    return bad


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("what", choices=["vocab", "roster", "rung2", "dict"], nargs="?", default="roster")
    a = ap.parse_args()
    if a.what == "vocab":
        print(json.dumps(load_vocab(), indent=1, ensure_ascii=False))
    elif a.what == "roster":
        r = roster_rows()
        print(f"{len(r)} roster rows ({sum(1 for x in r if not x['flagship'])} bodies + "
              f"{sum(1 for x in r if x['flagship'])} flagships)")
        for x in r:
            print(f"  {'*' if x['flagship'] else ' '} {x['body']:<12} {x['host']:<28} "
                  f"{len(x['surfaces'])} surface(s); seeded from {len(x['seeded_from'])} source(s)")
    elif a.what == "rung2":
        rows = rung_two_rows()
        bad = rung_two_is_well_formed(rows)
        print(f"{len(rows)} rung-two rows; "
              f"{sum(1 for r in rows if r['source'] == 'to be confirmed')} to be confirmed")
        if bad:
            raise SystemExit("\n".join(bad))
    else:
        for s in instrument_specs():
            print(f"{s['leg']:<14} {s['rf_state']:<14} {s['rf_plain_name'] or '(no plain name)'}")
