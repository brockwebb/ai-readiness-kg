# Bulk v1 — Pre-registered Gate Report

Generated: 2026-07-17T01:49:50.785290+00:00

Failed gates are FINDINGS, not blockers. No retuning (task hard stop).

| check | value | threshold | verdict |
|---|---|---|---|
| min_verified_included | 71 | 71 | PASS |
| grounding_zero_ungrounded | 0 | 0 | PASS |
| quarantine_rate | 0.0342 | 0.0152 | **FAIL** |
| edge_endpoint_validation | 683 | 0 | **FAIL** |
| orphan_rate | 0.0964 | 0.0034 | **FAIL** |
| projection_drift | 0 | 0 | PASS |
| empty_extraction_rate | 0.0145 | 0.1196 | PASS |

## Detail

```json
[
 {
  "check_id": "min_verified_included",
  "value": 71,
  "threshold": 71,
  "passed": true
 },
 {
  "check_id": "grounding_zero_ungrounded",
  "value": 0,
  "threshold": 0,
  "passed": true,
  "checked_items": 10840,
  "legacy_items_not_rechecked": 876,
  "failures": []
 },
 {
  "check_id": "quarantine_rate",
  "value": 0.0342,
  "threshold": 0.0152,
  "passed": false,
  "quarantined": 384,
  "total_items": 11224
 },
 {
  "check_id": "edge_endpoint_validation",
  "value": 683,
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
    "event_id": "acac0af1261641518b02e0dc0ac1a7c1",
    "edge": "cites",
    "problems": [
     "endpoint 'doc-fcsm-framework-for-data-quality' never asserted/manifested"
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
   }
  ]
 },
 {
  "check_id": "orphan_rate",
  "value": 0.0964,
  "threshold": 0.0034,
  "passed": false,
  "orphans": 387,
  "total_non_document_nodes": 4016
 },
 {
  "check_id": "projection_drift",
  "value": 0,
  "threshold": 0,
  "passed": true,
  "delta": {},
  "fingerprint": {
   "n:Document": 71,
   "n:Definition": 385,
   "n:Concept": 2162,
   "n:Construct": 0,
   "n:Instrument": 123,
   "n:Measure": 299,
   "n:Claim": 753,
   "n:Standard": 125,
   "n:Framework": 169,
   "r:ABOUT": 885,
   "r:ASSERTS": 885,
   "r:BUILDS_ON": 50,
   "r:CITES": 677,
   "r:CONFLICTS_WITH": 4,
   "r:DEFINES": 462,
   "r:EXTENDS": 16,
   "r:HAS_COMPONENT": 796,
   "r:IMPLEMENTS": 53,
   "r:MEASURES": 424,
   "r:MENTIONS": 2304,
   "r:PRECEDES": 99,
   "r:SUBTYPE_OF": 185,
   "r:USES_MEASURE": 295
  }
 },
 {
  "check_id": "empty_extraction_rate",
  "value": 0.0145,
  "threshold": 0.1196,
  "passed": true,
  "empty_docs": [
   "itu-ai-ready-analysis-towards-a-standardized-readiness-frame"
  ],
  "docs_extracted": 69,
  "corpus_size": 71
 }
]
```
