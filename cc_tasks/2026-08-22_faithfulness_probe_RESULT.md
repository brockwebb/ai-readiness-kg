# RESULT — Faithfulness probe: atomic decomposition, multi-agent judging, Dawid-Skene, pre-registered repair decision

**Task:** `cc_tasks/2026-08-22_faithfulness_probe.md` (immutable) · **Seldon task:** `68426971`
**Executed:** 2026-08-22/23 (≈ 23:40 → 04:30 UTC). Max OAuth only; `ANTHROPIC_API_KEY` unset. Two model streams at most.
**Sub-RESULTs:** `docs/research/2026-08-22_probe_{phase0_preflight, sample, decision, gate_report}`; data in `corpus/staging/metrics/probe_*`.

## Plain reading (what share of the 0.535 was what)
Of 935 atomic facts, 401 (42.9%) are entailed by their span. The 534 that are not split as: **scoring defect** (`doc_level_attribute`, attributes a span should never have been asked to carry) 76 = 14% of failures; **capture defect** (`span_truncated` + `subject_dropped`: the document supports the fact, the span missed it) 277 = 52%; **extraction fill** (`filled_attribute`: populated without span support — 20 of these are document-supported by mechanical check) 113 = 21%; **fabrication** (absent from span and from the document/window) 68 = 13% of failures, **7.3% of all facts**. So roughly nine-tenths of the TEVV 0.535 gap is repairable scoring and capture, and about one-tenth is the extractor asserting what the document does not say — concentrated in Instrument `method` text and structure-inferred semantic edges.

## Phase status
| phase | status |
|---|---|
| 0 Preflight | done — 136 → 146 tests (final **147**); schema v0.3.2 `span_entailable`; `judge_label` event type; probe shard excluded from projection |
| 1 Sample | done — seed 20260822; 400 items / 21 strata (type × epoch; edge families); TEVV 200 excluded; ±400-char windows (1 span not located) |
| 2 Decomposition | done — **935 facts** (561 deterministic attribute facts + 374 model-split propositions; 2.34/item; within the 800–2,000 band), `decompose_template.md` 1.0.0 |
| 3 Batch calibration | done — κ(single vs batch-10) = **0.915** on 50 → **batch size 10** |
| 4 Judging | done — Opus 4.8 935/935, Sonnet 5 935/935 (1,870 labels, PROV-attributed, `events/batch-009_probe_judge.jsonl`); self-consistency 94 facts κ = 0.957; cross-family: 94 markdown batches exported, inbox created, **not waited for**; TEVV sidecar contributed 0 labels (no overlap by design) |
| 5 Aggregation | done — crowd-kit Dawid-Skene; decision rule applied |
| 6 Hard items | done — 86 uncertain, **60 exported** (cap; overflow noted) to `probe_hard_items.jsonl` + readable `.md`, blank `human_label/human_class/orcid` |
| 7 Repair | done (non-flagged strata) — invariant mutation-tested; 23 spans relocated, 59 not relocatable, 79 attributes nulled; overlays in `events/batch-010.jsonl`; projection applies overlays last; grounding gate **0** after rebuild (drift 0; graph gates unchanged: quarantine 0.0237 / edge_endpoint 1209 / orphan 0.0877 findings) |
| 8 Close | done — DD-015/016; controls restored; 11 Seldon results; committed + pushed |

## Decision rule — applied
**F pooled = 0.0792 [0.0629, 0.0991]** (n=859 facts; `doc_level_attribute` and `grade_misassigned` excluded).

| stratum | F denom | F | Wilson 95% | verdict |
|---|---|---|---|---|
| Claim:kernel-v03 | 30 | 0.000 | [0.000, 0.114] | repair_then_rejudge |
| Claim:v1 | 31 | 0.000 | [0.000, 0.110] | repair_then_rejudge |
| Concept:kernel-v03 | 101 | 0.069 | [0.034, 0.136] | repair_then_rejudge |
| Concept:v1 | 97 | 0.041 | [0.016, 0.101] | repair_then_rejudge |
| Definition:kernel-v03 | 45 | 0.000 | [0.000, 0.079] | repair_then_rejudge |
| Definition:v1 | 44 | 0.000 | [0.000, 0.080] | repair_then_rejudge |
| Framework:kernel-v03 | 26 | 0.038 | [0.007, 0.189] | repair_then_rejudge |
| Framework:v1 | 32 | 0.031 | [0.006, 0.157] | repair_then_rejudge |
| Instrument:kernel-v03 | 67 | 0.254 | [0.165, 0.369] | reextract_required |
| Instrument:v1 | 70 | 0.171 | [0.101, 0.276] | reextract_required |
| Measure:kernel-v03 | 35 | 0.057 | [0.016, 0.186] | repair_then_rejudge |
| Measure:v1 | 39 | 0.154 | [0.072, 0.297] | repair_then_rejudge |
| Platform:kernel-v03 | 18 | 0.000 | [0.000, 0.176] | repair_then_rejudge |
| Practice:kernel-v03 | 25 | 0.040 | [0.007, 0.195] | repair_then_rejudge |
| Standard:kernel-v03 | 36 | 0.000 | [0.000, 0.096] | repair_then_rejudge |
| Standard:v1 | 29 | 0.069 | [0.019, 0.220] | repair_then_rejudge |
| Tool:kernel-v03 | 31 | 0.000 | [0.000, 0.110] | repair_then_rejudge |
| edge:document_structural:kernel-v03 | 23 | 0.130 | [0.045, 0.321] | repair_then_rejudge |
| edge:document_structural:v1 | 28 | 0.000 | [0.000, 0.121] | repair_then_rejudge |
| edge:semantic:kernel-v03 | 23 | 0.261 | [0.125, 0.465] | reextract_required |
| edge:semantic:v1 | 29 | 0.207 | [0.098, 0.384] | repair_then_rejudge |

**Overall: repair_path for other strata; reextract_required strata flagged.** `reextract_required`: `Instrument:v1`, `Instrument:kernel-v03`, `edge:semantic:kernel-v03` — corrected-prompt requirements in `docs/research/2026-08-22_probe_decision.md` (per-attribute spans for Instrument `method/owner/year`; semantic edges need both endpoints and the predicate in the span; structure-inferred relations go to `proposed_relationships`). Re-extraction is a separate task. No stratum reached the repair-only branch (F_upper < 0.05).

## Class proportions (pooled, Wilson 95%)
| class | n | share | CI |
|---|---|---|---|
| entailed | 401 | 0.429 | [0.398, 0.461] |
| span_truncated | 156 | 0.167 | [0.144, 0.192] |
| subject_dropped | 121 | 0.129 | [0.109, 0.152] |
| filled_attribute | 113 | 0.121 | [0.101, 0.143] |
| doc_level_attribute | 76 | 0.081 | [0.065, 0.101] |
| fabrication | 68 | 0.073 | [0.058, 0.091] |

Item roll-up: faithful 130/400 = 0.325 (an item is faithful iff every fact is entailed or doc_level_attribute).

## Raters — Dawid-Skene estimated confusion
| rater | P(e\|e) | P(ne\|e) | P(e\|ne) | P(ne\|ne) | agreement w/ MAP |
|---|---|---|---|---|---|
| claude-opus-4-8 | 0.983 | 0.017 | 0.075 | 0.925 | 0.923 |
| claude-sonnet-5 | 0.918 | 0.082 | 0.015 | 0.985 | 0.985 |

Position effect (entailed rate by batch position 0–9, both raters): 0.50, 0.45, 0.44, 0.51, 0.45, 0.46, 0.50, 0.48, 0.47, 0.48 — no trend.

## Repair pass (probe items only)
relocated 23 (exact/NFKC substring of item text in document) · relocation failed 59 (item text paraphrased, not verbatim in the document — the repair ceiling for deterministic relocation) · attributes nulled 79 · items skipped in `reextract_required` strata 53 · not applicable 42. Overlays: `grounding_relocated`, `attribute_nulled` (102 events, `events/batch-010.jsonl`), applied last by `build_projection.py` through an attribute whitelist.
**Mutation test (span-coverage invariant):** `tests/test_extraction_grounding.py::test_partial_span_reason_mutation_positive_control` seeds a known-partial span ("Is the methodology internally" vs the full claim) and the check fires with reason `span_partial`; parser path tested on/off in `tests/test_extraction_parser.py`. Config `extraction_gates.enforce_span_coverage: false` (task scope: probe items only; whole-graph enforcement is the follow-on sized from the 23/82 relocation success rate).

## Tokens / cost
Decomposition + judging (all runs): **16,095,207 tokens**. **Cost UNKNOWN** (unpriced by the control plane; envelope estimate $74.23 is a lower bound).

## controls.yaml
before `611d5dda…3684` → task `1e1654c6…0a74` (`extract: on`, `extract_daily_docs: 0`) → after **`611d5dda…3684`** (byte-identical). Note: `model_stub.invoke` does not consult the control plane, so `extract` gates nothing for judging; recorded as the task anticipated.

## Standing decisions (judgment calls)
1. **Hybrid decomposition:** literal attributes (name, steward, owner, year, version, operator, license, url, response_type, term, aliases) become one deterministic fact each with no model call; only free-text fields are model-split. Cheaper and exact; the model never invents a fact for a literal.
2. **Full-document fabrication check:** the class definition says "absent from the document", judges saw a window; literal-attribute `fabrication` calls were re-checked against full document text (33 checked, 20 → `filled_attribute`). Free-text propositions keep the window-based call; limit recorded.
3. **Edge strata** reuse the TEVV two-family split (×epoch) per the task; 21 strata, none merged.
4. **Second rater = `claude-sonnet-5`** (added to `model_config.yaml: secondary_judge_model_id`); same family, recorded as such (DD-016).
5. **`relocate_not_applicable`:** a judge class of span_truncated/subject_dropped on a fact whose item's text attribute the span already covers (e.g. the truncation is in another attribute) is counted, not relocated.
6. **CLI auto-update incident (again):** `claude` unresolvable for seconds at ~02:00 UTC killed the Opus stream at 210 facts. Root-caused into `model_stub` (OSError → `ModelInvocationError`, test added) and the judge retries with backoff; relaunched with resume; no duplicate labels. One Opus batch also timed out at 600 s and was retried by the resume pass.
7. **Invariant wiring:** `enforce_span_coverage` lives in `dixie_evidence.yaml: extraction_gates` (off) rather than a code constant, so turning it on is a config diff.

## Discrepancies vs the task
| task said | live |
|---|---|
| Sidecar rater ingested on its 40 items | 0 labels — the probe excludes the TEVV 200 (task's own rule), so no sidecar item has facts here. Pooling the two samples later is where the sidecar contributes. |
| "if the control plane gates all model calls on `extract`, note it" | It does not; only the bulk runner reads it. |
| Hard items "expected 20–40" | 86 uncertain; 60 exported (cap), overflow noted. |
| `fabrication` "checked against full doc text" | Mechanically for literal attributes only (decision 2). |
| Seldon results "F pooled with CI, per-class proportions, per-rater accuracy, batch-vs-single κ" | 11 registered (adds self-consistency κ); `--script-path` links show "no" (script artifacts not registered in this project's graph). |

## Commits
`ai-readiness-kg@74955f2` → `origin/main` (RESULT hash line added in the follow-up commit). dixie: no changes.

## Files
**New:** `scripts/{probe_decompose, probe_judge, probe_aggregate, probe_hard_items, probe_repair, probe_crossfamily_export}.py`, `kg/extraction/{decompose_template, probe_judge_template}.md`, `events/batch-009_probe_judge.jsonl`, `events/batch-010.jsonl`, `events/raw/{probe_decompose, probe_judge}/`, `corpus/staging/metrics/probe_*`, `corpus/staging/metrics/probe_crossfamily_batches/` (94), `corpus/staging/inbox/probe_crossfamily/README.md`, `tests/test_probe_aggregate.py`, `docs/research/2026-08-22_probe_*`.
**Modified:** `kg/schema.yaml` (v0.3.2), `kg/extraction/{schema_loader, parser, grounding, model_stub}.py`, `kg/extraction/model_config.yaml`, `scripts/build_projection.py`, `dixie_evidence.yaml`, `docs/{schema_v0.1.md, design_decisions.md}`, tests ×5.
