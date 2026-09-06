#!/usr/bin/env python3
"""Register the alias pass, the judged homograph pass, the regold allocation and the bare-span
count as named Results. **Zero model spend.**

Task `cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md` §1.3, §2.1, §2.3, §3, §4. DD-040:
every figure quoted resolves to a Result, and each number here is read back off an artifact on
disk rather than recomputed.

    /opt/anaconda3/bin/python3 scripts/register_epoch2_results.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TASK = "cc_tasks/2026-09-06_aliases_homograph_judge_epoch2.md"

ALIAS = REPO / "state" / "alias_generation_2026-09-06.json"
POP = REPO / "state" / "homograph_population_2026-09-06.json"
DEC = REPO / "assessment" / "results" / "homograph_decisions_2026-09-06_opus.jsonl"
ALLOC = REPO / "state" / "er_regold_allocation_2026-09-06.json"
BARE = REPO / "state" / "concept_bare_span_2026-09-06.json"

SCRIPT = {"alias": "generate_aliases", "judge": "homograph_judge",
          "alloc": "regold_allocation", "bare": "homograph_split"}
DATA = {"alias": "alias_generation_2026-09-06", "judge": "homograph_population_2026-09-06",
        "alloc": "er_regold_allocation_2026-09-06", "bare": "concept_bare_span_2026-09-06"}


def rows() -> list:
    al = json.loads(ALIAS.read_text(encoding="utf-8"))
    pop = json.loads(POP.read_text(encoding="utf-8"))
    dec = [json.loads(l) for l in DEC.read_text(encoding="utf-8").splitlines() if l.strip()]
    alloc = json.loads(ALLOC.read_text(encoding="utf-8"))
    bare = json.loads(BARE.read_text(encoding="utf-8"))
    c, ctrl = al["counts"], al["controls"]

    out = [
        ("alias_positive_control_failed", 0 if ctrl["positive_passed"] else 1, "alias",
         f"§1.2 GATE. 1 when fewer than 5 of the 6 stratum-D gold `same` pairs are joined by "
         f"the generated aliases. Measured {ctrl['positive_joined']} of 6 "
         f"({', '.join(ctrl['positive_missed_ids'])} all missed), so NOTHING was written to "
         f"the vocabulary log. The generators are not merely weak: four of the six produce no "
         f"candidate form AT ALL from §1.1's rule set, because the pairs are word reorderings "
         f"(`Agency inventory of AI use cases` / `AI use case inventory`, `Governance of "
         f"data` / `data governance`), a truncation (`subject protection`), and a "
         f"multi-token domain suffix (`robots.txt exclusion protocol`). The other two are "
         f"blocked by DUPLICATE TERMS in epoch 1, not by a missing generator."),
        ("alias_negative_control_violations", len(ctrl["negative_violations"]), "alias",
         f"§1.2 HARD STOP. Gold pairs the rater called `different` that the generated aliases "
         f"would have joined, over {ctrl['negative_pairs']} stratum-C and stratum-D pairs. "
         f"ZERO — the generators are safe, just insufficient. That asymmetry matters under "
         f"DD-045 §3: a false merge is the expensive error and none was proposed."),
        ("alias_refused_label_theft", c.get("refused_label_theft", 0), "alias",
         "Proposed aliases refused because the form is already claimed by a DIFFERENT term "
         "— the guard from 27b360f4 §1.2, applied unchanged. The term that owns a name is "
         "never overridden by another term's surface variant."),
        ("alias_refused_label_block", c.get("refused_label_block", 0), "alias",
         "Proposed aliases refused because the node's KG label is not among the term's "
         "`node_labels`: a Concept node does not alias onto a Standard term."),
        ("alias_refused_ambiguous_target", c.get("refused_ambiguous_target", 0), "alias",
         "Proposed aliases refused because the stripped form names more than one term; an "
         "ambiguous target resolves to neither, as everywhere else in this vocabulary."),
        ("vocab_auto_linked_after_aliases", al["auto_linked_after"], "alias",
         f"COUNTERFACTUAL, NOT A STATE OF THE GRAPH. Nodes that would auto-link if the "
         f"{al['proposals']} generated aliases were written, against "
         f"{al['auto_linked_before']} today — a delta of {al['auto_linked_delta']}. They were "
         f"NOT written: the §1.2 positive control failed. Registered because the size of the "
         f"forgone gain is the argument for fixing the generators rather than abandoning them."),
        ("vocab_residue_unresolved_after_aliases", al["residue_after"], "alias",
         f"COUNTERFACTUAL, as above: the residue would fall from {al['residue_before']} to "
         f"{al['residue_after']}. Nothing was written."),
        ("homograph_judge_population", pop["size"], "judge",
         f"§2.1: the {pop['band']} band terms plus the {pop['auto_keep_thin_arm']} auto_keep "
         f"terms with an arm holding fewer than three members. The task premise expects ~200 "
         f"and says report the exact number: 212. The premise's '61 of the 79 auto-keeps' is "
         f"61 of the 67 that reached auto-keep on the `s >= 0` limb, not of all 79; the "
         f"correct count over all auto_keeps is 73. Auto-split terms are excluded — the score "
         f"that produced them is retired for classification (DD-046)."),
        ("homograph_judge_positive_control_failed",
         0 if all(d["verdict"] == "distinct_senses" for d in dec
                  if d["term_id"] in ("air:concept/accessibility", "air:concept/ai-ready")) else 1,
         "judge",
         "§2.3 GATE. `air:concept/ai-ready` came back `distinct_senses` at confidence 0.78 "
         "and correctly identified the split — the organisational arm predicates the label of "
         "a PERSON (\"When does a user become 'AI-ready'?\") while the others predicate it of "
         "a data artifact. `air:concept/accessibility` came back `same_sense` at 0.72 and "
         "FAILED, for a cause the judge states itself: its organisational-maturity arm holds "
         "one node whose grounding span is the bare word, so the judge could only compare the "
         "two arms that carried evidence. The gold sample measured that same term as a live "
         "false merge. Nothing was written to the vocabulary log."),
        ("homograph_judge_terms_judged", len(dec), "judge",
         "Terms judged before the §2.3 gate fired and the paid pass was stopped: 10 "
         "calibration plus the second positive control. The remaining 202 were not judged, "
         "because a decision that cannot be written is a decision not worth 6.3M tokens."),
        ("concept_bare_span_count", bare["count"], "bare",
         f"Concept nodes whose `grounding_span` is identical to their `name` after case and "
         f"whitespace normalisation, out of {bare['total']}. A span that is the bare term "
         f"gives a judge, a rater or a reader nothing to resolve on: all three gold "
         f"`uncertain` verdicts were this class, and it is the direct cause of the §2.3 "
         f"control failure."),
        ("concept_bare_span_share", round(bare["count"] / bare["total"], 6), "bare",
         f"{bare['count']} of {bare['total']} Concept nodes. Within the §2.1 judged "
         f"population the effect is concentrated: {bare['population_terms_with_bare_only_arm']} "
         f"of 212 terms have at least one arm with no usable span, and "
         f"{bare['population_terms_with_at_most_one_evidenced_arm']} have at most ONE "
         f"evidenced arm, where a cross-arm distinction cannot be drawn on evidence at all."),
    ]
    for gen in ("schwartz_hearst", "determiner_strip", "version_strip",
                "generic_suffix_strip", "technical_specifications_variant"):
        out.append((f"alias_generated_{gen}", c.get(f"generated_{gen}", 0), "alias",
                    f"Aliases the `{gen}` generator proposed (not written — §1.2 gate failed)."))
    for r in alloc["strata"]:
        out.append((f"er_regold_n_stratum_{r['stratum']}", r["n_allocated"], "alloc",
                    f"Neyman (1934) allocation for the 200-pair regold, stratum "
                    f"{r['stratum']} ({r['description']}): N={r['N']}, p={r['p_used']} "
                    f"({r['errors_in_gold']} errors in {r['scored_in_gold']} gold pairs; "
                    f"p=0.5 where zero were observed, per §3), S={r['S']}, N*S={r['NS']}. "
                    f"Registered before epoch 2's numbers exist; the draw belongs to the next "
                    f"task, seed 20260906."))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    data = rows()
    if a.dry_run:
        for name, value, src, note in data:
            print(f"{name}\t{value}\t{note[:70]}")
        print(len(data), "Results")
        return 0
    ok = 0
    for name, value, src, note in data:
        r = subprocess.run(["seldon", "result", "register", "--value", str(value),
                            "--name", name, "--units", name,
                            "--description", f"{note} Derivation: scripts/{SCRIPT[src]}.py ({TASK}).",
                            "--script-name", SCRIPT[src], "--data-name", DATA[src]],
                           capture_output=True, text=True, cwd=REPO)
        ok += 1 if r.returncode == 0 else 0
        if r.returncode:
            print("FAILED:", name, r.stderr.strip()[-160:])
    print(f"registered {ok}/{len(data)} Results")
    return 0 if ok == len(data) else 1


if __name__ == "__main__":
    raise SystemExit(main())
