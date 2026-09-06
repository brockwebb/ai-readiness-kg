#!/usr/bin/env python3
"""Draw the ER gold sample and write the operator's blind sheet. **Zero model spend.**

Task `cc_tasks/2026-09-05_homograph_split_and_er_gold_sample.md` §5 — the one operator
touchpoint in that task, and it is a **value input the system is designed to measure, not
guess** (operating doctrine §2.3): whether two nodes denote the same thing is exactly the
judgment a gold standard exists to capture. `scripts/score_er_gold.py` was written and tested
BEFORE this sampler ran.

**The sheet is blind, and every omission is deliberate.** No cosine, no term name, no stratum,
no current pipeline decision. The strata are held in `state/er_gold_key.json`. A sheet that
showed the pipeline's answer would measure the operator's agreeableness; a sheet that showed
the cosine would anchor on the selector, which is the adversarial-review rubric's §2 rule and
the calibrated failure it records.

**Five strata, 20 each**, chosen so the sample spans the decision surface rather than its easy
middle: A the exact-name auto-links (the bulk, expected clean), B and C the prior task's
clerical band on both sides of its verdict, D the near-misses just under the 0.80 floor — the
recall question — and E cross-arm pairs inside terms the homograph pass KEPT, which is where a
false merge would hide. Weights are population sizes, registered, because 20 of a stratum of
90,000 and 20 of a stratum of 45 do not carry the same evidence.

    /opt/anaconda3/bin/python3 scripts/build_er_gold_sample.py [--seed 20260905]
"""
from __future__ import annotations

import argparse
import collections
import itertools
import json
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

from kg import vocab  # noqa: E402

import link_vocabulary as lv  # noqa: E402

TASK = "cc_tasks/2026-09-05_homograph_split_and_er_gold_sample.md"
SHEET = REPO / "docs" / "research" / "2026-09-05_er_gold_sample.md"
KEY = REPO / "state" / "er_gold_key.json"
DECISIONS = REPO / "assessment" / "results" / "vocab_link_decisions_2026-09-05_opus.jsonl"
HOMOGRAPH = REPO / "state" / "homograph_scores_2026-09-05.json"

PER_STRATUM = 20
NEAR_MISS = (0.70, 0.80)

STRATA = {
    "A": "exact-name auto-links: both nodes reached one term by the alias-first rule",
    "B": "clerical band, ACCEPTED by the prior task's judge",
    "C": "clerical band, REJECTED by the prior task's judge",
    "D": "near-miss: best-term cosine in [0.70, 0.80), auto-rejected below the floor",
    "E": "cross-arm pairs inside a term the homograph pass KEPT",
}


def node_rows(session) -> dict:
    rows = session.run(
        "MATCH (n) WHERE n.key IS NOT NULL AND n.name IS NOT NULL "
        "OPTIONAL MATCH (d:Document {doc_id: n.doc_id}) "
        "RETURN n.key AS key, labels(n)[0] AS label, n.name AS name, "
        "       n.grounding_span AS span, n.doc_id AS doc_id, d.title AS title, "
        "       d.construct_arm AS arm").data()
    return {r["key"]: r for r in rows}


def resolved_members(session) -> dict:
    out: dict = collections.defaultdict(list)
    for r in session.run("MATCH (n)-[:RESOLVES_TO]->(t:Term) "
                         "RETURN t.term_id AS term, n.key AS key").data():
        out[r["term"]].append(r["key"])
    return dict(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=20260905)
    ap.add_argument("--per-stratum", type=int, default=PER_STRATUM)
    a = ap.parse_args(argv)
    rng = random.Random(a.seed)

    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            nodes = node_rows(s)
            members = resolved_members(s)
            all_nodes = lv.read_nodes(s)
    finally:
        driver.close()

    terms = vocab.project()
    decisions = [json.loads(l) for l in DECISIONS.read_text(encoding="utf-8").splitlines() if l.strip()]
    homo = json.loads(HOMOGRAPH.read_text(encoding="utf-8"))

    pools: dict = {}

    # ---- A: every within-term pair among auto-linked members.
    a_pairs = []
    judged_keys = {d["node_key"] for d in decisions}
    for tid, keys in members.items():
        ks = sorted(k for k in keys if k in nodes and k not in judged_keys)
        if len(ks) < 2:
            continue
        a_pairs += [(x, y, tid) for x, y in itertools.combinations(ks, 2)]
    pools["A"] = a_pairs

    # ---- B / C: the prior band, converted to node-node by pairing with a term member the
    # node was NOT compared against directly. A band decision is (node, term); the gold
    # question is about two NODES, so the counterpart is a member the term already had.
    def band_pairs(verdict: str) -> list:
        out = []
        for d in decisions:
            if d["verdict"] != verdict:
                continue
            others = [k for k in members.get(d["term_id"], []) if k != d["node_key"] and k in nodes]
            if not others or d["node_key"] not in nodes:
                continue
            out.append((d["node_key"], rng.choice(sorted(others)), d["term_id"]))
        return out

    pools["B"] = band_pairs("same")
    pools["C"] = band_pairs("different")

    # ---- D: near misses. Recomputed in the SAME embedding space `link_vocabulary` used, with
    # the window opened below the 0.80 floor — these are the pairs the lower threshold threw
    # away, which is where recall is lost and nowhere else.
    res = lv.auto_link(all_nodes, terms)
    best = lv.best_terms(res["unlinked"], terms)
    d_pairs = []
    for key, (tid, cos) in best.items():
        if not (NEAR_MISS[0] <= cos < NEAR_MISS[1]):
            continue
        others = [k for k in members.get(tid, []) if k in nodes]
        if others and key in nodes:
            d_pairs.append((key, rng.choice(sorted(others)), tid))
    pools["D"] = d_pairs

    # ---- E: cross-arm pairs inside terms the homograph pass KEPT. If a homograph survived
    # §1's thresholds, this is the stratum in which it shows up as a false merge.
    e_pairs = []
    kept = [t for t, x in homo["terms"].items() if x["klass"] == "auto_keep"]
    for tid in kept:
        by_arm: dict = collections.defaultdict(list)
        for k in members.get(tid, []):
            if k in nodes and nodes[k]["arm"]:
                by_arm[nodes[k]["arm"]].append(k)
        arms = sorted(by_arm)
        for x, y in itertools.combinations(arms, 2):
            e_pairs += [(p, q, tid) for p in sorted(by_arm[x]) for q in sorted(by_arm[y])]
    pools["E"] = e_pairs

    # ---- draw
    drawn, key_rows = {}, []
    system_match = {"A": True, "B": True, "C": False, "D": False, "E": True}
    n = 0
    for h in sorted(pools):
        pool = sorted(set((x, y, t) for x, y, t in pools[h] if x != y))
        take = pool if len(pool) <= a.per_stratum else rng.sample(pool, a.per_stratum)
        drawn[h] = sorted(take)
        for x, y, tid in drawn[h]:
            n += 1
            key_rows.append({"pair_id": f"P{n:03d}", "stratum": h,
                             "system_match": system_match[h],
                             "node_a": x, "node_b": y, "term_id": tid})
    weights = {h: (len(set(pools[h])) / len(drawn[h]) if drawn[h] else 0.0) for h in pools}

    KEY.write_text(json.dumps({
        "task": TASK, "seed": a.seed, "per_stratum": a.per_stratum,
        "strata": STRATA,
        "stratum_population": {h: len(set(pools[h])) for h in pools},
        "stratum_drawn": {h: len(drawn[h]) for h in pools},
        "stratum_weights": weights,
        "pairs": key_rows}, indent=1) + "\n", encoding="utf-8")

    # ---- the blind sheet
    split_state = ("**§2 wrote NOTHING to the vocabulary log** — the §1.3 positive control "
                   "failed, so no homograph split was applied. These pairs are drawn from the "
                   "PRE-SPLIT vocabulary (epoch 1)."
                   if not homo.get("positive_control_passed") else
                   "Drawn after the §2 homograph split landed (epoch 2).")
    L = [f"# Entity-resolution gold sample — {len(key_rows)} pairs for the operator\n",
         f"**Task:** `{TASK}` §5. **Zero model spend.** **Seed:** {a.seed}. "
         f"**Drawn:** {a.per_stratum} per stratum from five strata.\n",
         f"{split_state}\n",
         "## What to do\n",
         "For each pair below, read the two spans and decide whether the two nodes denote "
         "**the same thing**. Not whether they are related, not whether they are about the "
         "same topic — whether a reader asking \"how many distinct X does this corpus "
         "describe\" should count them once or twice.\n",
         "- `same` — one thing, named twice.\n"
         "- `different` — two things. Includes the case where one is a SPECIES of the other "
         "(\"explainable AI techniques\" is narrower than \"explainable AI\"): narrower is "
         "not the same.\n"
         "- `uncertain` — the spans do not let you tell. This is a real answer and is "
         "excluded from the rates rather than pushed to one side.\n",
         "**You are not checking the machine's work.** The sheet deliberately does not show "
         "you the pipeline's decision, the similarity score, the vocabulary term, or which "
         "stratum a pair came from — those are held in `state/er_gold_key.json` and are "
         "joined in only at scoring time. Please do not read the key first.\n",
         "---\n"]
    for row in key_rows:
        A, B = nodes[row["node_a"]], nodes[row["node_b"]]
        L.append(f"## {row['pair_id']}\n")
        for tag, x in (("A", A), ("B", B)):
            L.append(f"**Node {tag}** — `{x['label']}` · *{x['title'] or x['doc_id']}* "
                     f"· arm `{x['arm']}`\n")
            L.append(f"> **{x['name']}**\n>\n> {' '.join((x['span'] or '(no span)').split())[:700]}\n")
        L.append(f"**{row['pair_id']} — verdict (same / different / uncertain):** ______\n")
        L.append(f"**{row['pair_id']} — note:** ______\n")
        L.append("---\n")

    SHEET.parent.mkdir(parents=True, exist_ok=True)
    SHEET.write_text("\n".join(L) + "\n", encoding="utf-8")
    summary = {"seed": a.seed, "pairs": len(key_rows),
               "stratum_population": {h: len(set(pools[h])) for h in pools},
               "stratum_drawn": {h: len(drawn[h]) for h in pools},
               "stratum_weights": {h: round(w, 4) for h, w in weights.items()},
               "split_applied": bool(homo.get("positive_control_passed"))}
    print(json.dumps(summary, indent=1))
    print(f"-> {SHEET.relative_to(REPO)}  {KEY.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
