#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The ship set of `cc_tasks/2026-10-04_views_regenerate_v3.md`, asserted against HEAD.
#
# Decision 6's expected diff, by file: the generator, the pack pages it regenerates (B, C, E, H
# and the number ledger), the two L0 site outputs the site generator moved, the evidence map,
# the deck module's mark, the RESULT and this file. Every other path is byte-identical to HEAD,
# which covers the task's byte-identical list (`docs/deck/`, `docs/catalog/`, `docs/figures/`,
# `docs/design/`, `framework/`, `corpus/`, `events/`). The line-level check of decision 6 is in
# the RESULT; this asserts the file set.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

ALLOWED=(
  'scripts/build_brief_pack.py'
  'docs/brief/B_usafacts_delta.md'
  'docs/brief/C_provenance.md'
  'docs/brief/E_architecture.md'
  'docs/brief/H_limits.md'
  'docs/brief/numbers.json'
  'docs/data/corpus_manifest.json'
  'docs/data/index.json'
  'docs/evidence/claims.yaml'
  'tests/test_brief_deck.py'
  'cc_tasks/2026-10-04_views_regenerate_v3_RESULT.md'
  'scripts/check_protected_views_regenerate_v3.sh'
)
while IFS= read -r path; do
  [ -z "$path" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$path" = "$a" ] && ok=1 && break; done
  if [ "$ok" -eq 0 ]; then echo "FAIL path outside the ship set moved: $path"; fail=1; fi
done < <(changed_and_new .)

# Decision 5: the deck module gains its mark and nothing else.
deck=$(git diff HEAD -- tests/test_brief_deck.py | grep '^[+-][^+-]' || true)
want='+pytestmark = pytest.mark.xfail(run=False, strict=True, reason="DN-009: deck rejected 2026-10-02; pinned at the 264-document corpus until removed")'
other=$(printf '%s\n' "$deck" | sed '/^$/d' | grep -v '^+$' | grep -vxF -- "$want" || true)
if [ -n "$other" ]; then echo "FAIL tests/test_brief_deck.py moved beyond its module mark:"; echo "$other"; fail=1; fi

# The store is append-only.
removed=$(git diff HEAD -- seldon_events.jsonl | grep -c '^-[^-]' || true)
if [ "$removed" -ne 0 ]; then echo "FAIL seldon_events.jsonl lost or changed $removed line(s)"; fail=1; fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
