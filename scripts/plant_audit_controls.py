#!/usr/bin/env python3
"""Plant three blind controls into a scratch copy of HEAD, for the full-project audit.

`cc_tasks/2026-10-04_full_audit.md` decision 6: "Three planted defects, placed by script in a
scratch copy before the audit reads (a claim with a wrong locator, a test with no assertion, a
number in a figure caption that is off by one), and the audit reports whether it caught each.
Planted defects are removed before the RESULT and never committed."

Why a copy and not the checkout: the plants must never be committable, and the readers must see
a tree that differs from HEAD in exactly the three planted files. `git archive HEAD` gives the
committed tree byte for byte, with nothing untracked and nothing gitignored.

Why random placement and a sealed manifest: the session that writes this script knows the three
*kinds* of plant (they are in the task file). It must not know *where* they are until the
audit's findings are frozen, or the control measures nothing. The draw uses `secrets` unless a
seed is given (a seed is for this script's own re-runs, never for the audit), and the manifest,
which records every location, is written outside the copy where the readers are pointed.

Modes:
  plant   --dest DIR --manifest FILE      copy HEAD to DIR, plant three, write FILE
  remove  --dest DIR --manifest FILE      check the plants are still as written, delete DIR,
                                          and confirm the checkout's three files equal HEAD

Exit codes: 0 ok; 2 precondition refused; 3 a plant could not be placed or verified.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import secrets
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The three plant targets, by the task's own wording. Paths are repository-relative.
CLAIMS_PATH = "docs/evidence/claims.yaml"
TESTS_GLOB = "tests/test_*.py"
CAPTIONS_GLOB = "docs/figures/*.caption.md"

# A claim locator into the framework record, `framework/ai_readiness_framework.json#ind:A7`.
# Re-pointing one at a different real indicator is the subtle wrong locator: it still resolves.
LOCATOR_RE = re.compile(r"^(\s+locator: framework/ai_readiness_framework\.json#ind:)([A-Z]\d+)\s*$")
CLAIM_ID_RE = re.compile(r"^- id: (CL-\d+)\s*$")

# A bare integer in caption prose: not part of a word, a decimal, a path, a range, a date or a
# hex id. Four-digit 19xx/20xx tokens are excluded as years.
CAPTION_INT_RE = re.compile(r"(?<![\w.#:/,-])(\d{1,6})(?![\w.:/,%-])")
YEAR_RE = re.compile(r"^(19|20)\d\d$")

# The planted test. It exercises real code paths of the standard library and asserts nothing,
# which is the defect: it can only fail by raising.
TEST_TEMPLATE = '''

def test_{stem}_payload_round_trip_is_stable(tmp_path):
    import json as _json

    payload = {{"id": "{stem}", "values": [1, 2, 3], "nested": {{"ok": True}}}}
    path = tmp_path / "{stem}_round_trip.json"
    path.write_text(_json.dumps(payload, sort_keys=True))
    reread = _json.loads(path.read_text())
    reread == payload
'''


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _refuse(msg: str) -> int:
    print(f"REFUSED: {msg}", file=sys.stderr)
    return 2


def _git_head() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, check=True,
                          capture_output=True, text=True).stdout.strip()


def _copy_head(dest: Path) -> None:
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=REPO_ROOT,
                             check=True, capture_output=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)


def _plant_claim_locator(dest: Path, rng: random.Random) -> dict:
    path = dest / CLAIMS_PATH
    lines = path.read_text().splitlines(keepends=True)
    sites, claim, known = [], None, set()
    for i, line in enumerate(lines):
        m = CLAIM_ID_RE.match(line)
        if m:
            claim = m.group(1)
        m = LOCATOR_RE.match(line.rstrip("\n"))
        if m:
            known.add(m.group(2))
            if claim:
                sites.append((i, claim, m.group(2)))
    if not sites or len(known) < 2:
        raise RuntimeError(f"{CLAIMS_PATH}: no indicator locators to re-point")
    i, claim, old = rng.choice(sites)
    new = rng.choice(sorted(known - {old}))
    m = LOCATOR_RE.match(lines[i].rstrip("\n"))
    lines[i] = f"{m.group(1)}{new}\n"
    path.write_text("".join(lines))
    return {"kind": "claim_wrong_locator", "path": CLAIMS_PATH, "line": i + 1, "claim": claim,
            "was": f"ind:{old}", "now": f"ind:{new}"}


def _plant_test_no_assert(dest: Path, rng: random.Random) -> dict:
    files = sorted(p for p in dest.glob(TESTS_GLOB) if "\ndef test_" in p.read_text())
    if not files:
        raise RuntimeError(f"{TESTS_GLOB}: no test module to plant into")
    path = rng.choice(files)
    stem = path.stem.removeprefix("test_")
    text = path.read_text()
    func = TEST_TEMPLATE.format(stem=stem)
    path.write_text(text.rstrip("\n") + "\n" + func)
    first = len(text.rstrip("\n").splitlines()) + 3
    return {"kind": "test_no_assertion", "path": str(path.relative_to(dest)), "line": first,
            "function": f"test_{stem}_payload_round_trip_is_stable"}


def _plant_caption_off_by_one(dest: Path, rng: random.Random) -> dict:
    sites = []
    for path in sorted(dest.glob(CAPTIONS_GLOB)):
        for ln, line in enumerate(path.read_text().splitlines(keepends=True)):
            for m in CAPTION_INT_RE.finditer(line):
                if not YEAR_RE.match(m.group(1)):
                    sites.append((path, ln, m.start(1), m.end(1), m.group(1)))
    if not sites:
        raise RuntimeError(f"{CAPTIONS_GLOB}: no caption integer to perturb")
    path, ln, a, b, old = rng.choice(sites)
    lines = path.read_text().splitlines(keepends=True)
    new = str(int(old) + 1)
    lines[ln] = lines[ln][:a] + new + lines[ln][b:]
    path.write_text("".join(lines))
    return {"kind": "caption_number_off_by_one", "path": str(path.relative_to(dest)),
            "line": ln + 1, "was": old, "now": new}


def plant(dest: Path, manifest: Path, seed: int | None) -> int:
    dest, manifest = dest.resolve(), manifest.resolve()
    if dest.exists():
        return _refuse(f"{dest} exists; the copy must be fresh")
    if REPO_ROOT in dest.parents or dest == REPO_ROOT:
        return _refuse(f"{dest} is inside the checkout; plants must never be committable")
    if dest in manifest.parents:
        return _refuse("the manifest must be outside the copy the readers are pointed at")
    seed = secrets.randbits(64) if seed is None else seed
    rng = random.Random(seed)
    _copy_head(dest)
    plants = []
    for fn in (_plant_claim_locator, _plant_test_no_assert, _plant_caption_off_by_one):
        try:
            plants.append(fn(dest, rng))
        except RuntimeError as exc:
            print(f"PLANT FAILED: {exc}", file=sys.stderr)
            return 3
    for p in plants:
        p["sha256_planted"] = _sha(dest / p["path"])
    record = {"written_at": datetime.now(timezone.utc).isoformat(), "head": _git_head(),
              "dest": str(dest), "seed": seed, "plants": plants}
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(record, indent=2) + "\n")
    print(f"planted 3 controls in {dest}; manifest sealed at {manifest} (not printed)")
    return verify_copy(dest, plants)


def verify_copy(dest: Path, plants: list[dict]) -> int:
    """The copy must differ from HEAD in exactly the planted files, or it is not the tree the
    audit claims to have read. Compared through git's own object hashes, file by file."""
    planted = {p["path"] for p in plants}
    tracked = subprocess.run(["git", "ls-tree", "-r", "HEAD"], cwd=REPO_ROOT, check=True,
                             capture_output=True, text=True).stdout.splitlines()
    expected = {}
    for row in tracked:
        meta, rel = row.split("\t", 1)
        mode, kind, oid = meta.split()
        if kind != "blob" or mode == "120000":
            continue
        if not (dest / rel).is_file():
            print(f"VERIFY FAILED: {rel} missing from the copy", file=sys.stderr)
            return 3
        expected[rel] = oid
    rels = sorted(expected)
    hashed = subprocess.run(["git", "hash-object", "--no-filters", "--stdin-paths"], check=True,
                            input="\n".join(str(dest / r) for r in rels) + "\n",
                            capture_output=True, text=True).stdout.split()
    if len(hashed) != len(rels):
        print(f"VERIFY FAILED: hashed {len(hashed)} of {len(rels)} files", file=sys.stderr)
        return 3
    changed = [r for r, h in zip(rels, hashed) if h != expected[r]]
    if sorted(changed) != sorted(planted):
        print(f"VERIFY FAILED: planted {sorted(planted)}, changed {sorted(changed)}", file=sys.stderr)
        return 3
    print(f"verified: copy differs from HEAD in exactly the {len(changed)} planted file(s)")
    return 0


def remove(dest: Path, manifest: Path) -> int:
    dest, manifest = dest.resolve(), manifest.resolve()
    if not manifest.exists():
        return _refuse(f"no manifest at {manifest}")
    record = json.loads(manifest.read_text())
    if Path(record["dest"]) != dest:
        return _refuse(f"manifest is for {record['dest']}, not {dest}")
    for p in record["plants"]:
        here = dest / p["path"]
        if not here.exists() or _sha(here) != p["sha256_planted"]:
            print(f"REMOVE CHECK FAILED: {p['path']} in the copy is not as planted", file=sys.stderr)
            return 3
    shutil.rmtree(dest)
    for p in record["plants"]:
        head_blob = subprocess.run(["git", "show", f"HEAD:{p['path']}"], cwd=REPO_ROOT,
                                   check=True, capture_output=True).stdout
        if (REPO_ROOT / p["path"]).read_bytes() != head_blob:
            print(f"REMOVE CHECK FAILED: checkout {p['path']} differs from HEAD", file=sys.stderr)
            return 3
    print(f"removed {dest}; the checkout's {len(record['plants'])} planted paths equal HEAD")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("mode", choices=["plant", "remove"])
    ap.add_argument("--dest", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=None,
                    help="for re-running this script only; an audit run leaves it unset")
    args = ap.parse_args(argv)
    if args.mode == "plant":
        return plant(args.dest, args.manifest, args.seed)
    return remove(args.dest, args.manifest)


if __name__ == "__main__":
    raise SystemExit(main())
