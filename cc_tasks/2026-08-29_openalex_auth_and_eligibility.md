# CC Task — OpenAlex auth fix and T0 eligibility gate

**Date:** 2026-08-29. **Repo:** /Users/brock/GitHub/ai-readiness-kg
**Mode:** Zero model spend. Metadata API, code, tests. **Immutable once written.**
**Before starting:** glob and read any `cc_tasks/2026-08-29_openalex_auth_and_eligibility_ADDENDUM*.md`.
**Result:** `cc_tasks/2026-08-29_openalex_auth_and_eligibility_RESULT.md`. Run `seldon cc complete` on this file at the end. Commit and push.

## 1. The defect

`scripts/t0_biblio_harvest.py` authenticates by `mailto=` polite pool. OpenAlex retired the polite pool and the `mailto` parameter and made an API key mandatory on 2026-02-13; unauthenticated callers get a small testing allowance and then hard errors. The harvester is therefore running on a testing allowance it exhausts within a handful of search calls.

`t2_priority.json` records `retryable_by_provider: {"api.openalex.org": 171}` across 149 documents, and the code labels this `daily quota exhausted, retry after reset`. That label is a claim about the world and it is wrong: 178 documents at two or three calls each cannot exhaust a real daily allowance. The consequence is that the nightly job (`com.brock.aikg.biblio-resume`) makes three requests, hits `CONSECUTIVE_QUOTA_STOP`, exits 0, and will never make progress. The guard fires correctly; the diagnosis attached to it is untested.

Operator has placed `OPENALEX_API_KEY` in `~/.wintermute/.env`.

## 2. Fix

1. **Read the key** from `OPENALEX_API_KEY` (env first, then `~/.wintermute/.env`, matching the repo's existing Neo4j credential idiom). Send it as `api_key` on every OpenAlex request. Remove `mailto` from OpenAlex calls; keep it on Crossref, where the polite pool is still live.
2. **Preflight.** If no key resolves, refuse to run with a message naming the fix (`OPENALEX_API_KEY missing; see docs`), and exit non-zero. Do not fall through to an unauthenticated attempt that will be misrecorded.
3. **Split the failure classes.** `provider_auth_error` (401/403/409, missing or rejected key) must be distinct in the record and in `retryable_by_provider` from `provider_quota_exhausted` (429 with a long Retry-After) and from `harvest_error` (transient 5xx/network). Auth error is retryable in the sense that a key fixes it, but it must never print the quota message. Rewrite `QUOTA_NOTE` usage accordingly; keep one constant per class used at both write and detect ends.
4. **Rate-limit headers.** OpenAlex returns `X-RateLimit-Remaining` and `X-RateLimit-Reset`. Read them and record remaining credits on the run summary, so a real exhaustion is evidenced rather than inferred from a Retry-After.
5. **`CONSECUTIVE_QUOTA_STOP` unchanged** in behaviour, but it must trigger only on `provider_quota_exhausted`, never on `provider_auth_error` (an auth stop is a hard exit at preflight, not a nightly no-op).

## 3. Eligibility gate — do not query OpenAlex for documents that cannot be in it

The corpus is majority federal gray literature (statutes, OMB memos, FCSM and agency reports) with no DOI and no scholarly index record. Queuing those as `retryable` forever is what made T0 look like a blocker.

Add a per-document eligibility test evaluated before any OpenAlex call. A document is **eligible** if it has a DOI or arXiv id in its primary URL, a derivable DOI under the existing publisher rules, or a manifest `source_type` in the academic/preprint set. Otherwise it is **ineligible** and is written as `resolution: bibliographic_out_of_scope` with the reason recorded — a terminal state, not retryable, and distinct from `bibliographic_partial` (which remains "every provider answered and none had a record"). Ineligible documents are excluded from the retryable count and from any coverage denominator that implies they are pending.

Report the eligible/ineligible split in the RESULT. This number is the honest ceiling on T0 coverage and should be stated as such.

## 4. Run and verify

1. `python -m kg.biblio resume` to completion. Report resolved / partial / out-of-scope / auth-error / transient counts, and the credit headers observed.
2. Confirm `python -m kg.biblio coverage` denominators reflect the eligibility split.
3. Confirm the nightly launchd job still runs clean against the new preflight.

## 5. Tests (positive-control discipline, methodology §7.5)

Each guard proven by a seeded known-bad, plus a mutation check that the test measures the guard and not something adjacent (the M2 failure mode from task 204bc046):
- Missing key → preflight refuses, non-zero exit, no request issued.
- Stubbed 409 → `provider_auth_error`, quota message absent, `CONSECUTIVE_QUOTA_STOP` not incremented.
- Stubbed 429 with long Retry-After → `provider_quota_exhausted`, stop after three.
- Stubbed 503 → `harvest_error`, retryable, no claim written.
- Gov PDF with no DOI → `bibliographic_out_of_scope`, zero OpenAlex requests issued for it.
- Mutation: disable the eligibility test → the gov-PDF test must fail.

## 6. Out of scope

GROBID; Semantic Scholar, DataCite, CORE, GovInfo rungs (recorded as candidates, not built here); reference-section parsing from Docling output; anything touching `model_stub` or T2.
