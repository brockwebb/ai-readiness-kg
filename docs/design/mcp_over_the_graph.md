# The graph through an MCP: nine read-only tools, every answer with its locator

**Generated** by `mcp/airkg_doc.py` from `cc_tasks/2026-09-17_mcp_over_the_graph.md` (decision 4), by RUNNING the tools against the live database. Nothing on this page is typed: re-run `/opt/anaconda3/bin/python3 mcp/airkg_doc.py --check` and it fails if the page and the server have drifted.

## What it is

Read-only knowledge graph of the AI-readiness framework for federal statistical publishers,
its measurement instrument, and the evidence behind every verdict it has published.

CALL `get_overview` FIRST. It gives the framework's counts by measurement tier and basis, the
cycle of record every verdict comes from, the bodies on that cycle, and — the part that decides
whether anything else here is current — the status of the framework projection gate.

EVERY ANSWER CARRIES LOCATORS. A `locators` list (or a `locator` on a row) names the record
node, the matrix cell, the retained response body and its sha256, the graph node or the corpus
document a fact came from. Cite them. `run_cypher` returns the projection gate's status beside
its rows for the same reason: a stale projection does not look stale, it answers.

TWO SOURCES AND NO THIRD. The framework record and the published matrices are the source of
truth; Neo4j is a projection of them and of the event log. Framework questions are answered
from the record even when the graph holds the same nodes.

BANDS ARE NOTIONAL. Effort and cost on a prescription are relative estimates assigned by
technique class, not predictions of anyone's calendar or budget; `band_note` says so once per
answer. A band with no estimate behind it reads `pending` and never a number.

READ-ONLY, AND SCOPED TO ONE DATABASE. Any write clause or unlisted procedure in `run_cypher`
comes back as a refusal message. This server touches no other graph.

## Running it

```bash
/opt/anaconda3/bin/python3 mcp/airkg_server.py            # stdio, the project database
/opt/anaconda3/bin/python3 mcp/airkg_server.py --no-graph # record-only, no Neo4j
```

Claude Code reads `.mcp.json` in this repository and needs nothing else. For Claude Desktop the same object goes in `~/Library/Application Support/Claude/claude_desktop_config.json` under `mcpServers`; the exact lines are in the task's RESULT §3.

The interpreter is named explicitly because `fastmcp`, the Neo4j driver and `pyyaml` are installed in `/opt/anaconda3/bin/python3` — the same interpreter `CLAUDE.md` names for extraction and projection.

## The rails

| rail | what it does | where |
|---|---|---|
| one database | an allow-list of exactly one name, read from `seldon.yaml:neo4j.database`; every other name is `SystemExit` at startup | `mcp/airkg_guard.py::assert_allowed_db` |
| read-only, belt 1 | write clauses and unlisted `CALL` procedures are refused before anything reaches the database, with the refusal RETURNED as a message | `mcp/airkg_guard.py::refusal` |
| read-only, belt 2 | every statement runs in the driver's explicit read transaction | `mcp/airkg_tools.py::Graph.read` |
| flood cap | 200 rows | `mcp/airkg_guard.py::MAX_ROWS` |

## The projection gate, at generation time

`green` — every node of the record is in the graph with every property equal (171 nodes compared against `framework/ai_readiness_framework.json`, cell for cell). `get_overview` recomputes this on every call and `run_cypher` returns it beside every result, because DD-057 makes a Cypher answer over the framework labels valid only while it is green.

## The tools

One real call each, with the answer the tool gave. Long lists are cut to 2 entries by the generator, which says so in place; **locator lists are never cut**.

### `get_overview()`



```json
{
  "graph": "ai-readiness-kg",
  "database": "seldon-ai-readiness-kg",
  "call_first": "This is the orientation tool. Every other tool's answer carries locators; `resolve_locator` opens what one names.",
  "framework": {
    "indicators_total": 49,
    "indicators_by_measurement_tier": {
      "M": 34,
      "O": 5,
      "unassigned": 5,
      "D": 5
    },
    "indicators_by_measurement_basis": {
      "harness_leg": 17,
      "open_tool": 5,
      "structured_field": 7,
      "unassigned": 5,
      "evaluation": 8,
      "declaration": 5,
      "judged_reading": 2
    },
    "by_tier_and_basis": [
      {
        "measurement_tier": "D",
        "measurement_basis": "declaration",
        "indicators": 5
      },
      {
        "measurement_tier": "M",
        "measurement_basis": "evaluation",
        "indicators": 8
      },
      "… 5 more (elided by mcp/airkg_doc.py, not by the tool)"
    ],
    "tier_meaning": {
      "M": "measurable now by this harness or a named structured field",
      "O": "measurable with an open tool whose documentation is in the corpus",
      "D": "declaration only — the act happens on the agency's side",
      "unassigned": "no tier yet, and the node carries the test that failed"
    },
    "counts": {
      "criteria": 7,
      "constructs": 47,
      "indicators": 48,
      "evidenced_by": 139,
      "evidenced_by_internal": 17,
      "gaps": 14,
      "measurement_specs": 22,
      "collectors_none_known": 4,
      "rules_built": 17,
      "specs_with_recorded_decision": 3,
      "candidate_indicators": 1,
      "indicators_measured": 16,
      "actions": 42,
      "actions_on_candidate_indicators": 3
    },
    "counts_basis": "Node and edge counts of the framework itself (criteria, constructs, indicators, evidenced_by, evidenced_by_internal, gaps, indicators_measured) EXCLUDE candidate indicators and their constructs (DD-054: the framework does not adopt what the instrument found about itself without the operator); candidate_indicators count… [898 chars]",
    "nodes": 171,
    "edges": 325,
    "actions": 45,
    "remediates_edges": 45,
    "locators": [
      {
        "kind": "record_key",
        "path": "framework/ai_readiness_framework.json",
        "key": "counts"
      },
      {
        "kind": "record_key",
        "path": "framework/ai_readiness_framework.json",
        "key": "counts_basis"
      },
      {
        "kind": "record_key",
        "path": "framework/ai_readiness_framework.json",
        "key": "nodes"
      },
      {
        "kind": "record_key",
        "path": "framework/ai_readiness_framework.json",
        "key": "edges"
      }
    ]
  },
  "cycle_of_record": {
    "cycle": "scan_2026-09-10_rj2",
    "measured": "2026-09-10",
    "kind": "rejudged",
    "bodies": [
      "BEA",
      "BJS",
      "… 14 more (elided by mcp/airkg_doc.py, not by the tool)"
    ],
    "n_bodies": 16,
    "matrices": [
      {
        "kind": "tierA",
        "path": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json",
        "legs": [
          "A4",
          "A5",
          "… 3 more (elided by mcp/airkg_doc.py, not by the tool)"
        ],
        "rows": 16
      },
      {
        "kind": "product",
        "path": "docs/reports/scan_matrix_product_2026-09-10_rj2.json",
        "legs": [
          "A1",
          "A2",
          "… 8 more (elided by mcp/airkg_doc.py, not by the tool)"
        ],
        "rows": 23
      }
    ],
    "locators": [
      {
        "kind": "config",
        "path": "docs/reports/publication.yaml",
        "key": "snapshot_cycle"
      },
      {
        "kind": "payload",
        "path": "state/scan_2026-09-10_rj2.json",
        "key": "derived_from"
      },
      {
        "kind": "matrix",
        "path": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json",
        "cell": "BEA/A4"
      },
      {
        "kind": "matrix",
        "path": "docs/reports/scan_matrix_product_2026-09-10_rj2.json",
        "cell": "BEA/A1"
      }
    ]
  },
  "projection_gate": {
    "gate": "tests/test_framework_projection_roundtrip.py",
    "decision": "DD-057",
    "means": "green: a Cypher answer over the framework labels is the record. stale: it is not, and `run_cypher` results about those labels are not current. unverified: the database was not reachable.",
    "locators": [
      {
        "kind": "source",
        "path": "tests/test_framework_projection_roundtrip.py",
        "symbol": "test_every_json_node_is_in_the_graph_cell_for_cell"
      }
    ],
    "status": "green",
    "nodes_compared": 171,
    "mismatches": [],
    "reason": "every node of the record is in the graph with every property equal"
  },
  "tools": [
    "get_overview",
    "get_indicator",
    "… 7 more (elided by mcp/airkg_doc.py, not by the tool)"
  ]
}
```

### `get_indicator(code='A5')`



```json
{
  "code": "A5",
  "indicator": "llms.txt (or equivalent) present; sitemap covers data products",
  "construct": "Discoverability surface",
  "construct_id": "con:A:discoverability-surface",
  "criterion": {
    "code": "A",
    "name": "ACCESSIBLE",
    "anchor": "USAFacts anchor: machine-readable access matters most. FCSM bridge: Utility → accessibility, timeliness.",
    "locator": {
      "kind": "record",
      "path": "framework/ai_readiness_framework.json",
      "node_id": "crit:A"
    }
  },
  "type": "AUTO",
  "status": "draft",
  "tier": "public",
  "tier_source": "rules.CURRENT['A5'] = RULE-A5-v2 (assessment/harness/scan/rules/__init__.py); measurement spec `spec:A5`",
  "tier_rule": "cc_tasks/2026-09-17_measurement_tiers.md decision 2 rule 1",
  "measurement_tier": "M",
  "measurement_basis": "harness_leg",
  "measurement_status": "measured",
  "notes": {
    "evidence_raw": "`llmstxt-proposal`; `sitemaps-protocol`",
    "gap": null,
    "measured_by": {
      "cycle": "scan_2026-09-07",
      "legs": [
        "A5"
      ],
      "params_hash": "4a1350802619fe8ff65c0fc38cce128298278d0d2787b24cd6cfa3a17eb656f4",
      "qualifying_findings": 23,
      "counts": {
        "pass": 2,
        "fail": 21,
        "not_applicable": 0,
        "error": 3
      },
      "definition": "at least one pass/fail/not_applicable Finding on an admitted, observable surface in a cycle with fired controls; `error` does not count",
      "recorded_by": "cc_tasks/2026-09-07_scan_run.md"
    }
  },
  "spec": {
    "indicator_code": "A5",
    "leg": "A5",
    "mode": "auto",
    "rule_id": "RULE-A5-v2",
    "collector_pin": "ultimate-sitemap-parser>=1.0",
    "signal": "HTTP GET /sitemap.xml (and the path robots.txt declares), /llms.txt, /.well-known/; parse the sitemap and test whether the product URL is covered.",
    "collector": "ultimate-sitemap-parser",
    "evidence_kind": "sitemap tree + coverage verdict for the product URL",
    "prior_art": "`sitemaps-protocol`; `llmstxt-proposal`",
    "decision": {
      "decided_by": "RULE-A5-v1",
      "question": "The signal says to fetch /llms.txt and /.well-known/ alongside the sitemap but states a coverage test only for the sitemap, leaving unsettled what a served llms.txt contributes to the verdict.",
      "decision": "A covering sitemap is the SOLE pass path. A served llms.txt is recorded as evidence and cannot satisfy the leg on its own. Rationale: the sitemap is the only one of the three with a standardised way to assert that a specific URL is covered; llms.txt has no such semantics, and accepting its mere presence would score hav… [595 chars]",
      "alternative": "Treat llms.txt as an alternative satisfier. That is a change to what the indicator MEANS, not to how it is measured, and belongs to the operator.",
      "recorded_by": "cc_tasks/2026-09-06_scan_targets.md",
      "why_here": "The review returned `spec_underspecified`: a different reasonable implementation would return a different verdict on some real surface, and neither control fixture can see the difference."
    },
    "id": "spec:A5",
    "locator": {
      "kind": "record",
      "path": "framework/ai_readiness_framework.json",
      "node_id": "spec:A5"
    }
  },
  "rule": {
    "rule_id": "RULE-A5-v2",
    "indicator_code": "A5",
    "qualifier": null,
    "version": "v2",
    "current": true,
    "leg": "A5",
    "locator": {
      "kind": "source",
      "path": "assessment/harness/scan/rules/__init__.py",
      "symbol": "CURRENT"
    }
  },
  "actions": [
    {
      "id": "act:a5-list-the-product-url-in-the-sitemap",
      "title": "List the product URL in the discovery file that is already served",
      "outcome": "discovery_file_omits_product",
      "effort": "hours",
      "cost": "none",
      "verifies_by": "RULE-A5-v2",
      "locator": {
        "kind": "record",
        "path": "framework/ai_readiness_framework.json",
        "node_id": "act:a5-list-the-product-url-in-the-sitemap"
      }
    },
    {
      "id": "act:a5-publish-a-sitemap-and-point-robots-txt-at-it",
      "title": "Publish a sitemap and point robots.txt at it",
      "outcome": "no_discovery_file",
      "effort": "days",
      "cost": "staff_time",
      "verifies_by": "RULE-A5-v2",
      "locator": {
        "kind": "record",
        "path": "framework/ai_readiness_framework.json",
        "node_id": "act:a5-publish-a-sitemap-and-point-robots-txt-at-it"
      }
    }
  ],
  "locators": [
    {
      "kind": "record",
      "path": "framework/ai_readiness_framework.json",
      "node_id": "ind:A5"
    },
    {
      "kind": "record",
      "path": "framework/ai_readiness_framework.json",
      "node_id": "con:A:discoverability-surface"
    }
  ],
  "cycle_of_record": {
    "cycle": "scan_2026-09-10_rj2",
    "locators": [
      {
        "kind": "config",
        "path": "docs/reports/publication.yaml",
        "key": "snapshot_cycle"
      },
      {
        "kind": "graph",
        "label": "Finding",
        "id_property": "cycle",
        "id": "scan_2026-09-10_rj2"
      }
    ],
    "verdicts": {
      "fail": 36,
      "error": 9,
      "pass": 7
    }
  }
}
```

### `get_body(name='NCHS')`



```json
{
  "body": "NCHS",
  "cycle": "scan_2026-09-10_rj2",
  "n_judged": 25,
  "n_failing": 21,
  "summary": "21 failing of 25 judged on scan_2026-09-10_rj2; 16 bodies are on this cycle",
  "legs": [
    {
      "leg": "A4",
      "verdict": "pass",
      "surface": "home:www.cdc.gov",
      "url": "https://www.cdc.gov/nchs/index.htm",
      "matrix": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json",
      "finding_id": "fnd_6bc41a5d60eb49319167f0fb",
      "reason": "robots.txt allows the product path for all 8 AI-crawler user agents",
      "rule_id": "RULE-A4-v1",
      "evidence": [
        {
          "error_class": null,
          "error_class_recorded": null,
          "collector": "robots",
          "leg": "A4",
          "surface_doc_id": "home:www.cdc.gov",
          "captured_at": "2026-09-10T17:59:54.672232+00:00",
          "sha256": "2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7",
          "obs_id": "obs_7d5add4fb04ea068d859b649",
          "raw_ref": "corpus/evidence/scan/28/2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7",
          "path": "corpus/evidence/scan/28/2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7",
          "exists": true,
          "bytes": 1699,
          "sha256_verified": true,
          "retained": true,
          "retention": "response body retained under its sha256",
          "locator": {
            "kind": "evidence",
            "path": "corpus/evidence/scan/28/2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7",
            "sha256": "2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7"
          }
        }
      ],
      "locators": [
        {
          "kind": "matrix",
          "path": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json",
          "cell": "NCHS/A4"
        },
        {
          "kind": "graph",
          "label": "Finding",
          "id_property": "finding_id",
          "id": "fnd_6bc41a5d60eb49319167f0fb"
        }
      ]
    },
    {
      "leg": "A5",
      "verdict": "fail",
      "surface": "home:www.cdc.gov",
      "url": "https://www.cdc.gov/nchs/index.htm",
      "matrix": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json",
      "finding_id": "fnd_38617cefaa483190125df4a4",
      "reason": "discovery files served (https://www.cdc.gov/wcms-auto-sitemap-index.xml) but none lists the product URL",
      "rule_id": "RULE-A5-v2",
      "evidence": [
        {
          "error_class": null,
          "error_class_recorded": null,
          "collector": "sitemap",
          "leg": "A5",
          "surface_doc_id": "home:www.cdc.gov",
          "captured_at": "2026-09-10T17:59:57.021165+00:00",
          "sha256": "7315b036b7a39e3243942a93a2ab378cdd7caa9acda7107e4068d79d6249860f",
          "obs_id": "obs_2adb3036ab5fced73714aac7",
          "raw_ref": "corpus/evidence/scan/73/7315b036b7a39e3243942a93a2ab378cdd7caa9acda7107e4068d79d6249860f",
          "path": "corpus/evidence/scan/73/7315b036b7a39e3243942a93a2ab378cdd7caa9acda7107e4068d79d6249860f",
          "exists": true,
          "bytes": 88946,
          "sha256_verified": true,
          "retained": true,
          "retention": "response body retained under its sha256",
          "locator": {
            "kind": "evidence",
            "path": "corpus/evidence/scan/73/7315b036b7a39e3243942a93a2ab378cdd7caa9acda7107e4068d79d6249860f",
            "sha256": "7315b036b7a39e3243942a93a2ab378cdd7caa9acda7107e4068d79d6249860f"
          }
        },
        {
          "error_class": "http_4xx",
          "error_class_recorded": "http_4xx",
          "collector": "sitemap",
          "leg": "A5",
          "surface_doc_id": "home:www.cdc.gov",
          "captured_at": "2026-09-10T17:59:57.697482+00:00",
          "sha256": "a6b66cdebef567c41fa89c8ee3a601dac20060d81d83738b60efcd680b7ecb93",
          "obs_id": "obs_b7dd7f315a187af1fe8c30ee",
          "raw_ref": "corpus/evidence/scan/a6/a6b66cdebef567c41fa89c8ee3a601dac20060d81d83738b60efcd680b7ecb93",
          "path": "corpus/evidence/scan/a6/a6b66cdebef567c41fa89c8ee3a601dac20060d81d83738b60efcd680b7ecb93",
          "exists": true,
          "bytes": 20905,
          "sha256_verified": true,
          "retained": true,
          "retention": "response body retained under its sha256",
          "locator": {
            "kind": "evidence",
            "path": "corpus/evidence/scan/a6/a6b66cdebef567c41fa89c8ee3a601dac20060d81d83738b60efcd680b7ecb93",
            "sha256": "a6b66cdebef567c41fa89c8ee3a601dac20060d81d83738b60efcd680b7ecb93"
          }
        },
        "… 4 more (elided by mcp/airkg_doc.py, not by the tool)"
      ],
      "locators": [
        {
          "kind": "matrix",
          "path": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json",
          "cell": "NCHS/A5"
        },
        {
          "kind": "graph",
          "label": "Finding",
          "id_property": "finding_id",
          "id": "fnd_38617cefaa483190125df4a4"
        }
      ]
    },
    "… 23 more (elided by mcp/airkg_doc.py, not by the tool)"
  ],
  "locators": [
    {
      "kind": "config",
      "path": "docs/reports/publication.yaml",
      "key": "snapshot_cycle"
    }
  ]
}
```

### `get_prescriptions(body='NCHS')`



```json
{
  "cycle": "scan_2026-09-10_rj2",
  "body": "NCHS",
  "leg": null,
  "failing_legs": [
    "A1",
    "A10",
    "… 10 more (elided by mcp/airkg_doc.py, not by the tool)"
  ],
  "bodies_on_cycle": 16,
  "notional": "(notional)",
  "band_note": "Notional relative estimate for a typical federal statistical publisher. Adjust for your platform, staffing, skills and procurement path; the band orders actions against each other, it does not predict your calendar or budget.",
  "ranked_by": "value.bodies_failing_now, then leg, then action id",
  "actions": [
    {
      "id": "act:a2-expose-an-api-and-publish-its-description",
      "title": "Expose the product through an API and publish the API's description",
      "description": "No OpenAPI or JSON API description was served at any probed path. Expose the product through a documented HTTP API and publish a machine-readable description of it; where the product already sits on a data platform, enabling the platform's own API is the cheaper route than building one.",
      "leg": "A2",
      "outcome": "no_api_description",
      "indicator_id": "ind:A2",
      "effort": "quarter",
      "effort_source": "notional:technique_class:expose_api, task 2026-09-17_notional_bands",
      "cost": "procurement",
      "cost_source": "notional:technique_class:expose_api, task 2026-09-17_notional_bands",
      "technique_class": "expose_api",
      "technique_source": [
        "corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 23 'Possible Approach to Implementation': \"If you use a data management platform, such as CKAN, you may be able to enable an existing API.\"",
        "corpus/kernel/w3c-dwbp-2017.md (doc_id `w3c-dwbp-2017`), Best Practice 25 'Possible Approach to Implementation': \"A typical API reference provides a comprehensive list of the calls the API can handle, describing the purpose of each one\"",
        "… 2 more (elided by mcp/airkg_doc.py, not by the tool)"
      ],
      "verifies_by": "RULE-A2-v3",
      "applies_to_publisher": true,
      "value": {
        "bodies_failing_now": 13,
        "bodies_on_the_cycle_of_record": 16,
        "bodies_failing_now_source": "docs/reports/scan_matrix_product_2026-09-10_rj2.json (cycle `scan_2026-09-10_rj2`, declared by docs/reports/publication.yaml:snapshot_cycle): 13 of 16 bodies carry the verdict `fail` on leg `A2`",
        "constructs_served": [
          "Programmatic access"
        ],
        "constructs_served_source": "`con:A:programmatic-access` -[DECOMPOSES_INTO]-> `ind:A2` in framework/ai_readiness_framework.json",
        "downstream_indicators": [],
        "downstream_indicators_source": "no field of any node in framework/ai_readiness_framework.json states that another indicator presupposes this one; scanned every string property of every node for a code other than its own",
        "bodies_failing_now_caveat": "a per-LEG count. `A2`'s rule has 2 failing outcomes, so this is an upper bound for this action alone: it is the number of bodies failing the leg, not the number failing on this outcome. The matrices of the cycle of record carry verdicts, not reasons, so the per-outcome split is not derivable from them."
      },
      "failing_on": [
        "scan-nchs-flagship-1-data-briefs",
        "scan-nchs-flagship-2-early-releases-of-selected-estimates-from-the-nhis"
      ],
      "locators": [
        {
          "kind": "record",
          "path": "framework/ai_readiness_framework.json",
          "node_id": "act:a2-expose-an-api-and-publish-its-description"
        },
        {
          "kind": "record",
          "path": "framework/ai_readiness_framework.json",
          "node_id": "ind:A2"
        },
        {
          "kind": "document",
          "doc_id": "w3c-dwbp-2017",
          "section": "Best Practice 23 'Possible Approach to Implementation",
          "path": "corpus/kernel/w3c-dwbp-2017.md"
        },
        {
          "kind": "document",
          "doc_id": "w3c-dwbp-2017",
          "section": "Best Practice 25 'Possible Approach to Implementation",
          "path": "corpus/kernel/w3c-dwbp-2017.md"
        },
        {
          "kind": "document",
          "doc_id": "openapi-specification-core",
          "section": "section 2 'Introduction",
          "path": "corpus/kernel/openapi-specification-core.md"
        },
        {
          "kind": "document",
          "doc_id": "schema-org-webapi",
          "section": "property `documentation`",
          "path": "corpus/kernel/schema-org-webapi.md"
        }
      ]
    },
    {
      "id": "act:a2-serve-a-parseable-api-description-at-the-documented-path",
      "title": "Serve a parseable OpenAPI description where the API is documented",
      "description": "A document is served at a probed API path but does not parse as an API description; a JSON content type alone is not a description. Publish an OpenAPI Description document (YAML or JSON) at that path, so a client can discover the operations without reading prose.",
      "leg": "A2",
      "outcome": "served_but_not_an_api_description",
      "indicator_id": "ind:A2",
      "effort": "days",
      "effort_source": "notional:technique_class:publish_new_file, task 2026-09-17_notional_bands",
      "cost": "staff_time",
      "cost_source": "notional:technique_class:publish_new_file, task 2026-09-17_notional_bands",
      "technique_class": "publish_new_file",
      "technique_source": [
        "corpus/kernel/openapi-specification-core.md (doc_id `openapi-specification-core`), section 2 'Introduction': \"The OpenAPI Specification (OAS) defines a standard, language-agnostic interface to HTTP APIs which allows both humans and computers to discover and understand the capabilities of the service without access to s… [386 chars]",
        "corpus/kernel/openapi-specification-core.md (doc_id `openapi-specification-core`), section 2 'Introduction': \"An OpenAPI Description (OAD) can then be used by documentation generation tools to display the API\"",
        "… 1 more (elided by mcp/airkg_doc.py, not by the tool)"
      ],
      "verifies_by": "RULE-A2-v3",
      "applies_to_publisher": true,
      "value": {
        "bodies_failing_now": 13,
        "bodies_on_the_cycle_of_record": 16,
        "bodies_failing_now_source": "docs/reports/scan_matrix_product_2026-09-10_rj2.json (cycle `scan_2026-09-10_rj2`, declared by docs/reports/publication.yaml:snapshot_cycle): 13 of 16 bodies carry the verdict `fail` on leg `A2`",
        "constructs_served": [
          "Programmatic access"
        ],
        "constructs_served_source": "`con:A:programmatic-access` -[DECOMPOSES_INTO]-> `ind:A2` in framework/ai_readiness_framework.json",
        "downstream_indicators": [],
        "downstream_indicators_source": "no field of any node in framework/ai_readiness_framework.json states that another indicator presupposes this one; scanned every string property of every node for a code other than its own",
        "bodies_failing_now_caveat": "a per-LEG count. `A2`'s rule has 2 failing outcomes, so this is an upper bound for this action alone: it is the number of bodies failing the leg, not the number failing on this outcome. The matrices of the cycle of record carry verdicts, not reasons, so the per-outcome split is not derivable from them."
      },
      "failing_on": [
        "scan-nchs-flagship-1-data-briefs",
        "scan-nchs-flagship-2-early-releases-of-selected-estimates-from-the-nhis"
      ],
      "locators": [
        {
          "kind": "record",
          "path": "framework/ai_readiness_framework.json",
          "node_id": "act:a2-serve-a-parseable-api-description-at-the-documented-path"
        },
        {
          "kind": "record",
          "path": "framework/ai_readiness_framework.json",
          "node_id": "ind:A2"
        },
        {
          "kind": "document",
          "doc_id": "openapi-specification-core",
          "section": "section 2 'Introduction",
          "path": "corpus/kernel/openapi-specification-core.md"
        },
        {
          "kind": "document",
          "doc_id": "openapi-specification-core",
          "section": "section 2 'Introduction",
          "path": "corpus/kernel/openapi-specification-core.md"
        },
        {
          "kind": "document",
          "doc_id": "w3c-dwbp-2017",
          "section": "Best Practice 25 'Possible Approach to Implementation",
          "path": "corpus/kernel/w3c-dwbp-2017.md"
        }
      ]
    },
    "… 31 more (elided by mcp/airkg_doc.py, not by the tool)"
  ],
  "locators": [
    {
      "kind": "record_key",
      "path": "framework/ai_readiness_framework.json",
      "key": "nodes"
    },
    {
      "kind": "config",
      "path": "docs/reports/publication.yaml",
      "key": "snapshot_cycle"
    }
  ]
}
```

### `get_evidence(finding_id='fnd_6bc41a5d60eb49319167f0fb')`



```json
{
  "finding_id": "fnd_6bc41a5d60eb49319167f0fb",
  "verdict": "pass",
  "reason": "robots.txt allows the product path for all 8 AI-crawler user agents",
  "rule_id": "RULE-A4-v1",
  "rule_version": "v1",
  "indicator_code": "A4",
  "target_doc_id": "home:www.cdc.gov",
  "current": false,
  "evidence_unretained": false,
  "observations": [
    {
      "error_class": null,
      "error_class_recorded": null,
      "collector": "robots",
      "leg": "A4",
      "surface_doc_id": "home:www.cdc.gov",
      "captured_at": "2026-09-10T17:59:54.672232+00:00",
      "sha256": "2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7",
      "obs_id": "obs_7d5add4fb04ea068d859b649",
      "raw_ref": "corpus/evidence/scan/28/2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7",
      "path": "corpus/evidence/scan/28/2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7",
      "exists": true,
      "bytes": 1699,
      "sha256_verified": true,
      "retained": true,
      "retention": "response body retained under its sha256",
      "locator": {
        "kind": "evidence",
        "path": "corpus/evidence/scan/28/2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7",
        "sha256": "2837016c20845bf0f86ecfad68dbb4d37993338ee4584abd502087da48ea5ca7"
      }
    }
  ],
  "note": "`error_class_recorded` is the class the log holds and `error_class` the corrected one, where an `observation_error_reclassified` overlay exists; the log line is never edited.",
  "locators": [
    {
      "kind": "graph",
      "label": "Finding",
      "id_property": "finding_id",
      "id": "fnd_6bc41a5d60eb49319167f0fb"
    }
  ]
}
```

### `get_document(doc_id='rfc-9309-robots-exclusion-protocol')`



```json
{
  "id": "rfc-9309-robots-exclusion-protocol",
  "is_platform_operator": false,
  "title": "RFC 9309: Robots Exclusion Protocol",
  "content_hash": "aea78e3b6eeca189a9ec60458e4fa83277ec0e4ef42613923b5e21933bd62e76",
  "prov_manifest_event": "977cb79db2f94fa098df154da94620c3",
  "pub_date": "n.d.",
  "doc_id": "rfc-9309-robots-exclusion-protocol",
  "source_type": "standard",
  "construct_arm": "publication_actionability",
  "primary_url": "https://www.rfc-editor.org/rfc/rfc9309",
  "key": "rfc-9309-robots-exclusion-protocol",
  "counts": {
    "definitions": 11,
    "concepts": 63,
    "claims": 59,
    "standards": 20,
    "practices": 15,
    "platforms": 2
  },
  "evidences_indicators": [
    "A11",
    "A12",
    "… 1 more (elided by mcp/airkg_doc.py, not by the tool)"
  ],
  "locators": [
    {
      "kind": "graph",
      "label": "Document",
      "id_property": "doc_id",
      "id": "rfc-9309-robots-exclusion-protocol"
    },
    {
      "kind": "document",
      "doc_id": "rfc-9309-robots-exclusion-protocol",
      "section": null,
      "path": null
    }
  ]
}
```

### `search_text(q='sitemap', limit=3)`



```json
{
  "query": "sitemap",
  "hits": [
    {
      "kind": "indicator",
      "code": "A5",
      "text": "llms.txt (or equivalent) present; sitemap covers data products",
      "doc_id": null,
      "section": "Discoverability surface",
      "locator": {
        "kind": "record",
        "path": "framework/ai_readiness_framework.json",
        "node_id": "ind:A5"
      }
    },
    {
      "kind": "action",
      "code": "A5",
      "text": "List the product URL in the discovery file that is already served",
      "doc_id": null,
      "section": "discovery_file_omits_product",
      "locator": {
        "kind": "record",
        "path": "framework/ai_readiness_framework.json",
        "node_id": "act:a5-list-the-product-url-in-the-sitemap"
      }
    },
    "… 1 more (elided by mcp/airkg_doc.py, not by the tool)"
  ],
  "n_hits": 10,
  "truncated": true,
  "searched": [
    "AssessmentIndicator.indicator (record)",
    "Action.title/description (record)",
    "… 2 more (elided by mcp/airkg_doc.py, not by the tool)"
  ],
  "locators": [
    {
      "kind": "record_key",
      "path": "framework/ai_readiness_framework.json",
      "key": "nodes"
    }
  ]
}
```

### `get_cycle_of_record()`



```json
{
  "cycle": "scan_2026-09-10_rj2",
  "kind": "rejudged",
  "derived_from": "scan_2026-09-10",
  "derived_from_params_hash": "4e0a92ba19ab769bb98b3a4a0c68640fbe465a04eaaec4aa6f2f0f41dc75c0df",
  "judgement_params_hash": "d3499218ef48273597ec67a6a81ae9c966e5801cf66915fbc106403c6da94624",
  "hash_meaning": "`derived_from_params_hash` identifies the COLLECTION the evidence came from; `judgement_params_hash` identifies this judgement of it. A re-judgement re-reads stored observations and fetches nothing.",
  "rejudged_note": "Findings only. Every Finding cites the `obs_id`s scan_2026-09-10 recorded; not one byte was re-fetched and not one Observation was created. The evidence is that cycle's, the judgement is this one's.",
  "rules": [
    "RULE-A1-v4",
    "RULE-A10-v3",
    "… 14 more (elided by mcp/airkg_doc.py, not by the tool)"
  ],
  "legs_judged": [
    "A1",
    "A10",
    "… 14 more (elided by mcp/airkg_doc.py, not by the tool)"
  ],
  "legs_not_judged": {
    "E5": "E5 judges the CYCLE, and the control set changed under v4 (a fifth fixture): re-judging the source cycle's four-fixture record against a five-fixture expectation would report a change in the instrument as a failure of the cycle. This task's own control gate is recorded as `control_gate`."
  },
  "verdict_counts": {
    "pass": 161,
    "fail": 459,
    "not_applicable": 0,
    "error": 119
  },
  "matrices": [
    {
      "kind": "tierA",
      "path": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json",
      "legs": [
        "A4",
        "A5",
        "… 3 more (elided by mcp/airkg_doc.py, not by the tool)"
      ],
      "rows": 16,
      "params_hash": "d3499218ef48273597ec67a6a81ae9c966e5801cf66915fbc106403c6da94624",
      "locator": {
        "kind": "matrix",
        "path": "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json",
        "cell": "BEA/A4"
      }
    },
    {
      "kind": "product",
      "path": "docs/reports/scan_matrix_product_2026-09-10_rj2.json",
      "legs": [
        "A1",
        "A2",
        "… 8 more (elided by mcp/airkg_doc.py, not by the tool)"
      ],
      "rows": 23,
      "params_hash": "d3499218ef48273597ec67a6a81ae9c966e5801cf66915fbc106403c6da94624",
      "locator": {
        "kind": "matrix",
        "path": "docs/reports/scan_matrix_product_2026-09-10_rj2.json",
        "cell": "BEA/A1"
      }
    }
  ],
  "locators": [
    {
      "kind": "config",
      "path": "docs/reports/publication.yaml",
      "key": "snapshot_cycle"
    },
    {
      "kind": "payload",
      "path": "state/scan_2026-09-10_rj2.json",
      "key": "derived_from_params_hash"
    },
    {
      "kind": "payload",
      "path": "state/scan_2026-09-10_rj2.json",
      "key": "params_hash"
    }
  ],
  "supersession": {
    "snapshot": "scan_2026-09-10_rj2",
    "snapshot_findings": 739,
    "successor": "scan_2026-09-10_rj3",
    "successor_generation": 3,
    "successor_kind": "rejudged",
    "superseded_findings": 739,
    "verdict_moves": 0,
    "reason_only_changes": 3,
    "line": "**Standing.** This snapshot has been superseded on the event log by `scan_2026-09-10_rj3`, generation 3 of this cycle, which re-judged the same evidence: 739 of this snapshot's 739 findings have a successor, 0 of them move a verdict and 3 change only the sentence that explains one. No number this report publishes diffe… [468 chars]",
    "decision": "DN-004 decision 1",
    "locators": [
      {
        "kind": "source",
        "path": "scripts/snapshot_successor.py",
        "symbol": "successor_info"
      },
      {
        "kind": "graph",
        "label": "Finding",
        "id_property": "cycle",
        "id": "scan_2026-09-10_rj3"
      }
    ]
  }
}
```

### `run_cypher(query='MATCH (r:Rule {current: true}) RETURN count(r) AS current_rules')`



```json
{
  "rows": [
    {
      "current_rules": 17
    }
  ],
  "row_count": 1,
  "truncated": false,
  "max_rows": 200,
  "database": "seldon-ai-readiness-kg",
  "projection_gate": "green",
  "locator": {
    "kind": "graph",
    "label": "*",
    "id_property": "database",
    "id": "seldon-ai-readiness-kg"
  }
}
```

## What this page is not

It is not the framework and it is not a view of it (DN-005 §5 rule 2): it is the exposure layer's documentation. The framework record, the matrices and the retained response bodies are the things; this server is one interface onto them, and the locators on every answer are what let a reader leave the interface and check the thing.

