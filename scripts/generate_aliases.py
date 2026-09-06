#!/usr/bin/env python3
"""Generate surface-form aliases, run the §1.2 controls, and write epoch-2 candidates.
**Zero model spend.**

Task `cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md` §1. The gold sample measured
stratum D's recall at **zero** — six of twenty near-misses were genuine matches and every one
was a surface-form variant. `scripts/alias_generators.py` holds the rules and the prior art;
this script applies them to the live graph, gates on the gold sample's own pairs, and writes.

**The controls are the point, and they are gold-derived rather than invented.** The positive
control is the six stratum-D pairs the rater called `same`: if the generators do not join at
least five of them, the generators do not do the job they were written for. The negative
control is the 19 stratum-C and 14 stratum-D pairs the rater called `different`: if any of
them are joined, the generators are merging things a reader said are distinct, and that is a
**hard stop** — a false merge is the expensive error (DD-045 §3).

    /opt/anaconda3/bin/python3 scripts/generate_aliases.py --phase plan
    /opt/anaconda3/bin/python3 scripts/generate_aliases.py --phase write
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

from kg import vocab  # noqa: E402

import alias_generators as ag  # noqa: E402
import link_vocabulary as lv  # noqa: E402

TASK = "cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md"
OUT = REPO / "state" / "alias_generation_2026-09-06.json"
KEY = REPO / "state" / "er_gold_key.json"
LABELS = REPO / "assessment" / "results" / "er_gold_labels_2026-09-05_main.jsonl"


def known_forms(terms: dict) -> dict:
    """{normalised form: [term_id]} over ACTIVE terms — prefLabels and aliases alike."""
    idx: dict = collections.defaultdict(list)
    for tid, t in terms.items():
        if t["state"] != "active":
            continue
        for label in [t["pref_label"], *t["alt_labels"]]:
            k = vocab.normalize(label)
            if k and tid not in idx[k]:
                idx[k].append(tid)
    return dict(idx)


def propose(nodes: list, terms: dict) -> tuple:
    """[(term_id, alias, derivation, evidence)] plus the refusal counts.

    Three passes, in this order because each feeds the next:

    1. **Schwartz & Hearst over TERM LABELS** (§1.1: "and every active term's
       prefLabel/aliases"). A term whose own label carries the parenthetical — `RDF (Resource
       Description Framework)` — knows both forms already; registering them makes the term
       reachable by either, and makes those forms available to pass 2's `known` set.
    2. **The four standardisation strips over unresolved node names**, against the `known`
       set pass 1 just widened.
    3. **Schwartz & Hearst over node names and spans.** When a pair mined from a node's own
       NAME resolves to exactly one term, the alias written is the node's **own surface
       form** — that is what makes the node resolve, and aliasing only the counterpart form
       leaves the node exactly as unresolved as it was.

    A proposal is made only for a term the form names UNAMBIGUOUSLY. The label-theft guard
    from `27b360f4` §1.2 is applied unchanged: an alias already claimed by a different term is
    refused, because the term that owns a name is not overridden by another term's variant.
    """
    forms = known_forms(terms)
    known = set(forms)
    linked = {k for k, _ in lv.auto_link(nodes, terms)["linked"]}
    counts = collections.Counter()
    proposals, seen = [], set()

    def offer(tid, alias, derivation, evidence, node_label=None):
        k = vocab.normalize(alias)
        if not k:
            return False
        allowed = terms[tid].get("node_labels") or []
        if node_label and allowed and node_label not in allowed:
            counts["refused_label_block"] += 1
            return False
        owner = forms.get(k)
        if owner and owner != [tid]:
            counts["refused_label_theft"] += 1
            return False
        if (tid, k) in seen:
            return False
        seen.add((tid, k))
        forms.setdefault(k, [tid])
        known.add(k)
        proposals.append((tid, alias, derivation, evidence))
        counts[f"generated_{derivation}"] += 1
        return True

    # ---- pass 1: term labels
    for tid, t in sorted(terms.items()):
        if t["state"] != "active":
            continue
        for label in [t["pref_label"], *t["alt_labels"]]:
            for long_form, short in ag.schwartz_hearst(label):
                for alias in (long_form, short):
                    offer(tid, alias, "schwartz_hearst", f"term:{tid}")

    # ---- pass 2: the standardisation strips
    for n in nodes:
        if n["key"] in linked or not n.get("name"):
            continue
        for v in ag.variants(n["name"], known):
            tids = forms.get(vocab.normalize(v["resolved_form"]) or "", [])
            if len(tids) != 1:
                counts["refused_ambiguous_target"] += 1
                continue
            offer(tids[0], n["name"], v["derivation"], n["key"], node_label=n["label"])

    # ---- pass 3: Schwartz & Hearst over node names and spans
    for n in nodes:
        unresolved = n["key"] not in linked
        for source, text in (("name", n.get("name") or ""),
                             ("span", (n.get("span") or "")[:1200])):
            for long_form, short in ag.schwartz_hearst(text):
                kl, ks = vocab.normalize(long_form), vocab.normalize(short)
                tl, ts = forms.get(kl or "", []), forms.get(ks or "", [])
                if len(tl) == 1 and len(ts) <= 1 and (not ts or ts == tl):
                    tid, counterpart = tl[0], short
                elif len(ts) == 1 and len(tl) <= 1 and (not tl or tl == ts):
                    tid, counterpart = ts[0], long_form
                else:
                    if tl and ts and tl != ts:
                        counts["refused_label_theft"] += 1
                    continue
                offer(tid, counterpart, "schwartz_hearst", n["key"], node_label=n["label"])
                # the node's OWN surface form, which is the alias that actually resolves it
                if unresolved and source == "name" and n.get("name"):
                    offer(tid, n["name"], "schwartz_hearst", n["key"], node_label=n["label"])
    return proposals, counts


def gold_controls(nodes: list, terms: dict, proposals: list) -> dict:
    """Would the proposals join the gold pairs they must, and none they must not?"""
    key = {p["pair_id"]: p for p in json.loads(KEY.read_text(encoding="utf-8"))["pairs"]}
    lab = {json.loads(l)["pair_id"]: json.loads(l)
           for l in LABELS.read_text(encoding="utf-8").splitlines() if l.strip()}
    trial = {tid: dict(t, alt_labels=list(t["alt_labels"])) for tid, t in terms.items()}
    for tid, alias, _, _ in proposals:
        if alias not in trial[tid]["alt_labels"]:
            trial[tid]["alt_labels"].append(alias)
    res = lv.auto_link(nodes, trial)
    where = dict(res["linked"])

    def joined(pid: str) -> bool:
        p = key[pid]
        a, b = where.get(p["node_a"]), where.get(p["node_b"])
        return bool(a and b and a == b)

    pos = [p for p in key if key[p]["stratum"] == "D" and lab[p]["verdict"] == "same"]
    neg = [p for p in key if key[p]["stratum"] in ("C", "D") and lab[p]["verdict"] == "different"]
    pos_joined = [p for p in pos if joined(p)]
    neg_joined = [p for p in neg if joined(p)]
    return {"positive_pairs": len(pos), "positive_joined": len(pos_joined),
            "positive_joined_ids": sorted(pos_joined),
            "positive_missed_ids": sorted(set(pos) - set(pos_joined)),
            "positive_passed": len(pos_joined) >= 5,
            "negative_pairs": len(neg), "negative_violations": sorted(neg_joined),
            "negative_passed": not neg_joined}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=("plan", "write"), default="plan")
    a = ap.parse_args(argv)

    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            nodes = lv.read_nodes(s)
    finally:
        driver.close()

    terms = vocab.project()
    proposals, counts = propose(nodes, terms)
    ctrl = gold_controls(nodes, terms, proposals)
    before = len(lv.auto_link(nodes, terms)["linked"])
    trial = {tid: dict(t, alt_labels=list(t["alt_labels"])) for tid, t in terms.items()}
    for tid, alias, _, _ in proposals:
        if alias not in trial[tid]["alt_labels"]:
            trial[tid]["alt_labels"].append(alias)
    after = len(lv.auto_link(nodes, trial)["linked"])

    summary = {"task": TASK, "vocabulary_epoch": vocab.epoch(),
               "linkable_nodes": len(nodes), "proposals": len(proposals),
               "counts": dict(counts),
               "auto_linked_before": before, "auto_linked_after": after,
               "auto_linked_delta": after - before,
               "residue_before": len(nodes) - before, "residue_after": len(nodes) - after,
               "controls": ctrl,
               "gate_passed": bool(ctrl["positive_passed"] and ctrl["negative_passed"]),
               "sample": [{"term_id": t, "alias": al, "derivation": d, "evidence": e}
                          for t, al, d, e in proposals[:25]]}
    OUT.write_text(json.dumps({**summary, "all_proposals": [
        {"term_id": t, "alias": al, "derivation": d, "evidence": e}
        for t, al, d, e in proposals]}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))

    if a.phase == "plan":
        return 0
    if not ctrl["negative_passed"]:
        raise SystemExit(f"HARD STOP: {len(ctrl['negative_violations'])} negative-control "
                         f"pair(s) would be joined: {ctrl['negative_violations']}. Nothing written.")
    if not ctrl["positive_passed"]:
        print("POSITIVE CONTROL FAILED — nothing written (§1.2).", file=sys.stderr)
        return 1
    for tid, alias, derivation, evidence in proposals:
        vocab.add_alias(tid, alias, source=f"surface-form generator ({TASK} §1.1)",
                        derivation=derivation, evidence=evidence)
    print(f"wrote {len(proposals)} term_alias_added events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
