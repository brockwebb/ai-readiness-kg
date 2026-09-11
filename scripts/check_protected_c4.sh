#!/usr/bin/env bash
# The zero-edits list of `cc_tasks/2026-09-11_l0_report_cycle4_revision.md`, asserted against
# HEAD rather than eyeballed in a diff.
#
#   "Zero edits to: rule modules, harness runtime, stored payloads, prior Results, prior
#    RESULTs, cycle evidence, targets, registration records, invariant pins, figures (they are
#    read, not re-rendered), report prose beyond decision 3 and 4."
#
# The last clause is a judgement and is argued in the RESULT; every other one is mechanical and
# is checked here. Then it LISTS what did change, because a check that only says "nothing
# forbidden moved" tells a reader nothing about what did.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

protected=(
  'assessment/harness/scan/rules/'
  'assessment/harness/scan/collectors/'
  'assessment/harness/probes/'
  'assessment/harness/scan/runner.py'
  'assessment/harness/scan/run.py'
  'assessment/harness/scan/publish.py'
  'assessment/harness/scan/rederive.py'
  'assessment/harness/scan/model.py'
  'assessment/harness/scan/errors.py'
  'assessment/harness/scan/manners.py'
  'assessment/harness/scan/stats.py'
  'assessment/harness/scan/frame.py'
  'assessment/harness/scan/figures.py'
  'assessment/harness/scan/figures.yaml'
  'assessment/harness/scan/params.yaml'
  'assessment/harness/scan/fixtures/'
  'assessment/harness/scan/figures/'
  'state/scan_'
  'corpus/evidence/'
  'tests/test_invariants.py'
)

for p in "${protected[@]}"; do
  changed=$(git diff --name-only HEAD -- "$p"; git ls-files --others --exclude-standard -- "$p")
  if [ -n "$changed" ]; then
    echo "FAIL protected path moved: $p"
    echo "$changed" | sed 's/^/       /'
    fail=1
  fi
done

# A stored payload is immutable and a figure is read, not re-rendered: assert the FILES are
# byte-identical to HEAD, not merely untracked-clean.
for f in $(git ls-files 'state/scan_*.json' 'assessment/harness/scan/figures/*/*.svg'); do
  if ! git diff --quiet HEAD -- "$f"; then
    echo "FAIL immutable artifact edited: $f"
    fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  echo "PASS  every protected path is byte-identical to HEAD"
fi

echo
echo "what DID change:"
{ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u | sed 's/^/       /'
exit "$fail"
