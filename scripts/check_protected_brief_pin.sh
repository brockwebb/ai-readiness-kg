#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-10_brief_pack_cites_seldon_at_a_pinned_commit.md`, asserted
# against HEAD. The task: "No verdict, record, score or framework cell may change"; one generator
# change and one regeneration. So the regeneration may move only the two pages that cite Seldon,
# and the scratch branch the Seldon-shift check made must be gone.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
TASK_STEM=2026-10-10_brief_pack_cites_seldon_at_a_pinned_commit
SELDON=/Users/brock/GitHub/seldon

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Every path that moved is on the write set.
while read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    scripts/build_brief_pack.py|tests/test_brief_pack.py|docs/brief/E_architecture.md|\
    docs/brief/INDEX.md|scripts/check_protected_brief_pin.sh|seldon_events.jsonl|\
    "cc_tasks/${TASK_STEM}_RESULT.md") ;;
    *) echo "FAIL moved outside the write set: $f"; fail=1 ;;
  esac
done <<< "$(changed_and_new .)"

# 2. A prior task file or RESULT is immutable.
if git diff --name-only HEAD -- cc_tasks/ | grep -v "^cc_tasks/${TASK_STEM}_RESULT.md$" | grep -q .; then
  echo "FAIL a tracked cc_tasks file changed:"; git diff --name-only HEAD -- cc_tasks/; fail=1
fi

# 3. The pack on disk is what the generator renders.
if ! $PY scripts/build_brief_pack.py --check; then
  echo "FAIL docs/brief/ is not what scripts/build_brief_pack.py renders"; fail=1
fi

# 4. The Seldon-shift check left nothing behind in the Seldon checkout.
if command git -C "$SELDON" branch --list 'scratch/*' | grep -q .; then
  echo "FAIL a scratch branch is left in $SELDON:"; command git -C "$SELDON" branch --list 'scratch/*'; fail=1
fi

# 5. Logs are append-only.
if git diff HEAD -- seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost or changed a line; the log is append-only"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
