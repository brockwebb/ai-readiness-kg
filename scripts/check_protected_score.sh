#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-18_scoring_model.md`, asserted against HEAD.
#
#   "**Write set:** `scripts/score.py` (new), `docs/design/scoring_model.md` (new, generated),
#    `tests/test_score.py` (new), `scripts/check_protected_score.sh` (new),
#    `seldon_events.jsonl`, the RESULT. The record is not written. `docs/` otherwise
#    byte-identical."
#
# The scoring model is a QUERY: it reads the record and the published matrices and writes
# nothing either of them holds. So the strongest thing this check can assert is that nothing a
# score is computed from moved, that no score was published (decision 8), and that the one page
# it added is what its generator prints.
#
# Extended by `cc_tasks/2026-09-18_scoring_levels.md` (flat view, A12 criterion, readiness
# levels): same write set plus that task's RESULT. Its decision 2 would have let the record move
# through the single writer if A12's promotion criterion were met on the record's own terms; it
# is stated as an operator decision, so the record stays protected here. Decision 5: the ladder
# is published nowhere either, which checks 3 to 5 already hold.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright: the record, the evidence, the harness, the logs, the published data.
for p in 'framework/' 'state/' 'corpus/' 'assessment/' 'events/' 'kg/' 'mcp/' \
         'docs/reports/' 'docs/data/' 'docs/crosswalk/' 'LICENSE' 'LICENSE-DATA' \
         'controls.yaml' 'dixie_evidence.yaml' 'seldon.yaml' 'Makefile' 'CITATION.cff' \
         '.zenodo.json' 'CLAUDE.md'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. Every path that moved is on the list.
ALLOWED=(
  'scripts/score.py'
  'scripts/check_protected_score.sh'
  'tests/test_score.py'
  'docs/design/scoring_model.md'
  'seldon_events.jsonl'
  'cc_tasks/2026-09-18_scoring_model_RESULT.md'
  'cc_tasks/2026-09-18_scoring_levels_RESULT.md'
)
while read -r f; do
  [ -z "$f" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$f" = "$a" ] && ok=1; done
  if [ "$ok" -eq 0 ]; then echo "FAIL moved outside the write set: $f"; fail=1; fi
done <<< "$(changed_and_new .)"

# 3. `docs/` otherwise byte-identical: the one new page, nothing else under docs/.
x=$(changed_and_new docs/ | grep -v '^docs/design/scoring_model.md$')
[ -n "$x" ] && { echo "FAIL docs/ moved beyond the design page:"; echo "$x" | sed 's/^/       /'; fail=1; }

# 4. The page is the generator's output, and it names no body (decision 8: nothing published).
if ! $PY scripts/score.py --check > /dev/null; then
  echo "FAIL docs/design/scoring_model.md is not scripts/score.py --explain"; fail=1
fi
if ! $PY - <<'EOF'
import sys
sys.path.insert(0, "scripts")
import score as S
page = open("docs/design/scoring_model.md", encoding="utf-8").read()
named = [b for b in S.bodies_on(S.snapshot_cycle()) if f"| {b} |" in page or f"{b}:" in page]
print(f"FAIL the design page names bodies: {named}" if named
      else "   design page: generated, and names no body")
sys.exit(1 if named else 0)
EOF
then fail=1; fi

# 5. Nothing under docs/ (the site) carries a score or level payload.
if git ls-files --others --exclude-standard -- docs/ | grep -qiE '(score|level).*\.(json|csv|html)$'; then
  echo "FAIL a score or level payload was added under docs/"; fail=1
fi

# 6. The Seldon log is append-only.
if git diff HEAD -- seldon_events.jsonl | grep -q '^-[^-]'; then
  echo "FAIL seldon_events.jsonl lost or changed a line; the log is append-only"; fail=1
fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
