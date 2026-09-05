#!/usr/bin/env python3
"""Deterministic entity linking against the controlled vocabulary. **Zero model spend.**

Task `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §1.3. Fellegi & Sunter (1969),
*JASA* 64(328):1183-1210, built for census record linkage: score candidate pairs, set an upper
threshold above which you link automatically and a lower one below which you reject
automatically, and send the band between them to clerical review. The design's whole point is
that **the band is where the judgment goes** — so the two automatic zones must be cheap and
honest about what they cannot decide, and the band must be small enough to afford. §2 is the
band; this script is everything else.

**Upper threshold (auto-link).** The node's name, normalised, is the preferred label or an
alias of *exactly one* term **within its own KG label block**. Two claimants link to neither.
This is a lookup, not a score: `kg.vocab.resolve` is the whole decision, and it is the same
function `build_projection.py` calls at write time (§1.4), so a node linked here and a node
linked at load are linked by identical code.

**Blocking.** Same KG label — `Concept`↔`Concept`, `Instrument`↔`Instrument`. An `Instrument`
named "Coverage" and a `Concept` named "Coverage" are two terms, and a linker that cannot tell
them apart is worse than no linker: the mislinked node stops being counted as unresolved, so
nothing downstream ever finds the error. Curated terms carry no node label and are visible to
every block, because a person authored them to name a thing.

**Candidate band.** Everything the upper threshold refused gets one embedding comparison
against the vocabulary, on-machine. Cosine in `[LOWER, 1.0)` is a candidate pair and goes to
§2. The band offers **one term per node** — the best-scoring one — because §2 prices the band
per pair and the reviewer's question is "does this node denote this term", which five terms
per node does not make five times more answerable.

**Lower threshold (auto-reject).** Below `LOWER`: no action. The node stays open and carries
`unresolved: true`. Unresolved is a *reported state*, never a guess.

    /opt/anaconda3/bin/python3 scripts/link_vocabulary.py --phase plan       # counts only
    /opt/anaconda3/bin/python3 scripts/link_vocabulary.py --phase band       # writes the band
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

from kg import vocab  # noqa: E402

TASK = "cc_tasks/2026-09-05_vocabulary_and_entity_linking.md"
BAND_OUT = REPO / "state" / "vocab_candidates_2026-09-05.jsonl"
PLAN_OUT = REPO / "state" / "vocab_linking_2026-09-05.json"

#: §1.3's pre-registered lower threshold. Not tuned after seeing the distribution — the RESULT
#: reports the distribution so a reader can see what 0.80 bought on this instrument.
LOWER = 0.80

#: The embedding instrument. `all-MiniLM-L6-v2`, L2-normalised, is what this repo already
#: uses: `scripts/t1_build_index.py` embedded 5,164 corpus chunks with it
#: (2026-08-29_corpus_t0_t1_substrate RESULT §1). Reusing it keeps ONE embedding space in the
#: repo. A stronger model (bge-large is also cached here) would shift the whole cosine
#: distribution and make the pre-registered 0.80 mean something different, which is a reason
#: to change instruments deliberately and never incidentally.
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

#: Labels linked. Same list the seed reads, and for the same reason: `Measure` and `Practice`
#: carry no `name` property at all, so there is nothing to link them on.
from seed_vocabulary import ENTITY_LABELS  # noqa: E402


# ---------------------------------------------------------------- upper threshold
def auto_link(nodes, terms: dict | None = None) -> dict:
    """{'linked': [(node_key, term_id)], 'unlinked': [node, …]} under the upper threshold."""
    terms = vocab.project() if terms is None else terms
    idx_by_label: dict = {}
    linked, unlinked = [], []
    for n in nodes:
        label = n.get("label")
        if label not in idx_by_label:
            idx_by_label[label] = vocab.alias_index(terms, node_label=label)
        tid = vocab.resolve(n.get("name"), index=idx_by_label[label])
        if tid:
            linked.append((n["key"], tid))
        else:
            unlinked.append(n)
    return {"linked": linked, "unlinked": unlinked}


# ---------------------------------------------------------------- band / lower threshold
def split_band(unlinked, best: dict) -> tuple:
    """Split the unlinked nodes on `LOWER`. `best` is {node_key: (term_id, cosine)}.

    Half-open on both ends: a cosine of exactly `LOWER` is IN the band (it was not
    auto-rejected), and 1.0 cannot occur because an identical normalised name would have
    auto-linked. Stated here because an off-by-one at a pre-registered threshold silently
    moves a registered count.
    """
    band, rejected = [], []
    for n in unlinked:
        hit = best.get(n["key"])
        if hit and hit[1] >= LOWER:
            band.append({**n, "term_id": hit[0], "cosine": float(hit[1])})
        else:
            rejected.append({**n, "unresolved": True,
                             "best_cosine": float(hit[1]) if hit else None,
                             "best_term_id": hit[0] if hit else None})
    return band, rejected


# ---------------------------------------------------------------- graph read + embedding
def read_nodes(session) -> list:
    out = []
    for label in ENTITY_LABELS:
        out += [dict(r, label=label) for r in session.run(
            f"MATCH (n:{label}) RETURN n.key AS key, n.name AS name, n.doc_id AS doc_id, "
            f"n.grounding_span AS span").data()]
    return out


def best_terms(unlinked, terms: dict) -> dict:
    """One best term per unlinked node, blocked by label, by cosine over local embeddings."""
    import numpy as np
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(EMBED_MODEL)
    active = {tid: t for tid, t in terms.items() if t["state"] == "active"}
    tids = sorted(active)
    # A term is represented by its preferred label and its scope note, which is what a
    # cataloguer reads to decide. Label alone would make the comparison a fuzzy string match
    # with extra steps.
    tvec = model.encode([f"{active[t]['pref_label']}. {active[t]['scope_note'][:400]}"
                         for t in tids], batch_size=128, normalize_embeddings=True,
                        show_progress_bar=False)
    # Which term rows each block may see.
    allowed = {}
    for label in {n["label"] for n in unlinked}:
        allowed[label] = np.array(
            [i for i, t in enumerate(tids)
             if not active[t].get("node_labels") or label in active[t]["node_labels"]])
    out: dict = {}
    for label in sorted(allowed):
        rows = [n for n in unlinked if n["label"] == label]
        cols = allowed[label]
        if not len(rows) or not len(cols):
            continue
        nvec = model.encode([f"{n.get('name') or ''}. {(n.get('span') or '')[:400]}"
                             for n in rows], batch_size=128, normalize_embeddings=True,
                            show_progress_bar=False)
        sim = nvec @ tvec[cols].T
        arg = sim.argmax(axis=1)
        for i, n in enumerate(rows):
            out[n["key"]] = (tids[int(cols[int(arg[i])])], float(sim[i, int(arg[i])]))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phase", choices=("plan", "band"), default="plan")
    a = ap.parse_args(argv)

    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    driver = get_neo4j_driver(cfg)
    try:
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            nodes = read_nodes(s)
    finally:
        driver.close()

    terms = vocab.project()
    res = auto_link(nodes, terms)
    by_label = collections.Counter(n["label"] for n in nodes)
    linked_by_label = collections.Counter(
        dict((n["key"], n["label"]) for n in nodes)[k] for k, _ in res["linked"])
    summary = {
        "task": TASK, "vocabulary_epoch": vocab.epoch(),
        "active_terms": sum(1 for t in terms.values() if t["state"] == "active"),
        "nodes": len(nodes), "nodes_by_label": dict(by_label),
        "auto_linked": len(res["linked"]), "auto_linked_by_label": dict(linked_by_label),
        "unlinked": len(res["unlinked"]),
        "distinct_terms_linked": len({t for _, t in res["linked"]}),
        "lower_threshold": LOWER, "embed_model": EMBED_MODEL,
    }
    if a.phase == "plan":
        print(json.dumps(summary, indent=1))
        return 0

    best = best_terms(res["unlinked"], terms)
    band, rejected = split_band(res["unlinked"], best)
    hist = collections.Counter(round(c, 1) for _, c in best.values())
    summary.update({
        "candidate_pairs": len(band), "auto_rejected": len(rejected),
        "cosine_histogram": {str(k): v for k, v in sorted(hist.items())},
        "band_by_label": dict(collections.Counter(p["label"] for p in band)),
    })
    BAND_OUT.write_text("".join(json.dumps({
        "node_key": p["key"], "label": p["label"], "name": p.get("name"),
        "doc_id": p.get("doc_id"), "span": (p.get("span") or "")[:800],
        "term_id": p["term_id"], "term_label": terms[p["term_id"]]["pref_label"],
        "term_scope_note": terms[p["term_id"]]["scope_note"][:600],
        "cosine": round(p["cosine"], 6)}, ensure_ascii=False) + "\n" for p in band),
        encoding="utf-8")
    PLAN_OUT.write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    print(f"-> {BAND_OUT.relative_to(REPO)}  {PLAN_OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
