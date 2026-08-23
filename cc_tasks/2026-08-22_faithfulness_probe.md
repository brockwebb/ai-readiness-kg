# CC Task — Faithfulness probe: atomic decomposition, multi-agent judging, Dawid-Skene aggregation, pre-registered repair decision

**Date:** 2026-08-22
**Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Max OAuth only; `ANTHROPIC_API_KEY` unset or abort.
**Execution model:** Multi-agent permitted. Judging batches are embarrassingly parallel once the decomposition file exists. Sub-RESULTs under `docs/research/2026-08-22_probe_*`; orchestrator assembles `cc_tasks/2026-08-22_faithfulness_probe_RESULT.md`, citing the Seldon task id from registration.
**This file is immutable.** Discrepancies reported, never reconciled.
**Operator contact policy:** None. Every fork has a rule below. The only operator-facing output is the hard-item export in Phase 6, which is a file, not a pause. Operator labels, when they arrive, are consumed by a follow-on, not by this task.

## Why this task exists

The 2026-08-22 TEVV task (Seldon `de7ae80b`) found judge-scored faithfulness 0.535 on n=200 and a second same-family rater at 0.525 on n=40 (sidecar `corpus/staging/metrics/tevv_human_subset_labels.jsonl`). The sidecar notes attribute the failures to six classes, five of which are pipeline or scoring defects rather than extraction fabrication. n=40 cannot size those classes (95% half-width ≈ 0.15 at p=0.5). This probe sizes them at n≈400 and applies a decision rule written here, before data.

## Literature this task is grounded on (cite in DD-015)

- Atomic-fact decomposition for faithfulness: Min et al. 2023 (FActScore); Es et al. 2023 (RAGAS faithfulness); Zha et al. 2023 (AlignScore).
- LLM-judge biases (position, verbosity, self-enhancement): Zheng et al. 2023 (MT-Bench); Panickssery et al. 2024 (self-recognition).
- Batch prompting effects: Cheng et al. 2023.
- Multi-rater aggregation with latent truth and per-rater confusion: Dawid & Skene 1979; Hovy et al. 2013 (MACE).
- Attribution vocabulary: W3C PROV-O (`prov:Person`, `prov:SoftwareAgent`, `prov:wasAttributedTo`); ORCID for persons.
- Proportion CI: Wilson score interval.

## Pre-registered decision rule (binding on the machine; written before data)

Let F = estimated proportion of atomic facts in class `fabrication` (Phase 5 definition), per stratum and pooled, with Wilson 95% CI.

- **F_upper < 0.05 in every stratum** → repair path: Phase 7 proceeds (span-coverage invariant + attribute nulling + re-judge). No re-extraction.
- **F_lower > 0.10 in any stratum** → that stratum is flagged `reextract_required` in the RESULT with the corrected-prompt requirements listed; re-extraction is a separate task. Repair path still proceeds for the other strata.
- **Otherwise** → repair path proceeds for all strata; a re-judge after repair (follow-on) decides.

The six fail classes and their repair disposition are fixed here:

| class | definition (at atomic-fact level) | disposition |
|---|---|---|
| `doc_level_attribute` | fact is an attribute the schema marks document-derived (`as_of_date`, harvest date, `operator` inferable from name) | scoring defect; excluded from F |
| `span_truncated` | span is a strict prefix/suffix/fragment of the item text; fact lies in the cut portion | capture defect; repair by re-locating span to cover item text |
| `subject_dropped` | span contains predicate/values, item supplies subject or agent from context | capture defect; repair by span extension; fact is not fabricated if document supports it |
| `filled_attribute` | `description`, `steward`, `owner`, `scale`, `version` populated without span support | extraction defect; repair by nulling (may be null, may not be guessed) |
| `fabrication` | fact contradicts the span or asserts content absent from span AND absent from the document (checked against full doc text) | counted in F |
| `grade_misassigned` | `evidence_grade` inconsistent with document signals (`is_platform_operator`, `source_type`) | grading defect; tracked separately, not in F |

## Phase 0 — Preflight (zero spend)

1. Tests green; record count. `controls.yaml` sha256; set `extract: on`, `extract_daily_docs: 0` (judging uses the model path but not the extraction runner; if the control plane gates all model calls on `extract`, note it). Restore byte-identical at close.
2. Schema v0.3.2, append-only: add `span_entailable: true|false` per attribute on every node type in `kg/schema.yaml`. Rule for assignment: `as_of_date`, `id`, enum classification fields (`evidence_grade`, `claim_type`, `normative_status`, `scope`, `tier`) → false; `name`, `text`, `claim_text`, `verbatim_text`, `term`, `description`, `steward`, `owner`, `year`, `version`, `operator`, `scale`, `license`, `url` → true. Extend the append-only test. Record the assignment table in the Phase 0 sub-RESULT.
3. Add event type `judge_label` to the event schema: `{item_id, event_id_judged, fact_id, label: entailed|not_entailed, class: <one of six>|null, confidence: 0..1|null, batch_id, batch_position, agent: {type: prov:SoftwareAgent|prov:Person, id, model_version|orcid, prompt_template_sha, call_id|null}, rated_at}`. Shard `events/batch-009_probe_judge.jsonl`, flagged `purpose: probe`, excluded by `build_projection.py` (extend the existing `purpose` filter; test).

## Phase 1 — Sample (deterministic, zero spend)

- Seed `20260822`. n=400 items stratified proportionally by `type` × epoch, minimum 15 per stratum, strata under 15 merged to `other:<epoch>` and reported. Edges stratified by the edge families the TEVV task used. Exclude the 200 already judged in `de7ae80b` so the two samples can be pooled later without overlap.
- For each item also capture: the grounding span, the item's full `extra`, and a ±400-char window of document text around the span (for `subject_dropped` and `fabrication` adjudication; the window is evidence, not the span).
- Write `corpus/staging/metrics/probe_sample.jsonl`.

## Phase 2 — Atomic decomposition (model spend, small)

- Decompose each item into atomic facts: one per `span_entailable: true` attribute value plus one per independent proposition in free text (Claims, Practices, Definitions). Edges decompose to one fact: "<from> <rel> <to>". Target 2–5 facts per node. Prompt template versioned and stamped.
- Output `corpus/staging/metrics/probe_facts.jsonl`: `{fact_id, item_id, event_id, attribute|null, fact_text}`. Facts for `span_entailable: false` attributes are not generated.
- Sanity: total facts between 800 and 2,000; outside that, log and continue.

## Phase 3 — Batch-vs-single calibration (model spend, small)

- 50 facts, seeded. Judge each twice with the Fable judge: singly, and inside batches of 10 with randomized order. κ between the two. **Rule:** κ ≥ 0.80 → batch size 10 for Phase 4; 0.60 ≤ κ < 0.80 → batch size 5; κ < 0.60 → single-item judging for Phase 4. Log the decision.

## Phase 4 — Multi-agent judging (model spend)

Three software agents minimum, all attributed per `judge_label.agent`:

1. **Fable judge** (pinned extraction-family model, Max OAuth): all facts, batched per Phase 3, order randomized per batch, `batch_position` recorded. Output per fact: `{fact_id, label, class, confidence}`.
2. **Second Claude family member** (Haiku or Sonnet per `model_config`, Max OAuth): all facts, same protocol. Different model, same family; recorded as such.
3. **Cross-family agent via operator chat export**: produce `corpus/staging/metrics/probe_crossfamily_batches/` as numbered markdown files of 10 facts each (fact, span, window), with an answer template. The operator pastes these into another vendor's model and drops the responses in `corpus/staging/inbox/probe_crossfamily/`. **This task does not wait for them.** Phase 5 runs with whatever agents have labels; the ingest of cross-family responses is a follow-on that re-runs Phase 5 with the extra rater. Agent id on ingest = the model name and version the operator records in the response file header; if absent, `unknown_crossfamily` and flagged.
4. **Existing sidecar** (`tevv_human_subset_labels.jsonl`, agent `claude-desktop-fable5`): ingested as a rater on its 40 items only, converted to fact-level labels by mapping item label to every fact of that item (noted as a coarse rater).

Judge prompt rules: the judge sees fact, span, window; labels entailment **against the span**; uses the window only to assign `subject_dropped` vs `fabrication`; returns a class from the six or null; confidence in [0,1]. Self-consistency: 10% of facts re-judged by agent 1 in a different batch; agreement reported.

## Phase 5 — Aggregation (zero spend)

- Dawid-Skene EM over all available raters at fact level (use `crowd-kit` if installable, else implement; record which). Output per fact: posterior P(entailed), MAP class, per-rater estimated confusion matrices.
- Class proportions per stratum and pooled with Wilson 95% CIs. F computed per the decision rule, excluding `doc_level_attribute` and `grade_misassigned` from the denominator.
- Roll up to item level: an item is `faithful` iff all its facts are entailed or `doc_level_attribute`.
- Apply the **decision rule**; record the verdict per stratum in `docs/research/2026-08-22_probe_decision.md`.
- Register Seldon results: F pooled with CI, per-class proportions, per-rater accuracy, batch-vs-single κ.

## Phase 6 — Hard-item export (operator file, non-blocking)

- Facts with posterior in [0.35, 0.65], or where raters split with both sides confidence ≥ 0.7, go to `corpus/staging/metrics/probe_hard_items.jsonl` with fact, span, window, each rater's label and reason, and blank `human_label`, `human_class`, `orcid`. Expected 20–40; if over 60, write the 60 most uncertain and note the overflow. Also produce a readable `probe_hard_items.md` view (one fact per block, span quoted, window indented) because the prior calibration set was unreadable as raw nodes.
- Operator labels are ingested by a follow-on as a `prov:Person` rater keyed on ORCID; the ORCID value is whatever the operator writes in the file. Never fabricate one.

## Phase 7 — Repair path (conditional on decision rule; extraction-adjacent spend, small)

Runs only for strata not flagged `reextract_required`.

1. **Span-coverage invariant**: add to the grounding validator the rule "span must cover the full item text for `verbatim_text`, `text`, `claim_text`, `name`, `term`; otherwise the item is quarantined with reason `span_partial`". **Mutation-test first**: seed a known-partial span, show the check fires, record it. Do not apply to the live log until the check is verified.
2. **Re-location pass**: for items classed `span_truncated` or `subject_dropped` in the probe, attempt deterministic re-location (exact or NFKC-normalized substring search of item text in document text). Success → `grounding_relocated` overlay event with old and new span. Failure → leave as is, counted.
3. **Attribute nulling**: for items classed `filled_attribute`, emit `attribute_nulled` overlay events setting the unsupported attribute to null with `reason: unsupported_by_span`. Overlay, never mutation; projection reads overlays last.
4. Apply 1–3 only to the probe items (not the whole graph). Whole-graph application is a follow-on sized from the probe's repair-success rate.
5. Rebuild projection; gates; grounding must remain 0.

## Phase 8 — Close

- `docs/design_decisions.md`: **DD-015** (probe design, literature, decision rule, and the distinction between capture defects and fabrication); **DD-016** (judge attribution: PROV-O agent block, ORCID for persons, model id + version + prompt sha for software agents).
- Tests green; `controls.yaml` restored, sha recorded; **commit and push**.
- RESULT: phase table; sample and fact counts; batch-vs-single κ and the batch-size decision; per-rater confusion matrices; class proportions with CIs per stratum; F and the verdict per stratum; hard-item export count; repair pass counts (relocated, nulled, failed); mutation-test record; token totals with cost UNKNOWN where unpriced; standing decisions; commit hashes; and a one-paragraph plain reading of what share of the 0.535 was scoring defect, capture defect, and fabrication.

## Out of scope

Whole-graph repair; any re-extraction; concept dedup; new harvest; waiting on cross-family or operator labels; changing the decision rule after data; editing this file.
