# Sourced, never executed: the one exclusion every `scripts/check_protected_*.sh` shares.
#
# `cc_tasks/2026-09-18_registration_commits.md` decision 3: two kinds of path are written into a
# dispatched session's checkout by actors other than the session, BY DESIGN, so they are never
# the session's protected paths:
#
#   * an untracked `cc_tasks/*.md` — a task file the Desktop authored or registered (and whose
#     registration commit failed, leaving it for the dispatcher's fallback sweep), or an
#     addendum authored beside a base task;
#   * `seldon_events.jsonl` — appended to by registration, by the dispatcher and by the
#     Desktop, and committed with the session's own write set at the end.
#
# The scoring session (`cc_tasks/2026-09-18_scoring_model_RESULT.md` §4 premise 10) went red on
# two task files registered at 03:01Z and had to prove its ship set in a clean worktree.
#
# WHAT IS NOT EXCLUDED, deliberately: a MODIFIED tracked `cc_tasks/*.md`. Task files are
# immutable once written and no other actor edits one, so "a prior RESULT or task file changed"
# stays a violation in every check that asserts it. And only NAME LISTINGS are filtered: every
# check's append-only test of the store reads `git diff HEAD -- seldon_events.jsonl` content,
# which passes through untouched.
#
# HOW: this file defines a shell function `git` that runs the real git (`command git`) and, for
# the three listing forms the checks use — `git diff --name-only`, `git ls-files --others|-o`,
# `git status --porcelain` — drops those paths from the output. Every other git invocation is
# passed straight through. It is a function rather than an edit to each check because the 35
# checks list the tree three different ways; one interposition sourced on line 2 of each keeps
# the exclusion in one place and leaves every other line of every check where it was.
#
# POSIX sh: fourteen of the checks run under `#!/bin/sh`. The real git's exit status is
# returned, so a check that tests it sees what it always saw.

_airkg_foreign_listing() {  # $1: the listing form (diff | others | porcelain)
  awk -v form="$1" '
    NF == 0 { next }
    {
      path = (form == "porcelain") ? substr($0, 4) : $0
      if (path == "seldon_events.jsonl") next
      untracked = (form == "others") || (form == "porcelain" && substr($0, 1, 2) == "??")
      if (untracked && path ~ /^cc_tasks\/[^\/]*\.md$/) next
      print
    }'
}

git() {
  _airkg_sub=""
  _airkg_form=""
  for _airkg_a in "$@"; do
    case "$_airkg_a" in
      -*) [ -n "$_airkg_sub" ] || continue ;;
      *) [ -n "$_airkg_sub" ] || { _airkg_sub="$_airkg_a"; continue; } ;;
    esac
    case "$_airkg_sub:$_airkg_a" in
      diff:--name-only) _airkg_form=diff ;;
      ls-files:--others|ls-files:-o) _airkg_form=others ;;
      status:--porcelain) _airkg_form=porcelain ;;
      *:--) break ;;
    esac
  done
  if [ -z "$_airkg_form" ]; then
    command git "$@"
    return $?
  fi
  _airkg_out=$(command git "$@")
  _airkg_rc=$?
  printf '%s\n' "$_airkg_out" | _airkg_foreign_listing "$_airkg_form"
  return "$_airkg_rc"
}
