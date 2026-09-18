#!/usr/bin/env python3
"""The requirements layer: `AssessmentTool` and `Precondition` nodes, and `REQUIRES` edges.

`cc_tasks/2026-09-18_requirements_layer.md` decisions 1 to 3, under DN-005 §2.2 (three ways to
measure) extended with the object each way needs, and DD-001 (every assertion citable).
**Zero spend, no network.** Every tool named here is documented on disk or named by the tool
map; nothing is fetched and no model is called.

**The shape is borrowed.** An expert system's rule base pairs a question with what answering it
requires. The record already held the question (the indicator), the test (the rule, or the open
tool its tier names) and the fix (the `Action`). It lacked the requirement: the thing a body
must have, buy or grant — or this project must build — before the test can run. CIS Benchmarks
record it as *audit prerequisites*; Lighthouse marks audits that need an authenticated origin;
the Search Console class of tool is the canonical measurement that needs the site owner's
account. One node type per side, an access class and a cost, linked from every test that needs
it.

**Why `AssessmentTool` and not `Tool`.** `Tool` is a KG node type (`kg/schema.yaml`: "Software
that implements one or more Measures"), and the literature extraction has minted 262 of them
(Search Console, Bing Webmaster Tools, extruct, slsa-verifier, ...). The framework loader owns
its labels by DETACH DELETE-and-rebuild, and `build_projection.py` owns the KG labels the same
way, so one label in both layers would be deleted by whichever projector ran second. The
schema's own comment on the assessment layer names the precedent: "Labels are prefixed
`Assessment*` because the KG's own `Framework` label is taken". `Precondition` collides with
nothing and keeps the task's name.

**Routes.** An edge's `route` names one way to close the test. Edges from one indicator that
share a route are needed TOGETHER (Bing's AI Performance report AND a verified site); two routes
are ALTERNATIVES (the agency's own edge logs, OR a Cloudflare zone's crawler dashboard). A
platform-account tool never travels without the account on its route.

**`closes`** says which gap the edge closes: `tier` (the indicator has no harness at all),
`unmeasured_half` (a harness leg whose tier note records a clause the rule does not read), or
`coverage` (a row of the tool map §3: the rule reads the clause on the surface fetched, and the
tool would carry it across the site). The third kind is how the tool map's §3 becomes a view of
the record rather than a hand-kept list (decision 5).

**Cost is notional, by kind, exactly as action bands are by technique class** (`cc_tasks/
2026-09-17_notional_bands.md`, DN-005 ADDENDUM_03). No document on disk states what running
any of these tools costs a federal statistical publisher, so the band is fixed by the tool's
kind through `NOTIONAL_TOOL_COST` and its source says so: `notional:tool_kind:<kind>, task
2026-09-18_requirements_layer`. `tooling` — the band no action class reached — is the band an
open-source tool takes: somebody installs and runs it.

**Error classes.** The body view (decision 4) must say what would let the harness observe a cell
it could not. A `Precondition` may carry `unlocks_error_classes`, drawn only from the classes
`scan.errors.CLASSES` counts as BLIND. The BLIND classes no precondition unlocks are listed in
`UNMAPPED_ERROR_CLASSES` with why, and a test holds the two lists to the harness's own map.

    /opt/anaconda3/bin/python3 scripts/tag_requirements.py [--check] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

TASK = "cc_tasks/2026-09-18_requirements_layer.md"
SCRIPT = "tag_requirements"
RECORD = "framework/ai_readiness_framework.json"

#: The tool map as it stood when this task began, before decision 5 made its §3 a view of the
#: record. A citation to a row of it is a citation to that commit, checked with `git show`, so
#: regenerating §3 from the graph cannot make a source cite itself.
TOOL_MAP_COMMIT = "76467ac"
TOOL_MAP_PATH = "docs/design/scan_tool_map.md"
TOOL_MAP_AT = f"{TOOL_MAP_PATH} §3 at commit {TOOL_MAP_COMMIT}"

# ------------------------------------------------------------------------- the enumerations

TOOL_KINDS = ("open_source", "hosted_free", "hosted_paid", "platform_account",
              "agency_internal")
#: The five the task named, and a sixth. `publisher_grant` exists because two BLIND error
#: classes need it and none of the five describes it: `refused` (the edge answered 401/403/429
#: to an identified client on a robots-permitted path) and `robots_disallowed` (robots.txt
#: forbids this client the path). What would let the harness see either is the publisher
#: admitting the identified client — not an account the harness logs into, not a script on a
#: page, not records the agency holds, not a set this project builds, not a second cycle. The
#: notional-bands precedent is the bar: no new class without a second thing needing it.
PRECONDITION_KINDS = ("site_owner_account", "page_script", "agency_records", "benchmark_set",
                      "second_cycle", "publisher_grant")
WHO_PROVIDES = ("publisher", "this_project", "third_party")
CLOSES = ("tier", "unmeasured_half", "coverage")
COST_BANDS = ("none", "tooling", "staff_time", "procurement")
SOURCE_KINDS = ("corpus", "record", "tool_map", "repo_file")

#: The kind fixes the band (see the module docstring); the table is the only place a band is
#: decided. `platform_account` is `none` because the platforms named here (Bing Webmaster
#: Tools, Cloudflare's AI Crawl Control) are free to the site owner; what they cost is the
#: owner's account, and that is a Precondition on the same route, not a price.
NOTIONAL_TOOL_COST = {
    "open_source": "tooling",
    "hosted_free": "none",
    "hosted_paid": "procurement",
    "platform_account": "none",
    "agency_internal": "staff_time",
}
#: Who supplies a tool's reading, by kind — the same question `who_provides` answers on a
#: Precondition, so the query can print one column for both. A tool this project installs or
#: queries is this project's to run; a platform account's report is read by the account
#: holder, which is the publisher; an agency-internal tool is the agency's.
WHO_RUNS_BY_KIND = {
    "open_source": "this_project",
    "hosted_free": "this_project",
    "hosted_paid": "this_project",
    "platform_account": "publisher",
    "agency_internal": "publisher",
}
NOTIONAL_PREFIX = "notional:tool_kind:"
NOTIONAL_TASK = "task 2026-09-18_requirements_layer"
BAND_NOTE = ("Notional relative cost by tool kind. It orders requirements against each other; "
             "it does not price a licence, an account or anyone's time, and an agency adjusts "
             "it for its own platform, staffing and procurement path.")
NONE_ON_DISK = "none_on_disk"


def notional_source(kind: str) -> str:
    return f"{NOTIONAL_PREFIX}{kind}, {NOTIONAL_TASK}"


#: doc_id -> path. A tool or edge citing a corpus document cites one of these, and the quote is
#: checked verbatim (whitespace-collapsed; PDFs through pypdf) before anything is written.
DOCS = {
    "wayback-cdx-server-api-readme": "corpus/tools/wayback-cdx-server/README.md",
    "oasdiff-readme": "corpus/tools/oasdiff/README.md",
    "aidrin-hiniduma-2024": "corpus/pilot/aidrin-hiniduma-2024.pdf",
    "slsa-specification-v1-0": "corpus/crosswalk/slsa-specification-v1-0.md",
    "bing-ai-performance-public-preview-2026":
        "corpus/kernel/bing-ai-performance-public-preview-2026.md",
    "cloudflare-ai-crawl-control": "corpus/kernel/cloudflare-ai-crawl-control.md",
    "cloudflare-ai-crawl-control-manage-crawlers":
        "corpus/kernel/cloudflare-ai-crawl-control-manage-crawlers.md",
    "aggarwal-2024-geo-generative-engine-optimization":
        "corpus/kernel/aggarwal-2024-geo-generative-engine-optimization.pdf",
    "extruct-readme": "corpus/kernel/extruct-readme.md",
    "scrapy-docs-landing": "corpus/kernel/scrapy-docs-landing.md",
}

# ------------------------------------------------------------------------------ the tools
#
# `doc` is a corpus citation `("corpus", doc_id, locator, quote)`, or None with `doc_note`
# saying why no document is on disk. The four without one are the ones the tool map §3 named
# and the corpus never admitted; they stand on the tool-map row their edge cites.

TOOLS = [
    {"slug": "wayback-cdx-server", "name": "Wayback Machine CDX Server API",
     "kind": "hosted_free",
     "doc": ("corpus", "wayback-cdx-server-api-readme", "'Basic Usage'",
             "The most simple query and the only required param for the CDX server is the "
             "**url** param")},
    {"slug": "oasdiff", "name": "oasdiff", "kind": "open_source",
     "doc": ("corpus", "oasdiff-readme", "opening description",
             "Command-line tool to compare and detect breaking changes in OpenAPI specs.")},
    {"slug": "aidrin", "name": "AIDRIN (AI Data Readiness Inspector) PyPI package",
     "kind": "open_source",
     "doc": ("corpus", "aidrin-hiniduma-2024", "the paper's tool section",
             "Users can install the AIDRIN PyPI package via the command line and use it for "
             "data readiness assessment"),
     "note": ("The paper's reference [1] locates the package on TestPyPI, not the production "
              "index; `ind:C5.tier_note` records the same caveat.")},
    {"slug": "slsa-verifier", "name": "slsa-verifier", "kind": "open_source",
     "doc": ("corpus", "slsa-specification-v1-0", "'Verifying artifacts'",
             "Tooling for organizations that need to protect first-party software is also "
             "available, such as [slsa-verifier](https://github.com/slsa-framework/slsa-verifier)."),
     "note": ("`ind:F6.tier_note` says the tool map §3 and the open-tool record name no tool "
              "for F6. The SLSA specification on disk names one, in two places; this node is "
              "that name.")},
    {"slug": "bing-webmaster-tools-ai-performance",
     "name": "Bing Webmaster Tools, AI Performance report", "kind": "platform_account",
     "doc": ("corpus", "bing-ai-performance-public-preview-2026", "'Page-level citation activity'",
             "Shows citation counts for specific URLs from your site, making it easy to see "
             "which individual pages are most often referenced across AI-generated answers "
             "during the selected date range."),
     "note": ("Public preview (February 2026). It counts citations of the owner's OWN pages "
              "across Microsoft Copilot and Bing's AI summaries; it cannot say which aggregator "
              "was cited instead, which is C4's other half.")},
    {"slug": "cloudflare-ai-crawl-control", "name": "Cloudflare AI Crawl Control",
     "kind": "platform_account",
     "doc": ("corpus", "cloudflare-ai-crawl-control", "overview",
             "AI Crawl Control (formerly AI Audit) gives you visibility into which AI services "
             "are accessing your content, and provides tools to manage access according to your "
             "preferences."),
     "note": "Reaches only a host whose edge is a Cloudflare zone."},
    {"slug": "perplexity-ai", "name": "Perplexity.ai", "kind": "hosted_paid",
     "doc": ("corpus", "aggarwal-2024-geo-generative-engine-optimization", "section 3.1 and C.1",
             "Perplexity.ai, which is a commercially deployed generative engine"),
     "kind_reason": ("decision 2 of the task: a definition that names a generative engine "
                     "requires a hosted_paid or platform_account tool; querying one at the scale "
                     "a product-by-product evaluation needs is a paid API use, and no document "
                     "on disk states its price."),
     "note": ("The one deployed generative engine a corpus document evaluates by name. The "
              "GEO paper queried it with uploaded sources because it 'does not allow the user "
              "to specify source URLs'; a C4 run asks the opposite question and needs its "
              "unconstrained answers.")},
    {"slug": "extruct", "name": "extruct", "kind": "open_source",
     "doc": ("corpus", "extruct-readme", "opening description",
             "*extruct* is a library for extracting embedded metadata from HTML markup.")},
    {"slug": "scrapy", "name": "Scrapy", "kind": "open_source",
     "doc": ("corpus", "scrapy-docs-landing", "opening description",
             "used to crawl websites and extract structured data from their pages")},
    {"slug": "ultimate-sitemap-parser", "name": "ultimate-sitemap-parser (usp)",
     "kind": "open_source", "doc": None,
     "doc_note": ("not admitted to the corpus. It is already a dependency of this harness — "
                  "the `sitemap` collector imports `usp` (docs/design/scan_tool_map.md §1) — "
                  "and the tool map §3 row its edge cites is the source that names it.")},
    {"slug": "openapi-spec-validator", "name": "openapi-spec-validator", "kind": "open_source",
     "doc": None,
     "doc_note": "not admitted to the corpus; named by the tool map §3 row its edge cites."},
    {"slug": "prance", "name": "prance", "kind": "open_source", "doc": None,
     "doc_note": "not admitted to the corpus; named by the tool map §3 row its edge cites."},
    {"slug": "catalog-data-gov-ckan-api", "name": "catalog.data.gov CKAN action API",
     "kind": "hosted_free", "doc": None,
     "doc_note": ("not admitted to the corpus; named by the tool map §3 row its edge cites, "
                  "which also records the interface as unavailable."),
     "note": ("The tool map §3 recorded every CKAN action endpoint answering HTTP 404 on "
              "2026-09-08; this node names the interface a D4 data.gov leg would read, and "
              "nothing here re-checked it (the task's network is `none`).")},
]

# ------------------------------------------------------------------------ the preconditions
#
# `description` is this layer's own sentence; what grounds each precondition is the citation on
# every edge that reaches it. `unlocks_source` grounds each error-class mapping in the harness's
# own class notes, one citation per class.

_ERRORS = "assessment/harness/scan/errors.py"

PRECONDITIONS = [
    {"slug": "edge-and-crawler-request-logs", "name": "Edge/WAF and crawler request logs",
     "kind": "agency_records", "who_provides": "publisher",
     "description": ("The host's edge, WAF or bot-manager decisions and its request logs for "
                     "identified AI crawlers, for the product path, shared with the assessor.")},
    {"slug": "cloudflare-zone-account", "name": "The publisher's Cloudflare zone",
     "kind": "site_owner_account", "who_provides": "publisher",
     "description": ("Access to the Cloudflare account and zone that fronts the host, from "
                     "which the AI Crawl Control dashboard is read.")},
    {"slug": "bing-webmaster-tools-verified-site",
     "name": "A verified site in Bing Webmaster Tools", "kind": "site_owner_account",
     "who_provides": "publisher",
     "description": ("The publisher's site verified in Bing Webmaster Tools, with the AI "
                     "Performance report read by or shared with the assessor.")},
    {"slug": "generative-engine-query-set", "name": "Generative-engine query set",
     "kind": "benchmark_set", "who_provides": "this_project",
     "description": ("Per product, the questions a user would put to a generative engine whose "
                     "answer should cite the product, with the authoritative URL each answer "
                     "should cite.")},
    {"slug": "product-question-benchmark", "name": "Per-product question benchmark",
     "kind": "benchmark_set", "who_provides": "this_project",
     "description": ("Per product, a versioned question set whose answers are published values, "
                     "scored against what a retrieval-paired model returns.")},
    {"slug": "vintage-disambiguation-set", "name": "Vintage disambiguation set",
     "kind": "benchmark_set", "who_provides": "this_project",
     "description": ("Per product, questions that name a vintage, with the vintage and value "
                     "each should retrieve.")},
    {"slug": "entailment-probe-set", "name": "Entailment probe set, re-aimed at products",
     "kind": "benchmark_set", "who_provides": "this_project",
     "description": ("The probe protocol's prompts re-aimed at a data product, with the product "
                     "text each model statement is judged against for entailment.")},
    {"slug": "adversarial-bank", "name": "Standing adversarial bank", "kind": "benchmark_set",
     "who_provides": "this_project",
     "description": ("Vintage traps, confusable series, unit traps, noise misreads and "
                     "suppression probes, per product, versioned.")},
    {"slug": "series-break-cases", "name": "Series-break cases", "kind": "benchmark_set",
     "who_provides": "this_project",
     "description": ("Series with a documented break in collection instrument or protocol, and "
                     "the comparison across each break an AI consumer must qualify.")},
    {"slug": "second-scan-cycle", "name": "A second scan cycle", "kind": "second_cycle",
     "who_provides": "this_project",
     "description": ("A later cycle of this harness over the same bodies: the second "
                     "measurement a comparison needs, and the re-observation a server-side "
                     "failure at capture time needs."),
     "unlocks_error_classes": ["dns", "timeout", "connection_reset", "http_5xx"],
     "unlocks_source": [("repo_file", _ERRORS, "a server error is not a product property"),
                        ("repo_file", _ERRORS, "no response within the configured timeout"),
                        ("repo_file", _ERRORS, "the host name did not resolve"),
                        ("repo_file", _ERRORS, "the peer closed the connection (TCP reset)")]},
    {"slug": "second-evaluation-run", "name": "A second evaluation run", "kind": "second_cycle",
     "who_provides": "this_project",
     "description": ("A scheduled re-run of the golden question set against the product "
                     "surface, so a baseline delta exists to alarm on.")},
    {"slug": "threshold-preregistration-records",
     "name": "Threshold pre-registration records", "kind": "agency_records",
     "who_provides": "publisher",
     "description": ("The agency's dated record that each evaluation's pass/fail threshold "
                     "existed before the results it judged.")},
    {"slug": "held-out-rotation-records", "name": "Held-out evaluation-set rotation records",
     "kind": "agency_records", "who_provides": "publisher",
     "description": "The agency's record of its held-out sets and their rotation schedule."},
    {"slug": "eval-failure-closure-records", "name": "Evaluation-failure closure records",
     "kind": "agency_records", "who_provides": "publisher",
     "description": ("The agency's tracked history from a failed evaluation to its fix in the "
                     "product, with the re-test and the time to closure.")},
    {"slug": "release-validation-records", "name": "Pre-release validation records",
     "kind": "agency_records", "who_provides": "publisher",
     "description": ("The agency's record that each release passed its expectation suite "
                     "before it went live.")},
    {"slug": "staging-regression-records", "name": "Staging regression records",
     "kind": "agency_records", "who_provides": "publisher",
     "description": ("The agency's record that an AI-consumer regression ran on the staging "
                     "surface before a major change was promoted.")},
    {"slug": "published-conformance-and-evaluation-report",
     "name": "The published conformance and evaluation report", "kind": "agency_records",
     "who_provides": "publisher",
     "description": ("The agency's report of spec conformance and fit-for-use evaluation for "
                     "the product, located for the assessor.")},
    {"slug": "evaluation-set-version-records", "name": "Evaluation-set version records",
     "kind": "agency_records", "who_provides": "publisher",
     "description": ("The agency's versions of its evaluation sets and rubrics, and which "
                     "version each published result came from.")},
    {"slug": "publisher-admits-the-identified-client",
     "name": "The publisher admits the identified client", "kind": "publisher_grant",
     "who_provides": "publisher",
     "description": ("The host serves this project's identified, robots-compliant client on the "
                     "product paths: robots.txt permits it and the edge does not refuse it."),
     "unlocks_error_classes": ["refused", "robots_disallowed"],
     "unlocks_source": [("repo_file", _ERRORS, "robots-permitted path: declined, not measured"),
                        ("repo_file", _ERRORS, "forbidden to look at a URL inside the product")]},
]

#: BLIND classes no precondition unlocks, and why. Held to `scan.errors.CLASSES` by the suite.
UNMAPPED_ERROR_CLASSES = {
    "parse_error": ("a response arrived and could not be read; what fixes it is the "
                    "publisher's response, which is an action, not a grant or a tool"),
    "redirect_loop": ("the server redirected past the maximum; the fix is the publisher's "
                      "redirect chain, which is an action, not a grant or a tool"),
    "collector_unavailable": ("the harness's own collector raised; the fix is this project's "
                              "code, and no requirement of the body's stands in the way"),
    "unknown": ("the harness's error map does not name the failure; it is counted per cycle "
                "until it is named, and nothing can be said to unlock what is not named"),
}

# ------------------------------------------------------------------------------- the scope
#
# Harness legs whose `tier_note` records an unmeasured half, each with the verbatim words that
# record it. The suite checks the other direction too: a note that says "unmeasured" or "not
# measured" and is missing here is an indicator this layer silently skipped.
UNMEASURED_HALF = {
    "A11": "The enforced and observed layers need edge or WAF logs and crawler request logs",
    "B1": "are not measured",
    "B2": "is recorded as unmeasured on every verdict",
    "B4": "The suppression-rules clause has no field in any admitted document",
    "B5": "The cross-vintage half is `unmeasured_until: second cycle with term codes`",
    "D3": "is not measured",
    "G4": "are recorded as unmeasured",
}

#: In scope, and no requirement closes the gap. Written onto the node as
#: `requirement_none_reason`, so the graph says it and not only this file.
NONE_REASONS = {
    "B1": ("The unmeasured half is whether the linked dictionary or the listed variables are "
           "'comprehensive', a judgement about their contents. No admitted document defines a "
           "test for it, so what stands in the way is an instrument this project has not "
           "specified — not a tool, an account or anything the body holds."),
    "B2": ("The 'versioned' clause has no field in any admitted document. What is missing is a "
           "standard to test against, not a tool or a grant."),
    "B4": ("The suppression-rules clause has no field in any admitted document (the failed "
           "search is on `ind:G5.tier_unassigned_reason`). What is missing is a standard, not a "
           "tool or a grant."),
    "D3": ("Whether the lineage reaches from collection through processing is readable by "
           "walking `wasDerivedFrom` on the same catalog records the rule already fetches. That "
           "is a rule this project would write, not a requirement of the body's."),
    "G4": ("The statutory-mandate and statistical-versus-administrative clauses have no field "
           "in any admitted document. What is missing is a standard, not a tool or a grant."),
    "G1-O": ("Measured: the G1 instrument exists and judged it (DD-036, `measurement_status: "
             "measured`). Nothing stands between it and a verdict."),
}


def _rec(node, field, quote):
    return ("record", node, field, quote)


def _tm(row, quote):
    return ("tool_map", row, quote)


def _c(doc_id, locator, quote):
    return ("corpus", doc_id, locator, quote)


#: One row per edge. `test` names the test the requirement makes possible; `route` groups the
#: edges needed together (module docstring).
REQUIRES = [
    # ---- tier O: the open tool the tier source names
    {"code": "A7", "to": "tool:wayback-cdx-server", "closes": "tier", "route": "wayback_cdx",
     "test": "a product or vintage URL's capture history and the status it answered at each capture",
     "for_clause": "Persistent URLs/DOIs for products and vintages",
     "source": _c("wayback-cdx-server-api-readme", "'Filtering'",
                  "Results may be filtered by timestamp using **from=** and **to=** params"),
     "note": ("Reaches the persistent-URL half. A DOI's persistence is its resolver's, and no "
              "resolver's documentation is on disk, so the DOI clause has no requirement here "
              "(`ind:A7.tier_note`).")},
    {"code": "F3", "to": "tool:wayback-cdx-server", "closes": "tier", "route": "wayback_cdx",
     "test": "the endpoints captured under a product path in the prior vintage, joined to the current vintage's",
     "for_clause": "endpoints survive a new vintage",
     "source": _c("wayback-cdx-server-api-readme", "'Url Match Scope'",
                  "**matchType=prefix** will return results for all results under the path"),
     "note": ("Reaches the endpoints clause only. Series identifiers and geography codes live "
              "in response bodies, which the index locates and does not carry "
              "(`ind:F3.tier_note`).")},
    {"code": "F2", "to": "tool:oasdiff", "closes": "tier", "route": "oasdiff_two_releases",
     "test": "breaking changes between two dated OpenAPI descriptions of the product's API",
     "for_clause": "compatibility checked mechanically",
     "source": _c("oasdiff-readme", "opening description",
                  "Command-line tool to compare and detect breaking changes in OpenAPI specs.")},
    {"code": "F2", "to": "pre:second-scan-cycle", "closes": "tier",
     "route": "oasdiff_two_releases",
     "test": "breaking changes between two dated OpenAPI descriptions of the product's API",
     "for_clause": "API/schema changes are versioned",
     "source": _rec("spec:F2", "note", "Becomes collectible once the scan runs twice.")},
    {"code": "C5", "to": "tool:aidrin", "closes": "tier", "route": "aidrin",
     "test": "the product scored on AIDRIN's published data-readiness dimensions",
     "for_clause": "Product scored against published AI-data-readiness metrics",
     "source": _c("aidrin-hiniduma-2024", "the paper's tool section",
                  "Users can install the AIDRIN PyPI package via the command line and use it "
                  "for data readiness assessment")},
    {"code": "F6", "to": "tool:slsa-verifier", "closes": "tier", "route": "slsa_verifier",
     "test": "a published provenance attestation verified against the released artifact",
     "for_clause": "Signed releases / provenance attestations",
     "source": _c("slsa-specification-v1-0", "'Consumer'",
                  "Client-side verification tooling can be either standalone, such as "
                  "[slsa-verifier](https://github.com/slsa-framework/slsa-verifier), or built "
                  "into the package ecosystem client.")},
    # ---- evaluations: the set this project would build, and the engine where one is named
    {"code": "C1", "to": "pre:product-question-benchmark", "closes": "tier",
     "route": "benchmark",
     "test": "answer accuracy of a retrieval-paired model against published values",
     "for_clause": "Benchmark question set per product",
     "source": _rec("ind:C1", "indicator", "Benchmark question set per product")},
    {"code": "C2", "to": "pre:entailment-probe-set", "closes": "tier", "route": "probe_protocol",
     "test": "entailment of model statements about the product from the product's own text",
     "for_clause": "Entailment-judged: do model statements about the product entail from product text?",
     "source": _rec("ind:C2", "tier_note",
                    "The definition names the probe protocol, 're-aimed', as the instrument; it "
                    "has not been re-aimed at a data product.")},
    {"code": "C3", "to": "pre:vintage-disambiguation-set", "closes": "tier", "route": "benchmark",
     "test": "whether retrieval returns the vintage a question asks for",
     "for_clause": "does retrieval return the vintage asked for?",
     "source": _rec("ind:C3", "indicator",
                    "Version/vintage disambiguation: does retrieval return the vintage asked for?")},
    {"code": "C4", "to": "tool:bing-webmaster-tools-ai-performance", "closes": "tier",
     "route": "bing_ai_performance",
     "test": "which of the product's pages AI answers cite, and how often",
     "for_clause": "Generative engines citing the product cite the authoritative page (not aggregators)",
     "source": _c("bing-ai-performance-public-preview-2026", "introduction",
                  "For the first time, you can understand how often your content is cited in "
                  "generative answers, with clear visibility into which URLs are referenced"),
     "note": ("Covers Microsoft's AI surfaces only, and counts the owner's own citations; "
              "whether an aggregator was cited INSTEAD needs the engine route.")},
    {"code": "C4", "to": "pre:bing-webmaster-tools-verified-site", "closes": "tier",
     "route": "bing_ai_performance",
     "test": "which of the product's pages AI answers cite, and how often",
     "for_clause": "Generative engines citing the product cite the authoritative page (not aggregators)",
     "source": _c("bing-ai-performance-public-preview-2026", "'Extending Search Insights to AI Answers'",
                  "Bing Webmaster Tools has long helped website owners understand indexing, "
                  "crawl health, and search performance.")},
    {"code": "C4", "to": "tool:perplexity-ai", "closes": "tier", "route": "engine_queries",
     "test": "whether a generative engine's answer about the product cites the agency page or an aggregator",
     "for_clause": "Generative engines citing the product cite the authoritative page (not aggregators)",
     "source": _c("aggarwal-2024-geo-generative-engine-optimization", "section 3.1",
                  "Perplexity.ai, which is a commercially deployed generative engine")},
    {"code": "C4", "to": "pre:generative-engine-query-set", "closes": "tier",
     "route": "engine_queries",
     "test": "whether a generative engine's answer about the product cites the agency page or an aggregator",
     "for_clause": "Generative engines citing the product cite the authoritative page (not aggregators)",
     "source": _rec("spec:C4-auto", "note",
                    "The AUTO leg needs a generative engine's citations as input, which is the "
                    "EVAL half of the indicator.")},
    {"code": "E6", "to": "pre:product-question-benchmark", "closes": "tier", "route": "benchmark",
     "test": "failures of the C1 to C3 evaluations localized to retrieval, vintage, metadata or model",
     "for_clause": "Discrepancy taxonomy localizing failures to retrieval / vintage / metadata / model",
     "source": _rec("ind:E6", "tier_note", "it presupposes the C1 to C3 evaluations")},
    {"code": "E6", "to": "pre:vintage-disambiguation-set", "closes": "tier", "route": "benchmark",
     "test": "failures of the C1 to C3 evaluations localized to retrieval, vintage, metadata or model",
     "for_clause": "Discrepancy taxonomy localizing failures to retrieval / vintage / metadata / model",
     "source": _rec("ind:E6", "tier_note", "it presupposes the C1 to C3 evaluations")},
    {"code": "E8", "to": "pre:product-question-benchmark", "closes": "tier", "route": "benchmark",
     "test": "a versioned golden question set re-run against the product surface",
     "for_clause": "Versioned golden question/answer sets re-run on schedule against the product surface",
     "source": _rec("ind:E8", "indicator",
                    "Versioned golden question/answer sets re-run on schedule against the "
                    "product surface")},
    {"code": "E8", "to": "pre:second-evaluation-run", "closes": "tier", "route": "benchmark",
     "test": "a versioned golden question set re-run against the product surface",
     "for_clause": "baseline deltas alarmed",
     "source": _rec("ind:E8", "indicator", "baseline deltas alarmed")},
    {"code": "E9", "to": "pre:adversarial-bank", "closes": "tier", "route": "benchmark",
     "test": "break modes of AI consumers against a standing adversarial bank",
     "for_clause": "Standing adversarial bank: vintage traps, confusable series, unit traps, DP-noise misreads, suppression probes",
     "source": _rec("ind:E9", "indicator", "Reported as break modes, not just pass rates")},
    {"code": "G2", "to": "pre:vintage-disambiguation-set", "closes": "tier", "route": "benchmark",
     "test": "whether retrieval returns the vintage a question asks for",
     "for_clause": "EVAL: vintage disambiguation (ties C3)",
     "source": _rec("ind:G2", "tier_note",
                    "the reading the definition asks for is C3's evaluation"),
     "note": ("The declared half — revision status machine-readable per value — is a "
              "structured-field test no rule makes yet; it needs a rule, not a requirement.")},
    # ---- judged readings
    {"code": "E1", "to": "pre:published-conformance-and-evaluation-report", "closes": "tier",
     "route": "agency_report",
     "test": "a reading of the agency's report for conformance kept apart from evaluation",
     "for_clause": "reported separately from fit-for-use evals (EVAL set)",
     "source": _rec("ind:E1", "tier_note",
                    "the reading is of a published report, not a served surface")},
    {"code": "E3", "to": "pre:evaluation-set-version-records", "closes": "tier",
     "route": "agency_records",
     "test": "a reading of which evaluation-set version each result came from",
     "for_clause": "results never pooled across versions",
     "source": _rec("ind:E3", "tier_note", "a pass needs the agency's records")},
    {"code": "G6", "to": "pre:series-break-cases", "closes": "tier", "route": "break_cases",
     "test": "whether an AI consumer comparing values across a break surfaces the break",
     "for_clause": "an AI system asked to compare values across a break must surface the break",
     "source": _rec("ind:G6", "tier_note",
                    "The consumer-side half is a G1-style preservation test"),
     "note": ("The declared half — the versioned epoch carried as metadata — is a "
              "structured-field test no rule makes yet; it needs a rule, not a requirement.")},
    # ---- declarations: only the agency can say
    {"code": "E2", "to": "pre:threshold-preregistration-records", "closes": "tier",
     "route": "agency_records", "test": "the order of threshold and result, from the agency's records",
     "for_clause": "pre-registered before results",
     "source": _rec("ind:E2", "tier_source",
                    "the agency's own timestamps are the only record of that order")},
    {"code": "E4", "to": "pre:held-out-rotation-records", "closes": "tier",
     "route": "agency_records", "test": "whether a held-out rotation exists, from the agency's records",
     "for_clause": "Public eval sets have a held-out rotation",
     "source": _rec("ind:E4", "tier_source",
                    "whether a rotation exists is a fact only the agency holds")},
    {"code": "E7", "to": "pre:eval-failure-closure-records", "closes": "tier",
     "route": "agency_records", "test": "mean time to closure over the agency's own history",
     "for_clause": "mean-time-to-closure tracked",
     "source": _rec("ind:E7", "tier_source",
                    "mean time to closure is measured over the agency's own ticket history")},
    {"code": "F1", "to": "pre:release-validation-records", "closes": "tier",
     "route": "agency_records", "test": "whether each release passed its suite before going live",
     "for_clause": "before going live",
     "source": _rec("ind:F1", "tier_source",
                    "happened on the agency's side of publication and leaves nothing on the "
                    "served surface")},
    {"code": "F5", "to": "pre:staging-regression-records", "closes": "tier",
     "route": "agency_records", "test": "whether the regression ran before promotion",
     "for_clause": "AI-consumer regression run before promotion",
     "source": _rec("ind:F5", "tier_source", "only the agency can say that it ran")},
    # ---- harness legs: the half the rule records as unmeasured
    {"code": "A11", "to": "pre:edge-and-crawler-request-logs", "closes": "unmeasured_half",
     "route": "agency_logs",
     "test": "declared policy compared with what the edge enforced and which crawlers came",
     "for_clause": "enforced (edge/WAF/bot-management treatment) vs observed (actual crawler request logs)",
     "source": _rec("ind:A11", "tier_note", UNMEASURED_HALF["A11"])},
    {"code": "A11", "to": "tool:cloudflare-ai-crawl-control", "closes": "unmeasured_half",
     "route": "cloudflare_zone",
     "test": "declared policy compared with what the edge enforced and which crawlers came",
     "for_clause": "enforced (edge/WAF/bot-management treatment) vs observed (actual crawler request logs)",
     "source": _c("cloudflare-ai-crawl-control", "overview",
                  "**Monitor robots.txt compliance** - Track which crawlers follow your "
                  "directives and create enforcement rules")},
    {"code": "A11", "to": "pre:cloudflare-zone-account", "closes": "unmeasured_half",
     "route": "cloudflare_zone",
     "test": "declared policy compared with what the edge enforced and which crawlers came",
     "for_clause": "enforced (edge/WAF/bot-management treatment) vs observed (actual crawler request logs)",
     "source": _c("cloudflare-ai-crawl-control-manage-crawlers", "'Manage AI crawlers'",
                  "Log in to the [Cloudflare dashboard ↗](https://dash.cloudflare.com/), and "
                  "select your account and domain.")},
    {"code": "B5", "to": "pre:second-scan-cycle", "closes": "unmeasured_half",
     "route": "second_cycle",
     "test": "one concept carrying one identifier across two vintages",
     "for_clause": "across products/vintages",
     "source": _rec("spec:B5", "note",
                    "The cross-vintage half is unmeasured until a second cycle with term codes.")},
    # ---- coverage: the tool map §3 rows at the frozen commit
    {"code": "A5", "to": "tool:ultimate-sitemap-parser", "closes": "coverage",
     "route": "sitemap_walk", "test": "the product URLs a declared sitemap actually lists",
     "for_clause": "sitemap covers data products",
     "source": _tm("Sitemap crawl and URL inventory",
                   "`ultimate-sitemap-parser`, or `scrapy` for a bounded crawl")},
    {"code": "A5", "to": "tool:scrapy", "closes": "coverage", "route": "bounded_crawl",
     "test": "the product URLs a declared sitemap actually lists",
     "for_clause": "sitemap covers data products",
     "source": _tm("Sitemap crawl and URL inventory",
                   "`ultimate-sitemap-parser`, or `scrapy` for a bounded crawl")},
    {"code": "A6", "to": "tool:extruct", "closes": "coverage", "route": "extruct_at_scale",
     "test": "Dataset markup on every page of a URL inventory, not on the one surface fetched",
     "for_clause": "markup valid on product pages",
     "source": _tm("schema.org `Dataset` extraction at scale",
                   "`extruct` (already a dependency) driven over a URL inventory rather than "
                   "one page"),
     "note": "Driven over the URL inventory one of A5's two routes produces."},
    {"code": "A2", "to": "tool:openapi-spec-validator", "closes": "coverage",
     "route": "openapi_spec_validator",
     "test": "the served API description validated against the OpenAPI schema",
     "for_clause": "Documented public API",
     "source": _tm("OpenAPI / AsyncAPI detection and validation",
                   "`openapi-spec-validator`, `prance`")},
    {"code": "A2", "to": "tool:prance", "closes": "coverage", "route": "prance",
     "test": "the served API description validated against the OpenAPI schema",
     "for_clause": "Documented public API",
     "source": _tm("OpenAPI / AsyncAPI detection and validation",
                   "`openapi-spec-validator`, `prance`")},
    {"code": "D4", "to": "tool:catalog-data-gov-ckan-api", "closes": "coverage",
     "route": "federal_catalog",
     "test": "whether the product is registered in the federal catalog",
     "for_clause": "data.gov/agency inventory current",
     "source": _tm("Federal DCAT catalog presence",
                   "`catalog.data.gov`'s CKAN action endpoints answered HTTP 404 on 2026-09-08"),
     "note": "The interface was unavailable when the tool map recorded it (see the tool's note)."},
]

#: The tool map §3 row this task deliberately does not carry into the graph, and why. It names
#: no tool, account or record, and no indicator consumes it; an edge needs an indicator.
DROPPED_TOOL_MAP_ROWS = {
    "Response-header profile": (
        "names no tool (\"no library needed\") and no indicator that consumes it (\"No "
        "indicator consumes them yet\"). What it describes is a harness change this project "
        "would make, and a REQUIRES edge needs an indicator at its tail."),
}

# ------------------------------------------------------------------------- citation checks

_TEXT_CACHE: dict = {}


def _norm(s: str) -> str:
    return " ".join(str(s).split())


def _file_text(rel: str) -> str:
    if rel not in _TEXT_CACHE:
        p = REPO / rel
        if p.suffix == ".pdf":
            from pypdf import PdfReader
            _TEXT_CACHE[rel] = " ".join(pg.extract_text() or "" for pg in PdfReader(p).pages)
        else:
            _TEXT_CACHE[rel] = p.read_text(encoding="utf-8")
    return _TEXT_CACHE[rel]


def _tool_map_at_commit() -> str:
    key = f"git:{TOOL_MAP_COMMIT}"
    if key not in _TEXT_CACHE:
        r = subprocess.run(["git", "show", f"{TOOL_MAP_COMMIT}:{TOOL_MAP_PATH}"],
                           capture_output=True, text=True, cwd=REPO)
        if r.returncode != 0:
            raise SystemExit(f"FATAL: cannot read {TOOL_MAP_PATH} at {TOOL_MAP_COMMIT}: "
                             f"{r.stderr.strip()}")
        _TEXT_CACHE[key] = r.stdout
    return _TEXT_CACHE[key]


def citation_opens(c: tuple, g: dict) -> tuple:
    """`(True, "")` when the citation's quote is where it says; `(False, why)` otherwise.
    Whitespace is collapsed on both sides (a Markdown source wraps sentences across lines);
    nothing else is normalised, so a paraphrase fails."""
    kind = c[0]
    try:
        if kind == "corpus":
            _, doc_id, _loc, quote = c
            if doc_id not in DOCS:
                return False, f"unknown doc_id {doc_id!r}"
            path = REPO / DOCS[doc_id]
            if not path.exists():
                return False, f"{DOCS[doc_id]} is not on disk"
            ok = _norm(quote) in _norm(_file_text(DOCS[doc_id]))
            return ok, "" if ok else f"quote not in {DOCS[doc_id]}: {quote!r}"
        if kind == "record":
            _, node_id, field, quote = c
            node = next((n for n in g["nodes"] if n["id"] == node_id), None)
            if node is None:
                return False, f"no node {node_id!r}"
            ok = _norm(quote) in _norm((node["properties"] or {}).get(field) or "")
            return ok, "" if ok else f"quote not in {node_id}.{field}: {quote!r}"
        if kind == "tool_map":
            _, row, quote = c
            lines = [l for l in _tool_map_at_commit().splitlines()
                     if l.startswith(f"| {row} |")]
            if not lines:
                return False, f"no row {row!r} in {TOOL_MAP_AT}"
            ok = quote in lines[0]
            return ok, "" if ok else f"quote not in row {row!r}: {quote!r}"
        if kind == "repo_file":
            _, rel, quote = c
            ok = (REPO / rel).exists() and _norm(quote) in _norm(_file_text(rel))
            return ok, "" if ok else f"quote not in {rel}: {quote!r}"
    except Exception as exc:                          # noqa: BLE001 — reported as a failure
        return False, f"{type(exc).__name__}: {exc}"
    return False, f"unknown citation kind {kind!r}"


def format_citation(c: tuple) -> str:
    """One string per citation, in the shape `scripts/tag_prescriptions.py` writes technique
    sources in, so `mcp/airkg_tools._technique_address` parses a corpus one to its doc_id."""
    kind = c[0]
    if kind == "corpus":
        _, doc_id, loc, quote = c
        return f"{DOCS[doc_id]} (doc_id `{doc_id}`), {loc}: \"{quote}\""
    if kind == "record":
        _, node_id, field, quote = c
        return f"{RECORD} node `{node_id}` field `{field}`: \"{quote}\""
    if kind == "tool_map":
        _, row, quote = c
        return f"{TOOL_MAP_AT}, row '{row}': \"{quote}\""
    _, rel, quote = c
    return f"{rel}: \"{quote}\""


# ------------------------------------------------------------------------------ validation

def validate(g: dict) -> None:
    """Refuse before writing. Each check is a way the tables could be wrong that a reader of
    the record could not see."""
    from scan.errors import BLIND, CLASSES, HARNESS_CURRENT
    inds = {n["properties"]["code"]: n["properties"] for n in g["nodes"]
            if "AssessmentIndicator" in n["labels"]}
    tool_ids = {f"tool:{t['slug']}" for t in TOOLS}
    pre_ids = {f"pre:{p['slug']}" for p in PRECONDITIONS}
    problems = []

    def fail(msg):
        problems.append(msg)

    if len(tool_ids) != len(TOOLS) or len(pre_ids) != len(PRECONDITIONS):
        fail("duplicate tool or precondition slug")
    for t in TOOLS:
        if t["kind"] not in TOOL_KINDS:
            fail(f"tool:{t['slug']}: kind {t['kind']!r}")
        if t["doc"] is None and not t.get("doc_note"):
            fail(f"tool:{t['slug']}: no document and no reason")
        if t["doc"] is not None:
            ok, why = citation_opens(t["doc"], g)
            if not ok:
                fail(f"tool:{t['slug']}: {why}")
    for p in PRECONDITIONS:
        if p["kind"] not in PRECONDITION_KINDS or p["who_provides"] not in WHO_PROVIDES:
            fail(f"pre:{p['slug']}: kind or who_provides illegal")
        for c in p.get("unlocks_source") or []:
            ok, why = citation_opens(c, g)
            if not ok:
                fail(f"pre:{p['slug']}: {why}")
        if bool(p.get("unlocks_error_classes")) != bool(p.get("unlocks_source")):
            fail(f"pre:{p['slug']}: an error-class mapping without its source, or the reverse")

    def ckind(c):
        k = CLASSES[c]["kind"]
        return k.get(HARNESS_CURRENT) if isinstance(k, dict) else k
    unlocked = [c for p in PRECONDITIONS for c in p.get("unlocks_error_classes") or []]
    if len(unlocked) != len(set(unlocked)):
        fail("an error class is unlocked twice")
    for c in unlocked:
        if c not in CLASSES or ckind(c) != BLIND:
            fail(f"error class {c!r} is not BLIND under the current harness")
    blind = {c for c in CLASSES if c is not None and ckind(c) == BLIND}
    if blind - set(unlocked) != set(UNMAPPED_ERROR_CLASSES):
        fail(f"BLIND classes unmapped {sorted(blind - set(unlocked))} != the listed "
             f"{sorted(UNMAPPED_ERROR_CLASSES)}")

    for code, quote in UNMEASURED_HALF.items():
        if quote not in (inds.get(code, {}).get("tier_note") or ""):
            fail(f"UNMEASURED_HALF[{code}] is not in its tier_note")
    keys = set()
    for r in REQUIRES:
        k = (r["code"], r["to"])
        if k in keys:
            fail(f"duplicate edge {k}")
        keys.add(k)
        if r["code"] not in inds:
            fail(f"{r['code']} is not an indicator")
            continue
        if r["to"] not in tool_ids | pre_ids:
            fail(f"{r['code']}: unknown requirement {r['to']}")
        if r["closes"] not in CLOSES:
            fail(f"{r['code']}->{r['to']}: closes {r['closes']!r}")
        if r["for_clause"] not in (inds[r["code"]].get("indicator") or ""):
            fail(f"{r['code']}: for_clause is not verbatim in the definition: "
                 f"{r['for_clause']!r}")
        ok, why = citation_opens(r["source"], g)
        if not ok:
            fail(f"{r['code']}->{r['to']}: {why}")
    reached = {r["to"] for r in REQUIRES}
    for p in PRECONDITIONS:
        if f"pre:{p['slug']}" not in reached and not p.get("unlocks_error_classes"):
            fail(f"pre:{p['slug']} is reached by nothing")
    for t in TOOLS:
        if f"tool:{t['slug']}" not in reached:
            fail(f"tool:{t['slug']} is reached by nothing")
    # scope: everything in scope is reached or has a reason; nothing has both
    with_edges = {r["code"] for r in REQUIRES}
    for code, p in inds.items():
        in_scope = p.get("measurement_basis") != "harness_leg" or code in UNMEASURED_HALF
        if not in_scope or p.get("measurement_basis") is None:
            continue
        if (code in with_edges) == (code in NONE_REASONS):
            fail(f"{code}: in scope with {'both' if code in with_edges else 'neither'} "
                 f"requirements and a none-reason")
    if problems:
        raise SystemExit("FATAL: the requirements tables do not validate:\n  "
                         + "\n  ".join(problems))


# ----------------------------------------------------------------------------------- build

def build(g: dict) -> tuple:
    """`(nodes, edges, indicator_updates)`. Deterministic: the same tables over the same record
    produce the same bytes."""
    validate(g)
    nodes, edges = [], []
    for t in TOOLS:
        props = {"name": t["name"], "kind": t["kind"], "who_provides": WHO_RUNS_BY_KIND[t["kind"]]}
        if t.get("kind_reason"):
            props["kind_reason"] = t["kind_reason"]
        if t["doc"] is not None:
            props["doc_id"] = t["doc"][1]
            props["doc_source"] = format_citation(t["doc"])
        else:
            props["doc_source"] = NONE_ON_DISK
            props["doc_source_note"] = t["doc_note"]
        props["cost_band"] = NOTIONAL_TOOL_COST[t["kind"]]
        props["cost_source"] = notional_source(t["kind"])
        props["band_note"] = BAND_NOTE
        if t.get("note"):
            props["note"] = t["note"]
        props["authored_by"] = TASK
        nodes.append({"id": f"tool:{t['slug']}", "labels": ["AssessmentTool"],
                      "properties": props})
    for p in PRECONDITIONS:
        props = {"name": p["name"], "kind": p["kind"], "description": p["description"],
                 "who_provides": p["who_provides"]}
        if p.get("unlocks_error_classes"):
            props["unlocks_error_classes"] = list(p["unlocks_error_classes"])
            props["unlocks_source"] = [format_citation(c) for c in p["unlocks_source"]]
        props["authored_by"] = TASK
        nodes.append({"id": f"pre:{p['slug']}", "labels": ["Precondition"],
                      "properties": props})
    for r in REQUIRES:
        props = {"closes": r["closes"], "route": r["route"], "test": r["test"],
                 "for_clause": r["for_clause"], "source": format_citation(r["source"]),
                 "source_kind": r["source"][0]}
        if r.get("note"):
            props["note"] = r["note"]
        edges.append({"from": f"ind:{r['code']}", "type": "REQUIRES", "to": r["to"],
                      "properties": props})
    updates = {f"ind:{code}": {"requirement_none_reason": reason}
               for code, reason in NONE_REASONS.items()}
    return nodes, edges, updates


def merge(g: dict, nodes: list, edges: list, updates: dict) -> dict:
    """Lay the layer over the record, replacing this task's own nodes and edges and keeping
    every other node and edge whole; set the none-reasons on their indicators. Order is the
    record's; new entries append."""
    new_nodes = {n["id"]: n for n in nodes}
    new_edges = {(e["from"], e["type"], e["to"]): e for e in edges}
    kept = []
    for n in g["nodes"]:
        if n["id"] in new_nodes:
            kept.append(new_nodes[n["id"]])
        elif n["id"] in updates:
            kept.append({**n, "properties": {**n["properties"], **updates[n["id"]]}})
        else:
            kept.append(n)
    have = {n["id"] for n in kept}
    kept += [n for n in nodes if n["id"] not in have]
    kept_e = [new_edges.get((e["from"], e["type"], e["to"]), e) for e in g["edges"]]
    have_e = {(e["from"], e["type"], e["to"]) for e in kept_e}
    kept_e += [e for e in edges if (e["from"], e["type"], e["to"]) not in have_e]
    out = dict(g)
    out["nodes"], out["edges"] = kept, kept_e
    return out


def summary(nodes: list, edges: list) -> dict:
    from collections import Counter
    by_id = {n["id"]: n for n in nodes}
    return {
        "tools": sum(1 for n in nodes if n["labels"] == ["AssessmentTool"]),
        "preconditions": sum(1 for n in nodes if n["labels"] == ["Precondition"]),
        "requires_edges": len(edges),
        "tools_by_kind": dict(sorted(Counter(n["properties"]["kind"] for n in nodes
                                             if n["labels"] == ["AssessmentTool"]).items())),
        "preconditions_by_kind": dict(sorted(Counter(
            n["properties"]["kind"] for n in nodes if n["labels"] == ["Precondition"]).items())),
        "preconditions_by_who_provides": dict(sorted(Counter(
            n["properties"]["who_provides"] for n in nodes
            if n["labels"] == ["Precondition"]).items())),
        "tool_cost_bands": dict(sorted(Counter(n["properties"]["cost_band"] for n in nodes
                                               if n["labels"] == ["AssessmentTool"]).items())),
        "notional_costs": sum(1 for n in nodes
                              if str(n["properties"].get("cost_source", "")).startswith(
                                  NOTIONAL_PREFIX)),
        "tools_with_no_document_on_disk": sorted(
            n["id"] for n in nodes if n["properties"].get("doc_source") == NONE_ON_DISK),
        "edges_by_closes": dict(sorted(Counter(e["properties"]["closes"] for e in edges).items())),
        "edges_by_source_kind": dict(sorted(Counter(e["properties"]["source_kind"]
                                                    for e in edges).items())),
        "edges_by_requirement_kind": dict(sorted(Counter(
            by_id[e["to"]]["properties"]["kind"] for e in edges).items())),
        "indicators_with_a_requirement": sorted({e["from"].removeprefix("ind:") for e in edges}),
        "indicators_with_a_none_reason": sorted(NONE_REASONS),
        "error_classes_unlocked": {n["id"]: n["properties"]["unlocks_error_classes"]
                                   for n in nodes if n["properties"].get("unlocks_error_classes")},
        "error_classes_unmapped": sorted(UNMAPPED_ERROR_CLASSES),
        "tool_map_rows_not_carried": sorted(DROPPED_TOOL_MAP_ROWS),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="validate the tables against the record, the corpus and the harness; "
                         "write nothing and print the summary")
    a = ap.parse_args(argv)
    import framework_writeback as fw
    g = fw.load()
    nodes, edges, updates = build(g)
    s = summary(nodes, edges)
    if a.check:
        print(json.dumps({"validated": True, "summary": s}, indent=1, ensure_ascii=False))
        return 0
    merged = merge(g, nodes, edges, updates)
    changes = {"tools_added": [n["id"] for n in nodes if n["labels"] == ["AssessmentTool"]],
               "preconditions_added": [n["id"] for n in nodes if n["labels"] == ["Precondition"]],
               "requires_added": [f"{e['from']}->{e['to']} ({e['properties']['route']})"
                                  for e in edges],
               "requirement_none_reason_set": sorted(updates),
               "summary": s}
    out = fw.save(merged, script=SCRIPT, task=TASK, changes=changes, dry_run=a.dry_run)
    print(json.dumps({"summary": s,
                      "save": {k: v for k, v in out.items()
                               if k not in ("delta", "changes", "counts")}},
                     indent=1, default=str, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
