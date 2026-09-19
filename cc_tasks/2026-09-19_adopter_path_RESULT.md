# RESULT: an adopter can scan their own site with `make scan-now FRAME=<file>`, on demand or on a schedule of their own, and read the result as files, with or without Neo4j

**Task:** `cc_tasks/2026-09-19_adopter_path.md`. At session start the glob `cc_tasks/2026-09-19_adopter_path_ADDENDUM*.md` matched 0 files. Before §3, at 2026-09-19T15:21:24Z, it matched 0 again (`logs/adopt_addendum_glob_pre_s3.log`).
**Session:** launched headless by the standing dispatcher from HEAD `129d767`.
**Framework layer served:** DN-005 §2.4, exposure. Anyone holding the repository can now run the framework's measured levels on their own site and get the verdicts, the ranked prescriptions and the requirements without this project in the loop.
**Spend:** zero model calls. **Network:** loopback only (127.0.0.1: the control fixtures and the `body_two_products` fixture standing in for "your site"), plus `git push`. No other host was contacted. The runbook's `www.example.org` frame is refused before any fetch, and that refusal is what it demonstrates. `scripts/fetch_allowlisted.py` was not used.

**Gate: green.** Tier `gate-task`, then the whole suite. `seldon verify` shows only the warning that was already there.
- **`make gate-task`:** `EXIT=0`, wall 659 s (`logs/adopt_gate_task.log`).
  - fast tier: 2707 passed, 3 skipped, 27 deselected, 12 xfailed, 0 failed, 643.34 s;
  - re-derivation tier (`-k re_derives`, every stored payload): 23 passed, 0 skipped, 25 deselected, 11.35 s.
- **Full suite (`pytest tests/ assessment/ -q -rs`, what `make gate-full` runs, plus `-p no:warnings`):** 2734 passed, 3 skipped, 12 xfailed, 0 deselected, 0 failed, 2298.25 s. `EXIT=0` (`logs/adopt_gate_full.log`). The three skips are the expected three: `tests/test_dispatch_config.py:333` (dispatched session), `tests/test_scan_harness.py:283` (E5), `assessment/tests/test_g1_preservation.py:337`. The full suite ran at the same time as `gate-task`, not after it, and contains every test `gate-task` runs.
- **`seldon verify`:** `EXIT=1`, which it defines as warnings only: 0 issues and 1 warning, `Stale artifacts — 36 stale`, all `…_2026-09-10_rj2` (`logs/adopt_seldon_verify.log`). The spot-scan RESULT reports the same warning, and this task did not cause it. `seldon verify --strict`: `EXIT=0`, "1 advisory finding reported but not blocking" (`logs/adopt_seldon_verify_strict.log`).
- **Protected paths:** `scripts/check_protected_adopt.sh` gives `PROTECTED PATHS OK`, `EXIT=0` (`logs/adopt_protected.log`). It checks that `state/`, `corpus/`, `events/`, `docs/reports/` and `framework/` are byte-identical. It also checks that `params.yaml` only gained lines, that its `params_hash` equals HEAD's, and that its identity is unchanged.
- **The runbook, run as written (decision 5):** `tests/test_adopter_path.py::test_the_runbook_runs_as_written` passed twice: alone (771.41 s, `logs/adopt_runbook_pytest.log`) and inside the full suite. Both runs wrote `logs/adopt_runbook.log`; the full-suite run wrote it last, and §0 quotes that run.

---

## 0. The runbook's commands and their logged output

The gate does not have a copy of the commands. It parses `docs/adopt/run_on_your_site.md` and runs every block fenced `bash`, verbatim and in order, in one `bash -euo pipefail`. It runs them in a copy of the working tree (every tracked file plus the untracked files that are not ignored, which is what a clone of the pushed commit holds). Everything below is copied from `logs/adopt_runbook.log`. Lines beginning `$ ` are the block as the page states it; the lines after them are what it printed.

**Not run by the gate.** Two blocks are fenced `bash not-run-by-gate`, and a test asserts that exactly these two are:
- `git clone … && pip install …` needs the network. The copy stands in for the clone.
- `make project RUN=out/my-site` plus the stdio server needs Neo4j. §2 gives the reason.

```
# docs/adopt/run_on_your_site.md run as written by tests/test_adopter_path.py::test_the_runbook_runs_as_written
# started 2026-09-19T15:22:11.526998+00:00 finished 2026-09-19T15:34:31.117372+00:00 (739.6 s); copy of the tree at /private/var/folders/s1/yqb3d76d7053f7dyy9fwtkzw0000gp/T/pytest-of-brock/pytest-4346/test_the_runbook_runs_as_writt0/ai-readiness-kg; SITE_PORT=49834
# exit 0
```

```
=== runbook block 1 ===
$ export PY="$(command -v python3)"
$ "$PY" -c 'import bs4, extruct, httpx, jsonschema, protego, pyshacl, rdflib, usp, yaml; print("requirements OK")'
requirements OK
=== runbook block 2 ===
$ mkdir -p frames
$ cat > frames/example.yaml <<'EOF'
$ frame: example
$ bodies:
$   - name: EXAMPLE
$     home: https://www.example.org/
$ EOF
$ "$PY" assessment/harness/scan/run.py --frame frames/example.yaml || echo "refused, as it should be"
refused, as it should be
=== runbook block 3 ===
$ sed -i.orig 's|^  user_agent: .*|  user_agent: "example-readiness-scan/1.0 (+mailto:webmaster@example.org)"|' assessment/harness/scan/params.yaml
$ grep -n '^  user_agent:' assessment/harness/scan/params.yaml
134:  user_agent: "example-readiness-scan/1.0 (+mailto:webmaster@example.org)"
=== runbook block 4 ===
$ cat > frames/my_site.yaml <<EOF
$ frame: my-site
$ bodies:
$   - name: MYSITE
$     home: http://127.0.0.1:${SITE_PORT}/index.html
$     flagships:
$       - http://127.0.0.1:${SITE_PORT}/index.html
$       - http://127.0.0.1:${SITE_PORT}/second.html
$ EOF
```

`make scan-now` (block 5). The control gate first, then the four surfaces of the frame at 1 request/s, then the render. The run's summary JSON (`logs/adopt_runbook.log` lines 38–187) is elided here except for the fields that carry the claims: `requests_per_host` `{"127.0.0.1:49834": 134}`, `control_verdict` `pass`, `verdict_counts` 64 pass / 0 fail / 0 error, `error_class_unknown` 0, `params_hash` `c6b4861c3e33…`, `base_params_hash` `073ec4c8729c…` (the copy's `params.yaml` with the adopter's identity; this repository's is `0ef2e016fea2…`), `params_overlay.cycle` `{name: scan_my-site_2026-09-19, targets: frame_my-site_52152cff577c}`.

```
=== runbook block 5 ===
$ make scan-now FRAME=frames/my_site.yaml
/opt/anaconda3/bin/python3 assessment/harness/scan/run.py --frame "frames/my_site.yaml" --out "out"
CONTROL GATE: PASS — both control fixtures fired and every rule returned its expected verdict; ordering not asserted (no surface was scanned in this cycle)
  MYSITE   well_known host:127.0.0.1:49834                       A12=P
  MYSITE   home       home:127.0.0.1:49834                       P P P P P P P P P P P P P P P P P P P P
  MYSITE   flagship   flagship:127.0.0.1:49834/index.html        P P P P P P P P P P P P P P P P P P P P P
  MYSITE   flagship   flagship:127.0.0.1:49834/second.html       P P P P P P P P P P P P P P P P P P P P P
…
/opt/anaconda3/bin/python3 scripts/render_run_report.py --frame "frames/my_site.yaml" --out "out"
{
 "cycle": "scan_my-site_2026-09-19",
 "cycle_of_record": "scan_my-site_2026-09-19",
 "matrices": [
  "out/my-site/reports/scan_matrix_tierA_my-site_2026-09-19.json",
  "out/my-site/reports/scan_matrix_tierA_my-site_2026-09-19.csv",
  "out/my-site/reports/scan_matrix_tierC_my-site_2026-09-19.json",
  "out/my-site/reports/scan_matrix_tierC_my-site_2026-09-19.csv",
  "out/my-site/reports/scan_matrix_product_my-site_2026-09-19.json",
  "out/my-site/reports/scan_matrix_product_my-site_2026-09-19.csv"
 ],
 "report": "out/my-site/report/scan_my-site_2026-09-19.md"
}
```

Block 6 `cat`s the report. The report is §1, so the log's copy of it (lines 209–322) is not repeated here. The directory listing that follows it is:

```
=== runbook block 6 ===
$ cat out/my-site/LATEST
$ cat "out/my-site/report/$(cat out/my-site/LATEST).md"
$ ls out/my-site/reports
scan_my-site_2026-09-19
…
publication.yaml
scan_matrix_product_my-site_2026-09-19.csv
scan_matrix_product_my-site_2026-09-19.json
scan_matrix_tierA_my-site_2026-09-19.csv
scan_matrix_tierA_my-site_2026-09-19.json
scan_matrix_tierC_my-site_2026-09-19.csv
scan_matrix_tierC_my-site_2026-09-19.json
```

```
=== runbook block 7 ===
$ "$PY" scripts/score.py --run out/my-site --body MYSITE
# scoring model — cycle scan_my-site_2026-09-19, 1 bodies
# Scores cover only what the harness measures; Tier O and D indicators are not scored.
# coverage: bodies scored 1/1; legs scored 21/23 adopted harness legs; indicators measured 21/48 in the framework (21/23 harness_leg); criteria measured 5/7
# two equal-weight schemes, no basis to prefer either: hierarchical (leg to criterion, OECD/JRC 2008 default) and flat (1/n per judged leg); readiness level is a cumulative ladder, never an average; `scripts/score.py --explain` for every step

MYSITE: score 1.000 hierarchical, rank 1; 1.000 flat, rank 1; of 1; legs 21/21, indicators 21/48, constructs 21/47, criteria 5/7; excluded rows none
MYSITE ranks 1 of 1 (hierarchical); no single leg's verdicts, reversed, would change it (the nearest is A1).

crit  construct                                                  leg           pass/judged  score
A     Machine-readable formats                                   A1                2/2      1.000
A     Application/data-tool machine surface                      A10               1/1      1.000
A     Effective crawler access (declared / enforced / observed)  A11-declared      1/1      1.000
A     Programmatic access                                        A2                2/2      1.000
A     Bulk access                                                A3                2/2      1.000
A     Crawler/agent access                                       A4                1/1      1.000
A     Discoverability surface                                    A5                1/1      1.000
A     Structured markup                                          A6                2/2      1.000
A     Timeliness of surface                                      A8                2/2      1.000
A     M2M agent surface                                          A9                2/2      1.000
B     Variable-level semantics                                   B1                2/2      1.000
B     Definitions surface                                        B2                2/2      1.000
B     Methodology legibility                                     B3                2/2      1.000
B     Quality metadata                                           B4                2/2      1.000
B     Semantic consistency                                       B5                2/2      1.000
D     License clarity                                            D1                2/2      1.000
D     Reuse permissions for AI                                   D2                2/2      1.000
D     Provenance completeness                                    D3                2/2      1.000
D     No dark data                                               D4                2/2      1.000
F     Change legibility                                          F4                2/2      1.000
G     Authority metadata                                         G4                2/2      1.000

criteria: A 1.000, B 1.000, C   —  , D 1.000, E   —  , F 1.000, G 1.000
gating: 21 of 21 judged legs passed outright; constructs with zero passes: none

readiness level: 5 — A: 10 clear, 0 fail, 0 unobservable of 10; B: 5 clear, 0 fail, 0 unobservable of 5; D: 4 clear, 0 fail, 0 unobservable of 4; F: 1 clear, 0 fail, 0 unobservable of 1; G: 1 clear, 0 fail, 0 unobservable of 1

prescription join — actions on this body's failing legs, cheapest effort band first, then by the score each would add (bands notional):
effort   cost         delta  leg           action

delta: the body's score if every failing row on that leg passed. Actions on the same leg share it; the matrix carries verdicts, not outcomes, so it is an upper bound for any one action.

latest measurement: scan_my-site_2026-09-19 (2026-09-19)
MYSITE's latest measurement is the snapshot scan_my-site_2026-09-19; no spot cycle has measured it since.
=== runbook block 8 ===
$ "$PY" -c 'import sys; sys.path.insert(0, "mcp"); import airkg_tools as T; print(T.Tools(graph=None, run="out/my-site").get_body("MYSITE")["summary"])'
0 failing of 39 judged on scan_my-site_2026-09-19; 1 bodies are on this cycle. MYSITE ranks 1 of 1 (hierarchical); no single leg's verdicts, reversed, would change it (the nearest is A1).
=== runbook block 9 ===
$ "$PY" assessment/harness/scan/rederive.py --from "out/my-site/state/$(cat out/my-site/LATEST).json" | tail -1
RE-DERIVATION GATE: PASS
=== runbook block 10 ===
$ make install-schedule
/opt/anaconda3/bin/python3 scripts/install_schedule.py
schedule.when is on_demand: nothing installed. Scan when you choose with `make scan-now FRAME=<your frame>`.
```

On stderr, from block 2 (the refusal, before any fetch; the control gate never ran):

```
REFUSING: params.yaml manners.user_agent is this project's identity ('ai-readiness-kg-scanner/0.2 (+https://github.com/brockwebb/ai-readiness-kg)') and this frame reaches www.example.org. Set it to your own: a product name and a contact a host operator can reach, e.g. "my-org-readiness-scan/1.0 (+mailto:webmaster@example.org)" (DD-060; docs/adopt/run_on_your_site.md step 2).
```

The test then asserts that the copy's own `state/`, `corpus/`, `events/` and `docs/reports/` are unchanged, file for file and size for size.

## 1. The rendered report for the fixture body

`out/my-site/report/scan_my-site_2026-09-19.md`, as block 6 printed it:

````markdown
# my-site: scan_my-site_2026-09-19

Rendered by `scripts/render_run_report.py` from `out/my-site/state/scan_my-site_2026-09-19.json` (cc_tasks/2026-09-19_adopter_path.md). Every section below is an answer of the MCP server (`mcp/airkg_server.py --run out/my-site`), so the report and the server cannot disagree. Neo4j was not read.

## The run

| | |
|---|---|
| measured on | 2026-09-19 |
| scope | frame |
| frame file | `frames/my_site.yaml` (sha256 `52152cff577c…`) |
| control gate | pass: both control fixtures fired, every rule returned its expected verdict, and every control observation precedes the first real host (2026-09-19T15:31:59.735189+00:00) |
| surfaces / findings / observations | 4 / 64 / 130 |
| verdicts | {"pass": 64, "fail": 0, "not_applicable": 0, "error": 0} |
| requests per host | {"127.0.0.1:49834": 134} |
| params_hash | `c6b4861c3e33…` (base `073ec4c8729c…` plus the cycle overlay) |
| cycle of record of this frame | scan_my-site_2026-09-19 |

## MYSITE

0 failing of 39 judged on scan_my-site_2026-09-19; 1 bodies are on this cycle. MYSITE ranks 1 of 1 (hierarchical); no single leg's verdicts, reversed, would change it (the nearest is A1).

### Every judged leg

| leg | verdict | surface | why |
|---|---|---|---|
| A1 | pass | `flagship:127.0.0.1:49834/index.html` | structured data SERVED at http://127.0.0.1:49834/estimates.csv (text/csv); classified on the response, not on the href |
| A1 | pass | `flagship:127.0.0.1:49834/second.html` | structured data SERVED at http://127.0.0.1:49834/estimates.csv (text/csv); classified on the response, not on the href |
| A10 | pass | `home:127.0.0.1:49834` | deep link HTTP 200; invalid route correctly HTTP 404; 2556 visible characters present before JS. The pre/post-JS DOM diff the signal also names was NOT run (renderer: none) |
| A11-declared | pass | `home:127.0.0.1:49834` | both declared-layer sources permit: robots.txt allows all 8 AI-crawler user agents and the page declares no restricting meta-robots directive. Enforced and observed layers require edge logs (agency_instrumented) |
| A12 | pass | `home:127.0.0.1:49834` | robots.txt permits example-readiness-scan/1.0 (+mailto:webmaster@example.org) for http://127.0.0.1:49834/index.html and the host served it (HTTP 200): the declared and enforced layers agree |
| A2 | pass | `flagship:127.0.0.1:49834/index.html` | machine-readable API description at http://127.0.0.1:49834/openapi.json (OpenAPI 3.0.3); auth scheme ['ApiKeyAuth']; rate limits declared |
| A2 | pass | `flagship:127.0.0.1:49834/second.html` | machine-readable API description at http://127.0.0.1:49834/openapi.json (OpenAPI 3.0.3); auth scheme ['ApiKeyAuth']; rate limits declared |
| A3 | pass | `flagship:127.0.0.1:49834/index.html` | whole-product download linked from the product page: http://127.0.0.1:49834/bulk/estimates-2026.zip (archive) |
| A3 | pass | `flagship:127.0.0.1:49834/second.html` | whole-product download linked from the product page: http://127.0.0.1:49834/bulk/estimates-2026.zip (archive) |
| A4 | pass | `home:127.0.0.1:49834` | robots.txt allows the product path for all 8 AI-crawler user agents |
| A5 | pass | `home:127.0.0.1:49834` | sitemap at http://127.0.0.1:49834/sitemap.xml lists the product URL (3 URLs) |
| A6 | pass | `flagship:127.0.0.1:49834/index.html` | markup declares Dataset and the graph conforms to the dcat_ap_min shapes (20 triples) |
| A6 | pass | `flagship:127.0.0.1:49834/second.html` | markup declares Dataset and the graph conforms to the dcat_ap_min shapes (20 triples) |
| A8 | pass | `flagship:127.0.0.1:49834/index.html` | markup declares the vintage via dateModified and the latest-vintage pointer resolves (http://127.0.0.1:49834/estimates-latest.csv -> HTTP 200, found by href token) |
| A8 | pass | `flagship:127.0.0.1:49834/second.html` | markup declares the vintage via dateModified and the latest-vintage pointer resolves (http://127.0.0.1:49834/estimates-latest.csv -> HTTP 200, found by href token) |
| A9 | pass | `flagship:127.0.0.1:49834/index.html` | machine-first entry point served at http://127.0.0.1:49834/openapi.json (application/json, HTTP 200) |
| A9 | pass | `flagship:127.0.0.1:49834/second.html` | machine-first entry point served at http://127.0.0.1:49834/openapi.json (application/json, HTTP 200) |
| B1 | pass | `flagship:127.0.0.1:49834/index.html` | variable-level metadata is reachable: all 1 catalog record(s) for the product at http://127.0.0.1:49834/data.json link a data dictionary (`describedBy` or `distribution.describedBy`); 1 of 1 schema.org `Dataset`(s) in the markup at http://127.0.0.1:49834/index.html list `variableMeasured`; not measured: the contents of the dictionary or of the listed variables (labels, definitions, units, universes) and whether they are comprehensive, which would need them dereferenced and a coverage threshold pre-registered |
| B1 | pass | `flagship:127.0.0.1:49834/second.html` | variable-level metadata is reachable: all 1 catalog record(s) for the product at http://127.0.0.1:49834/data.json link a data dictionary (`describedBy` or `distribution.describedBy`); 1 of 1 schema.org `Dataset`(s) in the markup at http://127.0.0.1:49834/second.html list `variableMeasured`; not measured: the contents of the dictionary or of the listed variables (labels, definitions, units, universes) and whether they are comprehensive, which would need them dereferenced and a coverage threshold pre-registered |
| B2 | pass | `flagship:127.0.0.1:49834/index.html` | all 1 `DefinedTerm`(s) linked from a `Dataset` at http://127.0.0.1:49834/index.html carry `termCode`, `inDefinedTermSet` and `description`; not measured: whether the definitions are versioned, because no admitted document names a version property on `DefinedTerm` or `DefinedTermSet` |
| B2 | pass | `flagship:127.0.0.1:49834/second.html` | all 1 `DefinedTerm`(s) linked from a `Dataset` at http://127.0.0.1:49834/second.html carry `termCode`, `inDefinedTermSet` and `description`; not measured: whether the definitions are versioned, because no admitted document names a version property on `DefinedTerm` or `DefinedTermSet` |
| B3 | pass | `flagship:127.0.0.1:49834/index.html` | methodology served as text/html at http://127.0.0.1:49834/methodology.html and retrievable without JS: 2403 visible characters, link density 0.0 |
| B3 | pass | `flagship:127.0.0.1:49834/second.html` | methodology served as text/html at http://127.0.0.1:49834/methodology.html and retrievable without JS: 2403 visible characters, link density 0.0 |
| B4 | pass | `flagship:127.0.0.1:49834/index.html` | all 1 catalog record(s) for the product at http://127.0.0.1:49834/data.json carry a quality measurement (`hasQualityMeasurement`) and revision metadata (`versionNotes` or `previousVersion` or `hasCurrentVersion`); not measured: the suppression-rules clause, for which no admitted document names a machine-readable field |
| B4 | pass | `flagship:127.0.0.1:49834/second.html` | all 1 catalog record(s) for the product at http://127.0.0.1:49834/data.json carry a quality measurement (`hasQualityMeasurement`) and revision metadata (`versionNotes` or `previousVersion` or `hasCurrentVersion`); not measured: the suppression-rules clause, for which no admitted document names a machine-readable field |
| B5 | pass | `flagship:127.0.0.1:49834/index.html` | all 1 concept(s) coded on two or more of the body's products carry one identifier (`termCode` within `inDefinedTermSet`); not measured: the cross-vintage half (same concept, same identifier across vintages), unmeasured until a second cycle with term codes |
| B5 | pass | `flagship:127.0.0.1:49834/second.html` | all 1 concept(s) coded on two or more of the body's products carry one identifier (`termCode` within `inDefinedTermSet`); not measured: the cross-vintage half (same concept, same identifier across vintages), unmeasured until a second cycle with term codes |
| D1 | pass | `flagship:127.0.0.1:49834/index.html` | markup licence field carries a recognised identifier (https://creativecommons.org/…) |
| D1 | pass | `flagship:127.0.0.1:49834/second.html` | markup licence field carries a recognised identifier (https://creativecommons.org/…) |
| D2 | pass | `flagship:127.0.0.1:49834/index.html` | robots.txt at http://127.0.0.1:49834/robots.txt declares a Content-Signal for both uses on the product path (ai-train=yes, ai-input=yes); not measured: the prose terms of use, which stay a judged reading, and whether the declaration is enforced, which is A12's |
| D2 | pass | `flagship:127.0.0.1:49834/second.html` | robots.txt at http://127.0.0.1:49834/robots.txt declares a Content-Signal for both uses on the product path (ai-train=yes, ai-input=yes); not measured: the prose terms of use, which stay a judged reading, and whether the declaration is enforced, which is A12's |
| D3 | pass | `flagship:127.0.0.1:49834/index.html` | all 1 catalog record(s) for the product at http://127.0.0.1:49834/data.json name a lineage (`wasGeneratedBy` or `prov:wasGeneratedBy` or `wasDerivedFrom` or `prov:wasDerivedFrom`) (`qualifiedAttribution` on 0 of 1); not measured: whether the named lineage reaches from collection through processing to the product, which would mean dereferencing the activities |
| D3 | pass | `flagship:127.0.0.1:49834/second.html` | all 1 catalog record(s) for the product at http://127.0.0.1:49834/data.json name a lineage (`wasGeneratedBy` or `prov:wasGeneratedBy` or `wasDerivedFrom` or `prov:wasDerivedFrom`) (`qualifiedAttribution` on 0 of 1); not measured: whether the named lineage reaches from collection through processing to the product, which would mean dereferencing the activities |
| D4 | pass | `flagship:127.0.0.1:49834/index.html` | the product appears in http://127.0.0.1:49834/data.json in 1 record(s) naming it in a DCAT-US URL field, and the catalog conforms to the pod_v1_1_min schema (2 of 2 datasets validated) |
| D4 | pass | `flagship:127.0.0.1:49834/second.html` | the product appears in http://127.0.0.1:49834/data.json in 1 record(s) naming it in a DCAT-US URL field, and the catalog conforms to the pod_v1_1_min schema (2 of 2 datasets validated) |
| F4 | pass | `flagship:127.0.0.1:49834/index.html` | machine-readable changelog at http://127.0.0.1:49834/changelog.json (application/json); 1 of 1 entries carry a revision class |
| F4 | pass | `flagship:127.0.0.1:49834/second.html` | machine-readable changelog at http://127.0.0.1:49834/changelog.json (application/json); 1 of 1 entries carry a revision class |
| G4 | pass | `flagship:127.0.0.1:49834/index.html` | all 1 catalog record(s) for the product at http://127.0.0.1:49834/data.json carry `bureauCode` and `programCode`, well-formed (across the whole catalog, `bureauCode` is carried on 2 and `programCode` on 2 of 2 record(s)); not measured: the statutory mandate and the statistical-versus-administrative provenance, for which no admitted document names a field |
| G4 | pass | `flagship:127.0.0.1:49834/second.html` | all 1 catalog record(s) for the product at http://127.0.0.1:49834/data.json carry `bureauCode` and `programCode`, well-formed (across the whole catalog, `bureauCode` is carried on 2 and `programCode` on 2 of 2 record(s)); not measured: the statutory mandate and the statistical-versus-administrative provenance, for which no admitted document names a field |

### What to fix first

Ranked by `value.bodies_failing_now, then leg, then action id`, over the legs MYSITE fails (none). Notional relative estimate for a typical federal statistical publisher. Adjust for your platform, staffing, skills and procurement path; the band orders actions against each other, it does not predict your calendar or budget.

No action applies: MYSITE fails no leg an action remediates.

### What the harness could not see, and what would let it

0 error cell(s) for MYSITE on scan_my-site_2026-09-19; 4 unmeasured half/halves and 33 untested test(s) that no body is measured on.

- Per-product question benchmark (benchmark_set; provided by this_project) would unlock 3: C1 (indicator), E6 (indicator), E8 (indicator)
- Vintage disambiguation set (benchmark_set; provided by this_project) would unlock 3: C3 (indicator), E6 (indicator), G2 (indicator)
- A second scan cycle (second_cycle; provided by this_project) would unlock 2: B5 (unmeasured half), F2 (indicator)
- Wayback Machine CDX Server API (hosted_free; provided by this_project) would unlock 2: A7 (indicator), F3 (indicator)
- Standing adversarial bank (benchmark_set; provided by this_project) would unlock 1: E9 (indicator)
- A verified site in Bing Webmaster Tools (site_owner_account; provided by publisher) would unlock 1: C4 (indicator)
- The publisher's Cloudflare zone (site_owner_account; provided by publisher) would unlock 1: A11 (unmeasured half)
- Edge/WAF and crawler request logs (agency_records; provided by publisher) would unlock 1: A11 (unmeasured half)
- Entailment probe set, re-aimed at products (benchmark_set; provided by this_project) would unlock 1: C2 (indicator)
- Evaluation-failure closure records (agency_records; provided by publisher) would unlock 1: E7 (indicator)
- Evaluation-set version records (agency_records; provided by publisher) would unlock 1: E3 (indicator)
- Generative-engine query set (benchmark_set; provided by this_project) would unlock 1: C4 (indicator)
- Held-out evaluation-set rotation records (agency_records; provided by publisher) would unlock 1: E4 (indicator)
- The published conformance and evaluation report (agency_records; provided by publisher) would unlock 1: E1 (indicator)
- Pre-release validation records (agency_records; provided by publisher) would unlock 1: F1 (indicator)
- A second evaluation run (second_cycle; provided by this_project) would unlock 1: E8 (indicator)
- Series-break cases (benchmark_set; provided by this_project) would unlock 1: G6 (indicator)
- Staging regression records (agency_records; provided by publisher) would unlock 1: F5 (indicator)
- Threshold pre-registration records (agency_records; provided by publisher) would unlock 1: E2 (indicator)
- AIDRIN (AI Data Readiness Inspector) PyPI package (open_source; provided by this_project) would unlock 1: C5 (indicator)
- Bing Webmaster Tools, AI Performance report (platform_account; provided by publisher) would unlock 1: C4 (indicator)
- catalog.data.gov CKAN action API (hosted_free; provided by this_project) would unlock 1: D4 (coverage)
- Cloudflare AI Crawl Control (platform_account; provided by publisher) would unlock 1: A11 (unmeasured half)
- extruct (open_source; provided by this_project) would unlock 1: A6 (coverage)
- oasdiff (open_source; provided by this_project) would unlock 1: F2 (indicator)
- openapi-spec-validator (open_source; provided by this_project) would unlock 1: A2 (coverage)
- Perplexity.ai (hosted_paid; provided by this_project) would unlock 1: C4 (indicator)
- prance (open_source; provided by this_project) would unlock 1: A2 (coverage)
- Scrapy (open_source; provided by this_project) would unlock 1: A5 (coverage)
- slsa-verifier (open_source; provided by this_project) would unlock 1: F6 (indicator)
- ultimate-sitemap-parser (usp) (open_source; provided by this_project) would unlock 1: A5 (coverage)

## Files

- payload: `out/my-site/state/scan_my-site_2026-09-19.json` (every Observation and Finding; re-derivable with `assessment/harness/scan/rederive.py --from`)
- retained response bodies: `out/my-site/evidence/scan_my-site_2026-09-19/`
- matrices: `out/my-site/reports/scan_matrix_*`
- cycle of record: `out/my-site/reports/publication.yaml`
````

The body passes every leg because the fixture was built to pass them all (`passes_all` with a second product). The report's substance is in three places:
- the A12 reason names the adopter's identity: "robots.txt permits example-readiness-scan/1.0 (+mailto:webmaster@example.org)";
- every leg has its reason, read from the payload with no graph;
- the requirements section lists what the harness could not see for any body, and which requirement would let it.

`tests/test_adopter_path.py::test_the_report_is_the_mcp_verbs_answer` asserts two things in-process: every line of the report's body section is `Tools(graph=None, run=…)`'s answer, and `get_evidence` on a Finding returns Observations whose retained bytes hash to their names.

## 2. What needs Neo4j and what does not

| | without Neo4j | with Neo4j |
|---|---|---|
| `make scan-now`: payload, evidence, matrices, `publication.yaml`, report | yes | yes (not read) |
| `rederive.py --from` on the run | yes | yes (not read) |
| `score.py --run` | yes. It never read the graph; its docstring said so before this task | the same |
| MCP `get_body`, `get_prescriptions`, `get_requirements` with `--run` | yes. Finding reasons, error classes and bytes come from the run's payload (`Tools._run_findings`) | yes, from the projection |
| MCP `get_evidence` with `--run` | yes, from the payload | yes, from the projection |
| MCP `get_overview`, `get_document`, `search_text` | yes, from the record | the definition layer of `search_text` needs it |
| MCP `get_indicator`'s verdict counts, `run_cypher`, `projection_gate`, supersession on `get_cycle_of_record` | no. Each says in words that the graph is unreachable and does not guess | yes |
| `make project RUN=…` | no | puts the run on the checkout's event log with `--no-promote` (its bytes stay in `out/`) and runs `build_projection.py` |

**This project's own no-graph server is unchanged.** With no `--run`, `get_evidence` still answers "Neo4j unreachable", and a test asserts it. The payload fallback applies to an adopter run only. This project's snapshot is a re-judgement whose Observations live in another cycle's payload and on the log.

**Not exercised: `make project` and `get_body` over the graph.** On this machine they would reset the projection in the one Neo4j database there is, which is this project's. `write_events` on an adopter payload was exercised into a throwaway log (`test_publishing_a_run_keeps_its_evidence_where_the_run_left_it`): the events carry the overlay, and `body_path` still points into `out/`. The projection step and a graph-backed `get_body` over an adopter run were not run.

## 3. Every premise this task file got wrong

1. **"The target list moves" into `frames/fss16.yaml`, "moved out of `params.yaml` or wherever `run.targets` reads them".** `run.targets` reads a registered DataFile, `state/scan_targets_fss_2026-09_v5.json`: 72 surfaces with their selection sources and admitted corpus doc ids. The same task protects `state/` as byte-identical, and `params.cycle.targets` names that file inside `params_hash`. The list could not move without breaking both, so `fss16.yaml` is `kind: target_datafile` and refers to it instead of copying it. A test holds `fss16.yaml` to the DataFile, tier by tier, and to `params.yaml`'s `targets` and `user_agent`. `run.py` without `--frame` is unchanged. `--frame fss16.yaml` is refused with the reason: this project's cycles are dispatched tasks that write `state/` and the log. The re-derivation tier (23 passed) is the byte-identity proof the task asked for.
2. **"This project's 16 bodies".** The frame is 16 Tier A bodies plus 3 Tier C reference hosts (GSA, NIST, data.gov): 19 agencies and 72 surfaces. `fss16.yaml` lists both tiers.
3. **"`scripts/score.py` and `mcp/` gain `--no-neo4j`".** `score.py` has never read Neo4j (its docstring: "It reads Neo4j for nothing"), and the MCP server has had `--no-graph` since it was written. A `--no-neo4j` flag on either would be a no-op or a duplicate, so none was added. What both lacked was a way to be pointed at an adopter's run. That is `--run DIR` on both, and in `Tools(run=…)` a payload-backed answer where the graph used to be the only source (§2).
4. **"`params.yaml` (`schedule`…)" with no word about `params_hash`.** `params_hash` hashed the whole file, so adding `schedule:` would have moved this project's hash from `0ef2e016fea2…`, the hash `scan_2026-09-10_rj4` (the snapshot) was judged under. It would also have given a cron-triggered cycle and a hand-triggered one different Finding ids from identical evidence. `model.UNHASHED_KEYS = ("schedule",)` excludes the key. No stored parameter set has it, so no recorded hash changes. A test asserts the hash still equals the snapshot's, that `schedule` does not move it, and that `user_agent` does. So `model.py` is in the write set, though the task did not name it.
5. **The write set, beyond that.** Five other files moved that the task did not name, each for the reason given here and in `scripts/check_protected_adopt.sh`:
   - `assessment/harness/scan/adopt.py` (new): frames, the identity refusal and the `out/` layout, shared by five callers;
   - `rederive.py`: `main` re-derives an overlaid run under its overlay, so the report's "re-derivable" line is true;
   - `scripts/prescriptions.py`: `use_run`, the one seam;
   - `scripts/install_schedule.py` (new): what `make install-schedule` runs;
   - `.gitignore`: `out/`.
6. **`report/<cycle>.md` (decision 4) and `out/<cycle>/report.md` (decision 5, §4) name two layouts.** The one built is `out/<frame>/report/<cycle>.md` under `out/<frame>/{state,evidence,reports}/`. A frame accumulates runs, and a spot run within a frame is read beside the frame's run of record (`out/<frame>/reports/publication.yaml`). A directory per cycle would have no place to hold that relation.
7. **"Clone … `make scan-now` … optionally `make project` and `get_body`", all "exercised end to end in the gate".** Two steps cannot run under `**Network:** allowlist: 127.0.0.1`: the clone and the `pip install`. `make project` would reset this machine's only projection. So the runbook fences those two blocks `not-run-by-gate`, and the gate asserts that they are the only two. `get_body` is exercised without the graph (runbook block 8).
8. **"Every command in the runbook is the command the gate ran, copied from its log, not typed."** This is inverted, so the claim cannot drift: the gate reads the commands from the runbook. The frame's port cannot be known in advance, so the gate's frame names `127.0.0.1:${SITE_PORT}`, and the page says so.
9. **Decision 3 needs the project's identity in a checkout where `params.yaml` is the adopter's.** `fss16.yaml` records the identity as `user_agent`. The refusal compares product tokens (RFC 9110 §10.1.5), so `ai-readiness-kg-scanner/0.3` is refused too. It also refuses a User-Agent with no contact against a non-loopback host.
10. **The Makefile pinned `PY := /opt/anaconda3/bin/python3`**, so an adopter's `make` would call a path that does not exist on their machine. It is `PY ?=` now. The value is unchanged here, and the runbook exports `PY`.
11. **"`make scan-now`" with no frame.** Here it would mean a cycle over 22 federal hosts from a make target, which is the thing "cadence off" rules out. So `make scan-now` refuses without `FRAME=`, and `--frame` refuses this project's frame.
12. **Two notes, not premises.**
    - `docs/adopt/` is under `docs/`, the Pages source, so the runbook is published on the next push. The task names that path.
    - The real-clock control cycle takes about 10 of the runbook's 12.3 minutes. An adopter will see that wait before their site is touched, and the runbook says the controls run first.

## 4. Gate

| gate | tier | result | log |
|---|---|---|---|
| `make gate-task` fast | everything but `slow` | 2707 passed, 3 skipped, 27 deselected, 12 xfailed, 0 failed, 643.34 s | `logs/adopt_gate_task.log` |
| `make gate-task` re-derivation | `-k re_derives`, every stored payload | 23 passed, 0 skipped, 25 deselected, 0 xfailed, 11.35 s; `EXIT=0`, wall 659 s | `logs/adopt_gate_task.log` |
| full suite | `pytest tests/ assessment/ -q -rs` | 2734 passed, 3 skipped (the expected 3), 0 deselected, 12 xfailed, 0 failed, 2298.25 s; `EXIT=0` | `logs/adopt_gate_full.log` |
| runbook alone | `-k runbook_runs_as_written` | 1 passed, 0 skipped, 41 deselected, 0 xfailed, 771.41 s; `EXIT=0` | `logs/adopt_runbook_pytest.log`, `logs/adopt_runbook.log` |
| new module, fast tier (development run) | `tests/test_adopter_path.py -m "not slow"` | 41 passed, 0 skipped, 1 deselected, 0 xfailed | contained in both gate runs above |
| `seldon verify` | — | `EXIT=1`: 0 issues, 1 pre-existing warning (36 stale `_rj2`); `--strict` `EXIT=0` | `logs/adopt_seldon_verify.log`, `logs/adopt_seldon_verify_strict.log` |
| protected paths | `scripts/check_protected_adopt.sh` | `PROTECTED PATHS OK`, `EXIT=0` | `logs/adopt_protected.log` |

This project's settings are unchanged (decision 6):
- the frame is the same DataFile;
- `schedule.when` is `on_demand`, and `make install-schedule` here prints "nothing installed" (runbook block 10, and `test_on_demand_installs_nothing`);
- the identity is `ai-readiness-kg-scanner/0.2 (+https://github.com/brockwebb/ai-readiness-kg)`;
- `params_hash` is `0ef2e016fea2…`, the same as before the task;
- no cadence entry was touched, and Seldon is not involved in the adopter path.
