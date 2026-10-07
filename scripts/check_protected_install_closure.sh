#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-07_install_closure_v2.md`, asserted against the commit the
# task started from (default a026e05a, HEAD when it was launched), not against HEAD: the task
# commits its code before `make gate-full`, because its stranger gate runs a `git archive` of
# HEAD, so HEAD already holds the work being checked.
#
# Write set, the task's own words: `pyproject.toml`, `docs/adopt/run_on_your_site.md` and its
# generator (`scripts/build_adopt_requirements.py`), `tests/test_adopter_path.py`, `Makefile`,
# the RESULT. Plus this check and the Seldon store (`seldon cc complete`). Byte-identical: every
# rule, collector, matrix and report, every stored payload and the framework record.
set -u
cd "$(dirname "$0")/.." || exit 2
BASE="${1:-a026e05a}"
fail=0

changed_and_new() {
  { git diff --name-only "$BASE" -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

allowed() {
  case "$1" in
    pyproject.toml|Makefile|docs/adopt/run_on_your_site.md) return 0 ;;
    scripts/build_adopt_requirements.py|scripts/check_protected_install_closure.sh) return 0 ;;
    tests/test_adopter_path.py|seldon_events.jsonl) return 0 ;;
    cc_tasks/2026-10-07_install_closure_v2_RESULT.md) return 0 ;;
  esac
  return 1
}

while IFS= read -r path; do
  [ -z "$path" ] && continue
  allowed "$path" || { echo "FAIL path outside the write set moved: $path"; fail=1; }
done < <(changed_and_new .)

for p in assessment/harness/scan/rules assessment/harness/scan/collectors docs/reports reports \
         framework/ai_readiness_framework.json state events corpus/manifest.json; do
  if [ -n "$(changed_and_new "$p")" ]; then echo "FAIL $p must be byte-identical and moved"; fail=1; fi
done

# Append-only: the Seldon store.
removed=$(git diff "$BASE" -- seldon_events.jsonl | grep -c '^-[^-]' || true)
if [ "$removed" -ne 0 ]; then echo "FAIL seldon_events.jsonl lost or changed $removed line(s)"; fail=1; fi

# The runbook's generated section re-renders from pyproject.toml exactly.
PY="${PY:-/opt/anaconda3/bin/python3}"
"$PY" scripts/build_adopt_requirements.py --check >/dev/null 2>&1 \
  || { echo "FAIL docs/adopt/run_on_your_site.md drifts from pyproject.toml"; fail=1; }

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
