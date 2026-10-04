#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-10-02_commerce_guidance_admission.md` (+ ADDENDUM-01),
# asserted against HEAD.
#
#   "Byte-identical: everything else, including docs/brief/, docs/deck/, framework/, and every
#    file in the FSS repository."
#
# Paths that moved and that the task file's write set does not name, each reported in the RESULT:
#
#   * scripts/admit_commerce_guidance.py — the admission, as a reviewable script (the
#     admit_tool_docs pattern) rather than a one-off shell line.
#   * scripts/run_commerce_extraction.py — the one-document chunked driver: the runner the task
#     names refuses the bulk_v038 profile (anchor contract, chunk-unit).
#   * scripts/fss_airkg_reconciliation.py, scripts/fss_screen_2026-10-02.yaml — decisions 5, 6, 10.
#   * scripts/check_protected_commerce_admission.sh — this file.
#   * events/batch-022.jsonl — the extraction_request (`python -m kg queue add`).
#   * state/spend_ledger.jsonl and four state/*_2026-10-02.json run records.
#   * events/raw/bulk_v038/<doc>.c00NN.*.json — the 25 raw responses (CLAUDE.md invariant 1).
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
DOC=generative-ai-and-open-data-guidelines-and-best-practices-de
FSS="$HOME/GitHub/icsp_notebook"

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Untouched outright.
for p in 'docs/brief/' 'docs/deck/' 'framework/' 'docs/reports/' 'kg/' 'assessment/' 'mcp/' \
         'controls.yaml' 'seldon.yaml' 'dixie_evidence.yaml' 'docs/design/' \
         'docs/design_decisions.md' 'docs/data/'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. Every path that moved is on the list.
ALLOWED=(
  'corpus/evidence/decisions.jsonl'
  'corpus/manifest.json'
  'docs/evidence/claims.yaml'
  'docs/evidence/kg_questions.md'
  'docs/evidence/kg_questions.yaml'
  'docs/research/2026-10-02_commerce_guidance_glossary_terms.csv'
  'docs/research/2026-10-02_commerce_guidance_two_pipelines.md'
  'docs/research/2026-10-02_fss_vs_airkg_corpus_reconciliation.csv'
  'docs/research/2026-10-02_fss_vs_airkg_corpus_reconciliation.md'
  'events/batch-001.jsonl'
  'events/batch-022.jsonl'
  'events/batch-023.jsonl'
  'scripts/admit_commerce_guidance.py'
  'scripts/check_protected_commerce_admission.sh'
  'scripts/fss_airkg_reconciliation.py'
  'scripts/fss_screen_2026-10-02.yaml'
  'scripts/run_commerce_extraction.py'
  'state/commerce_guidance_extraction_2026-10-02.json'
  'state/commerce_two_pipelines_2026-10-02.json'
  'state/definition_lookup_audit_2026-10-02.json'
  'state/fss_vs_airkg_reconciliation_2026-10-02.json'
  'state/spend_ledger.jsonl'
  'tests/test_commerce_guidance_admission.py'
  'cc_tasks/2026-10-02_commerce_guidance_admission_RESULT.md'
)
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    events/raw/bulk_v038/"$DOC".c00[0-9][0-9].87068818f5c4.0.3.8.claude-opus-5.json) continue ;;
  esac
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$path" = "$a" ] && ok=1 && break; done
  if [ "$ok" -eq 0 ]; then echo "FAIL path outside the write set moved: $path"; fail=1; fi
done < <(changed_and_new .)

# 3. Event shards and the ledgers are append-only: no line removed or changed.
for f in events/batch-001.jsonl events/batch-022.jsonl events/batch-023.jsonl \
         corpus/evidence/decisions.jsonl state/spend_ledger.jsonl seldon_events.jsonl; do
  removed=$(git diff HEAD -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done

# 4. The FSS repository: no tracked file changed, and the source PDF still hashes as admitted.
if [ -n "$(git -C "$FSS" diff --name-only HEAD)" ]; then
  echo "FAIL tracked files changed in $FSS"; git -C "$FSS" diff --name-only HEAD | sed 's/^/       /'
  fail=1
fi
sha=$(shasum -a 256 "$FSS/corpus/research/doc_genai_open_data_2025.pdf" | cut -d' ' -f1)
if [ "$sha" != "87068818f5c4c86f1a211cd2375738646ed586c0ca7211d5bd9604636493bd91" ]; then
  echo "FAIL the FSS copy hashes to $sha"; fail=1
fi

# 5. Prior RESULTs and task files unchanged.
moved=$(git diff --name-only HEAD -- 'cc_tasks/')
if [ -n "$moved" ]; then echo "FAIL tracked cc_tasks files changed:"; echo "$moved"; fail=1; fi

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
