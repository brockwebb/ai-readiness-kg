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
# The log path comes from the environment when one is given, so a test can run this wrapper
# without writing into the live log beside real passes (cc_tasks/2026-09-17_dispatcher_notifies.md
# decision 4: a fixture's REFUSING line landed in it at 2026-09-17T02:04:06Z). launchd sets no
# such variable, so the job writes where it always has.
LOG="${AIRKG_DISPATCH_LOG:-$REPO/logs/airkg_dispatch.log}"
LOG_DIR="$(dirname "$LOG")"
mkdir -p "$LOG_DIR"

# DD-007: subscription OAuth only. The dispatcher refuses a pass when either variable is set,
# and this unsets them so an inherited one from the launchd environment is not that refusal
# every five minutes.
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN

# NEO4J CREDENTIALS. **A launchd job inherits almost no environment** — not the login shell's,
# not the terminal's — so the variables a hand-run `seldon dispatch` picks up are simply absent
# here. The first scheduled pass proved it: it fired on time and died on
# `neo4j.exceptions.AuthError`, having changed nothing.
#
# The fallback is this repo's existing one (CLAUDE.md: "fallback: ~/.wintermute/.env", and the
# parse is `scripts/build_projection.py::_neo4j_creds`), reused rather than reinvented. Only
# NEO4J_* names are read and **no value is ever echoed** — the log this writes is a file on
# disk and a password in it would be a credential at rest in a path nobody thinks of as one.
WM_ENV="$HOME/.wintermute/.env"
if [ -z "${NEO4J_USERNAME:-}${NEO4J_USER:-}" ] && [ -f "$WM_ENV" ]; then
  while IFS= read -r line; do
    case "$line" in
      NEO4J_*=*)
        v="${line#*=}"
        # Strip ONE surrounding quote pair, which is what `.strip('"').strip("'")` does in
        # `scripts/build_projection.py`. Deleting every quote character in the value instead
        # is wrong and silently so: this password contains one, and a pass authenticated with
        # a password one character short fails with `AuthError` — indistinguishable from a
        # wrong password and from no password at all.
        v="${v%\"}"; v="${v#\"}"
        v="${v%\'}"; v="${v#\'}"
        export "${line%%=*}"="$v"
        ;;
    esac
  done < "$WM_ENV"
  unset v
fi
if [ -z "${NEO4J_USERNAME:-}${NEO4J_USER:-}" ] || [ -z "${NEO4J_PASSWORD:-}${NEO4J_PASS:-}" ]; then
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) | REFUSING: no Neo4j credentials in the launchd" \
       "environment or $WM_ENV; a pass cannot read the queue" >> "$LOG"
  exit 3
fi

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
/usr/bin/find "$LOG_DIR" -name "$(basename "$LOG").*" -mtime "+$RETAIN_DAYS" -delete 2>/dev/null

{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) | airkg-dispatch fire"
  cd "$REPO" && /opt/anaconda3/bin/seldon dispatch once 2>&1 | /usr/bin/cut -c "1-$MAX_LINE"
  rc=${PIPESTATUS[0]}
  echo "=== rc=$rc"
  exit $rc
} >> "$LOG" 2>&1
