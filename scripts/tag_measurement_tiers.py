#!/usr/bin/env python3
"""Tag every framework indicator with a measurement tier, sourced. **Zero spend, no network.**

`cc_tasks/2026-09-17_measurement_tiers.md` decisions 1 and 2, under DN-005 §2.2 and §4 item 2.

Three properties on every indicator the task's rules reach, written through
`framework_writeback.save` (the single writer):

* `measurement_tier` — **M** measured by this project's instruments, **O** measurable with open
  tools this project runs but does not own, **D** declared: only the agency can say
  (DN-005 §2.2, read as DN-005 ADDENDUM_01 records it).
* `measurement_basis` — the kind of act: `harness_leg`, `judged_reading`, `open_tool`,
  `evaluation`, `declaration`.
* `tier_source` — the locator the assignment rests on. `tier_rule` names which of decision 2's
  rules reached it, and `tier_note` carries anything a reader of the source alone would miss.

**An indicator the rules do not reach gets no tier.** It carries `tier_unassigned_reason`
instead, naming why no rule reached it and which tier its evidence points at, so the next task
starts from the reason rather than from a default. A tier is not defaulted: the tool map's
`scan-observable` verdict on 22 indicators was a keyword default, and this is the record that
replaces it (`scripts/scan_tool_map.py` now derives its verdict from these properties).

**Rule 1 is computed, not listed.** An indicator a rule in `rules.CURRENT` serves is M,
`harness_leg`, and the set is read from the registry at run time. Rules 2 to 5 are the table
below; each entry that quotes the definition is checked to be a verbatim substring of the
indicator's own text, so a quote cannot drift from the record it quotes.

**G1-D's `measurement_tier: product` moves to `measurement_level`.** It was the first
`measurement_tier` value in the record (DD-066 §6) and it names the surface level the construct
is measurable on (product against host), not who can measure it. DD-066 §6 says the tiering
task "may rename the field, but it does not remove this one": the value and its source move
verbatim, and `measurement_tier` takes the DN-005 §2.2 meaning DN-005 §4 item 2 assigns it.

    /opt/anaconda3/bin/python3 scripts/tag_measurement_tiers.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

TASK = "cc_tasks/2026-09-17_measurement_tiers.md"
SCRIPT = "tag_measurement_tiers"
RECORD = "framework/ai_readiness_framework.json"

TIERS = ("M", "O", "D")
BASES = ("harness_leg", "judged_reading", "open_tool", "evaluation", "declaration")
#: Which tier each basis may carry. `evaluation` and `judged_reading` are M because the
#: instruments are this project's (DN-005 ADDENDUM_01); a basis on the wrong tier is a typo.
BASIS_TIER = {"harness_leg": "M", "judged_reading": "M", "evaluation": "M",
              "open_tool": "O", "declaration": "D"}

#: The tier properties this script owns, in the order they are written.
TIER_KEYS = ("measurement_tier", "measurement_basis", "tier_source", "tier_rule", "tier_note",
             "tier_unassigned_reason")

#: The tool map as it stood before this task regenerated it: the commit its §2 verdicts are
#: cited at. Those verdicts are keyword defaults; rules 2 and 4 use them only after checking
#: them against the definition text.
TOOL_MAP_AT = "docs/design/scan_tool_map.md §2 at commit 52af6c7"
G1_INSTRUMENT = ("the G1 instrument: DD-036 (docs/design_decisions.md), "
                 "assessment/harness/probes/g1_preservation.py, frozen at v2")

#: Rule 1 notes: what the rule does NOT cover, where a reader of `rules.CURRENT` alone would
#: take the indicator for fully measured.
RULE1_NOTES = {
    "A11": ("The rule measures the DECLARED layer only (leg `A11-declared`). The enforced and "
            "observed layers need edge or WAF logs and crawler request logs, which spec "
            "`spec:A11-declared` places at `agency_instrumented`."),
    "A12": ("A CANDIDATE indicator (DD-054): its rule runs and enters no framework numerator "
            "until the operator adopts it."),
    "E5": ("The rule judges this instrument's own cycle (its control fixtures), not a "
           "publisher's; `not_measured_reason` on this node says why that is not `measured`."),
    "G1-D": ("A deterministic structured-field rule (`RULE-G1-D-v1`, the frozen `g1_declared` "
             "probe, DD-066 §7), not a judged reading: G1-O is the leg the G1 instrument "
             "judges. Measured on product surfaces only (`measurement_level`)."),
}

#: Rules 2 to 5, one entry per indicator they reach. `quote` is a verbatim substring of the
#: indicator's text and is checked; `source` is the locator the assignment rests on.
TABLE = {
    # ---- rule 2: the tool map's `not web-observable`, confirmed against the definition ----
    "E4": dict(
        rule=2, tier="D", basis="declaration",
        quote="Public eval sets have a held-out rotation",
        source=(f"{TOOL_MAP_AT} (verdict `not web-observable`), confirmed against the "
                "definition: a held-out set is by construction not published, so whether "
                "a rotation exists is a fact only the agency holds")),
    # ---- rule 3: an on-disk source names an open tool that reaches the spec ----
    "F6": dict(
        rule=3, tier="O", basis="open_tool",
        quote="Signed releases / provenance attestations",
        source=("corpus/crosswalk/slsa-specification-v1-0.md (doc_id "
                "`slsa-specification-v1-0`), page 'Distributing provenance': \"SLSA requires "
                "the distribution and verification of provenance metadata in the form of SLSA "
                "attestations\"; FAQ 'How does SLSA relate to in-toto?': the specification "
                "recommends in-toto attestations (https://github.com/in-toto/attestation) as "
                "the vehicle to express provenance"),
        note=("Verifying a published attestation against the artifact is the open-tool act. "
              "The skeleton's `tier: paid` is the PUBLISHER's cost of signing, a different "
              "axis. Rule 3 is read with decision 1's source list, which names 'a tool's "
              "documentation on disk'; the tool map §3 and the open-tool record name no tool "
              "for F6.")),
    # ---- rule 4: the tool map's `content-evaluation`, confirmed against the definition ----
    "G6": dict(
        rule=4, tier="M", basis="judged_reading",
        quote=("The consumer-side test: an AI system asked to compare values across a break "
               "must surface the break"),
        source=(f"{TOOL_MAP_AT} (verdict `content-evaluation`), confirmed against the "
                f"definition; instrument: {G1_INSTRUMENT}"),
        note=("The consumer-side half is a G1-style preservation test (does the restatement "
              "keep the qualifier); the declared half, the versioned epoch carried as "
              "metadata, is a structured-field test no rule makes yet.")),
    # ---- rule 5: the definition names a benchmark, an eval set, entailment, or what a
    #      generative system does ----
    "G1-O": dict(
        rule=5, tier="M", basis="judged_reading",
        quote="when the pinned consumer restates that same captured surface",
        source=(f"DD-036 §2 (docs/design_decisions.md): G1-O is the v2 EVAL; spec `spec:G1-O` "
                f"names its collector; instrument: {G1_INSTRUMENT}"),
        note=("Reached by rule 5, and its basis is `judged_reading` rather than `evaluation` "
              "because the instrument exists: it is the one rule 4 cites.")),
    "C1": dict(
        rule=5, tier="M", basis="evaluation",
        quote=("Benchmark question set per product; answer accuracy of a retrieval-paired "
               "model vs published values"),
        note="No such instrument exists yet."),
    "C2": dict(
        rule=5, tier="M", basis="evaluation",
        quote=("Entailment-judged: do model statements about the product entail from product "
               "text?"),
        note=("The definition names the probe protocol, 're-aimed', as the instrument; it has "
              "not been re-aimed at a data product.")),
    "C3": dict(
        rule=5, tier="M", basis="evaluation",
        quote="does retrieval return the vintage asked for?",
        note="No such instrument exists yet."),
    "C4": dict(
        rule=5, tier="M", basis="evaluation",
        quote=("Generative engines citing the product cite the authoritative page (not "
               "aggregators)"),
        note=("No such instrument exists yet; spec `spec:C4-auto` records `collector: "
              "none_known` for the URL-resolution half.")),
    "E6": dict(
        rule=5, tier="M", basis="evaluation",
        quote=("Discrepancy taxonomy localizing failures to retrieval / vintage / metadata / "
               "model"),
        note=("The failures it localizes are an evaluation's outputs (retrieval and model "
              "stages), so it presupposes the C1 to C3 evaluations. No such instrument exists "
              "yet.")),
    "E8": dict(
        rule=5, tier="M", basis="evaluation",
        quote=("Versioned golden question/answer sets re-run on schedule against the product "
               "surface"),
        note="No such instrument exists yet."),
    "E9": dict(
        rule=5, tier="M", basis="evaluation",
        quote=("Standing adversarial bank: vintage traps, confusable series, unit traps, "
               "DP-noise misreads, suppression probes"),
        note="No such instrument exists yet."),
    "G2": dict(
        rule=5, tier="M", basis="evaluation",
        quote="EVAL: vintage disambiguation (ties C3)",
        note=(f"{TOOL_MAP_AT} said `content-evaluation`; rule 4's confirmation fails because "
              "the reading the definition asks for is C3's evaluation, not the G1 instrument, "
              "so rule 5 reaches it. The declared half (revision status machine-readable per "
              "value) is a structured-field test no rule makes yet. No such instrument exists "
              "yet.")),
}

#: Indicators no rule reaches. The reason says why and names the tier its evidence points at,
#: which is a candidate for the next task and NOT an assignment.
_KEYWORD_DEFAULT = (f"{TOOL_MAP_AT} gave the keyword default (`scan-observable`, \"`http` + "
                    "`structured_data` would serve it\"), which is not a derivation; ")
UNASSIGNED = {
    "A7": _KEYWORD_DEFAULT + (
        "no rule in rules.CURRENT serves it and no on-disk source names an open tool for it. "
        "Candidates: M through the June harness's assessment/harness/probes/d1_stable_urls.py "
        "(resolves a distribution URL; not a rule in rules.CURRENT), or O through the Wayback "
        "CDX API that ResearchTask 43108db6 names for robots.txt history, which would reach "
        "URL persistence across time."),
    "B1": _KEYWORD_DEFAULT + (
        "no rule serves it. Candidates: M through assessment/harness/probes/d3_schema.py (a "
        "`describedBy` data dictionary), or O through `extruct` reading schema.org "
        "`variableMeasured`; the tool map §3 names `extruct` for A6 only."),
    "B2": _KEYWORD_DEFAULT + (
        "no rule serves it. Candidate: O through `extruct` over schema.org `DefinedTerm` (the "
        "evidence cell cites `schema-org-definedterm`); the tool map §3 names `extruct` for A6 "
        "only, and 'versioned' is not a DefinedTerm property."),
    "B4": (f"{TOOL_MAP_AT} said `not web-observable`, and the definition does not confirm it: "
           "'published as metadata, not prose' is a property of a served surface, so rule 2 "
           "does not reach it and no other rule does. Candidate: M, the structured-field test "
           "G1-D already makes for the error-measure subset."),
    "B5": _KEYWORD_DEFAULT + (
        "the definition ('Same concept ⇒ same identifier across products/vintages') needs two "
        "products or vintages compared, and no rule, collector or on-disk tool does that. "
        "Candidate tier undetermined."),
    "B6": _KEYWORD_DEFAULT + (
        "presence is fetchable, but 'plain-language' and 'current' need a judged reading and "
        "no rule reaches it. Candidate: M, judged_reading."),
    "C5": ("The definition ('Product scored against published AI-data-readiness metrics') "
           "names published metrics, not a benchmark, an eval set, entailment or what a "
           "generative engine does, so rule 5 does not reach it; the tool map verdict was the "
           "keyword default. Candidate: O through AIDRIN (`aidrin-hiniduma-2024`, "
           "`aidrin-2-0-a-framework-to-assess-data-readiness-for-ai`), but neither paper's "
           "text on disk says where the tool is obtained, so rule 3 cannot cite it."),
    "D2": (f"{TOOL_MAP_AT} said `not web-observable`, and the definition does not confirm it: "
           "terms of use are published text. The tool map §3 response-header row names D2 as "
           "a consumer with 'no library needed', which is a harness path and not an open "
           "tool. Candidate: M, a terms or header leg, or a judged reading of the terms."),
    "D3": (f"{TOOL_MAP_AT} said `not web-observable`, and the definition does not confirm it: "
           "'Source lineage published' is a served surface. Candidate: M; "
           "assessment/harness/probes/d3_provenance.py reads source and date signals, which is "
           "less than lineage."),
    "E1": _KEYWORD_DEFAULT + (
        "the definition names an eval set, but its value is how results are REPORTED, not "
        "the output of running an evaluation, so rule 5 does not reach it. Candidate: D, or "
        "a judged reading of a published report."),
    "E2": _KEYWORD_DEFAULT + (
        "the definition names an eval, but its value is whether thresholds are published and "
        "pre-registered, not the output of running one, so rule 5 does not reach it. "
        "Candidate: D (pre-registration is verifiable only against the agency's own "
        "timestamps)."),
    "E3": _KEYWORD_DEFAULT + (
        "'Eval sets and rubrics carry versions' is a practice of whoever runs the evaluation, "
        "not the output of running one, so rule 5 does not reach it. Candidate: D."),
    "E7": (f"{TOOL_MAP_AT} said `content-evaluation` (the keyword was 'document'), and the "
           "definition does not confirm it: 'mean-time-to-closure tracked' is an agency "
           "process, not a reading of a served surface, and its value is not an evaluation's "
           "output. Candidate: D."),
    "F1": _KEYWORD_DEFAULT + (
        "'pass a published expectation suite ... before going live' happens before "
        "publication, on the agency's side. Candidate: D; the suite's publication alone would "
        "be observable."),
    "F2": _KEYWORD_DEFAULT + (
        "spec `spec:F2` records `collector: none_known`. Candidate: O through `oasdiff` (an "
        "open-source OpenAPI breaking-change detector), which would reach 'compatibility "
        "checked mechanically'; no on-disk source names it, so it is the next tool-map row "
        "rather than a citation."),
    "F3": _KEYWORD_DEFAULT + (
        "spec `spec:F3` records `collector: none_known`. Candidate: O through a web archive's "
        "CDX index (ResearchTask 43108db6 names the Wayback CDX API), which would supply the "
        "prior vintage's endpoints."),
    "F5": _KEYWORD_DEFAULT + (
        "'Canary/staging surface ... AI-consumer regression run before promotion' is on the "
        "agency's side of publication. Candidate: D."),
    "G3": (f"{TOOL_MAP_AT} said `content-evaluation`, and the definition does not confirm it: "
           "stable series IDs and machine-readable crosswalks are structured properties, not "
           "a judged reading. Spec `spec:G3` records `collector: none_known`. Candidate tier "
           "undetermined."),
    "G4": _KEYWORD_DEFAULT + (
        "'carried as structured metadata' is observable, but no rule serves it; "
        "assessment/harness/probes/d3_provenance.py reads the issuing-authority half "
        "(publisher, bureauCode) and nothing reads the statutory mandate. Candidate: M."),
    "G5": (f"{TOOL_MAP_AT} said `content-evaluation` (the keyword was 'document'), and the "
           "definition does not confirm it: 'documented machine-readably with unique "
           "identifiers' is a structured-field test, not a judged reading. Candidate: M, "
           "harness_leg."),
}


def rule1(record_codes: set) -> dict:
    """`{code: (leg, rule_id)}` for every indicator a rule in `rules.CURRENT` serves.

    The leg-to-indicator map is `report_traceability.FRAMEWORK_CODE`, read rather than
    re-derived: `A11-declared` is one half of `A11` and has no node of its own.
    """
    from scan.rules import CURRENT
    import report_traceability
    out = {}
    for leg, rule_id in sorted(CURRENT.items()):
        code = report_traceability.FRAMEWORK_CODE.get(leg, leg)
        if code not in record_codes:
            raise SystemExit(f"FATAL: rules.CURRENT serves leg {leg!r}, and the record has no "
                             f"indicator {code!r}")
        if code in out:
            raise SystemExit(f"FATAL: two CURRENT legs serve {code}: {out[code][0]}, {leg}")
        out[code] = (leg, rule_id)
    return out


def assignments(g: dict) -> dict:
    """`{code: {tier keys}}` for every indicator in the record. Refuses on any gap, overlap,
    unquoted quote or basis on the wrong tier: the table is checked before anything is
    written."""
    inds = {n["properties"]["code"]: n for n in g["nodes"]
            if "AssessmentIndicator" in n["labels"]}
    specs = {n["id"] for n in g["nodes"] if "MeasurementSpec" in n["labels"]}
    r1 = rule1(set(inds))
    groups = [set(r1), set(TABLE), set(UNASSIGNED)]
    for i, a in enumerate(groups):
        for b in groups[i + 1:]:
            if a & b:
                raise SystemExit(f"FATAL: {sorted(a & b)} reached twice")
    missing = set(inds) - set().union(*groups)
    extra = set().union(*groups) - set(inds)
    if missing or extra:
        raise SystemExit(f"FATAL: not in any group {sorted(missing)}; not in the record "
                         f"{sorted(extra)}")

    out = {}
    for code, (leg, rule_id) in r1.items():
        spec = f"spec:{leg}"
        src = (f"rules.CURRENT[{leg!r}] = {rule_id} (assessment/harness/scan/rules/"
               f"__init__.py)" + (f"; measurement spec `{spec}`" if spec in specs else ""))
        entry = {"measurement_tier": "M", "measurement_basis": "harness_leg",
                 "tier_source": src, "tier_rule": f"{TASK} decision 2 rule 1"}
        if code in RULE1_NOTES:
            entry["tier_note"] = RULE1_NOTES[code]
        out[code] = entry
    for code, t in TABLE.items():
        if t["tier"] not in TIERS or BASIS_TIER.get(t["basis"]) != t["tier"]:
            raise SystemExit(f"FATAL: {code}: basis {t['basis']!r} on tier {t['tier']!r}")
        text = inds[code]["properties"].get("indicator") or ""
        quote = t.get("quote")
        if quote and quote not in text:
            raise SystemExit(f"FATAL: {code}: the quote is not in the definition: {quote!r}")
        src = t.get("source") or (f"definition of `ind:{code}` in {RECORD}: \"{quote}\"")
        if quote and t.get("source"):
            src += f"; definition of `ind:{code}`: \"{quote}\""
        entry = {"measurement_tier": t["tier"], "measurement_basis": t["basis"],
                 "tier_source": src, "tier_rule": f"{TASK} decision 2 rule {t['rule']}"}
        if t.get("note"):
            entry["tier_note"] = t["note"]
        out[code] = entry
    for code, reason in UNASSIGNED.items():
        out[code] = {"tier_unassigned_reason": reason,
                     "tier_rule": f"{TASK} decision 2, no rule reaches it"}
    return out


def rename_level(props: dict) -> dict:
    """G1-D's surface level moves from `measurement_tier` to `measurement_level`, verbatim.
    Returns what moved; a node already renamed returns nothing."""
    moved = {}
    if props.get("measurement_tier") not in (None, *TIERS):
        moved["measurement_level"] = props.pop("measurement_tier")
        props["measurement_level"] = moved["measurement_level"]
        if "measurement_tier_source" in props:
            props["measurement_level_source"] = props.pop("measurement_tier_source")
            moved["measurement_level_source"] = props["measurement_level_source"]
    return moved


def counts(assigned: dict) -> dict:
    """Per tier, per basis, the estimate count and the unassigned list: what the RESULT and
    the coverage test both state."""
    from collections import Counter
    tiers = Counter(a["measurement_tier"] for a in assigned.values() if "measurement_tier" in a)
    bases = Counter(a["measurement_basis"] for a in assigned.values()
                    if "measurement_basis" in a)
    return {"per_tier": dict(sorted(tiers.items())), "per_basis": dict(sorted(bases.items())),
            "estimates": sum(1 for a in assigned.values()
                             if str(a.get("tier_source", "")).startswith("estimate")),
            "unassigned": sorted(c for c, a in assigned.items() if "measurement_tier" not in a),
            "indicators": len(assigned)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    import framework_writeback as fw
    g = fw.load()
    plan = assignments(g)
    changes = {"nodes": {}, "renamed": {}}
    for n in g["nodes"]:
        if "AssessmentIndicator" not in n["labels"]:
            continue
        p = n["properties"]
        before = {k: p.get(k) for k in ("measurement_tier", "measurement_tier_source",
                                        *TIER_KEYS[1:])}
        moved = rename_level(p)
        if moved:
            changes["renamed"][n["id"]] = {"measurement_tier": "measurement_level",
                                           "measurement_tier_source":
                                               "measurement_level_source"}
        for k in TIER_KEYS:
            p.pop(k, None)
        p.update(plan[p["code"]])
        after = {k: p.get(k) for k in before}
        if after != before:
            changes["nodes"][n["id"]] = {k: [before[k], after[k]] for k in before
                                         if before[k] != after[k]}
    changes["counts"] = counts(plan)
    out = fw.save(g, script=SCRIPT, task=TASK, changes=changes, dry_run=a.dry_run)
    print(json.dumps({"counts": changes["counts"], "renamed": changes["renamed"],
                      "nodes_changed": len(changes["nodes"]),
                      "save": {k: v for k, v in out.items()
                               if k not in ("delta", "changes", "counts")}},
                     indent=1, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
