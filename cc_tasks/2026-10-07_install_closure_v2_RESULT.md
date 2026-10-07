# RESULT: install closure v2 (audit F-05, F-20)

**Task:** `cc_tasks/2026-10-07_install_closure_v2.md` (no addenda). **Model:** claude-opus-5-5 (Claude Code). **Tokens:** no tool in this session meters its own tokens, so none is quoted; the task's estimate was 1.5M. No model call by the harness, and none by any script. **Commits:** `da29f0a3` (the code, committed before `gate-full` because the stranger gate archives HEAD), then this RESULT.

## 0. Gates (all ran to completion; logs under `logs/`)
- `make gate-fast`: 3131 passed, 3 skipped, 30 deselected, 41 xfailed, EXIT=0, 942 s (`2026-10-07_install_closure_gate_fast.log`).
- `make gate-full`: 3161 passed, 3 skipped, 0 deselected, 41 xfailed, EXIT=0, 4229 s (`2026-10-07_install_closure_gate_full.log`, copied from `suite.log`). It ran the stranger gate on 3.12.4 against `da29f0a3` (`adopt_stranger_py3.12.4.log`) and the in-process runbook (`adopt_runbook.log`).
- `seldon verify`: all checks passed, EXIT=0 (`2026-10-07_install_closure_verify.log`). Protected paths (`scripts/check_protected_install_closure.sh a026e05a`, after the suite): PASS, EXIT=0 (`2026-10-07_install_closure_protected.log`).

## 1. Dependencies as declared (`pyproject.toml`, every one pinned to the author's interpreter)
Static `ast` scan of every tracked `.py` under `assessment/ kg/ scripts/ tests/ mcp/` found 29 third-party modules. Declared:
- **runtime (`pip install .`):** beautifulsoup4 4.12.3, extruct 0.18.0, httpx 0.28.1, jsonschema 4.26.0, Protego 0.1.16, pyshacl 0.40.1, rdflib 7.6.0, ultimate-sitemap-parser 1.8.1, PyYAML 6.0.1. `requires-python >=3.11`.
- **`graph`:** neo4j 6.0.3, seldon @ git+github.com/brockwebb/seldon@a694322e. **`mcp`:** fastmcp 3.2.3, neo4j 6.0.3. **`kg`:** dixie @ git+github.com/brockwebb/dixie@eeac6c4e, pypdf 6.7.0, tiktoken 0.12.0, nltk 3.9.3, docling 2.72.0. **`publishing`:** matplotlib 3.8.4, numpy 1.26.4, pillow 12.1.1, python-pptx 1.0.2, pypdf, textstat 0.7.13. **`research`:** pandas 2.2.2, crowd-kit 1.4.2, requests 2.34.2, sentence-transformers 4.1.0, numpy. **`dev`:** pytest 9.0.2, pytest-cov 7.0.0. **`all`:** every extra.
- **undeclarable (`[tool.airkg.install]`):** `control_plane`, `harvester`. `test_every_third_party_import_is_declared` fails on any other undeclared import.

## 2. What the clean run hit, and the fix
1. `pip install .` at the pre-task commit `a026e05a`, fresh venv: `Multiple top-level packages discovered in a flat-layout: ['kg', 'mcp', 'logs', …]`, EXIT=1 (`2026-10-07_install_closure_base_install.log`). Fixed at the cause: `[build-system]` plus `[tool.setuptools] packages = []`. The checkout is the tool; the install puts in the dependencies and no second copy of `kg`.
2. Only pyyaml was declared. Fixed: the nine above. The runbook's step 1 is now `python3 -m venv .venv; . .venv/bin/activate; python3 -m pip install .`.
3. 3.10.17 was refused by my own provisional `>=3.11`. With that bound lifted, the adopter path ran clean on 3.10.17 (`2026-10-07_stranger_explore_3.10.log`). The bound stays at 3.11 because eight repository modules import `tomllib` or `datetime.UTC` and dixie declares >=3.11.
4. Nothing else failed. Steps 2 to 6 ran unchanged through to a finished self-scan (CONTROL GATE PASS, RE-DERIVATION GATE PASS, report, score) on 3.11.12 and 3.14.5 (`adopt_stranger_py3.11.12.log`, `adopt_stranger_py3.14.5.log`, by `make gate-stranger`'s test with `AIRKG_STRANGER_PYTHON`), on 3.12.4 under `gate-full`, and on 3.12.13 in the exploratory run (`2026-10-07_stranger_explore_3.12.log`). Each run passed `pip check`.
5. Decision 3: `test_a_stranger_installs_and_runs_the_runbook` (slow; `make gate-full`, and alone as `make gate-stranger`) does the following: `git archive` of HEAD, the runbook's own install lines, `HOME` set to scratch, `PATH` = one `python3` + `/usr/bin:/bin:/usr/sbin:/sbin`, every `bash` block. The in-process test stays, with its assertions shared. Decision 4: `scripts/build_adopt_requirements.py [--check]` generates the runbook's requirements and install section from `pyproject.toml` and `seldon.yaml`. A suite test runs `--check`.

## 3. What a clean machine still cannot do (listed, not patched)
- The `kg` extra: anonymous `git ls-remote https://github.com/brockwebb/dixie.git` is refused (seldon's answers `a694322e`). That leaves corpus admission and extraction author-only. So are `run_bulk_extraction.py`, `batch_repair.py`, `repair_relocate.py` (`control_plane`) and `accept_two_acts.py` (`harvester`), which import from `~/.wintermute`.
- No clean venv installed the extras. Only the runtime set was measured. Step 7 (Neo4j, `make project`) is still not run by any gate (F-13, F-14).
- Transitive dependencies are not pinned. There is no lock file, and the 3.14 run resolved its own (e.g. lxml 6.1.3). The stranger gate needs pypi.org. Every run was on macOS, against the loopback fixture only.
- Out of scope and unchanged: the Makefile's `PY ?= /opt/anaconda3/bin/python3` (F-07; the runbook exports `PY`, but a new terminal does not) and the `sys.path` inserts of `/Users/brock/GitHub/seldon` (F-16).

## 4. Premises wrong
- Decision 1 assumes seldon and dixie are both installable from a URL. Only seldon is, for a stranger.
- Audit F-05 called `control_plane` and `harvester` modules that "do not resolve here". They do resolve here, through `sys.path` inserts into `~/.wintermute`. They are not packages anywhere, so the fault is not an oversight in the declaration.
- The runbook said "That is what a clone of the pushed commit holds" (the copy included untracked files, F-20) and "Seldon is not used" (step 7 needs it, F-13). Both sentences are corrected.
- The write set did not name a protected-paths check. I added `scripts/check_protected_install_closure.sh`, which checks against `a026e05a` because HEAD already holds the work.
