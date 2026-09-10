"""The standing readers for cycle 2's five new properties.

`cc_tasks/2026-09-07_scan_run_2.md` §1 and §3. Each of these is a property that was true by
nobody's doing until this task, and each has already cost the project something:

1. **A body enters the committed evidence store only when a published Observation cites it.**
   `run.py` used to write every body it fetched into `corpus/evidence/scan/`, published or
   not; 260 fixture blobs were quarantined and 418 real-host bodies are retained as cited by
   nothing (DD-058). Staging plus `publish.promote_evidence` inverts the default.
2. **One error convention on the log.** 266 observations recorded `http_4xx` on a 403 that the
   closed set now calls `refused`, and cycle 2's collectors classify by status — two
   conventions on one log make `error_class_counts` a measurement of the instrument.
3. **A withdrawn `conversion_gap` says so on the log**, not only in the Seldon graph, which is
   a projection and gets rebuilt.
4. **A cycle's Result names carry the cycle**, resolved through one function, so a figure can
   never look up a name no registrar bound.
5. **Every prior cycle still re-derives byte-identically** — including the fourth payload,
   which the harness-v3 gate did not cover.

The Neo4j-backed checks SKIP rather than fail when the database is down, for the reason
`tests/test_framework_projection_roundtrip.py` gives: a developer without the database gets a
green suite and an unverified claim, never a falsely green one.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SCAN = REPO / "assessment" / "harness" / "scan"
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))

from kg import eventlog                                             # noqa: E402
from kg.ingest.gate import GAP_EVENT                                # noqa: E402
from scan import errors as scan_errors                              # noqa: E402
from scan import load_params, publish, run as run_mod               # noqa: E402
from scan.fixtures.server import FixtureServer                      # noqa: E402
from scan.model import EVIDENCE_ROOT, params_hash                   # noqa: E402

import annotate_withdrawn_conversion_gaps as gaps_mod               # noqa: E402
import cycle_results                                                # noqa: E402
import reclassify_observation_errors as recl                        # noqa: E402
import register_evidence_retention_result as retention              # noqa: E402

PARAMS_REL = "assessment/harness/scan/params.yaml"

#: The four cycles that PRECEDE this one, with what each recorded. Literals,
#: because a gate that reads its expectation out of the artifact under test can only ever
#: pass. The fourth was missing from the harness-v3 gate: `scan_2026-09-07_controls` is the
#: payload a `--controls-only` run wrote, and it is exactly the one that was overwritten and
#: had to be recovered from git, so it is the one that most needs a reader.
PRIOR_CYCLES = {
    "scan_smoke_2026-09-06": 286,
    "scan_controls_2026-09-06": 33,
    "scan_2026-09-07": 437,
    "scan_2026-09-07_controls": 33,
}


def _rederive_module():
    """`rederive.py` by path — `assessment/harness/` holds a second `run.py`, and only the
    path disambiguates the two."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("scan_rederive_run2", SCAN / "rederive.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _params_for(payload: dict) -> dict:
    """The parameter set a cycle was MEASURED under, recovered from git BY HASH. Never
    reconstructed by hand: an approximation of an old parameter set makes the gate pass for
    the wrong reason."""
    revs = subprocess.run(["git", "log", "--format=%H", "--", PARAMS_REL],
                          capture_output=True, text=True, cwd=str(REPO)).stdout.split()
    for rev in revs:
        txt = subprocess.run(["git", "show", f"{rev}:{PARAMS_REL}"],
                             capture_output=True, text=True, cwd=str(REPO)).stdout
        if txt.strip() and params_hash(yaml.safe_load(txt)) == payload["params_hash"]:
            return yaml.safe_load(txt)
    if params_hash(load_params()) == payload["params_hash"]:
        # The current cycle: its params are on disk and not yet committed. Recovering them
        # from git would be recovering a set that does not exist yet.
        return load_params()
    raise AssertionError(
        f"no commit of {PARAMS_REL} hashes to {payload['params_hash'][:12]}…; the parameters "
        f"this cycle was measured under are not recoverable, so its Findings can never be "
        f"re-derived")


@pytest.fixture(scope="module")
def session():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        c = load_project_config(REPO)
        driver = get_neo4j_driver(c)
        with driver.session(database=c["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    with driver.session(database=c["neo4j"]["database"]) as s:
        yield s
    driver.close()


# ------------------------------------------------- §1.1 evidence enters only on citation

def test_a_collection_under_a_staging_root_writes_nothing_into_the_committed_store(tmp_path):
    """The property `--evidence-root` exists for, driven through a REAL fixture collection.

    `tests/conftest.py`'s autouse guard already redirects the store under pytest, so this
    would pass on any code. The check that means something is the second one: the bodies land
    in the STAGING root, so the redirect is doing the work rather than the collection simply
    producing nothing.
    """
    from scan.collectors import http
    from scan.manners import Fetcher
    from scan import model as scan_model
    params = load_params()
    staging = tmp_path / "staging"
    before = sorted(p.name for p in EVIDENCE_ROOT.rglob("*") if p.is_file())
    prior_root = scan_model.EVIDENCE_ROOT
    scan_model.EVIDENCE_ROOT = staging
    try:
        with FixtureServer("passes_all") as base:
            obs = http.fetch(Fetcher(params), "A1", "control:passes_all",
                             f"{base}/index.html", params, parse_links=True)
    finally:
        scan_model.EVIDENCE_ROOT = prior_root
    assert obs, "the fixture collection produced no observation, so it proves nothing"
    staged = [p for p in staging.rglob("*") if p.is_file()]
    assert staged, "nothing was staged; the redirect cannot be what kept the store clean"
    after = sorted(p.name for p in EVIDENCE_ROOT.rglob("*") if p.is_file())
    assert after == before, (
        f"a staged collection still wrote {len(after) - len(before)} blob(s) into "
        f"{EVIDENCE_ROOT}")


def test_promotion_copies_exactly_the_cited_digests_and_removes_the_staging_root(tmp_path):
    """§1.1's second clause. Two staged bodies, one cited: exactly one is promoted, the
    uncited one is not, and the staging directory is gone afterwards."""
    from scan.model import store_evidence, sha256_bytes
    staging, committed = tmp_path / "stage", tmp_path / "committed"
    cited_body, orphan_body = b"cited-by-an-observation", b"fetched-and-never-published"
    d_cited, _ = store_evidence(cited_body, staging)
    d_orphan, _ = store_evidence(orphan_body, staging)
    payload = {"evidence_root": str(staging), "observations_detail": [
        {"obs_id": "obs_x", "response": {"body_sha256": d_cited, "body_path": "stale"}},
        {"obs_id": "obs_y", "response": {"body_sha256": None, "body_path": None}},
    ]}
    out = publish.promote_evidence(payload, committed=committed)
    assert out["evidence_promoted"] == 1, out
    assert (committed / d_cited[:2] / d_cited).read_bytes() == cited_body
    assert not (committed / d_orphan[:2] / d_orphan).exists(), (
        "an uncited body was promoted; promotion is citation-driven or it is nothing")
    assert not staging.exists(), "the staging root survived publication"
    assert payload["observations_detail"][0]["response"]["body_path"].endswith(d_cited), (
        "body_path still points into the deleted staging root")


def test_promotion_refuses_when_a_cited_body_is_nowhere(tmp_path):
    """Invariant 3 one layer down: a Finding whose evidence the repo does not hold is not
    evidence, so a payload citing a digest with no bytes must fail LOUD rather than publish."""
    staging, committed = tmp_path / "stage", tmp_path / "committed"
    staging.mkdir()
    payload = {"evidence_root": str(staging), "observations_detail": [
        {"obs_id": "obs_x", "response": {"body_sha256": "de" * 32, "body_path": None}}]}
    with pytest.raises(SystemExit, match="neither the staging root"):
        publish.promote_evidence(payload, committed=committed)
    assert staging.is_dir(), "a refused promotion deleted the staging root anyway"


def test_the_staging_root_is_derived_from_the_cycle_and_is_not_the_committed_store():
    params = load_params()
    root = run_mod.staging_root(params)
    assert root.name == params["cycle"]["name"]
    assert EVIDENCE_ROOT not in root.parents and root != EVIDENCE_ROOT
    ignored = subprocess.run(["git", "check-ignore", str(root)],
                             capture_output=True, text=True, cwd=REPO)
    assert ignored.returncode == 0, (
        "the staging root is not gitignored; an interrupted run would leave untracked bodies "
        "in the working tree, which is the litter this design removes")


# ------------------------------------------------------- §1.2 one error convention on the log

@pytest.mark.slow   # replays the whole event log (pyproject marker definition)
def test_every_recorded_403_now_reads_as_refused_on_the_log():
    """No observation still carries `http_4xx` on a refusal status once the overlay is on.

    Read through `misfiled`, which is the same selector the writer uses: a test with its own
    second selector would be testing two implementations against each other.
    """
    assert not [r for r in recl.rows("status", load_params())
                if r["obs_id"] not in recl.overlaid()], (
        "observations recorded under the old 4xx convention are still un-overlaid")


def test_the_status_pass_leaves_the_deliberate_none_classifications_alone():
    """A10's `invalid_route` probe records `error_class=None` on a 4xx ON PURPOSE — the 404 IS
    the measurement (`collectors/lighthouse.py`). An overlay CORRECTS a recorded class; where
    the collector recorded none there is nothing to correct, and backfilling one would relabel
    a passing measurement a refusal."""
    picked = {r["obs_id"] for r in recl.rows("status", load_params())}
    deliberate = [ev["obs_id"] for ev in eventlog.replay()
                  if ev.get("event_type") == recl.OBS_EVENT
                  and ev.get("error_class") is None
                  and isinstance((ev.get("response") or {}).get("status"), int)
                  and (ev.get("response") or {}).get("status", 0) >= 400]
    assert deliberate, "no such observation on the log; this test proves nothing"
    assert not (picked & set(deliberate)), (
        f"{len(picked & set(deliberate))} deliberate `None` classifications were selected")


def test_each_reclassification_pass_owns_its_own_shard():
    """A shard is the unit an operator reaches for. "The 266 status corrections" has to be a
    file, not a query across a shard that also holds 93 transport corrections."""
    seen = {}
    for name, spec in recl.PASSES.items():
        path = REPO / "events" / f"batch-{spec['batch']:03d}.jsonl"
        assert spec["batch"] not in seen, f"{name} shares a shard with {seen[spec['batch']]}"
        seen[spec["batch"]] = name
        if not path.is_file():
            continue
        kinds = {json.loads(l).get("classified_from", "recorded_error")
                 for l in path.read_text(encoding="utf-8").splitlines() if l.strip()}
        assert kinds <= {name}, f"{path.name} holds passes {kinds}, not just {name!r}"


@pytest.mark.slow   # replays the whole event log (pyproject marker definition)
def test_the_overlay_is_idempotent():
    assert not [r for r in recl.rows("status", load_params())
                if r["obs_id"] not in recl.overlaid()]
    assert not [r for r in recl.rows("recorded_error") if r["obs_id"] not in recl.overlaid()]


def test_no_overlay_touches_the_runners_statement_about_itself():
    """`collector_unavailable` is the RUNNER saying the collector raised. The map classifies
    what a COLLECTOR saw and has no standing over it."""
    for pass_name, params in (("recorded_error", None), ("status", load_params())):
        for r in recl.rows(pass_name, params):
            assert r["error_class_recorded"] != "collector_unavailable"


@pytest.mark.parametrize("cls", ["refused", "connection_reset", "unknown"])
def test_the_closed_set_still_holds_the_classes_the_overlay_writes(cls):
    """`ERROR_CLASSES` may only grow — it is an input to the derived `obs_id`, so a removed
    member is a stored Observation that can no longer be rehydrated."""
    assert cls in scan_errors.ERROR_CLASSES


# --------------------------------------------- §1.3 a withdrawn conversion gap says so

def test_every_scan_surface_conversion_gap_carries_a_withdrawal_annotation():
    assert gaps_mod.gaps(), "no scan-surface conversion_gap on the log; this proves nothing"
    assert not gaps_mod.rows(), (
        f"{len(gaps_mod.rows())} scan-surface conversion gaps have no "
        f"`conversion_gap_withdrawn` overlay")


def test_each_withdrawal_names_the_research_task_it_withdrew():
    for ev in eventlog.replay():
        if ev.get("event_type") != gaps_mod.EVENT:
            continue
        assert ev.get("research_task_id"), ev
        assert ev.get("withdrawn_by") == gaps_mod.WITHDRAWN_BY


def test_a_conversion_gap_projects_to_no_kg_label():
    """§1.3 says: project the flag onto whatever the gap event projects to, and if it projects
    to nothing, say so and stop. It projects to nothing in the KG — no projector reads the
    event type — and its only projection is the Seldon ResearchTask minted at admission, which
    the next test reads. This asserts the premise so a future projector cannot add a node for
    it and leave the overlay silently unprojected."""
    sources = [REPO / "scripts" / "build_projection.py",
               REPO / "scripts" / "load_framework_graph.py",
               SCAN / "publish.py"]
    for src in sources:
        assert GAP_EVENT not in src.read_text(encoding="utf-8"), (
            f"{src.name} now projects {GAP_EVENT}; the withdrawal overlay must be projected "
            f"beside it or the graph will show 22 open gaps that the log says are withdrawn")


def test_every_withdrawn_gap_task_is_withdrawn_in_the_graph(session):
    ids = [ev["research_task_id"] for ev in eventlog.replay()
           if ev.get("event_type") == gaps_mod.EVENT]
    assert ids
    rows = session.run("MATCH (t:ResearchTask) WHERE t.artifact_id IN $ids "
                       "RETURN t.artifact_id AS id, t.state AS state", ids=ids)
    states = {r["id"]: r["state"] for r in rows}
    assert set(states) == set(ids), f"missing ResearchTasks: {set(ids) - set(states)}"
    assert set(states.values()) == {"withdrawn"}, states


# ------------------------------------------------------------- §1.4 the retained bodies

@pytest.mark.slow   # replays the whole event log (pyproject marker definition)
def test_the_uncited_set_only_shrinks_and_only_by_citation(session):
    """DD-058 as amended, and the amendment is why this test reads the way it does.

    The first version asserted `registered == recount` and FAILED — 418 against 417 — which is
    how the over-claim in DD-058 was found. Staging forbids the set GROWING (a cycle promotes
    only what it cites), but content addressing lets it SHRINK: cycle 2 re-fetched
    `bjs.ojp.gov/data/topic`, got bytes identical to a body an earlier diagnostic run had left
    behind, and that body stopped being uncited without moving.

    So the checkable property is the decomposition, not the equality: every body that left the
    set left by being CITED, never by being deleted, and the arithmetic closes exactly.

    **And `registered` is a fact about ONE moment, which is the second thing this test got
    wrong.** `retention.NAME` carries no cycle deliberately: it is the pre-flight census, what
    the store held uncited when `publish.promote_evidence` was installed (the script's own
    docstring). Two clauses below read it as though it were this cycle's `before` figure, which
    it was — for exactly one cycle. Cycle 2 cited one of those bodies, so cycle 3's `before`
    is 417 against a registered 418 and the test reported the property WORKING as the property
    failing. The arithmetic now closes against `uncited_before_this_cycle`, which is the
    quantity it was always about, and `registered` is used for the two things it can still
    say: the set never rose above it, and nothing left the committed store at all.
    """
    # The CYCLE, not a params hash: the census needs the cycle's hash AND the commit that
    # published it, and a caller that could pass a mismatched pair eventually would.
    #
    # This test was red from the moment cycle 2 was committed, and the failure was a wrong
    # NUMBER rather than an error — 578 against 418, which is 418 + the 160 bodies cycle 2
    # itself promoted. `tracked` was read NOW and `prior` before the cycle, so every body the
    # cycle put into the store counted as one the store had failed to cite beforehand. The
    # "before" set is now read at the parent of the publishing commit
    # (`cc_tasks/2026-09-08_scan_frame_fss.md` §0).
    c = retention.census(load_params()["cycle"]["name"])
    row = session.run("MATCH (r:Result {name: $n}) RETURN r.value AS v",
                      n=retention.NAME).single()
    if row is None:
        pytest.skip(f"{retention.NAME} is not registered yet")
    registered = int(row["v"])
    # NEVER BY DELETION, said directly rather than inferred from a count: every body the
    # store held before this cycle is still in it. This is DD-058's actual retention claim,
    # and a count falling can no longer be mistaken for it.
    before_set = set(retention.tracked_digests(f"{c['published_at_commit']}^"))
    now_set = set(retention.tracked_digests())
    gone = sorted(before_set - now_set)
    assert not gone, (
        f"{len(gone)} committed evidence body/bodies are no longer tracked: {gone[:5]}. "
        f"DD-058 retains them where they are; a body fetched from a public host is the record "
        f"that this scanner contacted it")
    assert c["uncited_before_this_cycle"] <= registered, (
        f"the uncited set stood at {c['uncited_before_this_cycle']} before this cycle against "
        f"a pre-flight census of {registered}; it GREW, and staging is supposed to make that "
        f"impossible")
    # The decomposition, closing against the quantity it is about. `uncited_now + newly_cited
    # == uncited_before` is the identity `census` is built to make checkable.
    assert (c["uncited_tracked_bodies"] + c["newly_cited_by_this_cycle"]
            == c["uncited_before_this_cycle"]), c
    assert c["uncited_tracked_bodies"] <= c["uncited_before_this_cycle"], (
        "the uncited set GREW; staging is supposed to make that impossible")
    # The two sets the decomposition is ABOUT, kept apart. A body this cycle promoted was in
    # neither set before it ran, and folding it into either is exactly how this went wrong.
    assert c["promoted_by_this_cycle"] > 0, (
        "a cycle that promoted nothing cannot demonstrate the property this test is for")
    assert c["tracked_bodies"] == (c["tracked_bodies_before_this_cycle"]
                                   + c["promoted_by_this_cycle"]), c
    assert c["newly_cited_by_this_cycle"] <= c["tracked_bodies_before_this_cycle"], (
        "a body can only LEAVE the uncited set if the store already held it")


# ------------------------------------------------ §1.5 / §4 a cycle name and its Results

def test_the_cycle_name_is_not_a_previous_cycles():
    name = load_params()["cycle"]["name"]
    assert name not in PRIOR_CYCLES, (
        f"cycle.name is {name!r}, which is a cycle already on the log. Its payload path, its "
        f"Result suffix and `refuse_clobber` all key on this name (DD-041, CLAUDE.md §11).")


def test_refuse_clobber_refuses_across_a_params_change(tmp_path):
    path = tmp_path / "old_cycle.json"
    path.write_text(json.dumps({"params_hash": "0" * 64}), encoding="utf-8")
    with pytest.raises(SystemExit, match="REFUSING to overwrite"):
        run_mod.refuse_clobber(path, load_params())


def test_name_for_suffixes_every_metric_this_cycle_registers():
    cycle = load_params()["cycle"]["name"]
    suffix = cycle_results.cycle_suffix(cycle)
    for base in ("scan_surfaces", "scan_findings", "scan_a1_pass", "scan_requests_total"):
        got = cycle_results.name_for(base, cycle)
        assert got == f"{base}_{suffix}", got
        cycle_results.check_name(got, cycle)


def test_name_for_leaves_the_first_cycles_bound_names_alone():
    """DD-056 §"What is not renamed": they are immutable and cited, and re-registering them
    suffixed would leave two records of one measurement."""
    for base in sorted(cycle_results.FIRST_CYCLE_EXCEPTIONS)[:5]:
        assert cycle_results.name_for(base, cycle_results.FIRST_CYCLE) == base
        assert cycle_results.name_for(base, "scan_2026-09-08") == f"{base}_2026-09-08"


def test_a_bare_per_cycle_name_is_refused_for_this_cycle():
    cycle = load_params()["cycle"]["name"]
    with pytest.raises(cycle_results.ResultNameError):
        cycle_results.check_name("scan_surfaces", cycle)


# --------------------------------------------------------- §3 every prior cycle re-derives

@pytest.mark.parametrize("cycle", sorted(PRIOR_CYCLES))
def test_every_prior_cycle_re_derives_byte_identically(cycle):
    """Each cycle under ITS OWN rules and ITS OWN params. `finding_identity` is 2 and every
    stored Finding of these four was made under 1, so a gate that re-judged history under
    today's parameters would fail for the one reason that does not matter."""
    path = REPO / "state" / f"{cycle}.json"
    assert path.is_file(), f"{path} is gone; a cycle's evidence is not replaceable"
    payload = json.loads(path.read_text(encoding="utf-8"))
    recorded = len(payload["findings_detail"]) + len(payload.get("control_findings_detail", []))
    assert recorded == PRIOR_CYCLES[cycle], f"{cycle} recorded {recorded}, not the gate's number"
    out = _rederive_module().rederive(payload, _params_for(payload))
    assert out["identical"], out
    assert out["recorded"] == PRIOR_CYCLES[cycle]


def test_this_cycle_re_derives_byte_identically():
    """The cycle under test, when it exists. Skips before the run rather than failing: the
    payload is the run's output and the run is §2."""
    cycle = load_params()["cycle"]["name"]
    path = REPO / "state" / f"{cycle}.json"
    if not path.is_file():
        pytest.skip(f"{cycle} has not been run yet")
    payload = json.loads(path.read_text(encoding="utf-8"))
    # Under the params this cycle was MEASURED under, recovered from git by hash — the same
    # rule every other re-derivation reader here follows. It used to pass `load_params()`,
    # which is only the same thing while `params.yaml` has not moved since the cycle ran; the
    # first task to correct a rule without re-measuring anything made it report
    # `params_changed`, which is the guard working and reads as the gate failing.
    out = _rederive_module().rederive(payload, _params_for(payload))
    assert out["identical"], out


# ------------------------------------------------- ADDENDUM-01: the three payload defects

def test_a_run_stamps_the_task_that_ordered_it():
    """ADDENDUM-01 defect 1. `run.py` used to stamp a module constant onto every payload, so
    cycle 2's payload names cycle 1's task file. `task` is not an input to any derived id, so
    nothing is re-identified by the correction — which is exactly why it could be wrong for a
    whole cycle without anything noticing."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", default=run_mod.TASK)
    assert ap.parse_args([]).task == run_mod.TASK
    assert ap.parse_args(["--task", "cc_tasks/x.md"]).task == "cc_tasks/x.md"
    src = (SCAN / "run.py").read_text(encoding="utf-8")
    assert '"task": a.task' in src, (
        "a payload still stamps the module constant rather than the invocation's --task")
    assert '"task": TASK' not in src


def test_every_published_cycle_agrees_with_the_log_about_which_task_ordered_it():
    """A payload whose `task` field is wrong is corrected by an append-only event, never by an
    edit (invariant 1). So the check is not "the field is right" — it is "the field is right OR
    the log says what it should have been"."""
    corrected = {ev["cycle"]: ev["task"] for ev in eventlog.replay()
                 if ev.get("event_type") == "cycle_task_corrected"}
    bad = []
    for cycle in list(PRIOR_CYCLES) + [load_params()["cycle"]["name"]]:
        path = REPO / "state" / f"{cycle}.json"
        if not path.is_file():
            continue
        said = json.loads(path.read_text(encoding="utf-8")).get("task")
        if cycle in corrected:
            continue                       # the log carries the correction; that is the fix
        if said and cycle.startswith("scan_") and said.endswith("_scan_run.md") \
                and cycle not in ("scan_smoke_2026-09-06", "scan_controls_2026-09-06",
                                  "scan_2026-09-07", "scan_2026-09-07_controls"):
            bad.append(f"{cycle} claims {said} and no cycle_task_corrected event says otherwise")
    assert not bad, bad


def test_every_error_class_on_this_cycle_is_grounded_in_recorded_text_or_a_status():
    """ADDENDUM-01 defect 2, asserted as the property rather than assumed as a regression.

    The addendum reported that the 20 ERS `dns` and the one `unknown` carry no error text, and
    that if the new `errors.py` path had dropped it that would be a regression of the very
    evidence the reclassification overlay reads. **Measured: the premise is false** — all 21
    carry `f"{type(exc).__name__}: {exc}"`, and this test is what keeps it that way. A
    transport class with nothing to classify FROM is a class nobody can re-derive or correct.

    **The exemption is READ from `errors.CLASSES`, not written here.** This test carried
    `robots_disallowed` as a literal, and `off_host` — the same thing one policy layer up,
    added by `cc_tasks/2026-09-08_scan_harness_v4.md` §1.3 — arrived as the second member of a
    set nobody had named. Cycle 3 recorded 164 correct `off_host` observations and this test
    called every one of them ungrounded. A closed set with an unnamed subset gets re-derived by
    hand at each call site and one copy is always stale, which is the defect `errors.py` exists
    to have closed once.
    """
    cycle = load_params()["cycle"]["name"]
    path = REPO / "state" / f"{cycle}.json"
    if not path.is_file():
        pytest.skip(f"{cycle} has not been run yet")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(scan_errors.NOT_FETCHED) == {"robots_disallowed", "off_host",
                                            "sitemap_off_site"}, (
        "the classes recorded without a request changed; this test's exemption follows them")
    ungrounded = []
    for o in payload["observations_detail"]:
        cls = o.get("error_class")
        if cls is None or cls in scan_errors.NOT_FETCHED:
            continue          # no request was made; the decision IS the record, not a failure
        r = o.get("response") or {}
        if not r.get("error") and not isinstance(r.get("status"), int):
            ungrounded.append((cls, o["leg"], o["target_doc_id"]))
    assert not ungrounded, (
        f"{len(ungrounded)} observations carry an error_class with neither recorded exception "
        f"text nor a status to classify from: {ungrounded[:5]}")


def test_the_denominator_is_per_leg_and_the_page_says_so():
    """ADDENDUM-01 defect 3. Two ERS surfaces went unobservable on a host-side DNS transient,
    so `applicable_n` is 22 on some legs and 23 on others. The arithmetic was already per leg;
    what was stale was the PAGE, which carried cycle 1's constant "n = 23 per leg" as a
    non-claim. A non-claim quoting a stale number is a claim."""
    cycle = load_params()["cycle"]["name"]
    suffix = cycle_results.cycle_suffix(cycle)
    mx_path = REPO / "state" / f"scan_matrix_{suffix}.json"
    if not mx_path.is_file():
        pytest.skip("this cycle has no matrix yet")
    per = json.loads(mx_path.read_text(encoding="utf-8"))["per_leg"]
    for leg, s in per.items():
        assert s["applicable_n"] == s["pass"] + s["fail"], leg
        if s["applicable_n"]:
            assert 0.0 <= s["ci95_low"] <= (s["pass_rate"] or 0.0) <= s["ci95_high"] <= 1.0, leg
    page = REPO / "docs" / "progress" / "index.html"
    if not page.is_file():
        pytest.skip("the progress page has not been generated")
    html = page.read_text(encoding="utf-8")
    ns = sorted({s["applicable_n"] for s in per.values()})
    if len(ns) > 1:
        assert "n = 23 per leg" not in html, (
            "the page still states a constant denominator this cycle does not have")
        assert f"n = {ns[0]}–{ns[-1]}" in html, (
            "the page does not state the per-leg denominator range")
