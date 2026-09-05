#!/usr/bin/env python3
"""The clerical-review band: does this node denote this term? **Model spend, bounded.**

Task `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §2. Fellegi & Sunter (1969) send
the band between the two thresholds to clerical review; the bottleneck that made controlled
vocabularies unaffordable for a century was that the clerk had to be a person. This script is
the clerk, and §2.2's Cohen's kappa against an independent model is what makes its verdicts
admissible rather than merely cheap.

**The instrument is versioned and shared.** The prompt below is derived from the
adversarial-review baseline rubric **v1.3.0** (`~/.claude/skills/adversarial-review/
rubric/baseline.md`), and every decision record stamps `rubric_version`. Three of its rules do
real work here:

* §2 anti-anchoring — "surface-form similarity is not concept identity; the same surface form
  in different senses is not [equivalent]", and a high similarity signal is evidence about the
  pipeline, not about the truth. **So the cosine is deliberately NOT in the prompt.** The band
  was selected by cosine; showing the judge the number it was selected on invites it to ratify
  the selector. This is the calibrated failure the rubric records (`cos=0.917` driven by shared
  boilerplate across two unrelated domains).
* §3 grounding — the reason must quote both spans verbatim, or say plainly it cannot.
* §1 role — a clean `different` is a real answer; manufacturing a `same` to look useful is
  the failure mode.

The overlay is project-local (`entity-linking`) and is **not** calibrated against the
baseline's own operator ledger, whose calibration base is 32 verdicts from one domain. §2.2's
kappa gate is this overlay's calibration and is stronger than what it inherits.

**Independence, enforced in code and not only in prose** — the same three conditions
`g1_calibration_rate.py` enforces, for the same reason: a different model for the second
rater, a hermetic empty cwd so no repo context reaches it (`model_stub` root cause
2026-07-09), and one pair per call so the rater cannot infer a distribution and rate to it.

    /opt/anaconda3/bin/python3 scripts/link_judge.py --dry-run
    /opt/anaconda3/bin/python3 scripts/link_judge.py --model claude-opus-5 --calibrate 50 --ceiling-tokens N
    /opt/anaconda3/bin/python3 scripts/link_judge.py --model claude-opus-5 --ceiling-tokens N
    /opt/anaconda3/bin/python3 scripts/link_judge.py --model claude-fable-5-1 --sample 100 --ceiling-tokens N
    /opt/anaconda3/bin/python3 scripts/link_judge.py --emit          # write term_link_judged events
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
from kg import eventlog, spend, vocab  # noqa: E402
from kg.extraction import model_stub  # noqa: E402

TASK = "cc_tasks/2026-09-05_vocabulary_and_entity_linking.md"
RUBRIC_VERSION = "v1.3.0"
OVERLAY = "entity-linking (project-local, ai-readiness-kg)"
BAND = REPO / "state" / "vocab_candidates_2026-09-05.jsonl"
EVIDENCE = REPO / "assessment" / "evidence" / "vocab_linking"
RESULTS = REPO / "assessment" / "results"

PROVIDER = "claude_max_oauth"
CLI = "claude"
CALL_CLASS = "judge"

#: §2.2's auto-accept threshold, pre-registered in the task and not tuned here.
ACCEPT_CONFIDENCE = 0.80
#: Draw seed, fixed so the calibration batch and the kappa sample are reproducible.
SEED = 20260905

INSTRUCTIONS = """You are an adversarial reviewer deciding ONE entity-linking question.

A knowledge graph keys every extracted node per document, so the same real-world thing appears
once per document that mentions it. A controlled vocabulary term is the canonical name for one
such thing. Your question is exactly this:

    Does the NODE below denote the same thing as the TERM below?

Rules, and they are the point of the exercise:

1. Surface-form similarity is NOT identity. Two different surface forms of one concept are the
   same thing; the SAME surface form used in two different senses is NOT. A phrase that names
   one thing in a statistical-agency context and another in a machine-learning context is two
   things, and the correct answer is `different`.
2. Decide from the node's grounding span and the term's scope note. The span is the sentence
   the node was extracted from; the scope note says what the term covers. If the span does not
   show you what the node means, that is what `uncertain` is for.
3. A broader-or-narrower relationship is NOT sameness. "explainable AI techniques" is narrower
   than "explainable AI"; if the node is a SPECIES of the term rather than the term, answer
   `different` and say so.
4. `different` is a real and useful answer. Do not manufacture a `same` to look decisive.
5. Quote both spans verbatim in your reason. Copy the run of characters; do not paraphrase,
   repair or stitch fragments. If you cannot quote, say plainly what you could not find.

Answer with exactly three lines and nothing else:
VERDICT: <one of same, different, uncertain>
CONFIDENCE: <a number between 0 and 1>
REASON: <one sentence, quoting both spans>"""

_V = re.compile(r"^\s*VERDICT\s*:\s*\**\s*(same|different|uncertain)\b", re.M | re.I)
_C = re.compile(r"^\s*CONFIDENCE\s*:\s*\**\s*([01](?:\.\d+)?)", re.M | re.I)
_R = re.compile(r"^\s*REASON\s*:\s*(.*)$", re.M | re.I | re.S)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def pair_id(row: dict) -> str:
    """Stable, filesystem-safe id for one (node, term) pair."""
    return hashlib.sha1(f"{row['node_key']}|{row['term_id']}".encode()).hexdigest()[:16]


def build_prompt(row: dict) -> str:
    """One pair, and nothing else. No cosine (rubric §2 anti-anchoring), no other pair, no
    aggregate — the judge cannot infer a distribution and rate to it."""
    return (f"{INSTRUCTIONS}\n\n---\n\n"
            f"NODE\n"
            f"  kg label: {row['label']}\n"
            f"  name: {row.get('name')}\n"
            f"  source document: {row.get('doc_id')}\n"
            f"  grounding span: {(row.get('span') or '(none recorded)')[:800]}\n\n"
            f"TERM\n"
            f"  preferred label: {row['term_label']}\n"
            f"  scope note: {(row.get('term_scope_note') or '(none)')[:600]}\n")


def parse_answer(text: str) -> tuple:
    v = _V.search(text or "")
    if not v:
        return None, None, None
    c = _C.search(text or "")
    r = _R.search(text or "")
    conf = float(c.group(1)) if c else None
    return v.group(1).lower(), conf, " ".join((r.group(1) if r else "").split())[:600]


def load_band() -> list:
    if not BAND.is_file():
        raise SystemExit(f"FATAL: {BAND.relative_to(REPO)} missing; run link_vocabulary.py --phase band")
    return [json.loads(l) for l in BAND.read_text(encoding="utf-8").splitlines() if l.strip()]


def stratified(rows: list, n: int) -> list:
    """§2.1: stratified across labels and similarity. Deterministic under SEED so the batch
    is reproducible and a rerun does not quietly draw a different sample."""
    if n >= len(rows):
        return list(rows)
    buckets: dict = {}
    for r in rows:
        buckets.setdefault((r["label"], round(r["cosine"] * 20) / 20), []).append(r)
    rng = random.Random(SEED)
    for v in buckets.values():
        rng.shuffle(v)
    out, keys = [], sorted(buckets)
    i = 0
    while len(out) < n:
        drawn = False
        for k in keys:
            if buckets[k][i:i + 1]:
                out.append(buckets[k][i])
                drawn = True
                if len(out) >= n:
                    break
        if not drawn:
            break
        i += 1
    return out


def decisions_path(label: str) -> Path:
    return RESULTS / f"vocab_link_decisions_2026-09-05_{label}.jsonl"


def read_decisions(label: str) -> dict:
    p = decisions_path(label)
    if not p.is_file():
        return {}
    return {json.loads(l)["pair_id"]: json.loads(l)
            for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--ceiling-tokens", type=int, default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--calibrate", type=int, default=0, help="run only N stratified pairs (§2.1)")
    ap.add_argument("--sample", type=int, default=0, help="rate a stratified sample of N (§2.2 kappa)")
    ap.add_argument("--label", default=None)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--emit", action="store_true", help="write term_link_judged events, no spend")
    a = ap.parse_args(argv)

    rows = load_band()
    parts = re.split(r"[^a-z0-9]+", a.model.lower())
    label = a.label or (parts[1] if len(parts) > 1 and parts[0] == "claude" else parts[0])

    if a.emit:
        return emit(label)

    todo = rows
    if a.calibrate:
        todo = stratified(rows, a.calibrate)
    elif a.sample:
        todo = stratified(rows, a.sample)

    if a.dry_run:
        p = build_prompt(todo[0])
        print(f"--- prompt for pair {pair_id(todo[0])} ({len(p)} chars) ---\n{p}")
        sizes = [len(build_prompt(r)) for r in todo]
        print(f"\n{len(todo)} pairs; prompt chars min {min(sizes)} max {max(sizes)} "
              f"mean {sum(sizes)//len(sizes)}")
        return 0

    model_stub.guard_no_api_key()
    if not a.ceiling_tokens:
        raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
    run_id = a.run_id or f"vocab_link_{label}_2026-09-05"
    ledger = spend.default_ledger()
    ledger.declare(run_id, a.ceiling_tokens,
                   declared_by=f"scripts/link_judge.py ({TASK})", call_class=CALL_CLASS)
    spend.set_current_run(run_id)
    consumer = ClaudeCLIConsumer(ConsumerConfig(model_id=a.model, provider=PROVIDER, cli=CLI,
                                                timeout_seconds=a.timeout, call_class=CALL_CLASS))
    ev_dir = EVIDENCE / label
    ev_dir.mkdir(parents=True, exist_ok=True)
    have = read_decisions(label)
    out_path = decisions_path(label)
    made, stop = 0, "band_complete"
    with out_path.open("a", encoding="utf-8") as fh:
        for row in todo:
            pid = pair_id(row)
            if pid in have:
                continue
            try:
                completion = consumer.complete(build_prompt(row), call_id=f"vlink.{pid}")
            except spend.SpendRefusalStop as refusal:
                stop = f"spend_refusal: {refusal}"
                break
            if completion.model_id != a.model:
                raise SystemExit(f"FATAL: envelope reports {completion.model_id!r}, expected {a.model!r}")
            verdict, conf, reason = parse_answer(completion.text)
            rec = {"pair_id": pid, "node_key": row["node_key"], "label": row["label"],
                   "name": row.get("name"), "doc_id": row.get("doc_id"),
                   "term_id": row["term_id"], "term_label": row["term_label"],
                   "cosine": row["cosine"], "rater": a.model,
                   "rubric_version": RUBRIC_VERSION, "overlay": OVERLAY,
                   "verdict": verdict, "confidence": conf, "reason": reason,
                   "usage": completion.usage, "ts": _now()}
            (ev_dir / f"{pid}.{a.model}.json").write_text(
                json.dumps({**rec, "prompt": build_prompt(row),
                            "response_text": completion.text}, indent=1), encoding="utf-8")
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            made += 1
    settled = ledger.status().get("runs", {}).get(run_id, {})
    print(json.dumps({"run_id": run_id, "rater": a.model, "pairs_decided_this_pass": made,
                      "stop": stop, "settled_tokens": settled.get("settled"),
                      "tokens_per_pair": round(settled.get("settled", 0) / made, 1) if made else None,
                      "decisions_file": str(out_path.relative_to(REPO))}, indent=1))
    return 0


def emit(label: str) -> int:
    """§2.2: auto-accept `same` at confidence >= 0.80 as `term_link_judged` events. Everything
    else stays unresolved — an `uncertain` is a decision NOT to link, recorded as one."""
    decisions = read_decisions(label)
    if not decisions:
        raise SystemExit(f"FATAL: no decisions for rater {label!r}")
    have = {ev.get("node_key") for ev in eventlog.replay()
            if ev.get("event_type") == "term_link_judged"}
    counts = {"same": 0, "different": 0, "uncertain": 0, "unparsed": 0,
              "accepted": 0, "below_confidence": 0, "already_on_log": 0}
    for rec in decisions.values():
        counts[rec["verdict"] or "unparsed"] = counts.get(rec["verdict"] or "unparsed", 0) + 1
        if rec["verdict"] != "same":
            continue
        if (rec.get("confidence") or 0) < ACCEPT_CONFIDENCE:
            counts["below_confidence"] += 1
            continue
        if rec["node_key"] in have:
            counts["already_on_log"] += 1
            continue
        eventlog.append({"event_type": "term_link_judged", "node_key": rec["node_key"],
                         "term_id": rec["term_id"], "verdict": "same",
                         "confidence": rec["confidence"], "rater": rec["rater"],
                         "rubric_version": rec["rubric_version"], "overlay": rec["overlay"],
                         "reason": rec["reason"], "pair_id": rec["pair_id"],
                         "ts": _now()}, batch=vocab.VOCAB_BATCH)
        counts["accepted"] += 1
    print(json.dumps(counts, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
