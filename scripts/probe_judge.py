#!/usr/bin/env python3
"""Probe Phases 3-4 — atomic-fact judging with PROV-attributed judge_label events
(task 2026-08-22_faithfulness_probe).

Each call judges a batch of facts (size from --batch; order randomized with a seeded RNG,
batch_position recorded). One `judge_label` event per (fact, agent) in the tagged shard
events/batch-009_probe_judge.jsonl (`purpose: probe`), raw envelopes in events/raw/probe_judge/.
Agents are software agents (PROV-O prov:SoftwareAgent) identified by model id + version string
from the CLI envelope + the sha256 of the judge template. Resume keyed on (fact_id, agent id,
run label).
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import random
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kg import eventlog                       # noqa: E402
from kg.extraction import model_stub          # noqa: E402

FACTS = REPO / "corpus/staging/metrics/probe_facts.jsonl"
SAMPLE = REPO / "corpus/staging/metrics/probe_sample.jsonl"
TEMPLATE = REPO / "kg/extraction/probe_judge_template.md"
RAW_DIR = REPO / "events/raw/probe_judge"


def set_prefix(prefix: str) -> None:
    """Reuse the protocol on another sample; labels stay in the probe_judge shard, keyed by run."""
    global FACTS, SAMPLE, RAW_DIR
    FACTS = REPO / f"corpus/staging/metrics/{prefix}_facts.jsonl"
    SAMPLE = REPO / f"corpus/staging/metrics/{prefix}_sample.jsonl"
    RAW_DIR = REPO / f"events/raw/{prefix}_judge"
TAG, BATCH_NO, PURPOSE = "probe_judge", 9, "probe"
CLASSES = {"doc_level_attribute", "span_truncated", "subject_dropped", "filled_attribute",
           "fabrication", "grade_misassigned"}
PER_CALL_TIMEOUT_S = 600


def judge_version() -> str:
    for line in TEMPLATE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*probe_judge_version:\s*(\S+)", line)
        if m:
            return m.group(1)
    raise model_stub.ModelConfigError("no probe_judge_version header")


def template_sha() -> str:
    return hashlib.sha256(TEMPLATE.read_bytes()).hexdigest()


def load_facts(fact_ids: set[str] | None = None) -> list[dict]:
    items = {}
    for l in SAMPLE.read_text(encoding="utf-8").splitlines():
        if l.strip():
            it = json.loads(l); items[it["event_id"]] = it
    facts = []
    for l in FACTS.read_text(encoding="utf-8").splitlines():
        if not l.strip():
            continue
        f = json.loads(l)
        if fact_ids is not None and f["fact_id"] not in fact_ids:
            continue
        it = items[f["event_id"]]
        facts.append({**f, "grounding_span": it["grounding_span"], "window": it.get("window"),
                      "stratum": it["stratum"], "doc_id": it["doc_id"], "kind": it["kind"], "type": it["type"]})
    return facts


def already(agent_id: str, run: str) -> set[str]:
    return {ev["fact_id"] for ev in eventlog.replay(tag=TAG)
            if ev.get("event_type") == "judge_label" and ev["agent"]["id"] == agent_id
            and ev.get("run") == run}


def judge_batch(batch: list[dict], cfg: dict, jv: str, sha: str, batch_id: str, run: str) -> tuple[int, dict]:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    payload = [{"fact_id": f["fact_id"], "fact": f["fact_text"], "attribute": f["attribute"],
                "item_type": f["type"], "grounding_span": f["grounding_span"], "window": f.get("window")}
               for f in batch]
    prompt = tpl.replace("{{facts_json}}", json.dumps(payload, ensure_ascii=False, indent=1))
    t0 = time.time()
    meta = model_stub.invoke(f"probe:{batch_id}", "", prompt=prompt, timeout=PER_CALL_TIMEOUT_S, config=cfg)
    wall = round(time.time() - t0, 1)
    (RAW_DIR / f"{batch_id}.{cfg['model_id']}.json").write_text(
        json.dumps({"batch_id": batch_id, "run": run, "model_id": cfg["model_id"], "usage": meta["usage"],
                    "cost_usd": meta["cost_usd"], "duration_ms": meta["duration_ms"], "wall_s": wall,
                    "session_id": meta.get("session_id"), "raw_result": meta["raw_result"]},
                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    got = {j.get("fact_id"): j for j in (meta["output"].get("judgments") or [])}
    n = 0
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for pos, f in enumerate(batch):
        j = got.get(f["fact_id"])
        if not j or j.get("label") not in ("entailed", "not_entailed"):
            continue   # missing = not labelled by this agent; resume will retry
        cls = j.get("class") if j.get("label") == "not_entailed" else None
        if cls is not None and cls not in CLASSES:
            cls = None
        conf = j.get("confidence")
        conf = float(conf) if isinstance(conf, (int, float)) and 0 <= conf <= 1 else None
        eventlog.append({"event_type": "judge_label", "purpose": PURPOSE, "run": run,
                         "item_id": f["item_id"], "event_id_judged": f["event_id"], "fact_id": f["fact_id"],
                         "label": j["label"], "class": cls, "confidence": conf,
                         "batch_id": batch_id, "batch_position": pos, "batch_size": len(batch),
                         "agent": {"type": "prov:SoftwareAgent", "id": cfg["model_id"],
                                   "model_version": cfg["model_id"], "prompt_template_sha": sha,
                                   "judge_version": jv, "call_id": meta.get("session_id")},
                         "rated_at": now}, batch=BATCH_NO, tag=TAG)
        n += 1
    return n, meta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None, help="model id (default: model_config model_id)")
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument("--run", required=True, help="run label: calib_single | calib_batch | main | selfcheck")
    ap.add_argument("--fact-ids-file", default=None, help="JSON list of fact_ids to judge (default all)")
    ap.add_argument("--seed", type=int, default=20260822)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--prefix", default="probe")
    a = ap.parse_args(); set_prefix(a.prefix)
    model_stub.guard_no_api_key()
    cfg = model_stub.load_model_config()
    if a.model:
        cfg = {**cfg, "model_id": a.model}
    jv, sha = judge_version(), template_sha()
    ids = set(json.loads(Path(a.fact_ids_file).read_text())) if a.fact_ids_file else None
    facts = load_facts(ids)
    done = already(cfg["model_id"], a.run)
    todo = [f for f in facts if f["fact_id"] not in done]
    if a.limit: todo = todo[:a.limit]
    rng = random.Random(f"{a.seed}:{a.run}:{cfg['model_id']}")
    rng.shuffle(todo)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    print(f"{cfg['model_id']} run={a.run} batch={a.batch}: facts {len(facts)} done {len(done)} todo {len(todo)}", flush=True)
    labelled = 0
    for b in range(0, len(todo), a.batch):
        batch = todo[b:b + a.batch]
        bid = f"{a.run}.{cfg['model_id']}.{hashlib.sha1(','.join(f['fact_id'] for f in batch).encode()).hexdigest()[:10]}"
        n = None
        for attempt in range(3):        # transient CLI/transport errors: retry with backoff
            try:
                n, meta = judge_batch(batch, cfg, jv, sha, bid, a.run); break
            except model_stub.ModelSubstitutionError as exc:
                print(f"  batch {bid}: SUBSTITUTION {exc} — stopping", flush=True); return 2
            except model_stub.ModelInvocationError as exc:
                print(f"  batch {bid}: ERROR (attempt {attempt + 1}/3) {str(exc)[:120]}", flush=True)
                time.sleep(20 * (attempt + 1))
        if n is None:
            continue
        labelled += n
        print(f"  batch {b // a.batch + 1}/{(len(todo) + a.batch - 1) // a.batch}: {n}/{len(batch)} labelled", flush=True)
    print(f"labelled {labelled}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
