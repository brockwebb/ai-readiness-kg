#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-02_scan_catalog.md` (+ ADDENDUM-01), asserted against HEAD.
#
#   "Byte-identical: everything else, including docs/evidence/, docs/brief/, docs/deck/, and the
#    framework record. No projection, no scan run, no collector built, no model call outside the
#    reader gate and the web searches in decision 4."
#
# Paths that moved and that the task file's write set does not name, each reported in the RESULT:
#
#   * docs/catalog/catalog_inputs.yaml — the declared inputs (value ratings, cheap-pass cases,
#     enabler quotes, tool licences): the generator reads them, so they ship with it.
#   * docs/catalog/enablers.csv, docs/catalog/enablers.md — decision 4's table.
#   * docs/catalog/rollups/{unlockers,set_cover,set_cover_uncovered,quick_wins}.csv and
#     docs/catalog/rollups/rollups.md — decision 5 (a) and addendum decision 12, split into files.
#   * scripts/check_protected_scan_catalog.sh — this file.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright.
for p in 'docs/evidence/' 'docs/brief/' 'docs/deck/' 'framework/' 'docs/reports/' 'kg/' \
         'assessment/' 'mcp/' 'events/' 'corpus/' 'state/' 'controls.yaml' 'seldon.yaml' \
         'dixie_evidence.yaml' 'docs/design/' 'docs/design_decisions.md' 'docs/data/'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. Every path that moved is on the list.
ALLOWED=(
  'docs/catalog/README.md'
  'docs/catalog/catalog_inputs.yaml'
  'docs/catalog/scan_catalog.csv'
  'docs/catalog/scan_catalog.md'
  'docs/catalog/actions.csv'
  'docs/catalog/actions.md'
  'docs/catalog/enablers.csv'
  'docs/catalog/enablers.md'
  'docs/catalog/front_door.csv'
  'docs/catalog/rollups/criterion_by_who.csv'
  'docs/catalog/rollups/matrix_actions.csv'
  'docs/catalog/rollups/matrix_scans.csv'
  'docs/catalog/rollups/quick_wins.csv'
  'docs/catalog/rollups/rollups.md'
  'docs/catalog/rollups/set_cover.csv'
  'docs/catalog/rollups/set_cover_uncovered.csv'
  'docs/catalog/rollups/staffing_by_cost.csv'
  'docs/catalog/rollups/unlockers.csv'
  'scripts/build_scan_catalog.py'
  'scripts/check_protected_scan_catalog.sh'
  'tests/test_scan_catalog.py'
  'cc_tasks/2026-10-02_scan_catalog_RESULT.md'
)
while IFS= read -r path; do
  [ -z "$path" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$path" = "$a" ] && ok=1 && break; done
  if [ "$ok" -eq 0 ]; then echo "FAIL path outside the write set moved: $path"; fail=1; fi
done < <(changed_and_new .)

# 3. The append-only store: no line removed or changed.
removed=$(git diff HEAD -- seldon_events.jsonl | grep -c '^-[^-]' || true)
if [ "$removed" -ne 0 ]; then echo "FAIL seldon_events.jsonl lost or changed $removed line(s)"; fail=1; fi

# 4. Prior RESULTs and task files unchanged.
moved=$(git diff --name-only HEAD -- 'cc_tasks/')
if [ -n "$moved" ]; then echo "FAIL tracked cc_tasks files changed:"; echo "$moved"; fail=1; fi

# 5. The generator reports no drift.
if ! /opt/anaconda3/bin/python3 scripts/build_scan_catalog.py --check; then
  echo "FAIL scripts/build_scan_catalog.py --check reports drift"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
