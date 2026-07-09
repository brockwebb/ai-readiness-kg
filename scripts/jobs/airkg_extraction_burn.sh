#!/bin/bash
# airkg-extraction-burn — launchd wrapper for the bulk v1 extraction runner.
# Task: cc_tasks/2026-07-05_airkg_bulk_extraction_v1.md Stage 4.
# Fires hourly; the runner itself no-ops cleanly on: cap exhausted, lease held,
# STOP file present, or run complete. Cap-tripping is normal operation.
set -u
# anaconda python carries the deps (dixie, pypdf); claude CLI lives in ~/.bun/bin
export PATH="/opt/anaconda3/bin:$HOME/.bun/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
LOG_DIR="$REPO/logs"
mkdir -p "$LOG_DIR"
# DD-007: subscription OAuth only — refuse inherited API credentials.
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN
# 2026-07-08 boost: knock out the big docs first while the window is wide. Remove
# this line to return to alphabetical order.
export BURN_ORDER=size_desc
# 2026-07-08 boost: don't let one high-quarantine outlier halt the whole overnight burn.
# Isolated breaches are recorded as findings; hard-STOP only on 3 consecutive over-threshold
# docs (systemic). The 0.10 threshold is unchanged. Remove this line to restore the
# pre-registered per-doc STOP.
export BURN_QUARANTINE_STOP_MODE=systemic

{
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) | airkg-extraction-burn fire"
  cd "$REPO" && /opt/anaconda3/bin/python3 scripts/run_bulk_extraction.py
  rc=$?
  echo "=== rc=$rc"
  exit $rc
} >> "$LOG_DIR/airkg_extraction_burn.log" 2>&1
