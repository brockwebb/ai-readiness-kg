#!/usr/bin/env bash
# The zero-edits list of `cc_tasks/2026-09-11_a3_a10_sources.md`, asserted against HEAD.
#
#   "Zero edits to: rule modules, harness runtime, stored payloads, prior Results, prior
#    RESULTs, cycle evidence, targets, figures, existing Document nodes, report prose beyond
#    decision 4."
#
# Decision 4 resolved to "the report carries no per-check source list, so it is not touched",
# so docs/reports/ is protected WHOLE here rather than partly. Then it LISTS what did change.
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
  'state/'
  'corpus/'
  'docs/reports/'
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

# **Existing Document nodes.** Nothing here writes one: the corpus manifest is unchanged (above,
# corpus/ is protected whole), and the framework loader only ever MATCHes a Document to hang an
# edge on it. Asserted on the loader's source rather than on the graph, because the graph holds
# no "before" to diff against and a claim that nothing moved has to be checkable.
if grep -nE '(SET|MERGE|CREATE)[^"]*:Document' scripts/load_framework_graph.py \
     | grep -v 'MATCH (d:Document' ; then
  echo "FAIL scripts/load_framework_graph.py writes to a Document node"
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS  every protected path is byte-identical to HEAD; no Document node is written"
fi

echo
echo "what DID change:"
{ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u | sed 's/^/       /'
exit "$fail"
