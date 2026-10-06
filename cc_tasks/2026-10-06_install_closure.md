# CC Task: `pip install .` installs a working tool, proven on a clean interpreter (audit F-05, F-20)

**Date:** 2026-10-06
**Project:** ai-readiness-kg
**Authored by:** Desktop session, from `docs/audit/2026-10-04_full_audit.md` operationalization items F-05 (`pyproject.toml:10` declares pyyaml alone; the scan imports nine packages and the repo imports seldon and dixie) and F-20 (`tests/test_adopter_path.py:510`: the "stranger" gate runs on the author's interpreter, `HOME` and untracked files). Nothing outside this machine can run the harness today; that is the first thing a reviewer tries.
**Implements:** DN-012 (closure of F-05, F-20); DN-005 §1 (open source exists so the work can be run by others).
**Framework layer served (DN-005 §5 rule 1):** hygiene; it advances no layer and says so. It is what lets any layer be checked by a stranger.
**Fulfils:** its own ResearchTask. Launched by the dispatcher.
**After:** none.
**Spend:** est. 1.5M tokens (Opus). Dependency work, one clean-venv run, the suite. No model call.
**Network:** `pip` against the package index for the clean-venv install; `git push`. No fetch by the harness.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

## Decisions

1. **Declare what is imported.** Enumerate every third-party import under `assessment/`, `kg/`, `scripts/` and `tests/` by static scan (not by what happens to be installed), pin each with the version the author's environment runs, and write them to `pyproject.toml`. `seldon` and `dixie` are declared as the git dependencies they are, at the commit this repository runs against; if either cannot be declared as a dependency because it is not installable from a URL, say so in the RESULT and in `docs/adopt/run_on_your_site.md`, as a limit.

2. **The stranger run.** In a fresh virtual environment with `HOME` set to a scratch directory and the repository checked out from `git archive` of HEAD (no untracked files, no author config), run `pip install .` and then the adopter path in `docs/adopt/run_on_your_site.md` against the self-site fixture only (no network). Record every failure and fix it at its cause. Stop fixing when the path runs to a finished self-scan; what remains is listed, not patched.

3. **Make the stranger gate real.** `tests/test_adopter_path.py` gains a mode that runs decision 2 in a subprocess with a scratch `HOME` and a `git archive` tree, marked slow, run by `make gate-full`. It fails on any undeclared import. The existing in-process test stays.

4. **Record the environment.** `docs/adopt/run_on_your_site.md` states the Python version, the Neo4j requirement and how to point at it, and the exact install line, generated from `pyproject.toml` so the two cannot drift.

**Write set:** `pyproject.toml`, `docs/adopt/run_on_your_site.md` and its generator, `tests/test_adopter_path.py`, `Makefile`, the RESULT. Byte-identical: every rule, collector, matrix and report.

**Immutable once written.**

## Gate and report
`make gate-fast`, `make gate-full`, `seldon verify`, the protected-paths diff. RESULT `cc_tasks/2026-10-06_install_closure_RESULT.md`, under 40 lines: the dependency list as declared; every failure the clean run hit and its fix; what remains undoable from a clean machine; premises wrong; tokens and model. `seldon cc complete`, commit, push.

**SEQUENCING:** static import scan → pyproject → clean venv run → fixes → gate mode → docs generator → gate-full → RESULT → push.
