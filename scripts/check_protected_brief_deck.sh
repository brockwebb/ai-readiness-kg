#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-23_brief_narrative.md`, asserted against the commit the task
# was launched on. (Earlier tasks' checks, `2026-09-22_brief_deck_assembly` against `a3756e3` and
# `2026-09-23_brief_deck_packaging` against `5ed4eac`, are in git history.)
#
#   "**Write set:** `docs/deck/brief_narrative.md` (new, verbatim from §Narrative, plus the comment
#    line), `scripts/build_brief_deck.py`, `docs/deck/brief_deck.pptx`, `tests/test_brief_deck.py`,
#    `scripts/check_protected_brief_deck.sh` (base moves to this task's launch commit), the RESULT.
#    Byte-identical: everything under `docs/brief/`, `docs/deck/brief_appendix.pptx`,
#    `docs/deck/diagrams/`, and every directory the packaging task listed."
#
# BASE is the dispatcher's `dispatch_launched` record commit for this task (`97b58374`), the last
# commit before the task wrote anything. Override with BASE=<rev> to re-run it later.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
TASK_STEM=2026-09-23_brief_narrative
BASE=${BASE:-996d8f0}

changed_and_new() {
  { git diff --name-only "$BASE" -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the task's byte-identical list, plus every other store of record.
for p in 'docs/brief/' 'docs/deck/brief_appendix.pptx' 'docs/deck/diagrams/' \
         'docs/deck/brief_deck_content.md' 'scripts/build_brief_pack.py' \
         'framework/' 'state/' 'events/' 'docs/reports/' 'docs/data/' 'docs/crosswalk/' \
         'assessment/' 'corpus/' 'mcp/' 'CITATION.cff' '.zenodo.json' 'kg/' 'controls.yaml' \
         'dixie_evidence.yaml' 'seldon.yaml' 'Makefile' 'CLAUDE.md' 'LICENSE' 'LICENSE-DATA'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. Every path that moved is on the write set.
while read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    docs/deck/brief_narrative.md|docs/deck/brief_deck.pptx|scripts/build_brief_deck.py|\
    tests/test_brief_deck.py|scripts/check_protected_brief_deck.sh|seldon_events.jsonl|\
    "cc_tasks/${TASK_STEM}_RESULT.md") ;;
    *) echo "FAIL moved outside the write set: $f"; fail=1 ;;
  esac
done <<< "$(changed_and_new .)"

# 3. The narrative is the task's §Narrative, verbatim below its comment line, except for the
#    numeral and citation corrections the RESULT lists (decision 2), which this diff shows.
if ! diff <(sed -n '/^## Narrative$/,$p' "cc_tasks/${TASK_STEM}.md" | tail -n +3) \
          <(tail -n +2 docs/deck/brief_narrative.md); then
  echo "NOTE the narrative differs from the task's §Narrative by the lines above; each must be in the RESULT"
fi

# 4. A prior task file or RESULT is immutable.
if git diff --name-only "$BASE" -- cc_tasks/ | grep -v "^cc_tasks/${TASK_STEM}_RESULT.md$" | grep -q .; then
  echo "FAIL a tracked cc_tasks file changed:"; git diff --name-only "$BASE" -- cc_tasks/; fail=1
fi

# 5. Both views are what their generators render.
if ! $PY scripts/build_brief_pack.py --check; then
  echo "FAIL docs/brief/ is not what scripts/build_brief_pack.py renders"; fail=1
fi
if ! $PY scripts/build_brief_deck.py --check; then
  echo "FAIL docs/deck/brief_deck.pptx or brief_appendix.pptx is not what scripts/build_brief_deck.py renders"; fail=1
fi

# 6. The deck renderer writes only under docs/deck/.
if grep -nE "write_text|write_bytes|open\([^)]*['\"][wa]" scripts/build_brief_deck.py \
     | grep -vE "out\.write_bytes|DIAGRAM_SIDECAR\.write_text|i\.write_text"; then
  echo "FAIL scripts/build_brief_deck.py writes somewhere other than docs/deck/"; fail=1
fi

# 7. Logs are append-only.
if git diff "$BASE" -- seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost or changed a line; the log is append-only"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
