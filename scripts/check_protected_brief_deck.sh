#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-23_brief_deck_packaging.md`, asserted against the commit the
# task was launched on. (This file was first written for `2026-09-22_brief_deck_assembly`; that
# task's check, against its own launch commit `a3756e3`, is in git history.)
#
#   "**Write set:** `scripts/build_brief_deck.py`, `docs/deck/**`, `tests/test_brief_deck.py`,
#    `scripts/build_brief_pack.py` (decision 3 only), `docs/brief/E_architecture.md` and
#    `numbers.json` if a diagram count changes (via the generator only),
#    `scripts/check_protected_brief_deck.sh` (updated for two outputs), the RESULT.
#    Byte-identical: `framework/`, `state/`, `events/`, `docs/reports/`, `docs/data/`,
#    `docs/crosswalk/`, `assessment/`, `corpus/`, `mcp/`, every other file under `docs/brief/`."
#   Decision 3: "Only `E_architecture.md`, the two PNGs and their sha sidecars may change under
#    `docs/brief/` and `docs/deck/diagrams/`."
#
# Decision 3 was committed on its own (its gate, `check_protected_brief_pack.sh`, reads HEAD), so
# this check diffs against the launch commit rather than HEAD: BASE is the dispatcher's
# `dispatch_launched` record commit for this task (`bffd0ed2`), the last commit before the task
# wrote anything. Override with BASE=<rev> to re-run it later.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
TASK_STEM=2026-09-23_brief_deck_packaging
BASE=${BASE:-5ed4eac}

changed_and_new() {
  { git diff --name-only "$BASE" -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the task's byte-identical list, plus every other store of record.
for p in 'framework/' 'state/' 'events/' 'docs/reports/' 'docs/data/' 'docs/crosswalk/' \
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
    docs/deck/*|docs/brief/*|scripts/build_brief_deck.py|scripts/build_brief_pack.py|\
    tests/test_brief_deck.py|scripts/check_protected_brief_deck.sh|seldon_events.jsonl|\
    "cc_tasks/${TASK_STEM}_RESULT.md") ;;
    *) echo "FAIL moved outside the write set: $f"; fail=1 ;;
  esac
done <<< "$(changed_and_new .)"

# 3. docs/brief/ and docs/deck/diagrams/ moved only where decision 3 allows.
while read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    docs/brief/E_architecture.md|docs/brief/numbers.json|docs/deck/diagrams/E_c.png|\
    docs/deck/diagrams/E_d.png|docs/deck/diagrams/diagrams.json) ;;
    *) echo "FAIL moved beyond decision 3: $f"; fail=1 ;;
  esac
done <<< "$(changed_and_new docs/brief/ docs/deck/diagrams/)"
if git diff "$BASE" -- scripts/build_brief_pack.py | grep '^[-+][^-+]' | grep -vE '^[-+]\s*#|flowchart|pg\.add\(\*mermaid\(\[' | grep -q .; then
  echo "FAIL scripts/build_brief_pack.py changed beyond the two diagram directions"; fail=1
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
