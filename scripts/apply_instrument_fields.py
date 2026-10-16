#!/usr/bin/env python3
"""Write every reader-facing field of each instrument entry into its MeasurementSpec, and an
`EVIDENCED_BY` edge from the spec to each corpus Document it cites. **Zero spend.**

`cc_tasks/2026-10-15_readiness_diagnostic_package.md` Part A, under DN-016 ruling 4: the
instrument's own content becomes graph state so every render of the diagnostic package is a
query, not a second copy of the YAML. This is the sibling of `scripts/apply_instrument_state.py`
(which writes `instrument_state` / `plain_name` / `fix_line`); it reuses that script's loader
(`instrument.load_entries`) and the ONE writer (`framework_writeback.save`, never a hand edit).

Onto each `spec:<leg>` MeasurementSpec it writes, from `assessment/instrument/RULE-*.yaml`:

* the plain-language dictionary fields the entry's `plain:` block carries (DN-016 §3), as
  `rf_question`, `rf_where_we_look`, `rf_what_client_does`, `rf_pass`, `rf_partial`, `rf_fail`,
  `rf_not_measured`, `rf_why_it_matters`, `rf_who_else`, `rf_rung_two_changes`;
* `rf_hypothesis` (the entry's full `question.text`), `rf_state`, and, where the entry carries
  them, `rf_plain_name` and `rf_fix_line`;
* `rf_requirements` — the verified quotes with their source ids (`expected_behavior.quotes`) —
  and `rf_standards_urls`, the receipted standards URLs cited by the entry that are not corpus
  documents (DN-015 §2: a `url:` source is a receipt, not a corpus id; recorded as a property,
  listed in the RESULT, never an `EVIDENCED_BY` edge).

For every corpus `doc_id` the entry cites (question.established_by, expected_behavior.sources,
test.recognized_method_sources, every branch's sources), an `EVIDENCED_BY` edge
`spec:<leg> -> doc:<doc_id>` is added if absent. `scripts/load_framework_graph.py` resolves it to
the KG-layer `Document {doc_id}` node (extended by this task to match a MeasurementSpec source,
not only an AssessmentIndicator). The write is purely additive, so `save` needs no `--force`. A
projection MUST follow (`scripts/load_framework_graph.py`), then
`tests/test_framework_projection_roundtrip.py`, or a Cypher answer over the framework labels is
stale (DD-057).

    /opt/anaconda3/bin/python3 scripts/apply_instrument_fields.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import framework_writeback as fw  # noqa: E402
import instrument as INS  # noqa: E402

SCRIPT = "scripts/apply_instrument_fields.py"
TASK = "cc_tasks/2026-10-15_readiness_diagnostic_package.md"

#: The entry's `plain:` keys, written as `rf_<key>` onto the spec. Every entry carries all of
#: them (the merge asserted it); the Part A check re-asserts non-empty on the graph side.
PLAIN_FIELDS = ["question", "where_we_look", "what_client_does", "pass", "partial", "fail",
                "not_measured", "why_it_matters", "who_else", "rung_two_changes"]

#: The readiness brief's short fields (`cc_tasks/2026-10-16_readiness_brief.md` Part A), authored
#: in a sidecar beside the entries so the reader-verified RULE-*.yaml are not edited for a
#: presentation field. Every leg carries all four; written as `rf_<key>`.
BRIEF_FIELDS_FILE = REPO / "assessment" / "instrument" / "brief_fields.yaml"
BRIEF_FIELDS = ["name_brief", "ask_plain", "tells_plain", "why_short"]


def load_brief_fields(path: Path = BRIEF_FIELDS_FILE) -> dict:
    """`{leg: {field: text}}` from the sidecar; `{}` when the file is absent (the write-back then
    behaves exactly as before it existed). A present file must cover every field it names."""
    if not path.is_file():
        return {}
    import yaml
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for leg, block in data.items():
        missing = [f for f in BRIEF_FIELDS if not str((block or {}).get(f) or "").strip()]
        if missing:
            raise SystemExit(f"FATAL: {path.name} {leg} is missing {missing}; nothing written")
    return data


def _corpus_ids(e: dict) -> list[str]:
    """Every corpus `doc_id` the entry cites, deduped, in first-seen order."""
    seen, out = set(), []

    def take(v):
        if not isinstance(v, list):
            return
        for s in v:
            if isinstance(s, dict) and "doc_id" in s and s["doc_id"] not in seen:
                seen.add(s["doc_id"])
                out.append(s["doc_id"])

    take((e.get("question") or {}).get("established_by"))
    take((e.get("expected_behavior") or {}).get("sources"))
    tm = (e.get("test") or {}).get("recognized_method_sources")
    take(tm if isinstance(tm, list) else None)
    for b in e.get("branches") or []:
        take(b.get("sources"))
    return out


def _standards_urls(e: dict) -> list[str]:
    seen, out = set(), []

    def take(v):
        if not isinstance(v, list):
            return
        for s in v:
            if isinstance(s, dict) and "url" in s and s["url"] not in seen:
                seen.add(s["url"])
                out.append(s["url"])

    take((e.get("question") or {}).get("established_by"))
    take((e.get("expected_behavior") or {}).get("sources"))
    tm = (e.get("test") or {}).get("recognized_method_sources")
    take(tm if isinstance(tm, list) else None)
    for b in e.get("branches") or []:
        take(b.get("sources"))
    return out


def _fix_line(e: dict) -> str | None:
    flc = e.get("fix_line_check") or {}
    if flc.get("verdict") == "rewritten":
        return flc.get("new_fix_line")
    if flc.get("verdict") == "consistent":
        return flc.get("fix_line")
    return None


def wanted(entries: list, brief: dict | None = None) -> dict:
    """`{spec_id: {props}}` and the list of `EVIDENCED_BY` edges the specs should carry."""
    props, edges = {}, []
    brief = brief or {}
    if brief:
        legs = {e["leg"] for e in entries}
        if set(brief) != legs:
            raise SystemExit(f"FATAL: {BRIEF_FIELDS_FILE.name} legs != entry legs: "
                             f"missing {sorted(legs - set(brief))}, extra {sorted(set(brief) - legs)}")
    for e in entries:
        sid = f"spec:{e['leg']}"
        plain = e.get("plain") or {}
        missing = [f for f in PLAIN_FIELDS if not str(plain.get(f) or "").strip()]
        if missing:
            raise SystemExit(f"FATAL: {e['rule_id']} has no plain block or is missing {missing}; "
                             "author it (DN-016 §3) before the write-back")
        p = {f"rf_{k}": plain[k] for k in PLAIN_FIELDS}
        if brief:
            p.update({f"rf_{k}": brief[e["leg"]][k] for k in BRIEF_FIELDS})
        p["rf_hypothesis"] = (e.get("question") or {}).get("text")
        p["rf_state"] = e.get("state")
        if e.get("plain_name"):
            p["rf_plain_name"] = e["plain_name"]
        fl = _fix_line(e)
        if fl:
            p["rf_fix_line"] = fl
        reqs = [{"source": q["source"], "quote": q["quote"]}
                for q in (e.get("expected_behavior") or {}).get("quotes") or []]
        # A JSON string, always, so the property is one shape on every spec (a flattened empty
        # list would otherwise key as `rf_requirements` while a non-empty list keys as
        # `rf_requirements_json`). A `specified` check cites quoted requirements; a
        # project-defined check with `source: none` carries "[]", which is correct, not missing.
        p["rf_requirements"] = json.dumps(reqs, ensure_ascii=False)
        urls = _standards_urls(e)
        if urls:
            p["rf_standards_urls"] = urls
        props[sid] = p
        for did in _corpus_ids(e):
            edges.append({"from": sid, "type": "EVIDENCED_BY", "to": f"doc:{did}",
                          "properties": {"doc_id": did}})
    return {"props": props, "edges": edges}


def apply(g: dict, w: dict) -> dict:
    by_id = {n["id"]: n for n in g["nodes"]}
    unmatched = sorted(sid for sid in w["props"] if sid not in by_id)
    if unmatched:
        raise SystemExit(f"FATAL: entries name specs the record does not hold: {unmatched}; nothing written")
    changed = {"specs": [], "edges_added": []}
    for sid, p in w["props"].items():
        # `rf_requirements` is now a JSON string; drop the flattened list key an earlier
        # revision of this script may have left (a node-property change, not a node/edge/counts
        # drop, so `save` permits it without --force).
        by_id[sid]["properties"].pop("rf_requirements_json", None)
        by_id[sid]["properties"].update(p)
        changed["specs"].append(sid)
    have = {(e["from"], e["type"], e["to"]) for e in g["edges"]}
    for e in w["edges"]:
        k = (e["from"], e["type"], e["to"])
        if k not in have:
            g["edges"].append(e)
            have.add(k)
            changed["edges_added"].append(k)
    return changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--task", default=TASK, help="the task file the write-back event names")
    fw.add_force_args(ap)
    a = ap.parse_args(argv)
    cfg = INS.load_config()
    entries = INS.load_entries()
    problems = INS.check(cfg, entries)
    if problems:
        raise SystemExit("FATAL: the entries do not pass `instrument.py check`; nothing written:\n  "
                         + "\n  ".join(problems))
    brief = load_brief_fields()
    w = wanted(entries, brief)
    g = fw.load()
    if g is None:
        raise SystemExit("FATAL: framework record not found")
    rep = apply(g, w)
    urls = sorted({u for p in w["props"].values() for u in p.get("rf_standards_urls", [])})
    ev = fw.save(g, script=SCRIPT, task=a.task,
                 changes={"applied": "reader-facing instrument fields and spec EVIDENCED_BY edges (DN-016 ruling 4)"
                                     + (" plus the readiness brief fields " + ", ".join("rf_" + f for f in BRIEF_FIELDS) if brief else ""),
                          "specs_updated": sorted(w["props"]), "evidenced_by_edges_added": len(rep["edges_added"]),
                          "standards_urls_as_property": urls},
                 dry_run=a.dry_run, **fw.force_kwargs(a))
    print(json.dumps({"specs_updated": len(rep["specs"]), "evidenced_by_edges_added": len(rep["edges_added"]),
                      "standards_urls_recorded_as_property": urls, "written": ev["written"],
                      "unchanged": ev.get("unchanged", False), "event_id": ev.get("event_id"),
                      "framework_sha256": ev["framework_sha256"], "delta": ev["delta_summary"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
