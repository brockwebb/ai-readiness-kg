#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The ship set of `cc_tasks/2026-10-04_views_regenerate_v2.md` as it STOPPED, asserted against HEAD.
#
# The task stopped before commit under its decision 4 ("Any other change stops the task before
# commit"): regeneration also moved `docs/brief/E_architecture.md:74`. Nothing in its write set
# ships, so the only paths that may move are the RESULT and this file. The regenerated state is
# kept, unapplied, at `logs/views_regenerate_v2_regenerated.patch`.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

ALLOWED=(
  'cc_tasks/2026-10-04_views_regenerate_v2_RESULT.md'
  'scripts/check_protected_views_regenerate_v2.sh'
)
while IFS= read -r path; do
  [ -z "$path" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$path" = "$a" ] && ok=1 && break; done
  if [ "$ok" -eq 0 ]; then echo "FAIL path outside the ship set moved: $path"; fail=1; fi
done < <(changed_and_new .)

# The store is append-only.
removed=$(git diff HEAD -- seldon_events.jsonl | grep -c '^-[^-]' || true)
if [ "$removed" -ne 0 ]; then echo "FAIL seldon_events.jsonl lost or changed $removed line(s)"; fail=1; fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
