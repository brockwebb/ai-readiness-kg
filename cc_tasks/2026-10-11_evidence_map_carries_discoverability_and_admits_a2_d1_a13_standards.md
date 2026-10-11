# CC Task: the evidence map carries the discoverability finding, and the standards behind A2, D1 and A13 are admitted so their numbers can be quoted

**Date:** 2026-10-11
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from the RESULTs of part 2 (`2026-10-07_seed_known_locations_verify_RESULT.md` §4, §5.9, Next) and the concise report (`2026-10-07_concise_report_prose_RESULT.md` §5.1).
**Implements:** DN-013-R1 (existence and discoverability are separate findings, and the report's centre is the gap between them).
**Framework layer served (DN-005 §5 rule 1):** §2.2, measurement, and the evidence floor (DN-001).
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none
**Spend:** est. 1M tokens (Opus). Read it as 2 to 4x low. No harness model call. Four document fetches, then evidence-map and view regeneration.
**Network:** allowlist: spec.openapis.org, spdx.org, creativecommons.org, www.rfc-editor.org

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Measured premises (verify before acting; report any that is wrong)

- `docs/evidence/FROZEN.md` names `scan_2026-10-07_composite_d` at `cd0ccae6de99`. The report cites it and no other.
- The headline of DN-013-R1, "15 body × object pairs, in 11 bodies, where the object exists and no product page reaches it, out of 29 where it exists" (54 of 88 per surface), is in `docs/research/2026-10-11_seeded_delta.md` (`scripts/seeded_delta.py`) and in no claim in `docs/evidence/claims.yaml`. So the concise report could not state it, and its centre became denials, absences and passes instead.
- `ind:A2` and `ind:D1` reach no admitted source, so the report states their verdicts in words, untagged (part 2 §5.9). RFC 9727 is named by `RULE-A13-v1` but not admitted (part 1 §3).
- The corpus admission path exists: `scripts/admit_commerce_guidance.py` and `cc_tasks/2026-10-02_commerce_guidance_admission.md` are the most recent precedent. Follow its conventions (identity, capture, sha, licence, the protected-paths script) and say where you departed from them.

## Decisions

1. **Admit four standards, as documents, at the versions the rules read:**
   - OpenAPI Specification 3.1 (spec.openapis.org), for `ind:A2`'s "parses as an API description" (RULE-A2-v6 also accepts Swagger 2.0; admit 2.0 too only if the rule's text cites it).
   - SPDX License List (spdx.org), for `ind:D1`'s "licence stated as an identifier".
   - Creative Commons licence deeds or the legal-code index (creativecommons.org), only if `RULE-D1-v6` names Creative Commons; if it does not, do not admit it, and say so.
   - RFC 9727, "api-catalog: A Well-Known URI and Link Relation to Help Discovery of APIs" (www.rfc-editor.org), for `ind:A13`.
   Each is admitted through the same path as the Commerce guidance, with its licence recorded. An admitted source binds to an indicator only where the rule's text already cites it; no rule changes.
2. **Discoverability claims.** Add claims to `docs/evidence/claims.yaml` through `scripts/build_evidence_map.py`, never by hand. At least: the 15 of 29 headline; the per-object breakdown (API, terms, changelog, inventory); the A13 verdicts per body; and the convention result (no host serves `application/linkset+json`; no page sends `rel="api-catalog"`). Each claim cites `_composite_d` Findings and the delta's Results, and quotes no number that is not in a Finding or a registered Result. If the delta's headline is not yet a registered Result, register it (`seldon result register`) with `scripts/seeded_delta.py` as its generator before the claim cites it.
3. **A2 and D1 become quotable.** Once their sources are admitted, the claims that state A2 and D1 verdicts carry their tags, and DN-001's floor passes on them. Report the before and after floor count.
4. **Nothing in the frozen composite moves.** No cycle, rule, Finding or Result of `_composite_d` changes; FROZEN.md is byte-identical. The evidence map is a view and is rebuilt; the report is not rebuilt here (the operator reads the current one first; the rewrite is its own task).

**Write set:** the admission script and its captures, the corpus records the admission path writes, `docs/evidence/claims.yaml` (via its builder), any `scripts/build_evidence_map.py` change needed to emit the new claims, registered Results, regenerated views, a protected-paths script, the RESULT. Byte-identical: every rule, collector, `manners.py`, `score.py`, every payload, `docs/evidence/FROZEN.md`, `reports/`.

## Gate

`make gate-task`. Quote passed, skipped, xfailed, deselected and wall clock. `build_evidence_map.py --check` clean. `seldon verify`. The protected-paths diff.

## RESULT

Under 50 lines: the four admissions (url, captured_at, sha256, licence; or why one was not admitted); the claims added, with ids and their text; the DN-001 floor before and after; premises wrong; logs. `seldon cc complete`, commit, push.
