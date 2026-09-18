#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The zero-edits list of `cc_tasks/2026-09-12_cited_documents_metadata_2.md`, asserted
# against HEAD:
#
#   "Zero edits to: corpus file bytes and hashes, events/batch-*.jsonl, rule modules,
#    harness, payloads, prior Results, prior RESULTs, figures, the skeleton, the record,
#    section prose."
#
# Two paths under corpus/ are SUPPOSED to move and are the point of the task:
# `corpus/evidence/decisions.jsonl` (the ledger gains six metadata_corrected events) and
# `corpus/manifest.json` (its projection). Everything else under corpus/ is protected, and
# the document binaries are gitignored, so their bytes are asserted by `kg.manifest verify`
# re-hashing every entry rather than by this diff.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

protected=(
  'assessment/harness/'
  'state/'
  'events/'
  'framework/ai_readiness_framework.json'
  'docs/crosswalk/usafacts_operationalization_skeleton.md'
  'docs/reports/sections/'
  'docs/reports/generated/matrix_tierA.md'
  'docs/reports/generated/matrix_tierC.md'
  'docs/reports/generated/matrix_product.md'
  'docs/reports/generated/rules_by_leg.md'
  'docs/reports/generated/requests_per_netloc.md'
)

for p in "${protected[@]}"; do
  changed=$(git diff --name-only HEAD -- "$p"; git ls-files --others --exclude-standard -- "$p")
  if [ -n "$changed" ]; then
    echo "FAIL protected path moved: $p"
    echo "$changed" | sed 's/^/       /'
    fail=1
  fi
done

echo "== corpus/: only the ledger and its projection may move =="
corpus=$(git diff --name-only HEAD -- corpus/ \
  | grep -Ev '^corpus/(evidence/decisions\.jsonl|manifest\.json)$' || true)
if [ -n "$corpus" ]; then
  echo "FAIL a corpus path other than the ledger and its projection moved:"
  echo "$corpus" | sed 's/^/       /'
  fail=1
fi

echo "== the ledger is append-only =="
# Every line that was in HEAD's ledger must still be there, byte-identical, in the same
# order. A correction is a new line at the end; an EDIT to an existing one is the failure
# this repo's first invariant exists to prevent.
old_lines=$(git show HEAD:corpus/evidence/decisions.jsonl | wc -l | tr -d ' ')
if ! git show HEAD:corpus/evidence/decisions.jsonl \
     | diff -q - <(head -n "$old_lines" corpus/evidence/decisions.jsonl) > /dev/null; then
  echo "FAIL the ledger's first $old_lines lines are not byte-identical to HEAD"
  fail=1
else
  new_lines=$(wc -l < corpus/evidence/decisions.jsonl | tr -d ' ')
  echo "       ledger: $old_lines lines at HEAD, $new_lines now, all $old_lines unchanged"
fi

echo "== no prior RESULT changed =="
# This task's OWN RESULT is the one RESULT file it may add; every other is prior work.
OWN_RESULT='cc_tasks/2026-09-12_cited_documents_metadata_2_RESULT.md'
prior=$(git diff --name-only HEAD -- 'cc_tasks/*_RESULT.md' | grep -v "^${OWN_RESULT}\$" || true)
if [ -n "$prior" ]; then
  echo "FAIL a prior RESULT changed:"
  echo "$prior" | sed 's/^/       /'
  fail=1
fi

if [ "$fail" -eq 0 ]; then
  echo
  echo "PASS  every protected path is byte-identical to HEAD; the ledger only grew"
fi

echo
echo "what DID change:"
{ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u | sed 's/^/       /'
exit "$fail"
