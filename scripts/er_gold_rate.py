#!/usr/bin/env python3
"""Label the ER gold sample with an independent model rater. **Model spend, bounded.**

Task `cc_tasks/2026-09-05_er_gold_fable_labels_and_score.md` §1-§2, which withdraws DD-045
§4's "gold is human-labelled". The gold is labelled by `claude-fable-5-1` — a model that took
**no part in any pipeline decision on these pairs**: the vocabulary seed, the alias-first
links, the clerical-band judgments and the homograph scores were all produced by
`claude-opus-5` or by deterministic code. The limitation is stated where the numbers are and
not only here: a same-family rater bounds correctness **relative to that rater**, not to
ground truth.

**The independence conditions, enforced in code rather than in prose** — the same three
`g1_calibration_rate.py` enforces, for the same reason (DD-037):

1. **A different model from every decision under test.** `--model` is required and
   `claude-opus-5` is refused by name.
2. **No repo context.** Calls go through `kg/extraction/model_stub.invoke`, which runs
   `claude -p` from a hermetic empty cwd (root-caused 2026-07-09), so no CLAUDE.md, no design
   decisions, no results files reach the rater.
3. **One pair per call, and the pair is all it sees.** No cosine, no vocabulary term, no
   stratum, no pipeline decision — those live only in `state/er_gold_key.json`, which the
   rater never reads. It cannot infer a distribution and rate to it.

The instruction block is lifted **verbatim from the sheet**, not restated here, so the rater
answers the question the sheet asks. Only the response format is added, because the sheet asks
a person to write in a blank.

    /opt/anaconda3/bin/python3 scripts/er_gold_rate.py --dry-run
    /opt/anaconda3/bin/python3 scripts/er_gold_rate.py --model claude-fable-5-1 --limit 10 --ceiling-tokens N
    /opt/anaconda3/bin/python3 scripts/er_gold_rate.py --model claude-fable-5-1 --ceiling-tokens N
    /opt/anaconda3/bin/python3 scripts/er_gold_rate.py --model claude-fable-5-1 --retest 30 --ceiling-tokens N
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
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

TASK = "cc_tasks/2026-09-05_er_gold_fable_labels_and_score.md"
SHEET = REPO / "docs" / "research" / "2026-09-05_er_gold_sample.md"
KEY = REPO / "state" / "er_gold_key.json"
EVIDENCE = REPO / "assessment" / "evidence" / "er_gold"
RESULTS = REPO / "assessment" / "results"

PROVIDER = "claude_max_oauth"
CLI = "claude"
CALL_CLASS = "judge"

#: Every pipeline decision on these pairs came from this model or from deterministic code. A
#: rater on it would be grading its own work, so the refusal lives in code and not only here.
PIPELINE_MODEL = "claude-opus-5"

#: §2's seeded re-rate draw. Fixed so the retest set is reproducible.
RETEST_SEED = 20260905
RETEST_PER_STRATUM = 6

RESPONSE_FORMAT = (
    "Answer with exactly three lines and nothing else:\n"
    "VERDICT: <one of same, different, uncertain>\n"
    "CONFIDENCE: <a number between 0 and 1>\n"
    "REASON: <one sentence, quoting the deciding phrase from EACH span>"
)

_V = re.compile(r"^\s*VERDICT\s*:\s*\**\s*(same|different|uncertain)\b", re.M | re.I)
_C = re.compile(r"^\s*CONFIDENCE\s*:\s*\**\s*([01](?:\.\d+)?)", re.M | re.I)
_R = re.compile(r"^\s*REASON\s*:\s*(.*)$", re.M | re.I | re.S)

#: One pair's block: everything the SHEET shows between its heading and its answer blanks.
_BLOCK = re.compile(r"^## (P\d{3})\n(.*?)\n\*\*P\d{3} — verdict ", re.M | re.S)


class SheetError(ValueError):
    """The sheet is not in the shape this rater was written against — fail loud rather than
    rate a pair whose second span was silently dropped (standard 4)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def instruction_block(sheet_text: str) -> str:
    """The sheet's own '## What to do' section, verbatim — everything the operator would read
    and nothing about the draw."""
    start = sheet_text.find("## What to do")
    if start < 0:
        raise SheetError("sheet has no '## What to do' section")
    end = sheet_text.find("\n---\n", start)
    if end < 0:
        raise SheetError("sheet has no rule after the instruction block")
    return sheet_text[start:end].strip()


def pair_blocks(sheet_text: str) -> list:
    """[(pair_id, block)] exactly as printed, with the answer blanks removed."""
    out = [(pid, body.strip()) for pid, body in _BLOCK.findall(sheet_text)]
    if not out:
        raise SheetError("no '## Pnnn' pair blocks found")
    return out


def build_prompt(instructions: str, pair_id: str, block: str) -> str:
    return f"{instructions}\n\n---\n\n## {pair_id}\n\n{block}\n\n---\n\n{RESPONSE_FORMAT}\n"


def parse_answer(text: str) -> tuple:
    v = _V.search(text or "")
    if not v:
        return None, None, None
    c = _C.search(text or "")
    r = _R.search(text or "")
    return (v.group(1).lower(), float(c.group(1)) if c else None,
            " ".join((r.group(1) if r else "").split())[:600])


def retest_pairs(key: dict, n: int) -> list:
    """§2: a seeded draw of `RETEST_PER_STRATUM` per stratum, capped at n."""
    by_stratum: dict = {}
    for p in key["pairs"]:
        by_stratum.setdefault(p["stratum"], []).append(p["pair_id"])
    rng = random.Random(RETEST_SEED)
    out = []
    for h in sorted(by_stratum):
        pool = sorted(by_stratum[h])
        out += rng.sample(pool, min(RETEST_PER_STRATUM, len(pool)))
    return sorted(out)[:n]


def decisions_path(pass_name: str) -> Path:
    return RESULTS / f"er_gold_labels_2026-09-05_{pass_name}.jsonl"


def read_decisions(pass_name: str) -> dict:
    p = decisions_path(pass_name)
    if not p.is_file():
        return {}
    return {json.loads(l)["pair_id"]: json.loads(l)
            for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="claude-fable-5-1")
    ap.add_argument("--ceiling-tokens", type=int, default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--limit", type=int, default=0, help="rate only the first N unrated pairs")
    ap.add_argument("--retest", type=int, default=0,
                    help="re-rate N pairs from the seeded draw into a SEPARATE pass file")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    sheet_text = SHEET.read_text(encoding="utf-8")
    instructions = instruction_block(sheet_text)
    blocks = dict(pair_blocks(sheet_text))
    key = json.loads(KEY.read_text(encoding="utf-8"))
    if len(blocks) != len(key["pairs"]):
        raise SheetError(f"sheet has {len(blocks)} pair blocks, key has {len(key['pairs'])}")

    pass_name = "retest" if a.retest else "main"
    wanted = retest_pairs(key, a.retest) if a.retest else [p["pair_id"] for p in key["pairs"]]

    if a.dry_run:
        pid = wanted[0]
        p = build_prompt(instructions, pid, blocks[pid])
        print(f"--- prompt for {pid} ({len(p)} chars) ---\n{p}")
        sizes = [len(build_prompt(instructions, x, blocks[x])) for x in wanted]
        print(f"\n{len(wanted)} pairs in pass {pass_name!r}; prompt chars "
              f"min {min(sizes)} max {max(sizes)} mean {sum(sizes)//len(sizes)}")
        return 0

    model_stub.guard_no_api_key()
    if a.model == PIPELINE_MODEL:
        raise SystemExit(f"FATAL: {a.model} produced the decisions under test; the gold rater "
                         f"must be independent of them (DD-037, and DD-045 addendum-01)")
    if not a.ceiling_tokens:
        raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")

    run_id = a.run_id or f"er_gold_{pass_name}_2026-09-05"
    ledger = spend.default_ledger()
    ledger.declare(run_id, a.ceiling_tokens,
                   declared_by=f"scripts/er_gold_rate.py ({TASK})", call_class=CALL_CLASS)
    spend.set_current_run(run_id)
    consumer = ClaudeCLIConsumer(ConsumerConfig(model_id=a.model, provider=PROVIDER, cli=CLI,
                                                timeout_seconds=a.timeout, call_class=CALL_CLASS))
    ev_dir = EVIDENCE / pass_name
    ev_dir.mkdir(parents=True, exist_ok=True)
    have = read_decisions(pass_name)
    todo = [p for p in wanted if p not in have]
    if a.limit:
        todo = todo[:a.limit]

    made, stop = 0, "pass_complete"
    with decisions_path(pass_name).open("a", encoding="utf-8") as fh:
        for pid in todo:
            prompt = build_prompt(instructions, pid, blocks[pid])
            try:
                completion = consumer.complete(prompt, call_id=f"ergold.{pass_name}.{pid}")
            except spend.SpendRefusalStop as refusal:
                stop = f"spend_refusal: {refusal}"
                break
            if completion.model_id != a.model:
                raise SystemExit(f"FATAL: envelope reports {completion.model_id!r}, "
                                 f"expected {a.model!r}")
            verdict, conf, reason = parse_answer(completion.text)
            rec = {"pair_id": pid, "pass": pass_name, "rater": a.model,
                   "verdict": verdict, "confidence": conf, "reason": reason,
                   "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                   "usage": completion.usage, "ts": _now()}
            (ev_dir / f"{pid}.{a.model}.json").write_text(
                json.dumps({**rec, "prompt": prompt, "response_text": completion.text},
                           indent=1), encoding="utf-8")
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            made += 1

    settled = ledger.status().get("runs", {}).get(run_id, {})
    print(json.dumps({"run_id": run_id, "pass": pass_name, "rater": a.model,
                      "rated_this_pass": made, "stop": stop,
                      "settled_tokens": settled.get("settled"),
                      "tokens_per_pair": round(settled.get("settled", 0) / made, 1) if made else None,
                      "file": str(decisions_path(pass_name).relative_to(REPO))}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
