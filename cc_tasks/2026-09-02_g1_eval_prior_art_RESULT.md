# RESULT — 2026-09-02_g1_eval_prior_art

**Task:** `cc_tasks/2026-09-02_g1_eval_prior_art.md`. No addenda existed (globbed `2026-09-02_g1_eval_prior_art_ADDENDUM*.md`: none). **Run:** 2026-09-02 UTC. **Model calls: zero** (OpenAlex / arXiv / Semantic Scholar / Europe PMC metadata and PDF fetches, WebSearch; `harvest_triage.py` refuses to start if `ANTHROPIC_API_KEY` is set).

**Memo:** `docs/research/2026-09-02_g1_eval_prior_art.md`.

## 1. The residual claim — answered

**No named metric or benchmark for numeric-uncertainty preservation under LLM restatement exists as of 2026-09-02.** The evidence is the logged search (below), in which every query family reached its neighbouring literature and none of the neighbours is the object. What exists decomposes the problem into five settled pieces (proposition-level unit; ordinal preservation levels; a named failure taxonomy; direct vs indirect assessment; producer-side definitions of MOE/CI/SE/CV/suppression) and one open piece — the numeric instrument itself, which is G1's contribution. Memo §1 and §4 state this with citations; §3 states the claim precisely with its falsifier and the search limits.

Strong-form claim from the handoff ("no known named prior art for uncertainty preservation") is confirmed false, as the Desktop pass found: Du, Lu & Qu 2026 (arXiv:2606.18471) is the named benchmark for verbal/diagnostic uncertainty preservation; van der Bles et al. 2019 is the taxonomy.

## 2. Query log summary

| run | log file | queries | ok | errored (recorded) | note |
|---|---|---|---|---|---|
| 1 | `docs/research/2026-09-02_g1_eval_prior_art_query_log_run1_fulltext.json` | 62 | 61 | 1 (S2 429) | OpenAlex full-text `search=` ranked off-topic high-citation works first; arXiv AND-of-all-tokens returned 0 for most phrasings. Kept as the record of why run 2 changed method. |
| 2 | `docs/research/2026-09-02_g1_eval_prior_art_query_log.json` | 88 | 86 | 2 (OpenAlex 400 on `?` in two titles) | OpenAlex `title_and_abstract.search`; hand-written arXiv boolean queries; 26 named-work resolutions; citation walks forward/backward from arXiv:2606.18471 (S2: 2 citers, 38 refs; OpenAlex: 0/0 — record too new) and van der Bles 2019 (OpenAlex 447 citers, S2 374; filtered by three sub-queries). |
| 3 | `docs/research/2026-09-02_g1_eval_prior_art_query_log_f6.json` | 12 | 12 | 0 | Added family F6 (caveat/qualifier, CV/RSE, DP noise, vintage) after run 2 showed the task's five families do not name G1's actual qualifier classes. |
| web | memo §5 | 11 | 11 | 0 | Family 5 grey literature and official-statistics guidance. |

Total scholarly-API queries: **162** (158 returned). Families and phrasings: F1 ×4, F2 ×4, F3 ×3, F4 ×3, F5 ×3, F6 ×4, each on three sources. Reproducer: `scripts/g1_prior_art_search.py` (new; `--oa-mode`, `--families`, `--skip-s2/--skip-named/--skip-citations`).

## 3. Counts

| class | n | where |
|---|---|---|
| candidate documents found and routed | 37 | `scripts/g1eval_list_2026-09-02.yaml` (verdict + clause per row) |
| staged (bytes in `corpus/staging/inbox/g1eval_2026-09-02/`) | 33 | 17 admits + 16 stage_only |
| **admitted** (`manifest_add`, AUTH-2, `events/batch-025.jsonl`) | **17** | epoch `g1eval-2026-09-02`; corpus included **194 → 211** |
| staged-not-admitted (register `excluded`, clause carried) | 16 | `ambiguous_contribution` ×1, `R1_out_of_scope` ×2, `R1_method_not_construct` ×7, `R1_no_marginal_contribution` ×6 |
| excluded without fetch | 3 | `R1_no_marginal_contribution` ×1 (Wiley paywall), `R1_method_not_construct` ×1 (IEEE paywall), `R1_out_of_scope` ×1 (usage survey) |
| fetch failed (`needs_source`) | 1 | UNECE HLG-MOS GenAI chapter — unece.org returns HTTP 403 to every scripted fetch tried (default UA, browser UA, HTTP/1.1 with Accept/Referer). Operator drop would admit it. |
| already held (R5), not re-fetched | 4 | `liu-2023-…`, `venkit-2025-deeptrace`, `zhang-2026-…`, `datacommons-docs-landing` |

Admitted doc_ids: `du-2026-possible-or-definite`, `van-der-bles-2019-communicating-uncertainty`, `peters-2025-generalization-bias-llm-summarization`, `manski-2015-communicating-uncertainty-official-economic-statistics`, `mazzi-2021-measuring-communicating-uncertainty-official-economic-statistics`, `zhao-2020-reducing-quantity-hallucinations`, `venktesh-2024-quantemp-numerical-claims`, `cao-2024-multimodal-long-form-summarization-financial-reports`, `lee-2026-when-summaries-distort-decisions`, `radhakrishnan-2024-knowing-when-to-ask-data-commons`, `zhou-2026-loomsum-table-grounded-faithfulness`, `min-2023-factscore`, `ebu-bbc-2025-news-integrity-ai-assistants`, `census-acs-general-handbook-2020`, `ons-uncertainty-and-how-we-measure-it`, `statcan-quality-guidelines-6th-edition`, `suleymanli-2025-llms-charts-official-statistics`. All carry `construct_arm: publication_actionability`, `grounding_surface: document`, clause R1, `discovered_via: g1-eval-prior-art-2026-09-02`, no vetting claimed (machine search). Three publisher PDFs (RSOS ×2, PNAS) 403'd scripted fetches and were taken from Europe PMC (PMC6549952, PMC10663791, PMC7149229), recorded in the register's `urls_tried`/`final_url`.

Rule reading applied: R1 as round 2 applied it — admit a work whose primary subject is machine consumption of published content **and** that carries a definition, a survey of the field's constructs, or a measurement instrument; cut methods, evidence-only replications, and different constructs, each with the clause and a one-line reason in the YAML. One cut is listed for operator review (`ansari-2026-slop-paradox-radiology-rewriting`, `ambiguous_contribution`, on the round-2 single-author/one-dataset precedent). A `manifest_add` reverses any cut.

## 4. Code changes (small, parameterizations of the standing path)

- `scripts/harvest_triage.py`: new verdict `stage_only` — fetch with full provenance, then mark `staged_not_admitted` with the clause. This is what "staged-not-admitted" means on the register; before, the only way to stage a document was to mark it admissible.
- `scripts/manifest_triage.py`: `REGISTER_STATUS["staged_not_admitted"] = "excluded"`; `--epoch-note` flag (the epoch note was hardcoded to the 2026-08-24 text and had been silently reused by round 2).
- `dixie_evidence.yaml`: `document_dirs` += `g1eval`. `.gitignore`: `corpus/g1eval/`.
- `tests/test_harvest_stage_only.py` (+3): stage_only routing, fetch unchanged, register mapping. Suite **631 passed** (`python -m pytest tests/`; count includes this session's concurrent tasks' additions).
- `scripts/g1_prior_art_search.py`: the logged search.

`python -m kg.manifest verify`: clean. `kg queue status` shows the 17 as `not_requested` — no extraction, per the task. `docs/corpus/manifest_table.md` was regenerated (`t1_build_index.py --phase table`) and is byte-identical: it reads the T1 index, which does not include the 17 until a `--phase convert/index` run, which is a substrate step this task did not order.

## 5. Discrepancies and things to know

1. **`events/batch-024.jsonl` gained one line** during admission: a `substrate_converted` (passthrough) event for the ONS markdown capture, emitted by the ingest gate the dixie sweep calls. Append-only; expected behaviour of the standing path (DD-030); reported because the task said not to touch that shard beyond `manifest_add`.
2. **Semantic Scholar 429s even with the key** on ~1 in 30 calls after five spaced retries; recorded as errors, never as zero hits.
3. **The task's five families do not name G1's qualifier classes** (CV, DP noise, vintage). Family F6 was added and logged; it found nothing, which is itself the finding for those classes (memo §4, open items).
4. UNECE chapter quote in the memo (§2.4) is from a search snippet, not a held copy; marked as such.

## 6. Out of scope, untouched

No extraction. No edit to the crosswalk skeleton or the assessment protocol. Burn state, spend ledger and other event shards untouched except as in §5.1. No probe design (memo §4 lists constraints only).
