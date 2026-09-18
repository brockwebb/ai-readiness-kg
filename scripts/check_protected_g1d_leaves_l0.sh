#!/bin/sh
. "$(dirname "$0")/check_protected_lib.sh"
# The protected-paths diff for cc_tasks/2026-09-15_g1d_leaves_l0.md + ADDENDUM_01.
#
# Base "Zero edits to": rule modules other than removing G1-D from leg lists (the module stays,
# with a docstring line), stored payloads, the log's existing shards, prior Results' values and
# states, prior RESULTs, figures, section prose, corpus/.
# ADDENDUM_01 moves into the write set: the report source, the three matrices, the fragments,
# results_tagged.json, the PDF and the G1-D Results' STATES.
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

say "STORED PAYLOADS — the history does not move (decision 2). Not one byte under state/"
must_be_empty "a stored payload changed" state/

say "THE LOG's existing shards — this task appends the framework write-back and nothing else"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import subprocess, sys
from pathlib import Path
REPO = Path("/Users/brock/GitHub/ai-readiness-kg")
tracked = [r for r in subprocess.run(["git", "ls-files", "events/"], capture_output=True,
                                     text=True, cwd=REPO).stdout.split() if r.endswith(".jsonl")]
bad, grew = [], []
for rel in tracked:
    was = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, cwd=REPO)
    if was.returncode:
        continue
    now = (REPO / rel).read_bytes()
    if not now.startswith(was.stdout):
        bad.append(rel)
    elif len(now) > len(was.stdout):
        grew.append(f"{rel}: +{len(now) - len(was.stdout)} bytes")
print("   appended to:", grew or "none")
print(f"   {len(tracked) - len(grew) - len(bad)} shard(s) byte-identical, {len(bad)} rewritten")
allowed = {"events/batch-033_framework.jsonl"}
stray = [g.split(":")[0] for g in grew if g.split(":")[0] not in allowed]
if bad or stray:
    print(f"   VIOLATION: rewritten={bad} unexpected_append={stray}")
    sys.exit(1)
PY

say "figures, corpus/ and the framework SKELETON"
must_be_empty "a figure changed" assessment/harness/scan/figures.py \
  assessment/harness/scan/figures.yaml assessment/harness/scan/figures
must_be_empty "corpus changed" corpus/
must_be_empty "the skeleton changed" framework/ai_readiness_framework_skeleton.md

say "rule modules — only rule_g1d.py may move, and only its DOCSTRING"
git status --porcelain -- assessment/harness/scan/rules/ | sed 's/^...//' \
  | grep -v '^assessment/harness/scan/rules/rule_g1d\.py$' \
  && { echo "   VIOLATION: a rule module other than rule_g1d.py changed"; fail=1; }
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import ast, subprocess, sys
REL = "assessment/harness/scan/rules/rule_g1d.py"
REPO = "/Users/brock/GitHub/ai-readiness-kg"
def code(src):
    t = ast.parse(src)
    for n in ast.walk(t):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b = n.body
            if b and isinstance(b[0], ast.Expr) and isinstance(b[0].value, ast.Constant) \
                    and isinstance(b[0].value.value, str):
                n.body = b[1:] or [ast.Pass()]
    return ast.dump(ast.fix_missing_locations(t))
was = subprocess.run(["git", "show", f"HEAD:{REL}"], capture_output=True, text=True,
                     cwd=REPO).stdout
now = open(f"{REPO}/{REL}", encoding="utf-8").read()
if code(was) != code(now):
    print("   VIOLATION: rule_g1d.py's CODE changed; only the docstring may move")
    sys.exit(1)
print("   rule_g1d.py: docstring only, code byte-identical under AST")
PY

say "prior RESULTs and prior cc_task files"
must_be_empty "a prior RESULT or task file changed" \
  'cc_tasks/2026-09-14*' 'cc_tasks/2026-09-13*' 'cc_tasks/2026-09-12*' \
  'cc_tasks/2026-09-11*' 'cc_tasks/2026-09-10*' 'cc_tasks/2026-09-09*' \
  'cc_tasks/2026-09-08*' 'cc_tasks/2026-09-07*' 'cc_tasks/2026-09-06*' \
  'cc_tasks/2026-09-15_claude_md_cites_dn005*' 'cc_tasks/2026-09-15_standing_dispatcher*'

say "docs/ — the report, its PDF, the matrices, the fragments and the data this task owns"
# `docs/data/ai_readiness_framework.json` and `docs/data/index.json` are here because
# decision 3 edits the framework RECORD, and the site publishes a byte copy of it plus a
# manifest that hashes the copy's source. ADDENDUM_01's write set does not enumerate them —
# nobody had noticed the copy follows the record — and leaving them stale would publish a
# copy and a digest contradicting the record this task just wrote.
# `tests/test_publication.py` is what caught it, which is the check doing its job.
git status --porcelain -- docs/ | sed 's/^...//' \
  | grep -vE '^(docs/reports/2026-09_fss_ai_readiness_L0\.(md|pdf)|docs/reports/sections/[0-9]+_[a-z]+\.md|docs/reports/scan_matrix_[A-Za-z]+_2026-09-10_rj2\.(json|csv)|docs/reports/generated/[A-Za-z0-9_]+\.md|docs/data/(results_tagged|ai_readiness_framework|index)\.json|docs/design_decisions\.md|docs/design/2026-09-1[456]_DN-00[456].*\.md)$' \
  && { echo "   VIOLATION: a published doc changed that this task does not own"; fail=1; }

say "the published framework COPY equals the record, and the manifest hashes the record"
/opt/anaconda3/bin/python3 - <<'COPYCHK' || fail=1
import hashlib, json, sys
from pathlib import Path
REPO = Path("/Users/brock/GitHub/ai-readiness-kg")
src = REPO / "framework" / "ai_readiness_framework.json"
dst = REPO / "docs" / "data" / "ai_readiness_framework.json"
digest = hashlib.sha256(src.read_bytes()).hexdigest()
idx = json.loads((REPO / "docs" / "data" / "index.json").read_text(encoding="utf-8"))
rec = next((c["sha256"] for c in idx["copies"]
            if c["source"] == "framework/ai_readiness_framework.json"), None)
print(f"   record {digest[:12]}  copy "
      f"{hashlib.sha256(dst.read_bytes()).hexdigest()[:12]}  manifest {str(rec)[:12]}")
if dst.read_bytes() != src.read_bytes() or rec != digest:
    print("   VIOLATION: the published copy or the manifest digest drifted from the record")
    sys.exit(1)
COPYCHK

say "NO OTHER CYCLE's matrices move — only the snapshot's were rebuilt"
must_be_empty "a matrix for another cycle changed" 'docs/reports/scan_matrix_*_2026-09-09*'

say "publication.yaml — the snapshot does NOT move (ADDENDUM_01: the report is a view)"
must_be_empty "publication.yaml changed" docs/reports/publication.yaml

say "prior Results — five withdrawn, two registered, every other value and state unmoved"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import sys
sys.path.insert(0, "/Users/brock/GitHub/seldon")
from pathlib import Path
WITHDRAWN = ["scan_l0_g1_d_pass_2026-09-10_rj2",
             "scan_l0_g1_d_applicable_n_2026-09-10_rj2",
             "scan_l0_host_leg_rate_g1_d_upper95_2026-09-10_rj2",
             "scan_l0_home_flagship_disagreement_cells_2026-09-10_rj2",
             "scan_l0_home_flagship_disagreement_bodies_2026-09-10_rj2"]
NEW = ["scan_l0_home_flagship_disagreement_cells_over_four_legs_2026-09-10_rj2",
       "scan_l0_home_flagship_disagreement_bodies_over_four_legs_2026-09-10_rj2"]
try:
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(Path("/Users/brock/GitHub/ai-readiness-kg"))
    d = get_neo4j_driver(cfg)
    with d.session(database=cfg["neo4j"]["database"]) as s:
        total = s.run("MATCH (r:Result) RETURN count(r)").single()[0]
        states = {r["st"]: r["n"] for r in s.run(
            "MATCH (r:Result) RETURN coalesce(r.state,'<none>') AS st, count(*) AS n")}
        w = {r["name"]: r["state"] for r in s.run(
            "MATCH (r:Result) WHERE r.name IN $n RETURN r.name AS name, r.state AS state",
            n=WITHDRAWN)}
        nw = {r["name"]: (r["state"], r["value"]) for r in s.run(
            "MATCH (r:Result) WHERE r.name IN $n "
            "RETURN r.name AS name, r.state AS state, r.value AS value", n=NEW)}
    d.close()
except Exception as exc:                                            # noqa: BLE001
    print(f"   SKIPPED: Neo4j unreachable ({exc})")
    sys.exit(0)
print(f"   Results total {total}; states {states}")
print(f"   withdrawn -> {w}")
print(f"   newly registered -> {nw}")
bad = []
if total != 7264:
    bad.append(f"total is {total}, expected 7264 (7262 + the two new names)")
if states.get("published") != 54:
    bad.append(f"published is {states.get('published')}, expected 54 (59 - 5 withdrawn)")
if any(v != "stale" for v in w.values()) or len(w) != 5:
    bad.append(f"the five withdrawals are not all stale: {w}")
if len(nw) != 2:
    bad.append(f"the two new Results are not both registered: {nw}")
if bad:
    print("   VIOLATION: " + "; ".join(bad))
    sys.exit(1)
PY

say "the report carries NO G1-D column and no host-level G1-D rate"
/opt/anaconda3/bin/python3 - <<'PY' || fail=1
import json, sys
from pathlib import Path
REPO = Path("/Users/brock/GitHub/ai-readiness-kg")
bad = []
for stem in ("tierA", "tierC", "product"):
    d = json.loads((REPO / "docs" / "reports"
                    / f"scan_matrix_{stem}_2026-09-10_rj2.json").read_text(encoding="utf-8"))
    if "G1-D" in d["legs"]:
        bad.append(f"{stem} still carries the G1-D column")
    if "G1-D" not in [w["leg"] for w in d.get("legs_withdrawn", [])]:
        bad.append(f"{stem} does not record the withdrawal in its metadata")
    if any("G1-D" in r["verdicts"] for r in d["rows"]):
        bad.append(f"{stem} has a G1-D verdict on a row")
md = (REPO / "docs" / "reports" / "2026-09_fss_ai_readiness_L0.md").read_text(encoding="utf-8")
lines = md.splitlines()
app = next(i for i, l in enumerate(lines) if l.startswith("## Method appendix"))
prose = sum(l.count("G1-D") for i, l in enumerate(lines)
            if i <= app and not l.lstrip().startswith("|"))
print(f"   G1-D in the report BODY's prose: {prose} (the withdrawal sentence); "
      f"DD-066 citations: {md.count('DD-066')}")
print(f"   G1-D in the METHOD APPENDIX's tables: "
      f"{sum(l.count('G1-D') for i, l in enumerate(lines) if i > app)} "
      f"(the record of what the cycle measured; decision 2 keeps it)")
if prose != 1:
    bad.append(f"the report body's prose mentions G1-D {prose} times, expected 1")
if md.count("DD-066") != 1:
    bad.append("the withdrawal sentence does not cite DD-066 exactly once")
for token in ("{{result:scan_l0_g1_d", "{{result:scan_l0_host_leg_rate_g1_d"):
    if token in "".join((REPO / "docs" / "reports" / "sections" / f).read_text(encoding="utf-8")
                        for f in ("10_frame.md", "20_matrix.md")):
        bad.append(f"the source still tags {token}")
if bad:
    print("\n".join(f"   VIOLATION: {b}" for b in bad))
    sys.exit(1)
PY

echo
echo "-- what this task DOES change, declared rather than diffed away"
git status --porcelain -- assessment/harness/scan/params.yaml assessment/harness/scan/run.py \
  assessment/harness/scan/rules/rule_g1d.py framework/ai_readiness_framework.json \
  scripts/ tests/ docs/ events/batch-033_framework.jsonl seldon_events.jsonl \
  'cc_tasks/2026-09-15_g1d_leaves_l0*' | sed 's/^/   /'
echo
echo "protected paths: $([ $fail -eq 0 ] && echo PASS || echo FAIL)"
exit $fail
