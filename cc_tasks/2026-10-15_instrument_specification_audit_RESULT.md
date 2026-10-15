# RESULT: the instrument specification (task db464d5f)

**Step 0.** One `dispatch_launched` (2026-10-15T12:39:29Z, this session); served model `claude-opus-5-5` == `seldon models resolve primary`. Reader `claude-fable-5-1` (role `judge`), 29 calls, 1,276,446 tokens (ceiling 3,000,000; pilot measured 43.8k/entry), 0 failures, no substitution. Network: 6 fetches via `scripts/fetch_allowlisted.py`, all 200 (one 301 to Google's moved status-code page), log `logs/2026-10-15_instrument_fetch.jsonl`, receipts `assessment/instrument/standards_receipts.yaml`.

**Part A: DN-015.** `docs/design/2026-10-15_DN-015_instrument_specification.md`: the standard, the entry schema, four states, page two shows only `specified`, the four-state cell. `seldon prior-art verify` **PASS** (verdict event `8a9d8db1…`), committed `166e9c99`. Messick and Cronbach–Meehl are held only through works that cite them (HELM; arXiv 2506.16697, 2505.08245); IEEE 829, pre-registration, codebooks and the VPAT/WCAG-EM searches returned off-topic rows and are recorded as failed searches.

**Part B: 16 entries** (`assessment/instrument/RULE-*.yaml`; table `reports/instrument/INSTRUMENT.{md,pdf}`). `scripts/instrument.py check`: 16 entries, **0 problems**; every source a corpus id or receipted URL; every attributed requirement backed by a verbatim quote verified against the source text (a planted false quote is caught); every pass/fail Finding on the cycle of record attributed to exactly one branch.

| Check | State | Why, in one phrase |
|---|---|---|
| A13 discoverability | project_defined | only the api-catalog and data.json branches are published; link reachability, terms, changelog and the composite are the project's |
| A2 API description | **invalid** | reader's 2nd no; before it project_defined: fails penalize "no OpenAPI at the recorded base", which no source requires |
| A1 machine format | specified | DWBP BP12, M-25-05 §5(a)(i), USAFacts §1 |
| A3 bulk download | specified | DWBP BP17; size floor and query-string rule stated as proxies |
| A4 crawler access (a declaration) | **invalid** | an absent robots.txt permits all (RFC 9309 §2.3.1.3); 5 of 8 listed tokens are training opt-outs; Googlebot and OAI-SearchBot not listed |
| A5 sitemap | specified | M-23-22 §III.4; sitemaps protocol; Google's sitemap purpose |
| A6 dataset markup | **invalid** | reader's 2nd no (quoting: "JSON-LD preferred", `name` as required not in a quoted passage); before it specified |
| A8 release date | project_defined | a pass can rest on temporalCoverage, which is not a release date |
| A9 machine entry point | project_defined | no published construct (frontier) |
| A10 data tool | project_defined | soft-404 branch published; the pre-JS 2000-character floor is not |
| B3 methodology | project_defined | "readable before scripts run" is the project's reading |
| D1 licence | project_defined | fails a detected licence for being worded, not an identifier |
| D4 inventory | specified | M-25-05 §4(a), §5(b)(ii); DCAT-US 1.1 |
| F4 change history | project_defined | fails an HTML changelog and unclassified entries (9 grid pages) |
| A11-declared (a declaration) | **invalid** | A4's two defects; reader's 2nd no on quoting |
| A12 coherence | invalid | coherence construct unpublished; reads a missing robots.txt as "nothing declared" |

**Fable (DN-015 §7)**, q1 source / q2 misreading / q3 undefined terms; round 2 only after a q1 no:
A13 r1 no/yes/yes, r2 yes/yes/no · A2 r1 no/yes/yes, r2 **no**/yes/yes · A1 r1 no/yes/yes, r2 yes/yes/yes · A3 r1 no/yes/yes, r2 yes/yes/yes · A4 r1 no/no/yes, r2 yes/no/yes · A5 r1 no/yes/yes, r2 yes/no/yes · A6 r1 no/yes/yes, r2 **no**/yes/yes · A8 r1 no/yes/yes, r2 yes/no/yes · A9 r1 yes/yes/yes · A10 r1 yes/yes/yes · B3 r1 no/yes/yes, r2 yes/no/yes · D1 r1 no/yes/yes, r2 yes/no/yes · D4 r1 no/yes/yes, r2 yes/no/yes · F4 r1 yes/yes/yes · A11-declared r1 no/yes/yes, r2 **no**/yes/yes · A12 r1 no/yes/yes, r2 yes/yes/no. Round-1 q1 nos were one defect class: a requirement attributed to a source with no passage behind it. Reasons verbatim in `reports/instrument/run/verify.json` and in INSTRUMENT.md. Claims on A1, A3, A9, A10, A12, A13, F4 were tightened after their last read from its q2 answer; INSTRUMENT.md marks each such entry "revised after its last reading".

**Part C: the record.** `scripts/apply_instrument_state.py` through `framework_writeback.save` (34 nodes changed, nothing dropped; event on `batch-033_framework`): `instrument_state` on 16 MeasurementSpecs, `plain_name` on 15 indicators (A11 kept, its other layers are agency-enabled), 3 fix lines rewritten (A2, A8, D1); `summary_grid_vocab.yaml` synced so the older script cannot revert it. `get_overview`: **`projection_gate.status: green`**, 232 nodes compared, 0 mismatches; DD-057 roundtrip 9 passed.

**Part D: page two** (`reports/instrument/PAGE_TWO_VERDICT.{md,pdf}`; `SUMMARY.pdf` not rebuilt). `specified` and not a declaration: **A1, A3, A5, D4** (4 of 13). Under the four-state rule **86 of 208 cells change state, all to "could not measure"** (81 fail, 5 partial; the 5 partials were pass + unmeasured). Not-measured pages: access denial 48, unconfirmed absence 40, the scanner's own robots compliance 22. Concentration: BLS 13 of 13, ORES 13, BTS 12, EIA 7, NASS 7. With only the 4 columns, page two holds 64 cells: could not measure 41, fail 15, pass 8.

**Gates.** `make gate-task` **EXIT=0**: gate-fast 3399 passed, 5 skipped, 41 xfailed, 0 deselected, 211.14 s; re-derivation 25 passed, 8.32 s (`logs/2026-10-15_instrument_gate_task2.log`; first run `…_gate_task.log` failed 4, below). `seldon verify` **All checks passed, EXIT=0** (`logs/2026-10-15_instrument_seldon_verify.log`). Protected paths: working-tree diff empty; committed since 75d9aa4e only the authorized write-back (record, its event, the vocab) (`logs/2026-10-15_instrument_protected.log`). `tests/test_instrument.py` 28 passed, including the SIGKILL resume test.

**Premises found wrong.**
1. "13 product-level checks and 5 site-level checks, 18": the grid's 13 include the site-level A4, A5, A10, so the union is 15; with A13, which the task names, the audit is **16** entries.
2. "The API discoverability rule (two branches project-invented)": the v2 RESULT said none; at branch level three are (link reachability under all four objects, plus terms and changelog having no convention at all).
3. The "API advertisement check" is A2 ("A documented machine interface"); A13 is discoverability. The four points are settled in A2's `settles`.
4. The two declarations among the site checks are A4 and A11-declared: A4 reads robots.txt only, and the v3 grid showed it as what a machine met.
5. The v3 grid counted `error` as fail, against DD-052 §6; 81 of its 164 fails were unmeasured pages.
6. `main` was red before this task: the brief pack and claims file still named record commit 380d8526 after the v3 write-back (14cbe706); regenerated (`9ce5db64`).
7. "a second no sets invalid": the three entries so set (A2, A6, A11) were failed on quotation coverage; A6's rule may be sound. A re-specification with the passages quoted is the route back for it; that is the operator's call with the page-two rebuild.
