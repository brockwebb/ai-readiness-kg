"""DN-003 decision 6, as a standing guard: no judgement the project asserts stays off the log.

`cc_tasks/2026-09-14_standing_guards.md` decision 1, guarding the incident
`cc_tasks/2026-09-14_rejudgements_on_the_log_RESULT.md` cleaned up.

**The incident.** Fourteen re-judged payloads lived in `state/`, twelve of them on no shard of
the append-only log — including `scan_2026-09-10_rj2`, the judgement of record for the
published report. Every gate in the repository was green throughout: the payloads re-derived
byte-identically, the projection round-tripped, the suite passed. Nothing asked the one
question that would have caught it, which is whether the judgements the project had ASSERTED
were the judgements a stranger replaying the log would get (DD-001). DN-003 decision 6 made it
a rule — "a re-judged payload in `state/` and not on the log is a gate failure for that task" —
and a rule that is true of exactly one task's gate is not a rule. This is where it binds.

The check is written as a pure function over four sets so the **red** half can run it against
the pre-guard world: `state/` as it stood on 2026-09-13 against the log as it stood on
2026-09-13. It reports the twelve. The **green** half runs the same function against what is
on disk now. Prior art for the shape is the file next door
(`tests/test_guards_replay_their_incidents.py`): a guard asserted only against the fixed code
proves the fixed code is fixed and says nothing about whether the guard would have SEEN the
defect.

**Three kinds of payload, and they are not one question.** A payload carrying `findings_detail`
is one of:

* **re-judged** — a judgement over another cycle's evidence. Its Findings belong on the log and
  each pairs to the judgement it replaces. It writes no Observation.
* **measured** — it fetched bytes. Its Observations AND its Findings belong on the log.
* **controls-only** — the loopback control fixtures, which measure the harness and not a host.
  Their observations are deliberately not published: a fixture is not evidence about a federal
  surface, and `publish.project` counts control observations apart for the same reason. The
  exemption is a CLOSED, NAMED set here, checked to be exactly those three and checked to carry
  no Finding at all, so "controls-only" cannot become the label under which a real cycle goes
  unpublished.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")


def _publish():
    """`scan/publish.py` BY PATH — `assessment/harness/` holds a second `run.py` and the same
    ambiguity is why every loader in this repo is path-based."""
    spec = importlib.util.spec_from_file_location(
        "scan_publish_guard", REPO / "assessment" / "harness" / "scan" / "publish.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pub = _publish()

#: The two re-judgements published on 2026-09-08, before DN-003 put `cycle` on the event. Their
#: Findings are on the log and their supersession is on the log; what they have no property for
#: is graph-side attribution, because `Finding.cycle` is null for every event written before
#: DN-003 and is deliberately NOT backfilled from `state/` — the projection is a function of
#: the log, and a property invented at projection time out of a file beside it is the
#: convention DN-003 decision 3 replaced with an edge
#: (`2026-09-14_rejudgements_on_the_log_RESULT.md` §6).
#:
#: A CLOSED set, asserted below to be exactly these two. It may only SHRINK — if those events
#: are ever superseded by ones carrying a cycle — and a thirteenth cycle arriving here would be
#: a cycle published without its attribution, which is the thing the guard is for.
PRE_DN003_CYCLES = frozenset({"scan_2026-09-07_rj1", "scan_2026-09-07b_rj1"})

#: Re-judgements published AFTER the guard existed (2026-09-14), so not among the twelve the
#: red test reconstructs as off the log. Closed and named, like the two sets around it; it grows
#: by one name per later re-judgement, and each name is the task that published it.
#: `scan_2026-09-10_rj4`: `cc_tasks/2026-09-18_rejudge_seven_legs.md`.
PUBLISHED_AFTER_THE_GUARD = frozenset({"scan_2026-09-10_rj4"})

#: The loopback control fixtures. Same rule: closed, named, may only shrink.
CONTROLS_ONLY = frozenset({"scan_controls_2026-09-06", "scan_2026-09-07_controls",
                           "scan_2026-09-07b_controls"})


def kind_of(name: str, payload: dict) -> str:
    if pub.is_rejudgement(payload):
        return "rejudged"
    if payload.get("cycle_kind") == "controls_only" or payload.get("cycle") == "controls_only":
        return "controls_only"
    return "measured"


def stored_payloads(state_dir: Path) -> dict:
    """Every payload in `state/` that carries a judgement, keyed by FILE STEM.

    The stem and not the `cycle` field: `state/scan_2026-09-07b_rj2.json` names itself
    `scan_2026-09-07b_rj1`, a recorded defect in an immutable payload (`publish.cycle_of`), and
    keying on the field would collapse two judgements of cycle 2 into one entry and hide
    whichever of them was missing.
    """
    out = {}
    for path in sorted(state_dir.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(doc, dict) and "findings_detail" in doc:
            out[path.stem] = doc
    return out


def legs_judged(doc: dict | None) -> set:
    return {f["leg"] for f in (doc or {}).get("findings_detail") or []}


def owes_a_predecessor(name: str, doc: dict, payloads: dict) -> list:
    """The Findings of a re-judgement that replace something: those on a leg its predecessor
    judged. A Finding on a leg the predecessor never judged has nothing to supersede, and
    `publish.write_supersession` rightly writes no pair for it. `scan_2026-09-10_rj4` is the
    first with any: the seven generation-11 to -13 legs
    (`cc_tasks/2026-09-18_rejudge_seven_legs.md`). A Finding on a leg the predecessor DID judge
    that has no pair is still the fork this guard exists for."""
    pred_legs = legs_judged(payloads.get(pub.supersedes_of(name)))
    return [f["finding_id"] for f in doc.get("findings_detail") or [] if f["leg"] in pred_legs]


def audit(payloads: dict, on_log_find: set, on_log_obs: set, paired: set) -> dict:
    """Which stored judgements are on the log, and which are not. **The guard itself.**

    Pure over its four inputs so the red half can hand it the pre-guard world. Nothing here
    reads a file or a database; `unpublished` is the failure DN-003 decision 6 names, and the
    other keys are the measurements that make the failure legible rather than a single boolean.
    """
    rows, unpublished, unpaired = [], [], []
    for name in sorted(payloads, key=lambda c: (pub.generation(c), c)):
        doc = payloads[name]
        kind = kind_of(name, doc)
        fids = [f["finding_id"] for f in doc.get("findings_detail") or []]
        oids = [o["obs_id"] for o in doc.get("observations_detail") or []]
        row = {"cycle": name, "kind": kind, "generation": pub.generation(name),
               "findings": len(fids), "findings_on_log": sum(1 for f in fids
                                                             if f in on_log_find),
               "observations": len(oids),
               "observations_on_log": sum(1 for o in set(oids) if o in on_log_obs),
               "supersedes": pub.supersedes_of(name),
               "findings_paired": sum(1 for f in fids if f in paired)}
        if kind == "rejudged":
            if row["findings_on_log"] != row["findings"]:
                unpublished.append(f"{name}: {row['findings'] - row['findings_on_log']} of "
                                   f"{row['findings']} Findings are not on the log")
            owed = owes_a_predecessor(name, doc, payloads)
            row["findings_on_new_legs"] = row["findings"] - len(owed)
            missing_pairs = sum(1 for f in owed if f not in paired)
            if missing_pairs:
                unpaired.append(f"{name}: {missing_pairs} of {len(owed)} Findings have no "
                                f"supersession event naming the judgement they replace")
        elif kind == "measured":
            if row["findings_on_log"] != row["findings"]:
                unpublished.append(f"{name}: {row['findings'] - row['findings_on_log']} of "
                                   f"{row['findings']} Findings are not on the log")
            if row["observations_on_log"] != len(set(oids)):
                unpublished.append(f"{name}: {len(set(oids)) - row['observations_on_log']} of "
                                   f"{len(set(oids))} Observations are not on the log")
        rows.append(row)
    return {"rows": rows, "unpublished": unpublished, "unpaired": unpaired,
            "by_kind": {k: sum(1 for r in rows if r["kind"] == k)
                        for k in ("rejudged", "measured", "controls_only")}}


def _log_sets():
    from kg import eventlog
    find, obs, paired = set(), set(), set()
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == pub.FIND_EVENT:
            find.add(ev["finding_id"])
        elif t == pub.OBS_EVENT:
            obs.add(ev["obs_id"])
        elif t == pub.SUPERSEDES_EVENT:
            paired.add(ev["finding_id"])
    return find, obs, paired


@pytest.fixture(scope="module")
def live():
    payloads = stored_payloads(REPO / "state")
    find, obs, paired = _log_sets()
    return payloads, audit(payloads, find, obs, paired)


# ================================================================== red: the incident replayed

def test_the_guard_reports_the_twelve_payloads_that_were_off_the_log(live):
    """**Red.** The pre-guard world: `state/` as it is, against a log missing the twelve
    re-judgements the 2026-09-14 task published.

    Reconstructed by subtraction rather than by checking out the old tree, because the tree is
    not the thing that changed — the LOG is, and it is append-only, so the pre-guard log is
    exactly today's log minus the events those twelve cycles wrote. Every one of the twelve is
    named in that RESULT's §1 table.
    """
    payloads, _ = live
    find, obs, paired = _log_sets()
    was_off = [c for c in payloads if kind_of(c, payloads[c]) == "rejudged"
               and c not in PRE_DN003_CYCLES and c not in PUBLISHED_AFTER_THE_GUARD]
    assert len(was_off) == 12, sorted(was_off)
    missing = {f["finding_id"] for c in was_off for f in payloads[c]["findings_detail"]}
    # The twelve wrote 6,041 `finding_derived` events and 6,797 supersession events; the two
    # `_rj1` cycles' Findings were already on the log in 2026-09-08 and their ids are shared
    # with nothing, so removing the twelve's ids removes exactly the twelve.
    pre = audit(payloads, find - missing, obs, paired - missing)
    assert pre["unpublished"], "the guard sees nothing wrong with the pre-guard log"
    named = {m.split(":")[0] for m in pre["unpublished"]}
    assert named == set(was_off), sorted(named ^ set(was_off))


def test_the_guard_reports_a_measured_cycle_whose_observations_never_reached_the_log(live):
    """**Red, the second class decision 1 names.** A measured payload in `state/` with its
    Observations off the log is the same defect one layer down: the evidence a stranger would
    replay is not the evidence that was judged."""
    payloads, _ = live
    find, obs, paired = _log_sets()
    target = "scan_2026-09-10"
    gone = {o["obs_id"] for o in payloads[target]["observations_detail"]}
    pre = audit(payloads, find, obs - gone, paired)
    assert any(m.startswith(f"{target}:") and "Observations are not on the log" in m
               for m in pre["unpublished"]), pre["unpublished"][:5]


def test_the_guard_reports_a_rejudgement_published_without_its_supersession(live):
    """**Red.** Findings on the log with no `finding_supersedes` event is a judgement that
    replaced something and did not say what. DN-003 decision 3 is the edge; this is the gate
    that notices its absence."""
    payloads, _ = live
    find, obs, paired = _log_sets()
    target = "scan_2026-09-10_rj3"
    gone = {f["finding_id"] for f in payloads[target]["findings_detail"]}
    pre = audit(payloads, find, obs, paired - gone)
    assert any(m.startswith(f"{target}:") for m in pre["unpaired"]), pre["unpaired"][:5]


# ================================================================== green: what ships today

def test_every_stored_judgement_is_on_the_log(live):
    """DN-003 decision 6, standing. Green at 15 re-judged and 6 measured (the fifteenth is
    `scan_2026-09-10_rj4`, `cc_tasks/2026-09-18_rejudge_seven_legs.md`)."""
    _payloads, a = live
    assert a["unpublished"] == [], json.dumps(a["unpublished"], indent=1)
    assert a["unpaired"] == [], json.dumps(a["unpaired"], indent=1)
    assert a["by_kind"] == {"rejudged": 15, "measured": 6, "controls_only": 3}, a["by_kind"]
    # The one cycle with Findings on legs its predecessor never judged, and how many.
    new_legs = {r["cycle"]: r["findings_on_new_legs"] for r in a["rows"]
                if r.get("findings_on_new_legs")}
    assert new_legs == {"scan_2026-09-10_rj4": 292}, new_legs


def test_the_controls_only_exemption_is_exactly_three_named_payloads_and_they_judge_nothing(
        live):
    """The exemption cannot grow silently, and it cannot cover a payload that judges anything.

    A controls-only payload's observations are loopback fixtures and are not published; if one
    of them also carried Findings, this guard would be excusing a real judgement from the log
    under a label about fixtures.
    """
    payloads, _a = live
    found = {c for c in payloads if kind_of(c, payloads[c]) == "controls_only"}
    assert found == set(CONTROLS_ONLY), sorted(found ^ set(CONTROLS_ONLY))
    for c in sorted(found):
        assert not payloads[c].get("findings_detail"), (
            f"{c} is exempted as controls-only and carries "
            f"{len(payloads[c]['findings_detail'])} Findings")


def test_the_pre_dn003_attribution_exemption_is_exactly_two_named_cycles(live):
    """`Finding.cycle` is the attribution DN-003 added; the two cycles published before it
    carry none. Closed set, asserted from `state/` and the log rather than trusted."""
    payloads, _a = live
    rj = {c for c in payloads if kind_of(c, payloads[c]) == "rejudged"}
    assert PRE_DN003_CYCLES <= rj, sorted(PRE_DN003_CYCLES - rj)
    assert len(PRE_DN003_CYCLES) == 2


@pytest.fixture(scope="module")
def graph():
    try:
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    yield driver, cfg["neo4j"]["database"]
    driver.close()


def test_every_rejudged_cycle_is_attributed_on_the_graph_by_finding_cycle(live, graph):
    """Decision 1's graph half: the Findings of a re-judged cycle answer to `Finding.cycle`,
    and every one of them carries a `SUPERSEDES` edge into the judgement it replaced.

    `params_hash` cannot answer this — four cycles judged in one generation share one hash, the
    report's own snapshot among them — which is why the property exists at all.
    """
    payloads, _a = live
    driver, db = graph
    unattributed, unlinked = [], []
    with driver.session(database=db) as s:
        for c in sorted(payloads):
            if kind_of(c, payloads[c]) != "rejudged" or c in PRE_DN003_CYCLES:
                continue
            fids = [f["finding_id"] for f in payloads[c]["findings_detail"]]
            n = s.run("MATCH (f:Finding) WHERE f.finding_id IN $ids AND f.cycle = $c "
                      "RETURN count(f) AS n", ids=fids, c=c).single()["n"]
            if n != len(fids):
                unattributed.append(f"{c}: {len(fids) - n} of {len(fids)} Findings do not "
                                    f"carry f.cycle = {c!r}")
            owed = owes_a_predecessor(c, payloads[c], payloads)
            e = s.run("MATCH (f:Finding)-[:SUPERSEDES]->(:Finding) "
                      "WHERE f.finding_id IN $ids RETURN count(*) AS n",
                      ids=owed).single()["n"]
            if e != len(owed):
                unlinked.append(f"{c}: {len(owed) - e} of {len(owed)} Findings on a leg its "
                                f"predecessor judged have no SUPERSEDES edge")
    assert unattributed == [], json.dumps(unattributed, indent=1)
    assert unlinked == [], json.dumps(unlinked, indent=1)


def test_the_two_pre_dn003_cycles_are_linked_even_though_they_are_not_attributed(live, graph):
    """The exemption is narrow and this is what makes it narrow: the two pre-DN-003 cycles are
    excused from `Finding.cycle` and from nothing else. Their supersession is on the graph."""
    payloads, _a = live
    driver, db = graph
    with driver.session(database=db) as s:
        for c in sorted(PRE_DN003_CYCLES):
            fids = [f["finding_id"] for f in payloads[c]["findings_detail"]]
            e = s.run("MATCH (f:Finding)-[:SUPERSEDES]->(:Finding) "
                      "WHERE f.finding_id IN $ids RETURN count(*) AS n",
                      ids=fids).single()["n"]
            assert e == len(fids), f"{c}: {len(fids) - e} of {len(fids)} unlinked"
            n = s.run("MATCH (f:Finding) WHERE f.finding_id IN $ids AND f.cycle IS NOT NULL "
                      "RETURN count(f) AS n", ids=fids).single()["n"]
            assert n == 0, (f"{c} now carries f.cycle on {n} Findings; it is no longer a "
                            f"pre-DN-003 cycle and belongs out of PRE_DN003_CYCLES")


# ============================== decision 4: --project-once is the same graph, a fourteenth of
# ============================== the wall clock

class _Rec:
    """A recording Neo4j session. Every statement `project()` issues, in order, with its
    parameters — which IS the end-state graph when the run begins with `project`'s own
    `DETACH DELETE` over every scan label and the database is written by nothing else.

    `.single()` answers the handful of reads `project` makes. The counts it returns are all
    zero and all unused by the comparison: what is compared is the WRITE sequence, and a read
    that answered differently between the two runs would change that sequence and be caught.
    """

    def __init__(self, calls):
        self.calls = calls

    def run(self, query, **params):
        self.calls.append((" ".join(query.split()), dict(sorted(params.items()))))
        return self

    def single(self):
        return _Zero()

    def __iter__(self):
        return iter(())

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Zero:
    def __getitem__(self, _k):
        return 0

    def get(self, _k, default=None):
        return 0


class _Driver:
    def __init__(self, calls):
        self.calls = calls

    def session(self, **_k):
        return _Rec(self.calls)

    def close(self):
        pass


def _two_cycle_fixture(root: Path) -> Path:
    """A measured cycle and two generations of re-judgement over it, in a throwaway `state/`.

    Two cycles is the smallest case that can tell the two modes apart: with one, "once at the
    end" and "after each" are the same call.
    """
    state = root / "state"
    state.mkdir(parents=True, exist_ok=True)
    obs = [{"obs_id": f"o{i}", "leg": "A1", "spec_code": "A1", "target_doc_id": "host:z",
            "captured_at": "2026-09-14T00:00:00Z", "collector": "c", "error_class": None,
            "params_hash": "p" * 64, "request": {"url": "https://z/"},
            "response": {"body_sha256": "s" * 64, "body_path": None}} for i in (1, 2)]
    find = [{"finding_id": "fz1", "rule_id": "RULE-A1-v1", "rule_version": "v1", "leg": "A1",
             "spec_code": "A1", "verdict": "pass", "reason": "r", "params_hash": "p" * 64,
             "target_doc_id": "host:z", "evidence": ["o1", "o2"]}]
    (state / "scan_z.json").write_text(json.dumps(
        {"cycle": "scan_z", "params_hash": "p" * 64, "findings_detail": find,
         "control_findings_detail": [], "observations_detail": obs}), encoding="utf-8")
    for gen, fid in ((1, "fz1g1"), (2, "fz1g2")):
        (state / f"scan_z_rj{gen}.json").write_text(json.dumps(
            {"cycle": f"scan_z_rj{gen}", "cycle_kind": "rejudged", "derived_from": "scan_z",
             "params_hash": "q" * 64,
             "findings_detail": [{**find[0], "finding_id": fid, "verdict": "fail"}],
             "control_findings_detail": [], "observations_detail": []}), encoding="utf-8")
    return state


#: The two fields `eventlog.append` stamps on every line and the projection never reads. They
#: differ between two runs by construction — a uuid4 and a wall-clock instant — so a comparison
#: of two publications has to drop them, and dropping them is only sound because `project()`
#: reads neither. That is asserted below rather than assumed.
_STAMPED = ("event_id", "timestamp")


def _log_content(events_dir: Path) -> list:
    out = []
    for shard in sorted(events_dir.glob("*.jsonl")):
        for line in shard.read_text(encoding="utf-8").splitlines():
            ev = json.loads(line)
            out.append((shard.name, {k: v for k, v in sorted(ev.items())
                                     if k not in _STAMPED}))
    return out


def _publish_run(tmp_path, monkeypatch, argv, label):
    """One publication of the two-cycle fixture, in a world of its own."""
    import importlib.util as iu
    from kg import eventlog
    root = tmp_path / label
    _two_cycle_fixture(root)
    events = root / "events"
    schema = root / "schema.yaml"
    schema.write_text('schema_version: "0.1"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)

    spec = iu.spec_from_file_location(f"rj_{label}", REPO / "scripts"
                                      / "publish_rejudgements.py")
    rj = iu.module_from_spec(spec)
    spec.loader.exec_module(rj)
    # `_publish()` loads `scan/publish.py` by path off `rj.REPO`, so it is called BEFORE that
    # global is repointed at the fixture tree — the module lives in the real repository and
    # only its own REPO moves.
    calls, projections = [], []
    mod = rj._publish()
    monkeypatch.setattr(rj, "REPO", root)
    monkeypatch.setattr(rj, "OUT", root / "record.json")
    monkeypatch.setattr(mod, "REPO", root)
    real_project = mod.project

    def counted():
        projections.append(1)
        return real_project()

    monkeypatch.setattr(mod, "project", counted)
    monkeypatch.setattr(rj, "_publish", lambda: mod)

    import seldon.config as sc
    monkeypatch.setattr(sc, "get_neo4j_driver", lambda *_a, **_k: _Driver(calls))
    monkeypatch.setattr(sc, "load_project_config",
                        lambda *_a, **_k: {"neo4j": {"database": "fixture"}})

    # The measured cycle first: a re-judgement may not be published before the Observations it
    # cites are on the log, and `preflight` STOPS on exactly that.
    mod.write_events(json.loads((root / "state" / "scan_z.json").read_text()),
                     root / "state" / "scan_z.json")
    assert rj.main(argv) == 0
    return {"log": _log_content(events), "calls": calls, "projections": len(projections)}


def test_project_once_leaves_the_same_graph_as_projecting_after_every_cycle(tmp_path,
                                                                            monkeypatch):
    """Decision 4. Two cycles, published both ways, compared on what determines the graph.

    The comparison is the full ordered sequence of statements `project()` issues against the
    database, parameters included, captured by a recording session. `project()` opens by
    deleting every scan-schema label and rebuilds from the whole log, so that sequence run
    against any starting state produces one graph — and if the two modes issue the same
    sequence, they leave the same graph. The LOG is compared too, because the sequence is a
    function of it.
    """
    with monkeypatch.context() as m:
        per_cycle = _publish_run(tmp_path, m, [], "per_cycle")
    with monkeypatch.context() as m:
        once = _publish_run(tmp_path, m, ["--project-once"], "once")

    assert per_cycle["projections"] == 2, per_cycle["projections"]
    assert once["projections"] == 1, once["projections"]
    assert per_cycle["log"] == once["log"]
    # The per-cycle run's calls are the first projection's statements followed by the second's;
    # only the LAST projection's are the end state, and that is what `--project-once` runs.
    assert per_cycle["calls"][-len(once["calls"]):] == once["calls"]
    assert len(once["calls"]) < len(per_cycle["calls"])


def test_the_projection_reads_nothing_the_comparison_dropped(tmp_path, monkeypatch):
    """The comparison above drops `event_id` and `timestamp` from the log. That is sound only
    because the projection never reads them, which is asserted here from the source rather
    than believed."""
    import ast
    src = (REPO / "assessment" / "harness" / "scan" / "publish.py").read_text(encoding="utf-8")
    fn = next(n for n in ast.parse(src).body
              if isinstance(n, ast.FunctionDef) and n.name == "project")
    body = ast.get_source_segment(src, fn)
    for field in _STAMPED:
        assert f'"{field}"' not in body and f"'{field}'" not in body, (
            f"project() reads {field!r}; the two-cycle comparison may not drop it")


def test_the_projection_is_reset_and_replay(tmp_path, monkeypatch):
    """Why N projections equal one: the first thing `project()` does is delete every node
    carrying a scan-schema label, and the only thing it reads afterwards is the log. An
    incremental projection would make `--project-once` a different result, not a faster one."""
    with monkeypatch.context() as m:
        run = _publish_run(tmp_path, m, ["--project-once"], "reset")
    first = run["calls"][0][0]
    assert first.startswith("MATCH (n) WHERE n:"), first
    assert "DETACH DELETE n" in first, first
