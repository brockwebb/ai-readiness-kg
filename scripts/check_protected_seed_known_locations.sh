#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The protected paths of `cc_tasks/2026-10-07_seed_known_locations_and_split_discoverability.md`
# (no addendum), asserted against the commit the dispatched session started from (`BASE`,
# default `ce656639`), so the check means the same thing before the task's commits and after.
#
# The task's byte-identical list: "`collectors/`, `manners.py`, `run.py`'s collection path,
# `scripts/score.py`, `targets.yaml`, every stored payload other than the new ones, every task
# file". `run.py`'s collection path is held as `run.py` and `runner.py` whole. Decision 1 adds:
# "Every predecessor stays in `REGISTRY`, unedited", so every `rule_*.py` module BASE holds is
# byte-identical too. The two shared rule helpers that changed are named, not exempted: `_scope.py`
# reads declarations scheme 2 beside scheme 1 (decision 5). `params.yaml` may gain only the
# `existence` and `discoverability` blocks and move only `link_probe.legs_served` (A13, decision
# 3); every value at BASE is otherwise unchanged. To that, the standing ones: every event shard
# and the Seldon store only GROW.
set -u
cd "$(dirname "$0")/.." || exit 2
BASE="${1:-ce656639}"
fail=0

# 1. Collectors, manners, the collection path, score.py, targets.yaml: byte-identical.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet "$BASE" -- "$f"; then echo "FAIL protected file changed: $f"; fail=1; fi
done < <( { command git ls-tree -r --name-only "$BASE" -- assessment/harness/scan/collectors/ \
              | grep '\.py$'
            printf '%s\n' assessment/harness/scan/manners.py assessment/harness/scan/run.py \
              assessment/harness/scan/runner.py scripts/score.py \
              assessment/harness/scan/targets.yaml; } )
added=$(git diff --name-only --diff-filter=A "$BASE" -- assessment/harness/scan/collectors/ \
          | grep -c '\.py$' || true)
if [ "$added" -ne 0 ]; then echo "FAIL $added collector module(s) added"; fail=1; fi

# 2. Every rule module BASE holds is byte-identical (predecessors unedited); only the two named
#    helpers and the registry may change.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet "$BASE" -- "$f"; then echo "FAIL a shipped rule module changed: $f"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- assessment/harness/scan/rules/ \
           | grep -E '/rule_[^/]*\.py$|/_(common|dcat_fields|schema_terms)\.py$')
for f in $(git diff --name-only "$BASE" -- assessment/harness/scan/rules/ | grep '\.py$'); do
  case "$f" in
    */rules/__init__.py|*/rules/_scope.py) echo "note: named change $f" ;;
    *) if git cat-file -e "$BASE:$f" 2>/dev/null; then echo "FAIL unexpected rule change: $f"; fail=1; fi ;;
  esac
done

# 3. `params.yaml`: every value at BASE unchanged but `link_probe.legs_served`; the only new keys
#    are the `existence` and `discoverability` blocks.
if ! BASE="$BASE" /opt/anaconda3/bin/python3 - <<'PY'
import os, subprocess, sys, yaml
old = yaml.safe_load(subprocess.run(["git", "show", f"{os.environ['BASE']}:assessment/harness/scan/params.yaml"],
                                    capture_output=True, text=True, check=True).stdout)
new = yaml.safe_load(open("assessment/harness/scan/params.yaml", encoding="utf-8"))
ALLOWED_MOVED = {"params.link_probe.legs_served"}
ALLOWED_NEW = {"params.existence", "params.discoverability"}
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
moved = old["link_probe"]["legs_served"], new["link_probe"]["legs_served"]
if moved[1] != moved[0] + ["A13"]:
    bad.append(f"params.link_probe.legs_served moved other than by adding A13: {moved}")
for b in bad:
    print(f"FAIL params.yaml: {b}")
sys.exit(1 if bad else 0)
PY
then fail=1; fi

# 4. No stored payload, matrix or task file that BASE holds moved.
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
