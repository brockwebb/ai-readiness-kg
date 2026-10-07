#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The protected paths of `cc_tasks/2026-10-06_absence_verdicts_recollection_v2.md` (and its
# ADDENDUM_01), asserted against the commit the session started from (`BASE`, default
# `b2b2c9b6`, HEAD when the operator launched it), so the check means the same thing before the
# task's commits and after them.
#
# The task's byte-identical list: "every rule, every collector, `score.py`". ADDENDUM_01
# amendment 2 ("B3 follows every methodology link on the page, not the first") is the one
# collector change the addendum orders, and it lives in `runner.collect_leg`, not in
# `collectors/`; `collectors/` itself stays byte-identical. `params.yaml` may change only in
# `cycle.name` (a new cycle is a new name, DD-041) and gain the one new key B3's bound needs.
# To that, the standing ones: no stored payload, no prior matrix, no prior task file or RESULT
# moves; every event shard and the Seldon store only GROW.
set -u
cd "$(dirname "$0")/.." || exit 2
BASE="${1:-b2b2c9b6}"
fail=0

# 1. Every rule module and every collector module shipped at BASE is byte-identical.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet "$BASE" -- "$f"; then echo "FAIL rule or collector changed: $f"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- assessment/harness/scan/rules/ \
           assessment/harness/scan/collectors/ | grep '\.py$')
# ... and no rule or collector module was added.
added=$(git diff --name-only --diff-filter=A "$BASE" -- assessment/harness/scan/rules/ \
          assessment/harness/scan/collectors/ | grep -c '\.py$' || true)
if [ "$added" -ne 0 ]; then echo "FAIL $added rule or collector module(s) added"; fail=1; fi

# 2. `params.yaml`: every value at BASE is unchanged except `cycle.name`; the only new key is
#    `b3_methodology.max_followed`.
if ! BASE="$BASE" /opt/anaconda3/bin/python3 - <<'PY'
import os, subprocess, sys, yaml
old = yaml.safe_load(subprocess.run(["git", "show", f"{os.environ['BASE']}:assessment/harness/scan/params.yaml"],
                                    capture_output=True, text=True, check=True).stdout)
new = yaml.safe_load(open("assessment/harness/scan/params.yaml", encoding="utf-8"))
ALLOWED_MOVED = {"params.cycle.name"}
ALLOWED_NEW = {"params.b3_methodology.max_followed"}
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
        for k in b:
            if k not in a and f"{path}.{k}" not in ALLOWED_NEW:
                bad.append(f"{path}.{k} (new key outside the write set)")
    elif a != b and path not in ALLOWED_MOVED:
        bad.append(path)
walk(old, new, "params")
for b in bad:
    print(f"FAIL params.yaml: {b}")
sys.exit(1 if bad else 0)
PY
then fail=1; fi

# 3. `score.py` is the scoring task's.
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

# 6. `targets.yaml` changed only under `declared_locations` (the declaration fields).
if ! BASE="$BASE" /opt/anaconda3/bin/python3 - <<'PY'
import os, subprocess, sys, yaml
old = yaml.safe_load(subprocess.run(["git", "show", f"{os.environ['BASE']}:assessment/harness/scan/targets.yaml"],
                                    capture_output=True, text=True, check=True).stdout)
new = yaml.safe_load(open("assessment/harness/scan/targets.yaml", encoding="utf-8"))
moved = sorted(k for k in set(old) | set(new) if k != "declared_locations" and old.get(k) != new.get(k))
for k in moved:
    print(f"FAIL targets.yaml moved outside declared_locations: {k}")
sys.exit(1 if moved else 0)
PY
then fail=1; fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
