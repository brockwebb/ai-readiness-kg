#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-09_main_green_dispatch_stuck_without_a_path.md`, asserted
# against the commit the task started from (argument 1). The task: "No verdict, record, score or
# framework cell may change"; the dispatcher's c7 and stuck counter (in Seldon), the tests that run
# a real pass, and the daily job's Issue and STOP handling. Nothing under the scan harness, the
# framework record, the corpus or the event shards moves.
set -u
cd "$(dirname "$0")/.." || exit 2
BASE="${1:?usage: check_protected_main_green.sh <base commit>}"
fail=0
TASK_STEM=2026-10-09_main_green_dispatch_stuck_without_a_path

changed_and_new() {
  { git diff --name-only "$BASE" -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Every path that moved is on the write set.
while read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    Makefile|scripts/jobs/airkg_daily_suite.sh|scripts/jobs/daily_suite_issues.py|\
    tests/test_dispatch_config.py|tests/test_dispatch_stuck_isolation.py|\
    tests/test_daily_suite_job.py|scripts/check_protected_main_green.sh|\
    docs/design/2026-09-15_DN-006_standing_dispatcher_ADDENDUM_08.md|\
    "cc_tasks/${TASK_STEM}_RESULT.md") ;;
    *) echo "FAIL moved outside the write set: $f"; fail=1 ;;
  esac
done <<< "$(changed_and_new .)"

# 2. A prior task file or RESULT is immutable.
if git diff --name-only "$BASE" -- cc_tasks/ | grep -v "^cc_tasks/${TASK_STEM}_RESULT.md$" | grep -q .; then
  echo "FAIL a tracked cc_tasks file changed:"; git diff --name-only "$BASE" -- cc_tasks/; fail=1
fi

# 3. The framework record, the scan harness, the events shards and the published views are
#    byte-identical (named, so a write-set slip there cannot hide behind rule 1's case list).
for p in framework/ assessment/ events/ kg/ corpus/ docs/brief/ docs/views/ controls.yaml \
         seldon.yaml dixie_evidence.yaml; do
  if git diff --quiet "$BASE" -- "$p" 2>/dev/null; then :; else
    echo "FAIL a protected path changed: $p"; fail=1
  fi
done

# 4. Logs are append-only.
if git diff "$BASE" -- seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost or changed a line; the log is append-only"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
