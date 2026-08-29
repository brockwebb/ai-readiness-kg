# RESULT — 2026-08-29_openalex_auth_and_eligibility

**Date:** 2026-08-29. **Zero model spend** — metadata API, code, tests. No addenda existed
(globbed).

**T0 is complete. `retryable: 0`.** 38 of 44 eligible documents resolved, 6 genuine findings,
134 out of scope, 0 pending. The whole corpus cost **349 OpenAlex credits of a 10,000/day
budget** — 3.5% of one day. The blocker was never volume.

---

## 1. The premise, verified against the live API before any code was written

The task's diagnosis is correct, and the probe sharpened it in a way that changed the design:

| request | result |
|---|---|
| `mailto=`, no key | **HTTP 429** `Insufficient budget … you only have $0 remaining` |
| no key at all | **HTTP 429**, byte-identical — so `mailto` now buys exactly nothing |
| **invalid** key | **HTTP 401** `Invalid or missing API key` |
| valid key | **HTTP 200**, `X-RateLimit-Limit: 10000` |

**The load-bearing finding: a *missing* key returns 429, not 401.** At the status line it is
indistinguishable from a genuine daily exhaustion. So no post-hoc classifier can separate
them — the *only* place the distinction can be drawn is preflight, before the first request.
That is why §2.2's preflight is not belt-and-braces; it is the sole mechanism.

Credit costs, measured: DOI lookup **1 credit**, title search **10**. 178 documents at two or
three calls each cannot approach 10,000 — confirming the task's arithmetic that the quota
label was false on its face.

## My error, plainly

Yesterday I wrote `daily quota exhausted, retry after reset` into 149 documents and reported
it as a measured finding, including in a commit message. The HTTP 429 was real; the
**diagnosis attached to it was not**, and I had not tested the attribution. The task is right
that "the guard fires correctly; the diagnosis attached to it is untested." Retracted here.

## 2. Fix

- **Key** from `OPENALEX_API_KEY` (env → `~/.wintermute/.env`), same idiom as
  `build_projection._neo4j_creds`. Sent as `api_key` on every OpenAlex request.
- **`mailto` removed from OpenAlex, kept on Crossref**, whose polite pool is still live.
- **Preflight** refuses with a non-zero exit naming the fix, issuing no request.
- **Three failure classes**, one constant each used at both the write and detect ends:

| class | trigger | what fixes it |
|---|---|---|
| `provider_auth_error` | 401/403/409 | a key. **Never** the quota message; hard exit, never a nightly no-op |
| `provider_quota_exhausted` | 429 + long `Retry-After` | the UTC reset |
| `harvest_error` | 5xx / network | a retry now |

  **Auth outranks quota in classification.** With no valid key every request returns a budget
  message, so a keyless run would otherwise report every document as quota-exhausted — which
  is precisely what happened.
- **Credit headers** (`X-RateLimit-Remaining`/`Limit`) recorded and reported, so a real
  exhaustion is *evidenced by the provider* rather than inferred from a `Retry-After` shape.
- **`CONSECUTIVE_QUOTA_STOP` unchanged**, now keyed to the quota class only.

## 3. Eligibility gate — and one correction to it

**44 eligible / 134 ineligible.** 44 is the honest ceiling on T0 coverage.

| doc_type | eligible | ineligible |
|---|---|---|
| academic | 35 | 0 |
| federal | 5 | 40 |
| intergovernmental | 2 | 11 |
| practitioner | 2 | 6 |
| industry | 0 | 47 |
| standard | 0 | 30 |

**Discrepancy reported, not reconciled: the task specifies `source_type`; no manifest entry
has that field.** The real field is `doc_type`, populated 178/178. Implemented against the
real field; the intent was unambiguous.

**One clause added to the rule as written, on evidence.** The literal rule (DOI ∨ arXiv ∨
academic type) is falsified by data already in hand: **9 already-resolved documents are
outside the academic types and carry no DOI** — they were found by title search. Under the
rule as stated they would be relabelled `bibliographic_out_of_scope`, asserting "no scholarly
index holds this" over records we are holding. So eligibility also accepts *an existing
resolution as proof of eligibility*. A prior **failure** confers nothing — tested for all
four failure states, since that is where the clause could become a loophole.

**What the gate costs, stated so it can be overridden cheaply.** The 134 ineligible documents
were never asked, so their absence from OpenAlex is a *prediction*, not a measurement. At 10
credits per title search, converting all 134 predictions into measurements costs ~1,340
credits — 13% of one day. If you want that measured rather than assumed, it is one flag and
one night; I did not do it because §3 pre-registers "evaluated before any OpenAlex call" and
§5 tests zero requests for an ineligible document.

## 4. Run and verify

```
eligible 44 | out_of_scope 134 | resolved 38 (38/44) | partial_finding 6
retryable 0 | auth_error 0 | quota_exhausted 0 | transient_error 0
openalex_credits_remaining 9651 / 10000
```

Resolutions: `arxiv_then_title` 13, `doi` 10, `crossref_title_search` 8, `arxiv_doi` 5,
`title_search` 2. Providers: openalex 30, crossref 8.

**The 6 `bibliographic_partial` are this project's first real findings of that class** (it was
0 before, because every unresolved document was a failure, not an answer): `bandi-2025`,
`mons-2026`, `nalla-2025`, `the-nation-s-data-at-risk`, `venkit-2025-deeptrace`,
`wu-2025-what-generative-search-engines-like`. Every provider was asked and none had a record.

**Nightly job verified clean against the new preflight** (`launchctl kickstart`): rc=0, both
guardrails held, and it now reports `coverage: COMPLETE — no retryable documents remain`.

## Three defects found while verifying, all fixed

**1. The arXiv branch was a permanently malformed query.** All 7 remaining failures were
`HTTP 400`: `locations.landing_page_url.search is not a valid field`. A 400 is not a transient
condition — those 7 were queued to retry forever against a request that could never succeed,
the same "pending forever" pathology this task fixes, one layer down. Replaced with arXiv's
deterministic DOI (`10.48550/arXiv.<id>`) — the same class of mechanical derivation as the
existing nature.com and aclanthology.org rules. **5 of the 7 resolved; the other 2 are
genuinely not in OpenAlex** and are now honest `bibliographic_partial`.

Two of those five were being rejected by the **title guard** despite the DOI naming them
exactly (AIDRIN; the school AI-readiness paper). A DOI is an exact identifier, so a fuzzy
title guard is the wrong instrument — the plain-DOI branch has never used one. The derived
route now matches that treatment.

A malformed query is now **counted and surfaced** in the run summary as a harness bug, because
the previous version filed it as ordinary provider flakiness and it sat unseen.

**2. Two published views of the corpus disagreed.** `manifest_table.md` reported "T0 resolved
29" while `kg.biblio coverage` reported 38. Cause: three sites had each hand-rolled their own
"unresolved" list, and they drifted when the failure classes split. Now imported from
`kg.biblio` — one definition. A test fails if a hand-rolled list reappears.

**3. `--phase project` could never advance its own T0 column.** The `biblio` table was written
only by `--phase index`, which re-embeds the whole corpus. So the nightly projection
republished a T0 number that was structurally frozen. Extracted `sync_biblio` (178 JSON reads
and upserts, no embedding) and called it from `phase_table`.

## 5. Tests: 287 → **303 passed**. Mutation matrix 10/10 killed

| mutation | result |
|---|---|
| M12 eligibility gate disabled | KILLED |
| M13 preflight made permissive | KILLED |
| M14 401 folded back into transient | KILLED |
| M15 auth no longer outranks quota | KILLED |
| M16 resolved-record clause dropped | KILLED |
| M17 `mailto` sent to OpenAlex again | KILLED |
| M18 `out_of_scope` treated as retryable | KILLED |
| M19 credit headers not recorded | KILLED |
| M20 `project` no longer refreshes T0 | KILLED *(after amendment)* |
| M21 hand-rolled unresolved list restored | KILLED |

**M20 initially SURVIVED — the M2 failure mode for the third time in three tasks.** The test
called `_sync_biblio_if_possible()` directly, so deleting the call from `phase_table` left it
green: it proved the sync *works*, not that the projection *uses* it. Rewritten to drive
`phase_table` and assert the published file. **The rule I keep re-learning: a guard test must
enter through the real entrypoint, or it measures the guard's neighbour.**

Also pinned: `RETRY_STATES` (harvester) ⊇ `RETRYABLE` (`kg.biblio`). A state retryable in one
and absent from the other would be permanently stuck — counted as pending, never retried.

## 6. Not done, per §6

GROBID; Semantic Scholar / DataCite / CORE / GovInfo rungs; reference-section parsing;
anything touching `model_stub` or T2. The 134 ineligible documents remain predictions rather
than measurements (see §3 for the cost of changing that).
