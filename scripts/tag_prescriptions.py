#!/usr/bin/env python3
"""The prescription layer: `Action` nodes and `REMEDIATES` edges on the framework of record.

`cc_tasks/2026-09-17_prescription_layer.md` decisions 1 and 2, under DN-005 §2.3 and §4 item 3.
**Zero spend, no network.** Every technique source is a document already on disk under
`corpus/`; nothing is fetched and no model is called.

**The shape is borrowed, not invented.** DN-005 §2.3 names WCAG (success criterion ->
sufficient techniques -> common failures), CIS Benchmarks and OpenSSF Scorecard; the task file
adds Lighthouse and NIST SP 800-53. What they share is the invariant this module enforces:
*an action is bound to the check that would detect its absence, and the same check verifies its
completion.* Here that is `Action.verifies_by` -> a rule id in `rules.CURRENT`, and a
`REMEDIATES` edge whose `outcome` names the failing branch of that rule the action closes.
**No action without a verifying rule**, and no failing outcome without an action.

**One action per failing outcome.** A rule's `fail` branches are enumerated in `OUTCOMES` by a
VERBATIM fragment of the branch's own reason string, checked as a substring of the current rule
module's source before anything is written — so an outcome cannot drift from the branch it
names, and a rule that ships a new version with a reworded branch fails this script rather than
leaving a prescription pointing at a sentence nobody produces. Each outcome gets exactly one
`Action` and therefore exactly one `REMEDIATES` edge, which is also what keeps edge identity
(`from`, `type`, `to`) unique for `framework_writeback.delta`.

**Effort and cost are NOTIONAL relative bands, assigned by technique class.** No document on
disk states a level of effort or a cost for any of these techniques — the search that failed is
in `cc_tasks/2026-09-17_prescription_layer_RESULT.md` §0, and the closest sentence in the corpus
(W3C DWBP Best Practice 14, *"Data publishers must balance the effort required to make the data
available in many formats against the cost of doing so"*) says the two exist, not how large
either is. That is right for the SOURCE field and wrong for the band: an empty band reads as
"no answer", when the honest answer is a notional relative estimate the agency adjusts for its
own shop (`cc_tasks/2026-09-17_notional_bands.md`, from the operator's ruling of 2026-09-17).

So every action carries a `technique_class`, and the class fixes both bands through
`NOTIONAL_BANDS` — no band is authored per action, because a per-action figure is exactly the
absolute estimate the literature says is not worth producing (Kahneman and Tversky 1979 on the
planning fallacy; Flyvbjerg 2006 on reference-class forecasting as the corrective; Cohn 2005 on
relative sizing as the practice teams actually use — none of the three is on disk, and they are
cited by reference in DN-005 ADDENDUM_03). The `_source` fields say what the band IS rather
than pretending to a locator: `notional:technique_class:<class>, task
2026-09-17_notional_bands`. Every action also carries `band_note` verbatim, so the adjustment
instruction travels with the number and not only with the document that ruled on it. These
bands are refined by evidence from agencies that act on them, never by further estimation.

**Value is computed, never authored.** `value.bodies_failing_now` is the count of bodies on the
CYCLE OF RECORD (`docs/reports/publication.yaml:snapshot_cycle`) whose verdict on the verifying
rule's leg is `fail`, read from the published matrices. It is a per-LEG count, which is an
upper bound for any single action where a leg has more than one failing outcome; the node says
so in `value.bodies_failing_now_caveat` rather than letting a reader over-read it.

    /opt/anaconda3/bin/python3 scripts/tag_prescriptions.py [--dry-run] [--check]
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

#: `TASK` is who authored the ACTIONS, and it goes on every node as `authored_by`; the bands
#: were authored by a later task and say so in their own `_source` markers. `WRITEBACK_TASK` is
#: the task file whose execution produces the current bytes, and it is what the event carries.
TASK = "cc_tasks/2026-09-17_prescription_layer.md"
#: The task that added generation 11's outcomes and actions, named on each of those actions'
#: `authored_by` and on the write-back event it ran.
DCAT_TASK = "cc_tasks/2026-09-18_dcat_field_rules.md"
#: The task that added generation 12's outcomes and actions (B1's schema.org half, B2, B5, D2).
SD_TASK = "cc_tasks/2026-09-18_schema_field_rules.md"
_NO_RECORD_CLASS = ("the outcome covers a host serving no catalog, which needs a new file, and "
                    "a catalog without the product's record, which needs an edit; it is classed "
                    "by the larger act, which is the one most hosts on the cycle of record face")
WRITEBACK_TASK = "cc_tasks/2026-09-17_notional_bands.md"
SCRIPT = "tag_prescriptions"
RECORD = "framework/ai_readiness_framework.json"
PUBLICATION = "docs/reports/publication.yaml"

#: The two bands. Every legal value is listed whether or not a class reaches it: `tooling` is
#: reached by no class in this layer, and the RESULT says so rather than dropping the value.
EFFORT_BANDS = ("hours", "days", "weeks", "quarter")
COST_BANDS = ("none", "tooling", "staff_time", "procurement")

#: The technique classes (`cc_tasks/2026-09-17_notional_bands.md` decision 1), each with the
#: one-line definition DN-005 ADDENDUM_03 records. A class is assigned from the action's own
#: description and the kinds of its technique sources; where the choice is not obvious on the
#: description's face the action carries `technique_class_reason`, and the RESULT tables it so
#: a reader can dispute the row.
TECHNIQUE_CLASSES = {
    "edit_existing":
        "a field, a directive or an identifier added to something the host already serves",
    "publish_new_file":
        "a file the host does not serve yet — a sitemap, a data.json, an llms.txt, a changelog "
        "feed, a structured methodology, a bulk download",
    "change_server_behaviour":
        "how the server answers rather than what it holds — content negotiation, real 404s, "
        "server-side rendering, edge or bot-manager alignment",
    "expose_api":
        "an HTTP API and its OpenAPI description where none exists",
    "harness_side":
        "this instrument's own controls (E5), acted on by the operator of the harness",
}

#: class -> (effort_band, cost_band). RELATIVE within this layer and not absolute: the bands
#: order the actions against each other for a typical federal statistical publisher, which is
#: the whole of what they claim. Decision 2.
NOTIONAL_BANDS = {
    "edit_existing": ("hours", "none"),
    "publish_new_file": ("days", "staff_time"),
    "change_server_behaviour": ("weeks", "staff_time"),
    "expose_api": ("quarter", "procurement"),
    "harness_side": ("hours", "none"),
}

#: On every action, once, verbatim (decision 4). The adjustment instruction is a property of
#: the record and not only of a document, so a consumer that reads one action reads it too.
BAND_NOTE = ("Notional relative estimate for a typical federal statistical publisher. Adjust "
             "for your platform, staffing, skills and procurement path; the band orders "
             "actions against each other, it does not predict your calendar or budget.")

#: The marker that stands where a document locator would stand. Decision 3: every band source
#: is either a document locator or one of these, and none is missing its class.
NOTIONAL_PREFIX = "notional:technique_class:"
NOTIONAL_TASK = "task 2026-09-17_notional_bands"


def notional_source(cls: str) -> str:
    return f"{NOTIONAL_PREFIX}{cls}, {NOTIONAL_TASK}"

#: doc_id -> the path on disk. Every technique source is one of these; a source that is not a
#: file this repository holds cannot be quoted, and an unquotable source is not a locator.
SOURCES = {
    "w3c-dwbp-2017": "corpus/kernel/w3c-dwbp-2017.md",
    "rfc-9309-robots-exclusion-protocol": "corpus/kernel/rfc-9309-robots-exclusion-protocol.md",
    "google-robots-txt-intro": "corpus/kernel/google-robots-txt-intro.md",
    "openai-crawlers-bots": "corpus/kernel/openai-crawlers-bots.md",
    "sitemaps-protocol": "corpus/kernel/sitemaps-protocol.md",
    "llmstxt-proposal": "corpus/kernel/llmstxt-proposal.md",
    "schema-org-dataset": "corpus/kernel/schema-org-dataset.md",
    "schema-org-datadownload": "corpus/kernel/schema-org-datadownload.md",
    "schema-org-datacatalog": "corpus/kernel/schema-org-datacatalog.md",
    "schema-org-webapi": "corpus/kernel/schema-org-webapi.md",
    "openapi-specification-core": "corpus/kernel/openapi-specification-core.md",
    "dcat-us-1-1-schema": "corpus/kernel/dcat-us-1-1-schema.md",
    "dcat-us-3-dataset-schema": "corpus/kernel/dcat-us-3-dataset-schema.md",
    "w3c-json-ld-1-1-core": "corpus/kernel/w3c-json-ld-1-1-core.md",
    "lighthouse-docs-overview": "corpus/kernel/lighthouse-docs-overview.md",
    "schema-org-definedterm": "corpus/kernel/schema-org-definedterm.md",
    "cloudflare-content-signals-policy": "corpus/kernel/cloudflare-content-signals-policy.md",
    # Not a corpus document: the instrument's own parameters. E5's rule judges THIS cycle, so
    # its techniques are ours and its locator is the file that declares them.
    "internal:scan-params": "assessment/harness/scan/params.yaml",
}

# --------------------------------------------------------------- the failing outcomes (§2)
#
# leg -> {outcome name: a VERBATIM fragment of the branch's reason string}. The fragment must
# appear in the CURRENT rule module's source (`rules.CURRENT[leg]`), checked before any write.
# Fragments are kept short and inside a single source line, because a rule's reason strings are
# f-strings wrapped across lines and a fragment spanning the wrap is not verbatim anywhere.
OUTCOMES = {
    "A1": {
        "only_pdf": "only PDF served; first: ",
        "no_structured_link": "no probed link serves a structured content type",
    },
    "A2": {
        "served_but_not_an_api_description": "does not parse as an API ",
        "no_api_description": "no OpenAPI/JSON API description served at any probed path",
    },
    "A3": {
        "filtered_query_not_whole_product": "download link(s) are filtered queries, not ",
        "below_bulk_floor": "the largest linked download is below the ",
        "no_whole_product_download": "no whole-product download linked from the product page ",
    },
    "A4": {
        "no_robots_txt": "no robots.txt served; retrieval is permitted by default but nothing ",
        "robots_disallows_ai_crawlers": "robots.txt disallows the product path for ",
    },
    "A5": {
        "discovery_file_omits_product": "discovery files served (",
        "no_discovery_file": "no sitemap, llms.txt or well-known discovery file served",
    },
    "A6": {
        "markup_without_dataset_type": "but no Dataset/DataCatalog type",
        "no_structured_markup": "no JSON-LD, microdata or RDFa on the product page",
        "shapes_violation": "but violates the ",
    },
    "A8": {
        "last_modified_header_only": "only an HTTP Last-Modified header (",
        "no_declared_date": "no declared release or modification date on the surface",
        "no_latest_vintage_pointer": "latest-vintage pointer on its own host, which the indicator also ",
        "latest_vintage_pointer_unresolved": "latest-vintage pointer(s) resolves ",
    },
    "A9": {
        "machine_path_answers_html": "probed path(s) answer with HTML rather than a ",
        "no_machine_first_path": "probed machine-first paths is served",
    },
    "A10": {
        "soft_404": "soft-404: ",
        "deep_link_error_status": "the product deep link itself returns HTTP ",
        "client_rendered_shell": "client-rendered shell",
    },
    "A11-declared": {
        "nothing_declared": "nothing is DECLARED: no robots.txt is served, so the declared layer of ",
        "robots_disallows_ai_crawlers": "robots.txt DISALLOWS the product path for ",
        "meta_robots_contradicts_robots_txt": "directives restrict it (",
    },
    "A12": {
        "robots_itself_refused": "to /robots.txt itself for ",
        "nothing_declared_for_this_client": "so nothing is DECLARED for this client and there is no ",
        "declared_permits_enforced_refuses": "to that same path: the declared and ",
    },
    "B3": {
        "methodology_requires_js": "retrievable without JS: ",
        "methodology_pdf_only": "methodology is PDF-only: ",
        "no_methodology_link": "no link to a methodology document from the product surface",
        "no_structured_text_methodology":
            "no structured-text methodology document reachable from the product surface",
    },
    "D1": {
        "licence_is_free_text": "free text, not a recognised identifier",
        "no_licence": "no licence in the product page's markup, in an HTTP Link header, or at a ",
    },
    "D4": {
        "catalog_schema_violation": "but the catalog violates ",
        "product_absent_from_catalog": "but the product is not in it",
        "no_catalog": "no public data.json catalog served on this host",
    },
    "E5": {
        "zero_controls_fired": "a cycle with zero fired controls is INVALID: expected ",
        "control_verdict_not_as_expected": "control verdict(s) were not as expected: ",
        "controls_ran_after_surfaces": "the controls did not all run before the first real host: ",
    },
    "F4": {
        "changelog_entries_lack_revision_class": "entries carry a revision class (floor ",
        "changelog_not_machine_readable": "a changelog page is served at ",
        "no_changelog": "no changelog or release-notes endpoint served",
    },
    "G1-D": {
        "no_error_measure_field": "error-measure field tokens appears as a ",
    },
    # Generation 11 (`cc_tasks/2026-09-18_dcat_field_rules.md` decision 4). One shared outcome,
    # `no_product_record`, covers the three states in which the product has no catalog record
    # — no catalog, a catalog that does not parse, a catalog without the product — because the
    # act that closes all three is the same: publish the product's record carrying the field.
    "B1": {
        "no_product_record": "no catalog record for the product",
        "no_data_dictionary": "lack a data dictionary (",
        # Generation 12 (`cc_tasks/2026-09-18_schema_field_rules.md`): `RULE-B1-v2` joins the
        # schema.org half. A B1-v2 `fail` needs both halves to fail, so its reason carries a
        # DCAT fragment above AND this one, and both actions apply.
        "no_variable_measured": "no `variableMeasured`",
    },
    "B4": {
        "no_product_record": "no catalog record for the product",
        "quality_measurement_absent": "lack a quality measurement (",
        "revision_metadata_absent": "lack revision metadata (",
    },
    "D3": {
        "no_product_record": "no catalog record for the product",
        "no_lineage_field": "lack a lineage field (",
    },
    "G4": {
        "no_product_record": "no catalog record for the product",
        "authority_codes_absent": "lack a valid `bureauCode` and `programCode`",
    },
    # Generation 12 (`cc_tasks/2026-09-18_schema_field_rules.md`).
    "B2": {
        "no_defined_terms": "no schema.org `DefinedTerm` in the product page's markup",
        "terms_not_linked": "the terms are not linked from the ",
        "terms_incomplete": "lack a `termCode`, an `inDefinedTermSet` or a ",
    },
    "B5": {
        "no_term_codes": "no term codes: none of the body's ",
        "codes_without_set": "codes without a set: ",
        "codes_not_shared_across_products": "codes not shared across products: ",
    },
    "D2": {
        "no_content_signal": "declares no Content-Signal for ",
        "unknown_category": "a category or value the Content Signals Policy does not define",
    },
}

# ------------------------------------------------------------------- the actions (§2)
#
# One entry per (leg, outcome). `slug` becomes `act:<slug>`; `title` is imperative and one
# line; `description` is what a web or data team executes, written in terms of the surface the
# rule actually probes, because a prescription a reader cannot act on is a slogan.
#
# `sources` is a list of (doc_id, locator, verbatim quote). Every quote is checked as a
# substring of `SOURCES[doc_id]` before anything is written, so a technique source cannot drift
# from the document it cites — the same discipline `tag_measurement_tiers.py` applies to the
# definition quotes it rests a tier on.
#
# `cls` is the technique class, and it is REQUIRED: a class that could be defaulted would be a
# band that could be defaulted, which is the thing the empty band was protecting against.
# `class_reason` is written only where the class is not obvious on the description's face.
def _a(leg, outcome, slug, title, description, sources, cls, note=None,
       applies_to_publisher=True, applies_to_note=None, class_reason=None, task=None):
    # `task` names the task that AUTHORED this action when it is not `TASK`, so an action added
    # by a later task says so on the node rather than inheriting the layer's founding task.
    return {"leg": leg, "outcome": outcome, "slug": slug, "title": title,
            "description": description, "sources": sources, "technique_class": cls,
            "class_reason": class_reason, "note": note,
            "applies_to_publisher": applies_to_publisher, "applies_to_note": applies_to_note,
            "task": task}


# Quotes reused across several actions, named once so a re-quote cannot drift from its twin.
Q_BP12 = ("w3c-dwbp-2017", "Best Practice 12 'Possible Approach to Implementation'",
          "Make data available in a machine-readable standardized data format that is easily "
          "parseable including but not limited to CSV, XML, HDF5, JSON and RDF serialization "
          "syntaxes")
Q_BP14 = ("w3c-dwbp-2017", "Best Practice 14 'Possible Approach to Implementation'",
          "providing at least one alternative will greatly increase the usability of the data")
Q_BP19 = ("w3c-dwbp-2017", "Best Practice 19 'Possible Approach to Implementation'",
          "A possible approach to implementation is to configure the Web server to deal with "
          "content negotiation of the requested resource.")
Q_BP17 = ("w3c-dwbp-2017", "Best Practice 17 'Possible Approach to Implementation'",
          "preprocessing a copy of the data into a single file and making the data accessible "
          "for download from one URI")
Q_BP23 = ("w3c-dwbp-2017", "Best Practice 23 'Possible Approach to Implementation'",
          "If you use a data management platform, such as CKAN, you may be able to enable an "
          "existing API.")
Q_BP25 = ("w3c-dwbp-2017", "Best Practice 25 'Possible Approach to Implementation'",
          "A typical API reference provides a comprehensive list of the calls the API can "
          "handle, describing the purpose of each one")
Q_BP1 = ("w3c-dwbp-2017", "Best Practice 1 'Possible Approach to Implementation'",
         "machine-readable metadata may be provided in a serialization format such as Turtle "
         "and JSON, or it can be embedded in the HTML page using [HTML-RDFA] or [JSON-LD]")
Q_BP4 = ("w3c-dwbp-2017", "Best Practice 4 'Possible Approach to Implementation'",
         "Data license information can be available via a link to, or embedded copy of, a "
         "human-readable license agreement.")
Q_BP5 = ("w3c-dwbp-2017", "Best Practice 5 'Possible Approach to Implementation'",
         "The machine-readable version of the data provenance can be provided using an "
         "ontology recommended to describe provenance information, such as W3C's Provenance "
         "Ontology [PROV-O].")
Q_BP6 = ("w3c-dwbp-2017", "Best Practice 6 'Possible Approach to Implementation'",
         "The machine-readable version of the dataset quality metadata may be provided using "
         "the Data Quality Vocabulary developed by the DWBP working group [VOCAB-DQV].")
Q_BP7 = ("w3c-dwbp-2017", "Best Practice 7 'Possible Approach to Implementation'",
         "Include a unique version number or date as part of the metadata for the dataset.")
Q_BP7_LATEST = ("w3c-dwbp-2017", "Best Practice 7 'Possible Approach to Implementation'",
                "the URI used to request the latest version of the data should not change as "
                "the versions change, but it should be possible to request a specific version "
                "through the API")
Q_BP8 = ("w3c-dwbp-2017", "Best Practice 8 'Possible Approach to Implementation'",
         "Provide a list of published versions and a description for each version that "
         "explains how it differs from the previous version.")
Q_BP8_API = ("w3c-dwbp-2017", "Best Practice 8 'Possible Approach to Implementation'",
             "An API can expose a version history with a single dedicated URL that retrieves "
             "the latest version of the complete history.")
Q_BP9 = ("w3c-dwbp-2017", "Best Practice 9 'Possible Approach to Implementation'",
         "To be persistent, URIs must be designed as such.")
Q_BP11 = ("w3c-dwbp-2017", "Best Practice 11 'Possible Approach to Implementation'",
          "That identifier points to an immutable snapshot of the document on the day of its "
          "publication.")
Q_BP22 = ("w3c-dwbp-2017", "Best Practice 22 'Possible Approach to Implementation'",
          "appropriate HTTP status codes with customized human-readable messages can be used")
Q_BP27 = ("w3c-dwbp-2017", "Best Practice 27 'Possible Approach to Implementation'",
          "the server should be configured to respond with an HTTP Response code of 410 (Gone)")

Q_RFC_ALLOW = ("rfc-9309-robots-exclusion-protocol", "section 2.2.2 'The \"Allow\" and "
               "\"Disallow\" Lines'",
               "\"disallow\" rule are equivalent, then the \"allow\" rule SHOULD be used.")
Q_RFC_SELF = ("rfc-9309-robots-exclusion-protocol", "section 2.2.2 'The \"Allow\" and "
              "\"Disallow\" Lines'", "The /robots.txt URI is implicitly allowed.")
Q_RFC_UA = ("rfc-9309-robots-exclusion-protocol", "section 2.2.1 'The User-Agent Line'",
            "Crawlers set their own name, which is called a product token, to find")
Q_GOOG = ("google-robots-txt-intro", "'Introduction to robots.txt'",
          "A robots.txt file tells search engine crawlers which URLs the crawler can access "
          "on your site.")
Q_GOOG_NOINDEX = ("google-robots-txt-intro", "'Introduction to robots.txt'",
                  "it is not a mechanism for keeping a web page out of Google")
Q_OPENAI = ("openai-crawlers-bots", "'Overview of OpenAI crawlers'",
            "OpenAI uses OAI-SearchBot and GPTBot robots.txt tags to enable webmasters to "
            "manage how their sites and content work with AI.")
Q_OPENAI_IPS = ("openai-crawlers-bots", "'Overview of OpenAI crawlers', GPTBot row",
                "Published IP addresses: <https://openai.com/gptbot.json>")
Q_SITEMAP_LOC = ("sitemaps-protocol",
                 "'Specifying the Sitemap location in your robots.txt file'",
                 "You can specify the location of the Sitemap using a robots.txt file. To do "
                 "this, simply add the following line including the full URL to the sitemap:")
Q_SITEMAP_HOST = ("sitemaps-protocol", "'Sitemaps XML format'",
                  "Also, all URLs in a Sitemap must be from a single host")
Q_SITEMAP_FMT = ("sitemaps-protocol", "'Sitemaps XML format'",
                 "The Sitemap protocol format consists of XML tags.")
Q_LLMS = ("llmstxt-proposal", "'Proposal'",
          "We propose adding a `/llms.txt` markdown file to websites to provide LLM-friendly "
          "content.")
Q_LLMS_MD = ("llmstxt-proposal", "'Proposal'",
             "pages with information that agents might need provide a clean markdown version "
             "of those pages at the same URL as the original page")
Q_LLMS_LINK = ("llmstxt-proposal", "'Proposal'",
               "These links can be provided as HTML `<link>` elements, or as an HTTP `Link:` "
               "response header.")
Q_LLMS_JS = ("llmstxt-proposal", "'Background'",
             "An HTML page wraps its information in navigation, ads, and JavaScript, and "
             "converting it back into clean text is difficult and imprecise.")
Q_SCHEMA_VAR = ("schema-org-dataset", "property `variableMeasured`",
                "The variableMeasured property can indicate (repeated as necessary) the "
                "variables that are measured in some dataset, either described as text or as "
                "pairs of identifier and description using PropertyValue")
Q_SCHEMA_LIC = ("schema-org-dataset", "'Dataset' example, the `license` field",
                "\"license\": [ \"http://spdx.org/licenses/CC0-1.0\", "
                "\"https://creativecommons.org/publicdomain/zero/1.0\" ]")
Q_SCHEMA_DIST = ("schema-org-dataset", "'Dataset' example, the `distribution` field",
                 "\"distribution\": { \"@type\": \"DataDownload\", \"contentUrl\": "
                 "\"https://www.sample-data-repository.org/dataset/472032.tsv\", "
                 "\"encodingFormat\": \"text/tab-separated-values\" }")
Q_SCHEMA_DATE = ("schema-org-dataset", "'Dataset' example, the `dateModified` field",
                 "\"dateModified\":\"2019-06-12T14:44:15Z\"")
Q_SCHEMA_DL = ("schema-org-datadownload", "property `encodingFormat`",
               "Media type typically expressed using a MIME format")
Q_SCHEMA_CAT = ("schema-org-datacatalog", "property `dataset`",
                "A dataset contained in this catalog.")
Q_SCHEMA_API = ("schema-org-webapi", "property `documentation`",
                "Further documentation describing the Web API in more detail.")
Q_OAS = ("openapi-specification-core", "section 2 'Introduction'",
         "The OpenAPI Specification (OAS) defines a standard, language-agnostic interface to "
         "HTTP APIs which allows both humans and computers to discover and understand the "
         "capabilities of the service without access to source code, documentation, or "
         "through network traffic inspection.")
Q_OAS_TOOLS = ("openapi-specification-core", "section 2 'Introduction'",
               "An OpenAPI Description (OAD) can then be used by documentation generation "
               "tools to display the API")
Q_DCAT_CATALOG = ("dcat-us-1-1-schema", "'What to Document - Datasets and Web APIs'",
                  "The catalog file for each agency should list all of the agency’s "
                  "datasets that can be made public, regardless of whether they are "
                  "distributed by a file download or a Web API.")
Q_DCAT_ID = ("dcat-us-1-1-schema", "'Catalog' fields, Metadata Catalog ID",
             "This should be the URL of the data.json file itself")
Q_DCAT_CASE = ("dcat-us-1-1-schema", "'Metadata File Format - JSON'",
               "The Project Open Data schema is case sensitive.")
Q_DCAT_DIST = ("dcat-us-1-1-schema", "'Metadata File Format - JSON'",
               "When a record has an **accessURL** or **downloadURL** , they should be "
               "contained as objects within a **distribution**.")
Q_DCAT3 = ("dcat-us-3-dataset-schema", "'DCAT-US 3.0: Dataset'",
           "Information about a dataset, including identifiers, contacts, coverage, "
           "distributions, and related resources.")
# DCAT-US fields named by the generation-11 rules (`cc_tasks/2026-09-18_dcat_field_rules.md`).
Q_DCAT_BUREAU = ("dcat-us-1-1-schema", "'Rationale for Metadata Nomenclature', bureauCode",
                 "to ensure every dataset is connected in a standard way with an agency bureau.")
Q_DCAT_PROGRAM = ("dcat-us-1-1-schema", "'Rationale for Metadata Nomenclature', programCode",
                  "to ensure that when applicable, every dataset is connected in a standard way "
                  "with an agency program office.")
Q_DCAT_BUREAU_FMT = ("dcat-us-1-1-schema", "'Further Metadata Field Guidance', bureauCode",
                     "Represent each bureau responsible for the dataset according to the codes "
                     "found in OMB Circular A-11, Appendix C")
Q_DCAT_DICT = ("dcat-us-1-1-schema",
               "'Further Metadata Field Guidance', distribution → describedBy",
               "This is used to specify a data dictionary or schema that defines fields or "
               "column headings in the distribution.")
Q_DCAT_DICT_TYPE = ("dcat-us-1-1-schema",
                    "'Further Metadata Field Guidance', distribution → describedBy",
                    "If this is a machine readable file the media type should be specified "
                    "with `describedByType`")
Q_DCAT3_QUALITY = ("dcat-us-3-dataset-schema", "property `hasQualityMeasurement`",
                   "List of quality measurements for the dataset (for example, completeness, "
                   "accuracy, or timeliness) beyond spatial or temporal resolution")
Q_DCAT3_VNOTES = ("dcat-us-3-dataset-schema", "property `versionNotes`",
                  "Notes describing how this version differs from earlier versions of the "
                  "dataset")
Q_DCAT3_PREV = ("dcat-us-3-dataset-schema", "property `previousVersion`",
                "reference to the previous dataset version")
Q_DCAT3_GENERATED = ("dcat-us-3-dataset-schema", "property `wasGeneratedBy`",
                     "List of activities that generated, or provide the business context for "
                     "the creation of the dataset")
# schema.org and Content Signals, named by the generation-12 rules
# (`cc_tasks/2026-09-18_schema_field_rules.md`).
Q_SDO_VARIABLES = ("schema-org-dataset", "property `variableMeasured`",
                   "The variableMeasured property can indicate (repeated as necessary) the "
                   "variables that are measured in some dataset, either described as text or as "
                   "pairs of identifier and description using PropertyValue")
Q_SDO_TERM = ("schema-org-definedterm", "type `DefinedTerm`, description",
              "Use the name property for the term being defined, use termCode if the term has "
              "an alpha-numeric code allocated, use description to provide the definition of "
              "the term.")
Q_SDO_TERM_WHAT = ("schema-org-definedterm", "type `DefinedTerm`, description",
                   "A word, name, acronym, phrase, etc. with a formal definition.")
Q_SDO_TERMSET = ("schema-org-definedterm", "property `hasDefinedTerm` (on `DefinedTermSet`)",
                 "A Defined Term contained in this term set.")
Q_BP15 = ("w3c-dwbp-2017", "Best Practice 15 'Why'",
          "referring to codes and terms from standards helps to avoid ambiguity and clashes "
          "between similar elements or values.")
Q_CS_DIRECTIVE = ("cloudflare-content-signals-policy", "'Categories'",
                  "The Content-Signal directive works by signaling your preference of either "
                  "allowing (yes) or disallowing (no) certain categories of AI actions.")
Q_CS_EXAMPLE = ("cloudflare-content-signals-policy", "'Categories', example",
                "Content-Signal: ai-train=no, search=yes, ai-input=no")
Q_JSONLD = ("w3c-json-ld-1-1-core", "section 1 'Introduction', design goals",
            "The JSON-LD syntax is very terse and human readable, requiring as little effort "
            "as possible from the developer.")
Q_LIGHTHOUSE = ("lighthouse-docs-overview", "'Introduction to Lighthouse'",
                "Each audit has a reference that explains why the audit is important, as well "
                "as how to fix it.")
Q_E5_CONTROL = ("internal:scan-params", "`e5_control`",
                "The control cycle is the instrument's own E5. A cycle with zero fired "
                "controls is INVALID.")
Q_E5_PREREG = ("internal:scan-params", "`e5_control`",
               "DERIVED FROM THE RULE SOURCE and written down BEFORE the fixtures were first "
               "run.")
Q_E5_ORDER = ("internal:scan-params", "`e5_ordering`",
              "the cycle passes the earliest surface observation's `captured_at`")


ACTIONS = [
    # ---------------------------------------------------------------------------- A1
    _a("A1", "only_pdf", "a1-publish-a-structured-distribution",
       "Publish the product as a structured download beside the PDF",
       "Every download link probed from the product page served a PDF. Publish at least one "
       "machine-readable distribution of the same content (CSV, JSON, Parquet, XLSX or XML) "
       "and link it from the product page. The rule classifies on the RESPONSE content type, "
       "not on the href, so the file must be served as its own media type.",
       [Q_BP12, Q_BP14, Q_SCHEMA_DIST], cls="publish_new_file"),
    _a("A1", "no_structured_link", "a1-serve-the-data-files-with-their-own-media-type",
       "Link a data file from the product page and serve it with its own media type",
       "No probed link answered with a structured content type. Either no data file is linked "
       "from the product page, or the files are served as `text/html` or "
       "`application/octet-stream`. Link the distribution from the product page and configure "
       "the web server or CDN to return the format's media type for it.",
       [Q_BP19, Q_SCHEMA_DL, Q_BP12], cls="change_server_behaviour",
       class_reason=(
           "the rule classifies on the RESPONSE content type, so the act is the web server or "
           "CDN media-type configuration; linking the file without it does not move the "
           "verdict")),
    # ---------------------------------------------------------------------------- A2
    _a("A2", "served_but_not_an_api_description",
       "a2-serve-a-parseable-api-description-at-the-documented-path",
       "Serve a parseable OpenAPI description where the API is documented",
       "A document is served at a probed API path but does not parse as an API description; a "
       "JSON content type alone is not a description. Publish an OpenAPI Description document "
       "(YAML or JSON) at that path, so a client can discover the operations without reading "
       "prose.",
       [Q_OAS, Q_OAS_TOOLS, Q_BP25], cls="publish_new_file",
       class_reason=(
           "not `expose_api`: a document is already served at the probed API path, so what is "
           "missing is the description file and not the API")),
    _a("A2", "no_api_description", "a2-expose-an-api-and-publish-its-description",
       "Expose the product through an API and publish the API's description",
       "No OpenAPI or JSON API description was served at any probed path. Expose the product "
       "through a documented HTTP API and publish a machine-readable description of it; where "
       "the product already sits on a data platform, enabling the platform's own API is the "
       "cheaper route than building one.",
       [Q_BP23, Q_BP25, Q_OAS, Q_SCHEMA_API], cls="expose_api"),
    # ---------------------------------------------------------------------------- A3
    _a("A3", "filtered_query_not_whole_product",
       "a3-add-a-whole-product-download-beside-the-query-builder",
       "Add a whole-product download beside the query builder",
       "Every download link on the product page is a filtered query (a table-builder or "
       "parameterised export), so a consumer can obtain slices but never the product. Publish "
       "the complete product as a single retrievable file and link it from the same page, "
       "keeping the query builder for the subset case.",
       [Q_BP17, Q_SCHEMA_DIST], cls="publish_new_file"),
    _a("A3", "below_bulk_floor", "a3-publish-the-complete-file-not-a-sample",
       "Publish the complete product, not a sample extract",
       "The largest linked download is below the whole-product floor, which is the shape of a "
       "sample or a summary rather than the product. Publish the complete file — compressed "
       "if it is large — and link it from the product page.",
       [Q_BP17, Q_BP12], cls="publish_new_file"),
    _a("A3", "no_whole_product_download", "a3-link-a-bulk-download-from-the-product-page",
       "Link a bulk download of the product from the product page",
       "No whole-product download is linked from the product page at all. Publish the product "
       "as one retrievable file at a stable URL and link it from the product page; where the "
       "product is served only through an API, add a bulk-download route to it.",
       [Q_BP17, Q_DCAT_DIST], cls="publish_new_file"),
    # ---------------------------------------------------------------------------- A4
    _a("A4", "no_robots_txt", "a4-serve-a-robots-txt-that-names-ai-crawlers",
       "Serve a robots.txt and state the policy for AI crawlers in it",
       "No robots.txt is served. Retrieval is permitted by default, but nothing is DECLARED, "
       "so a compliant AI client has no statement to rely on and an operator has no lever "
       "short of the edge. Serve `/robots.txt` and give the AI crawler product tokens their "
       "own groups.",
       [Q_RFC_UA, Q_GOOG, Q_OPENAI], cls="publish_new_file",
       class_reason=(
           "no robots.txt is served at all, so the act is publishing a file the host does not "
           "have, not editing a directive in one it does")),
    _a("A4", "robots_disallows_ai_crawlers", "a4-allow-the-data-paths-for-named-ai-crawlers",
       "Allow the product's data paths for the AI crawlers you intend to serve",
       "robots.txt disallows the product path for one or more AI crawler user agents. Where "
       "the intent is to serve the data and to throttle crawling, add an `allow` rule for the "
       "data paths in those user agents' groups: the most specific match wins, and an `allow` "
       "beats an equivalent `disallow`, so a broad `Disallow: /` can stand with the data "
       "paths carved out of it.",
       [Q_RFC_ALLOW, Q_OPENAI, Q_GOOG], cls="edit_existing"),
    # ---------------------------------------------------------------------------- A5
    _a("A5", "discovery_file_omits_product", "a5-list-the-product-url-in-the-sitemap",
       "List the product URL in the discovery file that is already served",
       "A sitemap, llms.txt or well-known discovery file is served and none of them lists the "
       "product URL, so a crawler that obeys the site's own discovery surface never reaches "
       "the product. Add the product's `<loc>` entry to the sitemap that covers its host.",
       [Q_SITEMAP_FMT, Q_SITEMAP_HOST, Q_LLMS], cls="edit_existing"),
    _a("A5", "no_discovery_file", "a5-publish-a-sitemap-and-point-robots-txt-at-it",
       "Publish a sitemap and point robots.txt at it",
       "No sitemap, llms.txt or well-known discovery file is served on the host, so the "
       "product is discoverable only by following links. Publish a sitemap covering the "
       "product URLs and declare its location in robots.txt; an `llms.txt` at the site root "
       "serves the same purpose for agent clients.",
       [Q_SITEMAP_LOC, Q_SITEMAP_FMT, Q_LLMS], cls="publish_new_file"),
    # ---------------------------------------------------------------------------- A6
    _a("A6", "markup_without_dataset_type", "a6-type-the-product-page-as-a-dataset",
       "Type the product page's existing markup as a Dataset",
       "The product page carries structured markup but no `Dataset` or `DataCatalog` type, so "
       "a consumer reading the graph finds an organisation or a web page where the product "
       "should be. Add a `Dataset` node to the existing JSON-LD and hang the distributions, "
       "licence and dates off it.",
       [Q_SCHEMA_DIST, Q_BP1, Q_JSONLD], cls="edit_existing"),
    _a("A6", "no_structured_markup", "a6-embed-json-ld-on-the-product-page",
       "Embed JSON-LD describing the product on the product page",
       "The product page carries no JSON-LD, microdata or RDFa at all: everything the page "
       "says about the product is prose. Embed a JSON-LD block describing the product as a "
       "`Dataset`, with its title, publisher, dates, licence and distributions.",
       [Q_BP1, Q_JSONLD, Q_SCHEMA_DIST], cls="edit_existing",
       class_reason=(
           "a JSON-LD block is markup added to a page the host already serves: no new file, "
           "and no change to how the server answers")),
    _a("A6", "shapes_violation", "a6-make-the-dataset-markup-conform-to-the-profile",
       "Make the Dataset markup conform to the profile it declares",
       "The markup declares a `Dataset` and violates the profile's shapes — a required "
       "property is missing, or a value is the wrong type. Fix the fields the validator names; "
       "the field set and its casing are defined, not a matter of taste.",
       [Q_DCAT3, Q_DCAT_CASE, Q_SCHEMA_DIST], cls="edit_existing"),
    # ---------------------------------------------------------------------------- A8
    _a("A8", "last_modified_header_only", "a8-declare-the-product-vintage-in-the-markup",
       "Declare the product's vintage in the markup, not only in a file header",
       "The only date observable is an HTTP `Last-Modified` header, which is a fact about the "
       "file the server holds and not a declared product vintage: touching the file moves it. "
       "Put `datePublished` and `dateModified` on the product's `Dataset` markup.",
       [Q_SCHEMA_DATE, Q_BP7], cls="edit_existing"),
    _a("A8", "no_declared_date", "a8-publish-a-release-date-for-the-product",
       "Publish a release date for the product",
       "No declared release or modification date appears on the surface, so a consumer cannot "
       "tell which vintage it is holding. Publish the release and revision dates as fields — "
       "`issued` and `modified` in the catalogue record, `datePublished`/`dateModified` in the "
       "page markup.",
       [Q_BP7, Q_DCAT3, Q_SCHEMA_DATE], cls="edit_existing"),
    _a("A8", "no_latest_vintage_pointer", "a8-serve-a-stable-latest-url-on-the-product-host",
       "Serve a stable 'latest' URL for the product on its own host",
       "The markup declares the vintage but the surface offers no latest-vintage pointer on "
       "its own host, so a consumer holding an old vintage has no way to ask for the current "
       "one. Publish a URL that always resolves to the latest release and keep the dated URLs "
       "beside it for the immutable snapshots.",
       [Q_BP7_LATEST, Q_BP11], cls="change_server_behaviour",
       class_reason=(
           "a URL that always resolves to the latest release is a route the server maintains "
           "across releases, not a file published once")),
    _a("A8", "latest_vintage_pointer_unresolved", "a8-make-the-latest-pointer-resolve",
       "Make the latest-vintage pointer resolve",
       "A latest-vintage pointer is declared and none of the candidates resolves: the URL is "
       "published and answers an error. Repair the redirect or the route so the pointer "
       "resolves, and design it to stay resolvable across releases rather than being "
       "regenerated with each one.",
       [Q_BP9, Q_BP11, Q_BP7_LATEST], cls="change_server_behaviour"),
    # ---------------------------------------------------------------------------- A9
    _a("A9", "machine_path_answers_html", "a9-return-a-machine-format-at-the-machine-path",
       "Return a machine format at the paths advertised for machines",
       "A probed machine-first path answers with HTML rather than a machine format: the route "
       "exists and returns the human page. Serve the machine representation at that path, or "
       "honour the request's `Accept` header and return the machine format when it is asked "
       "for.",
       [Q_BP19, Q_LLMS_MD, Q_LLMS_LINK], cls="change_server_behaviour"),
    _a("A9", "no_machine_first_path", "a9-publish-a-machine-first-entry-point",
       "Publish a machine-first entry point for the product",
       "None of the probed machine-first paths is served, so a machine client's only entry is "
       "the human page. Publish an entry point built for machines — an `/llms.txt` at the site "
       "root, an API root, or a data endpoint — and link it from the product page.",
       [Q_LLMS, Q_LLMS_LINK, Q_BP23], cls="publish_new_file"),
    # ---------------------------------------------------------------------------- A10
    _a("A10", "soft_404", "a10-return-a-real-status-for-routes-that-do-not-exist",
       "Return a real HTTP status for routes that do not exist",
       "An invented route under the product path answers HTTP 200: the host serves a "
       "human-readable 'not found' page with a success status, so a machine client cannot tell "
       "a real deep link from a typo and will treat the error page as the product. Return 404 "
       "(or 410 for a resource deliberately removed) with the explanation in the body.",
       [Q_BP22, Q_BP27], cls="change_server_behaviour"),
    _a("A10", "deep_link_error_status", "a10-make-the-product-deep-link-resolve",
       "Make the product's own deep link resolve",
       "The product deep link itself answers an error status, so the URL the product is "
       "published under does not reach it. Repair the route, and where the URL has moved, "
       "redirect the published one rather than retiring it.",
       [Q_BP9, Q_BP27], cls="change_server_behaviour"),
    _a("A10", "client_rendered_shell", "a10-serve-the-product-content-before-javascript-runs",
       "Serve the product's content in the first response, before JavaScript runs",
       "The deep link answers 200 and carries almost no visible text before JavaScript runs: "
       "the page is a client-rendered shell, and every consumer that does not execute scripts "
       "— including most crawlers and agents — sees an empty page. Server-render the product's "
       "content, or publish a clean text or markdown version at the same URL and point at it "
       "with a `Link` header.",
       [Q_LLMS_JS, Q_LLMS_MD, Q_LIGHTHOUSE], cls="change_server_behaviour"),
    # ---------------------------------------------------------------- A11 (declared leg)
    _a("A11-declared", "nothing_declared",
       "a11-declare-a-crawler-policy-for-the-product-path",
       "Declare a crawler policy for the product path",
       "No robots.txt is served, so the declared layer of the A11 triad is empty and there is "
       "nothing for the enforced and observed layers to be compared against. Serve a "
       "robots.txt that states the policy for the product path, per AI crawler product token.",
       [Q_GOOG, Q_RFC_UA, Q_OPENAI], cls="publish_new_file",
       class_reason=(
           "no robots.txt is served, so this is the same act as A4's `no_robots_txt` action on "
           "the same host: a file published where none exists")),
    _a("A11-declared", "robots_disallows_ai_crawlers",
       "a11-permit-the-ai-crawlers-you-intend-to-serve-on-the-product-path",
       "Permit, in robots.txt, the AI crawlers the product is meant to reach",
       "robots.txt disallows the product path for AI crawler user agents, so the declared "
       "policy is that these consumers are not served. Where that is not the intent, add "
       "`allow` rules for the product paths in those groups.",
       [Q_RFC_ALLOW, Q_OPENAI], cls="edit_existing"),
    _a("A11-declared", "meta_robots_contradicts_robots_txt",
       "a11-resolve-the-meta-robots-directive-that-contradicts-robots-txt",
       "Resolve the meta-robots directive that contradicts robots.txt",
       "robots.txt permits every AI crawler and the product page's own meta-robots directives "
       "restrict it: the declared layer has two sources and they disagree, so what is declared "
       "depends on which one a consumer reads. Decide the policy once and make the page's "
       "directives say it — robots.txt governs crawling, the meta directives govern indexing, "
       "and they are not interchangeable.",
       [Q_GOOG_NOINDEX, Q_GOOG], cls="edit_existing"),
    # ---------------------------------------------------------------------------- A12
    _a("A12", "robots_itself_refused", "a12-serve-robots-txt-to-every-client",
       "Serve /robots.txt to every client, including ones the edge does not recognise",
       "The host answered a refusal to `/robots.txt` itself for an identified client: the "
       "declared layer is not observable and the enforced layer refuses, so no consumer can "
       "learn the policy it is being held to. Exempt `/robots.txt` from bot management — the "
       "protocol treats it as implicitly allowed.",
       [Q_RFC_SELF, Q_GOOG], cls="change_server_behaviour",
       class_reason=(
           "the file exists and the EDGE refuses it, so the act is a bot-management exemption "
           "rather than an edit to the file"),
       note="A12 is a CANDIDATE indicator (DD-054): its rule runs, its Findings are reported, "
            "and they enter no framework numerator until the operator adopts it. The action is "
            "recorded on the same terms.",
       applies_to_note="The subject is the publisher's host, as for every other A-criterion "
                       "leg; what is provisional is the indicator, not who acts on it."),
    _a("A12", "nothing_declared_for_this_client",
       "a12-publish-a-robots-txt-group-an-identified-client-matches",
       "Publish a robots.txt group that an identified machine client matches",
       "Nothing is DECLARED for this client — the file is absent, empty, or carries no group "
       "its product token matches — so there is no declaration for the enforced layer to "
       "cohere with. Publish a group that a compliant identified client will match, at "
       "minimum a `user-agent: *` group with explicit rules.",
       [Q_RFC_UA, Q_RFC_SELF], cls="edit_existing",
       class_reason=(
           "the act named is adding a group to robots.txt. Where the file is absent outright, "
           "the publishing act is already carried by A4's and A11's `publish_new_file` actions "
           "on the same host, so classing this one `publish_new_file` would count that work "
           "twice"),
       note="A12 is a CANDIDATE indicator (DD-054): it enters no framework numerator until the "
            "operator adopts it.",
       applies_to_note="The subject is the publisher's host; what is provisional is the "
                       "indicator."),
    _a("A12", "declared_permits_enforced_refuses", "a12-align-the-edge-with-the-declaration",
       "Align the edge or bot manager with what robots.txt declares",
       "robots.txt PERMITS the identified client for a path and the host answered a refusal to "
       "that same path: the declared and enforced layers disagree, and the declaration is the "
       "one a compliant consumer obeys. Either allowlist compliant identified clients at the "
       "edge, or change the declaration so it states what is actually enforced. A published "
       "crawler identity with published address ranges is what makes the first option "
       "operable.",
       [Q_OPENAI_IPS, Q_RFC_ALLOW, Q_GOOG], cls="change_server_behaviour",
       note="A12 is a CANDIDATE indicator (DD-054): it enters no framework numerator until the "
            "operator adopts it. This is the outcome the indicator was proposed for — three "
            "principal agencies refused an identified client on paths their own robots.txt "
            "permits (`ind:A12.candidate_provenance`).",
       applies_to_note="The subject is the publisher's host; what is provisional is the "
                       "indicator."),
    # ---------------------------------------------------------------------------- B3
    _a("B3", "methodology_requires_js", "b3-serve-the-methodology-without-javascript",
       "Serve the methodology document without requiring JavaScript",
       "A methodology document is served and is not retrievable without executing JavaScript, "
       "so a consumer that reads the response body finds nothing. Server-render the "
       "methodology, or publish a plain text or markdown copy at a stable URL and link it.",
       [Q_LLMS_JS, Q_LLMS_MD], cls="change_server_behaviour",
       class_reason=(
           "the document is already served and the failure is that its content needs "
           "JavaScript to appear; the first route the action names is server-rendering it")),
    _a("B3", "methodology_pdf_only", "b3-publish-the-methodology-in-structured-text",
       "Publish the methodology in structured text beside the PDF",
       "The methodology is served as PDF only. Publish it in a structured text format — HTML "
       "or markdown — beside the PDF, so the definitions, universe and estimation notes can be "
       "read by a machine without a layout-recovery step.",
       [Q_BP12, Q_BP14], cls="publish_new_file"),
    _a("B3", "no_methodology_link", "b3-link-the-methodology-from-the-product-page",
       "Link the methodology from the product page",
       "The product surface links no methodology document, so a consumer reading the product "
       "has no path to how it was produced. Link the methodology from the product page, and "
       "name it in the catalogue record's data-dictionary field where one exists.",
       [Q_BP5, Q_DCAT3], cls="edit_existing"),
    _a("B3", "no_structured_text_methodology",
       "b3-publish-a-methodology-document-reachable-from-the-product",
       "Publish a methodology document reachable from the product surface",
       "No structured-text methodology document is reachable from the product surface: the "
       "links that exist do not lead to one. Publish the methodology — source, universe, "
       "collection, estimation and known limitations — at a stable URL and reach it from the "
       "product page in one hop.",
       [Q_BP5, Q_BP1], cls="publish_new_file"),
    # ---------------------------------------------------------------------------- D1
    _a("D1", "licence_is_free_text", "d1-state-the-licence-as-an-identifier",
       "State the licence as an identifier, not as a sentence",
       "A licence statement is present and its value is free text, so a machine can see that "
       "terms exist but not what they permit. State the licence as a recognised identifier — "
       "an SPDX id or the licence's canonical URL — in the markup's `license` property.",
       [Q_SCHEMA_LIC, Q_BP4], cls="edit_existing"),
    _a("D1", "no_licence", "d1-publish-a-machine-readable-licence",
       "Publish a machine-readable licence for the product",
       "No licence appears in the product page's markup, in an HTTP `Link` header, or at a "
       "probed terms endpoint, so a consumer has to assume the worst or guess. Publish the "
       "licence as a machine-readable value on the product's markup and in its catalogue "
       "record.",
       [Q_BP4, Q_SCHEMA_LIC], cls="edit_existing",
       class_reason=(
           "the licence is a value written into markup and a catalogue record the host already "
           "serves, not a file of its own")),
    # ---------------------------------------------------------------------------- D4
    _a("D4", "catalog_schema_violation", "d4-make-the-catalog-conform-to-dcat-us",
       "Make the public data catalog conform to the DCAT-US schema",
       "The product appears in the host's catalog and the catalog violates the schema, so a "
       "consumer that validates before reading rejects the whole file. Fix the fields the "
       "validator names; field names are case-sensitive and a near-miss is a miss.",
       [Q_DCAT_CASE, Q_DCAT_DIST, Q_DCAT3], cls="edit_existing"),
    _a("D4", "product_absent_from_catalog", "d4-add-the-product-to-the-public-data-inventory",
       "Add the product to the public data inventory already published",
       "A catalog is served on the host and the product is not in it, so the product is "
       "invisible to every consumer that starts from the inventory. Add the product's record "
       "to the catalog file; the inventory is meant to list all of the agency's public data "
       "assets, whether they are downloads or APIs.",
       [Q_DCAT_CATALOG, Q_SCHEMA_CAT], cls="edit_existing"),
    _a("D4", "no_catalog", "d4-publish-a-data-json-inventory",
       "Publish a data.json inventory on the host",
       "No public `data.json` catalog is served on this host, so there is no machine-readable "
       "inventory of what the agency publishes. Publish one at `/data.json` and let its own "
       "URL be its identifier.",
       [Q_DCAT_CATALOG, Q_DCAT_ID], cls="publish_new_file"),
    # ---------------------------------------------------------------------------- E5
    _a("E5", "zero_controls_fired", "e5-fire-every-declared-control-before-the-first-host",
       "Fire every declared control fixture before the cycle contacts a host",
       "A cycle with zero fired controls is INVALID: nothing licenses its verdicts, because "
       "nothing demonstrated that the instrument could still tell a pass from a fail. Run the "
       "declared fixtures at the head of the cycle and record their observations with it.",
       [Q_E5_CONTROL, Q_E5_PREREG], cls="harness_side", applies_to_publisher=False,
       applies_to_note="E5's rule judges THIS instrument's own cycle, not a publisher's "
                       "surface (`ind:E5.tier_note`, `not_measured_reason`). The actor is the "
                       "operator of the harness.",
       note="Not a prescription for a federal publisher. It is on the same footing as the "
            "others because the instrument is measured by its own instrument, which is what "
            "E5 is for."),
    _a("E5", "control_verdict_not_as_expected", "e5-investigate-the-control-verdict-that-moved",
       "Investigate a control verdict that moved, and never retune the expectation",
       "A control fixture returned a verdict other than the pre-registered one. The "
       "expectations were derived from the rule source and written down before the fixtures "
       "were first run, so a mismatch is a finding about the instrument: investigate the rule "
       "or the fixture. Editing the expectation to match what came out ends the gate.",
       [Q_E5_PREREG, Q_E5_CONTROL], cls="harness_side", applies_to_publisher=False,
       applies_to_note="E5's rule judges this instrument's own cycle. The actor is the "
                       "operator of the harness.",
       note="The one action in this layer whose execution is forbidden to change the check. "
            "That asymmetry is the point of a pre-registered control."),
    _a("E5", "controls_ran_after_surfaces", "e5-order-the-controls-before-the-surfaces",
       "Order the control fixtures ahead of every real host in the cycle",
       "One or more control observations are stamped after the cycle's earliest surface "
       "observation, so the canaries ran after the surfaces they were meant to license. Order "
       "the fixtures first, and keep the earliest surface timestamp on the cycle so the "
       "ordering stays falsifiable from stored evidence rather than asserted by the runner's "
       "control flow.",
       [Q_E5_ORDER, Q_E5_CONTROL], cls="harness_side", applies_to_publisher=False,
       applies_to_note="E5's rule judges this instrument's own cycle. The actor is the "
                       "operator of the harness."),
    # ---------------------------------------------------------------------------- F4
    _a("F4", "changelog_entries_lack_revision_class",
       "f4-carry-a-revision-class-on-every-changelog-entry",
       "Carry a revision class on every changelog entry",
       "A machine-readable changelog is served and too few of its entries carry a revision "
       "class, so a consumer can see that something changed but not whether it was a "
       "correction, a scheduled revision or a new release. Put a class on every entry — an "
       "Atom `<category term=...>`, or a `type`/`change_type` field in JSON.",
       [Q_BP8, Q_BP7], cls="edit_existing"),
    _a("F4", "changelog_not_machine_readable",
       "f4-serve-the-changelog-in-a-machine-readable-format",
       "Serve the changelog in a machine-readable format as well as a page",
       "A changelog page is served and not in a machine-readable content type, so the history "
       "is readable only by a person. Publish the same history as JSON, Atom or RSS at its own "
       "URL and keep the human page beside it.",
       [Q_BP8_API, Q_BP12], cls="publish_new_file"),
    _a("F4", "no_changelog", "f4-publish-a-version-history-endpoint",
       "Publish a version history for the product",
       "No changelog or release-notes endpoint is served, so a consumer holding an older "
       "vintage cannot learn what changed. Publish a list of released versions with, for each, "
       "what differs from the previous one; a single dedicated URL that returns the complete "
       "history is enough.",
       [Q_BP8, Q_BP8_API], cls="publish_new_file"),
    # ---------------------------------------------------------------------------- G1-D
    _a("G1-D", "no_error_measure_field", "g1d-publish-the-error-measure-as-a-structured-field",
       "Publish the error measure as a structured field beside the estimate",
       "None of the error-measure field tokens appears as a structured field on the surface: "
       "the uncertainty is in a footnote, a caption or nowhere, and a consumer reading the "
       "estimate gets a point value with no dispersion. Publish the margin of error, standard "
       "error or coefficient of variation as its own field beside each estimate — a column in "
       "the distribution and a `variableMeasured` entry in the markup.",
       [Q_SCHEMA_VAR, Q_BP6], cls="edit_existing",
       note="Withdrawn from the HOST level from cycle 5 (DD-066): a home page carries no "
            "estimate, so the leg cannot hold the property it measures there. The action is a "
            "product-surface action, which is the level `ind:G1-D.measurement_level` records."),
    # --------------------------------------------------- B1, B4, D3, G4 (generation 11)
    # `cc_tasks/2026-09-18_dcat_field_rules.md` decision 4. Techniques from the same DCAT-US
    # documents the fields cite. `no_product_record` is classed `publish_new_file` on every leg:
    # the outcome covers a host with no catalog as well as a catalog without the product's
    # record, and the class is the larger of the two acts, the one most hosts on the cycle of
    # record face (9 of its 16 bodies answer `/data.json` with no catalog, 3 serve one and 4
    # could not be observed; `cc_tasks/2026-09-18_dcat_field_rules_RESULT.md` §1).
    _a("B1", "no_product_record", "b1-publish-the-products-record-with-its-data-dictionary",
       "Publish the product's catalog record with a link to its data dictionary",
       "The product has no record in a data.json catalog on the host — none is served, or it "
       "does not parse, or the product is not in it — so no machine-readable record points a "
       "consumer at the dictionary that defines the product's fields. Publish the product's "
       "record in the agency's data.json and give its distribution a `describedBy` link to the "
       "data dictionary, with `describedByType` when the dictionary is machine-readable.",
       [Q_DCAT_CATALOG, Q_DCAT_DICT], cls="publish_new_file", task=DCAT_TASK,
       class_reason=_NO_RECORD_CLASS),
    _a("B1", "no_data_dictionary", "b1-link-the-data-dictionary-from-the-catalog-record",
       "Link the data dictionary from the product's catalog record",
       "The product's catalog record carries no `describedBy`, at the dataset level or on any "
       "distribution, so a consumer reading the record cannot find what the columns mean. Add "
       "`describedBy` on the distribution, pointing at the data dictionary or schema, and "
       "`describedByType` naming its media type when it is machine-readable.",
       [Q_DCAT_DICT, Q_DCAT_DICT_TYPE], cls="edit_existing", task=DCAT_TASK),
    _a("B4", "no_product_record", "b4-publish-the-products-record-with-quality-metadata",
       "Publish the product's catalog record with its quality and revision metadata",
       "The product has no record in a data.json catalog on the host, so its error measures "
       "and revision history exist, if at all, only in prose. Publish the product's record and "
       "carry `hasQualityMeasurement` and `versionNotes` (or `previousVersion`) on it.",
       [Q_DCAT_CATALOG, Q_DCAT3_QUALITY], cls="publish_new_file", task=DCAT_TASK,
       class_reason=_NO_RECORD_CLASS),
    _a("B4", "quality_measurement_absent", "b4-publish-quality-measurements-as-metadata",
       "Publish the product's quality measurements as catalog metadata",
       "The product's catalog record carries no `hasQualityMeasurement`, so the error measures "
       "a consumer needs to weigh an estimate are not machine-readable. List the product's "
       "quality measurements — accuracy, completeness, timeliness — as `hasQualityMeasurement` "
       "entries on the record.",
       [Q_DCAT3_QUALITY, Q_BP6], cls="edit_existing", task=DCAT_TASK),
    _a("B4", "revision_metadata_absent", "b4-state-what-changed-from-the-previous-version",
       "State what changed from the previous version in the catalog record",
       "The product's catalog record carries no `versionNotes`, `previousVersion` or "
       "`hasCurrentVersion`, so a consumer holding one vintage cannot tell from the record "
       "how it relates to the next. Add `versionNotes` saying how this version differs, and "
       "`previousVersion` pointing at the one it replaces.",
       [Q_DCAT3_VNOTES, Q_DCAT3_PREV, Q_BP8], cls="edit_existing", task=DCAT_TASK),
    _a("D3", "no_product_record", "d3-publish-the-products-record-with-its-lineage",
       "Publish the product's catalog record naming how it was generated",
       "The product has no record in a data.json catalog on the host, so no machine-readable "
       "record says what activity produced it or from what. Publish the product's record and "
       "name the generating activity on it with `wasGeneratedBy`.",
       [Q_DCAT_CATALOG, Q_DCAT3_GENERATED], cls="publish_new_file", task=DCAT_TASK,
       class_reason=_NO_RECORD_CLASS),
    _a("D3", "no_lineage_field", "d3-name-the-generating-activity-in-the-catalog-record",
       "Name the activity that generated the product in its catalog record",
       "The product's catalog record names no lineage — no `wasGeneratedBy` and no "
       "`wasDerivedFrom` — so the path from collection to product is not machine-readable. "
       "Add `wasGeneratedBy` naming the collection and estimation activities, and "
       "`prov:wasDerivedFrom` where the product is derived from another dataset.",
       [Q_DCAT3_GENERATED, Q_BP5], cls="edit_existing", task=DCAT_TASK),
    _a("G4", "no_product_record", "g4-publish-the-products-record-with-its-authority-codes",
       "Publish the product's catalog record carrying its bureau and program codes",
       "The product has no record in a data.json catalog on the host, so nothing machine-"
       "readable ties the product to the bureau and program that issue it, and an aggregator's "
       "copy carries as much authority as the original. Publish the product's record with "
       "`bureauCode` and `programCode`.",
       [Q_DCAT_CATALOG, Q_DCAT_BUREAU], cls="publish_new_file", task=DCAT_TASK,
       class_reason=_NO_RECORD_CLASS),
    _a("G4", "authority_codes_absent", "g4-carry-bureau-and-program-codes-on-the-record",
       "Carry `bureauCode` and `programCode` on the product's catalog record",
       "The product's catalog record lacks a well-formed `bureauCode` or `programCode`, so the "
       "issuing authority is not carried as structured metadata. Add both, in the formats the "
       "schema states: the OMB Circular A-11 agency and bureau code (`015:11`) and the Federal "
       "Program Inventory code (`015:001`).",
       [Q_DCAT_BUREAU, Q_DCAT_PROGRAM, Q_DCAT_BUREAU_FMT], cls="edit_existing",
       task=DCAT_TASK),
    # -------------------------------------------------- B1, B2, B5, D2 (generation 12)
    # `cc_tasks/2026-09-18_schema_field_rules.md`. Techniques from the documents the fields
    # cite: `schema-org-dataset`, `schema-org-definedterm`, `cloudflare-content-signals-policy`,
    # and W3C DWBP Best Practice 15 for the one act that is about a body rather than a page.
    _a("B1", "no_variable_measured", "b1-list-the-variables-measured-in-the-page-markup",
       "List the product's variables in its page markup",
       "The product page's schema.org markup carries no `variableMeasured`, so a crawler or "
       "an AI tool reading the page learns what the dataset is but not what it measures. Add "
       "`variableMeasured` to the page's `Dataset`, one `PropertyValue` per variable with its "
       "name and description.",
       [Q_SDO_VARIABLES, Q_BP1], cls="edit_existing", task=SD_TASK),
    _a("B2", "no_defined_terms", "b2-publish-concept-definitions-as-defined-terms",
       "Publish the product's concept definitions as schema.org `DefinedTerm`s",
       "The product page's markup carries no `DefinedTerm`, so the definitions of the concepts "
       "the product counts exist, if at all, only as prose. Mark each concept up as a "
       "`DefinedTerm` with its `name`, a `termCode`, the `inDefinedTermSet` it belongs to, and "
       "its definition as `description`.",
       [Q_SDO_TERM, Q_SDO_TERM_WHAT], cls="edit_existing", task=SD_TASK),
    _a("B2", "terms_not_linked", "b2-link-defined-terms-from-the-variables",
       "Link the defined terms from the product's variables",
       "The page publishes `DefinedTerm`s, and no `Dataset` reaches them, so nothing machine-"
       "readable says which variable a definition belongs to. Reference each term from the "
       "`Dataset` — as the `measurementTechnique` of the `variableMeasured` entry it defines.",
       [Q_SDO_VARIABLES, Q_SDO_TERM], cls="edit_existing", task=SD_TASK),
    _a("B2", "terms_incomplete", "b2-give-each-defined-term-a-code-set-and-definition",
       "Give each linked defined term a code, a term set and a definition",
       "A `DefinedTerm` linked from the product's variables lacks a `termCode`, an "
       "`inDefinedTermSet` or a `description`, so a consumer cannot tell which concept it is or "
       "what it means. Add all three.",
       [Q_SDO_TERM, Q_SDO_TERMSET], cls="edit_existing", task=SD_TASK),
    _a("B5", "no_term_codes", "b5-code-the-bodys-concepts-in-one-term-set",
       "Code the body's concepts in one published term set",
       "None of the body's product pages carries a coded `DefinedTerm`, so nothing machine-"
       "readable says that two products count the same concept. Publish one `DefinedTermSet` "
       "for the body's concepts, give each a `termCode`, and reference the terms from every "
       "product that uses them.",
       [Q_SDO_TERM, Q_SDO_TERMSET, Q_BP15], cls="publish_new_file", task=SD_TASK,
       class_reason=("the act the outcome needs is a term set the body does not yet publish, "
                     "which is a new file; the per-page references that follow are edits")),
    _a("B5", "codes_without_set", "b5-name-the-set-each-term-code-belongs-to",
       "Name the term set each term code belongs to",
       "Coded `DefinedTerm`s on the body's product pages carry no `inDefinedTermSet`, and a "
       "`termCode` identifies a term only within its set, so the codes cannot be compared "
       "across products. Add `inDefinedTermSet` to every coded term.",
       [Q_SDO_TERM, Q_SDO_TERMSET], cls="edit_existing", task=SD_TASK),
    _a("B5", "codes_not_shared_across_products", "b5-use-one-identifier-per-concept",
       "Use one identifier for each concept across the body's products",
       "A concept coded on two or more of the body's products carries a different `termCode` "
       "or term set on each, so a machine joining the products cannot tell that they count the "
       "same thing. Give each concept one code in one term set and use it on every product.",
       [Q_BP15, Q_SDO_TERMSET], cls="publish_new_file", task=SD_TASK,
       class_reason=("reconciling divergent codes means publishing the one term set every "
                     "product will point at; the per-page edits follow from it")),
    _a("D2", "no_content_signal", "d2-declare-ai-training-and-input-terms-in-robots-txt",
       "Declare the terms for AI training and AI input in robots.txt",
       "The host's robots.txt carries no `Content-Signal` for `ai-train` or `ai-input`, so the "
       "terms for the two uses the indicator names are not machine-readable where a crawler "
       "reads its rules. Add a `Content-Signal` line under the `User-agent` group, declaring "
       "`ai-train` and `ai-input` as `yes` or `no`.",
       [Q_CS_DIRECTIVE, Q_CS_EXAMPLE], cls="edit_existing", task=SD_TASK),
    _a("D2", "unknown_category", "d2-use-only-the-defined-content-signal-categories",
       "Use only the categories and values the Content Signals Policy defines",
       "A `Content-Signal` in the host's robots.txt names a category or a value the policy "
       "does not define, so a reader cannot know what it declares. Use `search`, `ai-input` "
       "and `ai-train`, each `yes` or `no`.",
       [Q_CS_DIRECTIVE, Q_CS_EXAMPLE], cls="edit_existing", task=SD_TASK),
]


# ---------------------------------------------------- downstream indicators (decision 1)
#
# "indicators whose spec presupposes this one, WHERE THE RECORD SAYS SO". A token scan over
# every text field of every node found four cross-references among the 17 harness legs and
# their specs; three of them are presuppositions and are listed here with the field and the
# verbatim sentence, checked against the record before anything is written. The fourth
# (`ind:G1-D.tier_note` naming G1-O) says which leg the G1 instrument judges, not that G1-O
# presupposes G1-D, so it is not a downstream edge. A leg absent from this table has an empty
# list and a source saying the scan found nothing — absence stated, never defaulted.
DOWNSTREAM = {
    "A4": [("A11", "ind:A11", "indicator",
            "A4 upgraded from declared-policy check to three-layer comparison"),
           ("A12", "spec:A12", "signal",
            "A robots.txt that DISALLOWS the path is not incoherence — it is A4's "
            "measurement, and this indicator is `not_applicable` there.")],
    "A11": [("A12", "ind:A12", "candidate_rationale",
             "The public-observable leg of A11's enforced layer.")],
}
NO_DOWNSTREAM = ("no field of any node in " + RECORD + " states that another indicator "
                 "presupposes this one; scanned every string property of every node for a "
                 "code other than its own")


def repo_text(rel: str) -> str:
    return (REPO / rel).read_text(encoding="utf-8")


def rule_module_source(leg: str) -> tuple:
    """`(rule_id, source text)` for the rule a NEW cycle judges this leg with."""
    import inspect
    from scan.rules import CURRENT, REGISTRY
    rid = CURRENT[leg]
    return rid, Path(inspect.getsourcefile(REGISTRY[rid])).read_text(encoding="utf-8")


def format_source(entry: tuple) -> str:
    doc_id, locator, quote = entry
    return f"{SOURCES[doc_id]} (doc_id `{doc_id}`), {locator}: \"{quote}\""


def cycle_of_record() -> str:
    import yaml
    return yaml.safe_load(repo_text(PUBLICATION))["snapshot_cycle"]


def matrix_fail_bodies(cycle: str) -> dict:
    """`{leg: (bodies_failing, bodies_total)}` from the published matrices of `cycle`.

    A body fails a leg when any of its rows on that matrix carries the verdict `fail` — the
    tier-A matrix is one row per body, the product matrix is one row per DECLARED flagship
    surface and a body may have several. Tier C reference hosts enter no Tier A denominator
    (DD-059) and have their own matrix, which is not read here.
    """
    suffix = cycle.replace("scan_", "")
    out = {}
    for kind in ("tierA", "product"):
        m = json.loads(repo_text(f"docs/reports/scan_matrix_{kind}_{suffix}.json"))
        rows = [r for r in m["rows"] if kind != "product" or r.get("declared")]
        bodies = {r["agency"] for r in rows}
        for leg in m["legs"]:
            failing = {r["agency"] for r in rows if r["verdicts"].get(leg) == "fail"}
            if leg in out:
                raise SystemExit(f"FATAL: leg {leg!r} is on two matrices of {cycle}")
            out[leg] = (len(failing), len(bodies), f"docs/reports/scan_matrix_{kind}_{suffix}.json")
    return out


def validate(g: dict) -> dict:
    """Refuse before writing. Every check here is a way the table could be wrong in a way a
    reader of the record could not see."""
    from scan.rules import CURRENT
    inds = {n["properties"]["code"]: n for n in g["nodes"]
            if "AssessmentIndicator" in n["labels"]}
    by_id = {n["id"]: n for n in g["nodes"]}
    harness = {c for c, n in inds.items()
               if n["properties"].get("measurement_basis") == "harness_leg"}

    # 1. the legs this task covers are exactly the harness legs, and each has a CURRENT rule
    legs = set(OUTCOMES)
    codes = {indicator_code(l) for l in legs}
    if codes != harness:
        raise SystemExit(f"FATAL: OUTCOMES covers {sorted(codes)}; the record's harness_leg "
                         f"indicators are {sorted(harness)}")
    for leg in legs:
        if leg not in CURRENT:
            raise SystemExit(f"FATAL: {leg!r} is not a leg in rules.CURRENT")

    # 2. every outcome fragment is verbatim in its CURRENT rule module
    for leg, outs in OUTCOMES.items():
        rid, src = rule_module_source(leg)
        for name, frag in outs.items():
            if frag not in src:
                raise SystemExit(f"FATAL: {leg}/{name}: the reason fragment is not in {rid}'s "
                                 f"module: {frag!r}")

    # 3. one action per outcome, no outcome uncovered, no duplicate slug
    pairs = {(a["leg"], a["outcome"]) for a in ACTIONS}
    want = {(l, o) for l, outs in OUTCOMES.items() for o in outs}
    if pairs != want:
        raise SystemExit(f"FATAL: uncovered {sorted(want - pairs)}; not an outcome "
                         f"{sorted(pairs - want)}")
    if len(pairs) != len(ACTIONS):
        raise SystemExit("FATAL: two actions share a (leg, outcome)")
    slugs = [a["slug"] for a in ACTIONS]
    if len(set(slugs)) != len(slugs):
        dup = sorted({s for s in slugs if slugs.count(s) > 1})
        raise SystemExit(f"FATAL: duplicate action slug(s) {dup}")

    # 4. every technique source quote is verbatim in the file it names
    for a in ACTIONS:
        if not a["sources"]:
            raise SystemExit(f"FATAL: {a['slug']} has no technique source")
        for doc_id, locator, quote in a["sources"]:
            if doc_id not in SOURCES:
                raise SystemExit(f"FATAL: {a['slug']}: unknown source {doc_id!r}")
            if quote not in repo_text(SOURCES[doc_id]):
                raise SystemExit(f"FATAL: {a['slug']}: the quote is not in "
                                 f"{SOURCES[doc_id]}: {quote!r}")

    # 5. every action carries a class the tables know, and every class carries both bands
    for a in ACTIONS:
        cls = a["technique_class"]
        if cls not in TECHNIQUE_CLASSES:
            raise SystemExit(f"FATAL: {a['slug']}: unknown technique_class {cls!r}; the "
                             f"classes are {sorted(TECHNIQUE_CLASSES)}")
        if cls not in NOTIONAL_BANDS:
            raise SystemExit(f"FATAL: technique_class {cls!r} has no band pair")
    for cls, (eff, cost) in NOTIONAL_BANDS.items():
        if cls not in TECHNIQUE_CLASSES:
            raise SystemExit(f"FATAL: NOTIONAL_BANDS names {cls!r}, which is not a class")
        if eff not in EFFORT_BANDS or cost not in COST_BANDS:
            raise SystemExit(f"FATAL: {cls!r} bands ({eff!r}, {cost!r}) are not legal values")

    # 6. the downstream table's quotes are verbatim in the record
    for up, rows in DOWNSTREAM.items():
        for code, nid, field, quote in rows:
            if code not in inds:
                raise SystemExit(f"FATAL: downstream {code!r} is not an indicator")
            text = (by_id[nid]["properties"] or {}).get(field) or ""
            if quote not in text:
                raise SystemExit(f"FATAL: downstream {up}->{code}: the quote is not in "
                                 f"{nid}.{field}: {quote!r}")
    return {"indicators": inds, "harness": harness}


def indicator_code(leg: str) -> str:
    """The indicator a leg measures. `A11-declared` is A11's declared leg; every other leg is
    its own code, including `G1-D`, which is an indicator (DD-036) and not a qualifier."""
    return "A11" if leg == "A11-declared" else leg


def construct_of(g: dict, code: str) -> tuple:
    """`(constructs, source)` from the DECOMPOSES_INTO edges that reach this indicator."""
    by_id = {n["id"]: n for n in g["nodes"]}
    ind_id = f"ind:{code}"
    edges = [e for e in g["edges"]
             if e["type"] == "DECOMPOSES_INTO" and e["to"] == ind_id
             and "AssessmentConstruct" in (by_id.get(e["from"], {}).get("labels") or [])]
    names = sorted({by_id[e["from"]]["properties"].get("name") for e in edges})
    src = "; ".join(f"`{e['from']}` -[DECOMPOSES_INTO]-> `{ind_id}` in {RECORD}" for e in edges)
    return names, src or f"no AssessmentConstruct decomposes into `{ind_id}` in {RECORD}"


def value_of(g: dict, leg: str, fails: dict) -> dict:
    """The computed value block. Nothing here is authored: every field is read from the
    matrices of the cycle of record or from an edge of the record itself."""
    code = indicator_code(leg)
    cycle = cycle_of_record()
    constructs, csrc = construct_of(g, code)
    n_out = len(OUTCOMES[leg])
    if leg in fails:
        n, total, path = fails[leg]
        vsrc = (f"{path} (cycle `{cycle}`, declared by {PUBLICATION}:snapshot_cycle): {n} of "
                f"{total} bodies carry the verdict `fail` on leg `{leg}`")
    else:
        n, total = 0, 0
        vsrc = (f"leg `{leg}` is on neither matrix of cycle `{cycle}` "
                f"({PUBLICATION}:snapshot_cycle), so no body fails it there")
    down = DOWNSTREAM.get(code, [])
    out = {
        "bodies_failing_now": n,
        "bodies_on_the_cycle_of_record": total,
        "bodies_failing_now_source": vsrc,
        "constructs_served": constructs,
        "constructs_served_source": csrc,
        "downstream_indicators": [c for c, _, _, _ in down],
        "downstream_indicators_source": "; ".join(
            f"`{nid}.{field}`: \"{q}\"" for _, nid, field, q in down) or NO_DOWNSTREAM,
    }
    if n_out > 1:
        out["bodies_failing_now_caveat"] = (
            f"a per-LEG count. `{leg}`'s rule has {n_out} failing outcomes, so this is an "
            f"upper bound for this action alone: it is the number of bodies failing the leg, "
            f"not the number failing on this outcome. The matrices of the cycle of record "
            f"carry verdicts, not reasons, so the per-outcome split is not derivable from "
            f"them.")
    return out


def build(g: dict) -> tuple:
    """`(nodes, edges)` for the prescription layer, computed from the record and the cycle of
    record. Deterministic: two runs over the same HEAD produce identical bytes."""
    from scan.rules import CURRENT
    validate(g)
    fails = matrix_fail_bodies(cycle_of_record())
    nodes, edges = [], []
    for a in ACTIONS:
        leg, code = a["leg"], indicator_code(a["leg"])
        rid = CURRENT[leg]
        cls = a["technique_class"]
        effort, cost = NOTIONAL_BANDS[cls]
        props = {
            "title": a["title"],
            "description": a["description"],
            "technique_source": [format_source(s) for s in a["sources"]],
            # The class, and the two bands it fixes. Neither band is authored per action; see
            # the module docstring for why a per-action figure would be the wrong instrument.
            "technique_class": cls,
            "effort_band": effort,
            "effort_source": notional_source(cls),
            "cost_band": cost,
            "cost_source": notional_source(cls),
            "band_note": BAND_NOTE,
            "verifies_by": rid,
            "leg": leg,
            "indicator_code": code,
            "outcome": a["outcome"],
            "applies_to_publisher": a["applies_to_publisher"],
            "value": value_of(g, leg, fails),
            "authored_by": a["task"] or TASK,
        }
        if a["class_reason"]:
            props["technique_class_reason"] = a["class_reason"]
        if a["applies_to_note"]:
            props["applies_to_note"] = a["applies_to_note"]
        if a["note"]:
            props["note"] = a["note"]
        nodes.append({"id": f"act:{a['slug']}", "labels": ["Action"], "properties": props})
        edges.append({"from": f"act:{a['slug']}", "type": "REMEDIATES", "to": f"ind:{code}",
                      "properties": {"outcome": a["outcome"],
                                     "rule_id": rid,
                                     "leg": leg,
                                     "reason_fragment": OUTCOMES[leg][a["outcome"]]}})
    return nodes, edges


def merge(g: dict, nodes: list, edges: list) -> dict:
    """Lay the prescription layer over the record, replacing this task's own nodes and edges
    and keeping every other node and edge whole. Order is the record's; new entries append."""
    new_nodes = {n["id"]: n for n in nodes}
    new_edges = {(e["from"], e["type"], e["to"]): e for e in edges}
    kept = [new_nodes[n["id"]] if n["id"] in new_nodes else n for n in g["nodes"]]
    have = {n["id"] for n in kept}
    kept += [n for n in nodes if n["id"] not in have]
    kept_e = []
    for e in g["edges"]:
        k = (e["from"], e["type"], e["to"])
        kept_e.append(new_edges[k] if k in new_edges else e)
    have_e = {(e["from"], e["type"], e["to"]) for e in kept_e}
    kept_e += [e for e in edges if (e["from"], e["type"], e["to"]) not in have_e]
    out = dict(g)
    out["nodes"], out["edges"] = kept, kept_e
    return out


def summary(nodes: list, edges: list) -> dict:
    from collections import Counter
    notional = [(n["id"], b) for n in nodes for b in ("effort", "cost")
                if n["properties"][f"{b}_source"].startswith(NOTIONAL_PREFIX)]
    return {
        "actions": len(nodes),
        "remediates_edges": len(edges),
        "legs": len(OUTCOMES),
        "outcomes": sum(len(v) for v in OUTCOMES.values()),
        "technique_sources": sum(len(n["properties"]["technique_source"]) for n in nodes),
        "distinct_source_documents": len({s.split(" (doc_id ")[0]
                                          for n in nodes
                                          for s in n["properties"]["technique_source"]}),
        "bands_from_a_document_locator": sum(
            1 for n in nodes for b in ("effort", "cost")
            if not n["properties"][f"{b}_source"].startswith(NOTIONAL_PREFIX)),
        "bands_notional": len(notional),
        "actions_per_class": dict(sorted(
            Counter(n["properties"]["technique_class"] for n in nodes).items())),
        "effort_bands": dict(sorted(
            Counter(n["properties"]["effort_band"] for n in nodes).items())),
        "cost_bands": dict(sorted(
            Counter(n["properties"]["cost_band"] for n in nodes).items())),
        "actions_with_a_class_reason": sorted(
            n["id"] for n in nodes if "technique_class_reason" in n["properties"]),
        "actions_not_for_a_publisher": sorted(
            n["id"] for n in nodes if not n["properties"]["applies_to_publisher"]),
        "actions_per_leg": dict(sorted(Counter(n["properties"]["leg"] for n in nodes).items())),
        "bodies_failing_now_per_leg": {
            leg: next(n["properties"]["value"]["bodies_failing_now"]
                      for n in nodes if n["properties"]["leg"] == leg)
            for leg in sorted(OUTCOMES)},
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--task", default=WRITEBACK_TASK,
                    help="the task that ORDERED this run, recorded on the `framework_writeback` "
                         "event")
    ap.add_argument("--check", action="store_true",
                    help="validate the table against the rules, the sources and the record; "
                         "write nothing and print the summary")
    a = ap.parse_args(argv)

    import framework_writeback as fw
    g = fw.load()
    nodes, edges = build(g)
    s = summary(nodes, edges)
    if a.check:
        print(json.dumps({"validated": True, "summary": s}, indent=1, ensure_ascii=False))
        return 0
    merged = merge(g, nodes, edges)
    changes = {"actions_added": [n["id"] for n in nodes],
               "remediates_added": [f"{e['from']}->{e['to']} ({e['properties']['outcome']})"
                                    for e in edges],
               "summary": s}
    out = fw.save(merged, script=SCRIPT, task=a.task, changes=changes,
                  dry_run=a.dry_run)
    print(json.dumps({"summary": s,
                      "save": {k: v for k, v in out.items()
                               if k not in ("delta", "changes", "counts")}},
                     indent=1, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
