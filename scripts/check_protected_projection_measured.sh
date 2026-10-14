#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-12_projection_replay_measured_then_batched.md`, asserted
# against the commit the task started from (default 6950b663, HEAD when it was launched), so it
# reads the same before and after the task's own commit.
#
# The task stopped at decision 1 (the measured cause is server-side scans first, per-row commits
# second; batching alone cannot reach decision 4's 10 minutes), so `scripts/build_projection.py`
# is byte-identical. What it wrote: the profiler, the canonical export (decision 3's instrument,
# kept as the next task's baseline), their tests, this script, the RESULT, and
# `controls.yaml`'s new `projection.canonical_export` block (the export's scope, config not
# code) and nothing else in it.
#
# Byte-identical: `build_projection.py`, every event file, the corpus, rules, collectors,
# `manners.py`, `score.py`, claims, views, `reports/`, `docs/evidence/FROZEN.md`, the framework
# record and every task file.
set -u
cd "$(dirname "$0")/.." || exit 2
BASE="${1:-6950b663}"
PY="${PY:-/opt/anaconda3/bin/python3}"
fail=0

changed_and_new() {
  { git diff --name-only "$BASE" -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

allowed() {
  case "$1" in
    scripts/profile_projection.py|scripts/projection_canonical_export.py) return 0 ;;
    tests/test_profile_projection.py|tests/test_projection_canonical_export.py) return 0 ;;
    scripts/check_protected_projection_measured.sh|controls.yaml) return 0 ;;
    seldon_events.jsonl) return 0 ;;
    cc_tasks/2026-10-12_projection_replay_measured_then_batched_RESULT.md) return 0 ;;
  esac
  return 1
}

# A task file ADDED since the base was committed by a registration, not by this session.
added_tasks=$(git diff --name-only --diff-filter=A "$BASE" -- 'cc_tasks/*.md')
while IFS= read -r path; do
  [ -z "$path" ] && continue
  printf '%s\n' "$added_tasks" | grep -qxF "$path" && continue
  allowed "$path" || { echo "FAIL path outside the write set moved: $path"; fail=1; }
done < <(changed_and_new .)

for p in scripts/build_projection.py assessment/harness/scan/rules \
         assessment/harness/scan/collectors assessment/harness/scan/manners.py \
         assessment/harness/scan/publish.py scripts/score.py events corpus \
         framework/ai_readiness_framework.json docs/evidence reports; do
  if [ -n "$(changed_and_new "$p")" ]; then echo "FAIL $p must be byte-identical and moved"; fail=1; fi
done

moved_tasks=$(git diff --name-only --diff-filter=MDR "$BASE" -- cc_tasks/ \
  | grep -vxF 'cc_tasks/2026-10-12_projection_replay_measured_then_batched_RESULT.md' || true)
if [ -n "$moved_tasks" ]; then echo "FAIL a task file moved: $moved_tasks"; fail=1; fi

removed=$(git diff "$BASE" -- seldon_events.jsonl | grep -c '^-[^-]' || true)
if [ "$removed" -ne 0 ]; then echo "FAIL seldon_events.jsonl lost or changed $removed line(s)"; fail=1; fi

# controls.yaml: `projection.canonical_export` added, nothing else moved.
"$PY" - "$BASE" <<'EOF' || fail=1
import subprocess, sys, yaml
base = sys.argv[1]
then = yaml.safe_load(subprocess.run(["git", "show", f"{base}:controls.yaml"],
                                     capture_output=True, text=True, check=True).stdout)
now = yaml.safe_load(open("controls.yaml", encoding="utf-8"))
bad = 0
if "canonical_export" not in (now.get("projection") or {}):
    print("FAIL controls.yaml projection.canonical_export missing"); bad = 1
now["projection"].pop("canonical_export", None)
if then != now:
    print("FAIL controls.yaml moved beyond projection.canonical_export"); bad = 1
sys.exit(bad)
EOF

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
