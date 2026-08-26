#!/usr/bin/env python3
"""Summarize a claude-cli backend usage JSONL slice (one benchmark document).
Reports: calls, token totals (fresh input / cache read / cache creation /
total input context / output), cache-read ratio, cost, model-call time."""
import json
import sys

def summarize(path):
    recs = [json.loads(l) for l in open(path) if l.strip()]
    if not recs:
        return {"calls": 0}
    t = lambda k: sum(r[k] for r in recs)
    total_in = t("input_tokens") + t("cache_read_tokens") + t("cache_creation_tokens")
    return {
        "calls": len(recs),
        "input_fresh": t("input_tokens"),
        "cache_read": t("cache_read_tokens"),
        "cache_creation": t("cache_creation_tokens"),
        "total_input_ctx": total_in,
        "output": t("output_tokens"),
        "grand_total_tokens": total_in + t("output_tokens"),
        "cache_read_ratio": round(t("cache_read_tokens") / total_in, 4) if total_in else None,
        "cost_usd_envelope": round(sum(r.get("cost_usd") or 0 for r in recs), 4),
        "model_time_s": round(sum(r.get("duration_ms") or 0 for r in recs) / 1000, 1),
        "retries": t("num_retries"),
    }

if __name__ == "__main__":
    print(json.dumps(summarize(sys.argv[1]), indent=1))
