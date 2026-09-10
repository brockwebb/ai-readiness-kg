# CC Task — scan-frame v5: the seven declared flagships enter the frame, verified robots-first

**Date:** 2026-09-10
**Project:** ai-readiness-kg
**Authored by:** Desktop session. Declarations: `docs/design/fss_flagship_declarations.md` (7 bodies; NCSES keeps the Annual Business Survey from cycle 3).
**Fulfils:** its own ResearchTask (`seldon cc register`). Runs after `2026-09-10_harness_small.md`. Precedes the cycle-4 run task, which is authored from this RESULT and does not exist yet.
**Spend:** zero model calls. **Network:** at most one `robots.txt` read and one identified HEAD-then-GET per declared landing page, 7 pages, on the 19 roster sites, under DD-060 and DD-063 (robots-first, same-site). Report the request count per site. No other request.

**Decisions taken here (operator overrides later):**
1. Each declared landing page becomes a `flagship` surface on its body's site in targets v5 (`COMPUTED_FROM` v4), only if the verification under §1 returns 200 after redirects on the same site. A 403 from a host already recorded as refusing the identified client (BLS, BTS, SSA) is expected and the surface is still declared, marked `refused_at_declaration`; the cycle measures it as refused.
2. Any other outcome (404, off-site redirect, timeout) is a finding about the declaration and a stop: the RESULT names it and the surface is NOT added. Nothing is substituted. The operator re-declares.
3. `fss_agencies_pending_operator_declaration_2026-09` stays registered as it is (a cycle-3 fact). A new Result `fss_agencies_pending_operator_declaration_2026-09-10 = <remaining after this task>` is registered against v5.

**Zero edits to:** shipped rule modules, registered Result values, prior RESULTs, cycle evidence, report prose, targets v4.

**Immutable once written. Glob `2026-09-10_scan_frame_v5_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Verify the seven, robots-first, identified client, through the fetcher (never a bare request). Record status, final URL, same-site check, and the robots verdict per page as Observations.
## 2. Build targets v5 per decisions 1 and 2. Surface count, site count, body count registered as Results against v5.
## 3. Gate (the one gate of this task)
Every one of the seven has a recorded Observation with a status; every added surface is same-site to its body; fixture gate and fast tier green; `seldon verify`; protected paths. The request log shows exactly the requests §1 permits and no other.
**Failure: report and stop, RESULT with the block on top, commit, push.**
## 4. Report
RESULT `cc_tasks/2026-09-10_scan_frame_v5_RESULT.md`: the seven, status by status, which entered, which stopped and why. `seldon cc complete`, commit, push. **Cycle 4 is not run by this task.**

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push.
