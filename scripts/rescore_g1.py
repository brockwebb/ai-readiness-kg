#!/usr/bin/env python3
"""Re-score persisted G1 evidence under the CURRENT parser (task 2026-09-03 steps 4.4 and 6).

Evidence is the raw model exchange on disk; scoring is a pure function of it. This script
walks evidence files, scores each against its proposition(s) with the parser in the working
tree, and writes a results file stamped with `parser_version` (harness.probes._g1_parse
.PARSER_VERSION, or --stamp to override when re-scoring an older rule set for a paired
comparison). Existing results files are never edited; each run writes a new file.

    python3 scripts/rescore_g1.py --evidence assessment/evidence/g1 [--evidence ...] \
        --out assessment/results/g1_v1_<name>.json [--split dev|holdout|all] [--stamp g1-parse-v0]

The results file carries: records, the rollup G1 block, the D8 expectation tests, the
per-evidence-file `normalised_text` (when the parser exposes it) and a `genuine_loss`
slot per record, filled by the reviewer step (scripts/g1_review_losses.py) — empty here.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO))

from harness.g1_fixtures import load_fixture_set  # noqa: E402
from harness.probes import _g1_parse  # noqa: E402
from harness.probes.base import Elicited  # noqa: E402
from harness.probes.g1_preservation import PreservationProbe, load_prompts  # noqa: E402
from harness.rollup import g1_block  # noqa: E402
from run_g1_pilot import expectation_tests  # noqa: E402

FIX = REPO / "assessment" / "tests" / "fixtures" / "g1"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--evidence", action="append", required=True, help="evidence directory (repeatable)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--split", choices=["dev", "holdout", "all"], default="all")
    ap.add_argument("--stamp", default=None, help="override PARSER_VERSION (paired v0 re-score)")
    ap.add_argument("--run-id", default=None, help="run id recorded on the results file")
    ap.add_argument("--name", action="append", default=None,
                    help="only evidence files with these basenames (repeatable; default: all in the directory)")
    ap.add_argument("--task", default="cc_tasks/2026-09-03_g1_eval_v1_parser_fullgrid_errata.md",
                    help="task reference recorded on the results file")
    ap.add_argument("--fresh-only", action="store_true",
                    help="task 2026-09-03 v2 step 1 (seal recompute): score ONLY the evidence files in the given "
                         "directories — never a parent-directory slot — and record fresh_only=true on the file")
    a = ap.parse_args(argv)
    if a.stamp:
        _g1_parse.PARSER_VERSION = a.stamp
        import harness.probes.g1_preservation as gp
        gp.PARSER_VERSION = a.stamp
    stamp = a.stamp or _g1_parse.PARSER_VERSION
    dev = load_fixture_set(FIX / "propositions.yaml")
    hold = load_fixture_set(FIX / "propositions_holdout.yaml")
    props = {p.id: ("dev", p) for p in dev.propositions}
    props.update({p.id: ("holdout", p) for p in hold.propositions})
    by_passage = {}
    for which, p in props.values():
        by_passage.setdefault(p.passage_id, []).append(p)
    probe = PreservationProbe(load_prompts(REPO / "assessment" / "config" / "g1_prompts.toml"), REPO / "assessment" / "evidence" / "g1")

    records, files = [], []
    for d in a.evidence:
        for path in sorted(Path(d).glob("*.json")):
            if a.name and path.name not in set(a.name):
                continue
            rec = json.loads(path.read_text(encoding="utf-8"))
            el = Elicited(proposition_id=rec["proposition_id"], mode=rec["mode"], prompt=rec["prompt"],
                          response_text=rec["response_text"], model_id=rec["model_id"],
                          prompt_epoch=rec["prompt_epoch"], timestamp=rec["timestamp"], evidence_path=str(path),
                          usage=rec.get("usage") or {})
            if rec["mode"] == "indirect":
                targets = by_passage.get(rec.get("passage_id"), [])
                cls = None
            else:
                targets = [props[rec["proposition_id"]][1]]
                cls = rec.get("qualifier_class")
            new = []
            for p in targets:
                if a.split != "all" and props[p.id][0] != a.split:
                    continue
                el_p = Elicited(**{**el.__dict__, "proposition_id": p.id})
                new.extend(probe.records(el_p, p, only_class=cls))
            records.extend(new)
            rel = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
            files.append({"evidence_path": rel, "mode": rec["mode"],
                          "n_records": len(new),
                          "normalised_text": getattr(_g1_parse, "normalise_text", lambda t: None)(rec["response_text"])})
    out = {"task": a.task, "run_id": a.run_id,
           "parser_version": stamp, "split": a.split, "evidence_dirs": a.evidence, "fresh_only": bool(a.fresh_only),
           "scored_at": _now(),
           "n_evidence_files": len(files), "files": files,
           "records": [dict(r.to_dict(), genuine_loss=None) for r in records],
           "g1": g1_block(records), "expectations": expectation_tests(records)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    all_ = out["g1"]["observed"]["all"]
    print(f"{stamp}: {len(files)} evidence files -> {len(records)} records; scored {all_['n_scored']}, "
          f"unparseable {all_['n_unparseable']}, L3+ {all_['preserved']}, rate {all_['preservation_rate']} "
          f"-> {a.out}")
    return 0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
