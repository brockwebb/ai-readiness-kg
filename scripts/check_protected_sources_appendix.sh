#!/usr/bin/env bash
# The zero-edits list of `cc_tasks/2026-09-11_report_sources_appendix.md`, asserted against HEAD:
#
#   "Zero edits to: rule modules, harness, payloads, prior Results, prior RESULTs, figures, the
#    skeleton and the record beyond decision 4, report section prose (a `{{fragment}}`-style
#    include for the appendix is the only change to a section file)."
#
# Decision 4 resolved to "A10 stays `stub`", so the record is protected WHOLE here. The section
# rule is asserted on the diff itself: the only section file that may change is 80_appendix.md,
# and every added line in it must be the include marker, its bold label, or blank.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

protected=(
  'assessment/harness/'
  'state/'
  'corpus/'
  'docs/crosswalk/usafacts_operationalization_skeleton.md'
  'framework/ai_readiness_framework.json'
  'events/'
  'docs/reports/generated/matrix_tierA.md'
  'docs/reports/generated/matrix_tierC.md'
  'docs/reports/generated/matrix_product.md'
  'docs/reports/generated/rules_by_leg.md'
  'docs/reports/generated/requests_per_netloc.md'
  'docs/reports/scan_matrix_product_2026-09-10_rj2.csv'
  'docs/reports/scan_matrix_tierA_2026-09-10_rj2.csv'
  'docs/reports/scan_matrix_tierC_2026-09-10_rj2.csv'
)

for p in "${protected[@]}"; do
  changed=$(git diff --name-only HEAD -- "$p"; git ls-files --others --exclude-standard -- "$p")
  if [ -n "$changed" ]; then
    echo "FAIL protected path moved: $p"
    echo "$changed" | sed 's/^/       /'
    fail=1
  fi
done

prior=$(git diff --name-only HEAD -- 'cc_tasks/*_RESULT.md')
if [ -n "$prior" ]; then
  echo "FAIL a prior RESULT changed:"
  echo "$prior" | sed 's/^/       /'
  fail=1
fi

# Section prose: only 80_appendix.md, and only the include and its label.
sections=$(git diff --name-only HEAD -- docs/reports/sections/ | grep -v '80_appendix.md$' || true)
if [ -n "$sections" ]; then
  echo "FAIL a section other than 80_appendix.md changed:"
  echo "$sections" | sed 's/^/       /'
  fail=1
fi
added=$(git diff HEAD -- docs/reports/sections/80_appendix.md | grep '^+' | grep -v '^+++' | sed 's/^+//')
removed=$(git diff HEAD -- docs/reports/sections/80_appendix.md | grep '^-' | grep -v '^---' || true)
if [ -n "$removed" ]; then
  echo "FAIL 80_appendix.md lost a line:"
  echo "$removed" | sed 's/^/       /'
  fail=1
fi
while IFS= read -r line; do
  case "$line" in
    ''|'**Sources per check.**'|'<!-- include: sources_per_check -->') ;;
    *) echo "FAIL 80_appendix.md gained prose beyond the include: $line"; fail=1 ;;
  esac
done <<< "$added"

if [ "$fail" -eq 0 ]; then
  echo "PASS  every protected path is byte-identical to HEAD; the only section change is the include"
fi

echo
echo "what DID change:"
{ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u | sed 's/^/       /'
exit "$fail"
