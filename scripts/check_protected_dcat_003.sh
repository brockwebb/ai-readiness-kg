#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The ship set of `cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting.md`, asserted
# against HEAD.
#
# The task READS both graphs and writes a report: everything it makes is under
# `reports/dcat_us_3_faq/`, plus the three scripts that make it, their test, this check, the
# shared spend ledger its model calls reserved against, and its RESULT. No corpus, event shard,
# framework record, scan payload, rule or existing `cc_tasks/` file may move.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

allowed() {
  case "$1" in
    reports/dcat_us_3_faq/*) return 0 ;;
    scripts/dcat_faq_evidence.py|scripts/dcat_faq_run.py|scripts/dcat_faq_build.py) return 0 ;;
    scripts/check_protected_dcat_003.sh|tests/test_dcat_faq.py) return 0 ;;
    state/spend_ledger.jsonl) return 0 ;;
    cc_tasks/2026-10-05_DCAT-003_dcat_us_3_faq_for_omb_meeting_RESULT.md) return 0 ;;
  esac
  return 1
}

while IFS= read -r path; do
  [ -z "$path" ] && continue
  allowed "$path" || { echo "FAIL path outside the ship set moved: $path"; fail=1; }
done < <(changed_and_new .)

# The spend ledger and the Seldon store are append-only.
for f in state/spend_ledger.jsonl seldon_events.jsonl; do
  removed=$(git diff HEAD -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done

# The run's checkpoint is append-only too: nothing it records is rewritten after the fact.
ck=reports/dcat_us_3_faq/run/checkpoint.jsonl
if git cat-file -e "HEAD:$ck" 2>/dev/null; then
  removed=$(git diff HEAD -- "$ck" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $ck lost or changed $removed line(s)"; fail=1; fi
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
