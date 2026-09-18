"""Every judgement the project has asserted is on the append-only log, in generation order,
with supersession on the graph.

`cc_tasks/2026-09-14_rejudgements_on_the_log.md` §3, implementing DN-003 decisions 1 to 6.

Seventeen was the task's count and fourteen is the number: fourteen re-judged payloads live in
`state/`, two of which (`scan_2026-09-07_rj1`, `scan_2026-09-07b_rj1`) reached the log in
2026-09-08 and twelve of which never did — among them `scan_2026-09-10_rj2`, the judgement of
record for the published report. The count is asserted here rather than restated, because "the
seventeen" is exactly the kind of number that survives three task files by being repeated.

**What these tests are for.** A re-judgement is the one publication shape that can be wrong in a
way nothing else notices: it creates no evidence, so no body is promoted, no fetch is logged and
no host is touched, and a payload that never reaches the log leaves the graph holding a
judgement its own author had already withdrawn. Four properties make that visible — the payload
is ON the log, its predecessor PRECEDES it there, the two are LINKED, and nothing that was
already written MOVED.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from kg import eventlog                                             # noqa: E402

SCAN = REPO / "assessment" / "harness" / "scan"

#: The fourteen re-judged payloads, with the number of Findings each carries. A literal, for
#: the reason every other payload table in this suite is one: a set computed from the directory
#: would pass unchanged the day a payload went missing.
REJUDGED = {
    "scan_2026-09-07_rj1": 352, "scan_2026-09-07_rj2": 352, "scan_2026-09-07_rj3": 352,
    "scan_2026-09-07b_rj1": 404, "scan_2026-09-07b_rj2": 404, "scan_2026-09-07b_rj3": 404,
    "scan_2026-09-07b_rj4": 404,
    "scan_2026-09-09_rj1": 634, "scan_2026-09-09_rj2": 634, "scan_2026-09-09_rj3": 634,
    "scan_2026-09-10_rj1": 739, "scan_2026-09-10_rj2": 739, "scan_2026-09-10_rj3": 739,
    # `cc_tasks/2026-09-18_rejudge_seven_legs.md`: the whole current registry, seven new legs.
    "scan_2026-09-10_rj4": 1009,
    "self_2026-09-13_rj1": 6,
}

#: The two published in 2026-09-08, each on its own numbered shard. They are NOT moved onto a
#: named cycle shard: DN-003 decision 4 says an append-only log does not get rewritten, so the
#: shard a cycle already owns stays the shard it owns and only the new events — its
#: supersession pairs — are appended to it.
ALREADY_ON_A_NUMBERED_SHARD = {"scan_2026-09-07_rj1": "batch-040.jsonl",
                               "scan_2026-09-07b_rj1": "batch-041.jsonl"}

#: The 2026-09-06 scaffold's Findings whose PAYLOAD did not survive: 630 on `batch-029.jsonl`
#: under three `params_hash` values, two of which match no committed revision of `params.yaml`
#: (`scripts/annotate_orphan_findings.py --report`). 120 of them are also orphans of their
#: EVIDENCE. The census names them `unattributed`, which is a measurement and not a shrug.
SCAFFOLD_UNATTRIBUTED = 630

#: The 2026-09-06 scaffold's orphans: Findings derived from control Observations it discarded
#: before publishing, annotated rather than deleted (`scripts/annotate_orphan_findings.py`).
#: They stay 120 — this task publishes no Finding whose evidence the log does not hold, so a
#: 121st would mean it did.
SCAFFOLD_ORPHANS = 120

#: Findings on a leg the predecessor never judged, per re-judgement: they have nothing to
#: supersede. Only `scan_2026-09-10_rj4` has any — B1, B2, B4, B5, D2, D3 and G4, first judged
#: there (`cc_tasks/2026-09-18_rejudge_seven_legs.md`): 46 × 6 surface legs + 16 bodies.
NEW_LEG_FINDINGS = {"scan_2026-09-10_rj4": 292}

#: The published report's snapshot (`docs/reports/publication.yaml`).
SNAPSHOT_CYCLE = "scan_2026-09-10_rj2"


def _mod(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


publish = _mod(SCAN / "publish.py", "scan_publish_rjlog")


def payload(cycle: str) -> dict:
    return json.loads((REPO / "state" / f"{cycle}.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def log():
    """One replay, shared. `(finding events in order, obs_ids, supersession pairs)`.

    Module-scoped because the log is 180 MB across 50-odd shards and every test below asks a
    question about the same pass over it.
    """
    finds, obs, pairs, unretained = [], set(), {}, set()
    for i, ev in enumerate(eventlog.replay()):
        t = ev.get("event_type")
        if t == publish.FIND_EVENT:
            finds.append((i, ev))
        elif t == publish.OBS_EVENT:
            obs.add(ev["obs_id"])
        elif t == publish.SUPERSEDES_EVENT:
            pairs[ev["finding_id"]] = ev["supersedes_finding_id"]
        elif t == publish.UNRETAINED_EVENT:
            unretained.add(ev["finding_id"])
    return {"findings": finds, "by_id": {ev["finding_id"]: (i, ev) for i, ev in finds},
            "obs": obs, "pairs": pairs, "unretained": unretained}


# ------------------------------------------------------------------ decision 1: on the log

def test_the_set_of_rejudged_payloads_is_the_one_this_task_published():
    """Fourteen, discovered from `state/` and checked against the literal.

    The task file says seventeen. The directory says fourteen and so does `PRIOR_CYCLES` in
    `tests/test_scan_harness_v4.py` (22 payloads, of which 8 are measured). A count in a task
    file is a premise; this is the measurement.
    """
    found = {p.stem for p in (REPO / "state").glob("*.json")
             if _is_cycle_payload(p) and publish.is_rejudgement(json.loads(
                 p.read_text(encoding="utf-8")))}
    assert found == set(REJUDGED), sorted(found ^ set(REJUDGED))


def _is_cycle_payload(path: Path) -> bool:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(doc, dict) and "findings_detail" in doc


@pytest.mark.parametrize("cycle", sorted(REJUDGED))
def test_every_rejudged_finding_is_on_the_log(cycle, log):
    """DN-003 decision 1. A judgement of record that is not on the log fails DD-001: a stranger
    replaying the log gets a different instrument than the one that published."""
    p = payload(cycle)
    assert len(p["findings_detail"]) == REJUDGED[cycle]
    missing = [f["finding_id"] for f in p["findings_detail"] if f["finding_id"] not in log["by_id"]]
    assert not missing, f"{cycle}: {len(missing)} Finding(s) not on the log, e.g. {missing[:3]}"


@pytest.mark.parametrize("cycle", sorted(REJUDGED))
def test_no_rejudged_finding_is_an_orphan(cycle, log):
    """Task decision 4's second half: a re-judged Finding whose cited `obs_id` resolves is not
    an orphan. All of them resolve, and they resolve to the SOURCE cycle's Observations —
    which is what makes publishing a judgement without publishing an Observation legitimate."""
    p = payload(cycle)
    missing = sorted({o for f in p["findings_detail"] for o in (f.get("evidence") or [])}
                     - log["obs"])
    assert not missing, f"{cycle} cites {len(missing)} obs_id(s) not on the log: {missing[:3]}"


def test_the_scaffold_orphans_are_still_a_hundred_and_twenty(log):
    """Task decision 4. The 120 are history and stay history; a 121st would mean this task
    published a Finding whose evidence the log does not hold."""
    orphans = {ev["finding_id"] for _i, ev in log["findings"]
               if any(o not in log["obs"] for o in (ev.get("evidence") or []))}
    assert len(orphans) == SCAFFOLD_ORPHANS
    assert orphans <= log["unretained"], sorted(orphans - log["unretained"])[:5]


def test_a_rejudged_payload_carries_no_observation():
    """A re-judgement creates no evidence (DN-003 decision 2). Asserted on the payloads as well
    as refused by `write_events`, because the refusal is only reached when someone publishes."""
    for cycle in sorted(REJUDGED):
        assert payload(cycle)["observations_detail"] == [], cycle


# ------------------------------------------------------------------ decision 5: the order

def test_publication_order_puts_every_predecessor_first():
    """Task decision 2. Derived from the chain, not typed: `publication_order` sorts by
    `(generation, name)`, so a judgement cannot be ordered ahead of the one it replaces."""
    order = publish.publication_order(REJUDGED)
    at = {c: i for i, c in enumerate(order)}
    for cycle in order:
        pred = publish.supersedes_of(cycle)
        if pred in at:
            assert at[pred] < at[cycle], f"{pred} is ordered after {cycle}"


@pytest.mark.parametrize("cycle", sorted(REJUDGED))
def test_every_payloads_predecessor_precedes_it_on_the_log(cycle, log):
    """DN-003 decision 5, as a property of the LOG rather than of the publishing script.

    The log's sequence should be the sequence in which the project asserted its judgements, so
    the last Finding of the superseded cycle must appear before the first Finding of the cycle
    that supersedes it. This is what a typed publication order cannot promise and a derived one
    can: the check is against the file that was written, not against the list that drove it.
    """
    pred = publish.supersedes_of(cycle)
    pred_payload = payload(pred)
    first = min(log["by_id"][f["finding_id"]][0] for f in payload(cycle)["findings_detail"])
    last = max(log["by_id"][f["finding_id"]][0] for f in pred_payload["findings_detail"]
               if f["finding_id"] in log["by_id"])
    assert last < first, (f"{cycle} starts at log position {first}, but {pred} is still being "
                          f"written at {last}")


# ------------------------------------------------------------------ decision 3: supersession

@pytest.mark.parametrize("cycle", sorted(REJUDGED))
def test_every_rejudged_finding_is_paired_with_the_one_it_replaces(cycle, log):
    """One to one on (site, leg) — the key a matrix row is built on, and the only key under
    which "the current judgement of this surface for this check" is a single Finding.

    **Every Finding of all fourteen pairs, and the zero is worth stating.** A Finding with no
    counterpart in its predecessor would be legitimate — cycle 1 has no `link_probe` leg, so a
    generation that introduced a rule reading it would register judgements the previous
    generation could not make — but it would also mean the chain forks, and a reader asking
    what superseded what would get a partial answer for that leg. None of the fourteen forks.
    """
    pred = publish.supersedes_of(cycle)
    by_key = {(f["target_doc_id"], f["leg"]): f["finding_id"]
              for f in payload(pred)["findings_detail"]}
    pred_legs = {leg for _d, leg in by_key}
    unpaired = []
    for f in payload(cycle)["findings_detail"]:
        old = by_key.get((f["target_doc_id"], f["leg"]))
        if old is None:
            unpaired.append((f["target_doc_id"], f["leg"]))
            continue
        assert log["pairs"].get(f["finding_id"]) == old, (
            f"{cycle}: {f['finding_id']} should supersede {old} on "
            f"{(f['target_doc_id'], f['leg'])}")
    # The legitimate case the docstring names, and only it: a leg the predecessor did not judge
    # AT ALL. `scan_2026-09-10_rj4` is the first to have one — the seven generation-11 to -13
    # legs, 292 Findings (`cc_tasks/2026-09-18_rejudge_seven_legs.md`). An unpaired Finding on
    # a leg the predecessor DID judge is still a fork, and still fails here.
    forks = [k for k in unpaired if k[1] in pred_legs]
    assert not forks, (f"{cycle} has {len(forks)} Finding(s) on a leg {pred} judged, with no "
                       f"counterpart there: {forks[:5]}")
    assert len(unpaired) == NEW_LEG_FINDINGS.get(cycle, 0), (
        f"{cycle}: {len(unpaired)} Finding(s) on legs {pred} never judged: "
        f"{sorted({k[1] for k in unpaired})}")


def test_the_pairing_is_one_to_one(log):
    """No Finding supersedes two, and no Finding is superseded by two. One judgement of record
    per (site, leg) per generation is the whole property; a fan-out anywhere in the chain makes
    "is this current" unanswerable."""
    olds = list(log["pairs"].values())
    assert len(olds) == len(set(olds)), "a Finding is superseded by more than one successor"


def test_the_report_snapshot_is_on_the_log_and_the_graph_can_say_it_is_not_current(log):
    """**The task's gate asked for the opposite and the opposite is not true.**

    §3 asks that "for the report's snapshot every Result's Finding is current (no successor)".
    It cannot be, and the two halves of this task are why: `scan_2026-09-10_rj2` is the
    published report's snapshot (`docs/reports/publication.yaml`), and generation 10 judged
    cycle 4 again as `scan_2026-09-10_rj3` on 2026-09-13. Publishing every re-judgement in
    generation order — DN-003 decisions 1 and 5, which this same task orders — necessarily puts
    rj3 on the log after rj2, and supersession then says so.

    So the checkable statement is the true one, and it is stronger: every Finding of the
    snapshot is on the log, every one of them has exactly one successor, and that successor is
    `scan_2026-09-10_rj3`. The published report is one generation behind the instrument, by
    exactly one generation, and the graph can now say which — which is what DN-003 decision 3
    exists for and what its closing paragraph asks the standing cadence to stop producing.
    """
    snap = payload(SNAPSHOT_CYCLE)["findings_detail"]
    assert all(f["finding_id"] in log["by_id"] for f in snap)
    successor = {f["finding_id"] for f in payload("scan_2026-09-10_rj3")["findings_detail"]}
    superseded = {old: new for new, old in log["pairs"].items()}
    for f in snap:
        assert superseded.get(f["finding_id"]) in successor, (
            f"{f['finding_id']} of the report snapshot has no successor in "
            f"scan_2026-09-10_rj3")


# ------------------------------------------------------------------ decision 4: the shards

def test_the_log_is_append_only_against_its_committed_bytes():
    """**Every tracked shard's committed bytes are a PREFIX of what it holds now.**

    The standing form of the task's byte-prefix check, and it outlives the task: it is true of
    an append-only log at every commit, not only at this one. `git show` is the baseline
    because it is the only copy of the shard that this working tree cannot have edited.
    """
    tracked = subprocess.run(["git", "ls-files", "events/"], capture_output=True, text=True,
                             cwd=REPO).stdout.split()
    checked = 0
    for rel in tracked:
        if not rel.endswith(".jsonl"):
            continue
        was = subprocess.run(["git", "show", f"HEAD:{rel}"], capture_output=True, cwd=REPO)
        if was.returncode:
            continue
        now = (REPO / rel).read_bytes()
        assert now.startswith(was.stdout), (
            f"{rel}: the committed bytes are no longer a prefix of the file — "
            f"{len(was.stdout)} committed, {len(now)} now. An append-only log was rewritten.")
        checked += 1
    assert checked >= 40, f"only {checked} shard(s) checked; the log has ~50"


@pytest.mark.parametrize("cycle,shard", sorted(ALREADY_ON_A_NUMBERED_SHARD.items()))
def test_a_cycle_already_on_a_numbered_shard_is_not_moved(cycle, shard):
    """DN-003 decision 4's second clause. `shard_for` DISCOVERS the shard a cycle's Findings
    are already on rather than reading a table, which is what lets "one shard per cycle" and
    "the log is not rewritten" hold at the same time."""
    ids = [f["finding_id"] for f in payload(cycle)["findings_detail"]]
    assert publish.shard_name(publish.shard_for(cycle, ids)) == f"events/{shard}"


@pytest.mark.parametrize("cycle", sorted(set(REJUDGED) - set(ALREADY_ON_A_NUMBERED_SHARD)))
def test_every_other_cycle_has_its_own_named_shard(cycle):
    """One shard per cycle, named from the cycle (DN-003 decision 4). The shard is the unit an
    operator reaches for when something is wrong, and `events/batch-040.jsonl` is not a name
    anyone can reach for."""
    path = REPO / "events" / f"cycle-{cycle}.jsonl"
    assert path.is_file(), f"{cycle} has no named shard at {path}"
    ids = {f["finding_id"] for f in payload(cycle)["findings_detail"]}
    on_shard = {json.loads(l)["finding_id"] for l in path.read_text(encoding="utf-8").splitlines()
                if l.strip() and json.loads(l).get("event_type") == publish.FIND_EVENT}
    assert on_shard == ids


def test_the_cycle_batch_table_is_gone():
    """Task decision 1. A typed cycle → batch table had to be edited before every publication,
    and silently sent an unlisted cycle to `SCAN_BATCH`, a shard three other cycles owned."""
    assert not hasattr(publish, "CYCLE_BATCH")
    assert not hasattr(publish, "batch_for")


def test_a_named_cycle_shard_is_replayed_by_default(tmp_path, monkeypatch):
    """A cycle shard is a GRAPH shard, unlike a tagged one. If `replay()` skipped it the events
    would be written and never projected — visible nowhere, which is the worst shape a defect
    in an append-only log can take."""
    events = tmp_path / "events"
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.1"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    eventlog.append({"event_type": "a"}, batch=1)
    eventlog.append({"event_type": "b"}, cycle="scan_2026-09-07_rj9")
    eventlog.append({"event_type": "c"}, batch=2)
    assert [e["event_type"] for e in eventlog.replay()] == ["a", "c", "b"]
    assert [p.name for p in eventlog.shards()] == [
        "batch-001.jsonl", "batch-002.jsonl", "cycle-scan_2026-09-07_rj9.jsonl"]


def test_a_cycle_shard_is_not_a_tagged_shard(tmp_path, monkeypatch):
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")
    with pytest.raises(ValueError, match="already named"):
        eventlog._shard_path(cycle="scan_x", tag="tevv")
    with pytest.raises(ValueError, match="exactly one of"):
        eventlog._shard_path(batch=1, cycle="scan_x")
    with pytest.raises(ValueError, match="exactly one of"):
        eventlog._shard_path()
    with pytest.raises(ValueError, match="cycle must match"):
        eventlog._shard_path(cycle="../escape")


# ------------------------------------------------------------------ the refusals (decision 1)

@pytest.fixture
def iso(tmp_path, monkeypatch):
    """A throwaway log, and `publish` pointed at it. The autouse guard in `conftest.py`
    refuses any append to the real shards; this is the sanctioned way past it."""
    events = tmp_path / "events"
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.1"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    return tmp_path


def _finding(fid, doc="host:x", leg="A1", evidence=()):
    return {"finding_id": fid, "rule_id": "RULE-A1-v1", "rule_version": "v1", "leg": leg,
            "spec_code": "A1", "verdict": "pass", "reason": "r", "params_hash": "p" * 64,
            "target_doc_id": doc, "evidence": list(evidence)}


def _rejudged(cycle="scan_x_rj1", findings=None, obs=()):
    return {"cycle": cycle, "cycle_kind": "rejudged", "derived_from": "scan_x",
            "params_hash": "p" * 64, "findings_detail": findings or [_finding("f1")],
            "control_findings_detail": [], "observations_detail": list(obs)}


def test_publish_refuses_a_rejudgement_that_carries_an_observation(iso):
    """A payload with an Observation is a measurement wearing a re-judgement's name."""
    p = _rejudged(obs=[{"obs_id": "o1"}])
    with pytest.raises(SystemExit, match="creates no evidence"):
        publish.write_events(p, iso / "scan_x_rj1.json")


def test_publish_refuses_a_rejudgement_citing_an_obs_id_not_on_the_log(iso, monkeypatch):
    """The refusal that distinguishes a re-judgement from a measurement.

    A measured cycle may publish a Finding and the Observation behind it in one breath. A
    re-judgement may not: its whole claim is that the evidence was ALREADY sufficient, so an
    `obs_id` the log does not hold means its source cycle was never published — and that is
    named here rather than found later as an orphan the log then keeps forever.

    The SOURCE cycle's payload is on disk here and its Observations are still not on the log,
    which is the exact shape of the defect: a re-judgement published from a `state/` directory
    that holds more than the log does.
    """
    _predecessor_on_disk(iso, monkeypatch, "scan_x")
    p = _rejudged(findings=[_finding("f1", evidence=["o-missing"])])
    with pytest.raises(SystemExit, match="neither on the log nor in this payload"):
        publish.write_events(p, iso / "scan_x_rj1.json")


def _predecessor_on_disk(root: Path, monkeypatch, cycle: str, findings=()):
    """A `state/<cycle>.json` for the payload a re-judgement supersedes, under a tmp REPO."""
    state = root / "state"
    state.mkdir(exist_ok=True)
    (state / f"{cycle}.json").write_text(json.dumps(
        {"cycle": cycle, "findings_detail": list(findings), "observations_detail": []}),
        encoding="utf-8")
    monkeypatch.setattr(publish, "REPO", root)


def test_publish_refuses_when_the_judgement_it_supersedes_is_not_on_the_log(iso, tmp_path,
                                                                            monkeypatch):
    """DN-003 decision 5 in the one place it binds. Publishing out of generation order leaves a
    hole in the chain, and "the current judgement of this surface" stops being answerable."""
    state = tmp_path / "state"
    state.mkdir()
    (state / "scan_x_rj1.json").write_text(json.dumps(
        {"cycle": "scan_x_rj1", "cycle_kind": "rejudged", "derived_from": "scan_x",
         "params_hash": "p" * 64, "findings_detail": [_finding("older")],
         "observations_detail": []}), encoding="utf-8")
    monkeypatch.setattr(publish, "REPO", tmp_path)
    p = _rejudged(cycle="scan_x_rj2", findings=[_finding("f2")])
    with pytest.raises(SystemExit, match="are not on the log"):
        publish.write_events(p, tmp_path / "scan_x_rj2.json")


def test_promote_evidence_refuses_a_payload_with_no_staging_root(tmp_path):
    """**The latent defect this task found, and it would have deleted the repository.**

    `promote_evidence` ends by removing the staging directory. A payload with no
    `evidence_root` — which is every re-judged payload, because a re-judgement fetches nothing
    — made `Path("")`, and `REPO / Path("")` is the REPOSITORY. It never fired because the two
    re-judgements published in 2026-09-08 were published with `--no-promote`, so the flag a
    human had to remember was the only thing between `publish.py --from state/<any _rj>.json`
    and `shutil.rmtree` on the working tree. `main` now refuses promotion for a re-judgement
    outright; this is the second lock on the same door, and it is the one that holds for a
    caller reaching the function directly.
    """
    with pytest.raises(SystemExit, match="names no `evidence_root`"):
        publish.promote_evidence({"observations_detail": []})
    with pytest.raises(SystemExit, match="repository root"):
        publish.promote_evidence({"observations_detail": [], "evidence_root": "."},
                                 staging=publish.REPO)


def test_a_rejudgement_is_published_without_promotion(iso, monkeypatch, capsys):
    """`main` never reaches the promotion path for a re-judgement, with or without the flag."""
    called = []
    monkeypatch.setattr(publish, "promote_evidence", lambda *a, **k: called.append(1) or {})
    src = iso / "scan_x_rj1.json"
    src.write_text(json.dumps(_rejudged(findings=[_finding("f1")])), encoding="utf-8")
    monkeypatch.setattr(publish, "REPO", iso)
    (iso / "state").mkdir(exist_ok=True)
    (iso / "state" / "scan_x.json").write_text(json.dumps(
        {"cycle": "scan_x", "findings_detail": [], "observations_detail": []}),
        encoding="utf-8")
    publish.main(["--from", str(src)])
    assert not called
    out = json.loads(capsys.readouterr().out)
    assert out["evidence_promotion"].startswith("refused")
    assert out["finding_events_written"] == 1
    assert out["shard"] == "events/cycle-scan_x_rj1.jsonl"


# ------------------------------------------------------------------ decision 4: the census

def test_the_census_reports_the_three_kinds_apart():
    """Task decision 4. `findings_evidence_unretained` and the orphan count mean different
    things per kind — among the measured Findings an orphan is the 2026-09-06 scaffold's
    discarded controls, among the re-judged ones it would be a judgement published ahead of
    its source cycle — and one number covering both reports the second as normal."""
    c = publish.census()
    assert set(c["by_kind"]) <= set(publish.KINDS) | {"unattributed"}
    for kind in ("measured", "self", "rejudged"):
        assert kind in c["by_kind"], c["by_kind"].keys()
    assert c["by_kind"]["rejudged"]["orphan_findings"] == 0
    assert c["by_kind"]["rejudged"]["findings"] == sum(REJUDGED.values())
    total = sum(v["findings"] for v in c["by_kind"].values())
    assert total == c["findings"]


def test_the_census_attributes_every_finding_it_can():
    """The only Findings the census cannot name a cycle for are the scaffold's 120, whose
    payload did not survive. `unattributed` is a measurement, not a shrug: it is asserted to
    be exactly those, so a future publication that forgot its cycle field lands here loudly."""
    c = publish.census()
    unattributed = c["by_kind"].get("unattributed", {"findings": 0})
    assert unattributed["findings"] == SCAFFOLD_UNATTRIBUTED
    assert unattributed["orphan_findings"] == SCAFFOLD_ORPHANS
    # Every orphan on the log is one of the scaffold's: nothing this task published joined them.
    assert sum(v["orphan_findings"] for v in c["by_kind"].values()) == SCAFFOLD_ORPHANS


# ------------------------------------------------------------------ the invariant readings

@pytest.mark.parametrize("cycle", sorted(REJUDGED))
def test_both_invariant_readings_are_zero_on_every_rejudged_payload(cycle):
    """§3's "both invariant readings 0". **No verdict about a product rests on evidence nobody
    collected**, read with `robots_disallowed` as blindness (`UNDER_V5`) and again without the
    host/product distinction (`UNDER_V5_ALL_RULES`).

    The machinery is IMPORTED from `tests/test_invariants.py` rather than copied: a second
    implementation of "is this verdict blind" is a second thing to be wrong, and the copy that
    drifted would be the one guarding the payloads this task just put on the log. The pinned
    history in that file is untouched — this asserts the reading for the ten payloads it does
    not pin, and re-asserts it for the four it does.
    """
    inv = _mod(REPO / "tests" / "test_invariants.py", "invariants_for_rjlog")
    p = payload(cycle)
    for product_only in (True, False):
        blind = inv.blind_verdicts(p, product_only=product_only, harness=5)
        assert not blind, (f"{cycle} under harness-5 "
                           f"({'product only' if product_only else 'all rules'}): {blind[:5]}")


# ------------------------------------------------------------------ the graph (decision 3)

@pytest.fixture(scope="module")
def graph():
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                        # noqa: BLE001
        pytest.skip(f"Neo4j unreachable, supersession unverified in the graph: {exc}")
    with driver.session(database=cfg["neo4j"]["database"]) as s:
        yield s
    driver.close()


def test_the_graph_holds_one_supersedes_edge_per_pair_on_the_log(graph, log):
    """§3's count clause: `SUPERSEDES` equals the count of re-judged Findings whose predecessor
    exists. Both sides are measured — the log's pairs and the graph's edges — because a
    projection that dropped half of them and a log that never held them read identically from
    inside the graph."""
    edges = graph.run("MATCH (:Finding)-[r:SUPERSEDES]->(:Finding) RETURN count(r)").single()[0]
    assert edges == len(log["pairs"]), (
        f"the log holds {len(log['pairs'])} supersession pairs and the graph {edges} edges; "
        f"the projection is stale")
    # Every re-judged Finding pairs, except those on a leg the predecessor never judged.
    assert edges == sum(REJUDGED.values()) - sum(NEW_LEG_FINDINGS.values())


def test_no_finding_supersedes_itself_or_forms_a_cycle(graph):
    """A chain, not a loop. `_rjN -> _rj(N-1)` is acyclic by construction, and the assertion
    is here because "by construction" is what every broken invariant in this repo was."""
    assert graph.run("MATCH (f:Finding)-[:SUPERSEDES]->(f) RETURN count(f)").single()[0] == 0
    assert graph.run(
        "MATCH p = (a:Finding)-[:SUPERSEDES*2..]->(a) RETURN count(p)").single()[0] == 0


@pytest.mark.parametrize("cycle", ["scan_2026-09-07_rj3", "scan_2026-09-07b_rj4",
                                   "scan_2026-09-09_rj3", "scan_2026-09-10_rj4",
                                   "self_2026-09-13_rj1"])
def test_the_newest_judgement_of_every_cycle_is_current(graph, cycle):
    """A Finding with no successor is current (DN-003 decision 3). The five newest judgements —
    generation 10, the instrument as it stands — are the ones a reader asking "what does this
    project say about this surface today" must land on."""
    ids = [f["finding_id"] for f in payload(cycle)["findings_detail"]]
    stale = graph.run(
        "MATCH (f:Finding) WHERE f.finding_id IN $ids AND NOT f.current "
        "RETURN f.finding_id AS id LIMIT 5", ids=ids).values()
    assert not stale, f"{cycle} has {len(stale)} superseded Finding(s): {stale}"
    n = graph.run("MATCH (f:Finding) WHERE f.finding_id IN $ids RETURN count(f)",
                  ids=ids).single()[0]
    assert n == len(ids), f"{cycle}: {len(ids) - n} Finding(s) missing from the graph"


def test_the_graph_says_the_published_report_is_one_generation_behind(graph):
    """**The finding this task produces, stated as a query rather than as a sentence.**

    The published report's snapshot is `scan_2026-09-10_rj2`
    (`docs/reports/publication.yaml`); generation 10 judged the same evidence again on
    2026-09-13 and nothing republished. Before this task the graph could not say so — the
    re-judgement was not on the log at all. Now every Finding of the snapshot has exactly one
    successor and it is in `scan_2026-09-10_rj3`, which is what DN-003 decision 3 means by
    "the projection can say so by query, not by convention", and what its closing paragraph
    asks the standing cadence to stop producing.
    """
    ids = [f["finding_id"] for f in payload(SNAPSHOT_CYCLE)["findings_detail"]]
    current = graph.run("MATCH (f:Finding) WHERE f.finding_id IN $ids AND f.current "
                        "RETURN count(f)", ids=ids).single()[0]
    assert current == 0, f"{current} Finding(s) of the report snapshot have no successor"
    succ = graph.run(
        "MATCH (a:Finding)-[:SUPERSEDES]->(b:Finding) WHERE b.finding_id IN $ids "
        "RETURN a.cycle AS cycle, count(*) AS n", ids=ids).values()
    assert succ == [["scan_2026-09-10_rj3", len(ids)]], succ
