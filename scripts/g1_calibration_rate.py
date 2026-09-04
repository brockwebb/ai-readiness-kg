#!/usr/bin/env python3
"""Rate the blind G1 calibration sheet with an INDEPENDENT model (task
2026-09-03_g1_calibration_rating_agreement, step 1).

Why a model and not the operator. The v2 genuine-loss counts come from an LLM reviewer
(Opus, this repo's CC session) whose agreement with anyone else is unmeasured. The second
rater has to be independent of that reviewer, and the operator's judgment is a narrow-band
sensor spent on genuine novelty, not on 60 labelling decisions — so the rater is a
different model with no context beyond the sheet, and the operator's only role is the
disagreement list (step 3). Desktop decision 2026-09-03; DD-037.

**The independence conditions this script enforces**, each one a way the rating could
otherwise be contaminated by the instrument it is meant to check:

1. **A different model.** `--model` is required and is compared against every envelope;
   the pinned reviewer's model (`claude-opus-5`) is refused by name — an Opus rater would
   be the reviewer's own model and measures nothing.
2. **No repo context.** The call goes through `kg/extraction/model_stub.invoke`, which runs
   `claude -p` from a hermetic empty cwd (root cause 2026-07-09), so no CLAUDE.md, no
   design decisions, no results files are in the rater's context.
3. **One record per call.** Each call carries the sheet's instruction block and exactly ONE
   record. The rater never sees another record, the stratum table, the scorer's level, the
   reviewer's verdict, the failure class, the surface type or any aggregate — so it cannot
   infer a distribution and rate to it.
4. **The sheet's own wording.** The instruction paragraph, the D2 level scale and the D9
   families are lifted verbatim from the sheet file rather than restated here, so the rater
   is answering the question the sheet asks.

Same three gates as every other model call in this repo: DD-007 (subscription OAuth only,
never `ANTHROPIC_API_KEY`), DD-022 (reserve-before-dispatch on the shared ledger; an
undeclared run refuses and a refusal is a clean stop), and invariant 5 (an envelope
reporting another model raises `ModelSubstitutionError` and stops the run).

Evidence is written per record BEFORE the filled sheet exists, so a stop mid-run leaves the
raw exchanges on disk and the sheet can be rebuilt from them without re-spending.

    /opt/anaconda3/bin/python3 scripts/g1_calibration_rate.py \
        --model claude-fable-5-1 --ceiling-tokens 2500000 \
        --run-id g1_calibration_fable_2026-09-03 [--dry-run] [--max-calls N]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))

from harness.consumers import ClaudeCLIConsumer, ConsumerConfig  # noqa: E402
from kg import spend  # noqa: E402
from kg.extraction import model_stub  # noqa: E402

TASK = "cc_tasks/2026-09-03_g1_calibration_rating_agreement.md"
RESULTS = REPO / "assessment" / "results"
SHEET = RESULTS / "g1_calibration_sheet_2026-09-03.md"
EVIDENCE = REPO / "assessment" / "evidence" / "g1" / "calibration"

# The reviewer under test. A rater on this model is not independent of it, whatever the
# task file says, so the refusal lives in code and not only in prose.
REVIEWER_MODEL = "claude-opus-5"

# `provider` and `cli` are not tunables: DD-007 fixes the transport to `claude -p` under
# subscription OAuth, and `model_stub.load_model_config` refuses any other provider. The
# tunables (model, timeout, call class, ceiling) are all CLI arguments.
PROVIDER = "claude_max_oauth"
CLI = "claude"

_BLOCK_RE = re.compile(r"^## (C\d{3})\n(.*?)\n\*\*C\d{3} — Level ", re.M | re.S)
_LEVEL_RE = re.compile(r"^\s*LEVEL\s*:\s*\**\s*(L[0-4]|U)\b", re.M | re.I)
_NOTE_RE = re.compile(r"^\s*NOTE\s*:\s*(.*)$", re.M | re.I | re.S)

RESPONSE_FORMAT = (
    "Answer with exactly two lines and nothing else:\n"
    "LEVEL: <one of L0, L1, L2, L3, L4, U>\n"
    "NOTE: <one short sentence; write none if the record is clean>"
)


class SheetParseError(ValueError):
    """The sheet is not in the shape this script was written against — fail loud rather
    than rate a record whose text was silently truncated (standard 4)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def instruction_block(sheet_text: str) -> str:
    """The sheet's labelling instructions, verbatim: the 'What to do' paragraph, the D2
    level scale, the D9 families and the per-record question — everything the human labeler
    would read, and nothing about the draw (the seed and stratum table are above it)."""
    start = sheet_text.find("## What to do")
    if start < 0:
        raise SheetParseError("sheet has no '## What to do' section")
    end = sheet_text.find("\n---\n", start)
    if end < 0:
        raise SheetParseError("sheet has no rule after the instruction block")
    return sheet_text[start:end].strip()


def record_blocks(sheet_text: str) -> list:
    """[(sample_id, block)] where block is the record exactly as printed on the sheet —
    the estimate, family, published forms, mode, compression, the prompt the consumer saw
    and its response — with the answer lines removed."""
    out = [(sid, body.strip()) for sid, body in _BLOCK_RE.findall(sheet_text)]
    if not out:
        raise SheetParseError("no '## C###' record blocks found")
    return out


def build_prompt(instructions: str, sample_id: str, block: str) -> str:
    return (f"{instructions}\n\n---\n\n## {sample_id}\n\n{block}\n\n---\n\n{RESPONSE_FORMAT}\n")


def parse_answer(text: str) -> tuple:
    """(level, note) or (None, None) when the answer is not in the requested shape. A
    missing NOTE with a good LEVEL is parseable — the level is the measurement."""
    m = _LEVEL_RE.search(text or "")
    if not m:
        return None, None
    level = m.group(1).upper()
    n = _NOTE_RE.search(text or "")
    note = " ".join((n.group(1) if n else "").split()).strip()
    return level, note


def fill_sheet(sheet_text: str, answers: dict, model_id: str, run_id: str) -> str:
    """The sheet with its answer lines filled. Records with no parseable answer keep the
    blank rule, so the agreement script reads them as unlabelled rather than as a level."""
    out = sheet_text
    for sid, a in answers.items():
        if not a.get("level"):
            continue
        note = a.get("note") or ""
        out = out.replace(f"**{sid} — Level (L0 / L1 / L2 / L3 / L4 / U):** ______",
                          f"**{sid} — Level (L0 / L1 / L2 / L3 / L4 / U):** {a['level']}")
        out = out.replace(f"**{sid} — Note:** ______", f"**{sid} — Note:** {note}")
    header = (f"# G1 EVAL v2 — reviewer calibration sheet (blind), RATED\n\n"
              f"**Rater:** `{model_id}` — an independent model, one record per call, hermetic cwd, "
              f"no repo context, no scorer or reviewer information (task `{TASK}`, run `{run_id}`; "
              f"raw exchanges under `assessment/evidence/g1/calibration/`). "
              f"**Rated:** {_now()}. {len([a for a in answers.values() if a.get('level')])} of "
              f"{len(answers)} records answered.\n")
    return out.replace("# G1 EVAL v2 — reviewer calibration sheet (blind)\n", header, 1)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="the rater model id, selected with `claude -p --model`")
    ap.add_argument("--ceiling-tokens", type=int, required=True,
                    help="per-run ceiling declared on the spend ledger (the task file's stated ceiling)")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--sheet", default=str(SHEET))
    ap.add_argument("--evidence-dir", default=str(EVIDENCE))
    ap.add_argument("--out", default=None, help="filled sheet (default: <sheet>_filled_<label>.md)")
    ap.add_argument("--label", default=None,
                    help="short name for the rater in the output filename (default: the model id's "
                         "family word, e.g. claude-fable-5-1 -> fable)")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--call-class", default="g1_eval", help="controls.yaml spend.call_class_floors key")
    ap.add_argument("--max-calls", type=int, default=0, help="0 = rate every unrated record")
    ap.add_argument("--dry-run", action="store_true", help="render prompts, spend nothing")
    a = ap.parse_args(argv)

    model_stub.guard_no_api_key()
    if a.model == REVIEWER_MODEL:
        raise SystemExit(f"FATAL: {a.model} is the reviewer's own model; the rater must be independent (DD-037)")

    sheet_text = Path(a.sheet).read_text(encoding="utf-8")
    instructions = instruction_block(sheet_text)
    blocks = record_blocks(sheet_text)

    spend_cfg = spend._spend_config()
    floor = int(spend_cfg["call_class_floors"].get(a.call_class, 0))
    if not floor:
        raise SystemExit(f"FATAL: controls.yaml has no call_class_floors.{a.call_class}")
    daily = int(spend_cfg["daily_tokens"])
    if a.ceiling_tokens > daily:
        raise SystemExit(f"FATAL: ceiling {a.ceiling_tokens:,} exceeds the standing daily band {daily:,}; stop and report")

    run_id = a.run_id or spend.default_run_id("g1_calibration")
    ev_dir = Path(a.evidence_dir)
    parts = re.split(r"[^a-z0-9]+", a.model.lower())
    label = a.label or (parts[1] if len(parts) > 1 and parts[0] == "claude" else parts[0])
    out_path = Path(a.out) if a.out else Path(a.sheet).with_name(Path(a.sheet).stem + f"_filled_{label}.md")

    def evidence_path(sample_id: str) -> Path:
        return ev_dir / f"{sample_id}.{a.model}.json"

    todo = [(sid, b) for sid, b in blocks if not evidence_path(sid).is_file()]
    print(f"run {run_id}: rater {a.model}, {len(blocks)} sheet records, {len(todo)} unrated; "
          f"at the {a.call_class} floor of {floor:,} tokens they need {len(todo) * floor:,} "
          f"vs ceiling {a.ceiling_tokens:,}")
    if len(todo) * floor > a.ceiling_tokens:
        print(f"NOTE: the floor estimate exceeds the ceiling; the run will stop cleanly when refused "
              f"and can be resumed (evidence on disk is never re-elicited)")

    if a.dry_run:
        sid, block = blocks[0]
        p = build_prompt(instructions, sid, block)
        print(f"\n--- dry run: prompt for {sid} ({len(p)} chars) ---\n{p[:1600]}\n…")
        print(f"\nprompt sizes: min {min(len(build_prompt(instructions, s, b)) for s, b in blocks)}, "
              f"max {max(len(build_prompt(instructions, s, b)) for s, b in blocks)} chars")
        return 0

    ledger = spend.default_ledger()
    ledger.declare(run_id, a.ceiling_tokens, declared_by=f"scripts/g1_calibration_rate.py ({TASK})",
                   call_class=a.call_class)
    spend.set_current_run(run_id)
    consumer = ClaudeCLIConsumer(ConsumerConfig(model_id=a.model, provider=PROVIDER, cli=CLI,
                                                timeout_seconds=a.timeout, call_class=a.call_class))
    ev_dir.mkdir(parents=True, exist_ok=True)

    made, stop_reason = 0, "sheet_complete"
    for sid, block in todo:
        if a.max_calls and made >= a.max_calls:
            stop_reason = f"max_calls={a.max_calls}"
            break
        prompt = build_prompt(instructions, sid, block)
        attempts, refused = [], None
        try:
            for attempt in range(2):        # one retry, and only on an unparseable answer
                completion = consumer.complete(prompt, call_id=f"g1cal.{sid}")
                if completion.model_id != a.model:
                    raise SystemExit(f"FATAL: envelope reports {completion.model_id!r}, expected {a.model!r}")
                level, note = parse_answer(completion.text)
                attempts.append({"attempt": attempt + 1, "response_text": completion.text,
                                 "usage": completion.usage, "duration_ms": completion.duration_ms,
                                 "cost_usd": completion.cost_usd,
                                 "spend_reservation_id": completion.spend_reservation_id,
                                 "level": level, "note": note, "timestamp": _now()})
                if level:
                    break
                print(f"  {sid}: answer not in the requested shape; one retry")
        except spend.SpendRefusalStop as refusal:
            # A refusal is the clean-stop contract (DD-022). A first attempt that already
            # landed is still evidence and is persisted below before the loop ends; only a
            # record with no attempt at all is left for the next invocation.
            refused = f"spend_refusal: {refusal}"
            print(f"STOP (clean): {refusal}")
            if not attempts:
                stop_reason = refused
                break
        made += 1
        last = attempts[-1]
        record = {"task": TASK, "run_id": run_id, "sample_id": sid, "model_id": a.model,
                  "rater_role": "independent calibration rater (DD-037)",
                  "sheet": str(Path(a.sheet).relative_to(REPO)), "prompt": prompt,
                  "response_text": last["response_text"], "level": last["level"], "note": last["note"],
                  "attempts": attempts, "retried": len(attempts) > 1,
                  "unparseable_after_retry": last["level"] is None,
                  "usage": last["usage"], "duration_ms": last["duration_ms"], "cost_usd": last["cost_usd"],
                  "spend_run_id": run_id, "spend_reservation_id": last["spend_reservation_id"],
                  "timestamp": last["timestamp"]}
        evidence_path(sid).write_text(json.dumps(record, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"  {sid}: {last['level'] or 'UNPARSEABLE'}"
              + (" (retried)" if len(attempts) > 1 else ""))
        if refused:
            stop_reason = refused
            break

    answers, retried, unparseable = {}, [], []
    for sid, _ in blocks:
        p = evidence_path(sid)
        if not p.is_file():
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        answers[sid] = {"level": rec.get("level"), "note": rec.get("note")}
        if rec.get("retried"):
            retried.append(sid)
        if rec.get("unparseable_after_retry"):
            unparseable.append(sid)

    out_path.write_text(fill_sheet(sheet_text, answers, a.model, run_id), encoding="utf-8")
    answered = sum(1 for v in answers.values() if v.get("level"))
    print(f"\nstop: {stop_reason}; calls this invocation {made}; rated {answered}/{len(blocks)} "
          f"(retried {len(retried)}, unparseable after retry {len(unparseable)}"
          + (f": {', '.join(unparseable)}" if unparseable else "") + ")")
    print(f"filled sheet: {out_path.relative_to(REPO)}")
    print(f"evidence: {ev_dir.relative_to(REPO)}/ ({len(answers)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
