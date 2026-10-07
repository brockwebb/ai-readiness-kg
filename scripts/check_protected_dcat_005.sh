#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-07_DCAT-005_brief_corrections_before_omb.md`, asserted
# against HEAD (DCAT-004 v2's commit, the record this task corrects).
#
# Write set, the task's own words: `reports/dcat_us_3_brief/` (BRIEF.md, BRIEF.pdf, ROWS.md,
# evidence/ new files only, run/, build_report.json), `brief_config.yaml` (a dated amendment
# block; prior lines untouched), `scripts/dcat_brief_*.py` and `scripts/dcat_faq_evidence.py`,
# `docs/evidence/claims.yaml` (append), tests, the RESULT. Plus the two shared stores every paid
# task appends to: the spend ledger (the run's declaration and its reservations) and the Seldon
# store (`seldon cc complete`). Byte-identical: `reports/dcat_us_3_faq/`, every rule, matrix and
# stored payload, the framework record, and DCAT-004 v2's own record (answers.json, every
# evidence file it wrote, DEMO.md and demo/).
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
B=reports/dcat_us_3_brief

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

allowed() {
  case "$1" in
    $B/BRIEF.md|$B/BRIEF.pdf|$B/ROWS.md|$B/build_report.json|$B/brief_config.yaml) return 0 ;;
    $B/run/*|$B/evidence/*) return 0 ;;
    scripts/dcat_brief_*.py|scripts/dcat_faq_evidence.py|scripts/check_protected_dcat_005.sh) return 0 ;;
    tests/test_dcat_brief.py) return 0 ;;
    docs/evidence/claims.yaml|state/spend_ledger.jsonl|seldon_events.jsonl) return 0 ;;
    cc_tasks/2026-10-07_DCAT-005_brief_corrections_before_omb_RESULT.md) return 0 ;;
  esac
  return 1
}

while IFS= read -r path; do
  [ -z "$path" ] && continue
  allowed "$path" || { echo "FAIL path outside the write set moved: $path"; fail=1; }
done < <(changed_and_new .)

# evidence/: new files only.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  echo "FAIL an existing evidence file changed: $f"; fail=1
done < <(git diff --name-only HEAD -- "$B/evidence")

# Byte-identical (the task's list, and DCAT-004 v2's record).
for p in reports/dcat_us_3_faq framework/ai_readiness_framework.json assessment/harness/scan/rules \
         docs/reports/scan_matrix_* "$B/answers.json" "$B/DEMO.md" "$B/demo"; do
  if [ -n "$(changed_and_new "$p")" ]; then echo "FAIL $p must be byte-identical and moved"; fail=1; fi
done
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet HEAD -- "$f"; then echo "FAIL a stored payload changed: $f"; fail=1; fi
done < <(command git ls-tree -r --name-only HEAD -- state/ | grep -E '^state/scan_[^/]*\.json$')

# Append-only: the config (a dated block after DCAT-004's lines), the evidence map, the
# checkpoint, the ledger, the Seldon store.
for f in "$B/brief_config.yaml" docs/evidence/claims.yaml "$B/run/checkpoint.jsonl" state/spend_ledger.jsonl \
         seldon_events.jsonl; do
  removed=$(git diff HEAD -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done

# The evidence map's three writers must each re-render the file exactly: its generator, DCAT-004's
# rows and this task's superseding rows.
PY=/opt/anaconda3/bin/python3
"$PY" scripts/build_evidence_map.py --check >/dev/null 2>&1 || { echo "FAIL docs/evidence/claims.yaml drifts from build_evidence_map.py"; fail=1; }
"$PY" scripts/dcat_brief_claims.py --check >/dev/null 2>&1 || { echo "FAIL docs/evidence/claims.yaml drifts from dcat_brief_claims.py"; fail=1; }
"$PY" scripts/dcat_brief_claims.py --dcat005 --check >/dev/null 2>&1 || { echo "FAIL docs/evidence/claims.yaml drifts from dcat_brief_claims.py --dcat005"; fail=1; }

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
