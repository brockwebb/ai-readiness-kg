#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The protected paths of `cc_tasks/2026-10-06_scoring_frontier_parent_host_counts.md`, asserted
# against the commit the task started from (`BASE`, default `faffa362`, HEAD when the dispatcher
# launched it), so the check means the same thing before the task's commits and after them.
#
# The task's own byte-identical list: "every rule and collector, `targets.yaml`". To that, the
# standing ones: `params.yaml` unchanged (a moved byte re-identifies every Finding, DD-067 §4);
# no stored payload, no matrix of any cycle but the cycle of record's, and no prior task file or
# RESULT moves; every event shard and the Seldon store only GROW.
set -u
cd "$(dirname "$0")/.." || exit 2
BASE="${1:-faffa362}"
fail=0

# 1. Rules, collectors, the runner that dispatches them, the cycle-1 roster and the params.
for p in assessment/harness/scan/rules/ assessment/harness/scan/collectors/ \
         assessment/harness/scan/runner.py assessment/harness/scan/targets.yaml \
         assessment/harness/scan/params.yaml; do
  if ! git diff --quiet "$BASE" -- "$p"; then echo "FAIL changed: $p"; fail=1; fi
done

# 2. No stored payload, no matrix but the cycle of record's, no prior task file or RESULT.
SNAP=$(/opt/anaconda3/bin/python3 -c "import yaml; print(yaml.safe_load(open('docs/reports/publication.yaml'))['snapshot_cycle'].replace('scan_', ''))")
while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in docs/reports/scan_matrix_*_"$SNAP".*) continue ;; esac
  if ! git diff --quiet "$BASE" -- "$f"; then echo "FAIL a prior record changed: $f"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- state/ docs/reports/ cc_tasks/ \
           | grep -E '^state/scan_[^/]*\.json$|^docs/reports/scan_matrix_|^cc_tasks/[^/]*\.md$')

# 3. The kept report snapshots are never rewritten.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet "$BASE" -- "$f"; then echo "FAIL a kept snapshot changed: $f"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- docs/reports/snapshots/)

# 4. Every event shard BASE holds only grows, and the Seldon store is append-only.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  removed=$(git diff "$BASE" -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- events/ seldon_events.jsonl \
           | grep -E '^events/[^/]*\.jsonl$|^seldon_events\.jsonl$')

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
