#!/usr/bin/env bash
. "$(dirname "$0")/check_protected_lib.sh"
# The protected paths of `cc_tasks/2026-10-07_seed_known_locations_verify.md` with its
# `_ADDENDUM_01.md`, asserted against the commit the operator-launched session started from
# (`BASE`, default `512c1315`), so the check means the same thing before the task's commits and
# after.
#
# The base task's byte-identical list: "every rule, collector, `manners.py`, `scripts/score.py`,
# every prior payload, every task file". ADDENDUM_01 A admits `run.py` and `runner.py` for
# exactly two things (A13 collection, D1's terms read): they are NAMED here, with their diff,
# which the RESULT quotes whole. The write set's shaped files are held to their shape:
# `targets.yaml` moves only in `declared_locations`, and every `read_from` the recollection wrote
# is kept; the part 1 seed table moves only in `status` and `verified_at`; `params.yaml` moves
# only `cycle.name` and gains only `d1_sources.terms_text_max_bytes`. To that, the standing ones:
# every event shard and the Seldon store only GROW.
set -u
cd "$(dirname "$0")/.." || exit 2
BASE="${1:-512c1315}"
fail=0

# 1. Collectors, manners, score.py, and every rule module: byte-identical; none added.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet "$BASE" -- "$f"; then echo "FAIL protected file changed: $f"; fail=1; fi
done < <( { command git ls-tree -r --name-only "$BASE" -- assessment/harness/scan/collectors/ \
              assessment/harness/scan/rules/ | grep '\.py$'
            printf '%s\n' assessment/harness/scan/manners.py scripts/score.py; } )
added=$(git diff --name-only --diff-filter=A "$BASE" -- assessment/harness/scan/collectors/ \
          assessment/harness/scan/rules/ | grep -c '\.py$' || true)
if [ "$added" -ne 0 ]; then echo "FAIL $added collector or rule module(s) added"; fail=1; fi

# 2. The two admitted files, named with their diff (ADDENDUM_01 A).
for f in assessment/harness/scan/run.py assessment/harness/scan/runner.py; do
  n=$(git diff "$BASE" -- "$f" | grep -c '^[-+][^-+]' || true)
  echo "note: admitted change $f ($n changed line(s)); diff: git diff $BASE -- $f"
done

# 3. params.yaml, targets.yaml, the part 1 seed table: held to their shape.
if ! BASE="$BASE" /opt/anaconda3/bin/python3 - <<'PY'
import os, subprocess, sys, yaml
base = os.environ["BASE"]
def at(path):
    return yaml.safe_load(subprocess.run(["git", "show", f"{base}:{path}"], capture_output=True,
                                         text=True, check=True).stdout)
def now(path):
    return yaml.safe_load(open(path, encoding="utf-8"))
bad = []
# params.yaml
P = "assessment/harness/scan/params.yaml"
old, new = at(P), now(P)
ALLOWED_MOVED, ALLOWED_NEW = {"params.cycle.name"}, {"params.d1_sources.terms_text_max_bytes"}
def walk(a, b, path):
    if isinstance(a, dict):
        if not isinstance(b, dict):
            bad.append(path); return
        for k, v in a.items():
            if k not in b:
                bad.append(f"{path}.{k} (removed)")
            else:
                walk(v, b[k], f"{path}.{k}")
        for k in b:
            if k not in a and f"{path}.{k}" not in ALLOWED_NEW:
                bad.append(f"{path}.{k} (new key outside the write set)")
    elif a != b and path not in ALLOWED_MOVED:
        bad.append(path)
walk(old, new, "params")
if new["cycle"]["name"] != "scan_2026-10-07_seeded":
    bad.append("params.cycle.name is not the task's cycle")
# targets.yaml: everything but declared_locations unchanged; every recollection read_from kept.
T = "assessment/harness/scan/targets.yaml"
old, new = at(T), now(T)
for k in set(old) | set(new):
    if k != "declared_locations" and old.get(k) != new.get(k):
        bad.append(f"targets.yaml {k} moved")
if new["declared_locations"]["scheme"] != 2:
    bad.append("targets.yaml declared_locations is not scheme 2")
for code, b in old["declared_locations"]["bodies"].items():
    nb = new["declared_locations"]["bodies"].get(code) or {}
    if (nb.get("unresolved") or []) != (b.get("unresolved") or []):
        bad.append(f"targets.yaml {code}.unresolved moved")
    if bool(nb.get("department_is_own_host")) != bool(b.get("department_is_own_host")):
        bad.append(f"targets.yaml {code}.department_is_own_host moved")
    api, napi = b.get("api_base") or {}, nb.get("api_base") or {}
    if api.get("read_from") and (napi.get("url") != api["url"] or
                                 napi.get("read_from") != api["read_from"]):
        bad.append(f"targets.yaml {code}.api_base read_from not kept")
    if api.get("terms_read_from") and napi.get("terms_read_from") != api["terms_read_from"]:
        bad.append(f"targets.yaml {code}.api_base.terms_read_from not kept")
    for field in ("inventory_urls", "changelog_urls"):
        kept = {(e["url"], repr(e.get("read_from"))) for e in nb.get(field) or []}
        for e in b.get(field) or []:
            if (e["url"], repr(e.get("read_from"))) not in kept:
                bad.append(f"targets.yaml {code}.{field} {e['url']} read_from not kept")
# The part 1 seed table: statuses and verified_at only.
S = "assessment/harness/scan/seeds/known_locations_2026-10-07.yaml"
def strip(t):
    for b in t["bodies"].values():
        for seeds in b["objects"].values():
            for e in seeds:
                e.pop("status", None); e.pop("verified_at", None)
    return t
if strip(at(S)) != strip(now(S)):
    bad.append("the part 1 seed table moved outside status and verified_at")
for x in bad:
    print(f"FAIL {x}")
sys.exit(1 if bad else 0)
PY
then fail=1; fi

# 4. No stored payload, matrix or task file that BASE holds moved.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if ! git diff --quiet "$BASE" -- "$f"; then echo "FAIL a prior record changed: $f"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- state/ docs/reports/ cc_tasks/ \
           | grep -E '^state/scan_[^/]*\.json$|^docs/reports/scan_matrix_|^cc_tasks/[^/]*\.md$')

# 5. Every event shard BASE holds only grows, and the Seldon store is append-only.
while IFS= read -r f; do
  [ -z "$f" ] && continue
  removed=$(git diff "$BASE" -- "$f" | grep -c '^-[^-]' || true)
  if [ "$removed" -ne 0 ]; then echo "FAIL $f lost or changed $removed line(s)"; fail=1; fi
done < <(command git ls-tree -r --name-only "$BASE" -- events/ seldon_events.jsonl \
           | grep -E '^events/[^/]*\.jsonl$|^seldon_events\.jsonl$')

if [ "$fail" -eq 0 ]; then echo "PROTECTED PATHS: PASS"; else echo "PROTECTED PATHS: FAIL"; fi
exit "$fail"
