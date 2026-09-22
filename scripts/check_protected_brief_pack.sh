#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-22_brief_material_pack_v2.md`, asserted against HEAD.
#
#   "**Write set:** `scripts/build_brief_pack.py`, `docs/brief/**` (all new),
#    `tests/test_brief_pack.py` (...), this task's `scripts/check_protected_brief_pack.sh`, the
#    RESULT. Byte-identical: `framework/`, `state/`, `events/`, `docs/reports/`, `docs/data/`,
#    `CITATION.cff`, `.zenodo.json`, `assessment/`, `corpus/`."
#
# The pack is a VIEW (DN-005): it reads and measures nothing. So the strongest thing this check
# can assert is that nothing it could have measured, judged or published moved, and that the
# pack on disk is the pack its generator produces rather than a pack somebody typed.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
TASK_STEM=2026-09-22_brief_material_pack_v2

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the task's byte-identical list, plus every other store of record.
for p in 'framework/' 'state/' 'events/' 'docs/reports/' 'docs/data/' 'CITATION.cff' \
         '.zenodo.json' 'assessment/' 'corpus/' 'kg/' 'mcp/' 'controls.yaml' \
         'dixie_evidence.yaml' 'seldon.yaml' 'Makefile' 'CLAUDE.md' 'LICENSE' 'LICENSE-DATA'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. `docs/` moved only under `docs/brief/`.
docs_moved=$(changed_and_new 'docs/' | grep -v '^docs/brief/')
if [ -n "$docs_moved" ]; then
  echo "FAIL docs/ moved outside docs/brief/:"; echo "$docs_moved" | sed 's/^/       /'; fail=1
fi

# 3. Every path that moved is on the list.
while read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    docs/brief/*|scripts/build_brief_pack.py|tests/test_brief_pack.py|\
    scripts/check_protected_brief_pack.sh|seldon_events.jsonl|\
    "cc_tasks/${TASK_STEM}_RESULT.md") ;;
    *) echo "FAIL moved outside the write set: $f"; fail=1 ;;
  esac
done <<< "$(changed_and_new .)"

# 4. A prior task file or RESULT is immutable. A modified tracked cc_tasks file is a violation.
if git diff --name-only HEAD -- cc_tasks/ | grep -v "^cc_tasks/${TASK_STEM}_RESULT.md$" | grep -q .; then
  echo "FAIL a tracked cc_tasks file changed:"; git diff --name-only HEAD -- cc_tasks/; fail=1
fi

# 5. The pack is GENERATED: the generator re-renders every page and compares byte for byte.
if ! $PY scripts/build_brief_pack.py --check; then
  echo "FAIL docs/brief/ is not what scripts/build_brief_pack.py renders"; fail=1
fi

# 6. The generator writes only under docs/brief/: no other path in it is opened for writing.
if grep -nE "write_text|open\([^)]*['\"][wa]" scripts/build_brief_pack.py \
     | grep -vE "p\.write_text\(v|CAPTURE\.write_text|i\.write_text" ; then
  echo "FAIL scripts/build_brief_pack.py writes somewhere other than docs/brief/"; fail=1
fi

# 7. Logs are append-only.
if git diff HEAD -- seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost or changed a line; the log is append-only"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
