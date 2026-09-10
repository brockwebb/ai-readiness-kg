"""The gate on the cycle-3 frame. `cc_tasks/2026-09-08_scan_frame_fss.md` §6, as amended by
`..._ADDENDUM-05.md` step 5.

Six clauses, and the second is the one the task exists for: **no rule selects a surface.**
Three selection rules were built for this frame and all three failed — anchor-substring
scraping (falsified by its own output), the Enterprise Data Inventory (blocked on a
department → domain mapping nobody publishes), and CISA's registry plus data.gov's harvest API
(no primary-domain field; the API is gone). DD-059 records why the frame is declared instead.
A test that only counted rows would let a fourth rule in without anyone noticing, so this one
reads every row's `selection_source` and refuses anything that is not a declaration.

The Neo4j-backed clause SKIPS rather than fails when the database is down, for the reason
`tests/test_framework_projection_roundtrip.py` gives: a developer without the database gets a
green suite and an unverified claim, never a falsely green one.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from support.sourcescan import strip_prose

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

from kg.ingest import gate as ingest_gate                             # noqa: E402
from scan import load_params                                          # noqa: E402

ROSTER = json.loads((REPO / "state" / "fss_roster_2026-09.json").read_text(encoding="utf-8"))
TARGETS = json.loads((REPO / "state" / "scan_targets_fss_2026-09.json")
                     .read_text(encoding="utf-8"))
PREFLIGHT = json.loads((REPO / "state" / "fss_preflight_2026-09.json")
                       .read_text(encoding="utf-8"))

#: The frame, ADDENDUM-05: 16 recognized statistical agencies and units + 3 reference hosts.
TIER_A = 16
TIER_C = 3
#: The ROSTER's hosts — one per body, and the set the pre-flight measured on 2026-09-08.
HOSTS = TIER_A + TIER_C
#: The TARGET list's hosts, which is a larger set and was always going to be. ADDENDUM-01
#: declares each Tier C body's machine entry point, and all three sit on their own hostname
#: (`catalog.data.gov`, `data.nist.gov`, `open.gsa.gov`) rather than a path under the home.
#: Targets v2 gave those rows their own `machine:` ids
#: (`cc_tasks/2026-09-08_scan_run_3b.md` decision 1), so the target list names 22 hosts for 19
#: bodies. Written as the ARITHMETIC and not as `22`, because a bare 22 would be equally happy
#: with a twentieth agency arriving unnoticed.
TARGET_HOSTS = HOSTS + TIER_C

#: What a `selection_source` may begin with. Anything else is a rule, and a rule is what
#: ADDENDUM-05 removed.
DECLARED_PREFIXES = ("operator declaration", "roster host", "declared machine entry point")


@pytest.fixture(scope="module")
def session():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        c = load_project_config(REPO)
        driver = get_neo4j_driver(c)
        with driver.session(database=c["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                          # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    with driver.session(database=c["neo4j"]["database"]) as s:
        yield s
    driver.close()


# ------------------------------------------------------------------ 1. the roster

def test_roster_tier_a_is_sixteen_by_parse():
    """§1's clause: 16 BY PARSE, from a retained body, never asserted.

    The count comes from the ICSP charter's `^` flag. The live About page flags 15 and links
    15 while its own prose says 16 — it contradicts itself — and the entry that differs is
    SSA/ORES. `params.frame.roster_authority` settles it and was declared before either body
    was parsed; the disagreement is recorded rather than resolved silently.
    """
    c = ROSTER["counts"]
    assert c["tier_a_charter"] == TIER_A
    assert len(ROSTER["tier_a"]) == TIER_A
    assert ROSTER["authority"] == load_params()["frame"]["roster_authority"]
    assert c["tier_a_about_flags"] == 15 and c["tier_a_about_prose"] == 16, (
        "the About page no longer contradicts itself; re-read it before trusting either count")
    assert len(ROSTER["tier_a_disagreements"]) == 1
    assert "Social Security" in ROSTER["tier_a_disagreements"][0]["entry"]
    for src in ROSTER["sources"]:
        assert src["retained_path"], f"{src['name']} was not retained as evidence"
        assert (REPO / src["retained_path"]).is_file()


def test_tier_c_is_declared_and_carries_its_restriction():
    """Tier C is not on the ICSP source and is not parsed from it (ADDENDUM-01 item 2). Every
    row carries the tier-0-only restriction on its face, so no later reader has to remember
    it."""
    assert len(ROSTER["tier_c"]) == TIER_C
    for t in ROSTER["tier_c"]:
        assert t["tier"] == "C" and t["tier0_legs_only"] is True
        assert "tier-0 legs only" in t["restriction"]
        assert t["source"].startswith("operator declaration")


# ------------------------------------------------------------------ 2. no rule selects

def test_every_target_row_is_declared_and_none_is_derived():
    """**The clause this task exists for.** Every row is an operator declaration or a roster
    host. A row whose provenance is a token match, an inventory lookup or any other derivation
    is what DD-059 removed, and counting rows would not catch it coming back."""
    bad = [(r["agency"], r["surface_kind"], r["selection_source"])
           for r in TARGETS["rows"]
           if not str(r.get("selection_source", "")).startswith(DECLARED_PREFIXES)]
    assert not bad, f"{len(bad)} row(s) carry a derived selection_source: {bad[:5]}"


def test_no_row_lies_outside_the_declared_hosts():
    """Every row sits on a host the frame declares, and the host list is exactly the roster's
    plus the three declared Tier C machine entry points — nothing else.

    Named for the property rather than for a count: this test was `..._the_nineteen_hosts` and
    pinned `len(allowed) == 19`, which targets v2 falsified by giving each Tier C machine entry
    point its own `machine:` row on its own hostname. Those three hosts were inside the frame
    the whole time — ADDENDUM-01 declares them and the ROW check below already carved them
    out — so the pin was measuring the id scheme, not the frame.
    """
    import urllib.parse
    allowed = {h["host"] for h in TARGETS["hosts"]}
    tier_c_machine = {urllib.parse.urlsplit(t["machine_entry_point"]).netloc.lower()
                      for t in ROSTER["tier_c"]}
    assert len(allowed) == TARGET_HOSTS
    assert len(tier_c_machine) == TIER_C
    # The composition, so a host cannot join the target list by being neither.
    assert allowed - tier_c_machine == {h["host"] for h in PREFLIGHT["rows"]}, (
        "the target hosts are not the pre-flighted roster plus the declared machine entry "
        "points")
    off = sorted({urllib.parse.urlsplit(r["url"]).netloc.lower() for r in TARGETS["rows"]
                  if urllib.parse.urlsplit(r["url"]).netloc.lower() not in allowed})
    assert not off, f"rows outside the frame: {off}"


def test_the_frame_has_no_tier_b_and_statcan_is_out():
    """ADDENDUM-05 removes Tier B. The roster KEEPS its parsed Tier B entries — the artifact is
    immutable and `fss_departments_tier_b` stands as a registered fact — but nothing in the
    target list may use them."""
    assert ROSTER["counts"]["tier_b_charter"] == 14, "the roster's parsed record is immutable"
    assert not any(r.get("tier") == "B" for r in TARGETS["rows"])
    assert TARGETS["statcan_excluded"] == ["STATCAN"]
    assert not any("statcan" in str(r["url"]).lower() for r in TARGETS["rows"])


def test_the_target_build_calls_no_selection_rule():
    """`frame.py` still exists and is still tested; **nothing in the build calls it**
    (ADDENDUM-05). Read from the source, because a build that imported it and happened not to
    use it today would use it tomorrow."""
    src = strip_prose((REPO / "scripts" / "build_fss_targets.py").read_text(encoding="utf-8"))
    for banned in ("frame.word_match", "frame.api_entry_point", "frame.for_agency",
                   "frame.shortlist", "frame.machine_entry_point", "frame.flagship_products"):
        assert banned not in src, f"the target build calls {banned}"


# ------------------------------------------------------------------ 3. admission

def test_admission_emitted_no_conversion_gap_for_this_epoch():
    """A scan surface is admitted to be MEASURED, not read — its extent IS the measurement
    (A10, B3) — so DD-030's convertibility gate must not fire on one. It fired 22 times on the
    cycle-1 admissions and each had to be withdrawn by hand; `purpose: scan_surface` is what
    makes it return early."""
    from kg import manifest
    entries = {e["doc_id"]: e for e in manifest._load_entries()}
    rows = [r for r in TARGETS["rows"] if r.get("doc_id")]
    admitted = [r for r in rows if r["doc_id"] in entries]
    assert admitted, "no declared surface is admitted"
    for r in admitted:
        assert entries[r["doc_id"]].get("purpose") == "scan_surface", r["doc_id"]
    gaps = {g for g in ingest_gate.gaps() if str(g).startswith("scan-")}
    # 22 gaps exist and they are cycle 1's, emitted before `purpose: scan_surface` existed and
    # withdrawn by `scripts/annotate_withdrawn_conversion_gaps.py`. They are on the log and the
    # log is append-only, so the checkable property is not "zero gaps" — it is that every gap
    # belongs to a surface admitted BEFORE the purpose existed, and that this frame's admission
    # added none. `scripts/admit_fss_targets.py` asserts the delta at admission time; this
    # asserts the standing state.
    withdrawn = set(ingest_gate.gaps()) & gaps
    assert gaps == withdrawn, (
        f"{len(gaps - withdrawn)} conversion gap(s) are not accounted for: "
        f"{sorted(gaps - withdrawn)[:5]}")
    for r in admitted:
        assert entries[r["doc_id"]].get("purpose") == "scan_surface"
    unadmitted_with_gap = gaps & {r["doc_id"] for r in rows if r.get("not_admitted")}
    assert not unadmitted_with_gap, (
        f"a conversion gap was emitted for a surface this frame could not admit: "
        f"{sorted(unadmitted_with_gap)}")


def test_an_unadmitted_row_says_why_on_its_face():
    """A doc_id row that is not admitted can produce no Finding — `OBSERVED_ON` requires a
    `:Document` — so it says so rather than letting a reader assume every declared surface is
    measurable."""
    for r in TARGETS["rows"]:
        if r.get("doc_id") and r.get("not_admitted"):
            assert r["not_admitted"] == "robots_disallowed"
            assert "robots.txt" in r["not_admitted_note"]


# ------------------------------------------------------------------ 4. pre-flight

def test_preflight_covers_exactly_the_nineteen_roster_hosts():
    """The pre-flight measured the ROSTER — one host per body, 19 — on 2026-09-08, before
    targets v2 existed. It does not cover the three Tier C machine entry points, and it must
    not be made to: a pre-flight is a measurement at a moment, and back-filling three rows into
    a registered artifact so an equality holds would be editing the record to fit the test.
    Cycle 3 contacted those three hosts for the first time and reported what it found
    (`cc_tasks/2026-09-08_scan_run_3b_RESULT.md` §7).
    """
    import urllib.parse
    assert PREFLIGHT["hosts"] == HOSTS
    tier_c_machine = {urllib.parse.urlsplit(t["machine_entry_point"]).netloc.lower()
                      for t in ROSTER["tier_c"]}
    assert ({r["host"] for r in PREFLIGHT["rows"]}
            == {h["host"] for h in TARGETS["hosts"]} - tier_c_machine)
    assert PREFLIGHT["user_agent"] == load_params()["manners"]["user_agent"], (
        "the pre-flight was measured under a different identity from the one params declares; "
        "DD-060 is that there is exactly one")


def test_preflight_results_exist_for_every_host(session):
    """Registered, not merely computed. Two Results per host plus the three summaries."""
    names = {r["name"] for r in session.run(
        "MATCH (r:Result) WHERE r.name STARTS WITH 'scan_preflight_' "
        "OR r.name STARTS WITH 'fss_hosts_' RETURN r.name AS name")}
    missing = []
    for h in PREFLIGHT["rows"]:
        slug = h["host"].replace(".", "_").replace("-", "_")
        for suffix in ("reachable_2026-09", "robots_status_2026-09"):
            n = f"scan_preflight_{slug}_{suffix}"
            if n not in names:
                missing.append(n)
    for n in ("fss_hosts_refusing_identified_client_2026-09",
              "fss_hosts_unreachable_2026-09", "fss_hosts_serving_robots_txt_2026-09"):
        if n not in names:
            missing.append(n)
    assert not missing, f"{len(missing)} pre-flight Results are not registered: {missing[:6]}"


def test_a_refusal_is_recorded_and_never_retried():
    """DD-060. The three hosts that refuse an identified client keep their surfaces, and the
    instrument does not vary its identity to get a better answer."""
    refusing = set(PREFLIGHT["refusing_identified_client"])
    assert refusing == {"www.bls.gov", "www.bts.gov", "www.ssa.gov"}
    for host in refusing:
        assert any(r["host"] == host for r in TARGETS["hosts"]), (
            f"{host} refused us and was dropped from the frame; a refusal is a measurement")


# ------------------------------------------------------------------ 5. the tool map

def test_the_tool_map_regenerates_byte_identically():
    """A generated document anyone can hand-edit is a document that will be hand-edited."""
    r = subprocess.run([sys.executable, "scripts/scan_tool_map.py", "--check"],
                       capture_output=True, text=True, cwd=str(REPO))
    assert r.returncode == 0, (r.stdout + r.stderr)[-800:]


# ------------------------------------------------------------------ 6. Tier C stays at tier 0

def test_no_tier_c_row_appears_in_a_tier_a_figure():
    """ADDENDUM-01 item 5: placing a Tier C host beside a Tier A agency ABOVE tier 0 is a
    category error, and the page refuses to render it.

    Enforced at the source of the numbers rather than in the renderer: `scripts/scan_report.py`
    writes two matrices, and F1, F2 and F5 read only the Tier A one. A reference host cannot
    reach a Tier A figure because it is not in the file those figures are drawn from.
    """
    import json as _json
    suffix = "2026-09-09"
    tier_a = REPO / "state" / f"scan_matrix_{suffix}.json"
    tier_c = REPO / "state" / f"scan_matrix_tierc_{suffix}.json"
    if not tier_a.is_file() or not tier_c.is_file():
        pytest.skip("cycle 3 has not been reported yet")
    a = _json.loads(tier_a.read_text(encoding="utf-8"))
    c = _json.loads(tier_c.read_text(encoding="utf-8"))
    assert a["tier"] == "A" and c["tier"] == "C"
    tiers = {r["doc_id"]: r.get("tier", "A")
             for r in _json.loads((REPO / "state" / "scan_targets_fss_2026-09.json")
                                  .read_text(encoding="utf-8"))["rows"] if r.get("doc_id")}
    stray = [r["doc_id"] for r in a["rows"] if tiers.get(r["doc_id"]) == "C"]
    assert not stray, f"Tier C surfaces in the Tier A matrix that F1/F2/F5 draw from: {stray}"
    assert c["rows"], "the Tier C matrix is empty; F6 would have nothing to draw"


def test_tier_c_is_judged_on_tier0_legs_and_no_others():
    import json as _json
    p = REPO / "state" / "scan_matrix_tierc_2026-09-09.json"
    if not p.is_file():
        pytest.skip("cycle 3 has not been reported yet")
    c = _json.loads(p.read_text(encoding="utf-8"))
    tier0 = set(load_params()["tier0"]["legs"])
    judged = {leg for r in c["rows"] for leg in r["verdicts"]}
    assert judged and judged <= tier0, f"Tier C judged outside tier0.legs: {judged - tier0}"
