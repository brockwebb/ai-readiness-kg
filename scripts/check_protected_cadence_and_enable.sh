#!/bin/bash
. "$(dirname "$0")/check_protected_lib.sh"
# Protected-paths diff for `cc_tasks/2026-09-16_cadence_and_enable.md` §5.
#
# The task's "Zero edits to" list, checked against the working tree rather than asserted in
# prose. A task that says it touched nothing and a diff that says otherwise is the disagreement
# this script exists to find before the RESULT claims the first one.
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO" || exit 1
fail=0

# Paths this task may not have touched at all.
PROTECTED=(
  "assessment/"
  "state/"
  "events/"
  "corpus/"
  "controls.yaml"
  "docs/reports/"
  "framework/"
  "kg/"
  "scripts/build_l0_report.py"
  "scripts/build_l0_site.py"
  "scripts/build_l0_matrices.py"
)
echo "=== protected paths: must show NO diff against HEAD ==="
for p in "${PROTECTED[@]}"; do
  out=$(git diff HEAD --stat -- "$p"; git status --porcelain -- "$p" | grep '^??' || true)
  if [ -n "$out" ]; then
    echo "FAIL $p"
    echo "$out"
    fail=1
  else
    echo "ok   $p"
  fi
done

echo
echo "=== CLAUDE.md: the task says it gains nothing ==="
if git diff HEAD --quiet -- CLAUDE.md; then
  echo "ok   CLAUDE.md unchanged"
else
  echo "FAIL CLAUDE.md changed:"
  git diff HEAD --stat -- CLAUDE.md
  fail=1
fi

echo
echo "=== seldon.yaml: only the dispatch block ==="
git diff HEAD -- seldon.yaml | grep '^[+-][^+-]' | grep -v '^[+-] *#' > /tmp/airkg_sy_diff.$$ || true
echo "changed non-comment lines:"
cat /tmp/airkg_sy_diff.$$
if grep -qE '^[+-] *(event_store|neo4j|project|shared_ontology):' /tmp/airkg_sy_diff.$$; then
  echo "FAIL seldon.yaml changed outside the dispatch block"
  fail=1
else
  echo "ok   seldon.yaml changed only inside dispatch:"
fi
rm -f /tmp/airkg_sy_diff.$$

echo
echo "=== the event log: this task writes no dispatch_* or cadence_created event ==="
added=$(git diff HEAD -- seldon_events.jsonl | grep '^+' | grep -c -E '"event_type": ?"(dispatch_|cadence_created)' || true)
echo "dispatch_/cadence_created events added by this task: $added"
if [ "$added" != "0" ]; then
  echo "FAIL the dispatcher wrote an event during this task"
  fail=1
else
  echo "ok   no dispatcher event written"
fi

echo
if [ "$fail" = "0" ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
