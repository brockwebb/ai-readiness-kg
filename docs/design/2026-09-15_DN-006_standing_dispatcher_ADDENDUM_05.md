# ADDENDUM 05 — `docs/design/2026-09-15_DN-006_standing_dispatcher.md`

**Date:** 2026-09-18. **Status:** AMENDS decision 2's criterion c5. Does not supersede anything.
Written by the implementing task (`cc_tasks/2026-09-18_network_allowlist.md`), from the
operator's ruling of 2026-09-18: acquisition is an agentic step, and a human enters only when a
credential or a block makes it impossible.

Decisions 1 and 3 to 10 stand as ADDENDUM_01 to ADDENDUM_04 left them.

---

## 1. Network is a declared budget, like Spend, and not a binary

**c5 as amended.** The task file's `**Network:**` header parses under this grammar
(`seldon/core/dispatch.py::NETWORK_GRAMMAR`), and passes if it does:

| form | kind | what the child gets |
|---|---|---|
| `**Network:** none` — `none` first, prose after it allowed (`none beyond git push`) | `none` | `SELDON_NETWORK_ALLOWLIST` removed from its environment |
| `**Network:** allowlist: host1, host2, ...` — exact hostnames, comma-separated; no wildcards, schemes, paths or ports | `allowlist` | `SELDON_NETWORK_ALLOWLIST=host1,host2,...` |
| `**Network:** <hosts>, under cadence <name>` — decision 8's provenance, unchanged | `cadence` | variable removed |

`git push` to the project's own remote is implied by all three. Anything else fails c5 as
`network_undeclared`, and the criteria vector carries a `message` naming the offending entries
and quoting the grammar. `dispatch_launched` records the parsed list as `network_allowlist`
(empty for `none`).

**One tightening, stated.** `none` used to match anywhere in the header, so a value naming hosts
and then saying "none else" read as a task that contacts nothing. It must now lead the value.
Every `none` spelling in the 2026-09-18 survey of `cc_tasks/` leads (`none.`, `none beyond git
push`, `NONE — ...`, `` `none` ``), so no dispatchable task changes verdict.

**Prior art.** An egress allowlist is how CI runners and build sandboxes declare network: Nix and
Bazel sandboxes deny by default and allow named fetches, and GitHub Actions hardening practice
declares allowed egress endpoints per job. A per-task host list plus a per-request fetch log is
the same contract at task grain. Hostnames are RFC 1123 names compared case-insensitively
(RFC 4343).

## 2. Enforcement is declarative plus audit, not a sandbox

The dispatcher enforces nothing at the socket. macOS offers no cheap per-process egress filter,
and the dispatcher does not claim one. The allowlist therefore has the **same standing as the
Spend header**: a declared budget, whose use is audited afterwards.

The audit is `scripts/fetch_allowlisted.py`. It refuses to run when `SELDON_NETWORK_ALLOWLIST`
is unset. It refuses any off-list URL before a socket opens, and runs the same check on every
redirect hop and on the `robots.txt` read. It fetches robots-first under the identified UA
through `scan.manners.Fetcher`. It writes one JSONL line per request: URL, status, bytes and
sha256. The RESULT of an allowlist task quotes that log whole. A fetch made any other way is a
departure the RESULT must name. The dispatcher cannot detect one.
