# CC Task: the Seldon suite's Neo4j tier fails when it cannot run; it does not skip and call itself green

**Date:** 2026-09-16
**Project:** ai-readiness-kg (every code change lands in `/Users/brock/GitHub/seldon`; the RESULT-format sentence and the re-read of recent RESULTs land here)
**Authored by:** Desktop session, from `cc_tasks/2026-09-16_dispatcher_commits_its_record_RESULT.md` §5.5, §6 row 3 and §7.1, and from the `seldon go` output of 2026-09-16 that listed `c609b1e1` as `graph=in_progress` and "blocked by the dispatcher" after the graph had it `completed` at `2026-09-16T16:00:29Z`.
**Implements:** the RESULT-waits-for-the-suite rule in `CLAUDE.md` (operator-ordered 2026-09-09): a gate line that quotes a number the reader cannot check is a placeholder; a green that is 730 skips is a placeholder with a number on it.
**Framework layer served (DN-005 §5 rule 1):** none. Gate integrity for both repos.
**Fulfils:** its own ResearchTask (`seldon cc register`). Launched by the dispatcher after `2026-09-16_headless_session_polls_to_completion.md` completes; this is the first session launched under that task's prompt clause, and §0 of the RESULT is its observation.
**Spend:** zero model calls. **Network:** none beyond `git push` to both repos' own remotes.

**HEADLESS NOTICE.** Under `claude -p` there is no next turn. Every command longer than two minutes is detached with its `EXIT=` line appended to its log and polled in this turn with `sleep 240; tail -5` until that line appears. Never use background-task mode; never wait to be notified.

---

## 0. The defect, stated once

`seldon/tests/conftest.py` reads `NEO4J_USERNAME` and `NEO4J_PASSWORD`. This machine exports `NEO4J_USER` and `NEO4J_PASS`, which `seldon/config.py:73` already accepts for production code. With neither pair set the fixture skips, so an ordinary shell reports `1177 passed, 730 skipped, EXIT=0` and every RESULT that quoted "Seldon suite green" without a skip count may have been quoting that. The 14 tests of `c609b1e1` were among the skips on the first run. `seldon/.env` holds the right values but nothing loads it, and `set -a; . .env` cannot, because the password carries an apostrophe and the value is unquoted (RESULT §5.5 has the shell error).

Prior art for the rule chosen below: a skipped test is a distinct outcome from a passed one in every test protocol that has one (TAP `# SKIP`, JUnit `<skipped/>`, pytest `-rs`), and the reason a protocol distinguishes it is so a reader can refuse to count it. Rust's `#[ignore]` runs only under an explicit `--ignored`; pytest's `xfail(strict=True)` turns an unexpected outcome into a failure. The shape is the same: an excused test is excused explicitly, by someone, on the record. A suite that excuses 38 percent of itself because an environment variable is spelled differently is not excused by anyone.

**Decisions taken here (operator overrides later):**

1. **One credential resolver.** `conftest.py` resolves Neo4j credentials through the same function production code uses in `seldon/config.py` (both name pairs, then the `~/.wintermute/.env` fallback that function already has). No second parser; no shell sourcing of `.env`. If `seldon/.env` is still wanted, it is loaded by that resolver with a parser that handles quoting, or it is deleted; the RESULT says which and why.
2. **Fail, do not skip, unless explicitly excused.** With Neo4j unreachable or credentials unresolved, the fixture raises a failure whose message names the two name pairs and the fallback path. Skipping is permitted only when `SELDON_TESTS_ALLOW_NEO4J_SKIP=1` is set in the environment, which nothing on this machine sets. The negative control is part of the gate: one run with every credential variable unset and the excuse unset, quoted in the RESULT, must show the fixture's failure, not a skip.
3. **Every gate line in every future RESULT quotes passed, skipped, xfailed and deselected.** One sentence added to `CLAUDE.md`'s "The RESULT waits for the suite" section, after the placeholder paragraph: a gate row that omits the skip count is a placeholder. `Makefile` targets in this repo are not changed; they already print the counts, and the rule is on the reader of the line.
4. **`seldon go` reads the live graph, not the finish event.** The Dispatcher block of `seldon go` listed `c609b1e1` as `graph=in_progress` and under "Blocked by the dispatcher" at a time the graph held `completed`. The block is reading `graph_state_observed` off the last `dispatch_finished` event. It reads the artifact's current state instead, and a task no longer in `blocked` is not listed as blocked. A test asserts it against a store where a `dispatch_finished{ok: false}` is followed by a `blocked -> in_progress -> completed` walk by another actor.
5. **Diagnose, do not fix, the session_id smear.** The hand-dispatched session's `artifact_updated` and `artifact_state_changed` events for `c609b1e1` (`e504dc63`, `b9cb5f08`, `ee6d74aa`, actor `cc`) carry `session_id` `87ea77ee-...`, which is the dispatcher's session id from the launch at 14:34Z. Find where `seldon cc complete` obtains its session id. If it reuses the last id in the store, say so in the RESULT with the line number and file an Issue; if it was set by the operator's environment, say that. Do not change it here: the write set below does not include it, and a provenance change is its own task.
6. **The re-read.** List every `*_RESULT.md` in both repos dated 2026-09-01 or later whose gate table or prose claims the Seldon suite green. For each, quote the passed and skipped counts if the file has them, or write `no skip count recorded`. This is a table in the RESULT, nothing more: which greens were greens is now a known unknown with a list, not a suspicion.

**Write set, derived from the decisions:** `seldon/tests/conftest.py`, `seldon/config.py` only if the resolver needs a signature the fixture can call, `seldon/commands/go.py` (or wherever the Dispatcher block is rendered) and the tests for decisions 2 and 4, in the Seldon repo; `CLAUDE.md` (one sentence) here; `seldon_events.jsonl` by this task's state transitions; the RESULT. Nothing else. The protected-paths check asserts `docs/` byte-identical.

**Immutable once written. Glob `2026-09-16_neo4j_fixture_fails_not_skips_ADDENDUM*.md` before starting and again before §4.**

---

## 1. Seldon repo: decisions 1, 2 and 4 with their tests. Three suite runs, each detached, logged and polled: (a) credentials exported as `NEO4J_USER`/`NEO4J_PASS` only, expecting zero Neo4j skips; (b) as `NEO4J_USERNAME`/`NEO4J_PASSWORD` only, same expectation; (c) nothing exported and the excuse unset, expecting the fixture's failure. Merged and pushed only if (a) and (b) are green with zero skips from the fixture and (c) fails as designed.
## 2. This repo: decision 3's sentence. Decision 5's diagnosis. Decision 6's table.
## 3. Gate
`make gate-fast` (no stored payload is touched), `seldon verify`, protected paths. Detached, logged, polled to `EXIT=0` inside this turn. Failure ships nothing: report and stop.
## 4. Report
RESULT `cc_tasks/2026-09-16_neo4j_fixture_fails_not_skips_RESULT.md`: §0 this session's own dispatch log and `dispatch_finished` event quoted verbatim, as the live observation for the predecessor's prompt clause (this is the only window that evidence exists in; capture it first); §1 both repos' commits; §2 the three suite runs with counts; §3 the `seldon go` Dispatcher block before and after, on the `c609b1e1` case; §4 the session_id diagnosis; §5 the re-read table; §6 every premise this task file got wrong; §7 the gate table with passed, skipped, xfailed, deselected, wall clock and log path per row. `seldon cc complete`, commit, push.

**SEQUENCING:** §0 of the RESULT is captured at the start of the session, before §1 → §1 (merged before §2) → §2 → glob addenda → §3 (detached, logged, polled inside the turn) → §4 → push both repos. Not launched before `2026-09-16_headless_session_polls_to_completion.md` is `completed` on the graph.
