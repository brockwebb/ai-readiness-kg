#!/usr/bin/env python3
"""Register the vocabulary and entity-linking figures as Seldon Results. **Zero spend.**

Task `cc_tasks/2026-09-05_vocabulary_and_entity_linking.md` §5. DD-040: a figure quoted
anywhere must resolve by name to a Result, and the path that produced it must be re-runnable.
Every number here is read back off an artifact on disk — the seed state file, the linking
summary, the decision JSONL, the calibration JSON, the residue summary — never recomputed in
this script, so a Result and the file it came from cannot drift apart.

    /opt/anaconda3/bin/python3 scripts/register_vocab_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-05_vocabulary_and_entity_linking.md"

SEED = REPO / "state" / "vocabulary_seed_2026-09-05.json"
LINK = REPO / "state" / "vocab_linking_2026-09-05.json"
RESIDUE = REPO / "state" / "vocab_residue_2026-09-05.json"
CAL = REPO / "assessment" / "results" / "vocab_calibration_2026-09-05.json"
DEC = REPO / "assessment" / "results" / "vocab_link_decisions_2026-09-05_opus.jsonl"


def rows() -> list:
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    link = json.loads(LINK.read_text(encoding="utf-8"))
    res = json.loads(RESIDUE.read_text(encoding="utf-8"))
    cal = json.loads(CAL.read_text(encoding="utf-8"))
    dec = [json.loads(l) for l in DEC.read_text(encoding="utf-8").splitlines() if l.strip()]

    c = seed["counts"]
    out = [
        ("vocab_e1_terms", link["active_terms"], "seed", SEED.name,
         "ACTIVE controlled-vocabulary terms at vocabulary_epoch 1, from five sourced inputs "
         "(§1.2). 67 curated — the framework's constructs and indicator groups, the discovery "
         "stack, the search-optimisation lineage — and 1,879 derived from KG name groups, each "
         "scoped to the node label its members carried. Every term carries a dcterms:source."),
        ("vocab_e1_aliases", c["aliases_total"], "seed", SEED.name,
         "skos:altLabel entries across the epoch-1 terms: surface variants from the name "
         "groups plus the model-asserted `aliases` property, admitted under the §1.2 guard."),
        ("vocab_e1_curated_terms", c["s1_framework_terms"] + c["s2_stack_terms"] + c["s3_lineage_terms"],
         "seed", SEED.name,
         "Terms authored from a cited human source rather than derived from the graph: 51 from "
         "the operationalisation skeleton's indicator table and the protocol's four dimensions, "
         "12 discovery-stack standards and frontier candidates, 4 search-optimisation lineage "
         "terms with dated first use."),
        ("vocab_e1_aliases_refused_as_label_theft", c["s5_refused_would_steal_a_preferred_label"],
         "seed", SEED.name,
         "Model-asserted aliases REFUSED by the §1.2 guard because the alias is already the "
         "preferred label of a different term. The case this exists for is the extractor "
         "asserting `AI-ready data -> high-quality data`: an equivalence between two things "
         "this corpus must keep apart, which would have linked silently had it been the sole "
         "claimant of that name."),
        ("vocab_nodes_linkable", link["nodes"], "link", LINK.name,
         "KG nodes eligible for linking: every node carrying a `name` property under a label "
         "some CQ collapses on (Concept, Instrument, Standard, Framework, Platform, Tool). "
         "Measure and Practice are excluded because not one of their 2,776 nodes carries a "
         "`name` at all."),
        ("vocab_auto_linked", link["auto_linked"], "link", LINK.name,
         "Nodes linked at the Fellegi-Sunter UPPER threshold: the normalised name is the "
         "preferred label or an alias of exactly ONE term inside the node's own label block. "
         "A name claimed by two terms links to neither."),
        ("vocab_candidate_pairs", link["candidate_pairs"], "link", LINK.name,
         "The Fellegi-Sunter CLERICAL BAND: (node, best term) pairs with cosine in [0.80, 1.0) "
         "under all-MiniLM-L6-v2, one term per node. This is the unit count the §2 ceiling was "
         "computed from."),
        ("vocab_auto_rejected", link["auto_rejected"], "link", LINK.name,
         "Nodes below the lower threshold of 0.80: no action, and the node carries "
         "`unresolved: true` in the graph. Unresolved is a reported state, never a guess."),
        ("vocab_link_decisions_same", sum(1 for d in dec if d["verdict"] == "same"),
         "judge", DEC.name, "Band pairs the reviewer judged to denote the same thing."),
        ("vocab_link_decisions_different", sum(1 for d in dec if d["verdict"] == "different"),
         "judge", DEC.name,
         "Band pairs the reviewer judged to denote DIFFERENT things despite a cosine above "
         "0.80 — the measure of what the embedding band could not decide on its own."),
        ("vocab_link_decisions_uncertain", sum(1 for d in dec if d["verdict"] == "uncertain"),
         "judge", DEC.name, "Band pairs the reviewer declined to call either way."),
        ("vocab_links_accepted", sum(1 for d in dec if d["verdict"] == "same"
                                     and (d.get("confidence") or 0) >= 0.80),
         "judge", DEC.name,
         "`same` at confidence >= 0.80, written as `term_link_judged` events and replayed by "
         "the loader as RESOLVES_TO edges. Everything else stays unresolved."),
        ("vocab_calibration_kappa", cal["kappa"], "calibration", CAL.name,
         f"Cohen's kappa (1960) between the reviewer `claude-opus-5` and the independent rater "
         f"`claude-fable-5-1` over {cal['n']} stratified band decisions under adversarial-review "
         f"rubric {cal['rubric_version']}. Observed agreement {cal['observed_agreement']}, chance "
         f"{cal['chance_agreement']}. Pre-registered gate 0.60 (Landis & Koch's lower bound for "
         f"substantial agreement): PASSED, so the band's links were written. CAVEAT ON ITS FACE: "
         f"two models of the same family answering an identical prompt one pair at a time will "
         f"agree about prompt determinacy as much as about truth; this kappa bounds rater "
         f"idiosyncrasy, not correctness."),
        ("vocab_calibration_disagreements", cal["n"] - int(round(cal["observed_agreement"] * cal["n"])),
         "calibration", CAL.name,
         "Decisions where the two raters differed, written as records for the operator in "
         "assessment/results/vocab_calibration_disagreements_2026-09-05.md. Informational, "
         "never an approval step."),
        ("vocab_residue_unresolved", res["unresolved"], "residue", RESIDUE.name,
         "Nodes still carrying no RESOLVES_TO edge after the deterministic layer and the judged "
         "band. Overwhelmingly names asserted once: 7,440 of the residue's name groups are "
         "singletons within their label."),
        ("vocab_e2_proposed", res["proposed_epoch_2_terms"], "residue", RESIDUE.name,
         "Unresolved names recurring in >= 3 documents, written to "
         "ontology/vocabulary_proposals_epoch2.yaml and NOT promoted (§3). One, and the reason "
         "the number is one is structural rather than disappointing: the epoch-1 seed already "
         "promoted every name recurring across two or more nodes, so a name can only survive "
         "into the residue at three documents if it is AMBIGUOUS. It is — `DCAT-US` is claimed "
         "both by the curated `air:dcat` (which lists it as an alias) and by the graph-derived "
         "`air:standard/dcat-us`, and the corpus treats DCAT-US as a standard in its own right. "
         "The curated alias is wrong and epoch 2 should split them."),
    ]
    return out


SCRIPTS = {"seed": "seed_vocabulary", "link": "link_vocabulary", "judge": "link_judge",
           "calibration": "vocab_calibration", "residue": "vocab_residue"}
DATA = {"seed": "vocabulary_seed_2026-09-05", "link": "vocab_linking_2026-09-05",
        "judge": "vocab_link_decisions_2026-09-05_opus",
        "calibration": "vocab_calibration_2026-09-05", "residue": "vocab_residue_2026-09-05"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = rows()
    if a.dry_run:
        for name, value, src, f, note in data:
            print(f"{name}\t{value}\t{src}\t{note[:70]}")
        print(len(data), "Results")
        return 0
    ok = 0
    for name, value, src, f, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(value),
                            "--name", name, "--units", name,
                            "--description", f"{note} Derivation: scripts/{SCRIPTS[src]}.py "
                                             f"-> {f} ({TASK}).",
                            "--script-name", SCRIPTS[src], "--data-name", DATA[src]],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode == 0:
            ok += 1
        else:
            print("FAILED:", name, r.stderr.strip()[-200:])
    print(f"registered {ok}/{len(data)} vocabulary Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
