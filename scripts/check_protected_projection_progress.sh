#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# Write-set guard for cc_tasks/2026-09-21_projection_progress.md. Compared against BASE = the
# commit the dispatched session started from (06393d7, the dispatcher's launch record).
set -u
cd "$(dirname "$0")/.." || exit 2
BASE=${BASE:-06393d7}
fail=0
touched=$({ git diff --name-only "$BASE"; git ls-files --others --exclude-standard; } | sed '/^$/d' | sort -u)

# Byte-identical outright: the record, the state directory, the event log.
for p in framework/ state/ events/; do
  moved=$(echo "$touched" | grep -E "^${p}" || true)
  [ -n "$moved" ] && { echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1; }
done

ALLOWED='^(scripts/build_projection\.py|controls\.yaml|tests/test_build_projection_progress\.py|scripts/check_protected_projection_progress\.sh|cc_tasks/2026-09-21_projection_progress_RESULT\.md|seldon_events\.jsonl|logs/)$|^logs/'
while IFS= read -r path; do
  [ -z "$path" ] && continue
  echo "$path" | grep -Eq "$ALLOWED" || { echo "FAIL not in the write set: $path"; fail=1; }
done <<< "$touched"

# controls.yaml: one key added, nothing else moved.
removed=$(git diff "$BASE" -- controls.yaml | grep -E '^-[^-]' || true)
[ -n "$removed" ] && { echo "FAIL controls.yaml lost lines:"; echo "$removed"; fail=1; }
added_keys=$(git diff "$BASE" -- controls.yaml | grep -E '^\+[^+#]' | grep -vE '^\+\s*#' || true)
[ "$(echo "$added_keys" | sed '/^$/d' | wc -l | tr -d ' ')" = 1 ] \
  || { echo "FAIL controls.yaml must add exactly one key:"; echo "$added_keys"; fail=1; }
[ "$fail" = 0 ] && echo "PROTECTED PATHS OK"
exit "$fail"
