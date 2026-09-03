#!/usr/bin/env python3
"""Re-score persisted G1 evidence under the CURRENT parser + scorer as FAMILY records (task
2026-09-03_g1_eval_v2 steps 5a and 6).

Evidence is the raw model exchange on disk; scoring is a pure function of it. This walks
evidence directories (v0/v1 evidence in assessment/evidence/g1[/holdout]; v2 evidence in
assessment/evidence/g1/v2/<dev|holdout|control>), scores every response against its
proposition(s) with the working-tree parser (`parser_version`) and scorer (`scorer_version`),
and writes ONE new results file: family records with per-form verdicts and D11 covariates,
the rollup G1 block (family cells, surface x compression cells), and the D14 expectation
tests. Existing results files are never edited.

    /opt/anaconda3/bin/python3 scripts/rescore_g1_v2.py --evidence DIR [--evidence DIR ...] \
        --out assessment/results/g1_v2_<name>.json [--split dev|holdout|all] [--consumer-model claude-opus-5] \
        [--control-model claude-haiku-4-5-20251001] [--v2-only | --v1-only] [--run-id R]

`--split` selects propositions by their v2 split (by passage: the twelve shared v1 passages
are dev). A v0/v1 evidence file (epoch g1-v0-2026-09-02) is scored at compression `none`.
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
sys.path.insert(0, str(REPO / "scripts"))

from harness.g1_expectations import expectations_v2  # noqa: E402
from harness.probes import _g1_parse  # noqa: E402
from harness.probes.base import Elicited  # noqa: E402
from harness.probes.g1_preservation import SCORER_VERSION, PreservationProbe, load_prompts  # noqa: E402
from harness.rollup import g1_block  # noqa: E402
from gen_g1_schedule import v2_split  # noqa: E402
from run_g1_v2 import load_all_fixtures  # noqa: E402

TASK = "cc_tasks/2026-09-03_g1_eval_v2_product_surfaces_compression.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--evidence", action="append", required=True, help="evidence directory (repeatable)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--split", choices=["dev", "holdout", "all"], default="all")
    ap.add_argument("--consumer-model", default="claude-opus-5")
    ap.add_argument("--control-model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--v2-only", action="store_true", help="only propositions from the v2 (product-surface) fixtures")
    ap.add_argument("--v1-only", action="store_true", help="only propositions from the v1 (prose_labeled) fixtures")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--name", action="append", default=None, help="only evidence files with these basenames")
    a = ap.parse_args(argv)

    props, passages, meta = load_all_fixtures()
    passage_split, prop_split, shared = v2_split()
    probe = PreservationProbe(load_prompts(REPO / "assessment" / "config" / "g1_prompts.toml"), REPO / "assessment" / "evidence" / "g1")

    def wanted(pid: str) -> bool:
        split, _, origin = prop_split[pid]
        if a.split != "all" and split != a.split:
            return False
        if a.v2_only and not origin.startswith("v2"):
            return False
        if a.v1_only and not origin.startswith("v1"):
            return False
        return True

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
            comp = rec.get("compression_level") or "none"
            if rec["mode"] == "indirect":
                targets = passages.get(rec.get("passage_id"), [])
                only_class = None
            else:
                targets = [props[rec["proposition_id"]]]
                only_class = rec.get("qualifier_class")
            new = []
            for p in targets:
                if not wanted(p.id):
                    continue
                el_p = Elicited(**{**el.__dict__, "proposition_id": p.id})
                fam = None
                if only_class:
                    from harness.records import FAMILY_OF
                    fam = FAMILY_OF[only_class]
                new.extend(probe.records(el_p, p, only_family=fam, compression=comp if rec["mode"] == "indirect" else "none",
                                         passage_meta=meta.get(p.passage_id), siblings=passages[p.passage_id]))
            records.extend(new)
            rel = str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)
            files.append({"evidence_path": rel, "mode": rec["mode"], "model_id": rec["model_id"], "prompt_epoch": rec["prompt_epoch"],
                          "compression_level": comp if rec["mode"] == "indirect" else None, "n_records": len(new)})
    out = {"task": TASK, "run_id": a.run_id, "parser_version": _g1_parse.PARSER_VERSION, "scorer_version": SCORER_VERSION,
           "split": a.split, "v2_only": a.v2_only, "v1_only": a.v1_only, "evidence_dirs": a.evidence, "scored_at": _now(),
           "shared_v1_passages_assigned_to_dev": shared,
           "n_evidence_files": len(files), "files": files,
           "records": [dict(r.to_dict(), genuine_loss=None) for r in records],
           "g1": g1_block(records),
           "expectations_v2": expectations_v2(records, consumer_model=a.consumer_model, control_model=a.control_model)}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    all_ = out["g1"]["observed"]["all"]
    print(f"{_g1_parse.PARSER_VERSION}/{SCORER_VERSION}: {len(files)} evidence files -> {len(records)} family records "
          f"({out['g1']['observed']['n_qualifiers']} qualifier forms); scored {all_['n_scored']}, unparseable {all_['n_unparseable']}, "
          f"L3+ {all_['preserved']}, rate {all_['preservation_rate']} -> {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
