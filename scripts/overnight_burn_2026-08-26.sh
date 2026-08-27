#!/bin/bash
# Overnight burn 2026-08-26 — detached driver launch (task cc_tasks/2026-08-26_overnight_burn.md).
# Pattern: scripts/jobs/airkg_extraction_burn.sh (env + DD-007 hygiene), detached via nohup
# so the driver outlives the CC session. Usage: overnight_burn_2026-08-26.sh <CEILING_TOKENS>
set -u
export PATH="/opt/anaconda3/bin:$HOME/.bun/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$REPO/logs"; mkdir -p "$LOG_DIR"
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN     # DD-007: subscription OAuth only
if [ $# -lt 1 ]; then echo "usage: $0 <CEILING_TOKENS>" >&2; exit 2; fi
export OVERNIGHT_CEILING="$1"
cd "$REPO"
nohup /opt/anaconda3/bin/python3 scripts/overnight_burn.py \
  >> "$LOG_DIR/overnight_burn_2026-08-26.log" 2>&1 &
echo "driver pid $! — log $LOG_DIR/overnight_burn_2026-08-26.log"
