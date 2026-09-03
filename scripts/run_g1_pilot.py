#!/usr/bin/env python3
"""G1 EVAL pilot runner (task 2026-09-02_g1_eval_probe_family_v0 step 6).

Walks the PRE-REGISTERED schedule in assessment/config/g1_pilot.toml — indirect calls per
passage, direct calls per (proposition, qualifier class) — under ONE pinned model
(assessment/config/g1_consumer.toml), through the repo choke point
(kg/extraction/model_stub.invoke: DD-007 OAuth-only gate, DD-022 reserve-before-dispatch,
invariant-5 model-identity gate). Evidence is written BEFORE anything is scored
(assessment/evidence/g1/<proposition>.<mode>[.<class>].<prompt_epoch>.<model_id>.json), then
each elicitation is scored deterministically (probes/g1_preservation.py) into EvalResults.

The run is declared on the shared spend ledger with the task's stated ceiling
(`--ceiling-tokens`, REQUIRED). A refusal is a clean stop (exit 0): the schedule prefix
reached is the pilot, and the report says how far it got. A dry run (`--dry-run`) renders
every prompt and reports the call count and the ceiling the full schedule would need at the
configured call-class floor, spending nothing.

    /opt/anaconda3/bin/python3 scripts/run_g1_pilot.py --ceiling-tokens 200000 [--run-id R] [--dry-run] [--max-calls N]

Outputs: assessment/results/g1_pilot_<run_id>.json (records + rollup G1 block + schedule
walk + pre-registered expectation tests E1–E3 / H1–H2), and a printed report.
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ASSESSMENT = REPO / "assessment"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ASSESSMENT))

from harness.consumers import ClaudeCLIConsumer, load_consumer_config  # noqa: E402
from harness.g1_fixtures import load_fixture_set  # noqa: E402
from harness.probes.g1_preservation import PreservationProbe, load_prompts  # noqa: E402
from harness.records import UNPARSEABLE, Level  # noqa: E402
from harness.rollup import g1_block, wilson_interval  # noqa: E402
from kg import spend  # noqa: E402
from kg.extraction import model_stub  # noqa: E402

CONFIG = ASSESSMENT / "config"
FIXTURES = ASSESSMENT / "tests" / "fixtures" / "g1"
EVIDENCE = ASSESSMENT / "evidence" / "g1"
RESULTS = ASSESSMENT / "results"
TASK = "cc_tasks/2026-09-02_g1_eval_probe_family_v0.md"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_schedule(path: Path) -> list:
    with path.open("rb") as fh:
        d = tomllib.load(fh)
    steps = d.get("steps")
    if not steps:
        raise SystemExit(f"FATAL: no [[steps]] in {path}")
    for i, s in enumerate(steps):
        if s.get("kind") == "indirect" and not s.get("passage"):
            raise SystemExit(f"FATAL: step {i} indirect without passage")
        if s.get("kind") == "direct" and not (s.get("proposition") and s.get("qualifier")):
            raise SystemExit(f"FATAL: step {i} direct without proposition/qualifier")
        if s.get("kind") not in ("indirect", "direct"):
            raise SystemExit(f"FATAL: step {i} unknown kind {s.get('kind')!r}")
    return steps


def _fixtures():
    dev = load_fixture_set(FIXTURES / "propositions.yaml")
    hold = load_fixture_set(FIXTURES / "propositions_holdout.yaml")
    props = {p.id: ("dev", p) for p in dev.propositions}
    props.update({p.id: ("holdout", p) for p in hold.propositions})
    passages = {}
    for which, fs in (("dev", dev), ("holdout", hold)):
        for p in fs.propositions:
            passages.setdefault(p.passage_id, []).append(p)
    return props, passages


def _rate(records, pred):
    sel = [r for r in records if pred(r) and r.outcome != UNPARSEABLE]
    k = sum(1 for r in sel if r.level >= Level.PRESERVED_TRANSFORMED)
    lo, hi = wilson_interval(k, len(sel))
    return {"n": len(sel), "preserved": k, "rate": (round(k / len(sel), 6) if sel else None), "wilson95": [lo, hi]}


def expectation_tests(records) -> dict:
    """E1–E3, H1–H2 as pre-registered in the task (design D8). Each reports supported /
    not supported / underpowered with the counts; 'underpowered' when a cell has n < 5 or
    the intervals overlap so that neither direction is excluded."""
    def verdict(a, b, direction_expected):
        if a["n"] < 5 or b["n"] < 5 or a["rate"] is None or b["rate"] is None:
            return "underpowered"
        lo_a, hi_a = a["wilson95"]
        lo_b, hi_b = b["wilson95"]
        if direction_expected == "a<b":
            if hi_a < lo_b:
                return "supported"
            if lo_a > hi_b:
                return "not supported"
            return "underpowered"
        return "underpowered"

    scored = [r for r in records if r.outcome != UNPARSEABLE]
    ind = _rate(records, lambda r: r.mode == "indirect")
    dire = _rate(records, lambda r: r.mode == "direct")
    e1 = {"statement": "indirect loses qualifiers at a higher rate than direct (Du 2026)",
          "indirect": ind, "direct": dire, "verdict": verdict(ind, dire, "a<b")}
    l1 = sum(1 for r in scored if r.level == Level.OMITTED)
    l0 = sum(1 for r in scored if r.level == Level.CORRUPTED)
    e2 = {"statement": "omission (L1) exceeds corruption (L0) (Du 2026; Ansari 2026)",
          "L1": l1, "L0": l0, "n_scored": len(scored),
          "verdict": ("underpowered" if l1 + l0 < 5 else ("supported" if l1 > l0 else "not supported"))}
    non_omission = [r for r in scored if r.level in (Level.CORRUPTED, Level.DEGRADED_VERBAL)]
    fc = {}
    for r in non_omission:
        fc[r.failure_class] = fc.get(r.failure_class, 0) + 1
    top = max(fc.items(), key=lambda kv: kv[1])[0] if fc else None
    e3 = {"statement": "among non-omission failures, form_shift (L2) is the most frequent (van der Bles 2019)",
          "failure_classes": fc, "most_frequent": top,
          "verdict": ("underpowered" if len(non_omission) < 5 else ("supported" if top == "form_shift" else "not supported"))}
    thin = _rate(records, lambda r: r.qualifier_class in ("CV", "RELIABILITY_FLAG", "SUPPRESSION"))
    core = _rate(records, lambda r: r.qualifier_class in ("MOE", "CI"))
    h1 = {"statement": "CV / RELIABILITY_FLAG / SUPPRESSION are lost at a higher rate than MOE / CI (hypothesis, no prior art)",
          "cv_flag_supp": thin, "moe_ci": core, "verdict": verdict(thin, core, "a<b")}
    vint = _rate(records, lambda r: r.qualifier_class == "VINTAGE")
    numeric = _rate(records, lambda r: r.qualifier_class in ("MOE", "CI", "SE", "CV", "DP_NOISE"))
    vint_omit = sum(1 for r in scored if r.qualifier_class == "VINTAGE" and r.level == Level.OMITTED)
    num_omit = sum(1 for r in scored if r.qualifier_class in ("MOE", "CI", "SE", "CV", "DP_NOISE") and r.level == Level.OMITTED)
    vo = {"n": vint["n"], "omitted": vint_omit, "rate": (round(vint_omit / vint["n"], 6) if vint["n"] else None),
          "wilson95": list(wilson_interval(vint_omit, vint["n"]))}
    no = {"n": numeric["n"], "omitted": num_omit, "rate": (round(num_omit / numeric["n"], 6) if numeric["n"] else None),
          "wilson95": list(wilson_interval(num_omit, numeric["n"]))}
    h2 = {"statement": "VINTAGE is omitted more often than any numeric qualifier (hypothesis, no prior art)",
          "vintage_omission": vo, "numeric_omission": no, "verdict": verdict(no, vo, "a<b")}
    return {"E1": e1, "E2": e2, "E3": e3, "H1": h1, "H2": h2}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ceiling-tokens", type=int, required=True,
                    help="per-run ceiling declared on the spend ledger (the task file's stated ceiling)")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--dry-run", action="store_true", help="render prompts, count calls, spend nothing")
    ap.add_argument("--max-calls", type=int, default=0, help="0 = walk the whole schedule (until refused)")
    ap.add_argument("--schedule", default=str(CONFIG / "g1_pilot.toml"))
    ap.add_argument("--split", choices=["dev", "holdout", "all"], default="all",
                    help="which fixture file's propositions to elicit (task 2026-09-03: the holdout is "
                         "sealed until the parser freeze, so the dev run passes --split dev)")
    ap.add_argument("--evidence-dir", default=None,
                    help="evidence directory (default assessment/evidence/g1; the holdout run uses .../g1/holdout)")
    a = ap.parse_args(argv)

    model_stub.guard_no_api_key()
    consumer_cfg = load_consumer_config(CONFIG / "g1_consumer.toml")
    prompts = load_prompts(CONFIG / "g1_prompts.toml")
    steps = load_schedule(Path(a.schedule))
    props, passages = _fixtures()
    for s in steps:
        if s["kind"] == "indirect" and s["passage"] not in passages:
            raise SystemExit(f"FATAL: schedule names unknown passage {s['passage']!r}")
        if s["kind"] == "direct" and s["proposition"] not in props:
            raise SystemExit(f"FATAL: schedule names unknown proposition {s['proposition']!r}")

    spend_cfg = spend._spend_config()
    floor = int(spend_cfg["call_class_floors"].get(consumer_cfg.call_class, 0))
    if not floor:
        raise SystemExit(f"FATAL: controls.yaml has no call_class_floors.{consumer_cfg.call_class}")
    daily = int(spend_cfg["daily_tokens"])
    if a.ceiling_tokens > daily:
        raise SystemExit(f"FATAL: ceiling {a.ceiling_tokens:,} exceeds the standing daily band {daily:,}; "
                         f"stop and report (task step 6)")

    run_id = a.run_id or spend.default_run_id("g1_eval_pilot")
    evidence_dir = Path(a.evidence_dir) if a.evidence_dir else EVIDENCE
    probe = PreservationProbe(prompts, evidence_dir)
    # Split selection (task 2026-09-03 step 3/5): a schedule step belongs to the split of
    # the propositions it elicits. An indirect step on a passage shared by both splits is
    # scored only for the selected split's propositions.
    def in_split(pid: str) -> bool:
        return a.split == "all" or props[pid][0] == a.split
    plan = []
    for s in steps:
        if s["kind"] == "indirect":
            pids = [p.id for p in passages[s["passage"]] if in_split(p.id)]
            if not pids:
                continue
            plan.append({"kind": "indirect", "passage": s["passage"], "propositions": pids})
        else:
            if not in_split(s["proposition"]):
                continue
            plan.append({"kind": "direct", "proposition": s["proposition"], "qualifier": s["qualifier"]})
    n_calls = len(plan)
    report = {"task": TASK, "run_id": run_id, "split": a.split, "evidence_dir": str(evidence_dir.relative_to(REPO)),
              "started_at": _now(), "model_id": consumer_cfg.model_id,
              "prompt_epoch": prompts.prompt_epoch, "ceiling_tokens": a.ceiling_tokens,
              "call_class": consumer_cfg.call_class, "call_class_floor": floor,
              "schedule_calls": n_calls, "schedule_tokens_at_floor": n_calls * floor,
              "dry_run": a.dry_run, "walk": [], "records": []}
    print(f"run {run_id}: {n_calls} scheduled calls; at the {consumer_cfg.call_class} floor of {floor:,} "
          f"tokens the whole schedule needs {n_calls * floor:,} vs ceiling {a.ceiling_tokens:,}")
    if a.dry_run:
        for i, step in enumerate(plan):
            if step["kind"] == "indirect":
                p0 = passages[step["passage"]][0]
                prompt = probe.render_prompt(p0, "indirect")
            else:
                prompt = probe.render_prompt(props[step["proposition"]][1], "direct", step["qualifier"])
            report["walk"].append({**step, "prompt_chars": len(prompt), "status": "dry_run"})
        out = RESULTS / f"g1_pilot_{run_id}_dryrun.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"dry run written: {out.relative_to(REPO)}")
        return 0

    ledger = spend.default_ledger()
    ledger.declare(run_id, a.ceiling_tokens, declared_by=f"scripts/run_g1_pilot.py ({TASK} step 6)",
                   call_class=consumer_cfg.call_class)
    spend.set_current_run(run_id)
    consumer = ClaudeCLIConsumer(consumer_cfg)
    records = []
    stop_reason = "schedule_complete"
    for i, step in enumerate(plan):
        if a.max_calls and i >= a.max_calls:
            stop_reason = f"max_calls={a.max_calls}"
            break
        try:
            if step["kind"] == "indirect":
                plist = [props[pid][1] for pid in step["propositions"]]
                call_id = f"{step['passage']}.indirect"
                existing = probe.existing_evidence(call_id, "indirect", None, consumer.model_id)
                if existing is not None:
                    el = existing
                else:
                    el = probe.elicit(consumer, passages[step["passage"]][0], "indirect", call_id=call_id)
                new = []
                for p in plist:
                    el_p = el.__class__(**{**el.__dict__, "proposition_id": p.id})
                    new.extend(probe.records(el_p, p))
            else:
                which, p = props[step["proposition"]]
                existing = probe.existing_evidence(p.id, "direct", step["qualifier"], consumer.model_id)
                if existing is not None:
                    el = existing
                else:
                    el = probe.elicit(consumer, p, "direct", step["qualifier"])
                new = probe.records(el, p, only_class=step["qualifier"])
            records.extend(new)
            status = "reused_evidence" if existing is not None else "ok"
            report["walk"].append({**step, "status": status, "evidence_path": str(Path(el.evidence_path).relative_to(REPO)),
                                   "usage": el.usage, "n_records": len(new)})
            if existing is not None:
                print(f"  [{i + 1}/{n_calls}] {step['kind']} {step.get('passage') or step['proposition']} "
                      f"-> reused {Path(el.evidence_path).name}; {len(new)} record(s)")
                continue
            print(f"  [{i + 1}/{n_calls}] {step['kind']} {step.get('passage') or step['proposition']} "
                  f"-> {len(new)} record(s); usage {el.usage.get('inputTokens')}/{el.usage.get('outputTokens')} "
                  f"(+cache {el.usage.get('cacheCreationInputTokens')}/{el.usage.get('cacheReadInputTokens')})")
        except spend.SpendRefusalStop as exc:
            stop_reason = f"spend_refused: {exc}"
            report["walk"].append({**step, "status": "spend_refused", "detail": str(exc)})
            print(f"  [{i + 1}/{n_calls}] STOP — {exc}")
            break
        except model_stub.ModelSubstitutionError as exc:
            stop_reason = f"model_substitution: {exc}"
            report["walk"].append({**step, "status": "model_substitution", "detail": str(exc)})
            print(f"  [{i + 1}/{n_calls}] STOP — {exc}")
            break
        except (model_stub.ModelInvocationError, model_stub.ModelRateLimitError) as exc:
            report["walk"].append({**step, "status": "invocation_error", "detail": str(exc)})
            print(f"  [{i + 1}/{n_calls}] error — {exc}")
            continue

    report["records"] = [r.to_dict() for r in records]
    report["g1"] = g1_block(records)
    report["expectations"] = expectation_tests(records)
    report["stop_reason"] = stop_reason
    report["calls_made"] = sum(1 for w in report["walk"] if w["status"] == "ok")
    report["calls_reused"] = sum(1 for w in report["walk"] if w["status"] == "reused_evidence")
    report["spend"] = ledger.status(run_id)
    report["finished_at"] = _now()
    out = RESULTS / f"g1_pilot_{run_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print(f"\nstop: {stop_reason}; calls made {report['calls_made']}/{n_calls} "
          f"(reused {report['calls_reused']}); records {len(records)}")
    for cls, modes in report["g1"]["observed"]["by_class_and_mode"].items():
        for mode, cell in modes.items():
            print(f"  {cls:16s} {mode:8s} n={cell['n']:2d} scored={cell['n_scored']:2d} "
                  f"unparseable={cell['n_unparseable']} L3+={cell['preserved']} rate={cell['preservation_rate']} "
                  f"wilson95={cell['wilson95']} levels={cell['levels']}")
    for k, v in report["expectations"].items():
        print(f"  {k}: {v['verdict']}")
    print(f"results: {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
