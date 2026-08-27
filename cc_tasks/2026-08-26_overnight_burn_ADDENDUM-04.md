# ADDENDUM-04 to `2026-08-26_overnight_burn.md` (Seldon cd8449de)

**Date:** 2026-08-27 ~09:15 ET
**Supersedes ADDENDUM-03 in full.** Desktop's product knowledge was stale: Claude Opus 5 shipped 2026-07-24 (model id `claude-opus-5`, dateless pinned snapshot; the current Opus, 4.8 is legacy; default on Claude Max; 1M context; 128K max output; effort defaults high; thinking on by default). Operator directs that this is the extraction model. No A/B arm.

## Model pin (before Lane 1″)

`kg/extraction/model_config.yaml`:
```
model_id: claude-opus-5       # operator decision 2026-08-27, ADDENDUM-04; verified against platform.claude.com/docs/en/models/opus-5/overview
effort: high
```
Comment records the prior pin (4.8, task 2026-07-03) and that it is superseded. The model-identity gate pins `claude-opus-5`: any envelope reporting a different `model_id` is discarded unparsed and the run STOPs (unchanged rule). Judge raters unchanged (`claude-opus-4-8` primary rater, `claude-sonnet-5` secondary) — the rater no longer shares a model with the extractor, which is the better-separated design; note it in DD.

Preflight (zero-spend-class, 3 calls): `claude -p "reply with your model id"` — envelope `model_id` must be `claude-opus-5` 3/3. Any other value ⇒ STOP with `model_pin_unavailable` and the RESULT states what came back; do not fall back to 4.8 silently.

`truncation_suspect_tokens` stays 40,000; it is a suspicion floor gated on an unparseable envelope, not an output cap. Record output-token max observed per document in the pilot verdict so we learn whether 128K removes the fallback path in practice.

## Lane 1″ runs on `claude-opus-5` only

Run id `pilot_v035b_opus5`, ceiling 4M. All 5 docs extracted fresh under Opus 5 (the 3 existing v0.3.5 extractions are 4.8-era and are **not** reused — pilot/bulk model continuity, the same rule the July pin was made under). Precondition, threshold, judge protocol, verdict path, PASS/FAIL consequences exactly as ADDENDUM-02. Lanes 2/3 and any future extraction run on the pinned model.

Cost per document from the ledger reported in the verdict, informational.

## Epoch note

A model change is a new extraction instrument. Everything extracted from here is epoch-tagged with the profile (`reextract_v035`) and `model_id: claude-opus-5` on the event; the probe stratifies by epoch, so kernel-v03/4.8 and v035/opus5 are never pooled in a faithfulness estimate. The queue task (00968603) projects the 4.8-era extractions as `stale` for the two re-extract strata only; other strata remain `extracted` until a measurement says otherwise — no blanket re-extraction of 134 docs on a model change without a pre-registered reason.
