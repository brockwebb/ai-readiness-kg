#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The protected paths of `cc_tasks/2026-10-06_absence_verdicts_rules.md`, asserted against the
# commit the task started from (`BASE`, default `0b86e070`, HEAD when the dispatcher launched it),
# so the check means the same thing before the task's commits and after them.
#
# The task's own byte-identical list: "every prior rule version, `params.yaml` values,
# `score.py`". To that, the standing ones every re-judgement keeps: no stored payload, no prior
# matrix, no prior task file or RESULT moves; every event shard and the Seldon store only GROW.
# The write set itself is wide by decision 6 (every view regenerates from the new snapshot), so
# this asserts what may NOT move rather than listing everything that may.
set -u
cd "$(dirname "$0")/.." || exit 2
BASE="${1:-0b86e070}"
fail=0

# 1. Every rule module shipped at BASE is byte-identical. Generation 14 is new files only.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet "$BASE" -- "$f"; then echo "FAIL shipped rule module changed: $f"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- assessment/harness/scan/rules/ | grep '/rule_[^/]*\.py$')

# 2. `params.yaml`: every value at BASE is still there, unchanged. New keys are allowed.
if ! BASE="$BASE" /opt/anaconda3/bin/python3 - <<'PY'
import os, subprocess, sys, yaml
old = yaml.safe_load(subprocess.run(["git", "show", f"{os.environ['BASE']}:assessment/harness/scan/params.yaml"],
                                    capture_output=True, text=True, check=True).stdout)
new = yaml.safe_load(open("assessment/harness/scan/params.yaml", encoding="utf-8"))
bad = []
def walk(a, b, path):
    if isinstance(a, dict):
        if not isinstance(b, dict):
            bad.append(path); return
        for k, v in a.items():
            if k not in b:
                bad.append(f"{path}.{k} (removed)")
            else:
                walk(v, b[k], f"{path}.{k}")
    elif a != b:
        bad.append(path)
walk(old, new, "params")
for b in bad:
    print(f"FAIL params.yaml value moved: {b}")
sys.exit(1 if bad else 0)
PY
then fail=1; fi

# 3. `score.py` is the scoring task's (`2026-10-06_scoring_frontier_parent_host_counts.md`).
if ! git diff --quiet "$BASE" -- scripts/score.py; then echo "FAIL scripts/score.py changed"; fail=1; fi

# 4. No stored payload, matrix, task file or RESULT that BASE holds moved.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet "$BASE" -- "$f"; then echo "FAIL a prior record changed: $f"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- state/ docs/reports/ cc_tasks/ \
           | grep -E '^state/scan_[^/]*\.json$|^docs/reports/scan_matrix_|^cc_tasks/[^/]*\.md$')

# 5. Every event shard BASE holds only grows, and the Seldon store is append-only.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  removed=$(git diff "$BASE" -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- events/ seldon_events.jsonl \
           | grep -E '^events/[^/]*\.jsonl$|^seldon_events\.jsonl$')

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
