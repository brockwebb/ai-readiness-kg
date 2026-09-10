"""Targets v5: the seven declared flagships, and what must remain true after they enter.

`cc_tasks/2026-09-10_scan_frame_v5.md` §3. Three things are checked and each has a history:

* **v4 is not edited.** Three cycles of Findings hang off v4's rows. v5 is a new file whose
  first 65 rows are v4's, identical and in order, so a diff shows exactly what was added.
* **Every added surface is same-site to its body.** The site bound is DD-063's site key. A
  declaration that resolved off-site would bind a contact this frame never declared, which is
  the defect the site key replaced the Public Suffix List to avoid.
* **The synthetic id scheme has ONE definition.** `flagship:` is the fourth prefix. The third
  was added to two of three copies of the prefix list and 957 observations were counted as
  missing Documents; the list now lives in `scan.model` and the readers import it.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

from scan.manners import netloc_of, same_site                       # noqa: E402
from scan.model import SYNTHETIC_PREFIXES                           # noqa: E402
from support.sourcescan import strip_prose                          # noqa: E402

V4 = REPO / "state" / "scan_targets_fss_2026-09.json"
V5 = REPO / "state" / "scan_targets_fss_2026-09_v5.json"
VERIFICATION = REPO / "state" / "fss_flagship_verification_2026-09-10.json"

#: The seven netlocs §1 permits this task to contact, and the per-netloc ceiling: one
#: robots.txt read, one HEAD, one GET. A fourth request to any of them, or one request to
#: anything else, is a manners failure and this is where it surfaces.
MAX_REQUESTS_PER_NETLOC = 3


def _json(p: Path) -> dict:
    if not p.is_file():
        pytest.skip(f"{p.relative_to(REPO)} not built")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def v4():
    return _json(V4)


@pytest.fixture(scope="module")
def v5():
    return _json(V5)


@pytest.fixture(scope="module")
def verification():
    return _json(VERIFICATION)


# ------------------------------------------------------------------ 1. v4 is not edited

def test_v5_carries_every_v4_row_unchanged_and_in_order(v4, v5):
    n = len(v4["rows"])
    assert v5["rows"][:n] == v4["rows"], (
        "v5 changed a row it inherited; three cycles of Findings are attached to those "
        "doc_ids and COMPUTED_FROM means read, not rewrite")
    assert v5["targets_version"] == 5 and v5["derived_from_version"] == 4


def test_v4_still_records_the_seven_as_pending(v4):
    """v4 is a record of what was true when cycle 3 measured, and stays one."""
    assert sorted(v4["agencies_pending_operator_declaration"]) == [
        "BLS", "BTS", "DRSMSU", "NAHMSAPHIS", "NCES", "ORES", "SAMHSACBHS"]


# ------------------------------------------------------------------ 2. what was added

def test_exactly_the_declared_bodies_gained_a_flagship(v4, v5):
    added = [r for r in v5["rows"][len(v4["rows"]):]]
    assert {r["surface_kind"] for r in added} == {"flagship"}
    assert sorted(r["agency"] for r in added) == sorted(
        v4["agencies_pending_operator_declaration"])
    assert v5["agencies_pending_operator_declaration"] == []


def test_every_added_surface_is_same_site_to_its_body(v4, v5):
    """The gate's own clause. The key is the body's, never the page's."""
    keys = {h["agency"]: h["site_key"] for h in v5["hosts"]}
    for r in v5["rows"][len(v4["rows"]):]:
        assert same_site(r["url"], keys[r["agency"]]), (
            f"{r['agency']}'s flagship {r['url']} is not on {keys[r['agency']]}")
        if r.get("verified_final_url"):
            assert same_site(r["verified_final_url"], keys[r["agency"]]), (
                f"{r['agency']}'s flagship redirects off its own site")


def test_a_refused_declaration_still_entered_and_says_so(v4, v5):
    """Decision 1. Dropping the surfaces of the hosts that refuse us would restrict the
    instrument to the hosts that permit us — the worst sampling rule an accessibility
    assessment can have."""
    refused = [r for r in v5["rows"][len(v4["rows"]):] if r.get("refused_at_declaration")]
    assert sorted(r["agency"] for r in refused) == ["BLS", "BTS", "ORES"]
    for r in refused:
        assert r["verified_status"] == 403


def test_the_added_ids_are_synthetic_and_distinct(v4, v5):
    added = v5["rows"][len(v4["rows"]):]
    ids = [r["doc_id"] for r in added]
    assert len(set(ids)) == len(ids), "two flagships share an id"
    assert all(i.startswith("flagship:") for i in ids)
    assert all(i.startswith(SYNTHETIC_PREFIXES) for i in ids)
    assert not (set(ids) & {r["doc_id"] for r in v4["rows"]})


# ------------------------------------------------------------------ 3. the id scheme, once

def test_the_synthetic_prefix_list_has_one_definition():
    """`flagship:` is the fourth prefix. The third went into two copies of three and 957
    observations of ordinary host surfaces were counted as missing Documents."""
    from scan import publish, run
    assert publish.SYNTHETIC_PREFIXES is SYNTHETIC_PREFIXES
    assert run.SYNTHETIC_PREFIXES is SYNTHETIC_PREFIXES
    assert "flagship:" in SYNTHETIC_PREFIXES
    hits = []
    for py in sorted((REPO / "assessment").rglob("*.py")) + \
            sorted((REPO / "scripts").glob("*.py")):
        if py.name == "model.py":
            continue
        code = strip_prose(py.read_text(encoding="utf-8"), literals=False)
        if '"host:", "home:"' in code:
            hits.append(str(py.relative_to(REPO)))
    assert not hits, f"a second copy of the prefix list is back, in {hits}"


def test_publish_runs_as_a_script_and_not_only_as_a_module():
    """`publish.py` is both, and only one of them was covered.

    The `flagship:` change gave it `from .model import SYNTHETIC_PREFIXES`. Every test imports
    this file as `scan.publish`, where a relative import is fine; the cycle runs it as
    `python assessment/harness/scan/publish.py`, where it raises `ImportError: attempted
    relative import with no known parent package`. The fast tier was green and the publish step
    of cycle 4 was not — after the run, with the payload written and 2,718 Observations waiting
    to reach the log. A dual-entry-point file needs its second entry point tested.
    """
    import subprocess
    r = subprocess.run([sys.executable, str(REPO / "assessment" / "harness" / "scan" /
                                            "publish.py"), "--help"],
                       capture_output=True, text=True, cwd=REPO)
    assert r.returncode == 0, f"publish.py cannot be run as a script:\n{r.stderr[-600:]}"


# ------------------------------------------------------------------ 4. the manners of §1

def test_the_verification_contacted_only_the_seven_declared_pages(verification):
    declared = {netloc_of(r["url"]) for r in verification["rows"]}
    assert len(declared) == 7
    contacted = set(verification["requests_per_netloc"])
    assert contacted == declared, (
        f"contacted a netloc §1 does not permit: {sorted(contacted - declared)}")
    for host, n in verification["requests_per_netloc"].items():
        assert n <= MAX_REQUESTS_PER_NETLOC, (
            f"{host} was asked {n} times; §1 permits robots.txt, HEAD and GET")


def test_every_declared_page_has_a_recorded_status(verification):
    assert len(verification["rows"]) == 7
    for r in verification["rows"]:
        assert r["status"] is not None, f"{r['body']} has no status; §3 requires one"
        assert r["final_url"] and r["same_site"]
        assert r["robots_permits"] is True, (
            f"{r['body']}: robots must be READ and permit the page before it is fetched")


def test_no_declaration_was_substituted(verification):
    """Decision 2. The declared URL is the surface; a redirect is recorded beside it, never
    written over it."""
    declared = {r["body"]: r["url"] for r in verification["rows"]}
    doc = _json(V5)
    for r in doc["rows"]:
        if r["surface_kind"] == "flagship" and r["agency"] in declared:
            if r.get("verified_at"):
                assert r["url"] == declared[r["agency"]]


# ------------------------------------------------------------------ 5. the builder derives

def test_the_v5_build_calls_no_frame_derivation():
    """Same ban as v4's builder carries. Nothing in this frame is derived by rule; every
    surface is a roster host or an operator declaration."""
    src = strip_prose((REPO / "scripts" / "build_fss_targets_v5.py").read_text(encoding="utf-8"))
    for banned in ("frame.word_match", "frame.api_entry_point", "frame.for_agency",
                   "frame.shortlist", "frame.machine_entry_point", "frame.flagship_products"):
        assert banned not in src, f"the v5 build calls {banned}"
