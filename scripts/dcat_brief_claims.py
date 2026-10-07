#!/usr/bin/env python3
"""Register the brief's claims in the evidence map. **Zero spend, no network.**

`cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md` decision 8, under DN-009
decision 2 (`docs/design/2026-10-02_DN-009_deck_rejected_evidence_map_first.md`): one claim per
row of the R6 table and one per yes-or-no answer, each with its evidence class and locators, in
`docs/evidence/claims.yaml`, so the long report inherits them.

The file's generator, `scripts/build_evidence_map.py`, owns the entries whose `source_task` is
its own task and carries every other entry through byte for byte, by id. This script owns the
entries whose `source_task` is THIS task, keyed `dcat_brief.*`: it reuses an id already on disk
for a key and gives a new key the next id after the highest in the file, the generator's own
rule. The rest of the file is re-serialised with the generator's dumper settings; the script
refuses to write if that changes a single byte of any entry it does not own.

Evidence class (DN-009 d2): a row with all three answers validated is `record` (established by
the documents, each cited with its locator and the span the validator quoted); a row the
validator left without an outcome is `unsupported`. Every numeral in a claim's text is on its
`numbers` list with its source, as the map's tests require.

    /opt/anaconda3/bin/python3 scripts/dcat_brief_claims.py [--check]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import yaml  # noqa: E402

import build_evidence_map as E  # noqa: E402
import dcat_faq_evidence as EV  # noqa: E402

TASK = "cc_tasks/2026-10-07_DCAT-004_v2_plain_language_brief_and_verdict.md"
ANSWERS = EV.BRIEF_OUT / "answers.json"
OUTCOME_WORDS = {"A": "asked for, and included as Mandatory or Recommended",
                 "B": "asked for, and left Optional, deferred, dropped or left out",
                 "C": "not asked for, though the standards say a catalog needs it (the void)",
                 "D": "asked for, but the standards say there is a better way to carry it (the mismatch)",
                 "E": "not determinable from the public record"}


def dump(doc: dict) -> str:
    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100, default_flow_style=False)


def manifest_add_lines() -> dict:
    """doc_id -> `events/batch-NNN.jsonl:<line>` of its manifest_add, the locator form the
    map's prior-art claims use for a document."""
    out = {}
    for p in sorted((REPO / "events").glob("batch-*.jsonl")):
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if '"manifest_add"' not in line:
                continue
            ev = json.loads(line)
            if ev.get("event_type") == "manifest_add":
                d = ev.get("doc_id") or (ev.get("payload") or {}).get("doc_id")
                out.setdefault(d, f"{p.relative_to(REPO).as_posix()}:{n}")
    return out


def numbers_for(text: str, sources: dict) -> list:
    out = []
    for x in dict.fromkeys(E.numerals(text)):
        if x not in sources:
            raise SystemExit(f"FATAL: numeral {x!r} in {text!r} has no stated source")
        out.append({"value": x, "source": sources[x]})
    return out


def evidence_rows(row: dict, ev: dict, adds: dict) -> list:
    by = {it["id"]: it for it in ev["items"]}
    out = []
    for x in row["items"]:
        if not x["kept"] or x["kind"] != "SENTENCE":
            if x["kept"] and x["kind"] == "NOT_KNOWN":
                out.append({"kind": "query", "id": "dcat_brief.absence_check",
                            "locator": f"reports/dcat_us_3_brief/evidence/need_{row['need_id']}_absence*.json",
                            "note": f"{x['part']}: {x['sentence']}"})
            continue
        for e in x["evidence"]:
            it = by[e]
            loc = it["locator"]
            where = ", ".join(f"{k} {v}" for k, v in loc.items() if k != "lines") if isinstance(loc, dict) else str(loc)
            doc = it["doc_id"]
            out.append({"kind": "document", "id": doc,
                        "locator": adds.get(doc) or f"reports/dcat_us_3_brief/evidence/need_{row['need_id']}.json#{e}",
                        "where": f"{it.get('graph')}: {where}",
                        "quote": (x.get("support_span") or "")[:300],
                        "note": f"{x['part']} (validated: {x.get('verdict')}, responsive {x.get('responsive')})"})
    return out


def claims(answers: dict, bcfg: dict) -> list:
    adds = manifest_add_lines()
    out = []
    src = {str(n["id"]): "the need's number in reports/dcat_us_3_brief/brief_config.yaml" for n in bcfg["needs"]}
    for nid in sorted(answers["rows"], key=int):
        r = answers["rows"][nid]
        ev = json.loads((EV.BRIEF_EVIDENCE_DIR / f"need_{nid}.json").read_text(encoding="utf-8"))
        def code(v):
            return f"`{v}`" if v else "not confirmed"
        if r["outcome"] == "unassigned":
            text = (f"Statistical need `{nid}` (`{r['need']}`) has no outcome under the `DN-011-R6` rule: "
                    f"{r['reason']}.")
            status = "unsupported"
        else:
            where = (f"is in outcome {r['outcome']}, {OUTCOME_WORDS[r['outcome']]}" if r["outcome"] != "unplaced"
                     else "is in outcome " + " or ".join(x for x in r["open"] if x != "outside_rule")
                     + ", the letters its validated answers leave open")
            text = (f"Statistical need `{nid}` (`{r['need']}`) {where}: asked {code(r['asked'])}, landed "
                    f"{code(r['landed'])}{' (deferred)' if r['deferred'] else ''} as served `2026-10-05`, "
                    f"literature {code(r['literature'])} (`DN-011-R6`).")
            status = "record"
        evid = evidence_rows(r, ev, adds) + [{"kind": "query", "id": "dcat_brief.r6",
                                              "locator": f"reports/dcat_us_3_brief/answers.json#rows.{nid}"}]
        out.append({"key": f"dcat_brief.r6.need_{nid}", "question": "DCAT-004 R6", "text": text,
                    "status": status, "evidence": evid, "numbers": numbers_for(text, src)})
    for name, v in answers["verdict"].items():
        label = {"findability": "findability", "fitness_for_use": "fitness-for-use assessment"}[name]
        rows = ", ".join(f"`{i}`" for i in v["rows"])
        lets = {str(k): x for k, x in v["open"].items()}
        text = (f"For statistical uses, DCAT-US `3.0` delivers {label}: `{v['answer']}`"
                f"{'' if v['determined'] else ' (not determined: the open placements give different answers)'}, "
                f"computed by the `DN-011-R7` rule from table rows {rows} (outcomes "
                + ", ".join(f"`{i}`: {' or '.join(x for x in lets[str(i)] if x != 'outside_rule')}" for i in v["rows"])
                + ").")
        out.append({"key": f"dcat_brief.r7.{name}", "question": "DCAT-004 R7", "text": text,
                    "status": "record",
                    "evidence": [{"kind": "query", "id": "dcat_brief.r7",
                                  "locator": "reports/dcat_us_3_brief/answers.json#verdict"}]
                    + [{"kind": "query", "id": "dcat_brief.r6",
                        "locator": f"reports/dcat_us_3_brief/answers.json#rows.{i}"} for i in v["rows"]],
                    "numbers": numbers_for(text, src)})
    return out


def render(answers: dict, bcfg: dict) -> str:
    text = E.CLAIMS.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    if dump(doc) != text:
        raise SystemExit("FATAL: claims.yaml does not round-trip through the generator's dumper; "
                         "refusing to rewrite it")
    others = [c for c in doc["claims"] if c.get("source_task") != TASK]
    held = {c["key"]: c["id"] for c in doc["claims"] if c.get("source_task") == TASK and c.get("key")}
    nxt = max(int(c["id"][3:]) for c in doc["claims"]) + 1
    mine = []
    for c in claims(answers, bcfg):
        cid = held.get(c["key"])
        if cid is None:
            cid, nxt = f"CL-{nxt:03d}", nxt + 1
        mine.append({"id": cid, **c, "source_task": TASK})
    allc = {c["id"]: c for c in others}
    clash = {c["id"] for c in mine} & set(allc)
    if clash:
        raise SystemExit(f"FATAL: ids {sorted(clash)} are held by another task's claims")
    allc.update({c["id"]: c for c in mine})
    doc["claims"] = [allc[k] for k in sorted(allc, key=lambda x: int(x[3:]))]
    out = dump(doc)
    before = {c["id"]: dump(c) for c in others}
    after = {c["id"]: dump(c) for c in yaml.safe_load(out)["claims"] if c.get("source_task") != TASK}
    if before != after:
        raise SystemExit("FATAL: re-serialising changed an entry this script does not own")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args(argv)
    answers = json.loads(ANSWERS.read_text(encoding="utf-8"))
    bcfg = yaml.safe_load(EV.BRIEF_CONFIG.read_text(encoding="utf-8"))
    out = render(answers, bcfg)
    if a.check:
        ok = E.CLAIMS.read_text(encoding="utf-8") == out
        print(f"docs/evidence/claims.yaml: {'no drift' if ok else 'DRIFT'}")
        return 0 if ok else 1
    E.CLAIMS.write_text(out, encoding="utf-8")
    d = yaml.safe_load(out)
    print(json.dumps({c["id"]: c["key"] for c in d["claims"] if c.get("source_task") == TASK}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
