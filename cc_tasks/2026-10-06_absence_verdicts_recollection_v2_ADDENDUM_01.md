# ADDENDUM 01 to `2026-10-06_absence_verdicts_recollection_v2.md`: the legs and declarations the rules task's RESULT widened

**Date:** 2026-10-06. Desktop session, from `cc_tasks/2026-10-06_absence_verdicts_rules_RESULT.md` §1, §3 and §5. Amends the base task; nothing in it is superseded. Still operator-launched (DN-012 d6); still not a dispatcher candidate.
**Implements:** DN-012 d3, d6.

## What changed

The rules task's inventory found four legs beyond the three the audit named, so generation 14 covers twelve legs: A1, A2, A3, A9, B1, B3, B4, D1, D3, D4, F4, G4. Every A2, A9, D1, F4 and D4-family absence is now `error` on every declared surface until the body's locations are declared, and five product legs are unmeasured on all 23 surfaces. The base task's decision 2 names only A1, A2, A3 and the D4 family. The declaration fields also grew: `api_base.terms_url` and `changelog_urls` exist and are empty for every body.

## Amendments

1. **Decision 1, declarations, widened.** For every body in `targets.yaml` `declared_locations` (the frame's 16, not the 14-agency roster rows), resolve and write with the page each was read from:
   - `api_base` (14 bodies still lack it; CENSUS and NASS are declared);
   - `api_base.terms_url` (the API's terms page, spec:D1) for every body that has an `api_base`;
   - `changelog_urls` (spec:F4: the product's or site's change log or release notes page);
   - the department `inventory_urls` entry for BLS and BTS, whose own pages 403'd on every cycle; read the department host from the department's home page, not from memory;
   - the `catalog.data.gov` organization URL for all 16 (the organization slug, read from catalog.data.gov's organization list).
   A location the body's own site does not publish is recorded as `not_declared` with the pages searched, and stays `error` under d1. That is the finding.

2. **Decision 2, legs, widened.** Collect A1, A2, A3, A9, B3, D1, F4 and the D4 family (D4, B1, B4, D3, G4) on the 16 bodies. The three reference hosts carry only `tier0.legs` and are not in this frame (RESULT §5.9). B3 follows every methodology link on the page, not the first.

3. **Decision 5, the delta table, widened** to all twelve legs. The named cases: Census ACS A2 ("documented API base declared and not probed"), the 28 D4 "no catalog" rows, and the 40 A9, D1 and F4 rows per leg that flipped on no declaration at all.

4. **Launch under the dispatcher's rule.** DN-006 decision 10 forbids a hand dispatch while `dispatch.enabled` is true. The operator launches this task as: `touch .seldon/DISPATCH_STOP`, wait for the lease to clear (`seldon dispatch status`), paste the dispatch line, and remove the STOP file at the session's close. The RESULT records the STOP's appearance and removal times.

5. **Report.** Add to the RESULT: declarations resolved per field per body (a 16 by 5 table), and the count of product legs still unmeasured on every surface after the recollection, against the five the rules task left.
