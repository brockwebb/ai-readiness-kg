#!/usr/bin/env python3
"""Probe Phase 6 — hard-item export for the operator (task 2026-08-22_faithfulness_probe).
Facts with posterior in [0.35, 0.65], or raters split with both sides confidence >= 0.7.
Writes probe_hard_items.jsonl (blank human_label / human_class / orcid — never fabricated)
and a readable probe_hard_items.md. Cap 60 most uncertain; overflow noted."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from kg import eventlog  # noqa: E402

AGG = REPO / "corpus/staging/metrics/probe_aggregate.json"
FACTS = REPO / "corpus/staging/metrics/probe_facts.jsonl"
SAMPLE = REPO / "corpus/staging/metrics/probe_sample.jsonl"
OUT_J = REPO / "corpus/staging/metrics/probe_hard_items.jsonl"
OUT_M = REPO / "corpus/staging/metrics/probe_hard_items.md"
CAP = 60


def main() -> int:
    agg = json.loads(AGG.read_text())
    facts = {f["fact_id"]: f for f in (json.loads(l) for l in FACTS.read_text().splitlines() if l.strip())}
    items = {it["event_id"]: it for it in (json.loads(l) for l in SAMPLE.read_text().splitlines() if l.strip())}
    labels = defaultdict(list)
    for ev in eventlog.replay(tag="probe_judge"):
        if ev.get("event_type") == "judge_label" and ev.get("run") == "main":
            labels[ev["fact_id"]].append({"agent": ev["agent"]["id"], "label": ev["label"], "class": ev.get("class"),
                                          "confidence": ev.get("confidence")})
    hard = []
    for fid, v in agg["per_fact"].items():
        p = v["p_entailed"]; ls = labels.get(fid, [])
        split = {l["label"] for l in ls}
        conf_split = len(split) == 2 and all(any((l["confidence"] or 0) >= 0.7 for l in ls if l["label"] == s) for s in split)
        if 0.35 <= p <= 0.65 or conf_split:
            hard.append((abs(p - 0.5), fid, v, ls))
    hard.sort(key=lambda t: t[0])
    total = len(hard); hard = hard[:CAP]
    with OUT_J.open("w", encoding="utf-8") as fj:
        for _, fid, v, ls in hard:
            f = facts[fid]; it = items[f["event_id"]]
            fj.write(json.dumps({"fact_id": fid, "item_id": f["item_id"], "event_id": f["event_id"], "doc_id": it["doc_id"],
                                 "stratum": it["stratum"], "attribute": f["attribute"], "fact_text": f["fact_text"],
                                 "grounding_span": it["grounding_span"], "window": it.get("window"),
                                 "p_entailed": v["p_entailed"], "map_class": v["class"], "raters": ls,
                                 "human_label": None, "human_class": None, "orcid": None, "rated_at": None},
                                ensure_ascii=False) + "\n")
    md = [f"# Probe hard items ({len(hard)} of {total} uncertain facts; cap {CAP})", "",
          "Label each fact: `human_label` entailed|not_entailed, `human_class` one of the six when not entailed, and your ORCID in `orcid` — in the JSONL sibling. A follow-on ingests these as a `prov:Person` rater.", ""]
    for _, fid, v, ls in hard:
        f = facts[fid]; it = items[f["event_id"]]
        md += [f"## {fid} — {it['type']} `{f['item_id']}` ({it['doc_id']}) · P(entailed)={v['p_entailed']:.2f} · MAP class={v['class']}", "",
               f"**Fact:** {f['fact_text']}", "", f"> **Span:** \"{it['grounding_span']}\"", ""]
        if it.get("window"):
            md += ["    " + it["window"].replace("\n", " "), ""]
        for l in ls:
            md.append(f"- {l['agent']}: {l['label']} / {l['class']} (conf {l['confidence']})")
        md.append("")
    OUT_M.write_text("\n".join(md), encoding="utf-8")
    print(f"hard items: {len(hard)} written (uncertain total {total}{' — OVERFLOW capped' if total > CAP else ''})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
