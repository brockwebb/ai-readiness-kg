#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The write set of `cc_tasks/2026-09-18_rejudge_seven_legs.md`, asserted against HEAD.
#
#   "the shard (append), docs/reports/scan_matrix_*_<cycle>_rjN.json, the L0 Results (append,
#    proposed), state/<cycle>_rjN.json, the projection, scripts/check_protected_rejudge.sh
#    (new), seldon_events.jsonl, the RESULT. publication.yaml, the report, the PDF, the site's
#    published Results, framework/, prior payloads: byte-identical."
#
# Paths the write set does not name. Each is reported in the RESULT §5 with the reason, and
# each is asserted below to be the only other thing that moved:
#
#   * `scan/reread.py` (new), `rederive.py` and `collectors/dcat.py`: the seven legs and D4-v3
#     read blocks no stored Observation carries. The re-judgement re-reads them from the
#     retained bodies (DD-067 §2), and the re-derivation gate re-reads the same way.
#     `dcat.membership_block` is `fetch_catalog`'s block, factored out so there is one copy.
#   * `run.py` records `surface_legs` on a measured payload (DD-067 §3); `rederive.py` honours it.
#   * `scripts/rejudge_seven_legs.py` (new), and `state/rejudgement_diff_2026-09-18.json`, its
#     record, as `rejudge_gen10.py` wrote `state/rejudgement_diff_2026-09-13.json`.
#   * `scripts/build_l0_matrices.py`: product columns per cycle, B5 once per body, and no report
#     fragment written for a cycle that is not the snapshot. `scripts/snapshot_successor.py`
#     compares the union of the two cycles' product columns. `scripts/prescriptions.py --cycle`.
#   * `docs/design_decisions.md`: DD-067, appended.
#   * `tests/test_rejudge_seven_legs.py` (new). Three test files gain the new payload:
#     `test_scan_harness_v4.py`, `test_rejudgements_on_the_log.py` and `test_standing_guards.py`.
#     The last two now admit an unpaired Finding only on a leg the predecessor never judged.
#   * three pages GENERATED from the graph, which publishing `_rj4` moved. Each is one line,
#     each is its generator's own output, and the suite's drift check on each went red until it
#     was regenerated: `docs/data/sources_per_check.json` (D4 `rules` 2 -> 3, since RULE-D4-v3
#     now has Findings on the graph; `build_l0_site.py --only sources_per_check`),
#     `docs/design/mcp_over_the_graph.md` (`current_rules` 16 -> 24; `mcp/airkg_doc.py`), and
#     `docs/design/scan_tool_map.md` (`dcat`'s entry points name `membership_block`;
#     `scripts/scan_tool_map.py`).
set -u
cd "$(dirname "$0")/.." || exit 2
fail=0
PY=/opt/anaconda3/bin/python3
NEW=scan_2026-09-10_rj4

changed_and_new() {
  { git diff --name-only HEAD -- "$@"; git ls-files --others --exclude-standard -- "$@"; } \
    | sed '/^$/d' | sort -u
}

# 1. Byte-identical outright: the published report and everything the site serves, the record,
#    the corpus, the rules, the params, the controls.
for p in 'docs/reports/publication.yaml' 'docs/reports/generated/' 'docs/index.html' \
         'docs/crosswalk/' 'docs/research/' 'framework/' 'corpus/' 'kg/' \
         'assessment/harness/scan/rules/' 'assessment/harness/scan/params.yaml' \
         'assessment/harness/scan/runner.py' 'assessment/harness/scan/manners.py' \
         'assessment/harness/scan/model.py' 'assessment/harness/scan/publish.py' \
         'assessment/harness/scan/fixtures/' 'assessment/harness/scan/collectors/v2clauses.py' \
         'controls.yaml' 'dixie_evidence.yaml' 'seldon.yaml' 'CITATION.cff' '.zenodo.json'; do
  moved=$(changed_and_new "$p")
  if [ -n "$moved" ]; then
    echo "FAIL protected path moved: $p"; echo "$moved" | sed 's/^/       /'; fail=1
  fi
done

# 2. The report and its PDF: whatever is under docs/reports/ that is not a new rj4 matrix.
moved=$(changed_and_new 'docs/reports/' | grep -vE "^docs/reports/scan_matrix_(tierA|tierC|product)_2026-09-10_rj4\.(json|csv)$")
if [ -n "$moved" ]; then
  echo "FAIL the report, its PDF or a prior matrix moved"; echo "$moved" | sed 's/^/       /'; fail=1
fi
for k in tierA tierC product; do
  for e in json csv; do
    f="docs/reports/scan_matrix_${k}_2026-09-10_rj4.$e"
    [ -f "$f" ] || { echo "FAIL missing $f"; fail=1; }
  done
done

# 2b. docs/data/: the appendix alone, and only its D4 `rules` count. Nothing the site publishes
#     as a Result (`results_tagged.json`), no copy, no manifest.
moved=$(changed_and_new 'docs/data/')
if [ "$moved" != "docs/data/sources_per_check.json" ]; then
  echo "FAIL docs/data/ moved other than the appendix:"; echo "$moved" | sed 's/^/       /'; fail=1
fi
dd=$(git diff --unified=0 HEAD -- docs/data/sources_per_check.json | grep -E '^[-+] ' )
if [ "$dd" != "$(printf '%s\n%s' '-   "rules": 2,' '+   "rules": 3,')" ]; then
  echo "FAIL the appendix moved other than one rules count:"; echo "$dd" | sed 's/^/       /'; fail=1
fi

# 3. state/: exactly the new payload and its diff record, both new; every prior payload untouched.
moved=$(changed_and_new 'state/')
want=$(printf '%s\n' "state/$NEW.json" "state/rejudgement_diff_2026-09-18.json" | sort)
if [ "$moved" != "$want" ]; then
  echo "FAIL state/ moved other than the new payload and its record:"; echo "$moved" | sed 's/^/       /'; fail=1
fi
if [ -n "$(git diff --name-only HEAD -- state/)" ]; then
  echo "FAIL a tracked payload under state/ was modified"; fail=1
fi

# 4. events/: one new shard, every committed shard's bytes a prefix of what is on disk.
new_shards=$(git ls-files --others --exclude-standard -- events/ | sort)
if [ "$new_shards" != "events/cycle-$NEW.jsonl" ]; then
  echo "FAIL events/ gained other than events/cycle-$NEW.jsonl:"; echo "$new_shards" | sed 's/^/       /'; fail=1
fi
"$PY" - <<'PYEOF' || fail=1
import subprocess, sys
from pathlib import Path
tracked = [r for r in subprocess.run(["git", "ls-files", "events/"], capture_output=True,
                                     text=True).stdout.split() if r.endswith(".jsonl")]
bad, grew = [], []
for rel in tracked:
    was = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True)
    if was.returncode:
        continue
    now = Path(rel).read_bytes()
    if not now.startswith(was.stdout):
        bad.append(rel)
    elif len(now) > len(was.stdout):
        grew.append(rel)
print(f"   events/: {len(tracked)} tracked shard(s); {len(grew)} appended to {grew}; "
      f"{len(bad)} rewritten {bad}")
sys.exit(1 if bad or grew else 0)
PYEOF

# 5. Every path that moved is on the list.
ALLOWED=(
  'assessment/harness/scan/reread.py'
  'assessment/harness/scan/rederive.py'
  'assessment/harness/scan/run.py'
  'assessment/harness/scan/collectors/dcat.py'
  'scripts/rejudge_seven_legs.py'
  'scripts/build_l0_matrices.py'
  'scripts/snapshot_successor.py'
  'scripts/prescriptions.py'
  'scripts/check_protected_rejudge.sh'
  'docs/design_decisions.md'
  'docs/data/sources_per_check.json'
  'docs/design/mcp_over_the_graph.md'
  'docs/design/scan_tool_map.md'
  'tests/test_standing_guards.py'
  'tests/test_rejudge_seven_legs.py'
  'tests/test_scan_harness_v4.py'
  'tests/test_rejudgements_on_the_log.py'
  "state/$NEW.json"
  'state/rejudgement_diff_2026-09-18.json'
  "events/cycle-$NEW.jsonl"
  'seldon_events.jsonl'
  'cc_tasks/2026-09-18_rejudge_seven_legs_RESULT.md'
)
for k in tierA tierC product; do
  for e in json csv; do ALLOWED+=("docs/reports/scan_matrix_${k}_2026-09-10_rj4.$e"); done
done
while IFS= read -r path; do
  [ -z "$path" ] && continue
  ok=0
  for a in "${ALLOWED[@]}"; do [ "$path" = "$a" ] && ok=1 && break; done
  if [ $ok -eq 0 ]; then echo "FAIL moved and not in the write set: $path"; fail=1; fi
done < <(changed_and_new '.')

# 6. No prior RESULT or task file edited (the lib admits untracked task files only).
moved=$(git diff --name-only HEAD -- 'cc_tasks/')
if [ -n "$moved" ]; then
  echo "FAIL a tracked task or RESULT file changed"; echo "$moved" | sed 's/^/       /'; fail=1
fi

# 7. The snapshot stays `_rj2` (decision 3).
snap=$("$PY" -c "import yaml;print(yaml.safe_load(open('docs/reports/publication.yaml'))['snapshot_cycle'])")
[ "$snap" = "scan_2026-09-10_rj2" ] || { echo "FAIL snapshot_cycle is $snap"; fail=1; }

if [ $fail -eq 0 ]; then echo "PROTECTED PATHS OK"; else echo "PROTECTED PATHS FAIL"; fi
exit $fail
