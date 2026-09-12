#!/usr/bin/env bash
# The zero-edits list of `cc_tasks/2026-09-11_framework_single_writer.md`, asserted against HEAD:
#
#   "Zero edits to: the skeleton, the record's content (this task adds no node or edge), the
#    projection loader, rule modules, harness, payloads, prior Results, docs/reports/."
#
# Then it LISTS what did change, so a reader sees the whole diff surface, not only the fence.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

protected=(
  'docs/crosswalk/usafacts_operationalization_skeleton.md'
  'framework/ai_readiness_framework.json'
  'scripts/load_framework_graph.py'
  'assessment/harness/'
  'state/'
  'corpus/'
  'docs/reports/'
  'events/'
  'cc_tasks/2026-09-11_a3_a10_sources_RESULT.md'
)

for p in "${protected[@]}"; do
  changed=$(git diff --name-only HEAD -- "$p"; git ls-files --others --exclude-standard -- "$p")
  if [ -n "$changed" ]; then
    echo "FAIL protected path moved: $p"
    echo "$changed" | sed 's/^/       /'
    fail=1
  fi
done

# Prior RESULTs: none may change. New RESULTs (this task's own) are allowed.
prior=$(git diff --name-only HEAD -- 'cc_tasks/*_RESULT.md')
if [ -n "$prior" ]; then
  echo "FAIL a prior RESULT changed:"
  echo "$prior" | sed 's/^/       /'
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo "PASS  every protected path is byte-identical to HEAD; no prior RESULT changed"
fi

echo
echo "what DID change:"
{ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u | sed 's/^/       /'
exit "$fail"
