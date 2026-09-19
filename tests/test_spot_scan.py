"""A spot scan: one body, on request, judged and published beside the frame's cycle of record.

`cc_tasks/2026-09-19_spot_scan.md`. Decisions 1 to 4 are pinned by the unit tests at the top —
the refusals first, because they are what stops a spot cycle standing in for the frame. The
module-scoped `loopback` fixture is decision 5: the spot path end to end over the loopback
control fixtures, into a throwaway tree, a throwaway event log and a scratch label set, and
nothing of it kept.

Loopback and a virtual clock (`cc_tasks/2026-09-10_virtual_time.md`): the fixtures are real
sockets on 127.0.0.1, the standing rate limit is not paid in wall time, and no federal host is
contacted anywhere in this file.
"""
from __future__ import annotations

import datetime as dt
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

from scan import load_params, spot                                   # noqa: E402

TODAY = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
SNAPSHOT = "scan_2026-09-10_rj4"


def _payload(cycle: str, **extra) -> dict:
    return {"cycle": cycle, "findings_detail": [], "control_findings_detail": [],
            "observations_detail": [], **extra}


# ============================================================ decision 1: the name

def test_a_spot_is_named_spot_body_day_and_several_bodies_are_multi():
    assert spot.spot_name(["BEA"], "2026-09-20") == "spot_bea_2026-09-20"
    assert spot.spot_name(["data.gov"], "2026-09-20") == "spot_data.gov_2026-09-20"
    assert spot.spot_name(["NCHS", "BEA"], "2026-09-20") == "spot_multi_2026-09-20"
    assert spot.spot_name(["BEA"], "2026-09-20", rerun="b") == "spot_bea_2026-09-20b"
    assert not spot.spot_name(["BEA"]).startswith("scan_")
    with pytest.raises(SystemExit):
        spot.spot_name([])
    with pytest.raises(SystemExit):
        spot.spot_name(["BEA"], "2026-09-20", rerun="a1")


def test_a_spot_payload_named_scan_is_refused():
    """The failure decision 1 exists to prevent, refused at every place a name meets a payload:
    the writer, the log and the matrices."""
    p = _payload("scan_2026-09-20", scope="spot", spot_targets=["BEA"])
    with pytest.raises(SystemExit, match="not named `spot_"):
        spot.check_identity("scan_2026-09-20", p)
    from scan import publish
    with pytest.raises(SystemExit, match="not named `spot_"):
        publish.write_events(p, Path("state/scan_2026-09-20.json"))
    with pytest.raises(SystemExit, match="not named `spot_"):
        publish.write_supersession(p, Path("state/scan_2026-09-20.json"))


def test_a_spot_name_on_a_frame_payload_and_an_unparseable_name_are_refused():
    with pytest.raises(SystemExit, match="does not carry `scope: spot`"):
        spot.check_identity("spot_bea_2026-09-20", _payload("spot_bea_2026-09-20"))
    with pytest.raises(SystemExit, match="does not parse"):
        spot.check_identity("spot_bea", _payload("spot_bea", scope="spot", spot_targets=["BEA"]))
    with pytest.raises(SystemExit, match="no `spot_targets`"):
        spot.check_identity("spot_bea_2026-09-20", _payload("x", scope="spot"))
    # A frame cycle, measured or re-judged, passes untouched.
    spot.check_identity("scan_2026-09-10_rj4", _payload("scan_2026-09-10_rj4"))
    spot.check_identity("spot_bea_2026-09-20_rj1",
                        _payload("spot_bea_2026-09-20_rj1", scope="spot", spot_targets=["BEA"]))


def test_the_writer_refuses_a_misnamed_spot_and_a_second_spot_of_one_day(tmp_path):
    from scan import run
    params = load_params()
    p = _payload("spot_bea_2026-09-20", scope="spot", spot_targets=["BEA"], params_hash="x")
    with pytest.raises(SystemExit, match="not named `spot_"):
        run.write_payload(tmp_path / "scan_2026-09-20.json", p, params)
    run.write_payload(tmp_path / "spot_bea_2026-09-20.json", p, params)
    # Same params, same name: `refuse_clobber` alone would let this overwrite the first.
    with pytest.raises(SystemExit, match="--rerun b"):
        run.write_payload(tmp_path / "spot_bea_2026-09-20.json", p, params)


def test_target_restricts_the_frame_to_the_bodys_rows_with_the_frames_legs():
    from scan import run
    params = load_params()
    full = run.targets(params)
    bea = run.targets(params, ["bea"])
    assert bea and {t["agency"] for t in bea} == {"BEA"}
    want = [t for t in full if t["agency"] == "BEA"]
    # The same rows, each with exactly the legs the full frame gives it.
    assert bea == want
    assert run.canonical_bodies(params, ["bea", "NCHS"]) == ["BEA", "NCHS"]


def test_an_unknown_target_is_refused_before_anything_runs(monkeypatch):
    """`main` refuses before the control cycle: an unknown body costs nothing to refuse and
    would have cost the controls to discover afterwards. No fetch can have happened, because
    the refusal is raised by the argument check and the fixture servers are never started.

    `main` sets the cycle licence (`model.CYCLE_TOKEN_ENV`) before it parses anything, which is
    right for a cycle and wrong for a test process: left set, it would license every LATER test
    in the session to write into the committed evidence store. `setenv` first, so the
    monkeypatch undo removes whatever `main` wrote."""
    from scan import model, run
    monkeypatch.setenv(model.CYCLE_TOKEN_ENV, "")
    with pytest.raises(SystemExit, match="names no body in the frame"):
        run.main(["--target", "NOPE", "--evidence-root", "/nonexistent-spot-root"])
    with pytest.raises(SystemExit, match="measure no surface"):
        run.main(["--target", "BEA", "--controls-only"])
    with pytest.raises(SystemExit, match="second SPOT"):
        run.main(["--rerun", "b"])
    import os
    assert os.environ.get(model.CYCLE_TOKEN_ENV) == "1"      # main did license, as a cycle does


# ============================================================ decision 2: never the snapshot

def test_a_spot_named_as_snapshot_is_refused_by_every_reader(monkeypatch, tmp_path):
    pub = tmp_path / "publication.yaml"
    text = (REPO / "docs" / "reports" / "publication.yaml").read_text(encoding="utf-8")
    pub.write_text(text.replace(f"snapshot_cycle: {SNAPSHOT}",
                                "snapshot_cycle: spot_bea_2026-09-20"), encoding="utf-8")
    import build_l0_report
    import build_l0_site
    import prescriptions
    monkeypatch.setattr(build_l0_report, "PUBLICATION", pub)
    monkeypatch.setattr(build_l0_site, "PUBLICATION", pub)
    monkeypatch.setattr(prescriptions, "PUBLICATION", pub)
    for load in (build_l0_report.load_publication, build_l0_site.publication,
                 prescriptions.snapshot_cycle):
        with pytest.raises(SystemExit, match="never the snapshot|is a full cycle"):
            load()
    with pytest.raises(SystemExit, match="is a full cycle"):
        spot.refuse_as_snapshot("spot_bea_2026-09-20")
    spot.refuse_as_snapshot(SNAPSHOT)


def test_a_spot_writes_no_supersession_and_never_pairs_with_a_frame_cycle(tmp_path, monkeypatch):
    from kg import eventlog
    from scan import publish
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")
    p = _payload("spot_bea_2026-09-20", scope="spot", spot_targets=["BEA"])
    out = publish.write_supersession(p, tmp_path / "spot_bea_2026-09-20.json")
    assert out["supersession_events_written"] == 0 and out["supersedes"] is None
    assert not (tmp_path / "events").exists() or not any(
        json.loads(l)["event_type"] == publish.SUPERSEDES_EVENT
        for f in (tmp_path / "events").glob("*.jsonl") for l in f.read_text().splitlines())
    # The cross-scope pairing is refused in both directions. `supersedes_of` cannot produce it
    # from a well-formed name, so the predecessor payload is placed where it would be read.
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(publish, "REPO", tmp_path)
    (state / "scan_2026-09-20.json").write_text(json.dumps(
        _payload("scan_2026-09-20", scope="spot", spot_targets=["BEA"])))
    frame_rj = _payload("scan_2026-09-20_rj1", cycle_kind="rejudged",
                        derived_from="scan_2026-09-20")
    with pytest.raises(SystemExit, match="never supersede one another"):
        publish.write_supersession(frame_rj, state / "scan_2026-09-20_rj1.json")


def test_a_spots_events_say_spot_and_a_frame_cycles_do_not():
    from scan import publish
    f = publish.cycle_fields(_payload("spot_bea_2026-09-20", scope="spot",
                                      spot_targets=["BEA"]), "spot_bea_2026-09-20")
    assert f["scope"] == "spot" and f["spot_targets"] == ["BEA"]
    assert f["cycle_kind"] == "measured" and f["generation"] == 0 and "supersedes" not in f
    g = publish.cycle_fields(_payload(SNAPSHOT, cycle_kind="rejudged",
                                      derived_from="scan_2026-09-10"), SNAPSHOT)
    assert "scope" not in g and "spot_targets" not in g


def test_a_spot_rejudgement_stays_a_spot():
    from scan import rederive
    src = json.loads((REPO / "state" / "scan_2026-09-10.json").read_text(encoding="utf-8"))
    src = dict(src, cycle="spot_bea_2026-09-10", scope="spot", spot_targets=["BEA"],
               params_cycle="scan_2026-09-10",
               observations_detail=[o for o in src["observations_detail"]
                                    if "bea" in str(o.get("target_doc_id"))])
    out = rederive.rejudge(src, load_params())
    assert out["cycle"] == "spot_bea_2026-09-10_rj1"
    assert out["scope"] == "spot" and out["spot_targets"] == ["BEA"]
    spot.check_identity(out["cycle"], out)


def test_the_scratch_projection_prefix_cannot_name_a_real_label():
    from scan import publish
    for bad in ("Observation", "Find", "scratch_", "Scratch_", "ScratchX"):
        with pytest.raises(SystemExit, match="scratch label prefix"):
            publish.project(label_prefix=bad)


# ============================================================ decision 4: the template

def test_the_spot_template_renders_a_dispatchable_task_for_one_body(tmp_path):
    import render_spot_scan as R
    text, stem = R.render("BEA", dt.datetime(2026, 9, 20, 12, tzinfo=dt.timezone.utc))
    assert stem == "2026-09-20_spot_scan_bea"
    for header in ("**Spend:**", "**Network:**", "**Framework layer served"):
        assert header in text
    # The dispatcher's own parser, so "dispatchable" means what `seldon dispatch` reads.
    from seldon.core import dispatch as D
    net = D.parse_network(D.parse_headers(text)["Network"])
    assert net["kind"] == "allowlist" and net["error"] is None, net
    assert "www.bea.gov" in net["hosts"] and "127.0.0.1" in net["hosts"]
    assert "spot_bea_2026-09-20" in text and "--target BEA" in text
    import re
    assert not re.findall(r"\{[a-z_]+\}", text), "an unsubstituted field"
    assert (REPO / "cc_tasks" / "templates" / "scan_cycle.md").read_text().count("{target}") == 0


# ============================================================ decision 5: loopback end to end

#: The scratch frame. `BEA` is the body the spot names — served by the `body_two_products`
#: fixture, one port, two product pages — and `NCHS` is a second body the spot must NOT touch.
#: Real agency names so the views can set the spot beside the real snapshot; every URL is
#: 127.0.0.1, every doc id synthetic, and the whole tree is deleted when the module ends.
SPOT_BODY, OTHER_BODY = "BEA", "NCHS"


def _frame_rows(agency: str, base: str, products: tuple) -> list:
    netloc = base.split("//", 1)[1]
    rows = [{"agency": agency, "tier": "A", "host": netloc, "surface_kind": "well_known",
             "url": f"{base}/robots.txt", "doc_id": f"host:{netloc}"},
            {"agency": agency, "tier": "A", "host": netloc, "surface_kind": "home",
             "url": f"{base}/index.html", "doc_id": f"home:{netloc}"}]
    rows += [{"agency": agency, "tier": "A", "host": netloc, "surface_kind": "flagship",
              "url": f"{base}{p}", "doc_id": f"flagship:{netloc}{p}"} for p in products]
    return rows


@pytest.fixture(scope="module")
def loopback(tmp_path_factory):
    """The spot path, end to end, into a throwaway tree. Returns what each stage produced."""
    from kg import eventlog
    from scan import model, publish, rederive, run
    from scan.clock import VirtualClock
    from scan.fixtures.server import FixtureServer
    from scan.manners import Fetcher
    import build_l0_matrices as M
    import cycle_results

    root = tmp_path_factory.mktemp("spot_loopback")
    state, staging, committed = root / "state", root / "staging", root / "evidence"
    events, reports = root / "events", root / "reports"
    for d in (state, staging, committed, reports):
        d.mkdir()
    params = load_params()
    label_prefix = f"ScratchSpot{uuid.uuid4().hex[:8]}_"
    out: dict = {"root": root, "label_prefix": label_prefix}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(model, "EVIDENCE_ROOT", staging)
        mp.setattr(run, "STATE_DIR", state)
        mp.setattr(run, "MANIFEST", root / "manifest.json")
        mp.setattr(M, "STATE", state)
        mp.setattr(eventlog, "_EVENTS_DIR", events)
        (root / "manifest.json").write_text(json.dumps({"entries": {}}), encoding="utf-8")
        with FixtureServer("body_two_products") as base_a, FixtureServer("passes_all") as base_b:
            frame = {"rows": _frame_rows(SPOT_BODY, base_a, ("/index.html", "/second.html"))
                     + _frame_rows(OTHER_BODY, base_b, ("/index.html",))}
            (state / f"{params['cycle']['targets']}.json").write_text(
                json.dumps(frame), encoding="utf-8")
            out["other_netloc"] = base_b.split("//", 1)[1]

            # 1. run: validate the target, controls first, then the body's surfaces only.
            bodies = run.canonical_bodies(params, [SPOT_BODY.lower()])
            cycle = spot.spot_name(bodies)
            tgts = run.targets(params, bodies)
            cf, e5, control_obs, ok = run.run_controls(params, clock=VirtualClock())
            out["controls_ok"], out["e5"] = ok, e5
            assert ok, e5.reason
            payload = run.run_cycle(params, tgts, (cf, e5, control_obs),
                                    Fetcher(params, clock=VirtualClock()), task="test",
                                    evidence_root=str(staging), cycle=cycle,
                                    spot_targets=bodies)
            src = state / f"{cycle}.json"
            run.write_payload(src, payload, params)
            out["cycle"], out["targets"], out["src"] = cycle, tgts, src

        # 2. publish: evidence into a throwaway committed root, events into a throwaway log.
        payload = json.loads(src.read_text(encoding="utf-8"))
        out["promoted"] = publish.promote_evidence(payload, staging=staging,
                                                    committed=committed)
        src.write_text(json.dumps(payload, indent=1, default=str) + "\n", encoding="utf-8")
        out["events"] = publish.write_events(payload, src)
        out["supersession"] = publish.write_supersession(payload, src)
        out["payload"] = payload
        out["log"] = list(eventlog.replay())

        # 3. re-derivation, under the params the cycle was measured under.
        out["rederive"] = rederive.rederive(payload, params)

        # 4. projection into a scratch label set, then removed whatever happened.
        try:
            out["projection"] = publish.project(label_prefix=label_prefix)
            out["projected"] = _scratch_counts(label_prefix)
        finally:
            out["scratch_left"] = _drop_scratch(label_prefix)

        # 5. matrices, restricted to the bodies present, and the Result names they would take.
        c = M.compute(cycle, params)
        out["matrices"] = c
        M.write_matrices(c, out_dir=reports, fragments=False)
        cycle_results.check_names([cycle_results.name_for(b, cycle) for b, _v, _n in
                                   c["results"]], cycle)
        out["result_names"] = [cycle_results.name_for(b, cycle) for b, _v, _n in c["results"]]
    # The views read the snapshot's published matrices beside the spot's.
    for kind in ("tierA", "tierC", "product"):
        name = f"scan_matrix_{kind}_{SNAPSHOT.replace('scan_', '')}.json"
        shutil.copy(REPO / "docs" / "reports" / name, reports / name)
    out["reports"] = reports
    yield out
    shutil.rmtree(root, ignore_errors=True)


def _driver():
    from seldon.config import get_neo4j_driver, load_project_config
    cfg = load_project_config(REPO)
    return get_neo4j_driver(cfg), cfg["neo4j"]["database"]


def _scratch_counts(prefix: str) -> dict:
    driver, db = _driver()
    try:
        with driver.session(database=db) as s:
            return {l: s.run(f"MATCH (n:{prefix}{l}) RETURN count(n)").single()[0]
                    for l in ("Observation", "Finding", "Rule")}
    finally:
        driver.close()


def _drop_scratch(prefix: str) -> int:
    driver, db = _driver()
    try:
        with driver.session(database=db) as s:
            s.run(f"MATCH (n) WHERE n:{prefix}Observation OR n:{prefix}Finding OR "
                  f"n:{prefix}Rule DETACH DELETE n")
            return s.run(f"MATCH (n) WHERE n:{prefix}Observation OR n:{prefix}Finding OR "
                         f"n:{prefix}Rule RETURN count(n)").single()[0]
    finally:
        driver.close()


def _views(loopback, monkeypatch):
    """Every view pointed at the throwaway reports tree: the prescription query, the scoring
    model that reads through it, and the MCP tools, which load both by path."""
    import prescriptions
    import score
    sys.path.insert(0, str(REPO / "mcp"))
    import airkg_tools
    monkeypatch.setattr(prescriptions, "REPORTS", loopback["reports"])
    tools = airkg_tools.Tools(graph=None)
    monkeypatch.setattr(tools._presc(), "REPORTS", loopback["reports"])
    monkeypatch.setattr(tools._score().P, "REPORTS", loopback["reports"])
    return prescriptions, score, tools


def test_loopback_the_spot_measures_the_named_body_and_nothing_else(loopback):
    p = loopback["payload"]
    assert loopback["cycle"] == f"spot_bea_{TODAY}"
    assert p["scope"] == "spot" and p["spot_targets"] == [SPOT_BODY]
    assert p["params_cycle"] == load_params()["cycle"]["name"]
    assert {t["agency"] for t in loopback["targets"]} == {SPOT_BODY}
    assert {r["agency"] for r in p["matrix"]} == {SPOT_BODY}
    assert loopback["other_netloc"] not in p["requests_per_host"]
    assert not any(loopback["other_netloc"] in str(o.get("target_url"))
                   for o in p["observations_detail"])
    # Controls first, exactly as a full cycle: the gate passed and its record is on the payload.
    assert loopback["controls_ok"] and p["control_verdict"] == "pass"
    assert p["control_findings"] == len(p["control_findings_detail"]) > 1
    # Every leg the frame gives the body's surfaces was judged, and B5 once for the body.
    legs = {(f["target_doc_id"], f["leg"]) for f in p["findings_detail"]}
    for t in loopback["targets"]:
        for leg in t["legs"]:
            assert (t["doc_id"], leg) in legs, (t["doc_id"], leg)
    b5 = [f for f in p["findings_detail"] if f["leg"] == "B5"]
    assert len(b5) == 1 and b5[0]["target_doc_id"].startswith("host:127.0.0.1:")
    print("\nSPOT PAYLOAD", json.dumps({k: v for k, v in p.items() if k not in (
        "matrix", "findings_detail", "observations_detail", "control_findings_detail",
        "robots_log", "surface_legs")}, indent=1, default=str))


def test_loopback_publish_writes_one_new_cycle_shard_and_no_supersession(loopback):
    ev, log = loopback["events"], loopback["log"]
    p = loopback["payload"]
    assert ev["shard"] == f"events/cycle-{loopback['cycle']}.jsonl"
    assert ev["generation"] == 0 and ev["supersedes"] is None
    assert ev["observation_events_written"] == len(p["observations_detail"])
    assert ev["finding_events_written"] == (len(p["findings_detail"])
                                            + len(p["control_findings_detail"]))
    assert loopback["supersession"]["supersession_events_written"] == 0
    assert not [e for e in log if e["event_type"] == "finding_supersedes"]
    assert all(e.get("scope") == "spot" and e.get("spot_targets") == [SPOT_BODY]
               and e.get("cycle") == loopback["cycle"] for e in log)
    # Evidence was promoted into the throwaway committed root, and every cited body is there.
    assert loopback["promoted"]["evidence_promoted"] > 0
    for o in p["observations_detail"]:
        d = (o.get("response") or {}).get("body_sha256")
        if d:
            assert (loopback["root"] / "evidence" / d[:2] / d).is_file()
    print("\nPUBLISH", json.dumps({**ev, **loopback["supersession"], **loopback["promoted"]},
                                  indent=1))


def test_loopback_the_spot_re_derives_byte_identically(loopback):
    r = loopback["rederive"]
    assert r["identical"], json.dumps(r, indent=1)[:2000]
    assert r["recorded"] == (len(loopback["payload"]["findings_detail"])
                             + len(loopback["payload"]["control_findings_detail"]))
    print("\nREDERIVE", json.dumps(r, indent=1))


def test_loopback_projects_into_scratch_labels_and_leaves_none_behind(loopback):
    proj, n = loopback["projection"], loopback["projected"]
    p = loopback["payload"]
    assert n["Observation"] == len({o["obs_id"] for o in p["observations_detail"]})
    assert n["Finding"] == len(p["findings_detail"]) + len(p["control_findings_detail"])
    assert proj["supersedes"] == 0 and proj["findings_superseded"] == 0
    assert proj["findings_current"] == n["Finding"]
    assert proj["observed_on_missing_document"] == 0
    assert "measures" not in proj            # the bridge onto real indicators was not built
    assert loopback["scratch_left"] == 0
    print("\nPROJECTION", json.dumps({"counts": proj, "scratch_nodes": n,
                                      "label_prefix": loopback["label_prefix"]}, indent=1))


def test_loopback_matrices_hold_the_bodies_present_and_name_results_by_the_spot(loopback):
    c, cycle = loopback["matrices"], loopback["cycle"]
    assert {r["agency"] for r in c["tier_a"]} == {SPOT_BODY} and c["tier_c"] == []
    assert {r["agency"] for r in c["product"]} == {SPOT_BODY}
    assert c["declared"] == 2
    assert c["head"]["scope"] == "spot" and c["head"]["spot_targets"] == [SPOT_BODY]
    names = loopback["result_names"]
    assert names and all(n.endswith(f"_{cycle}") for n in names)
    assert not any(n.startswith("scan_l0_tierc_") for n in names)
    note = next(n for b, _v, n in c["results"] if b == "scan_l0_a4_pass")
    assert "spot cycle" in note and "16 Tier A" not in note
    head = json.loads((loopback["reports"] / f"scan_matrix_tierA_{cycle}.json").read_text())
    assert head["scope"] == "spot" and [r["agency"] for r in head["rows"]] == [SPOT_BODY]
    print("\nMATRICES", json.dumps({"tier_a_rows": len(c["tier_a"]),
                                    "product_rows": len(c["product"]),
                                    "results": len(names), "head": c["head"]}, indent=1,
                                   default=str))


def test_loopback_views_show_the_spot_beside_the_snapshot(loopback, monkeypatch, capsys):
    presc, score, tools = _views(loopback, monkeypatch)
    cycle = loopback["cycle"]
    assert presc.published_cycles() == {"full": [SNAPSHOT], "spot": [cycle]}
    assert presc.latest_for(SPOT_BODY) == cycle
    assert presc.latest_for(OTHER_BODY) == SNAPSHOT
    diff = presc.since_snapshot(SPOT_BODY)
    snap_fail = {l for l, s in presc.leg_states(SNAPSHOT, SPOT_BODY).items() if s == "fail"}
    now = presc.leg_states(cycle, SPOT_BODY)
    assert set(diff["passed_since_snapshot"]) == {l for l in snap_fail if now.get(l) == "pass"}
    assert diff["passed_since_snapshot"], "the passes_all fixture passes legs BEA fails"
    assert "passed since the snapshot:" in diff["sentence"]

    # get_body: the snapshot's verdicts AND the latest measurement, named, dated, diffed.
    body = tools.get_body(SPOT_BODY)
    assert body["cycle"] == SNAPSHOT
    lm = body["latest_measurement"]
    assert lm["latest"] == cycle and lm["latest_measured_on"] == TODAY and lm["latest_is_spot"]
    assert lm["passed_since_snapshot"] == diff["passed_since_snapshot"]
    assert tools.get_body(OTHER_BODY)["latest_measurement"]["latest_is_spot"] is False

    # get_prescriptions(body): ranked by the latest measurement's failures, while
    # `bodies_failing_now` stays the snapshot's.
    pr = tools.get_prescriptions(body=SPOT_BODY)
    assert pr["failing_legs_from"] == cycle and pr["bodies_failing_now_from"] == SNAPSHOT
    assert set(pr["failing_legs"]) == {l for l, s in now.items() if s == "fail"}
    snap_acts = {a["id"]: a["value"] for a in presc.actions(presc.load_record())}
    assert all(a["value"] == snap_acts[a["id"]] for a in pr["actions"])

    # get_overview: spot cycles listed apart from full cycles.
    ov = tools.get_overview()
    assert ov["cycles"]["full"] == [SNAPSHOT]
    assert [s["cycle"] for s in ov["cycles"]["spot"]] == [cycle]
    assert ov["cycles"]["spot"][0]["bodies"] == [SPOT_BODY]
    assert ov["cycle_of_record"]["cycle"] == SNAPSHOT

    # score.py --body: the latest measurement block, unranked.
    assert score.main(["--body", SPOT_BODY]) == 0
    text = capsys.readouterr().out
    assert f"latest measurement: {cycle} ({TODAY})" in text and "unranked" in text
    assert score.prior_cycle(SNAPSHOT) != cycle
    with capsys.disabled():
        print("\nVIEWS get_body.latest_measurement:",
              json.dumps({k: v for k, v in lm.items() if k != "locators"}, indent=1))
        print("VIEWS get_prescriptions:", json.dumps({k: pr[k] for k in (
            "failing_legs", "failing_legs_from", "bodies_failing_now_from")}, indent=1))
        print("VIEWS get_overview.cycles:", json.dumps(ov["cycles"], indent=1))
        print("VIEWS score.py --body tail:\n" + "\n".join(text.splitlines()[-5:]))
