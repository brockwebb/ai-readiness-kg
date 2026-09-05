#!/usr/bin/env python3
"""The residue: what the vocabulary could not name, and what epoch 2 should. **Zero spend.**

Task `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §3. Franklin, Halevy & Maier
(2005), "From databases to dataspaces", *SIGMOD Record* 34(4), and Madhavan et al. (2007),
"Web-scale data integration: you can only afford to pay as you go", CIDR: seed a rough
vocabulary, resolve against it, **promote what recurs and deprecate what does not**, and never
wait for a complete ontology. This script is the promote-what-recurs half.

**The recurrence rule is `>= 3 documents`, from the task, and it is a rule about DOCUMENTS and
not about nodes.** A name asserted five times inside one paper is one author's phrasing; the
same name in three papers is the corpus agreeing on something. The seed already applies the
weaker version of this (a term needs a group of at least two nodes); three documents is the
stronger bar a promotion should clear.

**Nothing is promoted here.** §3 is explicit: promotion is a scheduled cadence, not a per-item
review, and a proposal file an operator can read is the deliverable. Writing epoch 2 from this
script would make the cadence a side effect of running a diagnostic.

    /opt/anaconda3/bin/python3 scripts/vocab_residue.py
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

from kg import eventlog, vocab  # noqa: E402

import link_vocabulary as lv  # noqa: E402

TASK = "cc_tasks/2026-09-05_vocabulary_and_entity_linking.md"
OUT_YAML = REPO / "ontology" / "vocabulary_proposals_epoch2.yaml"
OUT_JSON = REPO / "state" / "vocab_residue_2026-09-05.json"
MIN_DOCUMENTS = 3


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--min-documents", type=int, default=MIN_DOCUMENTS)
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
    # The same two link paths the loader uses, so "unresolved" here means exactly what
    # `n.unresolved = true` will mean in the graph after the replay.
    judged = {ev["node_key"] for ev in eventlog.replay()
              if ev.get("event_type") == "term_link_judged" and ev.get("verdict") == "same"}
    res = lv.auto_link(nodes, terms)
    linked = {k for k, _ in res["linked"]} | judged
    unresolved = [n for n in nodes if n["key"] not in linked]

    groups = collections.defaultdict(list)
    for n in unresolved:
        k = vocab.normalize(n.get("name"))
        if k:
            groups[(n["label"], k)].append(n)

    proposals = []
    for (label, key), members in sorted(groups.items()):
        docs = sorted({m.get("doc_id") for m in members if m.get("doc_id")})
        if len(docs) < a.min_documents:
            continue
        surfaces = collections.Counter(m.get("name") for m in members if m.get("name"))
        span = next((m.get("span") for m in members if m.get("span")), "") or ""
        proposals.append({
            "proposed_term_id": f"{vocab.NS}:{label.lower()}/"
                                f"{key.replace(' ', '-')[:80]}",
            "pref_label": surfaces.most_common(1)[0][0],
            "node_label": label,
            "alt_labels": sorted(s for s in surfaces if s != surfaces.most_common(1)[0][0]),
            "nodes": len(members),
            "documents": len(docs),
            "sources": docs[:12],
            "draft_scope_note": " ".join(span.split())[:400],
        })
    proposals.sort(key=lambda p: (-p["documents"], -p["nodes"]))

    summary = {
        "task": TASK, "vocabulary_epoch": vocab.epoch(),
        "nodes": len(nodes),
        "linked_total": len(linked),
        "linked_deterministic": len(res["linked"]),
        "linked_judged": len(judged & {n["key"] for n in nodes}),
        "unresolved": len(unresolved),
        "unresolved_named_groups": len(groups),
        "min_documents": a.min_documents,
        "proposed_epoch_2_terms": len(proposals),
        "proposed_by_label": dict(collections.Counter(p["node_label"] for p in proposals)),
        "unresolved_by_label": dict(collections.Counter(n["label"] for n in unresolved)),
    }

    import yaml
    OUT_YAML.parent.mkdir(parents=True, exist_ok=True)
    OUT_YAML.write_text(
        "# Proposed vocabulary terms for epoch 2 — NOT PROMOTED.\n"
        f"# {TASK} §3. Every entry is an unresolved name recurring in >= {a.min_documents}\n"
        "# documents after epoch 1 linking (deterministic + judged). Promotion is a scheduled\n"
        "# cadence, not a per-item review: an operator promotes from this file, and nothing\n"
        "# in the pipeline reads it.\n"
        + yaml.safe_dump({"epoch": 2, "generated_from": TASK, "proposals": proposals},
                         sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8")
    OUT_JSON.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    print(f"-> {OUT_YAML.relative_to(REPO)}  {OUT_JSON.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
