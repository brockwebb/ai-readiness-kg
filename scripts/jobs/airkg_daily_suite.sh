#!/bin/bash
# airkg-daily-suite — the whole suite, once a day, on `main`, from its own git worktree.
# Task: cc_tasks/2026-10-07_parallel_hosts_and_fast_gate.md decision 6 (DN-013-R4).
#
# WHY A WORKTREE. A gate must not run in a tree another process commits to: the recollection's
# first full-suite run died at 35% with no EXIT line at 2026-10-07T02:17:51Z, when a Desktop
# session committed in the same checkout (DN-013 ADDENDUM 01 A2). This job never runs a test in
# the working checkout. It keeps one detached worktree outside it, moves it to `main`'s commit,
# and runs `make suite` there.
#
# WHY IT SEEDS DATA. The suite reads gitignored inputs (corpus binaries, `state/substrate_md`,
# `state/docling_md`, the corpus index …) that a fresh worktree does not have, so a bare
# worktree goes red for want of data, not code. Every path `git` reports as ignored is copied
# in (`rsync`, so only what changed moves), less the ones that are logs, caches, session state
# or credentials (SEED_EXCLUDE below). A COPY and not a symlink: a test in the worktree that
# wrote through a link would be writing into the working checkout, which is the thing this job
# exists not to do.
#
# RED. The run's log path, `main`'s commit and the time go into the dispatcher's STOP file
# (`seldon.yaml dispatch.stop_file`, `.seldon/DISPATCH_STOP`), so nothing is dispatched onto a
# red main, and a Seldon Issue is opened naming the log. A STOP file someone else wrote is never
# overwritten: this job appends its lines to it.
# GREEN. A STOP file THIS job wrote (its first line is `STOP_MARK`) is removed and the removal is
# logged: main is green again and the reason for the stop is gone. A STOP file anyone else wrote
# is left exactly as it is.
#
# Exits 0 on a green suite and on a red one alike once the STOP and the Issue are written: a red
# suite is a finding about main, not a failure of this job. Non-zero only when the job itself
# could not do its work (no main, no worktree, no seed), so launchd's record means "the job
# broke" and nothing else.
set -u
export PATH="/opt/anaconda3/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
PY=/opt/anaconda3/bin/python3
# Overridable from the environment so a test can run this wrapper against a scratch repository
# (the dispatch wrapper's AIRKG_DISPATCH_LOG precedent). launchd sets none of them.
WT="${AIRKG_DAILY_WORKTREE:-$HOME/.cache/airkg/daily_suite_worktree}"
LOG_DIR="${AIRKG_DAILY_LOG_DIR:-$REPO/logs/daily_suite}"
BRANCH="${AIRKG_DAILY_BRANCH:-main}"
SUITE_TARGET="${AIRKG_DAILY_TARGET:-suite}"
SELDON="${AIRKG_SELDON:-/opt/anaconda3/bin/seldon}"
STOP_MARK="airkg-daily-suite: main is red"
mkdir -p "$LOG_DIR"
STAMP="$(date -u +%Y-%m-%dT%H%M%SZ)"
LOG="$LOG_DIR/$STAMP.log"
JOBLOG="$LOG_DIR/job.log"

say() { echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) | $*" >> "$JOBLOG"; }

# Ignored paths that are not inputs: logs, caches, session state, credentials, editor and OS
# litter. Everything else git ignores is data the suite may read.
SEED_EXCLUDE='^(logs/|\.seldon/|\.claude/|handoffs/|tmp/|\.venv/|venv/|env/|ENV/|\.env$|\.worktrees/|.*__pycache__/|\.pytest_cache/|\.mypy_cache/|\.ruff_cache/|\.hypothesis/|htmlcov/|build/|dist/|.*\.egg-info/|.*\.log$|.*\.DS_Store$|\.vscode/|\.idea/|.*\.sw[po]$|state/evidence_staging/)'

# Neo4j credentials, the dispatch wrapper's fallback and parse, so the suite's graph tests run
# rather than skip (a launchd job inherits almost no environment). No value is ever echoed.
WM_ENV="$HOME/.wintermute/.env"
if [ -z "${NEO4J_USERNAME:-}${NEO4J_USER:-}" ] && [ -f "$WM_ENV" ]; then
  while IFS= read -r line; do
    case "$line" in
      NEO4J_*=*)
        v="${line#*=}"
        v="${v%\"}"; v="${v#\"}"
        v="${v%\'}"; v="${v#\'}"
        export "${line%%=*}"="$v"
        ;;
    esac
  done < "$WM_ENV"
  unset v
fi
# DD-007: the suite makes no model call, and no inherited key may make one possible.
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN

# Retention, from controls.yaml by reference (the dispatch wrapper's rule, decision 7 there).
caps=$("$PY" -c "
import yaml
j = yaml.safe_load(open('$REPO/controls.yaml'))['jobs']['biblio_resume']
print(j['log_retention_days'])" 2>/dev/null)
RETAIN_DAYS="${caps:-30}"
/usr/bin/find "$LOG_DIR" -name '*.log' ! -name 'job.log' -mtime "+$RETAIN_DAYS" -delete 2>/dev/null

SHA="$(git -C "$REPO" rev-parse --verify --quiet "$BRANCH^{commit}")" \
  || { say "FAILED: no commit for $BRANCH in $REPO"; exit 2; }

# The worktree: created once, then moved to main's commit and cleaned of anything untracked
# that is not ignored (a test's leftover), keeping the seeded data.
if [ ! -e "$WT/.git" ]; then
  mkdir -p "$(dirname "$WT")"
  git -C "$REPO" worktree prune
  git -C "$REPO" worktree add --detach "$WT" "$SHA" >> "$JOBLOG" 2>&1 \
    || { say "FAILED: git worktree add $WT $SHA"; exit 2; }
else
  git -C "$WT" checkout --detach --force "$SHA" >> "$JOBLOG" 2>&1 \
    || { say "FAILED: checkout $SHA in $WT"; exit 2; }
  git -C "$WT" clean -fd >> "$JOBLOG" 2>&1
fi

# Seed the ignored inputs from the checkout. `-a --delete` per path, so a file removed from the
# checkout's data is removed from the copy too, and the copy is the checkout's data, exactly.
seeded=0
while IFS= read -r rel; do
  [ -z "$rel" ] && continue
  printf '%s\n' "$rel" | grep -Eq "$SEED_EXCLUDE" && continue
  src="$REPO/$rel"; dst="$WT/$rel"
  mkdir -p "$(dirname "$dst")"
  if [ -d "$src" ]; then
    /usr/bin/rsync -a --delete "$src/" "$dst/" || { say "FAILED: seed $rel"; exit 2; }
  else
    /usr/bin/rsync -a "$src" "$dst" || { say "FAILED: seed $rel"; exit 2; }
  fi
  seeded=$((seeded + 1))
done < <(git -C "$REPO" ls-files --others --ignored --exclude-standard --directory)

say "start $BRANCH@${SHA:0:12} in $WT ($seeded ignored path(s) seeded) -> $LOG"
( cd "$WT" && make --no-print-directory "$SUITE_TARGET" PY="$PY"; echo "EXIT=$?" ) > "$LOG" 2>&1
rc="$(sed -n 's/^EXIT=//p' "$LOG" | tail -1)"
summary="$(grep -E '^[0-9]+ (passed|failed)|^=+ .*(passed|failed|error)' "$LOG" | tail -1)"
say "finished $BRANCH@${SHA:0:12} EXIT=${rc:-none} ${summary}"

STOP_REL="$("$PY" -c "
import yaml
print(yaml.safe_load(open('$REPO/seldon.yaml'))['dispatch']['stop_file'])" 2>/dev/null)"
STOP="$REPO/${STOP_REL:-.seldon/DISPATCH_STOP}"

if [ "${rc:-}" = "0" ]; then
  if [ -f "$STOP" ] && [ "$(head -1 "$STOP")" = "$STOP_MARK" ]; then
    rm -f "$STOP"
    say "main is green again; removed the STOP file this job wrote ($STOP)"
  fi
  exit 0
fi

# Red, or no EXIT line at all (the run died): either way main is not known green. Whether the
# file exists is decided BEFORE anything is written to it, because `>>` creates it.
mkdir -p "$(dirname "$STOP")"
if [ ! -f "$STOP" ]; then
  echo "$STOP_MARK" > "$STOP"
fi
echo "$STAMP $BRANCH@$SHA EXIT=${rc:-none} log=$LOG" >> "$STOP"
say "main is RED; wrote $STOP"
( cd "$REPO" && "$SELDON" issue create \
    --description "Daily full suite on $BRANCH@${SHA:0:12} is red (EXIT=${rc:-none}, ${summary:-no summary line}). Log: $LOG. Dispatch is stopped by $STOP until main is green." \
    --type merge_blocked --importance high --urgency high --detection build_failure \
    --target structure ) >> "$JOBLOG" 2>&1 \
  || say "WARNING: seldon issue create failed; the STOP file stands and names the log"
exit 0
