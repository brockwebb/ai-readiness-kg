#!/usr/bin/env python3
"""Run the competency-question set in both views and emit the coverage measurement.

Task `cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md` §1.6. **Zero model spend** — the
queries are Cypher and the judging is done by the session that runs this, which is recorded
as an LLM judge in the report and in every Result's description.

    /opt/anaconda3/bin/python3 assessment/cq/run_cq.py [--set assessment/cq/cq_set_v1.yaml] [--date 2026-09-04]

Writes, and never overwrites — a rerun is a new dated file and new Results (§1.6):

    assessment/results/cq_v1_<date>.jsonl        one row per CQ per view
    docs/research/<date>_cq_coverage_v1.md       aggregates and the rule outcome

**The metrics, all pre-registered in the task (§1.4) and none of them adjustable here:**

  rows_raw / rows_collapsed   row counts in the two views
  dup_groups_unioned          collapse groups of size > 1 the collapsed answer depends on —
                              the Zaveri et al. 2016 conciseness cost for this question
  provenance_complete         fraction of answer rows traceable to a Document carrying a
                              content hash. NOTE: the task names `prov_source_sha256` on
                              Document; that property exists on Concept, not on Document, and
                              on Document the hash is `content_hash` (0 vs 211 nodes carry
                              them). The metric uses the property that exists and the RESULT
                              reports the substitution.
  misleading_raw              the raw answer is non-empty but would mislead a reader who did
                              not know duplicates exist — set when the raw view returns rows
                              whose entity column collapses to materially fewer groups.
  answerable_raw/_collapsed   filled by the JUDGE, not by this script: it emits `pending` and
                              the judging session writes its verdict and reason back with
                              --judge. A script that scored its own answerability would be
                              measuring its query, not the graph.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

from collapse import (canonical_key, collapse_rows, load_alias_index,  # noqa: E402
                      load_canonical_index)

TASK = "cc_tasks/2026-09-04_kg_diagnostic_and_cq_harness.md"
#: A raw answer counts as misleading when the collapse removes at least this share of its
#: ROWS — i.e. the reader who trusts the raw list is reading mostly repeats. Row-level, not
#: distinct-string-level, because §1.4's own example ("returns 3 of 14 `AI readiness` nodes'
#: edges") is about nodes: fourteen nodes with the same name share one canonical key, so a
#: string-level measure reads zero exactly where the duplication is worst.
#: Pre-registered here, before the first run, and not tuned afterwards.
MISLEADING_COLLAPSE_SHARE = 0.30


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_one(session, cq: dict, alias_index: dict, canonical_index: dict | None = None) -> dict:
    raw = session.run(cq["cypher_raw"]).data()
    col = collapse_rows(raw, cq["collapse_on"], alias_index)
    # The third view (task 2026-09-05_vocabulary_and_entity_linking §4). Same query, same
    # collapse implementation, a different index: `canonical` groups by the vocabulary term a
    # name RESOLVES_TO. `raw` and `collapsed` are untouched, because the before/after series
    # registered on them is closed and a view that moved them would make it uninterpretable.
    can = collapse_rows(raw, cq["collapse_on"], canonical_index) if canonical_index is not None else None

    distinct_raw = len({k for k in (canonical_key(r.get(cq["collapse_on"])) for r in raw) if k})
    distinct_col = len({g for g in col["groups"].values()})
    # Row-level shrink: how much of the raw answer was repeats of an entity already listed.
    shrink = (1 - col["rows_collapsed"] / col["rows_raw"]) if col["rows_raw"] else 0.0
    can_shrink = ((1 - can["rows_collapsed"] / can["rows_raw"]) if can and can["rows_raw"]
                  else 0.0)

    # provenance: rows traceable to a Document with a content hash
    doc_ids = {r.get("doc_id") for r in raw if r.get("doc_id")}
    hashed = set()
    if doc_ids:
        hashed = {r["doc_id"] for r in session.run(
            "MATCH (d:Document) WHERE d.doc_id IN $ids AND d.content_hash IS NOT NULL "
            "RETURN d.doc_id AS doc_id", ids=sorted(doc_ids)).data()}
    with_doc = [r for r in raw if r.get("doc_id")]
    prov = (sum(1 for r in with_doc if r["doc_id"] in hashed) / len(with_doc)) if with_doc else None

    return {
        "id": cq["id"], "category": cq["category"], "question": cq["question"].strip(),
        "collapse_on": cq["collapse_on"],
        "pass_criterion": cq["pass_criterion"].strip(),
        "rows_raw": col["rows_raw"], "rows_collapsed": col["rows_collapsed"],
        "distinct_entities_raw": distinct_raw, "distinct_entities_collapsed": distinct_col,
        "collapse_shrink": round(shrink, 6),
        "dup_groups_unioned": col["dup_groups"],
        "provenance_complete": None if prov is None else round(prov, 6),
        "misleading_raw": bool(raw) and shrink >= MISLEADING_COLLAPSE_SHARE,
        "rows_canonical": can["rows_collapsed"] if can else None,
        "distinct_entities_canonical": len({g for g in can["groups"].values()}) if can else None,
        "canonical_shrink": round(can_shrink, 6) if can else None,
        "dup_groups_canonical": can["dup_groups"] if can else None,
        "misleading_raw_canonical": (bool(raw) and can_shrink >= MISLEADING_COLLAPSE_SHARE)
                                    if can else None,
        "answerable_raw": "pending", "answerable_collapsed": "pending",
        "answerable_canonical": "pending" if can else None, "judge_reason": "",
        "sample_raw": raw[:6],
        "sample_collapsed": [{k: v for k, v in r.items() if k != "_members"} | {
            "_members": r.get("_members", [])[:6], "_row_count": r.get("_row_count")}
            for r in col["rows"][:6]],
    }


def aggregates(recs: list) -> dict:
    n = len(recs)
    yes_raw = sum(1 for r in recs if r["answerable_raw"] == "yes")
    yes_col = sum(1 for r in recs if r["answerable_collapsed"] == "yes")
    flips = [r["id"] for r in recs
             if r["answerable_collapsed"] == "yes"
             and (r["answerable_raw"] in ("no", "partial") or r["misleading_raw"])]
    # The same statistic against the third view, computed identically so the two are
    # comparable: a CQ flips raw->canonical when the canonical answer is usable and the raw
    # one either was not or would mislead a reader who did not know duplicates exist.
    has_can = any(r.get("answerable_canonical") not in (None, "pending") for r in recs)
    can_flips = [r["id"] for r in recs
                 if r.get("answerable_canonical") == "yes"
                 and (r["answerable_raw"] in ("no", "partial")
                      or r.get("misleading_raw_canonical"))] if has_can else []
    yes_can = sum(1 for r in recs if r.get("answerable_canonical") == "yes")
    by_cat: dict = {}
    for r in recs:
        c = by_cat.setdefault(r["category"], {"n": 0, "flips": 0, "ids": []})
        c["n"] += 1
        if r["id"] in flips:
            c["flips"] += 1
            c["ids"].append(r["id"])
    for c in by_cat.values():
        c["flip"] = round(c["flips"] / c["n"], 6) if c["n"] else None
    flip = round(len(flips) / n, 6) if n else None
    if flip is None:
        branch = "not computable"
    elif flip >= 0.30:
        branch = "entity resolution is P0 and blocks probe design"
    elif flip < 0.10:
        branch = "entity resolution deferred; recorded as a known limitation"
    else:
        branch = ("entity resolution scheduled as a task, not blocking probe design "
                  "(sift-kg three-layer pattern as the design)")
    can_flip = round(len(can_flips) / n, 6) if (n and has_can) else None
    # Enumeration categories, named in §4's acceptance criterion. They are the four whose
    # questions ask "which/how many X are there", which is precisely what duplicate entities
    # break; the other four ask about a definition, a claim, a conflict or a provenance chain,
    # where one good row is an answer.
    ENUM = ("measure_lookup", "instrument_coverage", "discovery_stack", "frontier_candidate")
    enum_recs = [r for r in recs if r["category"] in ENUM]
    enum_not_yes = [r["id"] for r in enum_recs if r.get("answerable_canonical") != "yes"]
    return {"n_cqs": n,
            "A_raw": round(yes_raw / n, 6) if n else None,
            "A_collapsed": round(yes_col / n, 6) if n else None,
            "A_canonical": round(yes_can / n, 6) if (n and has_can) else None,
            "flip": flip, "flip_ids": flips,
            "flip_canonical": can_flip, "flip_canonical_ids": can_flips,
            "C_dup_groups_canonical_total": (sum(r.get("dup_groups_canonical") or 0 for r in recs)
                                             if has_can else None),
            "acceptance": {
                "flip_raw_to_canonical_under_0_10": (can_flip < 0.10) if can_flip is not None else None,
                "every_enumeration_cq_yes_in_canonical": (not enum_not_yes) if has_can else None,
                "enumeration_cqs": len(enum_recs),
                "enumeration_not_yes": enum_not_yes,
                "criterion": ("pre-registered §4: flip(raw->canonical) < 0.10 on v1 AND every "
                              "measure_lookup / instrument_coverage / discovery_stack / "
                              "frontier_candidate CQ answerable `yes` in the canonical view"),
            } if has_can else None,
            "C_dup_groups_unioned_total": sum(r["dup_groups_unioned"] for r in recs),
            "misleading_raw_count": sum(1 for r in recs if r["misleading_raw"]),
            "by_category": by_cat,
            "rule_branch": branch,
            "rule": ("pre-registered §1.5: flip >= 0.30 -> ER is P0; flip < 0.10 -> ER "
                     "deferred; otherwise ER scheduled, not blocking")}


def write_report(recs: list, agg: dict, date: str, version: str = "v1") -> Path:
    """The markdown report §1.6 asks for. States the judge is an LLM in its own header, not a
    footnote: the answerability column is the only judged metric and everything downstream of
    it inherits that."""
    L = [f"# Competency-question coverage of the ai-readiness KG — set {version}, {date}\n",
         f"**Task:** `{TASK}` · **Zero model spend** · **CQ set:** "
         f"`assessment/cq/cq_set_{version}.yaml`, authored and committed before any query ran.\n",
         "**The answerability verdicts below are an LLM judge's** — the session that authored the "
         "questions also read the returned grounding spans and judged them against pass criteria "
         "it had written first and did not revise (§1.7). Every other metric on this page is "
         "counted, not judged.\n",
         "## The decision\n",
         f"- `A_raw` = **{agg['A_raw']}** · `A_collapsed` = **{agg['A_collapsed']}**",
         f"- `flip` = **{agg['flip']}** ({len(agg['flip_ids'])} of {agg['n_cqs']}): "
         f"{', '.join(agg['flip_ids'])}",
         f"- `C` (total duplicate groups unioned) = **{agg['C_dup_groups_unioned_total']}**",
         f"- raw answers flagged misleading: **{agg['misleading_raw_count']}**\n",
         f"**Rule (pre-registered, §1.5): {agg['rule']}**\n",
         f"**Branch that fired: {agg['rule_branch']}.**\n",
         "## Flip by category\n",
         "| category | n | flips | flip | driving CQs |", "|---|---:|---:|---:|---|"]
    for cat, c in sorted(agg["by_category"].items()):
        L.append(f"| {cat} | {c['n']} | {c['flips']} | {c['flip']} | {', '.join(c['ids']) or '—'} |")
    L += ["\n## Per CQ\n",
          "| CQ | category | raw | collapsed | rows raw→coll | dup groups | prov | misleading |",
          "|---|---|---|---|---:|---:|---:|---|"]
    for r in recs:
        prov = "—" if r["provenance_complete"] is None else f"{r['provenance_complete']:.2f}"
        L.append(f"| {r['id']} | {r['category']} | {r['answerable_raw']} | "
                 f"{r['answerable_collapsed']} | {r['rows_raw']}→{r['rows_collapsed']} | "
                 f"{r['dup_groups_unioned']} | {prov} | {'yes' if r['misleading_raw'] else ''} |")
    L.append("\n## Judge reasons\n")
    for r in recs:
        L.append(f"**{r['id']}** ({r['answerable_raw']} / {r['answerable_collapsed']}) — "
                 f"{r['question']}\n\n> {r['judge_reason']}\n")
    out = REPO / "docs" / "research" / f"{date}_cq_coverage_{version}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", default=str(REPO / "assessment/cq/cq_set_v1.yaml"))
    ap.add_argument("--date", default="2026-09-04")
    ap.add_argument("--judge", default=None,
                    help="JSON file of {cq_id: {answerable_raw, answerable_collapsed, "
                         "judge_reason}} to merge into an existing run before aggregating")
    a = ap.parse_args(argv)

    import yaml
    from seldon.config import get_neo4j_driver, load_project_config

    _set = yaml.safe_load(Path(a.set).read_text(encoding="utf-8"))
    cqs = _set["questions"]
    # The output name carries the SET VERSION, not a hardcoded `v1`. v2 exists (task
    # 2026-09-05_vocabulary_and_entity_linking §4) and writing its answers into a `cq_v1_*`
    # file would put two instruments' verdicts under one name — the exact thing the
    # `rubric_version` discipline elsewhere in this repo exists to prevent.
    _ver = str(_set.get("version") or "v1")
    out_jsonl = REPO / "assessment" / "results" / f"cq_{_ver}_{a.date}.jsonl"

    if a.judge:
        verdicts = json.loads(Path(a.judge).read_text(encoding="utf-8"))
        recs = [json.loads(l) for l in out_jsonl.read_text(encoding="utf-8").splitlines() if l.strip()]
        for r in recs:
            v = verdicts.get(r["id"])
            if v:
                r.update({k: v[k] for k in
                          ("answerable_raw", "answerable_collapsed", "answerable_canonical",
                           "judge_reason") if k in v})
        unjudged = [r["id"] for r in recs if r["answerable_raw"] == "pending"]
        if unjudged:
            raise SystemExit(f"FATAL: {len(unjudged)} CQ(s) still unjudged: {', '.join(unjudged)}")
    else:
        config = load_project_config(REPO)
        driver = get_neo4j_driver(config)
        try:
            with driver.session(database=config["neo4j"]["database"]) as session:
                alias_index = load_alias_index(session)
                canonical_index = load_canonical_index(session)
                print(f"alias index: {len(alias_index)} names carry aliases; "
                      f"canonical index: {len(canonical_index)} names resolve to a shared term",
                      file=sys.stderr)
                recs = [run_one(session, cq, alias_index, canonical_index) for cq in cqs]
        finally:
            driver.close()

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    out_jsonl.write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n"
                                 for r in recs), encoding="utf-8")
    agg = aggregates(recs)
    print(json.dumps({k: v for k, v in agg.items() if k != "by_category"}, indent=1))
    print(f"-> {out_jsonl.relative_to(REPO)}", file=sys.stderr)
    (REPO / "assessment" / "results" / f"cq_{_ver}_{a.date}_aggregates.json").write_text(
        json.dumps(agg, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    if all(r["answerable_raw"] != "pending" for r in recs):
        rep = write_report(recs, agg, a.date, _ver)
        print(f"-> {rep.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
