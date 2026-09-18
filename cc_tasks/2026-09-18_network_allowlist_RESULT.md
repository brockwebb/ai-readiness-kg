# RESULT — a task declares its network as an allowlist, and the dispatcher launches it

**Task:** `cc_tasks/2026-09-18_network_allowlist.md`. No addenda: `2026-09-18_network_allowlist_ADDENDUM*.md` was globbed before §1 and again before §3, and matched nothing both times.
**Executed:** 2026-09-18, a dispatched session (claim `55c37ad8`).
**Spend:** zero model calls. **Network:** `git push` to both repos' own remotes only. No fetch was made. The helper was exercised only against `httpx.MockTransport` and a socket layer that refuses every call.
**Gate:** green. Every command below reached its `EXIT=` line before this file was written. Seldon suite: 1986 passed, 0 skipped, `EXIT=0`. Here, `make gate-fast`: 2433 passed, 3 skipped, 25 deselected, 12 xfailed, `EXIT=0`. The full tier ran too, because a push follows: 2458 passed, 3 skipped, 12 xfailed, 0 deselected, `EXIT=0`. `seldon verify` and the protected-paths check both reached `EXIT=0`. Table in §4.

---

## 0. The grammar, and c5's new refusal messages

`seldon/core/dispatch.py::NETWORK_GRAMMAR`, verbatim:

> `**Network:** none` (optionally followed by prose, e.g. `none beyond git push`), or `**Network:** allowlist: host1, host2, ...` with exact hostnames (no wildcards, no schemes, no paths, no ports), or `**Network:** <hosts>, under cadence <name>`

`parse_network(value)` returns `{kind, hosts, error}`:

| value | kind | c5 | recorded |
|---|---|---|---|
| `none` leading the value (`none.`, `none beyond git push`, `NONE — …`, `` `none` ``) | `none` | ok | `network_allowlist: []`; the child's `SELDON_NETWORK_ALLOWLIST` is **removed** |
| `allowlist: a.org, B.org` | `allowlist` | ok | `network_allowlist: ["a.org", "b.org"]` (lower-cased, de-duplicated in order); child gets `SELDON_NETWORK_ALLOWLIST=a.org,b.org` |
| `…, under cadence <name>` (decision 8, unchanged) | `cadence` | ok | `[]`; variable removed |
| anything else | `None` | **fails**, reason `network_undeclared` | `message` on the c5 vector |

Hostnames must match RFC 1123 labels and are compared case-insensitively (RFC 4343). A sentence-ending period after the last host is dropped. Backticks around a host are tolerated because they are only formatting. A scheme, a path, a port, a `*`, an empty entry or prose is refused. The c5 vector now carries `network_kind` and `network_allowlist` next to `network_header`. `dispatch_launched` carries `network_allowlist` at top level. `seldon dispatch once`, when nothing is eligible, prints the c5 message under a `network_undeclared` row.

The refusal messages, captured from the merged code:

```
'allowlist: https://github.com' -> allowlist entries are not exact hostnames: 'https://github.com'; expected <GRAMMAR>
'allowlist:'                    -> allowlist names no host; expected <GRAMMAR>
'the sixteen FSS hosts.'        -> Network header 'the sixteen FSS hosts.' does not parse; expected <GRAMMAR>
```

`<GRAMMAR>` in these messages is the literal text quoted above; it is abbreviated here only to save width. It is not a placeholder: `tests/test_dispatch.py::test_c5_refuses_an_allowlist_that_is_not_exact_hostnames` asserts `D.NETWORK_GRAMMAR in message` for each of seven bad values. Those values are a scheme, a path, a wildcard, a port, prose, an empty list and an empty entry.

**One tightening, decided here.** `none` used to match *anywhere* in the header (`\bnone\b`). A value that named hosts and then said "none else" therefore read as a task that contacts nothing. It now has to lead the value. I surveyed every `**Network:**` header in `cc_tasks/`, and each one that means none puts it first, so no task's verdict changes. The live queue was checked with `seldon dispatch status`: `2026-09-18_dcat_field_rules.md` and `2026-09-18_schema_field_rules.md` read `none`, and `2026-09-18_tool_docs_ingest.md` reads `allowlist` with `["raw.githubusercontent.com", "github.com", "archive.org"]`. That last task was blocked by the old c5 and now passes it. It still waits on c2, which is this task.

## 1. Commits

**Seldon** (`/Users/brock/GitHub/seldon`, pushed to `origin/main`, branch deleted after merge):

* `ac7d005` feat: a task declares its network as an allowlist, and the dispatcher launches it. It touches `seldon/core/dispatch.py` (`NETWORK_GRAMMAR`, `NETWORK_ALLOWLIST_ENV`, `parse_network`, c5) and `seldon/commands/dispatch.py` (`network_allowlist` on `dispatch_launched`, the child env in `_run`, the c5 message in the no-eligible listing). It adds 15 tests to `tests/test_dispatch.py` and 2 to `tests/test_dispatch_launch.py`.
* `0812340` Merge feat/network-allowlist.

Tests came first. With the new tests in place and `seldon/` stashed back to `42dbd47`, the tests selected by `-k "c5 or allowlist"` gave **17 failed, 2 passed**; the 2 that passed were the old c5 tests. With the change, all pass. `network_declared_none` is kept as a wrapper over `parse_network`, because `tests/test_cadence_pass.py` calls it.

**This repo:** the commit that carries this RESULT. It holds `scripts/fetch_allowlisted.py`, `tests/test_fetch_allowlisted.py`, the two `CLAUDE.md` sentences, `docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_05.md`, `scripts/check_protected_network_allowlist.sh`, `seldon_events.jsonl` and this file.

* **Decision 3:** `scripts/fetch_allowlisted.py`. It refuses to run (exit 2) when `SELDON_NETWORK_ALLOWLIST` is unset or empty. Every URL is checked against the list before a `Fetcher` is even built, and a refused URL gets a log line and no request. The same check also runs as an httpx `request` event hook, so every redirect hop and the `robots.txt` read are checked before their connection. The hook logs its own refusals, because `Fetcher._robots_for` swallows exceptions. Fetches go robots-first under the identified UA through `scan.manners.Fetcher`, the pattern of `fetch_noaa_esip_sources.py`. A `response` hook writes one JSONL line per request actually sent, with URL, status, bytes and sha256. A file already on disk is never overwritten. Stored rows carry `acquisition_method: scripted_fetch` and `acquired_by: scripts/fetch_allowlisted.py`, ready for a ledger entry.
* **Decision 4:** ADDENDUM_05 records that the allowlist is a declared budget audited by the fetch log, with the same standing as `Spend`, and not a network sandbox. It also records the `none`-must-lead tightening.
* **Decision 5:** a sentence at the end of the corpus paragraph (Architecture invariant 2): corpus acquisition goes through the helper, from the Desktop as much as from a dispatched session. The grammar sentence is a new paragraph directly after the three-header rule (`**Spend:**`, `**Network:**`, `**Framework layer served`).

**Enforcement is declarative plus audit.** The dispatcher enforces nothing at the socket. A session can still fetch some other way, and only its RESULT would show it. That is the limit of this design, and it is stated in ADDENDUM_05 §2.

## 2. The helper's refusal tests

From `logs/2026-09-18_network_allowlist_helper_tests.log` (`pytest -v`):

```
tests/test_fetch_allowlisted.py::test_the_env_name_is_the_one_seldon_sets PASSED [  7%]
tests/test_fetch_allowlisted.py::test_refuses_to_run_when_the_allowlist_is_unset[env0] PASSED [ 14%]
tests/test_fetch_allowlisted.py::test_refuses_to_run_when_the_allowlist_is_unset[env1] PASSED [ 21%]
tests/test_fetch_allowlisted.py::test_refuses_to_run_when_the_allowlist_is_unset[env2] PASSED [ 28%]
tests/test_fetch_allowlisted.py::test_main_refuses_to_run_without_the_variable PASSED [ 35%]
tests/test_fetch_allowlisted.py::test_an_off_list_host_is_refused_before_any_socket_opens PASSED [ 42%]
tests/test_fetch_allowlisted.py::test_check_url_is_exact_host_and_http_only[https://api.github.com/repos] PASSED [ 50%]
tests/test_fetch_allowlisted.py::test_check_url_is_exact_host_and_http_only[https://github.com.evil.example/] PASSED [ 57%]
tests/test_fetch_allowlisted.py::test_check_url_is_exact_host_and_http_only[ftp://github.com/file] PASSED [ 64%]
tests/test_fetch_allowlisted.py::test_check_url_is_exact_host_and_http_only[file:///etc/passwd] PASSED [ 71%]
tests/test_fetch_allowlisted.py::test_check_url_is_case_insensitive_on_the_host PASSED [ 78%]
tests/test_fetch_allowlisted.py::test_an_on_list_fetch_is_robots_first_and_logs_every_request PASSED [ 85%]
tests/test_fetch_allowlisted.py::test_a_redirect_off_the_list_is_refused_at_that_hop PASSED [ 92%]
tests/test_fetch_allowlisted.py::test_an_existing_file_is_never_overwritten PASSED [100%]
============================== 14 passed in 0.16s ==============================
```

The test the task names is `test_an_off_list_host_is_refused_before_any_socket_opens`. It runs `main()` with `SELDON_NETWORK_ALLOWLIST=github.com,archive.org` against a `www.noaa.gov` URL. `socket.socket.connect`, `socket.create_connection` and `socket.getaddrinfo` are replaced by recorders that raise. The test asserts exit 1 and an empty recorder, which means no resolve and no connect. It also asserts exactly one log line: `event: refused`, `status: null`, reason naming `'www.noaa.gov'`. No output directory is created. The redirect test sends `github.com` to `codeload.github.com` and asserts that the second host is never requested and that its refusal is the last line of the log.

## 3. Premises this task file got wrong

1. **"c5 passes a task only when the header matches `none`."** It also passed decision 8's cadence form (`under cadence <name>`), and `none` matched anywhere in the value, not only as the value. The cadence form is kept unchanged. The anywhere-match is tightened (§0).
2. **"GitHub Actions `permissions`" as prior art for an egress allowlist.** A workflow's `permissions` key scopes the `GITHUB_TOKEN`'s API access; it declares nothing about network egress. The egress analogue in Actions practice is a per-job allowed-endpoints list (for example StepSecurity's harden-runner). ADDENDUM_05 cites Nix/Bazel sandboxing and that practice, not `permissions`. I did not locate or verify the "OpenSSF egress policy" the task names, so ADDENDUM_05 does not cite it.
3. **"One sentence in `CLAUDE.md`'s corpus section."** `CLAUDE.md` has no section by that name. The sentence went at the end of Architecture invariant 2, "Manifest is the only gate into the corpus", which is the corpus paragraph. "Beside the Spend line" was read as the three-header rule paragraph in the dispatch protocol.
4. **The write set omits the protected-paths check that §3 runs.** Following the precedent of every dispatcher task before this one, `scripts/check_protected_network_allowlist.sh` was added. It is the one path outside the listed write set, and it is named here for that reason.
5. **Not a premise error, but the next OODA should check it:** the queued `tool_docs_ingest` declares `github.com`. GitHub archive and release downloads redirect to `codeload.github.com` or `objects.githubusercontent.com`, and the helper refuses those hops by design. If that task needs archives, its header has to name those hosts. The task file is immutable, so that means an addendum.

## 4. Gate

Tier named by the task: `make gate-fast` (`-rs`). The full tier was also run because a push follows. No rule module, registry or stored payload was touched, so `gate-task`'s re-derivation adds nothing here beyond what the full tier ran.

| gate | result | wall-clock | log |
|---|---|---|---|
| Seldon suite (`pytest tests/ -q -rs`) at the pre-merge tree | 1986 passed, 0 skipped, 0 xfailed, 0 deselected, `EXIT=0` | 194.6 s | `logs/2026-09-18_network_allowlist_seldon_suite.log` |
| `make gate-fast` | 2433 passed, 3 skipped, 25 deselected, 12 xfailed, `EXIT=0` | 475.5 s | `logs/2026-09-18_network_allowlist_gate_fast.log` |
| full tier (`pytest tests/ assessment/ -q -rs`) | 2458 passed, 3 skipped, 0 deselected, 12 xfailed, `EXIT=0` | 1384.2 s | `logs/2026-09-18_network_allowlist_gate_full.log` |
| `seldon verify` | "All checks passed.", `EXIT=0` | — | `logs/2026-09-18_network_allowlist_verify.log` |
| protected paths (`scripts/check_protected_network_allowlist.sh`) | PASS, `EXIT=0`: 6 modified paths all in the write set; `docs/` moved only by ADDENDUM_05; CLAUDE.md lost no text; 7/7 point-of-the-task checks ok | — | `logs/2026-09-18_network_allowlist_protected.log` |

The 3 skips, from `-rs`:

* `tests/test_dispatch_config.py:333` is `interactive_only`, because `SELDON_SESSION_ID` is set in a dispatched session.
* `tests/test_scan_harness.py:281` skips because E5 judges the cycle's controls, not a surface.
* `assessment/tests/test_g1_preservation.py:337` skips because no dev proposition publishes SE and CI together.

The last two are standing. The first is a property of running inside a dispatched session.
