#!/bin/sh
# The protected-paths diff for cc_tasks/2026-09-15_abstract_five_checks.md.
#
# The task's write set is exactly two things: `docs/reports/publication.yaml` (decision 1, and
# decision 3 says nothing else in that file moves) and the files its consumers regenerate
# (decision 2 — "never by hand"). Everything else is "Zero edits to".
#
# So this check is stricter than most: it does not enumerate what may move and hope the rest
# held. It asserts the ONE allowed hunk in publication.yaml, then asserts that every modified
# path is in the generated set, and that nothing under the measurement tree moved at all.
#
# The status prefix is stripped before matching, so the check answers the same before and after
# `git add` (the defect found in check_protected_standing_guards.sh on 2026-09-14).
cd /Users/brock/GitHub/ai-readiness-kg || exit 2
echo "=== protected paths"
fail=0

say() { echo; echo "-- $1"; }
must_be_empty() {
  label="$1"; shift
  out=$(git status --porcelain -- "$@")
  [ -n "$out" ] && { echo "$out"; echo "   VIOLATION: $label"; fail=1; }
}

say "STORED PAYLOADS and the event log — this task measures nothing and judges nothing"
must_be_empty "a stored payload changed" state/
must_be_empty "the event log changed" events/

say "THE MEASUREMENT TREE — no rule, no harness, no schema, no framework record, no corpus"
must_be_empty "the rules or harness changed" assessment/
must_be_empty "kg/ changed" kg/
must_be_empty "the framework record or skeleton changed" framework/
must_be_empty "corpus changed" corpus/
must_be_empty "controls or the identity gate changed" controls.yaml dixie_evidence.yaml

say "THE REPORT and its inputs — the abstract is a SUMMARY of the report, not a source for it"
must_be_empty "the report source or a section changed" docs/reports/2026-09_fss_ai_readiness_L0.md \
  docs/reports/sections/ docs/reports/generated/
must_be_empty "a matrix changed" docs/reports/scan_matrix_tierA_2026-09-10_rj2.json \
  docs/reports/scan_matrix_tierA_2026-09-10_rj2.csv \
  docs/reports/scan_matrix_tierC_2026-09-10_rj2.json \
  docs/reports/scan_matrix_tierC_2026-09-10_rj2.csv \
  docs/reports/scan_matrix_product_2026-09-10_rj2.json \
  docs/reports/scan_matrix_product_2026-09-10_rj2.csv
must_be_empty "the PDF changed" docs/reports/2026-09_fss_ai_readiness_L0.pdf

say "TESTS, and every script but the one this gate needed"
must_be_empty "a test changed" tests/
git status --porcelain -- scripts/ | sed 's/^...//' \
  | grep -v '^scripts/check_protected_abstract_five_checks\.sh$' > /tmp/apfc_scripts.txt
if [ -s /tmp/apfc_scripts.txt ]; then
  cat /tmp/apfc_scripts.txt; echo "   VIOLATION: a script other than this check moved"; fail=1
else
  echo "   only scripts/check_protected_abstract_five_checks.sh (new, this gate)"
fi

say "PRIOR RESULTs and design decisions — a prior execution record is not edited"
git status --porcelain -- cc_tasks/ | sed 's/^...//' \
  | grep -v '^cc_tasks/2026-09-15_abstract_five_checks\(_RESULT\)\?\.md$' > /tmp/apfc_tasks.txt
if [ -s /tmp/apfc_tasks.txt ]; then
  cat /tmp/apfc_tasks.txt; echo "   VIOLATION: a cc_task other than this one's pair moved"; fail=1
else
  echo "   only this task and its RESULT"
fi
must_be_empty "a design decision or design note changed" docs/design_decisions.md docs/design/ \
  docs/schema_v0.1.md CLAUDE.md

say "publication.yaml — decision 3: ONE line moves, and it is the abstract's count"
added=$(git diff -U0 -- docs/reports/publication.yaml | grep -c '^+[^+]')
removed=$(git diff -U0 -- docs/reports/publication.yaml | grep -c '^-[^-]')
echo "   +$added / -$removed line(s)"
if [ "$added" != "1" ] || [ "$removed" != "1" ]; then
  git diff -- docs/reports/publication.yaml
  echo "   VIOLATION: publication.yaml moved by more than the one allowed line"; fail=1
fi
git diff -U0 -- docs/reports/publication.yaml | grep '^[+-][^+-]' | grep -qv 'host-level\|separately' \
  && { echo "   VIOLATION: the moved line is not the abstract's count line"; fail=1; }
git diff -- docs/reports/publication.yaml | grep -q '^-.*separately\. Six$' \
  || { echo "   VIOLATION: the removed line is not the 'Six' line"; fail=1; }
git diff -- docs/reports/publication.yaml | grep -q '^+.*separately\. Five$' \
  || { echo "   VIOLATION: the added line is not the 'Five' line"; fail=1; }

say "EVERY modified path is either publication.yaml, a GENERATED consumer, or this task's pair"
# The generated set is not typed: it is what the builder reports it wrote, plus the two records
# it stamps with a build date. Anything outside it is a hand edit, which decision 2 forbids.
git status --porcelain | sed 's/^...//' | sort > /tmp/apfc_all.txt
cat > /tmp/apfc_allowed.txt <<'EOF'
.zenodo.json
CITATION.cff
cc_tasks/2026-09-15_abstract_five_checks.md
cc_tasks/2026-09-15_abstract_five_checks_RESULT.md
docs/data/CITATION.cff
docs/data/index.json
docs/data/sources_per_check.json
docs/data/zenodo.json
docs/index.html
docs/llms.txt
docs/reports/publication.yaml
docs/sitemap.xml
scripts/check_protected_abstract_five_checks.sh
seldon_events.jsonl
EOF
sort -o /tmp/apfc_allowed.txt /tmp/apfc_allowed.txt
stray=$(comm -23 /tmp/apfc_all.txt /tmp/apfc_allowed.txt)
if [ -n "$stray" ]; then
  echo "$stray"; echo "   VIOLATION: a path outside the write set moved"; fail=1
else
  echo "   $(wc -l < /tmp/apfc_all.txt | tr -d ' ') modified path(s), all inside the write set"
fi

say "THE POINT OF THE TASK, asserted rather than assumed"
# The abstract's count must equal the number of legs the published tier-A matrix actually has.
# Typed nowhere: read from the matrix, which is the thing the summary summarizes.
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import json, re, sys, pathlib, yaml
REPO = pathlib.Path("/Users/brock/GitHub/ai-readiness-kg")
# The numeral map is `scripts/numerals.py`, imported rather than copied
# (`cc_tasks/2026-09-15_derived_counts_and_appendix_guard.md` decision 1). It used to be a dict
# literal here, and `scripts/build_l0_site.py` held the same fact as a literal numeral in a
# label; one copy moved under DD-066 and the other did not. A gate holding its own copy of what
# it gates is not a gate.
sys.path.insert(0, str(REPO / "scripts"))
from numerals import word
legs = json.loads((REPO / "docs/reports/scan_matrix_tierA_2026-09-10_rj2.json")
                  .read_text())["legs"]
want = word(len(legs)).capitalize()
pub = yaml.safe_load((REPO / "docs/reports/publication.yaml").read_text())
abstract = " ".join(pub["abstract"].split())
print(f"   the tier-A matrix has {len(legs)} legs: {legs}")
m = re.search(r"(\w+) host-level checks over one measurement cycle", abstract)
if not m:
    print("   VIOLATION: the abstract no longer states a count of host-level checks"); sys.exit(1)
print(f"   the abstract says {m.group(1)!r}; the matrix requires {want!r}")
if m.group(1) != want:
    print("   VIOLATION: the published summary disagrees with the matrix it summarizes")
    sys.exit(1)
# and every generated consumer carries the same sentence, whitespace-normalised
consumers = ["CITATION.cff", ".zenodo.json", "docs/data/CITATION.cff", "docs/data/zenodo.json",
             "docs/index.html", "docs/llms.txt"]
missing = [c for c in consumers
           if f"{want} host-level checks" not in " ".join((REPO / c).read_text().split())]
if missing:
    print(f"   VIOLATION: consumers still carry the old count: {missing}"); sys.exit(1)
print(f"   all {len(consumers)} generated consumers carry {want!r}")
stale = [c for c in consumers
         if "Six host-level checks" in " ".join((REPO / c).read_text().split())]
if stale:
    print(f"   VIOLATION: consumers still carry 'Six': {stale}"); sys.exit(1)
print("   no consumer still carries 'Six host-level checks'")
PY

echo
[ "$fail" = "0" ] && echo "=== protected paths: PASS" || echo "=== protected paths: FAIL"
exit "$fail"
