#!/usr/bin/env python3
"""Judged homograph pass over the diagnosed class. **Model spend, bounded.**

Task `cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md` §2. The embedding-score detector
from `0b8ea847` §1.2 is **retired for classification** (DD-046: its thresholds were
transplanted from a name-to-definition comparison and only 12 of 289 terms reached 0.80). Its
output survives only to define **which terms a judge looks at**: the 139 band terms plus every
auto_keep term with an arm holding fewer than three members — the class where `s` is noise.
Auto-split terms are neither judged nor split; the score that produced them is discredited.

**What the judge sees, and what it must not.** One term per call: preferred label, scope note,
and up to three grounding spans per construct arm, quoted verbatim with the arm named and the
document titled. **Cosine, `s` and the `0b8ea847` class are withheld** — the population was
selected by that score, and showing a judge the selector invites it to ratify the selection
(adversarial-review rubric v1.3.0 §2 anti-anchoring, and the calibrated `cos=0.917` failure it
records). Where an arm's only spans are bare — `grounding_span` equal to `name`, which is true
of 1,561 Concept nodes — the prompt says *no context available for this arm* rather than
quoting the bare word, because a bare word is not evidence and pretending otherwise invites a
confident answer with nothing behind it.

    /opt/anaconda3/bin/python3 scripts/homograph_judge.py --dry-run
    /opt/anaconda3/bin/python3 scripts/homograph_judge.py --model claude-opus-5 --limit 10 --ceiling-tokens N
    /opt/anaconda3/bin/python3 scripts/homograph_judge.py --model claude-opus-5 --ceiling-tokens N
    /opt/anaconda3/bin/python3 scripts/homograph_judge.py --model claude-fable-5-1 --sample 50 --ceiling-tokens N
"""
from __future__ import annotations

import argparse
import collections
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
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

from harness.consumers import ClaudeCLIConsumer, ConsumerConfig  # noqa: E402
from kg import spend, vocab  # noqa: E402
from kg.extraction import model_stub  # noqa: E402

TASK = "cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md"
RUBRIC_VERSION = "v1.3.0"
OVERLAY = "homograph-sense (project-local, ai-readiness-kg)"
HOMO = REPO / "state" / "homograph_scores_2026-09-05.json"
POP = REPO / "state" / "homograph_population_2026-09-06.json"
EVIDENCE = REPO / "assessment" / "evidence" / "homograph_judge"
RESULTS = REPO / "assessment" / "results"

PROVIDER, CLI, CALL_CLASS = "claude_max_oauth", "claude", "judge"
ACCEPT_CONFIDENCE = 0.80
SAMPLE_SEED = 20260906
SPANS_PER_ARM = 3

#: §2.3 positive control. Both are auto_keep with a thin arm, so both are in the population by
#: construction; the gold sample measured `accessibility` as a live false merge.
POSITIVE_CONTROL = ("air:concept/accessibility", "air:concept/ai-ready")
NEGATIVE_CONTROL = ("JSON-LD", "RDF", "PROV-O", "ISO 8601", "DataCite")

ARM_NAMES = {"publication_actionability": "publication actionability",
             "org_maturity": "organisational maturity",
             "training_data_readiness": "training-data readiness"}

INSTRUCTIONS = """You are an adversarial reviewer deciding ONE vocabulary question.

A controlled vocabulary term is the canonical name for one thing. Below is a term and the
grounding spans of the nodes that currently resolve to it, grouped by the CONSTRUCT ARM of the
document each came from. The arms are three different literatures:

  * organisational maturity  — how ready an ORGANISATION is to adopt AI
  * publication actionability — whether a PUBLISHED DATA PRODUCT can be found and correctly
                                processed by an AI system
  * training-data readiness   — whether data is fit to be INPUT to model training

Your question is exactly this:

    Do the spans below all denote ONE thing, or does this label name DIFFERENT things in
    different arms?

Rules, and they are the point of the exercise:

1. A shared LABEL is not a shared meaning. "Accessibility" can be an organisational capability
   in a maturity model and a property of a data file in a quality framework; those are two
   things wearing one word.
2. Decide from the spans. If an arm has no context available, you cannot conclude the label
   means something different there — say `uncertain` rather than inventing a distinction.
3. Related is not the same, and narrower is not the same; but a single concept discussed from
   two angles IS the same. A vocabulary that splits every context produces a term per document
   and is useless.
4. `same_sense` is a real and useful answer. Do not manufacture a split to look decisive.
5. Quote the deciding phrase from EACH arm you rely on, verbatim.

Answer with exactly three lines and nothing else:
VERDICT: <one of same_sense, distinct_senses, uncertain>
CONFIDENCE: <a number between 0 and 1>
REASON: <one sentence, quoting the deciding phrase from each arm>"""

_V = re.compile(r"^\s*VERDICT\s*:\s*\**\s*(same_sense|distinct_senses|uncertain)\b", re.M | re.I)
_C = re.compile(r"^\s*CONFIDENCE\s*:\s*\**\s*([01](?:\.\d+)?)", re.M | re.I)
_R = re.compile(r"^\s*REASON\s*:\s*(.*)$", re.M | re.I | re.S)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def population(homo: dict) -> list:
    """§2.1: band terms, plus auto_keep terms with any arm holding < 3 members."""
    out = []
    for tid, x in sorted(homo["terms"].items()):
        if x["klass"] == "band" or (x["klass"] == "auto_keep" and min(x["arms"].values()) < 3):
            out.append(tid)
    return out


def members(session, tids: list) -> dict:
    rows = session.run(
        "MATCH (n)-[:RESOLVES_TO]->(t:Term) WHERE t.term_id IN $tids "
        "MATCH (d:Document {doc_id: n.doc_id}) "
        "RETURN t.term_id AS term, labels(n)[0] AS label, n.name AS name, "
        "       n.grounding_span AS span, d.title AS title, d.doc_id AS doc_id, "
        "       d.construct_arm AS arm", tids=tids).data()
    out: dict = collections.defaultdict(list)
    for r in rows:
        out[r["term"]].append(r)
    return dict(out)


def _bare(span, name) -> bool:
    n = " ".join((name or "").split()).lower()
    s = " ".join((span or "").split()).lower()
    return (not s) or s == n


def build_prompt(term: dict, mem: list) -> str:
    by_arm: dict = collections.defaultdict(list)
    for m in mem:
        by_arm[m["arm"]].append(m)
    blocks = [f"TERM\n  preferred label: {term['pref_label']}\n"
              f"  scope note: {(term.get('scope_note') or '(none)')[:500]}\n"]
    for arm in sorted(by_arm):
        rows = by_arm[arm]
        usable = [m for m in rows if not _bare(m["span"], m["name"])]
        blocks.append(f"\nARM: {ARM_NAMES.get(arm, arm)} ({len(rows)} node(s))")
        if not usable:
            # §2.2 says to declare the absence rather than quote the bare word, and that is
            # what happens here. The DOCUMENT TITLES are still listed, because a title is not
            # the bare word and it is demonstrably load-bearing evidence: the gold rater
            # judged `mitre-ai-maturity-model::d-accessibility` a distinct sense from exactly
            # this — "Node A's bare 'Accessibility' in an AI maturity model context is an
            # organizational-capability dimension". Withholding the title would blind the
            # judge to the only evidence a human-equivalent rater had.
            titles = sorted({m["title"] or m["doc_id"] for m in rows})
            blocks.append("  no span text available for this arm — every node's grounding "
                          "span is the bare term itself. Its node(s) come from:")
            for t in titles[:SPANS_PER_ARM]:
                blocks.append(f"    · {t}")
            continue
        for m in usable[:SPANS_PER_ARM]:
            blocks.append(f"  · [{m['label']}] \"{m['name']}\" — {m['title'] or m['doc_id']}\n"
                          f"    > {' '.join((m['span'] or '').split())[:600]}")
    return f"{INSTRUCTIONS}\n\n---\n\n" + "\n".join(blocks) + "\n"


def parse_answer(text: str) -> tuple:
    v = _V.search(text or "")
    if not v:
        return None, None, None
    c = _C.search(text or "")
    r = _R.search(text or "")
    return (v.group(1).lower(), float(c.group(1)) if c else None,
            " ".join((r.group(1) if r else "").split())[:700])


def decisions_path(label: str) -> Path:
    return RESULTS / f"homograph_decisions_2026-09-06_{label}.jsonl"


def read_decisions(label: str) -> dict:
    p = decisions_path(label)
    if not p.is_file():
        return {}
    return {json.loads(l)["term_id"]: json.loads(l)
            for l in p.read_text(encoding="utf-8").splitlines() if l.strip()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--ceiling-tokens", type=int, default=None)
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default=None, help="judge exactly this term_id")
    ap.add_argument("--sample", type=int, default=0,
                    help="rate a stratified sample of N (band/auto_keep, seed 20260906)")
    ap.add_argument("--label", default=None)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    homo = json.loads(HOMO.read_text(encoding="utf-8"))
    pop = population(homo)
    terms = vocab.project()

    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            mem = members(s, pop)
    finally:
        driver.close()

    POP.write_text(json.dumps({
        "task": TASK, "population": pop, "size": len(pop),
        "band": sum(1 for t in pop if homo["terms"][t]["klass"] == "band"),
        "auto_keep_thin_arm": sum(1 for t in pop if homo["terms"][t]["klass"] == "auto_keep"),
        "positive_control_in_population": {t: t in pop for t in POSITIVE_CONTROL},
    }, indent=1) + "\n", encoding="utf-8")

    parts = re.split(r"[^a-z0-9]+", a.model.lower())
    label = a.label or (parts[1] if len(parts) > 1 and parts[0] == "claude" else parts[0])

    todo = pop
    if a.only:
        if a.only not in pop:
            raise SystemExit(f"FATAL: {a.only} is not in the §2.1 population")
        todo = [a.only]
    elif a.sample:
        by_class: dict = collections.defaultdict(list)
        for t in pop:
            by_class[homo["terms"][t]["klass"]].append(t)
        rng = random.Random(SAMPLE_SEED)
        todo, i = [], 0
        keys = sorted(by_class)
        while len(todo) < a.sample:
            drawn = False
            for k in keys:
                if i < len(by_class[k]):
                    todo.append(sorted(by_class[k])[i])
                    drawn = True
                    if len(todo) >= a.sample:
                        break
            if not drawn:
                break
            i += 1
        rng.shuffle(todo)

    if a.dry_run:
        tid = POSITIVE_CONTROL[0] if POSITIVE_CONTROL[0] in todo else todo[0]
        p = build_prompt(terms[tid], mem.get(tid, []))
        print(f"--- {tid} ({len(p)} chars) ---\n{p}")
        sizes = [len(build_prompt(terms[t], mem.get(t, []))) for t in todo]
        print(f"\npopulation {len(pop)}; this pass {len(todo)}; prompt chars "
              f"min {min(sizes)} max {max(sizes)} mean {sum(sizes)//len(sizes)}")
        return 0

    model_stub.guard_no_api_key()
    if not a.ceiling_tokens:
        raise SystemExit("FATAL: --ceiling-tokens required before any model call (DD-022)")
    run_id = a.run_id or f"homograph_judge_{label}_2026-09-06"
    ledger = spend.default_ledger()
    ledger.declare(run_id, a.ceiling_tokens,
                   declared_by=f"scripts/homograph_judge.py ({TASK})", call_class=CALL_CLASS)
    spend.set_current_run(run_id)
    consumer = ClaudeCLIConsumer(ConsumerConfig(model_id=a.model, provider=PROVIDER, cli=CLI,
                                                timeout_seconds=a.timeout, call_class=CALL_CLASS))
    ev_dir = EVIDENCE / label
    ev_dir.mkdir(parents=True, exist_ok=True)
    have = read_decisions(label)
    remaining = [t for t in todo if t not in have]
    if a.limit:
        remaining = remaining[:a.limit]

    made, stop = 0, "pass_complete"
    with decisions_path(label).open("a", encoding="utf-8") as fh:
        for tid in remaining:
            prompt = build_prompt(terms[tid], mem.get(tid, []))
            try:
                completion = consumer.complete(prompt, call_id=f"homo.{tid.replace('/', '_')}")
            except spend.SpendRefusalStop as refusal:
                stop = f"spend_refusal: {refusal}"
                break
            if completion.model_id != a.model:
                raise SystemExit(f"FATAL: envelope reports {completion.model_id!r}, expected {a.model!r}")
            verdict, conf, reason = parse_answer(completion.text)
            rec = {"term_id": tid, "pref_label": terms[tid]["pref_label"],
                   "klass": homo["terms"][tid]["klass"], "arms": homo["terms"][tid]["arms"],
                   "rater": a.model, "rubric_version": RUBRIC_VERSION, "overlay": OVERLAY,
                   "verdict": verdict, "confidence": conf, "reason": reason,
                   "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                   "usage": completion.usage, "ts": _now()}
            (ev_dir / f"{tid.replace('/', '_').replace(':', '_')}.{a.model}.json").write_text(
                json.dumps({**rec, "prompt": prompt, "response_text": completion.text}, indent=1),
                encoding="utf-8")
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fh.flush()
            made += 1

    settled = ledger.status().get("runs", {}).get(run_id, {})
    print(json.dumps({"run_id": run_id, "rater": a.model, "population": len(pop),
                      "judged_this_pass": made, "stop": stop,
                      "settled_tokens": settled.get("settled"),
                      "tokens_per_term": round(settled.get("settled", 0) / made, 1) if made else None,
                      "file": str(decisions_path(label).relative_to(REPO))}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
