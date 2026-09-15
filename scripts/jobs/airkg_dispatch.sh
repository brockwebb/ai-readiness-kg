#!/bin/bash
# airkg-dispatch — launchd wrapper for `seldon dispatch once`.
# Task: cc_tasks/2026-09-15_standing_dispatcher.md §2, decision 7.
# Design: docs/design/2026-09-15_DN-006_standing_dispatcher.md.
#
# Fires every 300 s. The pass no-ops cleanly and exits 0 on every ordinary outcome —
# disabled, STOP file present, lease held, nothing eligible — the same contract the burn's
# cap exhaustion has, so launchd never learns to treat a healthy pass as a failure.
#
# Log caps are `controls.yaml jobs.biblio_resume`'s, BY REFERENCE (decision 7): one set of
# retention rules for every job in this repo, read from the file rather than copied, so
# moving them moves them everywhere.
set -u
# The anaconda python carries seldon and neo4j; the claude CLI lives in ~/.bun/bin and is what
# a dispatched session is launched with.
export PATH="/opt/anaconda3/bin:$HOME/.bun/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$REPO/logs"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/airkg_dispatch.log"

# DD-007: subscription OAuth only. The dispatcher refuses a pass when either variable is set,
# and this unsets them so an inherited one from the launchd environment is not that refusal
# every five minutes.
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN

# The plist's StartInterval and seldon.yaml's poll_interval_s are one parameter written twice;
# refuse rather than let them drift, because the file that EXPLAINS the value is seldon.yaml
# and the file that ACTS on it is the plist.
PLIST="$REPO/scripts/jobs/com.brock.airkg-dispatch.plist"
declared=$(/opt/anaconda3/bin/python3 -c "
import sys, yaml
print(yaml.safe_load(open('$REPO/seldon.yaml'))['dispatch']['poll_interval_s'])" 2>/dev/null)
in_plist=$(/usr/bin/awk '/<key>StartInterval<\/key>/{getline; gsub(/[^0-9]/,""); print; exit}' \
  "$PLIST" 2>/dev/null)
if [ -n "$declared" ] && [ -n "$in_plist" ] && [ "$declared" != "$in_plist" ]; then
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) | REFUSING: poll_interval_s=$declared but the" \
       "plist StartInterval=$in_plist; change both or neither" >> "$LOG"
  exit 2
fi

# Retention, from controls.yaml rather than typed here.
caps=$(/opt/anaconda3/bin/python3 -c "
import yaml
j = yaml.safe_load(open('$REPO/controls.yaml'))['jobs']['biblio_resume']
print(j['log_max_line_chars'], j['log_max_run_bytes'], j['log_retention_days'])" 2>/dev/null)
read -r MAX_LINE MAX_RUN RETAIN_DAYS <<< "${caps:-2000 2097152 30}"

# Rotate before the run, so a single pass can never be truncated mid-write.
if [ -f "$LOG" ] && [ "$(/usr/bin/stat -f%z "$LOG")" -gt "$MAX_RUN" ]; then
  mv "$LOG" "$LOG.$(date -u +%Y%m%dT%H%M%SZ)"
fi
/usr/bin/find "$LOG_DIR" -name 'airkg_dispatch.log.*' -mtime "+$RETAIN_DAYS" -delete 2>/dev/null

{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) | airkg-dispatch fire"
  cd "$REPO" && /opt/anaconda3/bin/seldon dispatch once 2>&1 | /usr/bin/cut -c "1-$MAX_LINE"
  rc=${PIPESTATUS[0]}
  echo "=== rc=$rc"
  exit $rc
} >> "$LOG" 2>&1
