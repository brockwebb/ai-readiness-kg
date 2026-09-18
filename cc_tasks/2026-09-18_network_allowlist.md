# CC Task: a task declares its network as an allowlist, and the dispatcher launches it

**Date:** 2026-09-18
**Project:** ai-readiness-kg (dispatcher change and tests in `/Users/brock/GitHub/seldon`; DN-006 addendum and `CLAUDE.md` sentence here)
**Authored by:** Desktop session, from the operator's ruling of 2026-09-18: acquisition is an agentic step; a human enters only when a credential or a block makes it impossible. Today DN-006 c5 refuses every task whose `Network` header is not `none`, so any corpus ingest waits for a hand.
**Implements:** DN-006 decision 2 (eligibility criteria), amended: network is a declared budget like spend, not a binary.
**Framework layer served (DN-005 §5 rule 1):** none. Dispatch path.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher.
**Spend:** zero model calls. **Network:** none beyond `git push` to both repos' own remotes.

---

## 0. The rule as it stands and the shape it takes

`seldon/core/dispatch.py` c5 (`_NETWORK_NONE_RE`) passes a task only when the `**Network:**` header matches `none` (with the `beyond git push` phrasing tolerated). The header was a binary because the first dispatched tasks needed nothing; it was never a design claim that unattended sessions must not fetch. The harness already has the discipline an unattended fetch needs: robots-first, identified UA, every request logged with status, evidence retained by hash (`scripts/fetch_noaa_esip_sources.py`; `CLAUDE.md` manners). Prior art for the shape: egress allowlists are how CI runners and sandboxes declare network (GitHub Actions `permissions` and OpenSSF's egress policy; Nix and Bazel sandboxes deny by default and allow named fetches with hashes). A declared allowlist of hosts plus a fetch log is the same contract at task granularity.

**Decisions taken here (operator overrides later):**

1. **The header grammar.** `**Network:** none` (unchanged), or `**Network:** allowlist: host1, host2, …` with exact hostnames, no wildcards, no schemes, no paths. Anything else fails c5 with a message quoting the grammar. `beyond git push` stays implied for both.
2. **c5 passes an allowlist task**, and `dispatch_launched` records the parsed list as `network_allowlist`. The child gets `SELDON_NETWORK_ALLOWLIST` (comma-separated) in its environment.
3. **The session-side contract is the existing fetch discipline, made checkable.** A fetch helper in this repo (`scripts/fetch_allowlisted.py`, from `fetch_noaa_esip_sources.py`'s pattern: robots-first, identified UA, one log line per request with URL, status, bytes, sha256) refuses any URL whose host is not in `SELDON_NETWORK_ALLOWLIST`, and refuses to run when the variable is unset. The RESULT of an allowlist task quotes its fetch log whole. A test drives the helper with an off-list host and asserts refusal before any socket opens.
4. **Enforcement is declarative plus audit, not a network sandbox.** macOS offers no cheap per-process egress filter, so the dispatcher does not claim one. The RESULT says so, and the DN-006 addendum records that the allowlist is a declared budget audited by the fetch log, the same standing as `Spend`.
5. **The Desktop can still fetch with its own tools; it does not.** Corpus acquisition goes through the helper so the ledger's `acquisition_method` and `acquired_by` stay uniform. One sentence in `CLAUDE.md`'s corpus section.

**Write set:** `seldon/core/dispatch.py`, `seldon/commands/dispatch.py` (the env var), their tests, in the Seldon repo; `scripts/fetch_allowlisted.py` (new), `tests/test_fetch_allowlisted.py` (new), `CLAUDE.md` (two sentences: the header grammar beside the Spend line, and decision 5), `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_0N.md` (next free number; glob first), `seldon_events.jsonl`, the RESULT. `docs/` otherwise byte-identical.

**Immutable once written. Glob `2026-09-18_network_allowlist_ADDENDUM*.md` before starting and again before §3.**

---

## 1. Seldon repo: decisions 1 and 2, tests first. Suite green, 0 skipped. Merged, pushed.
## 2. This repo: decisions 3 to 5.
## 3. Gate
`make gate-fast` (`-rs`), `seldon verify`, protected paths. Detached and polled inside this turn per `CLAUDE.md`. Failure ships nothing.
## 4. Report
RESULT `cc_tasks/2026-09-18_network_allowlist_RESULT.md`: §0 the grammar and c5's new refusal messages; §1 both repos' commits; §2 the helper's refusal test output; §3 every premise this task file got wrong; §4 the gate table, tier named. `seldon cc complete`, commit, push.

**SEQUENCING:** §1 (merged before §2) → §2 → glob addenda → §3 → §4 → push both repos.
