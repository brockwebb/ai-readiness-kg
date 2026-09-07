#!/usr/bin/env python3
"""Conformance review: does each `v1` rule implement its `MeasurementSpec`? **Model spend.**

Task `cc_tasks/2026-09-06_scan_targets.md` §2. The harness RESULT states the gap this closes
plainly: *"Every rule is at `v1` and none has been reviewed against its `MeasurementSpec` by
anyone but its author."* A rule that passes its control fixtures has been shown to be
self-consistent; it has NOT been shown to measure the thing the framework said it would.

**This is a conformance review, not a rating.** The question is whether the code implements
the clause, so the output is a diff against a written spec — `conforms`, `deviates` (naming
the clause), or `spec_underspecified` (naming the decision the rule had to make that the spec
does not settle). There is no score, no Fable second rater, and no kappa: agreement between
two raters is a property worth measuring when the target is a judgement, and "does line 24
implement the sentence 'HEAD and read Content-Type'" is not one.

**The instrument is versioned and shared.** Derived from the adversarial-review baseline
rubric **v1.3.0** (`~/.claude/skills/adversarial-review/rubric/baseline.md`); every record
stamps `rubric_version`. Three of its rules do real work here:

* §2 anti-anchoring — **the smoke-run verdicts are withheld from the prompt.** A reviewer
  told "A2 failed on 15 of 15 surfaces" reasons backward from the outcome: a rule that fails
  everything looks broken and a rule that passes looks right, and neither is evidence about
  conformance. This is the same discipline that kept the cosine out of `link_judge.py`'s
  prompt — never show the judge the number the item was selected on.
* §3 grounding — a `deviates` must quote the spec clause and the rule line verbatim. A
  deviation that cannot be quoted is not a finding.
* §1 role — `conforms` is a real answer. Manufacturing a deviation to look useful is the
  failure mode this overlay is most exposed to, because the reviewer knows it was asked to
  review sixteen rules and expects some to be wrong.

The `code` overlay in the skill is an uncalibrated STUB and is deliberately NOT used; this
overlay is project-local (`rule-conformance`) and its calibration is §2's own re-review of
every `deviates` against the fixtures, not an inherited agreement rate.

    /opt/anaconda3/bin/python3 scripts/rule_review.py --dry-run
    /opt/anaconda3/bin/python3 scripts/rule_review.py --calibrate 3 --ceiling-tokens N
    /opt/anaconda3/bin/python3 scripts/rule_review.py --ceiling-tokens N
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
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from harness.consumers import ClaudeCLIConsumer, ConsumerConfig  # noqa: E402
from kg import spend  # noqa: E402
from kg.extraction import model_stub  # noqa: E402

TASK = "cc_tasks/2026-09-06_scan_targets.md"
RUBRIC_VERSION = "v1.3.0"
OVERLAY = "rule-conformance (project-local, ai-readiness-kg)"
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
RULES_DIR = REPO / "assessment" / "harness" / "scan" / "rules"
EVIDENCE = REPO / "assessment" / "evidence" / "rule_review"
DECISIONS = REPO / "assessment" / "results" / "rule_review_2026-09-06.jsonl"

PROVIDER = "claude_max_oauth"
CLI = "claude"
CALL_CLASS = "judge"
VERDICTS = ("conforms", "deviates", "spec_underspecified")

#: §2's calibration size. Three rules, chosen to span the shapes rather than at random: one
#: whose spec is a mechanical recipe (A1), one whose spec is a policy judgement (A4), and the
#: one whose spec this repo wrote itself last task (E5). A random three could easily be three
#: mechanical recipes and would calibrate nothing.
CALIBRATION_LEGS = ("A1", "A4", "E5")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def framework() -> dict:
    return json.loads(FRAMEWORK.read_text(encoding="utf-8"))


def review_items() -> list:
    """One item per `v1` rule: its spec, its indicator's row, and its source. Nothing about
    how it performed."""
    from scan.rules import BY_LEG, REGISTRY                       # noqa: E402
    g = framework()
    specs = {n["properties"].get("leg"): n["properties"]
             for n in g["nodes"] if "MeasurementSpec" in n["labels"]}
    inds = {n["properties"].get("code"): n["properties"]
            for n in g["nodes"] if "AssessmentIndicator" in n["labels"]}
    params = _params()
    out = []
    for leg, rule_id in sorted(BY_LEG.items()):
        spec = specs.get(leg) or {}
        ind = inds.get(spec.get("indicator_code") or leg.split("-")[0]) or {}
        src = Path(REGISTRY[rule_id].__file__).read_text(encoding="utf-8")
        out.append({"leg": leg, "rule_id": rule_id, "spec": spec, "indicator": ind,
                    "source": src,
                    "fixtures": params["e5_control"]["expected_verdicts"]})
    return out


def _params() -> dict:
    from scan import load_params                                  # noqa: E402
    return load_params()


PROMPT = """You are reviewing one rule of a measurement harness for CONFORMANCE to its written
specification. You are not rating the rule and you are not asked whether its verdicts are
correct. The only question is whether the code implements what the specification says.

## The indicator this rule measures
code: {code}
construct: {construct}
indicator: {indicator}
type: {type} · tier: {tier}

## The MeasurementSpec — this is the specification
signal: {signal}
evidence_kind: {evidence_kind}
prior_art: {prior_art}

## The control fixtures every rule is run against
Two local static sites. Each rule must return the stated verdict on each:
{fixtures}
`passes_all` is a well-formed surface (robots allowing everything, sitemap, llms.txt, valid
data.json, schema.org Dataset JSON-LD, CSV and JSON downloads, a licence line, a
machine-readable release date). `fails_all` is PDF-only with no robots, no sitemap, a
soft-404 shell (HTTP 200 with an HTML error page for any path), no markup and no licence.

## The rule source
```python
{source}
```

## What to return
A JSON object and nothing else:

{{"verdict": "conforms" | "deviates" | "spec_underspecified",
  "spec_clause": "<the sentence or phrase of `signal` at issue, quoted verbatim, or null>",
  "rule_evidence": "<the line(s) of the rule source at issue, quoted verbatim, or null>",
  "finding": "<one or two sentences>",
  "confidence": <0.0-1.0>}}

Definitions, and they are narrow on purpose:

- `conforms` — the rule implements the signal. It may be stricter in a way the signal
  implies. This is a real and expected answer; do not manufacture a deviation.
- `deviates` — the rule fails to implement a clause of the signal, or implements something
  the signal does not authorise. Quote BOTH the clause and the code. A deviation you cannot
  quote on both sides is not a deviation, and you should return `conforms` instead.
- `spec_underspecified` — the rule had to decide something the signal does not settle, and a
  different reasonable implementation would return a different verdict on some real surface.
  Name that decision in `finding`. Do not use this for a detail that could not change any
  verdict.

Return the JSON object only."""


def build_prompt(item: dict) -> str:
    s, i = item["spec"], item["indicator"]
    return PROMPT.format(
        code=i.get("code") or item["leg"], construct=i.get("construct") or "(none recorded)",
        indicator=i.get("indicator") or "(none recorded)",
        type=i.get("type") or "?", tier=i.get("tier") or "?",
        signal=s.get("signal") or "(none recorded)",
        evidence_kind=s.get("evidence_kind") or "(none recorded)",
        prior_art=s.get("prior_art") or "(none recorded)",
        fixtures="\n".join(f"- {k}: every rule must return `{v}`"
                           for k, v in item["fixtures"].items()),
        source=item["source"])


def parse_answer(text: str) -> dict:
    """Strict. A response that does not carry one of the three verdicts is a failed call, not
    a defaulted one — a silently defaulted verdict is a fabricated review."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"no JSON object in response: {text[:200]!r}")
    obj = json.loads(m.group(0))
    if obj.get("verdict") not in VERDICTS:
        raise ValueError(f"verdict {obj.get('verdict')!r} outside {VERDICTS}")
    return obj


def read_decisions() -> dict:
    if not DECISIONS.is_file():
        return {}
    return {json.loads(l)["leg"]: json.loads(l)
            for l in DECISIONS.read_text(encoding="utf-8").splitlines() if l.strip()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--ceiling-tokens", type=int, default=0)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--calibrate", type=int, default=0,
                    help="review only the CALIBRATION_LEGS, to measure the rate before "
                         "declaring the ceiling for the rest (DD-042)")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    items = review_items()
    if a.calibrate:
        items = [i for i in items if i["leg"] in CALIBRATION_LEGS][:a.calibrate]

    if a.dry_run:
        sizes = [len(build_prompt(i)) for i in items]
        print(build_prompt(items[0])[:2500])
        print(f"\n... {len(items)} rules; prompt chars min {min(sizes)} max {max(sizes)} "
              f"mean {sum(sizes)//len(sizes)}")
        return 0

    model_stub.guard_no_api_key()
    if not a.ceiling_tokens:
        raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
    run_id = a.run_id or "rule_review_2026-09-06"
    ledger = spend.default_ledger()
    ledger.declare(run_id, a.ceiling_tokens,
                   declared_by=f"scripts/rule_review.py ({TASK})", call_class=CALL_CLASS)
    spend.set_current_run(run_id)
    consumer = ClaudeCLIConsumer(ConsumerConfig(model_id=a.model, provider=PROVIDER, cli=CLI,
                                                timeout_seconds=a.timeout,
                                                call_class=CALL_CLASS))
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    DECISIONS.parent.mkdir(parents=True, exist_ok=True)
    have = read_decisions()
    made, stop = 0, "complete"
    with DECISIONS.open("a", encoding="utf-8") as fh:
        for item in items:
            leg = item["leg"]
            if leg in have:
                continue
            prompt = build_prompt(item)
            try:
                completion = consumer.complete(prompt, call_id=f"rulerev.{leg}")
            except spend.SpendRefusalStop as refusal:
                stop = f"spend_refusal: {refusal}"
                break
            if completion.model_id != a.model:
                raise SystemExit(f"FATAL: envelope reports {completion.model_id!r}, "
                                 f"expected {a.model!r}")
            obj = parse_answer(completion.text)
            rec = {"leg": leg, "rule_id": item["rule_id"], "rater": a.model,
                   "rubric_version": RUBRIC_VERSION, "overlay": OVERLAY,
                   "verdict": obj["verdict"], "spec_clause": obj.get("spec_clause"),
                   "rule_evidence": obj.get("rule_evidence"), "finding": obj.get("finding"),
                   "confidence": obj.get("confidence"), "usage": completion.usage,
                   "ts": _now()}
            (EVIDENCE / f"{leg}.{a.model}.json").write_text(
                json.dumps({**rec, "prompt": prompt, "response_text": completion.text},
                           indent=1), encoding="utf-8")
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            made += 1
    st = ledger.status().get("runs", {}).get(run_id, {})
    print(json.dumps({"run_id": run_id, "rules_reviewed_this_pass": made, "stop": stop,
                      "settled_tokens": st.get("settled"),
                      "tokens_per_rule": round(st.get("settled", 0) / made, 1) if made else None,
                      "remaining": st.get("remaining"),
                      "decisions": str(DECISIONS.relative_to(REPO))}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
