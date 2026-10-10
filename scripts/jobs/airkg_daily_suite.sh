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
# GREEN. This job's own lines are removed from the STOP file — `STOP_MARK` and its one-per-red-run
# record lines — and nothing else; the file is deleted only when nothing else is left in it. A
# line someone else wrote stays, and with it the stop, until whoever wrote it removes it
# (cc_tasks/2026-10-09_main_green_dispatch_stuck_without_a_path.md decision 7: the 2026-10-07
# file began with an operator budget line and carried three red-run lines after it; the old rule,
# "delete the file if its first line is STOP_MARK", would have left all four lines there forever,
# and on a file that began with STOP_MARK it would have deleted an operator line appended later).
#
# ISSUES (decision 6 there). `daily_suite_issues.py` beside this: a red run opens a NAMED Issue per
# failing test set, or records the run on the open one of that name; a green run resolves every
# open Issue this job opened, with the green log's path.
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
  git -C "$REPO" worktree add --quiet --detach "$WT" "$SHA" >> "$JOBLOG" 2>&1 \
    || { say "FAILED: git worktree add $WT $SHA"; exit 2; }
else
  git -C "$WT" checkout --quiet --detach --force "$SHA" >> "$JOBLOG" 2>&1 \
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

# Sibling checkouts the suite reaches by RELATIVE path, linked beside the worktree so `../<name>`
# resolves from it as it does from the checkout. One today: `tests/test_dispatch_config.py`
# reads `REPO/../seldon`, and without the link the first installed run skipped two tests the
# checkout runs (2026-10-07T20:36Z). A link and not a copy: it is another repository, read-only
# to the suite, and a copy of it would be a second Seldon to keep current.
SIBLINGS="seldon"
for name in $SIBLINGS; do
  if [ -d "$(dirname "$REPO")/$name" ] && [ ! -e "$(dirname "$WT")/$name" ]; then
    ln -s "$(dirname "$REPO")/$name" "$(dirname "$WT")/$name"
  fi
done

say "start $BRANCH@${SHA:0:12} in $WT ($seeded ignored path(s) seeded) -> $LOG"
( cd "$WT" && make --no-print-directory "$SUITE_TARGET" PY="$PY"; echo "EXIT=$?" ) > "$LOG" 2>&1
rc="$(sed -n 's/^EXIT=//p' "$LOG" | tail -1)"
summary="$(grep -E '^[0-9]+ (passed|failed)|^=+ .*(passed|failed|error)' "$LOG" | tail -1)"
say "finished $BRANCH@${SHA:0:12} EXIT=${rc:-none} ${summary}"

STOP_REL="$("$PY" -c "
import yaml
print(yaml.safe_load(open('$REPO/seldon.yaml'))['dispatch']['stop_file'])" 2>/dev/null)"
STOP="$REPO/${STOP_REL:-.seldon/DISPATCH_STOP}"

ISSUES=("$PY" "$REPO/scripts/jobs/daily_suite_issues.py")
ISSUE_ARGS=(--seldon "$SELDON" --repo "$REPO" --log "$LOG" --sha "$SHA" --stamp "$STAMP"
            --branch "$BRANCH")
# The record line a red run appends, as a pattern: `<STAMP> <branch>@<40-hex sha> EXIT=<rc> log=…`.
OWN_LINE='^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{6}Z [^ ]+@[0-9a-f]{40} EXIT=[^ ]+ log=.+$'

if [ "${rc:-}" = "0" ]; then
  if [ -f "$STOP" ]; then
    kept="$(grep -Fvx -- "$STOP_MARK" "$STOP" | grep -Ev -- "$OWN_LINE")"
    if [ -z "$(printf '%s' "$kept" | tr -d '[:space:]')" ]; then
      rm -f "$STOP"
      say "main is green again; removed the STOP file, every line of which this job wrote ($STOP)"
    elif [ "$kept" != "$(cat "$STOP")" ]; then
      printf '%s\n' "$kept" > "$STOP"
      say "main is green again; removed this job's lines from $STOP and left $(printf '%s\n' "$kept" | wc -l | tr -d ' ') line(s) someone else wrote: dispatch stays stopped until they are removed"
    else
      say "main is green; $STOP holds no line this job wrote and is left as it is"
    fi
  fi
  ( cd "$REPO" && "${ISSUES[@]}" green "${ISSUE_ARGS[@]}" ) >> "$JOBLOG" 2>&1 \
    || say "WARNING: closing this job's Issues failed; see the lines above"
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
( cd "$REPO" && "${ISSUES[@]}" red "${ISSUE_ARGS[@]}" --rc "${rc:-}" --summary "$summary" \
    --stop "$STOP" ) >> "$JOBLOG" 2>&1 \
  || say "WARNING: recording the red run as an Issue failed; the STOP file stands and names the log"
exit 0
