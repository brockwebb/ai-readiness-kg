# CC Task — report-draft closeout, then manners: read robots.txt before any fetch, and bound contact to the site

**Date:** 2026-09-09
**Project:** ai-readiness-kg
**Authored by:** Desktop session, OODA on `2026-09-09_report_draft_RESULT.md`. Verified on the graph: `e1b7cd4b` still `proposed`; RESULT §6 carries `<SUITE>` and `<PROTECTED>` unfilled; no `cc complete` recorded.
**Fulfils:** its own ResearchTask (`seldon cc register`). Part of `520ec74b` (cycle-4 maintenance), item (1); the rest of `520ec74b` stays queued.
**Spend:** zero model calls. **Network: none.** Fixtures on loopback only. No federal host.

**Premise (from report-draft RESULT §3, read against the request log by CC):** cycle 3 issued `GET https://samhsa.gov/sitemap.xml` and `GET https://data.gov/sitemap.xml` without having fetched either host's `robots.txt`. `manners` gates on-roster hosts but the sitemap follower dereferences a declared URL on any netloc without the robots pre-read. scan-run-3b RESULT §2's account ("only robots.txt was fetched") is falsified by the log and stays on the record as falsified; this task does not edit it.

**Decisions taken here (operator overrides later):**
1. **Robots-first is unconditional.** No collector issues any request to a netloc whose `robots.txt` this cycle has not fetched and parsed first. Enforced in the fetcher, not in each collector, so a new collector cannot forget it.
2. **The contact bound is the site, not the netloc.** A site is a registrable domain per the Public Suffix List (`publicsuffix2` or `tldextract`, pinned; the list snapshot's date is a registered param). The roster becomes a list of sites; every netloc under a roster site is in scope; `www.samhsa.gov` and `samhsa.gov` are one site. Prior art: the "same site" definition in the WHATWG URL/Fetch standards, which uses the same registrable-domain test.
3. **Off-site declarations are observed, not followed.** A `robots.txt` that declares a sitemap on another site produces an observation `sitemap_off_site` with the declared URL, and no request. A5 treats an off-site declaration as `not_applicable` for discovery-by-sitemap, with the reason on the Finding, never as `fail`. New rule version for A5 (`RULE-A5-v<next>`), predecessor untouched.
4. **Frame unit stays the body (agency).** Sites are the contact unit; bodies are the denominator. Both counts registered per cycle.

**Zero edits to:** shipped rule modules, any prior RESULT (report-draft's §6 excepted, below), registered Result values, cycle-3 evidence, the report file.

**Immutable once written. Glob `2026-09-09_closeout_and_manners_ADDENDUM*.md` before starting and again before §3.**

---

## 0. Close out report-draft
Run the full suite and the protected-paths diff for `e1b7cd4b`. Replace the two placeholders in `cc_tasks/2026-09-09_report_draft_RESULT.md` §6 with the results, dated, and nothing else in that file. If the suite is red, stop here and report; the report stays a draft. If green: `seldon cc complete e1b7cd4b`, commit, push. Then continue.

## 1. Fixture and derivation first
A new loopback fixture `sitemap_on_sibling`: a host whose `robots.txt` declares its sitemap on a second loopback netloc (two ports is acceptable if the site resolver treats them as one site; state which mechanism and why). Under the current code its expected behaviour is the defect: a GET to the sibling with no robots pre-read. `fixture_expectations.py` derives the row; it should report the defect as a difference before any code changes. If it cannot see the defect, extend the derivation (it must know which collectors dereference declared URLs), and say so.

## 2. Fix
Decisions 1 to 3. Robots-first in the fetcher; site resolver; `sitemap_off_site` observation; `RULE-A5-v<next>`; roster file gains `site` per host (a new targets version, `COMPUTED_FROM` v2). Unit tests for: same-site sibling followed after its own robots read; off-site declaration observed and not fetched; a netloc with no robots yet is never GET.

## 3. Gate (the one gate of this task)
Seven-fixture control gate (the six plus `sitemap_on_sibling`) against derived tables, `unknown` = 0. Byte-identical re-derivation of all eight prior payloads under their own rules. A test that replays cycle 3's request log through the new fetcher policy and reports which requests it would have refused: expected exactly the two apex sitemap GETs, and they are reported by URL. Hygiene green; full suite; `seldon verify`.
**Failure writes no params change and no tool map: report and stop, RESULT with the block on top, commit, push.**

## 4. Report
RESULT `cc_tasks/2026-09-09_closeout_and_manners_RESULT.md`: §0 outcome first, then the gate, the fixture mechanism chosen, the replay result, every premise this task got wrong. Append DD-062: robots-first is enforced in the fetcher; the contact unit is the site (PSL registrable domain); off-site declarations are observed, not followed. `seldon cc complete`, commit, push. **No federal host is contacted by this task; cycle 4 is a separate task.**

**SEQUENCING:** §0 (hard stop if red) → §1 → §2 → glob addenda → §3 (hard stop) → §4 → push.
