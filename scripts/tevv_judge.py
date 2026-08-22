#!/usr/bin/env python3
"""TEVV Phase 3 — faithfulness judging (task 2026-08-22_kernel_tevv).

Judge = the pinned extraction model (kg/extraction/model_config.yaml) via model_stub.invoke
(hermetic cwd, Max OAuth, model-substitution gate). One item per call; prompt from
kg/extraction/judge_template.md (judge_version header stamped on every judgment). Output
strictly {entailed, reason}. Raw envelopes persisted to events/raw/tevv_judge/. Judgments
appended to corpus/staging/metrics/tevv_faithfulness_judgments.jsonl (resume by item
event_id). Known limitation (DD-013): same model family as the extractor — the 40-item
human subset exists for that reason.
"""
from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kg.extraction import model_stub  # noqa: E402

SAMPLE = REPO / "corpus" / "staging" / "metrics" / "tevv_faithfulness_sample.jsonl"
OUT = REPO / "corpus" / "staging" / "metrics" / "tevv_faithfulness_judgments.jsonl"
RAW_DIR = REPO / "events" / "raw" / "tevv_judge"
TEMPLATE = REPO / "kg" / "extraction" / "judge_template.md"
PER_CALL_TIMEOUT_S = 300


def judge_version() -> str:
    for line in TEMPLATE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*judge_version:\s*(\S+)", line)
        if m:
            return m.group(1)
    raise model_stub.ModelConfigError(f"no judge_version header in {TEMPLATE}")


def render(item: dict) -> str:
    tpl = TEMPLATE.read_text(encoding="utf-8")
    shown = {"id": item["item_id"], "type": item["type"], "text": item["text"], **(item.get("extra") or {})}
    return (tpl.replace("{{item_kind}}", item["kind"])
               .replace("{{item_type}}", item["type"])
               .replace("{{item_json}}", json.dumps(shown, ensure_ascii=False, indent=1))
               .replace("{{grounding_span}}", item["grounding_span"]))


def parse_verdict(output: dict) -> tuple[bool, str]:
    if not isinstance(output, dict) or not isinstance(output.get("entailed"), bool):
        raise model_stub.ModelInvocationError(f"judge output is not {{entailed: bool, ...}}: {str(output)[:200]}")
    return output["entailed"], str(output.get("reason", ""))[:500]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-items", type=int, default=None)
    ap.add_argument("--retry-failed", action="store_true")
    a = ap.parse_args()
    model_stub.guard_no_api_key()
    jv = judge_version()
    cfg = model_stub.load_model_config()
    items = [json.loads(l) for l in SAMPLE.read_text(encoding="utf-8").splitlines() if l.strip()]
    done: dict[str, dict] = {}
    if OUT.exists():
        for l in OUT.read_text(encoding="utf-8").splitlines():
            if l.strip():
                j = json.loads(l); done[j["event_id"]] = j
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    n, ok, fail = 0, 0, 0
    for it in items:
        prev = done.get(it["event_id"])
        if prev and (prev.get("entailed") is not None or not a.retry_failed):
            continue
        if a.max_items is not None and n >= a.max_items:
            break
        n += 1
        prompt = render(it)
        t0 = time.time()
        rec = {"event_id": it["event_id"], "item_id": it["item_id"], "kind": it["kind"],
               "type": it["type"], "stratum": it["stratum"], "doc_id": it["doc_id"],
               "judge_version": jv, "model_id": cfg["model_id"],
               "ts": datetime.datetime.now(datetime.timezone.utc).isoformat()}
        try:
            meta = model_stub.invoke(f"judge:{it['event_id'][:12]}", "", prompt=prompt,
                                     timeout=PER_CALL_TIMEOUT_S, config=cfg)
            entailed, reason = parse_verdict(meta["output"])
            rec.update({"entailed": entailed, "reason": reason, "usage": meta["usage"],
                        "cost_usd": meta["cost_usd"], "duration_ms": meta["duration_ms"],
                        "wall_s": round(time.time() - t0, 1), "error": None})
            ok += 1
        except (model_stub.ModelInvocationError, model_stub.ModelSubstitutionError) as exc:
            meta = {"raw_result": None}
            rec.update({"entailed": None, "reason": None, "error": str(exc)[:300],
                        "wall_s": round(time.time() - t0, 1)})
            fail += 1
        (RAW_DIR / f"{it['event_id']}.{jv}.{cfg['model_id']}.json").write_text(
            json.dumps({**rec, "raw_result": meta.get("raw_result")}, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8")
        with OUT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        print(f"  [{n}] {it['stratum']:28s} {str(rec['entailed']):5s} {rec['wall_s']}s "
              f"{'' if not rec['error'] else 'ERR ' + rec['error'][:60]}", flush=True)
    print(f"judged {n}: ok {ok} fail {fail}; total recorded {len(done) + n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
