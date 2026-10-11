#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-07_concise_report_prose.md`, asserted against HEAD.
#
# Write set, the task's own words: `reports/concise/`, `scripts/concise_report_*.py`,
# `docs/style/operator_banned_words.yaml`, `scripts/dcat_faq_lint.py` (reading the list only),
# tests for the gate measures, the RESULT. Plus, each needed and named in the RESULT: this check;
# `pyproject.toml` (spaCy declared, which `tests/test_adopter_path.py` requires of a new import);
# the two shared stores every paid task appends to, the spend ledger and the Seldon store.
# Byte-identical: `docs/evidence/claims.yaml`, `FROZEN.md`, every rule, matrix and stored
# payload, `scripts/score.py`, every report under `docs/reports/`.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

allowed() {
  case "$1" in
    reports/concise/*) return 0 ;;
    scripts/concise_report_*.py|scripts/check_protected_concise_report_prose.sh|scripts/dcat_faq_lint.py) return 0 ;;
    docs/style/operator_banned_words.yaml|pyproject.toml) return 0 ;;
    tests/test_concise_report_gate.py|tests/test_concise_report_run.py|tests/test_concise_report_shipped.py) return 0 ;;
    state/spend_ledger.jsonl|seldon_events.jsonl) return 0 ;;
    cc_tasks/2026-10-07_concise_report_prose_RESULT.md) return 0 ;;
  esac
  return 1
}

while IFS= read -r path; do
  [ -z "$path" ] && continue
  allowed "$path" || { echo "FAIL path outside the write set moved: $path"; fail=1; }
done < <(changed_and_new .)

# Byte-identical (the task's list).
for p in docs/evidence/claims.yaml docs/evidence/FROZEN.md assessment/harness/scan/rules scripts/score.py \
         docs/reports framework/ai_readiness_framework.json; do
  if [ -n "$(changed_and_new "$p")" ]; then echo "FAIL $p must be byte-identical and moved"; fail=1; fi
done
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet HEAD -- "$f"; then echo "FAIL a stored payload changed: $f"; fail=1; fi
done < <(command git ls-tree -r --name-only HEAD -- state/ | grep -E '^state/scan_[^/]*\.json$')

# Append-only: the ledger and the Seldon store.
for f in state/spend_ledger.jsonl seldon_events.jsonl; do
  removed=$(git diff HEAD -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done

# The lint change reads the list and removes no rule: no line of the old file's RULES block is gone,
# and the DCAT files it guards still pass it.
removed=$(git diff HEAD -- scripts/dcat_faq_lint.py | grep -c '^-[^-]' || true)
[ "$removed" -le 2 ] || { echo "FAIL scripts/dcat_faq_lint.py lost $removed line(s); it may only add the list"; fail=1; }
PY=/opt/anaconda3/bin/python3
"$PY" scripts/dcat_faq_lint.py reports/dcat_us_3_faq/FAQ.md reports/dcat_us_3_faq/ATTACHMENT_evidence.md \
    reports/dcat_us_3_brief/BRIEF.md reports/dcat_us_3_brief/ROWS.md >/dev/null 2>&1 \
  || { echo "FAIL the DCAT files no longer pass the lint"; fail=1; }
"$PY" scripts/dcat_faq_lint.py reports/concise/REPORT.md >/dev/null 2>&1 || { echo "FAIL REPORT.md fails the lint"; fail=1; }
"$PY" scripts/build_evidence_map.py --check >/dev/null 2>&1 || { echo "FAIL docs/evidence/claims.yaml drifts"; fail=1; }

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
