# Repair Phase 1 — Detection sweep (task 2026-08-23_whole_graph_repair, Seldon 803b024f)

Zero spend. `scripts/repair_detect.py` over every live node in both epochs (8,858 scanned; 160 Instrument nodes skipped — `reextract_required` in both epochs; edges are not span-repaired, and `edge:semantic:kernel-v03` is reextract_required). Items already overlaid by the probe are evaluated on their overlaid state.

| detector | total | v1 | kernel-v03 |
|---|---|---|---|
| span_partial (span does not cover the text attribute) | **5,277** | 3,168 | 2,109 |
| filled_attr (span_entailable attribute value not in span) | **7,875** | 4,581 | 3,294 |

span_partial by type: Concept 2,904, Claim 1,236, Measure 340, Definition 286, Practice 185, Standard 151, Framework 132, Platform 33, Tool 10.
filled_attr by attribute: description 4,659, aliases 1,430, term 498, response_type 494, steward 304, year 175, owner 169, version 60, operator 54, url 28, license 4; free-text attributes (description/method/…) are 65% of entries.

Worklists: `corpus/staging/metrics/repair_span_partial.jsonl`, `repair_filled_attr.jsonl`.

## Comparison with the probe's projected rates — divergence flagged
The probe measured, among *failed atomic facts*, 52% capture (span_truncated + subject_dropped) and 21% filled_attribute. The mechanical sweep finds capture 40% and filled 60% of detections — filled is **~2.9× the probe's share → flagged as a finding** (> 2×). Cause: the probe's judges accept a *paraphrased* `description` as entailed by the span; the sweep's normalized-substring rule cannot, so free-text attributes (description 4,659, aliases 1,430) are over-detected relative to judged entailment. This is the definition the task pre-registers ("absent from span under normalized substring match"), so it is applied as written; the consequence — nulling descriptions the span paraphrases — is a scope cost of the mechanical rule, recorded here and testable by the success measure only for relocation (a nulled attribute produces no fact, so over-nulling is invisible to entailment). Recommended follow-on: a judged (not substring) filled-attribute detector for free-text attributes before any re-grounding task.

Also: span_partial hits 60% of scanned nodes — the probe's item-level faithful rate was 32.5%, consistent.
