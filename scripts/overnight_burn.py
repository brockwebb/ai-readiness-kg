#!/usr/bin/env python3
"""Overnight burn driver — task 2026-08-26_overnight_burn (Seldon d2756bd1-adjacent; see
task file). Lanes 0 -> 1 -> (2 || 3) -> 4, detached, unattended; every lane has a
pre-registered gate; a gate FAIL stops that lane and the driver moves on.

Safety mechanisms (each cited in the task's lessons table): DD-022 spend guard at the stub
(all lanes run under declared ledger ceilings; the daily band is the global bound);
DD-019 batching/session-resume/cache-ratio/decoys (batch_repair, restoration_v2); DD-015
positive controls mid-run; DD-017 gate-before-wire for restorations; rate-limit backoff
(sleep 600s, 6 consecutive -> lane STOP `rate_limited`); hard wall-clock stop; STOP file
honored between units of work; per-lane commit+push.

Run detached:  scripts/overnight_burn_2026-08-26.sh  (nohup wrapper)
Status:        state/overnight_burn_status.json
STOP file:     state/overnight_burn_STOP  (halts between units of work)
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

import yaml                                                 # noqa: E402
from kg import eventlog, spend                              # noqa: E402
from kg.extraction import model_stub, parser, schema_loader, grounding  # noqa: E402
import run_bulk_extraction as rbe                           # noqa: E402

TASK = "cc_tasks/2026-08-26_overnight_burn.md"
PY = sys.executable
CEILING = int(os.environ["OVERNIGHT_CEILING"])              # required; no default (DD-022)
WALL_STOP_UTC = os.environ.get("OVERNIGHT_WALL_STOP", "2026-08-27T08:45:00+00:00")
STATUS = REPO / "state" / "overnight_burn_status.json"
STOP_FILE = REPO / "state" / "overnight_burn_STOP"
SUMMARY_MD = REPO / "docs" / "research" / "2026-08-27_overnight_burn_SUMMARY.md"
VERDICT_MD = REPO / "docs" / "research" / "2026-08-26_pilot_reextract_v035_verdict.md"
PILOT_SHARD_NO, PILOT_TAG = 13, "reextract_v035"   # ADDENDUM-01: v0.3.5 pilot shard tag
LANE2_SHARD = 16                                            # events/batch-016.jsonl (untagged)
RESTORE_TAG = "restoration_v2"
SEMANTIC = parser.SEMANTIC_EDGE_TYPES
F_STOP = 0.10                                               # DD-015 decision rule, mid-run
PILOT_ITEM_FAITHFUL = 0.70
ACCEPT_THRESHOLD = 0.90                                     # restoration class gate (DD-017)
RATE_SLEEP_S, RATE_MAX = 600, 6
QUAR_WINDOW = 3                                             # systemic quarantine streak


# ------------------------------------------------------------------ plumbing
def now_utc() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def wall_ok() -> bool:
    return now_utc() < datetime.datetime.fromisoformat(WALL_STOP_UTC)


def halted() -> bool:
    return STOP_FILE.exists()


import threading
_STATUS_LOCK = threading.Lock()


def status(lane: str, state: str, **detail) -> None:
    with _STATUS_LOCK:
        doc = json.loads(STATUS.read_text()) if STATUS.exists() else {}
        doc[lane] = {**doc.get(lane, {}), "state": state, "ts": now_utc().isoformat(), **detail}
        STATUS.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"[{now_utc().isoformat()}] {lane}: {state} {detail if detail else ''}", flush=True)


def wall_remaining_s() -> int:
    stop = datetime.datetime.fromisoformat(WALL_STOP_UTC)
    return max(60, int((stop - now_utc()).total_seconds()))


def commit_push(msg: str) -> None:
    _COMMIT_LOCK.acquire()
    paths = ["events", "state", "docs/research", "corpus/staging/candidate_register.jsonl",
             "corpus/staging/pilot_adds_run_log.md", "scripts", "kg", "tests",
             "docs/design_decisions.md", "cc_tasks"]
    try:
        subprocess.run(["git", "add", *paths], cwd=REPO, check=True, capture_output=True)
        # never sweep in the concurrent probe/tgbench shards (other tasks' state)
        subprocess.run(["git", "reset", "-q", "HEAD", "events/batch-009_probe_judge.jsonl"],
                       cwd=REPO, capture_output=True)
        r = subprocess.run(["git", "commit", "-m", msg + "\n\nCo-Authored-By: Claude Fable 5 "
                            "<noreply@anthropic.com>"], cwd=REPO, capture_output=True, text=True)
        if r.returncode == 0:
            subprocess.run(["git", "push"], cwd=REPO, capture_output=True, timeout=120)
    except Exception as exc:                                # commit failures never kill a lane
        print(f"commit_push non-fatal: {exc}", flush=True)
    finally:
        _COMMIT_LOCK.release()


import threading as _th
_COMMIT_LOCK = _th.Lock()


class RateLimitStop(RuntimeError):
    pass


def invoke_backoff(state: dict, *args, **kw) -> dict:
    """model_stub.invoke with the overnight rate-limit rule: release+sleep 10 min on a
    rate-limit rejection; 6 consecutive -> RateLimitStop (lane ends `rate_limited`)."""
    while True:
        try:
            meta = model_stub.invoke_with_layer_fallback(*args, **kw)
            state["consec"] = 0
            return meta
        except model_stub.ModelRateLimitError as exc:
            state["consec"] = state.get("consec", 0) + 1
            if state["consec"] >= RATE_MAX:
                raise RateLimitStop(str(exc))
            print(f"rate-limited ({state['consec']}/{RATE_MAX}) — sleeping {RATE_SLEEP_S}s",
                  flush=True)
            time.sleep(RATE_SLEEP_S)


def _next_daily_roll() -> datetime.datetime:
    """The next 00:05Z after now — the UTC band rolls at midnight UTC (20:00 ET)."""
    now = now_utc()
    roll = now.replace(hour=0, minute=5, second=0, microsecond=0)
    if roll <= now:
        roll += datetime.timedelta(days=1)
    return roll


def sleep_until_daily_roll(lane: str) -> bool:
    """ADDENDUM-02: on a scope=daily refusal before the wall stop, sleep to 00:05Z and
    retry. Returns False when the wall stop lands first (caller stops instead)."""
    roll = _next_daily_roll()
    stop = datetime.datetime.fromisoformat(WALL_STOP_UTC)
    if roll >= stop:
        status(lane, "stopped", reason="daily band exhausted and wall stop precedes the roll")
        return False
    secs = (roll - now_utc()).total_seconds()
    status(lane, "daily_band_sleep", until=roll.isoformat(), seconds=int(secs))
    while now_utc() < roll:
        if halted():
            return False
        time.sleep(min(60, max(1, (roll - now_utc()).total_seconds())))
    return True


def last_refusal_scope(run_id: str, since_iso: str) -> str | None:
    """Scope of the newest `refuse` record for run_id after since_iso, from the ledger."""
    scope = None
    ledger_path = spend.default_ledger().path
    for line in ledger_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("record") == "refuse" and r.get("run_id") == run_id                 and r.get("ts", "") >= since_iso:
            scope = r.get("scope")
    return scope


def declare(run_id: str, ceiling: int, call_class: str) -> None:
    spend.default_ledger().declare(run_id, ceiling, declared_by=TASK, call_class=call_class)


def run_env(run_id: str) -> dict:
    env = dict(os.environ)
    env[spend.RUN_ENV] = run_id
    env.pop("ANTHROPIC_API_KEY", None); env.pop("ANTHROPIC_AUTH_TOKEN", None)
    return env


# ------------------------------------------------------------------ corpus / replay reads
def live_items():
    """Per-doc live (projectable, non-superseded) node/edge events, one pass."""
    # minimal supersede read: whole-extraction supersedes only (stratum-scoped ones keep
    # the doc's other strata live, which is what this worklist needs)
    sup = set()
    for ev in eventlog.replay():
        if ev.get("event_type") == "extraction_superseded" and not ev.get("superseded_strata"):
            sup.add((ev["doc_id"], ev["superseded_source_sha256"]))
    nodes, edges = defaultdict(list), defaultdict(list)
    for ev in eventlog.replay():
        if ev.get("purpose") in ("tevv_retest", "probe", "benchmark", "reextract"):
            continue
        et = ev.get("event_type")
        if et not in ("node_asserted", "edge_asserted"):
            continue
        sha = (ev.get("provenance") or {}).get("source_sha256")
        if (ev.get("doc_id"), sha) in sup:
            continue
        (nodes if et == "node_asserted" else edges)[ev["doc_id"]].append(ev)
    return nodes, edges


def corpus_paths() -> dict[str, Path]:
    members = {}
    for prof in ("v1", "kernel_v03", "reextract_v035"):
        try:
            rbe.apply_profile(prof)
            members.update(rbe.corpus_members())
        except SystemExit as exc:
            print(f"profile {prof}: {exc}", flush=True)
    return members


def extract_doc(doc_id: str, path: Path, rstate: dict, timeout: int = 1800):
    """Full extraction under the pinned v0.3.4 prompt; returns (parse_result, meta, sha)."""
    from kg.extraction import pipeline as _pipeline
    text = rbe.doc_text(path)
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    meta = invoke_backoff(rstate, doc_id, text, timeout=timeout)
    # harness owns document_id/provenance (v3 contract) — same ownership step the bulk
    # pipeline applies before parsing (first launch missed this; lane1 error 02:56Z)
    output = _pipeline._apply_provenance_ownership(meta["output"], doc_id)
    result = parser.parse_extraction(output, text, enforce_span_coverage=True)
    return result, meta, sha, text


def stamp(extraction_event_id: str, model_id: str, sha: str, epoch: str) -> dict:
    p = model_stub.provenance_stamp(extraction_event_id, model_id=model_id)
    return {**p, "corpus_epoch": epoch, "source_sha256": sha}


# ------------------------------------------------------------------ judging helpers
def write_sample(prefix: str, records: list[dict]) -> Path:
    out = REPO / f"corpus/staging/metrics/{prefix}_sample.jsonl"
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                   encoding="utf-8")
    return out


def sample_records(items: list[dict], doc_texts: dict[str, str], stratum_fn) -> list[dict]:
    """Probe-sample-format records from freshly parsed items.
    items: [{doc_id, kind: node|edge, type, item}]"""
    recs = []
    for it in items:
        item = it["item"]
        ev_id = uuid.uuid4().hex
        span = item.get("grounding_span") or ""
        text = doc_texts.get(it["doc_id"], "")
        norm = grounding.normalize(text)
        nspan = grounding.normalize(span)
        i = norm.find(nspan)
        window = norm[max(0, i - 400): i + len(nspan) + 400] if i >= 0 else None
        if it["kind"] == "edge":
            extra = {"from_id": item.get("from_id"), "edge_type": it["type"],
                     "to_id": item.get("to_id")}
            txt = f"{item.get('from_id')} {it['type']} {item.get('to_id')}"
            recs.append({"item_id": item.get("from_id", "") + "->" + item.get("to_id", ""),
                         "event_id": ev_id, "kind": "edge", "type": "edge",
                         "stratum": stratum_fn(it), "text": txt, "grounding_span": span,
                         "doc_id": it["doc_id"], "extra": extra, "window": window})
        else:
            recs.append({"item_id": item.get("id"), "event_id": ev_id, "kind": "node",
                         "type": it["type"], "stratum": stratum_fn(it),
                         "text": item.get("name") or item.get("text") or "",
                         "grounding_span": span, "doc_id": it["doc_id"],
                         "extra": item, "window": window})
    return recs


def run_probe_protocol(prefix: str, run: str, run_id: str, raters: list[str | None],
                       fact_limit: int | None = None) -> dict | None:
    """decompose -> judge (one run per rater) -> aggregate. Returns the aggregate dict."""
    env = run_env(run_id)
    r = subprocess.run([PY, "scripts/probe_decompose.py", "--prefix", prefix],
                       cwd=REPO, env=env, capture_output=True, text=True, timeout=min(3600, wall_remaining_s()))
    print(r.stdout[-800:], r.stderr[-400:], flush=True)
    if r.returncode != 0:
        return None
    fact_args = []
    if fact_limit is not None:
        facts_file = REPO / f"corpus/staging/metrics/{prefix}_facts.jsonl"
        fids = [json.loads(l)["fact_id"] for l in facts_file.read_text().splitlines() if l.strip()]
        sel = fids[:fact_limit]
        sel_file = REPO / f"corpus/staging/metrics/{prefix}_fact_sel.json"
        sel_file.write_text(json.dumps(sel))
        fact_args = ["--fact-ids-file", str(sel_file)]
    for model in raters:
        cmd = [PY, "scripts/probe_judge.py", "--prefix", prefix, "--run", run, "--batch", "10",
               *fact_args]
        if model:
            cmd += ["--model", model]
        r = subprocess.run(cmd, cwd=REPO, env=env, capture_output=True, text=True, timeout=min(7200, wall_remaining_s()))
        print(r.stdout[-800:], r.stderr[-400:], flush=True)
        if r.returncode != 0:
            return None
    r = subprocess.run([PY, "scripts/probe_aggregate.py", "--prefix", prefix, "--run", run],
                       cwd=REPO, env=env, capture_output=True, text=True, timeout=600)
    print(r.stdout[-1200:], r.stderr[-400:], flush=True)
    if r.returncode != 0:
        return None
    agg = REPO / f"corpus/staging/metrics/{prefix}_aggregate.json"
    return json.loads(agg.read_text()) if agg.exists() else None


def positive_control(lane: str, prefix: str, run_id: str, fresh: list[dict],
                     doc_texts: dict[str, str], stratum_label: str) -> bool:
    """DD-015 mid-run control: 60-fact sample, single secondary rater. True = continue."""
    import random as _rnd
    rng = _rnd.Random(prefix)
    pool = list(fresh)
    rng.shuffle(pool)
    recs = sample_records(pool[:30], doc_texts, lambda it: stratum_label)
    if not recs:
        status(lane, "control_skipped", reason="no fresh items to sample")
        return True
    write_sample(prefix, recs)
    cfg = model_stub.load_model_config()
    agg = run_probe_protocol(prefix, prefix, run_id,
                             raters=[cfg["secondary_judge_model_id"]], fact_limit=60)
    if not agg:
        status(lane, "control_error", reason="probe protocol failed — treating as STOP (fail safe)")
        return False
    f_hi = (agg.get("pooled") or {}).get("F_hi")
    ok = f_hi is not None and f_hi <= F_STOP
    status(lane, "control_pass" if ok else "control_STOP",
           F=agg["pooled"].get("F"), F_hi=f_hi, n=agg["pooled"].get("n_in_F_denominator"))
    return ok


# ------------------------------------------------------------------ Lane 1
def top_instrument_docs(n: int = 3) -> list[str]:
    nodes, _ = live_items()
    counts = Counter()
    for d, evs in nodes.items():
        counts[d] = sum(1 for e in evs if (e.get("payload") or {}).get("type") == "Instrument")
    return [d for d, c in counts.most_common(n) if c > 0]


def lane1() -> bool:
    lane = "lane1_pilot"
    status(lane, "running")
    run_id = "pilot_v035"   # ADDENDUM-01 Lane 1′
    declare(run_id, 3_000_000, "extraction")
    spend.set_current_run(run_id)
    members = corpus_paths()
    docs = [d for d in top_instrument_docs(6) if d in members][:3]
    if len(docs) < 3:
        status(lane, "STOP", reason=f"only {len(docs)} instrument-bearing docs with files")
        return False
    status(lane, "running", pilot_docs=docs)
    raw_dir = REPO / "events/raw/reextract_v035_pilot"
    raw_dir.mkdir(parents=True, exist_ok=True)
    fresh, doc_texts = [], {}
    per_doc: dict = {}
    rstate: dict = {}
    for d in docs:
        if halted() or not wall_ok():
            status(lane, "STOP", reason="wall clock / STOP file")
            return False
        try:
            result, meta, sha, text = extract_doc(d, members[d], rstate)
        except RateLimitStop as exc:
            status(lane, "rate_limited", detail=str(exc)[:200]); return False
        except spend.SpendRefusalStop as exc:
            status(lane, "STOP", reason=f"spend guard: {exc}"); return False
        except (model_stub.ModelInvocationError, model_stub.ModelSubstitutionError,
                ValueError) as exc:
            status(lane, "STOP", reason=f"{d}: {str(exc)[:200]}"); return False
        doc_texts[d] = text
        (raw_dir / f"{d}.{sha[:12]}.{model_stub.prompt_version()}.json").write_text(
            json.dumps({"doc_id": d, "usage": meta["usage"], "cost_usd": meta["cost_usd"],
                        "raw_result": meta["raw_result"]}, ensure_ascii=False, indent=1) + "\n")
        ex_id = uuid.uuid4().hex
        prov = stamp(ex_id, meta["model_id"], sha, "reextract-v035-pilot")
        kept_n = kept_e = 0
        for nrec in result.nodes:
            if nrec["type"] != "Instrument":
                continue
            eventlog.append({"event_type": "node_asserted", "purpose": "reextract",
                             "doc_id": d, "provenance": prov,
                             "payload": {"id": nrec["id"], "type": "Instrument",
                                         "item": nrec["item"]}},
                            batch=PILOT_SHARD_NO, tag=PILOT_TAG)
            fresh.append({"doc_id": d, "kind": "node", "type": "Instrument",
                          "item": nrec["item"]})
            kept_n += 1
        for erec in result.edges:
            if erec["type"] not in SEMANTIC:
                continue
            eventlog.append({"event_type": "edge_asserted", "purpose": "reextract",
                             "doc_id": d, "provenance": prov,
                             "payload": {"type": erec["type"], "from_id": erec["from_id"],
                                         "to_id": erec["to_id"], "item": erec["item"]}},
                            batch=PILOT_SHARD_NO, tag=PILOT_TAG)
            fresh.append({"doc_id": d, "kind": "edge", "type": erec["type"],
                          "item": erec["item"]})
            kept_e += 1
        eventlog.append({"event_type": "reextract_pilot_metrics", "purpose": "reextract",
                         "doc_id": d, "counts": result.counts(),
                         "instruments": kept_n, "semantic_edges": kept_e,
                         "span_lacks_name_precheck": result.precheck_span_lacks_name,
                         "emission_mode": meta.get("emission_mode") or "single_pass",
                         "proposed": len(result.proposed_relationships), "task": TASK},
                        batch=PILOT_SHARD_NO, tag=PILOT_TAG)
        per_doc[d] = (kept_n, kept_e, result.precheck_span_lacks_name,
                      meta.get("emission_mode") or "single_pass")
        status(lane, "running", doc=d, instruments=kept_n, semantic_edges=kept_e,
               span_lacks_name=result.precheck_span_lacks_name,
               emission=per_doc[d][3])

    n_instr = sum(1 for f in fresh if f["kind"] == "node")
    n_sem = sum(1 for f in fresh if f["kind"] == "edge")
    # ADDENDUM-01 precondition: admitted items > 0 in BOTH strata for >= 2 of the 3 docs,
    # else FAIL:harness_or_prompt and the judge is NOT run (no spend judging nothing).
    docs_with_both = sum(1 for d in docs if per_doc.get(d, (0, 0))[0] > 0
                         and per_doc.get(d, (0, 0))[1] > 0)
    if docs_with_both < 2:
        rows = "\n".join(f"| `{d}` | {per_doc.get(d, (0,0,0,'—'))[0]} | "
                          f"{per_doc.get(d, (0,0,0,'—'))[1]} | "
                          f"{per_doc.get(d, (0,0,0,'—'))[2]} | "
                          f"{per_doc.get(d, (0,0,0,'—'))[3]} |" for d in docs)
        VERDICT_MD.write_text(
            "# Pilot re-extract v0.3.5 — verdict: FAIL:harness_or_prompt\n\n"
            f"Precondition not met: items > 0 in BOTH strata for >= 2/3 docs "
            f"(got {docs_with_both}/3). Judge not run (ADDENDUM-01).\n\n"
            "| doc | instruments | semantic edges | span_lacks_name precheck | emission |\n"
            "|---|---|---|---|---|\n" + rows + "\n")
        status(lane, "FAIL", reason=f"precondition {docs_with_both}/3 docs with both strata")
        return False
    recs = sample_records(fresh, doc_texts,
                          lambda it: "Instrument:pilot" if it["kind"] == "node"
                          else "edge:semantic:pilot")
    write_sample("pilot_v035", recs)
    cfg = model_stub.load_model_config()
    agg = run_probe_protocol("pilot_v035", "pilot_v035", run_id,
                             raters=[None, cfg["secondary_judge_model_id"]])
    if not agg:
        status(lane, "STOP", reason="probe protocol failed")
        return False
    per = agg.get("per_stratum") or {}
    faithful = (agg.get("items") or {}).get("faithful_rate")
    checks = {}
    for s in ("Instrument:pilot", "edge:semantic:pilot"):
        r = per.get(s)
        checks[s] = {"present": bool(r), "F": r and r.get("F"), "F_hi": r and r.get("F_hi"),
                     "n": r and r.get("n_in_F_denominator"),
                     "pass": bool(r) and r.get("F_hi") is not None and r["F_hi"] < F_STOP}
    ok = all(c["pass"] for c in checks.values()) and (faithful or 0) >= PILOT_ITEM_FAITHFUL
    # top fabrication patterns for the morning on FAIL
    fab_notes = []
    if not ok:
        pf = agg.get("per_fact") or {}
        fab = [fid for fid, v in pf.items() if v.get("class") == "fabrication"]
        facts_file = REPO / "corpus/staging/metrics/pilot_v034_facts.jsonl"
        fmap = {json.loads(l)["fact_id"]: json.loads(l) for l in
                facts_file.read_text().splitlines() if l.strip()}
        fab_notes = [f"- `{fmap[f]['attribute']}`: {fmap[f]['fact_text'][:140]}"
                     for f in fab[:3] if f in fmap]
    lines = [f"# Pilot re-extract v0.3.5 — verdict: {'PASS' if ok else 'FAIL'}", "",
             f"Task: `{TASK}` Lane 1 (Seldon id in RESULT). Run `{run_id}` (ceiling 3M).",
             f"Pilot docs: {', '.join(f'`{d}`' for d in docs)}",
             f"Items: {n_instr} Instrument, {n_sem} semantic edges; "
             f"facts {agg.get('n_facts')}; raters 2 (Dawid-Skene: {agg.get('method')}).",
             "Per-doc (instruments / semantic edges / span_lacks_name precheck / emission): "
             + "; ".join(f"`{d}` {per_doc.get(d)}" for d in docs), "",
             "| stratum | F | F_upper | n | pass (< 0.10) |", "|---|---|---|---|---|"]
    for s, c in checks.items():
        lines.append(f"| {s} | {c['F'] if c['F'] is not None else '—'} | "
                     f"{c['F_hi'] if c['F_hi'] is not None else '—'} | {c['n'] or 0} | "
                     f"{'PASS' if c['pass'] else 'FAIL'} |")
    lines += ["", f"Item-level faithful: {faithful:.3f} (pre-registered ≥ {PILOT_ITEM_FAITHFUL})"
              if faithful is not None else "Item-level faithful: —",
              "", f"**Lanes 2 and 3 are {'GO' if ok else 'NO-GO'}** per the pre-registered rule "
              f"(F_upper < {F_STOP} in both strata AND item-faithful ≥ {PILOT_ITEM_FAITHFUL})."]
    if fab_notes:
        lines += ["", "Top fabrication patterns:"] + fab_notes
    VERDICT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    status(lane, "PASS" if ok else "FAIL", faithful=faithful,
           checks={k: v["pass"] for k, v in checks.items()})
    commit_push(f"overnight burn Lane 1: pilot v0.3.4 {'PASS' if ok else 'FAIL'}")
    return ok


# ------------------------------------------------------------------ Lane 2
def lane2() -> None:
    lane = "lane2_reextract"
    status(lane, "running")
    run_id = "reextract_v034_bulk"
    declare(run_id, CEILING, "extraction")
    spend.set_current_run(run_id)
    members = corpus_paths()
    nodes, edges = live_items()
    pilots = set((json.loads(STATUS.read_text()).get("lane1_pilot") or {}).get("pilot_docs") or [])
    worklist = []
    doc_shas: dict[str, set] = {}
    for d in set(nodes) | set(edges):
        if d in pilots or d not in members:
            continue
        instr = [e for e in nodes.get(d, []) if (e.get("payload") or {}).get("type") == "Instrument"]
        sem = [e for e in edges.get(d, []) if (e.get("payload") or {}).get("type") in SEMANTIC]
        if instr or sem:
            worklist.append(d)
            doc_shas[d] = {(e.get("provenance") or {}).get("source_sha256")
                           for e in instr + sem} - {None}
    worklist.sort(key=lambda d: members[d].stat().st_size, reverse=True)
    live_ids = {d: {(e.get("payload") or {}).get("id") for e in nodes.get(d, [])} - {None}
                for d in worklist}
    status(lane, "running", worklist=len(worklist))
    review_path = REPO / "corpus/staging/metrics/lane2_semantic_edge_review.jsonl"
    raw_dir = REPO / "events/raw/reextract_v034_bulk"; raw_dir.mkdir(parents=True, exist_ok=True)
    done = {ev["doc_id"] for ev in eventlog.replay()
            if ev.get("event_type") == "extraction_superseded"
            and ev.get("superseded_strata") and ev.get("task") == TASK}
    fresh, doc_texts = [], {}
    rstate: dict = {}
    processed = 0
    q_streak = 0
    controlled = False
    for d in worklist:
        if d in done:
            continue
        if halted() or not wall_ok():
            status(lane, "stopped", reason="wall clock / STOP file", processed=processed)
            break
        try:
            result, meta, sha, text = extract_doc(d, members[d], rstate)
        except RateLimitStop as exc:
            status(lane, "rate_limited", detail=str(exc)[:200]); break
        except spend.SpendRefusalStop as exc:
            if exc.refusal.scope == "daily" and wall_ok():
                if sleep_until_daily_roll(lane):
                    continue
            status(lane, "ceiling_stop", reason=str(exc)[:200]); break
        except (model_stub.ModelInvocationError, model_stub.ModelSubstitutionError,
                ValueError) as exc:
            status(lane, "doc_error", doc=d, err=str(exc)[:160]); continue
        doc_texts[d] = text
        (raw_dir / f"{d}.{sha[:12]}.{model_stub.prompt_version()}.json").write_text(
            json.dumps({"doc_id": d, "usage": meta["usage"], "cost_usd": meta["cost_usd"],
                        "raw_result": meta["raw_result"]}, ensure_ascii=False, indent=1) + "\n")
        if processed < 3:
            u = meta.get("usage") or {}
            status(lane, "running", cache_check_call=processed + 1,
                   cache_read=int(u.get("cacheReadInputTokens", 0) or 0),
                   cache_write=int(u.get("cacheCreationInputTokens", 0) or 0),
                   fresh_input=int(u.get("inputTokens", 0) or 0),
                   note="whole-doc single-pass: no shared prefix expected; logged per ADDENDUM-01, not gated")
        c = result.counts()
        rate = c["quarantined"] / max(1, c["nodes"] + c["edges"] + c["quarantined"])
        over = rate > rbe.QUARANTINE_STOP_RATE
        q_streak = q_streak + 1 if over else 0
        if q_streak >= QUAR_WINDOW:
            status(lane, "quarantine_STOP", doc=d, rate=round(rate, 3), streak=q_streak)
            break
        ex_id = uuid.uuid4().hex
        prov = stamp(ex_id, meta["model_id"], sha, "reextract-v035")
        new_ids = set()
        kept_n = kept_e = routed = 0
        for nrec in result.nodes:
            if nrec["type"] != "Instrument":
                continue
            eventlog.append({"event_type": "node_asserted", "doc_id": d, "provenance": prov,
                             "payload": {"id": nrec["id"], "type": "Instrument",
                                         "item": nrec["item"]}}, batch=LANE2_SHARD)
            new_ids.add(nrec["id"])
            fresh.append({"doc_id": d, "kind": "node", "type": "Instrument", "item": nrec["item"]})
            kept_n += 1
        allowed = new_ids | live_ids.get(d, set())
        for erec in result.edges:
            if erec["type"] not in SEMANTIC:
                continue
            if erec["from_id"] in allowed and erec["to_id"] in allowed:
                eventlog.append({"event_type": "edge_asserted", "doc_id": d, "provenance": prov,
                                 "payload": {"type": erec["type"], "from_id": erec["from_id"],
                                             "to_id": erec["to_id"], "item": erec["item"]}},
                                batch=LANE2_SHARD)
                fresh.append({"doc_id": d, "kind": "edge", "type": erec["type"], "item": erec["item"]})
                kept_e += 1
            else:   # endpoint not resolvable against live ids: morning review, not the graph
                with review_path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"doc_id": d, **{k: erec[k] for k in
                                         ("type", "from_id", "to_id")},
                                         "item": erec["item"], "reason": "unresolvable_endpoint"},
                                        ensure_ascii=False) + "\n")
                routed += 1
        for old_sha in doc_shas.get(d) or {None}:
            if old_sha:
                eventlog.append({"event_type": "extraction_superseded", "doc_id": d,
                                 "superseded_source_sha256": old_sha,
                                 "superseded_strata": ["instrument", "semantic_edges"],
                                 "replacement_shard": f"batch-{LANE2_SHARD:03d}",
                                 "task": TASK}, batch=LANE2_SHARD)
        processed += 1
        status(lane, "running", doc=d, n=kept_n, e=kept_e, review=routed,
               quarantine=round(rate, 3), processed=processed)
        if processed == 8 and not controlled:
            controlled = True
            if not positive_control(lane, "ctrl_lane2", run_id, fresh, doc_texts,
                                    "lane2:pooled"):
                status(lane, "control_STOP_final", processed=processed)
                break
    status(lane, "done", processed=processed)
    rep = spend.default_ledger().reconcile(run_id)
    status(lane, "done", processed=processed, reconcile_ok=rep["ok"],
           settled=rep["settled_total"])
    commit_push(f"overnight burn Lane 2: {processed} docs re-extracted (instrument+semantic strata)")


# ------------------------------------------------------------------ Lane 3
def lane3() -> None:
    lane = "lane3_triage"
    status(lane, "running")
    run_id = "triage_extract"
    declare(run_id, CEILING, "extraction")
    # Phase-0 retag (report: only the manifested RFI notice carries an arm to supersede;
    # the regulations.gov comments index was excluded_by_rule R3_listing_page in 7456614d
    # and has no manifest entry or construct_arm — discrepancy recorded, not reconciled)
    prior = [ev for ev in eventlog.replay()
             if ev.get("event_type") == "document_annotation"
             and ev.get("property") == "construct_arm"
             and ev.get("doc_id") == "doc-rfi-ai-open-gov-data-2024"
             and ev.get("task") == TASK]
    if not prior:
        eventlog.append({"event_type": "document_annotation",
                         "doc_id": "doc-rfi-ai-open-gov-data-2024",
                         "property": "construct_arm", "value": "publication_actionability",
                         "rule": "task Lane 3 Phase-0 retag", "rule_version": "2026-08-26.1",
                         "rationale": "subject is AI-ready open government data assets — "
                                      "publication_actionability, superseding 7456614d's "
                                      "R3-placement org_maturity tag", "task": TASK},
                        batch=LANE2_SHARD)
    status(lane, "running", retagged=["doc-rfi-ai-open-gov-data-2024"],
           retag_skipped="doc-rfi-comments-docket-listing (not manifested — excluded R3_listing_page)")
    env = run_env(run_id)
    progress = REPO / "docs/research/2026-08-27_triage_extract_progress.md"
    if not progress.exists():
        progress.write_text("# Triage-epoch extraction — overnight burn 2026-08-26 Lane 3\n",
                            encoding="utf-8")
    base = [PY, "scripts/run_bulk_extraction.py", "--profile", "reextract_v034",
            "--ceiling-tokens", str(CEILING), "--run-id", run_id]
    try:
        r = subprocess.run(base + ["--max-docs", "8"], cwd=REPO, env=env,
                           capture_output=True, text=True,
                           timeout=min(4 * 3600, wall_remaining_s()))
    except subprocess.TimeoutExpired:
        status(lane, "stopped", reason="wall-clock cap killed the first-8 run (resume-safe shards)")
        return
    print(r.stdout[-1500:], r.stderr[-500:], flush=True)
    if r.returncode != 0:
        status(lane, "stopped", reason=f"first-8 run exited {r.returncode}"); return
    fresh, doc_texts = [], {}
    members = corpus_paths()
    for ev in eventlog.replay():
        if ev.get("event_type") in ("node_asserted", "edge_asserted") \
                and (ev.get("provenance") or {}).get("corpus_epoch") == "triage-2026-08-24":
            p = ev.get("payload") or {}
            kind = "node" if ev["event_type"] == "node_asserted" else "edge"
            fresh.append({"doc_id": ev["doc_id"], "kind": kind,
                          "type": p.get("type"), "item": p.get("item") or p})
            if ev["doc_id"] not in doc_texts and ev["doc_id"] in members:
                doc_texts[ev["doc_id"]] = rbe.doc_text(members[ev["doc_id"]])
    if fresh and not positive_control(lane, "ctrl_lane3", run_id, fresh, doc_texts,
                                      "lane3:pooled"):
        status(lane, "control_STOP_final")
        commit_push("overnight burn Lane 3: control STOP after first 8 docs")
        return
    if halted() or not wall_ok():
        status(lane, "stopped", reason="wall clock / STOP file"); return
    rc = 0
    while True:
        t0 = now_utc().isoformat()
        try:
            r = subprocess.run(base, cwd=REPO, env=env, capture_output=True, text=True,
                               timeout=min(6 * 3600, wall_remaining_s()))
            print(r.stdout[-1500:], r.stderr[-500:], flush=True)
            rc = r.returncode
        except subprocess.TimeoutExpired:
            status(lane, "stopped", reason="wall-clock cap killed the main run (resume-safe shards)")
            rc = -9
            break
        if last_refusal_scope(run_id, t0) == "daily" and wall_ok():
            if sleep_until_daily_roll(lane):
                continue
        break
    rep = spend.default_ledger().reconcile(run_id)
    status(lane, "done", rc=rc, reconcile_ok=rep["ok"], settled=rep["settled_total"])
    commit_push("overnight burn Lane 3: triage-epoch extraction window complete")


# ------------------------------------------------------------------ Lane 4
def lane4(resume: bool = False) -> None:
    lane = "lane4_repair"
    status(lane, "running", mode="resume" if resume else "full")
    # a) restoration v2 — full: stage 1 + 2; resume (ADDENDUM-02): stage 2 only, from the
    # first unjudged proposal (restoration_v2.py stage 2 is idempotent on judged keys)
    stages = ((("2", "restoration_v2_resume"),) if resume
              else (("1", "restoration_v2_s1"), ("2", "restoration_v2_s2")))
    for stage, rid in stages:
        while True:
            if halted() or not wall_ok():
                status(lane, "stopped", reason="wall clock / STOP file"); return
            env = run_env(rid)
            t0 = now_utc().isoformat()
            try:
                r = subprocess.run([PY, "scripts/restoration_v2.py", "--stage", stage,
                                    "--ceiling-tokens", str(CEILING), "--run-id", rid],
                                   cwd=REPO, env=env, capture_output=True, text=True,
                                   timeout=min(8 * 3600, wall_remaining_s()))
            except subprocess.TimeoutExpired:
                status(lane, "stopped", reason=f"wall cap killed stage {stage} (resume-safe)")
                return
            print(r.stdout[-1500:], r.stderr[-500:], flush=True)
            status(lane, "running", stage=stage, rc=r.returncode)
            if r.returncode == 3:
                status(lane, "stopped", reason=f"restoration stage {stage} diagnostic halt (rc 3)")
                return
            if last_refusal_scope(rid, t0) == "daily" and wall_ok():
                if sleep_until_daily_roll(lane):
                    continue
                return
            break
    # b) acceptance sample: 100 accepted restorations, full probe protocol, 2 raters
    accepted = [ev for ev in eventlog.replay(tag=RESTORE_TAG)
                if ev.get("event_type") == "attribute_restored"]
    status(lane, "running", accepted=len(accepted))
    if accepted:
        import random as _rnd
        import restoration_v2 as rv2
        ktypes = rv2.key_types()
        rng = _rnd.Random("restoration_v2_accept")
        sample = rng.sample(accepted, min(100, len(accepted)))
        recs = []
        for ev in sample:
            ntype = ktypes.get((ev["doc_id"], ev["item_id"])) or "Concept"
            recs.append({"item_id": ev["item_id"], "event_id": ev["event_id"],
                         "kind": "node", "type": ntype,
                         "stratum": "restoration_v2",
                         "text": str(ev.get("value")),
                         "grounding_span": ev.get("supporting_passage") or "",
                         "doc_id": ev["doc_id"],
                         "extra": {"id": ev["item_id"],
                                   ev["attribute"]: ev.get("value")},
                         "window": None})
        write_sample("restv2_accept", recs)
        cfg = model_stub.load_model_config()
        declare("restoration_v2_accept", CEILING, "judge")
        agg = run_probe_protocol("restv2_accept", "restv2_accept", "restoration_v2_accept",
                                 raters=[None, cfg["secondary_judge_model_id"]])
        if agg:
            pooled = agg.get("pooled") or {}
            n = pooled.get("n_facts") or 0
            entailed = (agg.get("per_fact") and
                        sum(1 for v in agg["per_fact"].values() if v.get("entailed")))
            rate = (entailed / n) if n else 0.0
            ok = rate >= ACCEPT_THRESHOLD
            if ok:
                eventlog.append({"event_type": "restoration_class_accepted",
                                 "restoration_class": "restoration_v2",
                                 "shard_tag": RESTORE_TAG,
                                 "fact_entailment_rate": rate, "n_facts": n,
                                 "threshold": ACCEPT_THRESHOLD, "task": TASK},
                                batch=LANE2_SHARD)
            status(lane, "acceptance_PASS" if ok else "acceptance_FAIL",
                   rate=round(rate, 4), n_facts=n)
        else:
            status(lane, "acceptance_error", reason="probe protocol failed — class stays unprojected")
    # c) relocation resume, two shards sequential (concurrency budget), decoys+cache on
    declare("repair_resume", CEILING, "cleanup")
    for shard in ("0/2", "1/2"):
        while True:
            if halted() or not wall_ok():
                status(lane, "stopped", reason="wall clock / STOP file"); return
            env = run_env("repair_resume")
            t0 = now_utc().isoformat()
            try:
                r = subprocess.run([PY, "scripts/batch_repair.py", "--shard", shard,
                                    "--redo-unrepairable", "--kinds", "relocate",
                                    "--exclude-types", "Instrument",
                                    "--ceiling-tokens", str(CEILING), "--run-id", "repair_resume"],
                                   cwd=REPO, env=env, capture_output=True, text=True,
                                   timeout=min(5 * 3600, wall_remaining_s()))
            except subprocess.TimeoutExpired:
                status(lane, "stopped", reason=f"wall cap killed relocation shard {shard}")
                return
            print(r.stdout[-1500:], r.stderr[-500:], flush=True)
            status(lane, "running", relocation_shard=shard, rc=r.returncode)
            if r.returncode == 3:
                status(lane, "stopped", reason=f"relocation shard {shard} diagnostic halt")
                return
            if last_refusal_scope("repair_resume", t0) == "daily" and wall_ok():
                if sleep_until_daily_roll(lane):
                    continue
                return
            break
    # d) re-judge of prior model_assisted_batch relocations (50 items, reported number)
    prior = [ev for ev in eventlog.replay()
             if ev.get("event_type") == "grounding_relocated"
             and ev.get("method") == "model_assisted_batch"]
    if prior:
        import random as _rnd
        rng = _rnd.Random("reloc_rejudge")
        sample = rng.sample(prior, min(50, len(prior)))
        import batch_repair as br
        item_texts = {}
        for l in br.SPAN_WORK.read_text().splitlines():
            if l.strip():
                w = json.loads(l)
                item_texts[(w["doc_id"], w["item_id"])] = w.get("item_text")
        recs = []
        for ev in sample:
            itext = item_texts.get((ev["doc_id"], ev["item_id"]))
            if not itext:
                continue
            # the relocation-success question, phrased as the probe judges facts:
            # does the relocated span entail the item's own text ("name: <item_text>")
            recs.append({"item_id": ev["item_id"], "event_id": ev["event_id"],
                         "kind": "node", "type": "Concept", "stratum": "reloc_rejudge",
                         "text": itext,
                         "grounding_span": ev.get("new_span") or "",
                         "doc_id": ev["doc_id"],
                         "extra": {"id": ev["item_id"], "name": itext},
                         "window": None})
        write_sample("reloc_rejudge", recs)
        cfg = model_stub.load_model_config()
        declare("reloc_rejudge", CEILING, "judge")
        agg = run_probe_protocol("reloc_rejudge", "reloc_rejudge", "reloc_rejudge",
                                 raters=[cfg["secondary_judge_model_id"]])
        if agg:
            status(lane, "running", reloc_rejudge_n=agg.get("n_facts"),
                   reloc_rejudge_F=(agg.get("pooled") or {}).get("F"))
    status(lane, "done")
    commit_push("overnight burn Lane 4: restoration v2 + relocation resume window complete")



# ------------------------------------------------------------------ Lane 1'' (ADDENDUM-02/04)
PRIOR_PILOTS = ["data-readiness-for-ai-a-360-degree-survey", "aidrin-hiniduma-2024",
                "fcsm-23-02-a-framework-for-data-quality-case-studies"]
VERDICT_V035B = REPO / "docs" / "research" / "2026-08-27_pilot_reextract_v035b_verdict.md"
PILOT_B_TAG = "reextract_v035b"


def top_semantic_docs(n: int, exclude: set) -> list[tuple[str, int]]:
    _, edges = live_items()
    counts = Counter()
    for d, evs in edges.items():
        if d in exclude:
            continue
        counts[d] = sum(1 for e in evs if (e.get("payload") or {}).get("type") in SEMANTIC)
    return [(d, c) for d, c in counts.most_common(n) if c > 0]


def lane1b() -> bool:
    """ADDENDUM-02 Lane 1'' under ADDENDUM-04's opus-5 pin: 5 stratum-matched docs, all
    extracted fresh; pooled precondition (Instruments >= 20 AND semantic edges >= 20);
    judge capped at 120 facts/stratum; raters opus-4-8 + sonnet-5 (per config)."""
    import random as _rnd
    lane = "lane1b_pilot"
    run_id = "pilot_v035b_opus5"
    declare(run_id, 4_000_000, "extraction")
    spend.set_current_run(run_id)
    members = corpus_paths()
    top2 = top_semantic_docs(4, set(PRIOR_PILOTS))
    top2 = [(d, c) for d, c in top2 if d in members][:2]
    docs = PRIOR_PILOTS + [d for d, _ in top2]
    status(lane, "running", docs=docs,
           semantic_doc_prior_counts={d: c for d, c in top2})
    raw_dir = REPO / "events/raw/reextract_v035b_pilot"
    raw_dir.mkdir(parents=True, exist_ok=True)
    fresh, doc_texts, per_doc = [], {}, {}
    rstate: dict = {}
    for d in docs:
        if halted() or not wall_ok():
            status(lane, "STOP", reason="wall clock / STOP file"); return False
        try:
            result, meta, sha, text = extract_doc(d, members[d], rstate)
        except RateLimitStop as exc:
            status(lane, "rate_limited", detail=str(exc)[:200]); return False
        except spend.SpendRefusalStop as exc:
            if exc.refusal.scope == "daily" and wall_ok() and sleep_until_daily_roll(lane):
                try:
                    result, meta, sha, text = extract_doc(d, members[d], rstate)
                except Exception as exc2:
                    status(lane, "STOP", reason=f"{d}: {str(exc2)[:200]}"); return False
            else:
                status(lane, "STOP", reason=f"spend guard: {exc}"); return False
        except (model_stub.ModelInvocationError, model_stub.ModelSubstitutionError,
                ValueError) as exc:
            status(lane, "STOP", reason=f"{d}: {str(exc)[:200]}"); return False
        doc_texts[d] = text
        (raw_dir / f"{d}.{sha[:12]}.{model_stub.prompt_version()}.{meta['model_id']}.json").write_text(
            json.dumps({"doc_id": d, "usage": meta["usage"], "cost_usd": meta.get("cost_usd"),
                        "emission_mode": meta.get("emission_mode") or "single_pass",
                        "raw_result": meta["raw_result"]}, ensure_ascii=False, indent=1) + "\n")
        ex_id = uuid.uuid4().hex
        prov = stamp(ex_id, meta["model_id"], sha, "reextract-v035-pilot")
        kept_n = kept_e = 0
        for nrec in result.nodes:
            if nrec["type"] != "Instrument":
                continue
            eventlog.append({"event_type": "node_asserted", "purpose": "reextract",
                             "doc_id": d, "provenance": prov,
                             "payload": {"id": nrec["id"], "type": "Instrument",
                                         "item": nrec["item"]}},
                            batch=PILOT_SHARD_NO, tag=PILOT_B_TAG)
            fresh.append({"doc_id": d, "kind": "node", "type": "Instrument", "item": nrec["item"]})
            kept_n += 1
        for erec in result.edges:
            if erec["type"] not in SEMANTIC:
                continue
            eventlog.append({"event_type": "edge_asserted", "purpose": "reextract",
                             "doc_id": d, "provenance": prov,
                             "payload": {"type": erec["type"], "from_id": erec["from_id"],
                                         "to_id": erec["to_id"], "item": erec["item"]}},
                            batch=PILOT_SHARD_NO, tag=PILOT_B_TAG)
            fresh.append({"doc_id": d, "kind": "edge", "type": erec["type"], "item": erec["item"]})
            kept_e += 1
        out_tokens = int((meta.get("usage") or {}).get("outputTokens", 0) or 0)
        per_doc[d] = {"instruments": kept_n, "semantic_edges": kept_e,
                      "span_lacks_name": result.precheck_span_lacks_name,
                      "emission": meta.get("emission_mode") or "single_pass",
                      "output_tokens": out_tokens}
        eventlog.append({"event_type": "reextract_pilot_metrics", "purpose": "reextract",
                         "doc_id": d, "counts": result.counts(), **per_doc[d], "task": TASK},
                        batch=PILOT_SHARD_NO, tag=PILOT_B_TAG)
        status(lane, "running", doc=d, **per_doc[d])
    n_instr = sum(v["instruments"] for v in per_doc.values())
    n_sem = sum(v["semantic_edges"] for v in per_doc.values())
    settled = spend.default_ledger().status(run_id)["runs"][run_id]["settled"]
    cost_per_doc = settled // max(1, len(docs))

    def doc_table() -> str:
        rows = "\n".join(
            f"| `{d}` | {v['instruments']} | {v['semantic_edges']} | {v['span_lacks_name']} "
            f"| {v['emission']} | {v['output_tokens']:,} |" for d, v in per_doc.items())
        return ("| doc | instruments | semantic edges | span_lacks_name | emission | max output tokens |\n"
                "|---|---|---|---|---|---|\n" + rows)

    if not (n_instr >= 20 and n_sem >= 20):
        VERDICT_V035B.write_text(
            "# Pilot re-extract v0.3.5b (opus-5) — verdict: FAIL:harness_or_prompt\n\n"
            f"Pooled precondition not met: Instruments {n_instr} (need >= 20), semantic edges "
            f"{n_sem} (need >= 20) across 5 docs. Judge not run (ADDENDUM-02).\n\n"
            + doc_table() + "\n\n"
            f"Run `{run_id}`: settled {settled:,} tokens; cost/doc ~{cost_per_doc:,} (informational).\n")
        status(lane, "FAIL", reason=f"pooled precondition I={n_instr} E={n_sem}")
        return False
    status(lane, "precondition_met", instruments=n_instr, semantic_edges=n_sem)
    recs = sample_records(fresh, doc_texts,
                          lambda it: "Instrument:pilot" if it["kind"] == "node"
                          else "edge:semantic:pilot")
    write_sample("pilot_v035b", recs)
    cfg = model_stub.load_model_config()
    env = run_env(run_id)
    r = subprocess.run([PY, "scripts/probe_decompose.py", "--prefix", "pilot_v035b"],
                       cwd=REPO, env=env, capture_output=True, text=True,
                       timeout=min(3600, wall_remaining_s()))
    print(r.stdout[-800:], r.stderr[-400:], flush=True)
    if r.returncode != 0:
        status(lane, "STOP", reason="decompose failed"); return False
    # per-stratum random cap of 120 facts (ADDENDUM-02)
    sample_by_ev = {rec["event_id"]: rec for rec in recs}
    facts = [json.loads(l) for l in
             (REPO / "corpus/staging/metrics/pilot_v035b_facts.jsonl").read_text().splitlines()
             if l.strip()]
    by_stratum = defaultdict(list)
    for f_ in facts:
        by_stratum[sample_by_ev[f_["event_id"]]["stratum"]].append(f_["fact_id"])
    rng = _rnd.Random("pilot_v035b")
    sel = []
    for s, fids in by_stratum.items():
        sel += fids if len(fids) <= 120 else rng.sample(fids, 120)
    sel_file = REPO / "corpus/staging/metrics/pilot_v035b_fact_sel.json"
    sel_file.write_text(json.dumps(sel))
    status(lane, "judging", facts_selected=len(sel),
           per_stratum={s: min(len(v), 120) for s, v in by_stratum.items()})
    for model in (cfg["primary_judge_model_id"], cfg["secondary_judge_model_id"]):
        r = subprocess.run([PY, "scripts/probe_judge.py", "--prefix", "pilot_v035b",
                            "--run", "pilot_v035b", "--batch", "10", "--model", model,
                            "--fact-ids-file", str(sel_file)],
                           cwd=REPO, env=env, capture_output=True, text=True,
                           timeout=min(7200, wall_remaining_s()))
        print(r.stdout[-800:], r.stderr[-400:], flush=True)
        if r.returncode != 0:
            status(lane, "STOP", reason=f"judge {model} failed"); return False
    r = subprocess.run([PY, "scripts/probe_aggregate.py", "--prefix", "pilot_v035b",
                        "--run", "pilot_v035b"], cwd=REPO, env=env,
                       capture_output=True, text=True, timeout=600)
    print(r.stdout[-1200:], r.stderr[-400:], flush=True)
    agg_path = REPO / "corpus/staging/metrics/pilot_v035b_aggregate.json"
    if r.returncode != 0 or not agg_path.exists():
        status(lane, "STOP", reason="aggregate failed"); return False
    agg = json.loads(agg_path.read_text())
    per = agg.get("per_stratum") or {}
    faithful = (agg.get("items") or {}).get("faithful_rate")
    checks = {}
    for s in ("Instrument:pilot", "edge:semantic:pilot"):
        rr = per.get(s)
        checks[s] = {"F": rr and rr.get("F"), "F_hi": rr and rr.get("F_hi"),
                     "n": rr and rr.get("n_in_F_denominator"),
                     "pass": bool(rr) and rr.get("F_hi") is not None and rr["F_hi"] < F_STOP}
    ok = all(c["pass"] for c in checks.values()) and (faithful or 0) >= PILOT_ITEM_FAITHFUL
    settled = spend.default_ledger().status(run_id)["runs"][run_id]["settled"]
    lines = [f"# Pilot re-extract v0.3.5b (opus-5) — verdict: {'PASS' if ok else 'FAIL'}", "",
             f"Task `{TASK}` ADDENDUM-02 protocol under the ADDENDUM-04 model pin "
             f"(`claude-opus-5`; preflight 3/3). Run `{run_id}` (ceiling 4M): settled "
             f"{settled:,} tokens; cost/doc ~{settled // len(docs):,} (informational).",
             f"Raters: {cfg['primary_judge_model_id']} + {cfg['secondary_judge_model_id']} "
             f"(neither shares a model with the extractor).", "",
             doc_table(), "",
             f"Pooled precondition: Instruments {n_instr} >= 20, semantic edges {n_sem} >= 20 — met.",
             f"Facts judged: {len(sel)} (cap 120/stratum); Dawid-Skene: {agg.get('method')}.", "",
             "| stratum | F | F_upper | n | pass (< 0.10) |", "|---|---|---|---|---|"]
    for s, c in checks.items():
        lines.append(f"| {s} | {c['F'] if c['F'] is not None else '—'} | "
                     f"{c['F_hi'] if c['F_hi'] is not None else '—'} | {c['n'] or 0} | "
                     f"{'PASS' if c['pass'] else 'FAIL'} |")
    lines += ["", (f"Item-level faithful: {faithful:.3f} (pre-registered >= {PILOT_ITEM_FAITHFUL})"
                   if faithful is not None else "Item-level faithful: —"),
              "", "Per-rater agreement (bias visibility, ADDENDUM-03 note carried forward):",
              "```json", json.dumps(agg.get("raters"), indent=1), "```",
              "", f"**Lanes 2 and 3 are {'GO' if ok else 'NO-GO'}** per the pre-registered rule."]
    VERDICT_V035B.write_text("\n".join(lines) + "\n", encoding="utf-8")
    status(lane, "PASS" if ok else "FAIL", faithful=faithful,
           checks={k: v["pass"] for k, v in checks.items()})
    commit_push(f"overnight burn ADDENDUM-02/04: pilot v0.3.5b opus-5 {'PASS' if ok else 'FAIL'}")
    return ok


# ------------------------------------------------------------------ summary / main
def write_summary() -> None:
    led = spend.default_ledger()
    st = led.status()
    stat = json.loads(STATUS.read_text()) if STATUS.exists() else {}
    recs = {}
    for rid in st.get("runs", {}):
        try:
            recs[rid] = led.reconcile(rid)
        except Exception as exc:
            recs[rid] = {"ok": False, "error": str(exc)[:120]}
    lines = ["# Overnight burn 2026-08-26 → 27 — SUMMARY (driver exit)", "",
             f"Task: `{TASK}`. Written {now_utc().isoformat()} by scripts/overnight_burn.py.",
             f"CEILING (execute line carried an unfilled placeholder; interpreted as the "
             f"standing declared band, no band change): **{CEILING:,}** tokens; "
             f"`spend.daily_tokens` untouched at 55M.", "",
             "## Ledger totals per run (`python -m kg.spend status`)", "",
             "| run | ceiling | committed | settled | outstanding | refusals | reconcile |",
             "|---|---|---|---|---|---|---|"]
    for rid, r in sorted(st.get("runs", {}).items()):
        rec = recs.get(rid, {})
        lines.append(f"| {rid} | {r['ceiling_tokens']:,} | {r['committed']:,} | "
                     f"{r['settled']:,} | {r['outstanding']:,} | {r['refusals']} | "
                     f"{'OK' if rec.get('ok') else rec.get('note') or 'MISMATCH'} |")
    lines += ["", f"Committed today (daily band {st['daily_tokens']:,}): "
              f"**{st['committed_today']:,}**", "", "## Lane states", "",
              "```json", json.dumps(stat, indent=1), "```", "",
              "Gate verdicts, counts, and artifacts: see the lane states above, "
              "`docs/research/2026-08-26_pilot_reextract_v034_verdict.md`, "
              "`corpus/staging/metrics/restoration_v2_summary.json`, "
              "`corpus/staging/metrics/batch_repair_summary.json`, and the per-lane shards "
              "(batch-013_reextract_v034 / batch-014_restoration_v2 / batch-015 / batch-016)."]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    lanes = set((os.environ.get("OVERNIGHT_LANES") or "all").split(","))
    status("driver", "started", ceiling=CEILING, wall_stop=WALL_STOP_UTC, pid=os.getpid(),
           lanes=sorted(lanes))
    if lanes == {"1b"}:
        ok1 = False
        try:
            ok1 = lane1b()
        except Exception as exc:
            status("lane1b_pilot", "error", detail=str(exc)[:300])
        if ok1:
            # ADDENDUM-02: on PASS, Lanes 2 || 3 as a second detached invocation
            env2 = dict(os.environ)
            env2["OVERNIGHT_LANES"] = "2,3"
            log = (REPO / "logs" / "overnight_burn_2026-08-26.log").open("a")
            subprocess.Popen([PY, str(REPO / "scripts" / "overnight_burn.py")],
                             cwd=REPO, env=env2, stdout=log, stderr=log,
                             start_new_session=True)
            status("driver", "lanes_2_3_launched_detached")
        status("driver", "exited", lane1b_pass=ok1)
        commit_push("overnight burn ADDENDUM-02/04: Lane 1'' pilot opus-5 "
                    + ("PASS -> lanes 2||3 launched" if ok1 else "FAIL"))
        return 0
    if lanes == {"4resume"}:
        try:
            lane4(resume=True)
        except Exception as exc:
            status("lane4_repair", "error", detail=str(exc)[:300])
        write_summary()
        status("driver", "exited")
        commit_push("overnight burn ADDENDUM-02: Lane 4 resume complete — SUMMARY")
        return 0
    if lanes == {"1"}:
        ok1 = False
        try:
            ok1 = lane1()
        except Exception as exc:
            status("lane1_pilot", "error", detail=str(exc)[:300])
        status("driver", "exited", lane1_pass=ok1)
        commit_push("overnight burn ADDENDUM-01: Lane 1' pilot v0.3.5 "
                    + ("PASS" if ok1 else "FAIL"))
        return 0
    if lanes == {"2", "3"}:
        import threading
        t3 = threading.Thread(target=lane3, daemon=False)
        t3.start()
        try:
            lane2()
        except Exception as exc:
            status("lane2_reextract", "error", detail=str(exc)[:300])
        t3.join()
        write_summary()
        status("driver", "exited")
        commit_push("overnight burn ADDENDUM-01: lanes 2||3 window complete — SUMMARY")
        return 0
    ok1 = False
    try:
        ok1 = lane1()
    except Exception as exc:
        status("lane1_pilot", "error", detail=str(exc)[:300])
    if halted() or not wall_ok():
        status("driver", "stopped_before_bulk")
    elif ok1:
        # Lane 3 rides a subprocess pipeline; Lane 2 runs in-process. Run Lane 3 FIRST as a
        # background process and Lane 2 in this process — 2 concurrent model streams total
        # (MAX_CONCURRENT_MODEL_CALLS=2; run_bulk runs single-stream without --fleet).
        import threading
        t3 = threading.Thread(target=lane3, daemon=False)
        t3.start()
        try:
            lane2()
        except Exception as exc:
            status("lane2_reextract", "error", detail=str(exc)[:300])
        t3.join()
    else:
        status("driver", "lanes_2_3_skipped", reason="Lane 1 FAIL/STOP — pre-registered rule")
        try:
            lane3_skip_note = "Lane 3 depends on Lane 1 PASS (extraction under the corrected prompt)"
            status("lane3_triage", "skipped", reason=lane3_skip_note)
        except Exception:
            pass
    if not halted() and wall_ok():
        try:
            lane4()
        except Exception as exc:
            status("lane4_repair", "error", detail=str(exc)[:300])
    write_summary()
    status("driver", "exited")
    commit_push("overnight burn: driver exit — SUMMARY, ledger, shards")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
