# CC Task — manners closeout: site key is the roster host, one contact policy, a script guard, and the RESULT waits for the suite

**Date:** 2026-09-09
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-09_closeout_and_manners_RESULT.md`. Verified: `4956af18` still `proposed`; RESULT §1 and §6 carry `<SUITE>`, `<VERIFY>`, `<PROTECTED>` unfilled; no `cc complete`. Second consecutive task with this shape.
**Fulfils:** its own ResearchTask (`seldon cc register`). Completes `520ec74b` item (1) with `4956af18`.
**Spend:** zero model calls. **Network: none.** Loopback fixtures only. No federal host.

**Decisions taken here (operator overrides later):**
1. **Site key is the roster host, not the registrable domain.** DD-062's "site = PSL registrable domain" is superseded: it admitted whole department domains (`usda.gov`, `ed.gov`, `ojp.gov`, `cdc.gov`, `nsf.gov`) and merged ERS, NASS and APHIS into one site. The key for a roster host is that host with one leading `www.` stripped; a netloc is same-site if it equals the key or ends with `.` + key. Prior art: cookie domain-matching, RFC 6265 §5.1.3. Consequences the gate must show: 19 sites for 19 roster hosts; `samhsa.gov` same-site as `www.samhsa.gov`; `catalog.data.gov` same-site as `www.data.gov`; `nass.usda.gov` and `www.usda.gov` NOT same-site as `www.ers.usda.gov`. The PSL dependency is removed unless something else uses it.
2. **One contact policy.** `on_roster_host` (links) and the declaration bound (sitemaps, pointers) use the same site-key test. `params.manners.same_host_only` is retired or redefined as the single `same_site` policy; a declared or linked URL off-site is observed, never fetched. Targets v3 → v4 with `site_key` per host, `COMPUTED_FROM` v3.
3. **A script cannot write into the committed evidence store.** The evidence writer refuses to write under `corpus/evidence/` unless invoked by the cycle runner (an explicit token or env set only by `run_cycle`); every other caller is redirected to a quarantine root and the redirect is logged. Fixture drivers and ad-hoc scripts hit that path by default. Test: a direct collector call from a script lands in quarantine.
4. **The RESULT waits for the suite.** No RESULT file is created until the full suite, `seldon verify` and the protected-paths diff have run to completion and their output is on disk; the RESULT is then written from that output. If the session cannot reach that point, the RESULT is still written and its §1 says "suite not run" in words, never a placeholder. Add this as a rule to CLAUDE.md under the RESULT protocol, and remove `<SUITE>`-style placeholders from any RESULT template that has them.

**Zero edits to:** shipped rule modules, prior RESULTs except filling the three placeholders in `2026-09-09_closeout_and_manners_RESULT.md` (§0 below), registered Result values, cycle evidence, the report.

**Immutable once written. Glob `2026-09-09_manners_closeout_ADDENDUM*.md` before starting and again before §3.**

---

## 0. Close out `4956af18`
Run its full suite, `seldon verify`, protected-paths diff. Fill the three placeholders in its RESULT §1 and §6 with the results, dated, nothing else. If red, stop and report. If green: `seldon cc complete 4956af18`, commit, push. Then continue.

## 1. Decisions 1 to 3
Implement. Unit tests for every consequence listed under decision 1, the unified policy under decision 2, and the script redirect under decision 3. DD-063 appended: site key defined; DD-062's PSL clause superseded and why (17 sites, department domains admitted); one contact policy; script guard.

## 2. Decision 4
CLAUDE.md rule; template placeholders removed.

## 3. Gate (the one gate of this task)
Seven-fixture control gate against derived tables, `unknown` = 0; `fetcher gates every request: True`; byte-identical re-derivation of all eight prior payloads; replay of cycle 3's log under the unified policy reports 24 netlocs contacted, 2 without a robots read, 0 refused, and, new, 0 off-site fetches; targets v4 shows 19 site keys. Hygiene green; **then** full suite, `seldon verify`, protected paths, all complete before the RESULT is opened.
**Failure writes no params change and no tool map: report and stop, RESULT with the block on top, commit, push.**

## 4. Report
RESULT `cc_tasks/2026-09-09_manners_closeout_RESULT.md`, written only after §3's suite output exists. §0 outcome first, gate, the 19 site keys as a table, every premise this task got wrong. `seldon cc complete`, commit, push. **Cycle 4 is not run by this task and is not the next task; it waits on the operator's flagship declarations.**

**SEQUENCING:** §0 (hard stop if red) → §1 → §2 → glob addenda → §3 (hard stop; suite completes before any RESULT text) → §4 → push.
