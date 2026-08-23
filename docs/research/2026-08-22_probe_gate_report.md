# Probe repair (v1 + kernel-v03) — Pre-registered Gate Report

Scope: profiles=v1,kernel_v03 epochs=['kernel-v03', 'v1'] shards=[4, 6]

Generated: 2026-08-23T03:37:06.796773+00:00

Failed gates are FINDINGS, not blockers. No retuning (task hard stop).

| check | value | threshold | verdict |
|---|---|---|---|
| min_verified_included | 134 | 71 | PASS |
| grounding_zero_ungrounded | 0 | 0 | PASS |
| quarantine_rate | 0.0237 | 0.0152 | **FAIL** |
| edge_endpoint_validation | 1209 | 0 | **FAIL** |
| orphan_rate | 0.0877 | 0.0034 | **FAIL** |
| projection_drift | 0 | 0 | PASS |
| empty_extraction_rate | 0.0075 | 0.1196 | PASS |

## TEVV gates (pre-registered 2026-08-22; fails are findings)

| check | realized | threshold | verdict |
|---|---|---|---|
| stability_kappa_pooled | -0.5904 | 0.61 | **FAIL** |
| stability_kappa_per_type_min | -0.7891 | 0.61 | **FAIL** |
| stability_jaccard_pooled | 0.2848 | 0.7 | **FAIL** |
| faithfulness_precision_pooled | 0.535 | 0.9 | **FAIL** |
| faithfulness_precision_stratum_min | 0.0 | 0.85 | **FAIL** |
| grade_platform_official_precision | 0.831 | 0.9 | **FAIL** |
| grade_peer_reviewed_precision | 1.0 | 0.9 | PASS |

## Detail

```json
[
 {
  "check_id": "min_verified_included",
  "value": 134,
  "threshold": 71,
  "passed": true
 },
 {
  "check_id": "grounding_zero_ungrounded",
  "value": 0,
  "threshold": 0,
  "passed": true,
  "checked_items": 20297,
  "legacy_items_not_rechecked": 876,
  "failures": []
 },
 {
  "check_id": "quarantine_rate",
  "value": 0.0237,
  "threshold": 0.0152,
  "passed": false,
  "quarantined": 492,
  "total_items": 20789
 },
 {
  "check_id": "edge_endpoint_validation",
  "value": 1209,
  "threshold": 0,
  "passed": false,
  "violations": [
   {
    "event_id": "e2b4f6805b15424dbea2146dd406bd78",
    "edge": "cites",
    "problems": [
     "endpoint 'gilovich-griffin-kahneman-heuristics-and-biases-2002' never asserted/manifested"
    ]
   },
   {
    "event_id": "0afd210f550543769bab390f2a5be9b1",
    "edge": "cites",
    "problems": [
     "endpoint 'banke-technology-readiness-levels-demystified-2010' never asserted/manifested"
    ]
   },
   {
    "event_id": "055eab74f1b54bf28da01b91ea0d4f8d",
    "edge": "cites",
    "problems": [
     "endpoint 'vanschoren-rijn-bischl-openml-2015' never asserted/manifested"
    ]
   },
   {
    "event_id": "6043a7ccbb62452ba6e9637efff4c93a",
    "edge": "cites",
    "problems": [
     "endpoint 'andrade-pacheco-monitoring-infectious-diseases-uganda-2016' never asserted/manifested"
    ]
   },
   {
    "event_id": "506ba505a3de455d8d9b9ed608ed22d0",
    "edge": "cites",
    "problems": [
     "endpoint 'nanotechnology-community-data-readiness-levels-2013' never asserted/manifested"
    ]
   },
   {
    "event_id": "8baa8a629cbd42e2ac7507484b2dd6e8",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-commerce-ai-ready-data-guidance' never asserted/manifested"
    ]
   },
   {
    "event_id": "5411643476654a8dbcc898ce4165c96d",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-public-law-115-435-title-ii' never asserted/manifested"
    ]
   },
   {
    "event_id": "1d16ff3b4ba145c286701147a3441234",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-omb-statistical-policy-directive-4' never asserted/manifested"
    ]
   },
   {
    "event_id": "dc3d9faf6bbc4b1b8bf3464405e8a022",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-44-usc-3563' never asserted/manifested"
    ]
   },
   {
    "event_id": "3cf2537a679646ceace5d49c5e590a0f",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-modelcontextprotocol-github' never asserted/manifested"
    ]
   },
   {
    "event_id": "5542e4c3c0574b2a9fd4de870f25ff0a",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-44-usc-3502-20' never asserted/manifested"
    ]
   },
   {
    "event_id": "6c1667e000a44ca1830277aea48c9306",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-omb-m-25-05' never asserted/manifested"
    ]
   },
   {
    "event_id": "ab8ff22d2e8d4c008c61a64d0b627c64",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-commerce-genai-open-data-2025' never asserted/manifested"
    ]
   },
   {
    "event_id": "c047980f4914444d91c3bcef4bd4ae2f",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-evidence-act-phase2-guidance' never asserted/manifested"
    ]
   },
   {
    "event_id": "832458a52a1a4f25a1015fdd3ea9622d",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-fcsm-ai-readiness-call-to-action' never asserted/manifested"
    ]
   },
   {
    "event_id": "64c71666faef46deb614cd9cafcf708d",
    "edge": "cites",
    "problems": [
     "endpoint 'hiniduma-2024-360-survey' never asserted/manifested"
    ]
   },
   {
    "event_id": "83ad7a81552d40ed806eb4de42ce4352",
    "edge": "cites",
    "problems": [
     "endpoint 'blake-mangiameli-2011' never asserted/manifested"
    ]
   },
   {
    "event_id": "67ac41a2b74842d6ab68e0070a3ed244",
    "edge": "cites",
    "problems": [
     "endpoint 'bors-2018' never asserted/manifested"
    ]
   },
   {
    "event_id": "a281b5731e7541acb97775e2fca9b15a",
    "edge": "cites",
    "problems": [
     "endpoint 'breunig-2000-lof' never asserted/manifested"
    ]
   },
   {
    "event_id": "0f51f9bcae9145e6873b348560d8d6ad",
    "edge": "cites",
    "problems": [
     "endpoint 'pokrajac-2007-ilof' never asserted/manifested"
    ]
   }
  ]
 },
 {
  "check_id": "orphan_rate",
  "value": 0.0877,
  "threshold": 0.0034,
  "passed": false,
  "orphans": 608,
  "total_non_document_nodes": 6935
 },
 {
  "check_id": "projection_drift",
  "value": 0,
  "threshold": 0,
  "passed": true,
  "delta": {},
  "fingerprint": {
   "n:Document": 134,
   "n:Definition": 690,
   "n:Concept": 3537,
   "n:Construct": 0,
   "n:Instrument": 131,
   "n:Measure": 444,
   "n:Claim": 1126,
   "n:Standard": 334,
   "n:Framework": 201,
   "n:Practice": 305,
   "n:Tool": 82,
   "n:Platform": 85,
   "r:ABOUT": 1505,
   "r:APPLIES_TO": 257,
   "r:ASSERTS": 1451,
   "r:BUILDS_ON": 118,
   "r:CITES": 1220,
   "r:CONFLICTS_WITH": 3,
   "r:CONSUMES": 59,
   "r:DEFINES": 924,
   "r:EXTENDS": 24,
   "r:HAS_COMPONENT": 1063,
   "r:IMPLEMENTED_BY": 32,
   "r:IMPLEMENTS": 97,
   "r:MEASURES": 552,
   "r:MENTIONS": 4353,
   "r:PRECEDES": 129,
   "r:RECOMMENDS": 336,
   "r:SUBTYPE_OF": 399,
   "r:SUPPORTED_BY": 59,
   "r:TARGETS": 61,
   "r:USES_MEASURE": 414
  }
 },
 {
  "check_id": "empty_extraction_rate",
  "value": 0.0075,
  "threshold": 0.1196,
  "passed": true,
  "empty_docs": [
   "itu-ai-ready-analysis-towards-a-standardized-readiness-frame"
  ],
  "docs_extracted": 134,
  "corpus_size": 134
 },
 {
  "check_id": "stability_kappa_pooled",
  "value": -0.5904,
  "threshold": 0.61,
  "passed": false
 },
 {
  "check_id": "stability_kappa_per_type_min",
  "value": -0.7891,
  "threshold": 0.61,
  "passed": false
 },
 {
  "check_id": "stability_jaccard_pooled",
  "value": 0.2848,
  "threshold": 0.7,
  "passed": false
 },
 {
  "check_id": "faithfulness_precision_pooled",
  "value": 0.535,
  "threshold": 0.9,
  "passed": false
 },
 {
  "check_id": "faithfulness_precision_stratum_min",
  "value": 0.0,
  "threshold": 0.85,
  "passed": false
 },
 {
  "check_id": "grade_platform_official_precision",
  "value": 0.831,
  "threshold": 0.9,
  "passed": false,
  "phase_stop_triggered": false
 },
 {
  "check_id": "grade_peer_reviewed_precision",
  "value": 1.0,
  "threshold": 0.9,
  "passed": true
 }
]
```
