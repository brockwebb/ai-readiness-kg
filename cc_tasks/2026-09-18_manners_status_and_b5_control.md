# CC Task: robots.txt status handled per RFC 9309, a two-product control for B5, and D4's membership question closed

**Date:** 2026-09-18
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `cc_tasks/2026-09-18_tool_docs_ingest_RESULT.md` §4 item 7, `2026-09-18_schema_field_rules_RESULT.md` §3 premise 4 and its "Open" list, and `2026-09-18_dcat_field_rules_RESULT.md` §1 (the D4 substring membership question, read there before deciding).
**Implements:** the manners rule (DD-060, DD-062: robots-first, and the RFC the fetcher claims to follow) and E5 (every leg has a control the cycle fires).
**Framework layer served (DN-005 §5 rule 1):** §2.2 Tier M, instrument integrity ahead of cycle 5.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push`. Fixtures on loopback only.

---

## 0. Three instrument defects, each small, each ahead of a measured cycle

1. **`scan.manners.Fetcher._robots_for` parses the response body as robots text regardless of status.** RFC 9309 §2.3.1.3: a 4xx means unavailable, and the crawler may access any resource. §2.3.1.4: a 5xx means unreachable, and the crawler must assume complete disallow (a crawler may treat a long-standing 5xx as unavailable after a reasonable period; this instrument does not, because a cycle is one pass). Today a 5xx with an empty body yields allow. Cycle 5 fetches 16 hosts under this code.
2. **B5 has no control fixture.** Every fixture serves one product on one port, and `CONTROL_LEGS` excludes body legs, so E5's "every declared control fires" holds for B5 vacuously.
3. **D4's substring membership** (the DCAT RESULT §1 left it open): whether a product counts as "in the catalog" when its URL is a substring match rather than an exact `landingPage`/`accessURL`. Read that section, then decide by the DCAT-US document's own definition of the field, quote it, and write the rule the quote supports as `RULE-D4-v2` only if the current behaviour contradicts the quote. If the current behaviour is what the document says, no version moves and the RESULT says so.

**Decisions taken here (operator overrides later):**

1. **`_robots_for` keys on status before it parses.** 2xx: parse. 3xx: follow per the existing redirect policy, then apply this table to the final response. 4xx: allow all, and record `robots_status: unavailable` on the Observation. 5xx, timeout, connection error: disallow all, record `robots_status: unreachable`, and every fetch to that host in the cycle returns `error` with that reason, never `fail` (DD-052 §6). The status and the decision go on the manners log line so gate clause 4 of the cycle template can replay them.
2. **Prior payloads are not re-derived on this change.** Collection code is not judgement code; the stored Observations already carry the bodies they were judged on. `make gate-task`'s byte-identical re-derivation must still pass, which is the proof of that sentence.
3. **A two-product control fixture, `body_two_products`, served on one port with two product pages carrying `DefinedTerm`s that share codes, and a sibling variant that does not.** `params.yaml:e5_control` gains B5 rows derived from the rule source before the controls run, with the derivation comment, as the D2 rows were. `CONTROL_LEGS` admits body legs whose fixture declares `products: 2`.
4. **D4 per item 3 above.** Whatever the answer, the RESULT quotes the DCAT-US sentence it rests on.

**Write set:** `assessment/harness/scan/manners.py` and its tests; the control fixture files and `params.yaml:e5_control`; `rules/__init__.py` (`CONTROL_LEGS`) only if decision 3 needs it; `RULE-D4-v2` and the registry only if decision 4 finds a contradiction, with the record moved through the writer in that case; `scripts/check_protected_manners.sh` (new); `seldon_events.jsonl`; the RESULT. `state/`, `corpus/`, `docs/reports/` byte-identical.

**Immutable once written. Glob `2026-09-18_manners_status_and_b5_control_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Read RFC 9309 §2.3.1 as admitted in the corpus (quote the two clauses), the DCAT RESULT §1, and the D2 control derivation in `params.yaml`.
## 2. Decisions 1 to 4. Tests first.
## 3. Gate
`make gate-task` (re-derivation tier is non-optional here) plus `make gate-full` (`-rs`), the slow control tier run first, `seldon verify`, protected paths. Detached and polled inside this turn per `CLAUDE.md`. Expected skips: 3. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_manners_status_and_b5_control_RESULT.md`: §0 the status table as implemented, with the RFC quotes; §1 the B5 control rows and their derivation; §2 the D4 answer with its quote; §3 every premise this task file got wrong; §4 the gate table, tier named, the re-derivation line quoted. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 → §2 → glob addenda → §3 → §4 → push. Runs after `2026-09-18_registration_commits.md`.
