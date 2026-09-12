"""The framework record has ONE writer, and that writer refuses to drop what it did not author.

Task `cc_tasks/2026-09-11_framework_single_writer.md`. The incident: `build_framework_graph.py`
regenerated `framework/ai_readiness_framework.json` from the skeleton and silently dropped 22
`MEASURED_BY` edges, A12's construct and internal refs, and six `counts` keys — 843 deleted
lines caught by a diff and a `git checkout`, which is a habit, not a guard
(`2026-09-11_a3_a10_sources_RESULT.md` §7). These are the guards.

1. **Single writer** — statically, no module in the repo but `scripts/framework_writeback.py`
   opens the record for writing. The scanner is exercised on a positive control so the
   assertion cannot pass vacuously.
2. **Refusal** — a write that removes a node, an edge or a `counts` key is refused without
   `force=True` + `reason`; with them, the reason lands on the `framework_writeback` event.
3. **No-op regeneration** — the skeleton over `HEAD` reproduces the record byte for byte.
4. **The delta is on the event** — added, removed, changed, with before/after values.
"""
from __future__ import annotations

import ast
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import build_framework_graph as bfg  # noqa: E402
import framework_writeback as fw  # noqa: E402
from kg import eventlog  # noqa: E402

RECORD = REPO / "framework" / "ai_readiness_framework.json"
RECORD_NAME = "ai_readiness_framework.json"
#: Where a writer could hide. `tests/` is scanned too: a test that writes the real record is
#: a writer.
SCAN_ROOTS = ("scripts", "kg", "assessment", "tests")


# --------------------------------------------------------------- 1. the single writer
def writers_in(source: str, filename: str = "<module>") -> list:
    """Every call in `source` that writes to the framework record, as `(lineno, text)`.

    A name is an ALIAS of the record if it is bound, in any scope, to a PATH-SHAPED expression
    over the record or an existing alias: the name itself (`JSON_PATH = FRAMEWORK`), a module
    attribute (`fw.FRAMEWORK`, `bfg.OUT`), `REPO / "framework" / "ai_readiness_framework.json"`,
    `Path(<alias>)`, `str(<alias>)`, `<x> or <alias>` (the writer's own `path = path or
    FRAMEWORK`), or an argparse `default=` built from one (`--out`, then read back as `a.out`).
    `g = json.loads(FRAMEWORK.read_text())` is NOT an alias: what it binds is the content, and
    a payload derived from the content is not the record. Names match on token boundaries.
    A write is `<alias>.write_text(...)`, `open(<alias>, "w"|"a"|...)`, `<alias>.open("w")`,
    and any of those on a `Path(<alias>)`. Reads are not writes.
    """
    tree = ast.parse(source, filename)
    lines = source.splitlines()

    def seg(node) -> str:
        return ast.get_source_segment(source, node) or ""

    import re
    aliases = {RECORD_NAME}

    def mentions(text: str) -> bool:
        return any(re.search(r"(?<![\w.])" + re.escape(a) + r"(?!\w)", text) if "." not in a
                   else re.search(r"(?<!\w)" + re.escape(a) + r"(?!\w)", text)
                   for a in aliases)

    def path_shaped(node) -> bool:
        """Is this expression the record's path (or built from it), as opposed to its content?"""
        if isinstance(node, (ast.Name, ast.Attribute, ast.Constant)):
            return mentions(seg(node))
        if isinstance(node, ast.BoolOp):
            return any(path_shaped(v) for v in node.values)
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            return path_shaped(node.left) or path_shaped(node.right)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("Path", "str") and node.args:
            return path_shaped(node.args[0])
        return False

    # bindings, in any scope, to a path-shaped expression over the record or an alias
    changed = True
    while changed:
        changed = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                    and isinstance(node.targets[0], ast.Name) \
                    and node.targets[0].id not in aliases and path_shaped(node.value):
                aliases.add(node.targets[0].id)
                changed = True
    # argparse defaults built from an alias: `add_argument("--out", default=str(OUT))`, read
    # back as `a.out` / `args.out`
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
                and node.func.attr == "add_argument":
            flag = next((seg(a).strip("\"'") for a in node.args if isinstance(a, ast.Constant)), "")
            for kw in node.keywords:
                if kw.arg == "default" and path_shaped(kw.value):
                    dest = flag.lstrip("-").replace("-", "_")
                    aliases |= {f"{ns}.{dest}" for ns in ("a", "args", "ns", "opts", "options")}
    # a module that imports the writer's FRAMEWORK / another module's OUT by attribute
    aliases |= {"fw.FRAMEWORK", "bfg.OUT", "framework_writeback.FRAMEWORK"}

    def names_record(node) -> bool:
        return path_shaped(node)

    def is_write_mode(call: ast.Call) -> bool:
        mode = None
        if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant):
            mode = call.args[1].value
        for kw in call.keywords:
            if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                mode = kw.value.value
        return isinstance(mode, str) and any(c in mode for c in "wa+x")

    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        f = node.func
        # <alias>.write_text(...) / Path(<alias>).write_text(...)
        if isinstance(f, ast.Attribute) and f.attr in ("write_text", "write_bytes") \
                and names_record(f.value):
            hits.append((node.lineno, lines[node.lineno - 1].strip()))
        # open(<alias>, "w") / <alias>.open("w")
        if isinstance(f, ast.Name) and f.id == "open" and node.args \
                and names_record(node.args[0]) and is_write_mode(node):
            hits.append((node.lineno, lines[node.lineno - 1].strip()))
        if isinstance(f, ast.Attribute) and f.attr == "open" and names_record(f.value) \
                and (is_write_mode(ast.Call(func=f, args=[ast.Constant(""), *node.args],
                                            keywords=node.keywords))):
            hits.append((node.lineno, lines[node.lineno - 1].strip()))
    return sorted(set(hits))


def test_the_scanner_catches_every_shape_a_writer_takes():
    """Positive control. An assertion of "no other writer" over a scanner that catches nothing
    is a vacuous pass; each of these is a shape a past or plausible writer used."""
    src = '''
from pathlib import Path
import json
REPO = Path(".")
FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
JSON_PATH = FRAMEWORK
def a(g):
    FRAMEWORK.write_text(json.dumps(g))                     # shape 1: the a3a10 incident
def b(g):
    Path(JSON_PATH).write_text(json.dumps(g))               # shape 2: build_measurement_specs
def c(g):
    with open(FRAMEWORK, "w") as fh:
        json.dump(g, fh)                                    # shape 3: builtin open
def d(g):
    with JSON_PATH.open("a", encoding="utf-8") as fh:
        fh.write("x")                                       # shape 4: Path.open
def e(args):
    Path(args.out).write_text("{}")                         # shape 5: argparse default
def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(FRAMEWORK))
def reads_only():
    return json.loads(FRAMEWORK.read_text())                # not a write
def other_file(g):
    (REPO / "state" / "x.json").write_text(json.dumps(g))   # not the record
'''
    hits = writers_in(src)
    assert [h[0] for h in hits] == [8, 10, 12, 15, 18], hits


def test_only_framework_writeback_opens_the_record_for_writing():
    """Decision 1. Every module under the scan roots, `scripts/framework_writeback.py` excepted."""
    offenders = {}
    for root in SCAN_ROOTS:
        for path in sorted((REPO / root).rglob("*.py")):
            if path == REPO / "scripts" / "framework_writeback.py":
                continue
            if "__pycache__" in path.parts:
                continue
            hits = writers_in(path.read_text(encoding="utf-8"), str(path))
            if hits:
                offenders[str(path.relative_to(REPO))] = hits
    assert not offenders, json.dumps(offenders, indent=1)


def test_the_writer_itself_writes_only_in_save():
    src = (REPO / "scripts" / "framework_writeback.py").read_text(encoding="utf-8")
    hits = writers_in(src, "framework_writeback.py")
    tree = ast.parse(src)
    save = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "save")
    assert hits, "the writer does not write?"
    assert all(save.lineno <= ln <= save.end_lineno for ln, _ in hits), hits


# --------------------------------------------------------------- fixtures for 2 and 4
@pytest.fixture
def record_copy(tmp_path, monkeypatch):
    """A byte copy of the record under tmp_path, with the event log redirected there too."""
    events = tmp_path / "events"
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    dst = tmp_path / "framework" / RECORD_NAME
    dst.parent.mkdir()
    shutil.copyfile(RECORD, dst)
    return dst


def _events(tmp_path) -> list:
    shard = tmp_path / "events" / f"batch-{fw.BATCH:03d}_{fw.TAG}.jsonl"
    if not shard.exists():
        return []
    return [json.loads(l) for l in shard.read_text(encoding="utf-8").splitlines() if l.strip()]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------- 2. the refusal
def test_a_write_that_drops_an_edge_is_refused_without_force(record_copy, tmp_path):
    before = record_copy.read_bytes()
    g = _load(record_copy)
    victim = next(e for e in g["edges"] if e["type"] == "MEASURED_BY")
    g["edges"].remove(victim)
    with pytest.raises(fw.RefusedWrite) as exc:
        fw.save(g, script="test", task="test", changes={}, path=record_copy)
    msg = str(exc.value)
    assert "1 edge(s)" in msg and "MEASURED_BY" in msg and victim["from"] in msg, msg
    assert record_copy.read_bytes() == before, "the refused write touched the file"
    assert _events(tmp_path) == [], "the refused write logged an event"


def test_a_write_that_drops_a_node_is_refused_and_names_it(record_copy):
    g = _load(record_copy)
    victim = next(n for n in g["nodes"] if "MeasurementSpec" in n["labels"])
    g["nodes"].remove(victim)
    with pytest.raises(fw.RefusedWrite, match="1 node\\(s\\).*MeasurementSpec.*" + victim["id"]):
        fw.save(g, script="test", task="test", changes={}, path=record_copy)


def test_a_write_that_drops_a_counts_key_is_refused(record_copy):
    g = _load(record_copy)
    del g["counts"]["rules_built"]                     # the one key `recount` cannot restore
    with pytest.raises(fw.RefusedWrite, match="counts key\\(s\\): rules_built"):
        fw.save(g, script="test", task="test", changes={}, path=record_copy)


def test_the_incident_itself_is_refused(record_copy):
    """`generate()` alone — the skeleton with nothing preserved — over the record. This is the
    exact write the a3a10 task caught by hand; the refusal must name what it would drop."""
    with pytest.raises(fw.RefusedWrite) as exc:
        fw.save(bfg.generate(), script="test", task="test", changes={}, path=record_copy)
    msg = str(exc.value)
    assert "MEASURED_BY" in msg and "MeasurementSpec" in msg and "counts key(s)" in msg, msg


def test_force_without_a_reason_is_refused(record_copy):
    g = _load(record_copy)
    g["edges"].pop()
    with pytest.raises(fw.RefusedWrite, match="--force without --reason"):
        fw.save(g, script="test", task="test", changes={}, path=record_copy, force=True)
    with pytest.raises(fw.RefusedWrite, match="--force without --reason"):
        fw.save(g, script="test", task="test", changes={}, path=record_copy, force=True,
                reason="   ")


def test_a_forced_drop_is_written_and_the_reason_is_on_the_event(record_copy, tmp_path):
    g = _load(record_copy)
    victim = next(e for e in g["edges"] if e["type"] == "MEASURED_BY")
    g["edges"].remove(victim)
    out = fw.save(g, script="test", task="test", changes={"x": 1}, path=record_copy,
                  force=True, reason="synthetic drop for the refusal test")
    assert out["written"] is True
    after = _load(record_copy)
    assert victim not in after["edges"]
    (ev,) = _events(tmp_path)
    assert ev["event_type"] == fw.EVENT
    assert ev["forced"]["reason"] == "synthetic drop for the refusal test"
    assert ev["delta"]["edges_removed"] == [victim]
    assert ev["delta_summary"]["edges_removed"] == {"MEASURED_BY": 1}
    assert ev["framework_sha256"] == out["framework_sha256"]


def test_the_cli_flags_are_the_same_on_every_writer():
    """Decision 2 says `--force --reason "<text>"`; a writer that spells it differently is a
    writer nobody can force the same way twice."""
    import argparse
    ap = argparse.ArgumentParser()
    fw.add_force_args(ap)
    a = ap.parse_args(["--force", "--reason", "why"])
    assert fw.force_kwargs(a) == {"force": True, "reason": "why"}
    assert fw.force_kwargs(ap.parse_args([])) == {"force": False, "reason": None}
    for name in ("build_framework_graph", "build_measurement_specs", "framework_writeback_rules",
                 "framework_writeback_measured", "framework_writeback_decisions",
                 "framework_writeback_evidence", "framework_writeback_normalize",
                 "add_candidate_indicator"):
        src = (REPO / "scripts" / f"{name}.py").read_text(encoding="utf-8")
        assert "fw.add_force_args(ap)" in src, name
        assert "**fw.force_kwargs(a)" in src, name


# --------------------------------------------------------------- 3. no-op regeneration
def test_regenerating_from_the_current_skeleton_over_head_is_a_no_op():
    """Decision 3. Generate, merge over the record, recount, serialise: the same bytes."""
    g = bfg.build(fw.load(RECORD))
    fw.apply_counts(g)
    assert fw.serialize(g) == RECORD.read_text(encoding="utf-8")


def test_regenerating_through_the_writer_writes_nothing_and_logs_nothing(record_copy, tmp_path):
    before = record_copy.read_bytes()
    out = fw.save(bfg.build(fw.load(record_copy)), script="test", task="test", changes={},
                  path=record_copy)
    assert out["written"] is False and out["unchanged"] is True
    assert out["delta_summary"] == {"nodes_added": {}, "nodes_removed": {}, "nodes_changed": 0,
                                    "edges_added": {}, "edges_removed": {}, "edges_changed": 0,
                                    "counts_keys_dropped": [], "counts_moved": {}}
    assert record_copy.read_bytes() == before
    assert _events(tmp_path) == []


def test_the_generator_does_not_read_the_candidate_table():
    """A12 is a candidate (DD-054), authored by `add_candidate_indicator`, not by a skeleton
    row. Parsing the candidate table as criterion G is how the incident re-authored it."""
    rows, unparsed = bfg.parse(bfg.SKELETON.read_text(encoding="utf-8"))
    assert unparsed == []
    assert "A12" not in {r["code"] for r in rows}
    gen = bfg.generate()
    assert "ind:A12" not in {n["id"] for n in gen["nodes"]}
    cur = fw.load(RECORD)
    a12 = next(n for n in cur["nodes"] if n["id"] == "ind:A12")
    assert a12["properties"]["status"] == "candidate"
    merged = bfg.merge(gen, cur)
    assert next(n for n in merged["nodes"] if n["id"] == "ind:A12") == a12


def test_what_the_skeleton_does_not_author_is_exactly_what_merge_preserves():
    """The list the RESULT reports, asserted rather than typed: everything in the record that
    `generate()` does not produce, by kind."""
    gen, cur = bfg.generate(), fw.load(RECORD)
    gen_ids = {n["id"] for n in gen["nodes"]}
    gen_edges = {fw._edge_key(e) for e in gen["edges"]}
    preserved_nodes = [n for n in cur["nodes"] if n["id"] not in gen_ids]
    preserved_edges = [e for e in cur["edges"] if fw._edge_key(e) not in gen_edges]
    from collections import Counter
    assert Counter(n["labels"][0] for n in preserved_nodes) == \
        {"MeasurementSpec": 22, "AssessmentConstruct": 1, "AssessmentIndicator": 1}
    assert Counter(e["type"] for e in preserved_edges) == \
        {"MEASURED_BY": 22, "EVIDENCED_BY_INTERNAL": 3, "DECOMPOSES_INTO": 2, "EVIDENCED_BY": 2}
    assert set(cur["counts"]) - set(gen["counts"]) == \
        {"measurement_specs", "collectors_none_known", "rules_built",
         "specs_with_recorded_decision", "candidate_indicators", "indicators_measured"}
    # and nothing the skeleton authors is missing from the record
    assert not (gen_ids - {n["id"] for n in cur["nodes"]})
    assert not (gen_edges - {fw._edge_key(e) for e in cur["edges"]})


def test_a_skeleton_edit_reaches_the_record_and_a_write_back_survives_it(record_copy, tmp_path):
    """The generator preserves write-backs while carrying an authored change. Simulated by
    editing the GENERATED side rather than the skeleton file: a Status cell changes on A1."""
    cur = fw.load(record_copy)
    gen = bfg.generate()
    a1 = next(n for n in gen["nodes"] if n["id"] == "ind:A1")
    a1["properties"]["status"] = "edited-in-test"
    merged = bfg.merge(gen, cur)
    m_a1 = next(n for n in merged["nodes"] if n["id"] == "ind:A1")
    c_a1 = next(n for n in cur["nodes"] if n["id"] == "ind:A1")
    assert m_a1["properties"]["status"] == "edited-in-test"
    assert m_a1["properties"]["measurement_status"] == c_a1["properties"]["measurement_status"]
    assert m_a1["properties"].get("measured_by") == c_a1["properties"].get("measured_by")
    assert list(m_a1["properties"]) == list(c_a1["properties"]), "key order moved"
    out = fw.save(merged, script="test", task="test", changes={}, path=record_copy)
    assert out["written"] is True
    (ev,) = _events(tmp_path)
    assert ev["delta"]["nodes_changed"] == [
        {"id": "ind:A1", "properties": {"status": [c_a1["properties"]["status"],
                                                   "edited-in-test"]}}]
    assert ev["delta"]["edges_removed"] == [] and ev["delta"]["nodes_removed"] == []
    assert "forced" not in ev


# --------------------------------------------------------------- 4. the delta on the event
def test_the_event_carries_the_delta_with_before_and_after(record_copy, tmp_path):
    g = _load(record_copy)
    spec = next(n for n in g["nodes"] if n["id"] == "spec:A1")
    old_rule = spec["properties"]["rule_id"]
    spec["properties"]["rule_id"] = "RULE-A1-test"
    g["nodes"].append({"id": "ind:TEST", "labels": ["AssessmentIndicator"],
                       "properties": {"code": "TEST", "status": "candidate"}})
    g["edges"].append({"from": "ind:TEST", "type": "MEASURED_BY", "to": "spec:A1"})
    e = next(e for e in g["edges"] if e["type"] == "EVIDENCED_BY")
    e["properties"]["doc_id"] = e["properties"]["doc_id"]      # untouched -> not in delta
    out = fw.save(g, script="test", task="test", changes={}, path=record_copy)
    (ev,) = _events(tmp_path)
    d = ev["delta"]
    assert d["nodes_changed"] == [{"id": "spec:A1",
                                   "properties": {"rule_id": [old_rule, "RULE-A1-test"]}}]
    assert [n["id"] for n in d["nodes_added"]] == ["ind:TEST"]
    assert d["edges_added"] == [{"from": "ind:TEST", "type": "MEASURED_BY", "to": "spec:A1"}]
    assert d["edges_changed"] == [] and d["edges_removed"] == [] and d["nodes_removed"] == []
    assert d["counts_moved"]["candidate_indicators"] == [1, 2]
    assert ev["counts_moved"] == out["counts_moved"]
    assert ev["framework_sha256"] == out["framework_sha256"]
    # and the delta is enough to replay: apply it to the old record and get the new one
    old = json.loads(RECORD.read_text(encoding="utf-8"))
    new = _load(record_copy)
    nodes = {n["id"]: n for n in old["nodes"]}
    for n in d["nodes_added"]:
        nodes[n["id"]] = n
    for c in d["nodes_changed"]:
        for k, (_, after) in c["properties"].items():
            nodes[c["id"]]["properties"][k] = after
    edges = {fw._edge_key(e): e for e in old["edges"]}
    for e in d["edges_added"]:
        edges[fw._edge_key(e)] = e
    assert {n["id"]: n for n in new["nodes"]} == nodes
    assert {fw._edge_key(e): e for e in new["edges"]} == edges


def test_a_dry_run_computes_the_delta_and_the_refusal_but_writes_nothing(record_copy, tmp_path):
    before = record_copy.read_bytes()
    g = _load(record_copy)
    g["nodes"][0]["properties"]["name"] = "changed"
    out = fw.save(g, script="test", task="test", changes={}, path=record_copy, dry_run=True)
    assert out["written"] is False and "unchanged" not in out
    assert out["delta_summary"]["nodes_changed"] == 1
    assert record_copy.read_bytes() == before and _events(tmp_path) == []
    g["edges"].pop()
    with pytest.raises(fw.RefusedWrite):
        fw.save(g, script="test", task="test", changes={}, path=record_copy, dry_run=True)


def test_the_first_write_to_an_empty_path_is_all_added(tmp_path, monkeypatch):
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")
    dst = tmp_path / RECORD_NAME
    out = fw.save(bfg.generate(), script="test", task="test", changes={}, path=dst)
    assert out["written"] is True and dst.exists()
    assert out["delta_summary"]["nodes_removed"] == {} and out["delta_summary"]["nodes_added"]


def test_existing_events_are_not_rewritten():
    """Decision 4's last sentence. The shard is append-only; the pre-task events carry no
    `delta` and that is how they stay."""
    shard = REPO / "events" / f"batch-{fw.BATCH:03d}_{fw.TAG}.jsonl"
    evs = [json.loads(l) for l in shard.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert evs, "no framework_writeback events on the ledger"
    first = evs[0]
    assert "delta" not in first and first["event_type"] == fw.EVENT


def test_the_scanner_catches_the_two_writers_that_existed_before_this_task():
    """Positive control on the REAL incident code, not a synthetic module: at `bb660f9` (the
    commit the a3a10 task shipped) `build_framework_graph.main` and
    `build_measurement_specs.main` each wrote the record directly."""
    import subprocess
    expected = {"scripts/build_framework_graph.py": ["Path(a.out).write_text("],
                "scripts/build_measurement_specs.py": ["Path(a.json).write_text("]}
    for rel, needles in expected.items():
        try:
            src = subprocess.run(["git", "show", f"bb660f9:{rel}"], cwd=REPO, check=True,
                                 capture_output=True, text=True).stdout
        except (OSError, subprocess.CalledProcessError) as exc:   # no git / shallow clone
            pytest.skip(f"cannot read {rel} at bb660f9: {exc}")
        hits = writers_in(src, rel)
        assert hits, f"{rel} at bb660f9 wrote the record and the scanner missed it"
        for needle in needles:
            assert any(needle in text for _, text in hits), (needle, hits)
