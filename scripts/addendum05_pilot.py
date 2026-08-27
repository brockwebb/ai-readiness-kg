#!/usr/bin/env python3
"""ADDENDUM-05 §2 + §3b runner.

Phases (each idempotent; each retries once after a sleep-to-00:05Z on a scope=daily
refusal, per ADDENDUM-02's band rule):

  doc5         extract `mitre-ai-maturity-model` under the re-declared 9M
               `pilot_v035b_opus5` run (the 4 banked extractions are reused, not re-run),
               append to the tagged shard, then re-run the §3a triage so doc 5's
               proposed_relationships join the candidate pool.
  instr_judge  §2: Instrument-stratum judge over all 5 docs' admitted Instrument nodes
               (re-derived from the persisted raws), cap 120 facts, raters
               opus-4-8 + sonnet-5, Dawid-Skene; standalone verdict
               docs/research/2026-08-27_pilot_instrument_verdict.md.
  edge_judge   §3b: judge single_span + evidence_set candidates (cap 120 random) with the
               located evidence set presented as grounding; run `edge_suppression_judge`,
               ceiling 2M; pre-registered read: fact-level entailed >= 0.85 pooled ==>
               v0.3.6 justified. Verdict docs/research/2026-08-27_edge_suppression_judge_verdict.md.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import random
import subprocess
import sys
import time
import uuid
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

from kg import eventlog, spend                              # noqa: E402
from kg.extraction import model_stub, parser, grounding     # noqa: E402
from kg.extraction.pipeline import _apply_provenance_ownership  # noqa: E402
import run_bulk_extraction as rbe                           # noqa: E402
import addendum05_triage as triage                          # noqa: E402

TASK = "cc_tasks/2026-08-26_overnight_burn.md (ADDENDUM-05)"
PY = sys.executable
PILOT_RUN = "pilot_v035b_opus5"
PILOT_DOCS = triage.PILOT_DOCS
DOC5 = "mitre-ai-maturity-model"
SHARD_NO, TAG = 13, "reextract_v035b"
RAW_DIR = triage.RAW_DIR
WALL_STOP = "2026-08-28T03:30:00+00:00"
F_STOP, ITEM_FAITHFUL, ENTAIL_PASS = 0.10, 0.70, 0.85
INSTR_VERDICT = REPO / "docs/research/2026-08-27_pilot_instrument_verdict.md"
EDGE_VERDICT = REPO / "docs/research/2026-08-27_edge_suppression_judge_verdict.md"


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


def wall_ok() -> bool:
    return now_utc() < datetime.datetime.fromisoformat(WALL_STOP)


def sleep_to_roll() -> bool:
    roll = now_utc().replace(hour=0, minute=5, second=0, microsecond=0)
    if roll <= now_utc():
        roll += datetime.timedelta(days=1)
    if roll >= datetime.datetime.fromisoformat(WALL_STOP):
        return False
    print(f"daily band: sleeping until {roll.isoformat()}", flush=True)
    while now_utc() < roll:
        time.sleep(min(120, max(1, (roll - now_utc()).total_seconds())))
    return True


def daily_refused_since(run_id: str, since_iso: str) -> bool:
    for line in spend.default_ledger().path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("record") == "refuse" and r.get("run_id") == run_id \
                and r.get("scope") == "daily" and r.get("ts", "") >= since_iso:
            return True
    return False


def members_all() -> dict:
    out = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof)
        out.update(rbe.corpus_members())
    # leave the v0.3.5 pinned template active for extraction (sha-verified)
    rbe.apply_profile("reextract_v035")
    return out


def pilot_outputs() -> dict[str, dict]:
    """doc_id -> merged parsed-output dict from the persisted opus-5 raws."""
    outs = {}
    for d in PILOT_DOCS:
        raws = sorted(RAW_DIR.glob(f"{d}.*.json"))
        if not raws:
            continue
        raw = json.loads(raws[-1].read_text())
        out = triage.merged_pilot_output(raw.get("raw_result") or "")
        if out:
            outs[d] = out
    return outs


# ------------------------------------------------------------------ phase doc5
def phase_doc5() -> int:
    members = members_all()
    if sorted(RAW_DIR.glob(f"{DOC5}.*.json")):
        print("doc5 already extracted; skipping")
        return 0
    spend.set_current_run(PILOT_RUN)
    text = rbe.doc_text(members[DOC5])
    sha = hashlib.sha256(members[DOC5].read_bytes()).hexdigest()
    meta = model_stub.invoke_with_layer_fallback(DOC5, text)
    output = _apply_provenance_ownership(meta["output"], DOC5)
    result = parser.parse_extraction(output, text, enforce_span_coverage=True)
    (RAW_DIR / f"{DOC5}.{sha[:12]}.{model_stub.prompt_version()}.{meta['model_id']}.json").write_text(
        json.dumps({"doc_id": DOC5, "usage": meta["usage"], "cost_usd": meta.get("cost_usd"),
                    "emission_mode": meta.get("emission_mode") or "single_pass",
                    "raw_result": meta["raw_result"]}, ensure_ascii=False, indent=1) + "\n")
    ex_id = uuid.uuid4().hex
    prov = {**model_stub.provenance_stamp(ex_id, model_id=meta["model_id"]),
            "corpus_epoch": "reextract-v035-pilot", "source_sha256": sha}
    kept_n = kept_e = 0
    for nrec in result.nodes:
        if nrec["type"] != "Instrument":
            continue
        eventlog.append({"event_type": "node_asserted", "purpose": "reextract",
                         "doc_id": DOC5, "provenance": prov,
                         "payload": {"id": nrec["id"], "type": "Instrument",
                                     "item": nrec["item"]}}, batch=SHARD_NO, tag=TAG)
        kept_n += 1
    for erec in result.edges:
        if erec["type"] not in parser.SEMANTIC_EDGE_TYPES:
            continue
        eventlog.append({"event_type": "edge_asserted", "purpose": "reextract",
                         "doc_id": DOC5, "provenance": prov,
                         "payload": {"type": erec["type"], "from_id": erec["from_id"],
                                     "to_id": erec["to_id"], "item": erec["item"]}},
                        batch=SHARD_NO, tag=TAG)
        kept_e += 1
    eventlog.append({"event_type": "reextract_pilot_metrics", "purpose": "reextract",
                     "doc_id": DOC5, "counts": result.counts(), "instruments": kept_n,
                     "semantic_edges": kept_e,
                     "span_lacks_name": result.precheck_span_lacks_name,
                     "emission": meta.get("emission_mode") or "single_pass",
                     "output_tokens": int((meta.get("usage") or {}).get("outputTokens", 0) or 0),
                     "task": TASK}, batch=SHARD_NO, tag=TAG)
    print(f"doc5: {kept_n} instruments, {kept_e} semantic edges, "
          f"emission {meta.get('emission_mode') or 'single_pass'}")
    subprocess.run([PY, "scripts/addendum05_triage.py"], cwd=REPO, check=True)
    return 0


# ------------------------------------------------------------------ shared judging bits
def window_for(norm: str, span: str) -> str | None:
    nspan = grounding.normalize(span)
    i = norm.find(nspan)
    return norm[max(0, i - 400): i + len(nspan) + 400] if i >= 0 else None


def write_sample(prefix: str, recs: list[dict]) -> None:
    (REPO / f"corpus/staging/metrics/{prefix}_sample.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs), encoding="utf-8")


def run_protocol(prefix: str, run: str, run_id: str, raters: list[str],
                 fact_cap: int | None, env_extra: dict) -> dict | None:
    import os
    env = dict(os.environ)
    env[spend.RUN_ENV] = run_id
    env.update(env_extra)
    r = subprocess.run([PY, "scripts/probe_decompose.py", "--prefix", prefix],
                       cwd=REPO, env=env, capture_output=True, text=True, timeout=3600)
    print(r.stdout[-600:], r.stderr[-300:], flush=True)
    if r.returncode != 0:
        return None
    fact_args = []
    if fact_cap is not None:
        facts_path = REPO / f"corpus/staging/metrics/{prefix}_facts.jsonl"
        fids = [json.loads(l)["fact_id"] for l in facts_path.read_text().splitlines() if l.strip()]
        rng = random.Random(prefix)
        sel = fids if len(fids) <= fact_cap else rng.sample(fids, fact_cap)
        sel_path = REPO / f"corpus/staging/metrics/{prefix}_fact_sel.json"
        sel_path.write_text(json.dumps(sel))
        fact_args = ["--fact-ids-file", str(sel_path)]
    for model in raters:
        r = subprocess.run([PY, "scripts/probe_judge.py", "--prefix", prefix, "--run", run,
                            "--batch", "10", "--model", model, *fact_args],
                           cwd=REPO, env=env, capture_output=True, text=True, timeout=7200)
        print(r.stdout[-600:], r.stderr[-300:], flush=True)
        if r.returncode != 0:
            return None
    r = subprocess.run([PY, "scripts/probe_aggregate.py", "--prefix", prefix, "--run", run],
                       cwd=REPO, env=env, capture_output=True, text=True, timeout=600)
    print(r.stdout[-1000:], r.stderr[-300:], flush=True)
    agg = REPO / f"corpus/staging/metrics/{prefix}_aggregate.json"
    return json.loads(agg.read_text()) if agg.exists() else None


# ------------------------------------------------------------------ phase instr_judge
def phase_instr_judge() -> int:
    members = members_all()
    outs = pilot_outputs()
    cfg = model_stub.load_model_config()
    fresh, texts, per_doc = [], {}, {}
    for d, out in outs.items():
        text = rbe.doc_text(members[d])
        texts[d] = grounding.normalize(text)
        res = parser.parse_extraction(_apply_provenance_ownership(out, d), text,
                                      enforce_span_coverage=True)
        instr = [n for n in res.nodes if n["type"] == "Instrument"]
        per_doc[d] = len(instr)
        for n in instr:
            fresh.append((d, n["item"]))
    total = sum(per_doc.values())
    print("instrument counts:", per_doc, "pooled:", total)
    if total < 20:
        INSTR_VERDICT.write_text(
            "# Instrument-stratum verdict (ADDENDUM-05 §2): FAIL:precondition\n\n"
            f"Pooled Instrument nodes {total} < 20 after doc 5. Per-doc: {per_doc}\n")
        return 1
    recs = []
    for d, item in fresh:
        span = item.get("grounding_span") or ""
        recs.append({"item_id": item.get("id"), "event_id": uuid.uuid4().hex,
                     "kind": "node", "type": "Instrument", "stratum": "Instrument:pilot",
                     "text": item.get("name") or "", "grounding_span": span, "doc_id": d,
                     "extra": item, "window": window_for(texts[d], span)})
    write_sample("pilot_instrB", recs)
    spend.set_current_run(PILOT_RUN)
    agg = run_protocol("pilot_instrB", "pilot_instrB", PILOT_RUN,
                       [cfg["primary_judge_model_id"], cfg["secondary_judge_model_id"]],
                       fact_cap=120, env_extra={})
    if not agg:
        print("protocol failed"); return 2
    s = (agg.get("per_stratum") or {}).get("Instrument:pilot") or {}
    faithful = (agg.get("items") or {}).get("faithful_rate")
    ok = s.get("F_hi") is not None and s["F_hi"] < F_STOP and (faithful or 0) >= ITEM_FAITHFUL
    settled = spend.default_ledger().status(PILOT_RUN)["runs"][PILOT_RUN]["settled"]
    INSTR_VERDICT.write_text("\n".join([
        f"# Instrument-stratum verdict (ADDENDUM-05 §2): {'PASS' if ok else 'FAIL'}", "",
        f"Run `{PILOT_RUN}` (re-declared 9M per §0): settled {settled:,}; "
        f"cost/doc ~{settled // 5:,} (informational). Model `claude-opus-5`, prompt v0.3.5; "
        f"raters {cfg['primary_judge_model_id']} + {cfg['secondary_judge_model_id']}.",
        f"Per-doc admitted Instruments: {per_doc} (pooled {total} ≥ 20).",
        f"Facts judged: {s.get('n_in_F_denominator')} in F-denominator; "
        f"Dawid-Skene {agg.get('method')}.", "",
        f"| F | F_upper | pass(<{F_STOP}) | item-faithful | pass(≥{ITEM_FAITHFUL}) |",
        "|---|---|---|---|---|",
        f"| {s.get('F')} | {s.get('F_hi')} | {'Y' if (s.get('F_hi') or 1) < F_STOP else 'N'} "
        f"| {faithful} | {'Y' if (faithful or 0) >= ITEM_FAITHFUL else 'N'} |", "",
        "Per-rater agreement:", "```json", json.dumps(agg.get("raters"), indent=1), "```", "",
        "**Consequence (per §2):** " + (
            "Instrument stratum unlocked — Lane 2 may supersede `[instrument]` only; "
            "Lane 3 still waits for the semantic stratum." if ok else
            "Instrument stratum stays closed; Lanes 2/3 closed."), ""]), encoding="utf-8")
    print("instrument verdict:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# ------------------------------------------------------------------ phase edge_judge (3b)
def phase_edge_judge() -> int:
    run_id = "edge_suppression_judge"
    spend.default_ledger().declare(run_id, 2_000_000, declared_by=TASK, call_class="judge")
    spend.set_current_run(run_id)
    cfg = model_stub.load_model_config()
    cands = [json.loads(l) for l in
             (REPO / "corpus/staging/metrics/edge_suppression_candidates.jsonl")
             .read_text().splitlines() if l.strip()]
    loc = [c for c in cands if c["class"] in ("single_span", "evidence_set")]
    if len(loc) < 20:
        EDGE_VERDICT.write_text(
            "# Edge-suppression judge (ADDENDUM-05 §3b): NOT RUN\n\n"
            f"Locatable candidates {len(loc)} < 20 — the semantic stratum's problem is not "
            "the span rule (per §3a rule). Stratum closed for today; no v0.3.6.\n")
        return 1
    rng = random.Random("edge_suppression")
    sample = loc if len(loc) <= 120 else rng.sample(loc, 120)
    recs = []
    for i, c in enumerate(sample):
        evidence = " ".join((c.get("evidence") or {}).get("sentences") or [])
        recs.append({"item_id": f"cand{i}", "event_id": uuid.uuid4().hex, "kind": "edge",
                     "type": "edge", "stratum": f"suppressed:{c['class']}",
                     "text": f"{(c['from'] or ['?'])[0]} {c['edge_type']} {(c['to'] or ['?'])[0]}",
                     "grounding_span": evidence, "doc_id": c["doc_id"],
                     "extra": {"from_id": (c["from"] or ["?"])[0], "edge_type": c["edge_type"],
                               "to_id": (c["to"] or ["?"])[0]},
                     "window": None})
    write_sample("edge_supp", recs)
    agg = run_protocol("edge_supp", "edge_supp", run_id,
                       [cfg["primary_judge_model_id"], cfg["secondary_judge_model_id"]],
                       fact_cap=None, env_extra={})
    if not agg:
        print("protocol failed"); return 2
    per_fact = agg.get("per_fact") or {}
    n = len(per_fact)
    entailed = sum(1 for v in per_fact.values() if v.get("entailed"))
    rate = entailed / n if n else 0.0
    ok = rate >= ENTAIL_PASS
    by_stratum = {}
    for s, r in (agg.get("per_stratum") or {}).items():
        ent = sum(1 for v in per_fact.values() if v.get("stratum") == s and v.get("entailed"))
        tot = sum(1 for v in per_fact.values() if v.get("stratum") == s)
        by_stratum[s] = f"{ent}/{tot}"
    settled = spend.default_ledger().status(run_id)["runs"][run_id]["settled"]
    EDGE_VERDICT.write_text("\n".join([
        f"# Edge-suppression judge (ADDENDUM-05 §3b): "
        f"{'OVER-SUPPRESSION — v0.3.6 justified' if ok else 'suppression is correct — no v0.3.6'}", "",
        f"Candidates judged: {len(sample)} of {len(loc)} locatable (§3a); evidence sets "
        f"presented as grounding. Raters {cfg['primary_judge_model_id']} + "
        f"{cfg['secondary_judge_model_id']}, Dawid-Skene {agg.get('method')}; run `{run_id}` "
        f"settled {settled:,} (ceiling 2M).", "",
        f"**Fact-level entailed: {entailed}/{n} = {rate:.3f}** "
        f"(pre-registered pass ≥ {ENTAIL_PASS}). Per class: {by_stratum}", "",
        "Per-rater agreement:", "```json", json.dumps(agg.get("raters"), indent=1), "```", ""]),
        encoding="utf-8")
    print(f"edge judge: entailed {rate:.3f} ->", "v0.3.6 justified" if ok else "no v0.3.6")
    return 0 if ok else 1


PHASES = {"doc5": (phase_doc5, PILOT_RUN), "instr_judge": (phase_instr_judge, PILOT_RUN),
          "edge_judge": (phase_edge_judge, "edge_suppression_judge")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=sorted(PHASES), required=True)
    a = ap.parse_args()
    model_stub.guard_no_api_key()
    fn, run_id = PHASES[a.phase]
    while True:
        t0 = now_utc().isoformat()
        try:
            rc = fn()
        except spend.SpendRefusalStop as exc:
            if exc.refusal.scope == "daily" and wall_ok() and sleep_to_roll():
                continue
            print(f"spend guard: {exc} — stop", flush=True)
            return 4
        if rc == 2 and daily_refused_since(run_id, t0) and wall_ok():
            if sleep_to_roll():
                continue
        return rc


if __name__ == "__main__":
    raise SystemExit(main())
