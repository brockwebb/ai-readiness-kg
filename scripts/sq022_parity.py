#!/usr/bin/env python3
"""SQ-022 Part C: run the pre-registered parity set (docs/evidence/sq022/parity_queries.yaml) against the corpus layer
in the project database and in the kit graph's database, canonicalize, compare, and trace every difference.

    /opt/anaconda3/bin/python3 scripts/sq022_parity.py --kept-out <kept_out.jsonl> --out docs/evidence/sq022/<run>

squiddy cc_tasks/2026-10-22_SQ-022_..._consumer_repointed.md Part C, under squiddy DN-049 R-210 as amended. The query
file is the specification and was committed before any answer from the new database was read (8ce578c1); this script
implements it and nothing else: its configurations, its dialect map, its canonicalization and its tracing rule are the
file's, read from the file, so a change of rule is a change of that file, never of this one. Zero spend: local reads.

The two configurations, one verb layer (mcp/airkg_tools.Tools), built fresh in this process:
    old  Tools(graph=<project db>)                                   corpus reader = the assessment reader
    new  Tools(graph=<project db>, corpus=<kit db, layer corpus>)

Output, per run directory: answers_old.jsonl and answers_new.jsonl (each call's canonical answer), differences.jsonl
(every difference with its trace), and result.json (the verb table: calls, equal, traced, untraced, with the n).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "mcp"))
import airkg_guard as guard  # noqa: E402
import airkg_tools as T  # noqa: E402

QUERIES = REPO / "docs" / "evidence" / "sq022" / "parity_queries.yaml"
#: the query file's corrections, each a file beside it, applied in order when present (never an edit of the file)
ERRATA = [REPO / "docs" / "evidence" / "sq022" / "parity_queries_ERRATUM_01.yaml"]
KIT_CONFIG = REPO / "graphs" / "ai-readiness" / "config.yaml"

#: The verbs' own keys on a get_document answer; every other top-level key is a Document property (`{**p, ...}`).
DOC_VERB_KEYS = {"doc_id", "counts", "evidences_indicators", "locators", "corpus_database", "error", "nearest"}


# ------------------------------------------------------------------ the specification, read


def load_spec() -> dict:
    """The query file, with its errata applied. ERRATUM 01: the relationship-type dialect, from the kit graph's own
    `domain.airkg_schema.class_of` (source type -> class); `reltypes` maps the old store's type to the kit's."""
    import yaml
    spec = yaml.safe_load(QUERIES.read_text(encoding="utf-8"))
    spec["reltypes"], spec["errata"] = {}, []
    for e in ERRATA:
        if not e.is_file():
            continue
        er = yaml.safe_load(e.read_text(encoding="utf-8"))
        spec["errata"].append(str(e.relative_to(REPO)))
        if "relationship_types" in (er.get("dialect_add") or {}):
            cfg = yaml.safe_load(KIT_CONFIG.read_text(encoding="utf-8"))
            class_of = cfg["domain"]["airkg_schema"]["class_of"]
            edge_types = set(cfg["domain"]["airkg_schema"].get("source_edge_types") or []) or {
                k for k in class_of if k[:1].islower()}
            spec["reltypes"] = {k.upper(): class_of[k] for k in edge_types}
    return spec


def expand(calls: list[dict]) -> list[dict]:
    """C11 and C12 name one count query per label or type; the file gives their text (its closing comment)."""
    out = []
    for c in calls:
        if c.get("count_per") == "label":
            for lab in c["labels"]:
                out.append({**c, "id": f"{c['id']}.{lab}", "item": ("label", lab),
                            "args": {"query": f"MATCH (n:{lab}) RETURN count(n) AS n"}})
        elif c.get("count_per") == "type":
            for t in c["types"]:
                out.append({**c, "id": f"{c['id']}.{t}", "item": ("type", t),
                            "args": {"query": f"MATCH (a)-[e:{t}]->(b) WHERE NOT a:AssessmentIndicator AND NOT "
                                              f"a:Observation AND NOT a:Finding RETURN count(e) AS n"}})
        else:
            out.append(c)
    return out


_REL_PATTERN = re.compile(r"\[([^\]]*?):([A-Z_]+)([^\]]*)\]")


def rewrite(query: str, spec: dict) -> str:
    for old, new in spec["dialect"]["cypher_rewrite"].items():
        query = re.sub(re.escape(old) + r"\b", new, query)
    # ERRATUM 01: a relationship type inside `[...]`, the old store's name to the kit's class
    rel = spec.get("reltypes") or {}
    return _REL_PATTERN.sub(lambda m: f"[{m.group(1)}:{rel.get(m.group(2), m.group(2))}{m.group(3)}]", query)


# ------------------------------------------------------------------ running


def run_call(tools, call: dict, args: dict, config: str, spec: dict):
    verb = call["verb"]
    if verb == "run_cypher":
        layer = call.get("layer", "assessment")
        q = args["query"]
        if layer == "corpus" and config == "new":
            q = rewrite(q, spec)
        return tools.run_cypher(q, layer=layer)
    return getattr(tools, verb)(**args)


def resolve_args(call: dict, old_answers: dict) -> dict:
    out = {}
    for k, v in (call.get("args") or {}).items():
        if isinstance(v, dict) and "from" in v:
            cur = old_answers[v["from"]]
            for part in re.findall(r"[^.\[\]]+", v["path"]):
                cur = cur[int(part)] if part.isdigit() else cur[part]
            out[k] = cur
        else:
            out[k] = v
    return out


# ------------------------------------------------------------------ canonicalization (the file's `canonicalize`)


def canon_props(p: dict, side: str, spec: dict) -> tuple[str | None, dict]:
    """(node key, the property map canonicalized): the new side's names mapped to the old's, bookkeeping dropped."""
    p = dict(p)
    key = p.pop(spec["dialect"]["node_key"][side], None)       # the row's identity, compared as the row key
    # bookkeeping first, so a renamed property (kit `instrument_method` -> `method`) is never confused with the kit's
    # own stamp of the same old name (`method: extraction`)
    for k in spec["canonicalize"]["store_bookkeeping_properties"][side]:
        p.pop(k, None)
    if side == "new":
        for kit, old in spec["dialect"]["renamed_properties"].items():
            if kit in p:
                p[old] = p.pop(kit)
    # a Document's `id` IS its node key in both stores (the old one MERGEs Document on id = doc_id)
    if p.get("id") == key:
        p.pop("id")
    return key, p


def strip_store_identity(x):
    if isinstance(x, dict):
        if x.get("kind") == "graph" and x.get("id_property") == "database":
            x = {k: v for k, v in x.items() if k != "id"}
        return {k: strip_store_identity(v) for k, v in x.items()
                if k not in ("database",)}
    if isinstance(x, list):
        return [strip_store_identity(v) for v in x]
    return x


def canon_locator(loc: dict, spec: dict) -> dict:
    if isinstance(loc, dict) and loc.get("kind") == "graph" and loc.get("id_property") in (
            spec["dialect"]["node_key"]["old"], spec["dialect"]["node_key"]["new"]):
        return {**loc, "id_property": "<node_key>"}
    return loc


def canonicalize(call: dict, ans: dict, side: str, spec: dict) -> dict:
    a = strip_store_identity(copy.deepcopy(ans))
    a.pop("corpus_database", None)        # new-only field naming the store: store identity, reported below
    a.pop("layer", None)
    if call["verb"] == "get_document" and "error" not in a:
        props = {k: v for k, v in a.items() if k not in DOC_VERB_KEYS}
        _key, props = canon_props({**props, spec["dialect"]["node_key"][side]: a.get("doc_id")}, side, spec)
        a = {**{k: v for k, v in a.items() if k in DOC_VERB_KEYS}, "properties": props}
    if call["verb"] == "search_text":
        for h in a.get("hits") or []:
            h["locator"] = canon_locator(h.get("locator"), spec)
    if call["verb"] == "run_cypher" and "rows" in a:
        rows = []
        for r in a["rows"]:
            r = dict(r)
            for k, v in list(r.items()):
                if isinstance(v, dict):
                    nk, pv = canon_props(v, side, spec)
                    r[k] = {"__key__": nk, **pv}
            rows.append(r)
        a["rows"] = rows
    return a


# ------------------------------------------------------------------ comparison


def diff(a, b, path="") -> list[tuple[str, object, object]]:
    """(path, old, new) for every leaf that differs; a key on the new side only is reported as `+` (an addition)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            if k not in b:
                out.append((f"{path}.{k}", a[k], "<absent>"))
            elif k not in a:
                out.append((f"{path}.+{k}", "<absent>", b[k]))
            else:
                out += diff(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if a == b:
            return []
        return [(path, a, b)]
    return [] if a == b else [(path, a, b)]


# ------------------------------------------------------------------ tracing (the file's `TRACING`)


class Stores:
    """Direct reads of both stores' item sets, for tracing only (never through the verbs' row cap)."""

    def __init__(self, old: T.Graph, new: T.Graph, reltypes: dict | None = None):
        self.old, self.new = old, new
        self.reltypes = reltypes or {}

    def ids(self, side: str, label: str, where: str = "", **params) -> set:
        g = self.old if side == "old" else self.new
        key = g.dialect["key"] if label != "Document" else "doc_id"
        rows, _ = g.read(f"MATCH (n:{label}) {where} RETURN n.{key} AS k", limit=10_000_000, **params)
        return {r["k"] for r in rows}

    def triples(self, side: str, typ: str, a: str = "", b: str = "") -> set:
        g = self.old if side == "old" else self.new
        k = g.dialect["key"]
        t = typ if side == "old" else self.reltypes.get(typ, typ)     # reported under the old name (ERRATUM 01)
        rows, _ = g.read(f"MATCH (x{a})-[e:{t}]->(y{b}) WHERE NOT x:AssessmentIndicator AND NOT x:Observation "
                         f"AND NOT x:Finding RETURN coalesce(x.{k}, x.doc_id) AS s, coalesce(y.{k}, y.doc_id) AS o",
                         limit=10_000_000)
        return {(r["s"], typ, r["o"]) for r in rows}


def item_sets(call: dict, st: Stores, side: str) -> dict:
    """{kind: set of item keys} behind a COUNT answer, by the same pattern (the file: `a count`)."""
    cid = call["id"]
    if cid.startswith("C11."):
        return {f"node:{call['item'][1]}": st.ids(side, call["item"][1])}
    if cid.startswith("C12."):
        return {"edge": st.triples(side, call["item"][1])}
    if cid == "C02":
        return {"node:Definition": st.ids(side, "Definition"), "node:Instrument": st.ids(side, "Instrument")}
    if cid == "C05":
        return {"node:Construct": st.ids(side, "Construct"),
                "edge": st.triples(side, "GROUNDS", ":Construct", ":Definition")
                | {t for typ in ("DEFINES", "MENTIONS", "ABOUT", "SUBTYPE_OF", "EXTENDS", "CONFLICTS_WITH",
                                 "HAS_COMPONENT", "MEASURES", "APPLIES_TO")
                   for t in st.triples(side, typ, ":Definition", ":Concept") | st.triples(side, typ, ":Concept",
                                                                                          ":Definition")}}
    if cid == "C08":
        return {"edge": st.triples(side, "OPERATIONALIZES", ":Instrument")
                | st.triples(side, "OPERATIONALIZED_BY", ":Framework", ":Instrument")}
    if cid == "C09":
        return {"edge": st.triples(side, "ASSERTS", ":Document", ":Concept")}
    if cid == "C10":
        return {"node:Definition": st.ids(side, "Definition", "WHERE NOT ()-[:DEFINES]->(n)")}
    return {}


def trace_items(old_only: dict, new_only: dict, kept: dict) -> tuple[list, list]:
    """(traced, untraced) item descriptions: an old-only item traces by its kept-out key; a new-only item never does."""
    traced, untraced = [], []
    for kind, items in old_only.items():
        for it in sorted(items, key=str):
            if kind == "edge":
                k = ("edge", json.dumps([it[0], it[1], it[2]]))
            else:
                k = ("node", json.dumps([it, kind.split(":", 1)[1]]))
            (traced if k in kept else untraced).append({"side": "old_only", "kind": kind, "item": list(it)
                                                        if isinstance(it, tuple) else it,
                                                        "kept_out_as": kept.get(k)})
    for kind, items in new_only.items():
        for it in sorted(items, key=str):
            untraced.append({"side": "new_only", "kind": kind, "item": list(it) if isinstance(it, tuple) else it})
    return traced, untraced


def trace(call, a_old, a_new, diffs, st: Stores, kept: dict, answers_old: dict, answers_new: dict) -> dict:
    """Every difference of one call, traced or not, by the file's rule for its answer's shape."""
    traced, untraced, notes = [], [], []
    cid, verb = call["id"], call["verb"]
    # a COUNT: the symmetric difference of the item sets under the same pattern
    if verb == "run_cypher" and (cid.startswith("C11.") or cid.startswith("C12.")
                                 or cid in ("C02", "C05", "C08", "C09", "C10")):
        so, sn = item_sets(call, st, "old"), item_sets(call, st, "new")
        old_only = {k: so[k] - sn.get(k, set()) for k in so}
        new_only = {k: sn[k] - so.get(k, set()) for k in sn}
        t, u = trace_items(old_only, new_only, kept)
        return {"traced": t, "untraced": u, "notes": [f"items: {sum(map(len, so.values()))} old, "
                                                      f"{sum(map(len, sn.values()))} new"]}
    # ROWS: by node key (C01 Documents by doc_id; C03/C07 by the property map's key; C04 by key; C06 by (a, b))
    if verb == "run_cypher" and cid in ("C01", "C03", "C04", "C06", "C07"):
        def rk(r):
            if cid == "C01":
                return ("node:Document", r.get("id"))
            if cid == "C04":
                return ("node:Definition", r.get("key"))
            if cid == "C06":
                return ("edge", (r["a"]["__key__"], "CONFLICTS_WITH", r["b"]["__key__"]))
            return ("node:Definition" if cid == "C03" else "node:Instrument", r["p"]["__key__"])
        ro = {rk(r): r for r in a_old.get("rows") or []}
        rn = {rk(r): r for r in a_new.get("rows") or []}
        oo, nn = defaultdict(set), defaultdict(set)
        for k in set(ro) - set(rn):
            oo[k[0]].add(k[1])
        for k in set(rn) - set(ro):
            nn[k[0]].add(k[1])
        # a truncated list: a new-only row the old store holds beyond the cap is DISPLACED
        if a_old.get("truncated") or a_new.get("truncated"):
            for kind in list(nn):
                full_old = item_sets({"id": "C11.x", "item": ("label", kind.split(":")[1])}, st, "old")[kind] \
                    if kind.startswith("node:") else set()
                disp = {x for x in nn[kind] if x in full_old}
                if disp:
                    notes.append(f"{len(disp)} new-only row(s) displaced: held by the old store beyond the row cap")
                    traced += [{"side": "new_only", "kind": kind, "item": x, "displaced": True} for x in sorted(disp)]
                    nn[kind] -= disp
        t, u = trace_items(oo, nn, kept)
        traced += t
        untraced += u
        for k in set(ro) & set(rn):
            for path, x, y in diff(ro[k], rn[k], f"rows[{k[1]}]"):
                if ".+" in path:
                    notes.append(f"addition {path}")
                else:
                    untraced.append({"side": "both", "kind": "value", "path": path, "old": x, "new": y})
        for path, x, y in diffs:
            if not path.startswith(".rows") and path not in (".row_count", ".truncated"):
                if ".+" in path:
                    notes.append(f"addition {path}")
                else:
                    untraced.append({"side": "both", "kind": "value", "path": path, "old": x, "new": y})
        return {"traced": traced, "untraced": untraced, "notes": notes}
    # get_document: counts per label by item set of that document; properties are values
    if verb == "get_document":
        doc = call["args"]["doc_id"]
        for path, x, y in diffs:
            if path.startswith(".counts."):
                lab = {o.lower() + "s": o for o in T.ADDRESSABLE_LABELS + ("Concept", "Claim", "Standard",
                       "Framework", "Practice", "Measure", "Instrument", "Tool", "Platform", "Construct")}.get(
                    path.split(".")[2].lstrip("+"))
                if lab is None:
                    untraced.append({"side": "both", "kind": "count", "path": path, "old": x, "new": y})
                    continue
                so = st.ids("old", lab, "WHERE n.doc_id = $d", d=doc)
                sn = st.ids("new", lab, "WHERE n.doc_id = $d", d=doc)
                t, u = trace_items({f"node:{lab}": so - sn}, {f"node:{lab}": sn - so}, kept)
                traced += t
                untraced += u
            elif ".+" in path:
                notes.append(f"addition {path}")
            else:
                untraced.append({"side": "both", "kind": "value", "path": path, "old": x, "new": y})
        return {"traced": traced, "untraced": untraced, "notes": notes}
    # search_text: definition hits by key; a limited list's new-only hit is displaced when the old store holds it
    if verb == "search_text":
        def hk(h):
            return ((h.get("locator") or {}).get("id") if h.get("kind") == "definition" else None,
                    json.dumps(h, sort_keys=True))
        def defs(ans):
            return {(h.get("locator") or {}).get("id"): h for h in ans.get("hits") or [] if h.get("kind") == "definition"}
        do, dn = defs(a_old), defs(a_new)
        full_old_ids = st.ids("old", "Definition")
        oo = {"node:Definition": set(do) - set(dn)}
        nn = {"node:Definition": set(dn) - set(do)}
        disp = {x for x in nn["node:Definition"] if x in full_old_ids and a_old.get("truncated")}
        if disp:
            traced += [{"side": "new_only", "kind": "node:Definition", "item": x, "displaced": True}
                       for x in sorted(disp)]
            nn["node:Definition"] -= disp
            notes.append(f"{len(disp)} new-only hit(s) displaced: held by the old store beyond the limit")
        t, u = trace_items(oo, nn, kept)
        traced += t
        untraced += u
        for k in set(do) & set(dn):
            for path, x, y in diff(do[k], dn[k], f"hits[{k}]"):
                untraced.append({"side": "both", "kind": "value", "path": path, "old": x, "new": y})
        rec_o = [h for h in a_old.get("hits") or [] if h.get("kind") != "definition"]
        rec_n = [h for h in a_new.get("hits") or [] if h.get("kind") != "definition"]
        if rec_o != rec_n:
            untraced.append({"side": "both", "kind": "value", "path": "hits[record]", "old": len(rec_o),
                             "new": len(rec_n)})
        # n_hits and truncated follow from the hit sets: traced when every hit-set difference is
        for path, x, y in diffs:
            if path in (".n_hits", ".truncated", ".hits"):
                continue
            if ".+" in path:
                notes.append(f"addition {path}")
            else:
                untraced.append({"side": "both", "kind": "value", "path": path, "old": x, "new": y})
        return {"traced": traced, "untraced": untraced, "notes": notes}
    # any other verb: a difference is a value difference, untraced
    for path, x, y in diffs:
        if ".+" in path:
            notes.append(f"addition {path}")
        else:
            untraced.append({"side": "both", "kind": "value", "path": path, "old": x, "new": y})
    return {"traced": traced, "untraced": untraced, "notes": notes}


# ------------------------------------------------------------------ main


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--kept-out", default=None,
                    help="the kept-out list (default: the query file's `kept_out`); its sha256 is recorded")
    ap.add_argument("--out", required=True, help="the run directory")
    ap.add_argument("--configs", default="old,new", help="which configurations to run (default both)")
    args = ap.parse_args(argv)
    spec = load_spec()
    kept_path = Path(args.kept_out or spec["kept_out"])
    kept = {}
    for ln in kept_path.open(encoding="utf-8"):
        x = json.loads(ln)
        kept[(x["kind"], json.dumps(x["key"]))] = x["reason"]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    project_db, kit_db = guard.project_database(), guard.corpus_database()
    g_old = T.Graph(project_db)
    g_kit = T.Graph(kit_db, layer="corpus")
    configs = {"old": T.Tools(graph=T.Graph(project_db)),
               "new": T.Tools(graph=T.Graph(project_db), corpus=T.Graph(kit_db, layer="corpus"))}
    calls = expand(spec["calls"])
    answers = {"old": {}, "new": {}}
    raw_old = {}
    for side in ("old", "new"):
        with (out / f"answers_{side}.jsonl").open("w", encoding="utf-8") as fh:
            for c in calls:
                a = resolve_args(c, raw_old)
                ans = run_call(configs[side], c, a, side, spec)
                if side == "old":
                    raw_old[c["id"]] = ans
                answers[side][c["id"]] = canonicalize(c, ans, side, spec)
                fh.write(json.dumps({"id": c["id"], "verb": c["verb"], "args": a,
                                     "answer": answers[side][c["id"]]}, ensure_ascii=False, default=str) + "\n")
                fh.flush()
    st = Stores(g_old, g_kit, spec["reltypes"])
    table = defaultdict(Counter)
    with (out / "differences.jsonl").open("w", encoding="utf-8") as fh:
        for c in calls:
            o, n = answers["old"][c["id"]], answers["new"][c["id"]]
            d = diff(o, n)
            row = table[c["verb"] + ("" if c["verb"] != "run_cypher" else f" ({c.get('layer', 'assessment')})")]
            row["calls"] += 1
            if not d:
                row["equal"] += 1
                continue
            tr = trace(c, o, n, d, st, kept, answers["old"], answers["new"])
            only_additions = not tr["untraced"] and not tr["traced"]
            if only_additions:
                row["equal"] += 1
                status = "equal_with_additions"
            elif tr["untraced"]:
                row["untraced"] += 1
                status = "untraced"
            else:
                row["traced"] += 1
                status = "traced"
            row["items_traced"] += len(tr["traced"])
            row["differences_untraced"] += len(tr["untraced"])
            fh.write(json.dumps({"id": c["id"], "verb": c["verb"], "status": status,
                                 "n_traced": len(tr["traced"]), "n_untraced": len(tr["untraced"]),
                                 "notes": tr["notes"], "untraced": tr["untraced"][:200],
                                 "untraced_by_kind": dict(Counter(f"{u['side']}:{u['kind']}" for u in tr["untraced"])),
                                 "traced_by_reason": dict(Counter(t.get("kept_out_as") or ("displaced" if t.get(
                                     "displaced") else "?") for t in tr["traced"]))},
                                ensure_ascii=False, default=str) + "\n")
    result = {"queries": str(QUERIES.relative_to(REPO)),
              "queries_sha256": hashlib.sha256(QUERIES.read_bytes()).hexdigest(),
              "errata": {e: hashlib.sha256((REPO / e).read_bytes()).hexdigest() for e in spec["errata"]},
              "kept_out": str(kept_path), "kept_out_sha256": hashlib.sha256(kept_path.read_bytes()).hexdigest(),
              "databases": {"assessment": project_db, "corpus_old": project_db, "corpus_new": kit_db},
              "calls": len(calls), "seconds": round(time.monotonic() - t0, 1),
              "table": {k: {f: v.get(f, 0) for f in ("calls", "equal", "traced", "untraced", "items_traced",
                                                     "differences_untraced")} for k, v in table.items()},
              "untraced_calls": sum(v.get("untraced", 0) for v in table.values())}
    result["pass"] = result["untraced_calls"] == 0
    (out / "result.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result["table"], indent=1))
    print(f"parity {'PASS' if result['pass'] else 'FAIL'}: {result['untraced_calls']} call(s) with untraced "
          f"differences of {len(calls)}; {result['seconds']}s")
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
