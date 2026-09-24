#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-23_brief_narrative_v2.md`, asserted against the commit the
# task was launched on. (Earlier tasks' checks, `2026-09-22_brief_deck_assembly` against `a3756e3`,
# `2026-09-23_brief_deck_packaging` against `5ed4eac` and `2026-09-23_brief_narrative` against
# `996d8f0`, are in git history.)
#
#   "**Write set:** `docs/deck/brief_narrative.md` (the five sections), `docs/deck/brief_deck.pptx`,
#    `tests/test_brief_deck.py` only if a split or overflow needs a count changed,
#    `scripts/check_protected_brief_deck.sh` (base moves to this launch commit; its narrative diff
#    now compares to §Replacements for the five sections and to `f0dd9dc` for the rest), the
#    RESULT. Byte-identical: everything else the last two deck tasks listed,
#    `brief_appendix.pptx` included."
#
# BASE is the dispatcher's `dispatch_launched` record commit for this task (`3afb7840`), the last
# commit before the task wrote anything. Override with BASE=<rev> to re-run it later.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
TASK_STEM=2026-09-23_brief_narrative_v2
BASE=${BASE:-3f0d0e7}
# The narrative every section not replaced by this task must still match, byte for byte.
NARRATIVE_BASE=f0dd9dc

changed_and_new() {
  { git diff --name-only "$BASE" -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the task's byte-identical list, plus every other store of record.
for p in 'docs/brief/' 'docs/deck/brief_appendix.pptx' 'docs/deck/diagrams/' \
         'docs/deck/brief_deck_content.md' 'scripts/build_brief_pack.py' \
         'scripts/build_brief_deck.py' \
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
    docs/deck/brief_narrative.md|docs/deck/brief_deck.pptx|\
    tests/test_brief_deck.py|scripts/check_protected_brief_deck.sh|seldon_events.jsonl|\
    "cc_tasks/${TASK_STEM}_RESULT.md") ;;
    *) echo "FAIL moved outside the write set: $f"; fail=1 ;;
  esac
done <<< "$(changed_and_new .)"

# 3. The narrative is `NARRATIVE_BASE`'s, with the title section and the four sections the task
#    names replaced whole by its §Replacements (decision 1). Any line this diff prints is a
#    deviation the RESULT must list; a section that moved or went missing fails outright.
expected=$(mktemp); trap 'rm -f "$expected"' EXIT
if ! $PY - "$NARRATIVE_BASE" "cc_tasks/${TASK_STEM}.md" > "$expected" <<'PYEOF'
import re, subprocess, sys
base, task = sys.argv[1], sys.argv[2]
old = subprocess.run(["git", "show", f"{base}:docs/deck/brief_narrative.md"], check=True,
                     capture_output=True, text=True).stdout
rep = open(task, encoding="utf-8").read().split("\n## Replacements\n", 1)[1]
blocks = [b.strip("\n") for b in re.split(r"(?m)^### .*\n", rep)[1:]]
replaced = ["# What a machine sees when it reads federal statistics",
            "## The problem is measurable, and nobody was measuring it",
            "## Start with our own product",
            "## What we measured against, and how it differs from USAFacts",
            "## What the whole cohort looks like"]
if len(blocks) != len(replaced):
    sys.exit(f"§Replacements has {len(blocks)} blocks, the task names {len(replaced)} sections")
comment, body = old.split("\n", 1)
out, hit = [], 0
for sec in [x for x in re.split(r"(?m)^(?=#{1,2} )", body) if x]:
    head = sec.split("\n", 1)[0]
    if head in replaced:
        out.append(blocks[replaced.index(head)] + sec[len(sec.rstrip("\n")):]); hit += 1
    else:
        out.append(sec)
if hit != len(replaced):
    sys.exit(f"{hit} of {len(replaced)} named sections found in {base}'s narrative")
sys.stdout.write(comment + "\n" + "".join(out))
PYEOF
then
  echo "FAIL the expected narrative could not be built from ${NARRATIVE_BASE} and §Replacements"; fail=1
elif ! diff "$expected" docs/deck/brief_narrative.md; then
  echo "NOTE the narrative differs from ${NARRATIVE_BASE} + §Replacements by the lines above; each must be in the RESULT"
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
