#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-19_g4_locators_and_progress_drift.md`, asserted against HEAD.
#
#   "docs/crosswalk/usafacts_operationalization_skeleton.md (G4's evidence cell only),
#    framework/ai_readiness_framework.json (through `save` only), docs/reports/ rebuilt products
#    that carry the G4 appendix rows, docs/progress/ only if decision 4's determinism fix changes
#    its bytes, scripts/framework_progress.py, tests/ (the grounding test for the two quotes; the
#    drift test), events/ and seldon_events.jsonl by the writers that own them, the RESULT.
#    state/, corpus/, assessment/harness/scan/rules/: byte-identical."
#
# Paths the write set does not name, each reported in the RESULT §6 with its reason, each listed
# in ALLOWED below and nowhere else:
#
#   * `CITATION.cff`, `.zenodo.json`, `docs/data/*` and `docs/sitemap.xml`, `docs/index.html`:
#     `scripts/build_l0_site.py` is the last step of the report rebuild the write set DOES name,
#     and these carry the digests and the build date of the files it rebuilt. The write set said
#     "docs/reports/ rebuilt products" and the rebuild does not stop at docs/reports/.
#   * `scripts/check_protected_g4_locators.sh`: this file. Every task's protected-path check is
#     new, by construction.
#
# `docs/progress/` is asserted BYTE-IDENTICAL here and not merely allowed: decision 4 permits a
# change only as the consequence of a determinism fix, and the generator needed none — the fix
# it did need was to a status line that could not print a path outside the repository.
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Byte-identical outright: the instrument, every stored payload, the corpus, the progress page.
for p in 'kg/' 'assessment/' 'state/' 'corpus/' 'docs/progress/' 'docs/research/' \
         'docs/design/' 'docs/reports/scan_matrix_' 'docs/reports/sections/' \
         'docs/reports/publication.yaml' 'docs/data/results_tagged.json' \
         'docs/data/corpus_manifest.json' 'mcp/' 'Makefile' \
         'controls.yaml' 'dixie_evidence.yaml' 'seldon.yaml'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. The skeleton moved in exactly one row, and that row is G4's.
"$PY" - <<'PYEOF' || fail=1
import subprocess, sys
rel = "docs/crosswalk/usafacts_operationalization_skeleton.md"
was = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, text=True).stdout
now = open(rel, encoding="utf-8").read()
a, b = was.splitlines(), now.splitlines()
moved = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
ok = len(a) == len(b) and len(moved) == 1 and b[moved[0]].startswith("| G4 |")
print(f"   {rel}: {len(moved)} line(s) differ; lengths {len(a)} -> {len(b)}")
if not ok:
    print(f"FAIL the skeleton moved other than in G4's row alone: {moved[:5]}")
sys.exit(0 if ok else 1)
PYEOF

# 3. events/: no new shard; every committed shard a byte prefix of what is on disk; exactly one
#    shard appended to, with exactly the one event the single writer emits.
new_shards=$(git ls-files --others --exclude-standard -- events/)
if [ -n "$new_shards" ]; then
  echo "FAIL events/ gained a shard:"; echo "$new_shards" | sed 's/^/       /'; fail=1
fi
"$PY" - <<'PYEOF' || fail=1
import json, subprocess, sys
from pathlib import Path
want = {"events/batch-033_framework.jsonl": {"framework_writeback": 1}}
tracked = [r for r in subprocess.run(["git", "ls-files", "events/"], capture_output=True,
                                     text=True).stdout.split() if r.endswith(".jsonl")]
bad, grew = [], {}
for rel in tracked:
    was = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True).stdout
    now = Path(rel).read_bytes()
    if not now.startswith(was):
        bad.append(rel)
    elif len(now) > len(was):
        kinds = {}
        for line in now[len(was):].decode("utf-8").splitlines():
            t = json.loads(line)["event_type"]
            kinds[t] = kinds.get(t, 0) + 1
        grew[rel] = kinds
print(f"   events/: {len(tracked)} tracked shard(s); appended {grew}; rewritten {bad}")
if bad or grew != want:
    print(f"FAIL events/: want exactly {want}")
    sys.exit(1)
PYEOF

# 4. The write-back dropped nothing: the event's own delta, read back off the shard.
"$PY" - <<'PYEOF' || fail=1
import json, sys
from pathlib import Path
line = Path("events/batch-033_framework.jsonl").read_text(encoding="utf-8").splitlines()[-1]
d = json.loads(line).get("delta") or json.loads(line).get("payload", {}).get("delta", {})
dropped = {k: v for k, v in d.items()
           if k in ("nodes_removed", "edges_removed", "counts_keys_dropped") and v}
print(f"   framework_writeback delta: {json.dumps(d, sort_keys=True)}")
if dropped:
    print(f"FAIL the write-back dropped something: {dropped}")
    sys.exit(1)
PYEOF

# 5. Every path that moved is on the list.
ALLOWED=(
  '.zenodo.json' 'CITATION.cff'
  'docs/crosswalk/usafacts_operationalization_skeleton.md'
  'docs/data/CITATION.cff' 'docs/data/ai_readiness_framework.json' 'docs/data/index.json'
  'docs/data/sources_per_check.json' 'docs/data/zenodo.json'
  'docs/index.html' 'docs/sitemap.xml'
  'docs/reports/2026-09_fss_ai_readiness_L0.md' 'docs/reports/2026-09_fss_ai_readiness_L0.pdf'
  'docs/reports/generated/sources_per_check.md'
  'docs/reports/generated/2026-09_fss_ai_readiness_L0.build.md'
  'events/batch-033_framework.jsonl'
  'framework/ai_readiness_framework.json'
  'scripts/framework_progress.py' 'scripts/check_protected_g4_locators.sh'
  'tests/test_g4_locators_and_progress_drift.py'
  'cc_tasks/2026-09-19_g4_locators_and_progress_drift_RESULT.md'
)
while IFS= read -r path; do
  [ -z "$path" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$path" = "$a" ] && ok=1 && break; done
  if [ "$ok" = 0 ]; then echo "FAIL not in the write set: $path"; fail=1; fi
done < <({ git diff --name-only HEAD; git ls-files --others --exclude-standard; } | sort -u)

if [ "$fail" = 0 ]; then echo "PROTECTED PATHS OK"; fi
exit "$fail"
