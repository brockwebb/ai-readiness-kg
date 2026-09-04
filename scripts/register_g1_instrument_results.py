#!/usr/bin/env python3
"""Register the G1 instrument-at-freeze numbers as Seldon Results (task
2026-09-03_g1_freeze_calibration_redefinition_findings, step 3). **Zero model calls.**

The findings memo is written under the rule that no number appears in it as a literal — every
one resolves to a registered Result through `{{result:NAME:value}}`. The v2 measurement numbers
were registered by `scripts/register_g1_v2_results.py`; the numbers that DESCRIBE the frozen
instrument (how many propositions and passages per split and surface type, how many calls the
pre-registered schedule holds, what each declared run settled on the spend ledger) were not,
so §2 of the memo would have had to carry literals. They are registered here instead, computed
from the fixture files, the pre-registered schedule and the spend ledger rather than typed:

    g1_v2_instrument_fixture_{dev,holdout}_{propositions,passages}
    g1_v2_instrument_fixture_{dev,holdout}_{surface_type}_propositions
    g1_v2_instrument_schedule_{dev,holdout,control}_{steps,new_calls}
    g1_v2_instrument_schedule_new_calls_total / _tokens_at_floor
    g1_v2_instrument_spend_{run_id}_settled  and  g1_v2_instrument_spend_task_total
    g1_v1_holdout_fresh_gate_unparseable_share, g1_v2_holdout_gate_unparseable_share

    /opt/anaconda3/bin/python3 scripts/register_g1_instrument_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tomllib
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "scripts"))

from harness.g1_fixtures import load_fixture_set  # noqa: E402

TASK = "cc_tasks/2026-09-03_g1_freeze_calibration_redefinition_findings.md"
FIX = REPO / "assessment" / "tests" / "fixtures" / "g1" / "v2"
SCHEDULE = REPO / "assessment" / "config" / "g1_v2_schedule.toml"
LEDGER = REPO / "state" / "spend_ledger.jsonl"
RUNS = ("g1_eval_v2_dev_2026-09-03", "g1_eval_v2_dev_2026-09-03_b",
        "g1_eval_v2_holdout_2026-09-03", "g1_eval_v2_control_2026-09-03")
FLOOR = 34000            # controls.yaml spend floor for the g1_eval call class (DD-022)

BASE = ("G1 EVAL v2 instrument at freeze (parser g1-parse-v2, scorer g1-score-v2, prompt epoch "
        "g1-v2-2026-09-03, consumer claude-opus-5), frozen for the January pilot by DD-036; "
        f"registered by scripts/register_g1_instrument_results.py for {TASK}")

#: The registered DataFiles each group of numbers is read from, cited as `--data-name` so the
#: Results carry `computed_from` instead of naming their source only in prose. The first run of
#: this script passed no provenance flags at all and its 29 Results had to be backfilled
#: afterwards (cc_tasks/2026-09-04_result_migration_completion.md step 6); citing the source at
#: registration is what stops that recurring.
FIXTURE_DATA = {"dev": "g1_v2_fixture_propositions_dev",
                "holdout": "g1_v2_fixture_propositions_holdout"}
SCHEDULE_DATA = "g1_v2_schedule"
LEDGER_DATA = "spend_ledger"
GATE_DATA = {"g1_v1_holdout_fresh_gate_unparseable_share": "g1_v1_holdout_fresh_reviewed",
             "g1_v2_holdout_gate_unparseable_share": "g1_v2_holdout_reviewed"}


def fixture_numbers() -> list:
    out = []
    for split, path in (("dev", FIX / "propositions.yaml"), ("holdout", FIX / "propositions_holdout.yaml")):
        fs = load_fixture_set(path)
        props = fs.propositions
        out.append((f"g1_v2_instrument_fixture_{split}_propositions", len(props),
                    f"propositions in {path.relative_to(REPO)} (v2 product-surface fixtures)",
                    FIXTURE_DATA[split]))
        out.append((f"g1_v2_instrument_fixture_{split}_passages", len({p.passage_id for p in props}),
                    f"distinct passages in {path.relative_to(REPO)}", FIXTURE_DATA[split]))
        for st, n in sorted(Counter(p.surface_type for p in props).items()):
            out.append((f"g1_v2_instrument_fixture_{split}_{st}_propositions", n,
                        f"propositions of surface_type {st} in {path.relative_to(REPO)}",
                        FIXTURE_DATA[split]))
    return out


def schedule_numbers() -> list:
    with SCHEDULE.open("rb") as fh:
        steps = tomllib.load(fh)["steps"]
    out, total_new, total_steps = [], 0, 0
    for split in ("dev", "holdout"):
        rows = [s for s in steps if s["split"] == split]
        # `reusable` marks a slot whose prompt text is byte-identical to a v0-epoch slot that
        # already has a response for the pinned consumer (DD-035 D12): it costs nothing.
        new_calls = [s for s in rows if not s.get("reusable")]
        total_new += len(new_calls)
        total_steps += len(rows)
        out.append((f"g1_v2_instrument_schedule_{split}_steps", len(rows),
                    f"steps for split {split} in {SCHEDULE.relative_to(REPO)} (pre-registered before any call)"))
        out.append((f"g1_v2_instrument_schedule_{split}_new_calls", len(new_calls),
                    f"steps for split {split} with no reusable byte-identical v0-epoch slot"))
    control = [s for s in steps if s["split"] == "holdout"]
    total_new += len(control)
    total_steps += len(control)
    out.append(("g1_v2_instrument_schedule_control_steps", len(control),
                "control-arm steps (D13: the holdout grid under the control consumer)"))
    out.append(("g1_v2_instrument_schedule_control_new_calls", len(control),
                "control-arm calls (no v0-epoch evidence exists for the control consumer, so none reuse)"))
    out.append(("g1_v2_instrument_schedule_new_calls_total", total_new,
                "new consumer calls across dev, holdout and the control arm, after v0-epoch reuse"))
    out.append(("g1_v2_instrument_schedule_tokens_at_floor", total_new * FLOOR,
                f"schedule cost at the DD-022 g1_eval estimate floor of {FLOOR} tokens per call"))
    out.append(("g1_v2_instrument_schedule_calls_without_reuse", total_steps,
                "consumer calls the same schedule would have cost with no byte-identical reuse"))
    out.append(("g1_v2_instrument_schedule_tokens_at_floor_without_reuse", total_steps * FLOOR,
                f"that counterfactual at the {FLOOR}-token floor (against the task cap of 8,000,000)"))
    # every schedule number is read from the one pre-registered schedule file
    return [r if len(r) == 4 else (*r, SCHEDULE_DATA) for r in out]


def spend_numbers() -> list:
    settled: Counter = Counter()
    for line in LEDGER.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)          # flat rows: {"record": "reserve"|"settle"|…, "run_id": …}
        if r.get("record") != "settle" or r.get("run_id") not in RUNS:
            continue
        settled[r["run_id"]] += int(r.get("actual_tokens") or 0)
    out = [(f"g1_v2_instrument_spend_{run}_settled", settled[run],
            f"tokens settled on state/spend_ledger.jsonl by run {run} (declared ceiling 2,000,000)")
           for run in RUNS]
    out.append(("g1_v2_instrument_spend_task_total", sum(settled.values()),
                "tokens settled across the four declared v2 runs (task cap 8,000,000)", LEDGER_DATA))
    # every spend number is read from the shared ledger
    return [r if len(r) == 4 else (*r, LEDGER_DATA) for r in out]


def gate_numbers() -> list:
    """The two readiness-gate shares. Each gate is stated as a share against a 0.10 threshold but
    only its numerator and denominator were registered, so the memo could not cite the share
    itself. Computed from the reviewed results files, not retyped."""
    out = []
    for name, path, note in (
        ("g1_v1_holdout_fresh_gate_unparseable_share",
         REPO / "assessment" / "results" / "g1_v1_holdout_fresh_reviewed.json",
         "v1 readiness gate restated on the 35 responses elicited after the v1 freeze (DD-035 item 7)"),
        ("g1_v2_holdout_gate_unparseable_share",
         REPO / "assessment" / "results" / "g1_v2_holdout_reviewed.json",
         "v2 readiness gate on the sealed holdout under the pinned consumer (DD-035 item 8)"),
    ):
        cell = json.loads(path.read_text(encoding="utf-8"))["g1"]["observed"]["all"]
        n = cell.get("n")
        out.append((name, round(cell["n_unparseable"] / n, 6),
                    f"{note}: unparseable share = n_unparseable / n from {path.relative_to(REPO)} "
                    f"(threshold 0.10, pre-registered; reported before any other number)",
                    GATE_DATA[name]))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--skip", type=int, default=0)
    a = ap.parse_args(argv)
    rows = fixture_numbers() + schedule_numbers() + spend_numbers() + gate_numbers()
    if a.dry_run:
        for name, value, note, data in rows:
            print(f"{name}\t{value}\t{data}\t{note}")
        print(len(rows), "Results")
        return 0
    ok = 0
    rows = rows[a.skip:]
    for name, value, note, data in rows:
        cmd = ["seldon", "result", "register", "--value", str(value), "--name", name,
               "--units", name, "--description", f"{BASE}: {note}", "--data-name", data]
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        else:
            print("FAILED:", name, r.stderr.strip()[-200:])
    print(f"registered {ok}/{len(rows)} instrument Results")
    return 0 if ok == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
