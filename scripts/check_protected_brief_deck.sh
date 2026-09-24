#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-24_brief_narrative_v3.md`, asserted against the commit the
# task was launched on. (Earlier tasks' checks, `2026-09-22_brief_deck_assembly` against `a3756e3`,
# `2026-09-23_brief_deck_packaging` against `5ed4eac`, `2026-09-23_brief_narrative` against
# `996d8f0` and `2026-09-23_brief_narrative_v2` against `3f0d0e7`, are in git history.)
#
#   "**Write set:** `scripts/build_brief_pack.py` (decision 1 only), `docs/brief/B_usafacts_delta.md`
#    and `numbers.json` if a count changes (via the generator only), `docs/deck/brief_narrative.md`
#    (decision 2 only), `docs/deck/brief_deck.pptx`, `tests/test_brief_deck.py`,
#    `tests/test_brief_pack.py` (a test that the two quotations ground),
#    `scripts/check_protected_brief_deck.sh` (base moves to this launch commit; narrative diff base
#    is `73a3c91` plus decision 2), the RESULT. Byte-identical: every other file under `docs/brief/`
#    and `docs/deck/`, `build_brief_deck.py`, and every directory the earlier deck tasks listed."
#
# Two files the task lists byte-identical move, and only by the pack commit they stamp (RESULT §5):
# committing page B moves the last commit that wrote `docs/brief/`, which the appendix's cover
# prints, and which line 1 of `brief_deck_content.md` must name for
# `test_the_content_file_names_the_pack_it_was_built_from`. §3 below allows exactly that and no more.
#
# BASE is the dispatcher's `dispatch_launched` record commit for this task (`087adf78`), the last
# commit before the task wrote anything. Override with BASE=<rev> to re-run it later.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
TASK_STEM=2026-09-24_brief_narrative_v3
BASE=${BASE:-a4fa402}
# The narrative decision 2 edits, sentence by sentence.
NARRATIVE_BASE=73a3c91

changed_and_new() {
  { git diff --name-only "$BASE" -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the task's byte-identical list, plus every other store of record.
for p in 'docs/deck/diagrams/' 'scripts/build_brief_deck.py' \
         'framework/' 'state/' 'events/' 'docs/reports/' 'docs/data/' 'docs/crosswalk/' \
         'assessment/' 'corpus/' 'mcp/' 'CITATION.cff' '.zenodo.json' 'kg/' 'controls.yaml' \
         'dixie_evidence.yaml' 'seldon.yaml' 'Makefile' 'CLAUDE.md' 'LICENSE' 'LICENSE-DATA'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. Every path that moved is on the write set (plus the two stamp-only files of §3).
while read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    scripts/build_brief_pack.py|docs/brief/B_usafacts_delta.md|docs/brief/numbers.json|\
    docs/deck/brief_narrative.md|docs/deck/brief_deck.pptx|\
    docs/deck/brief_appendix.pptx|docs/deck/brief_deck_content.md|\
    tests/test_brief_deck.py|tests/test_brief_pack.py|scripts/check_protected_brief_deck.sh|\
    seldon_events.jsonl|"cc_tasks/${TASK_STEM}_RESULT.md") ;;
    *) echo "FAIL moved outside the write set: $f"; fail=1 ;;
  esac
done <<< "$(changed_and_new .)"

# 3. The stamp-only files moved by their pack commit and nothing else.
if ! $PY - "$BASE" <<'PYEOF'
import io, re, subprocess, sys, zipfile
base = sys.argv[1]
pack = subprocess.run(["git", "log", "-1", "--format=%H", "--", "docs/brief"], check=True,
                      capture_output=True, text=True).stdout.strip()
show = lambda p: subprocess.run(["git", "show", f"{base}:{p}"], check=True,
                                capture_output=True).stdout
old = show("docs/deck/brief_deck_content.md").decode("utf-8")
new = open("docs/deck/brief_deck_content.md", encoding="utf-8").read()
stamped = re.sub(r"(brief pack at commit )[0-9a-f]{40}", rf"\g<1>{pack}", old, count=1)
if new != stamped:
    sys.exit("FAIL docs/deck/brief_deck_content.md moved by more than its pack-commit stamp")
o = zipfile.ZipFile(io.BytesIO(show("docs/deck/brief_appendix.pptx")))
n = zipfile.ZipFile("docs/deck/brief_appendix.pptx")
if o.namelist() != n.namelist():
    sys.exit("FAIL brief_appendix.pptx gained or lost a member")
moved = [m for m in n.namelist() if o.read(m) != n.read(m)]
if moved and moved != ["ppt/slides/slide1.xml"]:
    sys.exit(f"FAIL brief_appendix.pptx moved outside its cover: {moved}")
if moved:
    t = lambda z: re.sub(r"\d{4}-\d{2}-\d{2} · pack commit [0-9a-f]{12}", "STAMP",
                         z.read("ppt/slides/slide1.xml").decode("utf-8"))
    if t(o) != t(n):
        sys.exit("FAIL the appendix cover moved by more than its pack stamp")
PYEOF
then fail=1; fi

# 4. The narrative is `NARRATIVE_BASE`'s with decision 2's sentence edits applied, each exactly
#    once. G's label is page B's ("FSS-derived constructs"), not the task's wording, per decision
#    2's last paragraph. Any line this diff prints is a deviation the RESULT must list.
expected=$(mktemp); trap 'rm -f "$expected"' EXIT
if ! $PY - "$NARRATIVE_BASE" > "$expected" <<'PYEOF'
import subprocess, sys
t = subprocess.run(["git", "show", f"{sys.argv[1]}:docs/deck/brief_narrative.md"], check=True,
                   capture_output=True, text=True).stdout
quote = ("> As government continues to evolve its role as a data provider to AI systems, these "
         "criteria should provide a roadmap for allowing AI to not only access, but also "
         "understand and validate the data they are retrieving and presenting to users. [B]")
edits = [
    ("a test for each of 49 indicators, three criteria the framework needed and did not have,",
     "49 indicators written as tests, 24 of them with a rule that runs today, three criteria the "
     "framework needed and did not have,"),
    ("USAFacts' guide gives agencies 7 criteria [G] for AI-ready data, written for the people who "
     "decide what to publish [B].",
     "USAFacts' guide gives agencies four criteria for AI-ready data, accessible, understandable, "
     "accurate and open, written for the people who decide what to publish [B]."),
    ("Four of the criteria, A through D, describe the public surface a publisher controls: "
     "accessible, documented, licensed and cataloged.",
     "The guide calls itself a roadmap, and its four criteria, A through D, are accessible, "
     "understandable, accurate and open [B]."),
    ("the criteria for evaluation, release and governance that a running measurement turned out "
     "to need,",
     "the three criteria a running measurement turned out to need, E the TEVV loop, F release "
     "engineering and G the FSS-derived constructs,"),
    ("A to D are USAFacts' criteria, E to G are added [B].",
     "A to D are USAFacts' four, E to G are added [B]."),
    ("Three criteria, E evaluation, F release and G governance, have no USAFacts counterpart and "
     "are marked added.",
     "Three criteria, E the TEVV loop, F release engineering and G the FSS-derived constructs, "
     "have no USAFacts counterpart and are marked added [B]."),
    # The p. 2 quotation, its own paragraph after the paragraph the third edit is in.
    ("The contribution is the join, and the fact that it runs.\n",
     "The contribution is the join, and the fact that it runs.\n\n" + quote + "\n"),
]
for old, new in edits:
    if t.count(old) != 1:
        sys.exit(f"decision 2 edit does not match exactly once in {sys.argv[1]}: {old[:60]!r}")
    t = t.replace(old, new)
sys.stdout.write(t)
PYEOF
then
  echo "FAIL the expected narrative could not be built from ${NARRATIVE_BASE} and decision 2"; fail=1
elif ! diff "$expected" docs/deck/brief_narrative.md; then
  echo "NOTE the narrative differs from ${NARRATIVE_BASE} + decision 2 by the lines above; each must be in the RESULT"
fi

# 5. A prior task file or RESULT is immutable.
if git diff --name-only "$BASE" -- cc_tasks/ | grep -v "^cc_tasks/${TASK_STEM}_RESULT.md$" | grep -q .; then
  echo "FAIL a tracked cc_tasks file changed:"; git diff --name-only "$BASE" -- cc_tasks/; fail=1
fi

# 6. Both views are what their generators render.
if ! $PY scripts/build_brief_pack.py --check; then
  echo "FAIL docs/brief/ is not what scripts/build_brief_pack.py renders"; fail=1
fi
if ! $PY scripts/build_brief_deck.py --check; then
  echo "FAIL docs/deck/brief_deck.pptx or brief_appendix.pptx is not what scripts/build_brief_deck.py renders"; fail=1
fi

# 7. The deck renderer writes only under docs/deck/.
if grep -nE "write_text|write_bytes|open\([^)]*['\"][wa]" scripts/build_brief_deck.py \
     | grep -vE "out\.write_bytes|DIAGRAM_SIDECAR\.write_text|i\.write_text"; then
  echo "FAIL scripts/build_brief_deck.py writes somewhere other than docs/deck/"; fail=1
fi

# 8. Logs are append-only.
if git diff "$BASE" -- seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost or changed a line; the log is append-only"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
