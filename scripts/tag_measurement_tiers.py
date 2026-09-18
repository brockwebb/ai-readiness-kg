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

**The 20 rows no rule reached are revisited by `cc_tasks/2026-09-17_unassigned_indicators.md`**
(`TABLE2`, `UNASSIGNED2`, `OPEN_TOOL_CANDIDATE` below). Its decisions extend rules 2 to 5 with
three tests, each of which can also FAIL and leave the row unassigned:

* **decision 1 (D).** The definition must carry a clause placing the act on the agency's side
  of publication — an act before the product goes live, or a fact held only in the agency's
  own records. The clause is quoted and checked against the definition like any other quote.
* **decision 2 (M, `structured_field`).** A corpus document must name the structured field, and a
  collector in `docs/design/scan_tool_map.md` §1 must already have an entry point that would
  read it. Both go on the node as `tier_field` and `tier_collector`, and `tier_note` says
  there is no rule in `rules.CURRENT` yet.
* **decision 3 (O, `open_tool`).** The tool's own documentation must be on disk in `corpus/`.
  Where it is not, the node keeps its reason and gains `open_tool_candidate`, which is a
  shopping list for a later ingest task and is NOT a tier.

**The shopping list is closed by `cc_tasks/2026-09-18_tool_docs_ingest.md`** (`TABLE3` below).
It fetched and admitted the two tool documents the list named — `oasdiff`'s README and the
Wayback CDX Server API's — and decision 2 of that task tiers A7, F2 and F3 O on a cited section
of each, dropping `open_tool_candidate` from all three.

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
TASK2 = "cc_tasks/2026-09-17_unassigned_indicators.md"
TASK3 = "cc_tasks/2026-09-18_tool_docs_ingest.md"
TASK4 = "cc_tasks/2026-09-18_dcat_field_rules.md"
SCRIPT = "tag_measurement_tiers"
RECORD = "framework/ai_readiness_framework.json"

TIERS = ("M", "O", "D")
BASES = ("harness_leg", "structured_field", "judged_reading", "open_tool", "evaluation",
         "declaration")
#: Which tier each basis may carry. `evaluation` and `judged_reading` are M because the
#: instruments are this project's (DN-005 ADDENDUM_01); a basis on the wrong tier is a typo.
#: `structured_field` is the sixth value, added by DN-005 ADDENDUM_02: a corpus document names
#: the field and an existing collector already fetches the surface that carries it, and NO rule
#: in `rules.CURRENT` reads it yet. It is not `harness_leg`, because ADDENDUM_01 defines that
#: value as "a rule in `rules.CURRENT` serves the indicator" and three gates outside this file
#: depend on it meaning exactly that — `tag_prescriptions.validate`, the two prescription-layer
#: tests, and the projection's `harness_leg_indicators_without_an_action` count.
BASIS_TIER = {"harness_leg": "M", "structured_field": "M", "judged_reading": "M",
              "evaluation": "M", "open_tool": "O", "declaration": "D"}

#: The tier properties this script owns, in the order they are written.
TIER_KEYS = ("measurement_tier", "measurement_basis", "tier_source", "tier_rule", "tier_note",
             "tier_field", "tier_collector", "tier_unassigned_reason", "open_tool_candidate")

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
    # Generation 11 (`cc_tasks/2026-09-18_dcat_field_rules.md`): four `structured_field` rows
    # that became rule 1 when their rules entered `rules.CURRENT`. What each rule leaves
    # unmeasured is printed on its every verdict as well as here.
    "B1": ("The rule is B1's DCAT half: every catalog record for the product links a data "
           "dictionary (`describedBy`). The schema.org `variableMeasured` half is not read yet "
           "(cc_tasks/2026-09-18_schema_field_rules.md), and the dictionary's contents and "
           "whether they are 'comprehensive' are not measured."),
    "B4": ("The rule measures the error-measure clause (`hasQualityMeasurement`) and the "
           "revisions-policy clause (`versionNotes` / `previousVersion` / "
           "`hasCurrentVersion`) on the product's catalog record. The suppression-rules clause "
           "has no field in any admitted document and is recorded as unmeasured."),
    "D3": ("The rule reads that the product's catalog record names a lineage (`wasGeneratedBy` "
           "or `wasDerivedFrom`, bare or `prov:`-prefixed); whether that lineage reaches from "
           "collection through processing to the product is not measured."),
    "G4": ("The rule measures the issuing-authority clause (`bureauCode` and `programCode`, "
           "well-formed) on the product's catalog record. The statutory-mandate and "
           "statistical-versus-administrative clauses have no field in any admitted document "
           "and are recorded as unmeasured."),
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


# ---------------------------------------------------------------------------------------
# `cc_tasks/2026-09-17_unassigned_indicators.md`: the 20 rows above, revisited.
# ---------------------------------------------------------------------------------------

#: Tool map §1 entry points, quoted so the source a node carries names the same string the
#: generated table does. A collector row that loses an entry point makes these stale, which is
#: what `tests/test_measurement_tiers.py::test_a_named_collector_is_a_collector_that_exists`
#: is for.
_STRUCTURED = "`structured_data.fetch` / `structured_data.store_evidence`"
_DCAT = "`dcat.fetch_catalog` / `dcat.store_evidence`"
_ROBOTS = "`robots.fetch` / `robots.store_evidence`"
_EXTRUCT = ("corpus/kernel/extruct-readme.md (doc_id `extruct-readme`): \"*extruct* is a "
            "library for extracting embedded metadata from HTML markup\", supporting "
            "\"embedded JSON-LD\" — the library the `structured_data` collector already runs")
_NO_RULE = "No rule in rules.CURRENT yet. "

#: Decisions 1 to 3, one entry per indicator they reach. Same shape as `TABLE`, plus
#: `rule_text` (this task's decision rather than the predecessor's) and, for decision 2,
#: `field` and `collector`, which go on the node.
TABLE2 = {
    # ---- decision 1: the definition places the act on the agency's side of publication ----
    "E2": dict(
        rule_text=f"{TASK2} decision 1", tier="D", basis="declaration",
        quote="pre-registered before results",
        source=("the definition places the act before publication: a threshold is "
                "pre-registered only if it existed BEFORE the results it judges, and the "
                "agency's own timestamps are the only record of that order"),
        note=("The published half — that thresholds are published at all, and that changes "
              "are versioned events — is readable from a served surface. The clause the "
              "indicator turns on is the order, which is not.")),
    "E7": dict(
        rule_text=f"{TASK2} decision 1", tier="D", basis="declaration",
        quote="mean-time-to-closure tracked",
        source=("the definition names a tracked internal metric: mean time to closure is "
                "measured over the agency's own ticket history, which no served surface "
                "carries"),
        note=("The 'Documented path ... with re-test' half would be readable if the agency "
              "published the path; the indicator's value turns on the tracked metric, which "
              "is held in the agency's records.")),
    "F1": dict(
        rule_text=f"{TASK2} decision 1", tier="D", basis="declaration",
        quote="before going live",
        source=("the definition places the act before publication: whether a release PASSED "
                "the suite before it went live happened on the agency's side of publication "
                "and leaves nothing on the served surface"),
        note=("The suite's own publication is observable — 'a published expectation suite' is "
              "a document a scan could fetch — and that is a different, narrower indicator "
              "than this one.")),
    "F5": dict(
        rule_text=f"{TASK2} decision 1", tier="D", basis="declaration",
        quote="AI-consumer regression run before promotion",
        source=("the definition places the act before publication: the regression runs "
                "against the staging surface before promotion, and only the agency can say "
                "that it ran"),
        note=("A canary or staging host may itself be fetchable where it is public; the act "
              "the definition names is the run before promotion, which is not.")),
    # ---- decision 2: a corpus document names the field, a tool map §1 collector reads it ----
    "B1": dict(
        rule_text=f"{TASK2} decision 2", tier="M", basis="structured_field",
        quote="variable-level metadata (labels, definitions, units, universes)",
        field="schema.org `variableMeasured` (as `PropertyValue`: `name`, `description`, "
              "`unitText`, `minValue`/`maxValue`); DCAT-US `describedBy`",
        collector=f"{_STRUCTURED}; {_DCAT}",
        source=("corpus/kernel/schema-org-dataset.md (doc_id `schema-org-dataset`), the "
                "`variableMeasured` row: \"The variableMeasured property can indicate "
                "(repeated as necessary) the variables that are measured in some dataset, "
                "either described as text or as pairs of identifier and description using "
                "PropertyValue\", and the worked Dataset example, whose `variableMeasured` "
                "entries carry `name`, `description` and `unitText`; "
                "corpus/kernel/dcat-us-1-1-schema.md (doc_id `dcat-us-1-1-schema`), "
                "`describedBy`: \"used to specify a data dictionary or schema that defines "
                f"fields or column headings in the dataset\"; {_EXTRUCT}"),
        note=(_NO_RULE + "`structured_data` already fetches and retains the whole JSON-LD "
              "block for A6 and A8; what is missing is a rule that reads `variableMeasured` "
              "out of it. 'Comprehensive' is a completeness judgement the field alone does "
              "not settle: a rule would have to pre-register its own coverage threshold, and "
              "none is pre-registered.")),
    "B2": dict(
        rule_text=f"{TASK2} decision 2", tier="M", basis="structured_field",
        quote="Concept/term definitions published, versioned, linked from variables",
        field="schema.org `DefinedTerm` with `termCode`, `inDefinedTermSet` and `description`",
        collector=_STRUCTURED,
        source=("corpus/kernel/schema-org-definedterm.md (doc_id `schema-org-definedterm`): "
                "\"Use the name property for the term being defined, use termCode if the term "
                "has an alpha-numeric code allocated, use description to provide the "
                "definition of the term\", with `inDefinedTermSet` \"A DefinedTermSet that "
                "contains this term\" and `termCode` \"A code that identifies this DefinedTerm "
                "within a DefinedTermSet\"; the link from variables is "
                "corpus/kernel/schema-org-dataset.md, whose `measurementTechnique` expects a "
                f"`DefinedTerm`; {_EXTRUCT}"),
        note=(_NO_RULE + "The 'versioned' clause has no field: no admitted document names a "
              "version property on `DefinedTerm` or `DefinedTermSet` (searched "
              "schema-org-definedterm, schema-org-dataset, w3c-dcat-3, dcat-us-3-dataset-"
              "schema). A rule would measure the published and linked clauses and record the "
              "versioned clause as unmeasured.")),
    "B4": dict(
        rule_text=f"{TASK2} decision 2", tier="M", basis="structured_field",
        quote="published as metadata, not prose",
        field="DCAT-US 3 `hasQualityMeasurement`; `versionNotes` / `previousVersion` / "
              "`hasCurrentVersion`",
        collector=_DCAT,
        source=("corpus/kernel/dcat-us-3-dataset-schema.md (doc_id `dcat-us-3-dataset-"
                "schema`), `hasQualityMeasurement`: \"List of quality measurements for the "
                "dataset (for example, completeness, accuracy, or timeliness) beyond spatial "
                "or temporal resolution\"; `versionNotes`: \"Notes describing how this version "
                "differs from earlier versions of the dataset\", beside `previousVersion` "
                "\"reference to the previous dataset version\""),
        note=(_NO_RULE + "The error-measure clause is `hasQualityMeasurement` and the "
              "revisions-policy clause is `versionNotes`/`previousVersion`. The "
              "suppression-rules clause has no field — the same failed search that leaves G5 "
              "unassigned — so a rule would record that clause as unmeasured.")),
    "B5": dict(
        rule_text=f"{TASK2} decision 2", tier="M", basis="structured_field",
        quote="Same concept ⇒ same identifier across products/vintages",
        field="schema.org `DefinedTerm.termCode` within `inDefinedTermSet`",
        collector=_STRUCTURED,
        source=("corpus/kernel/schema-org-definedterm.md (doc_id `schema-org-definedterm`): "
                "`termCode` is \"A code that identifies this DefinedTerm within a "
                "DefinedTermSet\" and `inDefinedTermSet` is \"A DefinedTermSet that contains "
                "this term\" — the identifier and the concept the definition compares"),
        note=(_NO_RULE + "It would be the first rule to compare two collected surfaces rather "
              "than judge one: the cross-product half is decidable inside a single cycle, "
              "which captures many products, and the cross-vintage half across two cycles on "
              f"the log. {TASK2} decision 5 left this undetermined; the document that names "
              "`termCode` settles the field and the collector, and the reading is in the "
              "RESULT for the operator to overturn.")),
    "D2": dict(
        rule_text=f"{TASK2} decision 2", tier="M", basis="structured_field",
        quote="Terms address model training/retrieval use explicitly",
        field="the `Content-Signal` directive in robots.txt, categories `ai-train` and "
              "`ai-input`",
        collector=_ROBOTS,
        source=("corpus/kernel/cloudflare-content-signals-policy.md (doc_id "
                "`cloudflare-content-signals-policy`): \"The Content-Signal directive works by "
                "signaling your preference of either allowing (yes) or disallowing (no) "
                "certain categories of AI actions\", where `ai-train` is \"Training or "
                "fine-tuning AI models\" and `ai-input` is \"Inputting content into one or "
                "more AI models (e.g., retrieval augmented generation, grounding, or other "
                "real-time taking of content for generative AI search answers)\", carried as "
                "\"Content-Signal: ai-train=no, search=yes, ai-input=no\""),
        note=(_NO_RULE + "`ai-train` and `ai-input` are the two uses the definition names — "
              "training and retrieval — and the file that carries them is already fetched and "
              "retained whole for A4, A5, A11-declared and A12. The prose terms-of-use half "
              "stays a judged reading; this assignment covers the machine-readable half. The "
              "Content Signals page's own warning that the directives are preferences and not "
              "enforcement is the A11 declared-versus-enforced split, not a bar to reading the "
              "declaration.")),
    "D3": dict(
        rule_text=f"{TASK2} decision 2", tier="M", basis="structured_field",
        quote="Source lineage published (collection → processing → product)",
        field="DCAT-US 3 `wasGeneratedBy` and `qualifiedAttribution`; DCAT-3 "
              "`prov:wasGeneratedBy` / `prov:wasDerivedFrom`",
        collector=f"{_DCAT}; {_STRUCTURED}",
        source=("corpus/kernel/dcat-us-3-dataset-schema.md (doc_id `dcat-us-3-dataset-"
                "schema`), `wasGeneratedBy`: \"List of activities that generated, or provide "
                "the business context for the creation of the dataset\", beside "
                "`qualifiedAttribution` \"List of agents with specific responsibilities for "
                "the dataset\"; corpus/kernel/w3c-dcat-3.md (doc_id `w3c-dcat-3`) carries the "
                "same property as `prov:wasGeneratedBy` and names `prov:wasDerivedFrom`; the "
                "ontology behind both is on disk at corpus/crosswalk/w3c-prov-o-ontology.html "
                "(doc_id `w3c-prov-o-ontology`)"),
        note=(_NO_RULE + "The node's `gap` cell says no PROV-O or W3C-PROV document is "
              "admitted and that the skeleton's PROV-aligned standards nodes did not resolve. "
              "That is stale: `w3c-prov-o-ontology` and `w3c-prov-dm-data-model` are both "
              "`included` and `verified` in corpus/manifest.json. The gap cell belongs to the "
              "evidence layer and is left as written; the staleness is reported in the "
              "RESULT.")),
    "G4": dict(
        rule_text=f"{TASK2} decision 2", tier="M", basis="structured_field",
        quote="carried as structured metadata",
        field="DCAT-US 1.1 `bureauCode` and `programCode`, beside `publisher`",
        collector=_DCAT,
        source=("corpus/kernel/dcat-us-1-1-schema.md (doc_id `dcat-us-1-1-schema`), "
                "`bureauCode`, whose example is \"The Office of the Solicitor (86) at the "
                "Department of the Interior (010) would be: {\\\"bureauCode\\\":[\\\"010:86\\\"]}\", "
                "and `programCode`: \"Federal agencies, list the primary program related to "
                "this data asset, from the Federal Program Inventory\""),
        note=(_NO_RULE + "`bureauCode`, `programCode` and `publisher` carry the issuing "
              "authority. No admitted document names a field for the statutory mandate or for "
              "the statistical-versus-administrative distinction (searched dcat-us-1-1-schema, "
              "dcat-us-3-dataset-schema, w3c-dcat-3, schema-org-dataset, "
              "ddi-codebook-specification), so a rule would measure the authority clause and "
              "record the other two as unmeasured.")),
    # ---- decision 3: the tool's documentation is on disk ----
    "C5": dict(
        rule_text=f"{TASK2} decision 3", tier="O", basis="open_tool",
        quote="Product scored against published AI-data-readiness metrics",
        source=("corpus/pilot/aidrin-hiniduma-2024.pdf (doc_id `aidrin-hiniduma-2024`): "
                "\"AIDRIN offers a PyPI (Python Package Index) package [1] to users who are "
                "proficient in Python\" and \"Users can install the AIDRIN PyPI package via "
                "the command line and use it for data readiness assessment\", with reference "
                "[1] giving the locator \"AIDRIn: AI Data Readiness Inspector. "
                "test.pypi.org/project/aidrin/0.5.4\"; the metrics it scores against are the "
                "paper's own published dimensions"),
        note=("The predecessor's reason said neither AIDRIN paper's text says where the tool "
              "is obtained. It does, in reference [1]. The index named is TestPyPI and not the "
              "production index, which is recorded here rather than smoothed over. No harness "
              "path runs it under this project's manners and evidence retention, which is "
              "what keeps this O rather than M (DN-005 §2.2).")),
}

#: Replacement reasons for the rows this task revisited and could NOT tier. Each says which
#: test failed and on what, so the next task starts from the failure and not from the guess.
UNASSIGNED2 = {
    "E1": (f"{TASK2} decision 1 finds no clause placing the act on the agency's side of "
           "publication. The act the definition names is 'reported separately from', which is "
           "a publication act, and the ordering constraint 'a product cannot pass validation "
           "while failing verification' is checkable from the two reports the first clause "
           "requires. What is missing is therefore an instrument that reads a published "
           "conformance report, not the agency's cooperation. Candidate: M, judged_reading; "
           "no such instrument exists and no rule or collector reaches a report."),
    "E3": (f"{TASK2} decision 1 finds no clause placing the act on the agency's side of "
           "publication. 'Eval sets and rubrics carry versions' is a property of a published "
           "artifact, and 'results never pooled across versions' is a property of published "
           "results. Its observability is one-sided: a results table that cites no instrument "
           "version fails visibly, while a pass cannot be confirmed without the agency's own "
           "records, and one-sided observability is not one of the three tiers. Candidate: D "
           "for the second clause. No admitted document names a version field for an eval set "
           "or a rubric."),
    "B6": (f"{TASK2} decision 4: the G1 precedent does not carry it. G1's act is a "
           "preservation score — a pinned consumer restates a captured surface and the "
           "restatement is scored for what it kept (DD-036 §2). B6 asks two different "
           "questions about the surface itself: whether the summary is plain language, a "
           "readability property of the text and not of a restatement, and whether it is "
           "current, a freshness comparison against the product's own modified date. Neither "
           "is a preservation score, so B6 needs a different instrument and stays unassigned. "
           "The 'current' half is the closer of the two to a structured-field test: DCAT-US 3 "
           "`modified` on the dataset against the summary page's own date."),
    "G3": (f"{TASK2} decision 5: a corpus document names the artifact the crosswalk would be, "
           "and no collector reads it. corpus/kernel/sdmx-3-0-section-1-framework.pdf (doc_id "
           "`sdmx-3-0-section-1-framework`) defines the Structure Map — \"Structure maps "
           "describes a mapping between data structure definitions or dataflows for the "
           "purpose of transforming a data set into a different structure\" — and the "
           "representation maps that map value and code lists. No collector in "
           "docs/design/scan_tool_map.md §1 reads SDMX, so decision 2's second half fails and "
           "the tier stays undetermined. Candidate: M, harness_leg, once an SDMX collector "
           "exists; the stable-series-ID half would be DCAT-US 3 `previousVersion` and "
           "`hasCurrentVersion` through `dcat.fetch_catalog`."),
    "G5": (f"{TASK2} decision 2: no admitted document names a machine-readable suppression or "
           "disclosure field. The search that failed: `suppress`, `confidential` and "
           "`disclosure` across corpus/kernel, corpus/crosswalk and corpus/components — the "
           "only hit is bing-webmaster-guidelines, on search-result suppression — and across "
           "the SDMX 3.0 §1 and DDI codebook texts. The indicator's own source, "
           "`usafacts-ai-ready-data-guide`, asks publishers to \"Properly identify and "
           "document suppressed data (e.g., in very small counties) in plain language with "
           "unique identifiers\": plain language is the prose this indicator says it "
           "strengthens, and the field that would replace it does not exist in any admitted "
           "document. Stays unassigned."),
}

#: Decision 3's shopping list: a tool named by the row's own reason whose documentation is not
#: in `corpus/`. It is not a tier, and the node keeps its reason beside it.
_NOT_IN_CORPUS = "documentation not in corpus"
OPEN_TOOL_CANDIDATE = {
    "A7": f"Wayback CDX API (ResearchTask 43108db6) — {_NOT_IN_CORPUS}",
    "F2": f"oasdiff — {_NOT_IN_CORPUS}",
    "F3": f"Wayback CDX API (ResearchTask 43108db6) — {_NOT_IN_CORPUS}",
}


# ---------------------------------------------------------------------------------------
# `cc_tasks/2026-09-18_tool_docs_ingest.md`: the shopping list, fetched and admitted.
# ---------------------------------------------------------------------------------------

_CDX = ("corpus/tools/wayback-cdx-server/README.md (doc_id `wayback-cdx-server-api-readme`)")
_OASDIFF = "corpus/tools/oasdiff/README.md (doc_id `oasdiff-readme`)"
_NO_HARNESS = ("No harness path runs it under this project's manners, evidence retention and "
               "re-derivation discipline, which is what keeps this O rather than M "
               "(DN-005 §2.2). Nothing was measured when the tier was assigned. ")

#: Decision 2 of the ingest task: tier O on the strength of a cited section of the admitted
#: document, not on the candidate field. Same shape as `TABLE2`.
TABLE3 = {
    "A7": dict(
        rule_text=f"{TASK3} decision 2", tier="O", basis="open_tool",
        quote="Persistent URLs/DOIs for products and vintages",
        source=(f"{_CDX}, 'Basic Usage': \"the only required param for the CDX server is the "
                "**url** param\", returning one row per capture with the fields "
                "`[\"urlkey\",\"timestamp\",\"original\",\"mimetype\",\"statuscode\","
                "\"digest\",\"length\"]`; 'Filtering': \"Results may be filtered by "
                "timestamp using **from=** and **to=** params\" and \"**filter=**[!]*field*:"
                "*regex*\", for which \"It is often useful to filter by *mimetype* or "
                "*statuscode*\" — a product or vintage URL's capture history, with the status "
                "it answered at each capture, over a declared date range"),
        note=(_NO_HARNESS + "The index reaches the persistent-URL half of the definition. A "
              "DOI's persistence is its resolver's, not the archive's: a rule built on this "
              "document would record the DOI clause as unmeasured unless it also reads the "
              "resolver. The predecessor's M candidate (assessment/harness/probes/"
              "d1_stable_urls.py, not a rule in rules.CURRENT) stands beside this and is not "
              "displaced by it.")),
    "F2": dict(
        rule_text=f"{TASK3} decision 2", tier="O", basis="open_tool",
        quote="compatibility checked mechanically",
        source=(f"{_OASDIFF}: \"Command-line tool to compare and detect breaking changes in "
                "OpenAPI specs\"; 'Compare two specs': \"`breaking` — only the changes that "
                "break existing API clients\"; 'API lifecycle': \"Deprecate APIs and "
                "parameters\" and \"Version bumps — report a breaking change released "
                "without a major version bump\""),
        note=(_NO_HARNESS + "It reaches all three clauses only for an API that publishes an "
              "OpenAPI description; an API that publishes none is a finding about F2, not a "
              "comparison oasdiff can make. The deprecation-window and version-bump detail "
              "is in DEPRECATION.md and VERSIONING.md, which the README links and which were "
              "not fetched. Spec `spec:F2`'s note holds: two dated releases are needed, so a "
              "single-point scan cannot run it.")),
    "F3": dict(
        rule_text=f"{TASK3} decision 2", tier="O", basis="open_tool",
        quote="endpoints survive a new vintage",
        source=(f"{_CDX}, 'Url Match Scope': \"**matchType=prefix** will return results for "
                "all results under the path\", with the 'Filtering' section's **from=** / "
                "**to=** date range and the 'Collapsing' section's \"Only show unique urls in "
                "a prefix query\" "
                "(`collapse=urlkey&matchType=prefix`) — the set of endpoints captured under a "
                "product's path in the prior vintage's date range, to join against the "
                "current vintage's"),
        note=(_NO_HARNESS + "The index reaches the endpoints clause. Series identifiers and "
              "geography codes live in response bodies, which the index locates (timestamp, "
              "original URL, digest) and does not carry, so a rule built on this document "
              "alone would record those two clauses as unmeasured; the published-crosswalk "
              "alternative is a separate observation of the current surface. Spec "
              "`spec:F3`'s note holds: two vintages are needed.")),
}

TABLE.update(TABLE2)
for _code in TABLE2:
    UNASSIGNED.pop(_code)
UNASSIGNED.update(UNASSIGNED2)
TABLE.update(TABLE3)
for _code in TABLE3:
    UNASSIGNED.pop(_code)
    OPEN_TOOL_CANDIDATE.pop(_code)


# ---------------------------------------------------------------------------------------
# `cc_tasks/2026-09-18_dcat_field_rules.md`: four rows become rule 1, two take a tier.
# ---------------------------------------------------------------------------------------

#: Decision 2: B1, B4, D3 and G4 are served by a rule in `rules.CURRENT` (generation 11), so
#: rule 1 — computed from the registry — reaches them, and their `structured_field` entries
#: leave the table. Named rather than derived, so that a rule leaving `CURRENT` makes
#: `assignments` refuse (the row would be reached by nothing) instead of silently re-basing.
RULE1_FROM_TABLE2 = ("B1", "B4", "D3", "G4")

_E_SOURCE = ("cc_tasks/2026-09-17_unassigned_indicators_RESULT.md §0 (the row's decision 1 "
             "reading: the act is a publication act and the artifact a published report); "
             f"{TASK4} decision 5")
_E_NOTE = "no instrument exists; the reading is of a published report, not a served surface"

#: Decision 5: the Desktop's naming decision for the two rows decision 1 of the previous task
#: could not tier. `judged_reading` on tier M, no fourth tier.
TABLE4 = {
    "E1": dict(
        rule_text=f"{TASK4} decision 5", tier="M", basis="judged_reading",
        quote="reported separately from",
        source=_E_SOURCE,
        note=_E_NOTE),
    "E3": dict(
        rule_text=f"{TASK4} decision 5", tier="M", basis="judged_reading",
        quote="Eval sets and rubrics carry versions",
        source=_E_SOURCE,
        note=(_E_NOTE + "; observability is one-sided: a fail is visible, a pass needs the "
              "agency's records")),
}

for _code in RULE1_FROM_TABLE2:
    TABLE.pop(_code)
TABLE.update(TABLE4)
for _code in TABLE4:
    UNASSIGNED.pop(_code)

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
        if not (t.get("rule") or t.get("rule_text")):
            raise SystemExit(f"FATAL: {code}: no rule or rule_text names the decision")
        if bool(t.get("field")) != bool(t.get("collector")):
            raise SystemExit(f"FATAL: {code}: a field without a collector, or the reverse")
        if t["tier"] not in TIERS or BASIS_TIER.get(t["basis"]) != t["tier"]:
            raise SystemExit(f"FATAL: {code}: basis {t['basis']!r} on tier {t['tier']!r}")
        text = inds[code]["properties"].get("indicator") or ""
        quote = t.get("quote")
        if quote and quote not in text:
            raise SystemExit(f"FATAL: {code}: the quote is not in the definition: {quote!r}")
        src = t.get("source") or (f"definition of `ind:{code}` in {RECORD}: \"{quote}\"")
        if quote and t.get("source"):
            src += f"; definition of `ind:{code}`: \"{quote}\""
        rule_text = t.get("rule_text") or f"{TASK} decision 2 rule {t['rule']}"
        entry = {"measurement_tier": t["tier"], "measurement_basis": t["basis"],
                 "tier_source": src, "tier_rule": rule_text}
        if t.get("note"):
            entry["tier_note"] = t["note"]
        # Decision 2 of the second task: the field and the collector entry point that would
        # read it are ON THE NODE, not only inside the prose source, so a reader can join a
        # tier to the collector row without parsing a sentence.
        if t.get("field"):
            entry["tier_field"] = t["field"]
            entry["tier_collector"] = t["collector"]
        out[code] = entry
    for code, reason in UNASSIGNED.items():
        rule_text = (f"{TASK2} decision 2, no test reaches it" if code in UNASSIGNED2
                     else f"{TASK} decision 2, no rule reaches it")
        entry = {"tier_unassigned_reason": reason, "tier_rule": rule_text}
        if code in OPEN_TOOL_CANDIDATE:
            entry["open_tool_candidate"] = OPEN_TOOL_CANDIDATE[code]
        out[code] = entry
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
            "open_tool_candidates": sorted(c for c, a in assigned.items()
                                           if a.get("open_tool_candidate")),
            "indicators": len(assigned)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--task", default=TASK3,
                    help="the task that is WRITING, recorded on the `framework_writeback` event")
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
    # The event names the task that is WRITING, which since the third pass is TASK3; the
    # per-node `tier_rule` still names whichever task's decision reached that node.
    out = fw.save(g, script=SCRIPT, task=a.task, changes=changes, dry_run=a.dry_run)
    print(json.dumps({"counts": changes["counts"], "renamed": changes["renamed"],
                      "nodes_changed": len(changes["nodes"]),
                      "save": {k: v for k, v in out.items()
                               if k not in ("delta", "changes", "counts")}},
                     indent=1, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
