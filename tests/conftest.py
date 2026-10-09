"""Shared fixtures for extraction tests: redirect all on-disk writes into tmp_path so tests
never touch the real events/, corpus/staging/, or kg/schema.yaml.

The extraction parser reads the *real* kg/schema.yaml (the authoritative type catalogue);
only the event log's schema_version read is redirected to a minimal tmp schema.
"""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import build_projection as _proj  # noqa: E402

from kg import eventlog  # noqa: E402
from kg.extraction import metrics as metrics_mod
from kg.extraction import staging


@pytest.fixture
def ext_iso(tmp_path, monkeypatch):
    events = tmp_path / "events"
    schema = tmp_path / "schema.yaml"
    schema.write_text('schema_version: "0.1"\n', encoding="utf-8")
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", events)
    monkeypatch.setattr(eventlog, "_SCHEMA_PATH", schema)
    monkeypatch.setattr(metrics_mod, "_METRICS_DIR", tmp_path / "metrics")
    monkeypatch.setattr(staging, "_REVIEW_DIR", tmp_path / "proposed")
    return tmp_path


# The real events/ directory is the source of truth (invariant 1). A test that appends to it
# writes synthetic facts into the append-only log, where the no-delete rule then protects them
# forever. This happened: tests/test_ground_truth.py drove phase_score without redirecting the
# event log and left `ground_truth_floor` events for documents `d#c1`/`d#c2` — which do not
# exist — in events/batch-021_ground_truth.jsonl, three of them committed.
#
# Autouse, so no future test can opt out by forgetting. Writes are refused unless _EVENTS_DIR
# has been repointed (ext_iso, or a test's own monkeypatch); reads are untouched, because
# tests that assert against the live ledger are legitimate.
_REAL_EVENTS_DIR = eventlog._EVENTS_DIR


@pytest.fixture(autouse=True)
def no_writes_to_the_real_event_log(monkeypatch):
    real_append = eventlog.append

    # `cycle=` is the named-shard form (DN-003 decision 4, `events/cycle-<name>.jsonl`). It is
    # passed THROUGH rather than dropped: a guard that silently lost the destination would send
    # a cycle's events to `batch-None` and the test asserting the shard would fail for a reason
    # that has nothing to do with what it is testing.
    def guarded(event, batch=None, tag=None, cycle=None):
        if eventlog._EVENTS_DIR == _REAL_EVENTS_DIR:
            raise AssertionError(
                "test appended to the REAL event log "
                f"(event_type={event.get('event_type')!r}, batch={batch}, tag={tag!r}, "
                f"cycle={cycle!r}). "
                "Use the ext_iso fixture, or monkeypatch eventlog._EVENTS_DIR onto tmp_path."
            )
        return real_append(event, batch, tag, cycle)

    monkeypatch.setattr(eventlog, "append", guarded)


@pytest.fixture(scope="session")
def fixture_models_home(tmp_path_factory):
    """One fixture model lock per test session (per xdist worker): a copy of seldon's
    registry, the fixture ids, and a CLI that refuses to run. Built once, because the guard
    below runs on every test."""
    from model_lock import build_models_home
    return build_models_home(tmp_path_factory.mktemp("models_home"))


@pytest.fixture(autouse=True)
def no_live_model_lock(monkeypatch, fixture_models_home):
    """Seldon AD-035 (task MODEL-001): every launcher resolves its model through
    `seldon.models`, which reads the live lock unless `SELDON_MODELS_HOME` says otherwise.
    A test that read the live lock would change meaning on every `seldon models refresh`,
    and one that reached the live lock's CLI would make a PAID call. Autouse, so no test can
    opt out by forgetting: the accessor sees the fixture lock, whose CLI exits 97 without
    calling anything. A test that means to launch writes its own fake CLI and lock
    (`tests/model_lock.py`) and repoints the variable itself."""
    from model_lock import MODELS_HOME_ENV
    monkeypatch.setenv(MODELS_HOME_ENV, str(fixture_models_home))


@pytest.fixture(autouse=True)
def restore_the_pinned_prompt_path(monkeypatch):
    """`apply_arm`/`apply_profile` rebind `model_stub._PROMPT_PATH` as arm-scoped state. A
    test that binds an arm's template and does not put it back leaves every later test reading
    `prompt_version` from the wrong prompt — the same class of defect as the one found in
    production: two reads of what is meant to be one fact, silently disagreeing.

    The restore goes through `monkeypatch`, not a snapshot-and-assign, because ordering bites:
    the guard fixture above already requests `monkeypatch`, so monkeypatch is set up FIRST and
    its undo stack unwinds LAST. A yield-based restore here ran before monkeypatch's undo, and
    monkeypatch then put the polluted value back. Registering the no-op setattr first makes
    this the last undo applied, which is the only ordering that wins."""
    from kg.extraction import model_stub
    monkeypatch.setattr(model_stub, "_PROMPT_PATH", model_stub._PROMPT_PATH)


@pytest.fixture(autouse=True)
def restore_chunked_pilot_run_state(monkeypatch):
    """`chunked_pilot`'s run state is module globals by design — every function reads them at
    call time so an arm can be rebound without threading a config object through. That makes
    them leak between tests: a test that drives `phase_burn` or `apply_arm` and does not put
    them back points every later test at another arm's shard, documents or purpose.

    Autouse and through monkeypatch, for the ordering reason in the fixture above: registered
    first, undone last, so a test's own patches unwind before this one."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    import chunked_pilot as cp
    for name in ("PROFILE", "PROFILE_CLASS", "RUN_ID", "JUDGE_RUN_ID", "SHARD_NO", "TAG",
                 "RAW_DIR", "CORPUS_EPOCH", "EMISSION", "ARM_ROLE", "DOCS", "DOC_PATHS",
                 "PURPOSE", "CHUNK_FILTER", "BATCH_ID"):
        monkeypatch.setattr(cp, name, getattr(cp, name))


@pytest.fixture(autouse=True)
def no_seldon_artifacts_from_tests(monkeypatch):
    """The admission gate's auto-task shells out to the real `seldon` CLI, which no guard
    covered. Wiring `kg.ingest.gate.check` into `kg.manifest.add` made every admission test
    mint a real ResearchTask in the operator's graph — 22 of them, from fixture doc_ids like
    `fcsm-25-03` and `doc-one`, before the run finished. The event-log guard above caught
    nothing because the leak was a subprocess, not an event.

    A test that means to exercise registration monkeypatches `register_gap_task` itself, which
    overrides this. Anything else reaching the real CLI is the defect, and it fails loudly
    rather than quietly writing to a graph the test does not own."""
    from kg.ingest import gate

    def guarded(doc_id, gap_class, detail):
        raise AssertionError(
            f"test reached the real `seldon` CLI to register a ResearchTask "
            f"(doc_id={doc_id!r}, gap_class={gap_class!r}). Monkeypatch "
            f"`kg.ingest.gate.register_gap_task` in the test that means to exercise it.")

    monkeypatch.setattr(gate, "register_gap_task", guarded)


@pytest.fixture(autouse=True)
def no_writes_to_the_real_substrate_store(monkeypatch, tmp_path_factory):
    """Same reasoning as the event-log guard, for the other durable store the gate writes.
    A conversion that SUCCEEDS in a test would otherwise drop a substrate file into
    `state/substrate_md/`, which is the corpus's real projection."""
    from kg.ingest import convert
    monkeypatch.setattr(convert, "_SUBSTRATE_DIR",
                        tmp_path_factory.mktemp("substrate"))


# No test touches the live Neo4j projection (task 2026-09-02_post_burn_reconciliation §4).
# `phase_burn` now closes a completed burn by probing Neo4j and replaying the projection; a
# test that drives the loop to completion without injecting both would open a real bolt
# connection and spawn the real scripts/build_projection.py — which happened once, on
# 2026-09-02 at 21:40Z, and collided with a rebuild in flight. Autouse and loud: the probe
# and the live document read raise, and a subprocess whose argv names the replay script is
# refused before it starts. Tests that mean to exercise the close inject their own probe and
# replay (see tests/test_projection_at_burn_close.py).
_REPLAY_SCRIPT = "build_projection.py"
_real_subprocess_run = subprocess.run


@pytest.fixture(autouse=True)
def no_live_projection(monkeypatch):
    def refuse(*a, **k):
        raise AssertionError("test reached the live Neo4j projection; inject probe/replay")

    def guarded_run(cmd, *a, **k):
        argv = cmd if isinstance(cmd, (list, tuple)) else [cmd]
        if any(_REPLAY_SCRIPT in str(part) for part in argv):
            raise AssertionError(f"test tried to spawn the real projection replay: {argv}")
        return _real_subprocess_run(cmd, *a, **k)

    monkeypatch.setattr(_proj, "neo4j_reachable", refuse)
    monkeypatch.setattr(_proj, "projected_document_ids_live", refuse)
    monkeypatch.setattr(subprocess, "run", guarded_run)


# The scan harness's evidence store is a DURABLE, COMMITTED store — `corpus/evidence/scan/`
# is tracked, unlike every other `corpus/` lane (see the note in .gitignore). Same reasoning
# as the event-log and substrate guards above: a test that stores evidence writes into the
# corpus, and content-addressing does not save it, because the control fixture server binds an
# EPHEMERAL port that is substituted into every body carrying `HOSTPORT`. So each run of
# `tests/test_scan_harness.py` produced a fresh set of blobs under a fresh digest and the
# store grew without bound; 260 of them were committed before this guard existed
# (`cc_tasks/2026-09-07_scan_hygiene.md` §2, quarantined by
# `scripts/quarantine_fixture_evidence.py`).
#
# `store_evidence` reads `EVIDENCE_ROOT` at CALL time (`root or EVIDENCE_ROOT` inside the
# body), which is the module-path-global convention this repo uses precisely so a test can
# repoint it — so redirecting the global is the whole fix. The wrapper is the belt to that
# suspenders: the collectors bound `store_evidence` by name at import (`from ..model import
# store_evidence`), so a future caller passing an explicit `root=` would bypass the redirect,
# and this refuses that loudly rather than letting it write.
#
# Autouse, so no future test can opt out by forgetting.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "assessment" / "harness"))
from scan import model as _scan_model                                    # noqa: E402
from scan import collectors as _scan_collectors                          # noqa: E402

_REAL_EVIDENCE_ROOT = _scan_model.EVIDENCE_ROOT


def _evidence_writers() -> list:
    """Every module holding its own binding of `store_evidence`. Enumerated once, here, so a
    collector added tomorrow is covered without anyone remembering this file — and enumerated
    at import rather than per test, because the fixture below runs on all ~1,500 of them."""
    import importlib
    import pkgutil
    mods = [_scan_model]
    for info in pkgutil.iter_modules(_scan_collectors.__path__):
        mod = importlib.import_module(f"{_scan_collectors.__name__}.{info.name}")
        if hasattr(mod, "store_evidence"):
            mods.append(mod)
    return mods


_EVIDENCE_WRITERS = _evidence_writers()


@pytest.fixture(autouse=True)
def no_writes_to_the_real_evidence_store(monkeypatch, tmp_path_factory):
    monkeypatch.setattr(_scan_model, "EVIDENCE_ROOT",
                        tmp_path_factory.mktemp("scan_evidence"))

    real_store = _scan_model.store_evidence

    def guarded(body, root=None):
        if (root or _scan_model.EVIDENCE_ROOT) == _REAL_EVIDENCE_ROOT:
            raise AssertionError(
                "test wrote into the REAL scan evidence store "
                f"({_REAL_EVIDENCE_ROOT}). Let the autouse redirect stand, or pass an "
                "explicit tmp_path root.")
        return real_store(body, root)

    # Every module that did `from ..model import store_evidence` holds its OWN binding, so
    # patching the model alone does not reach them.
    for mod in _EVIDENCE_WRITERS:
        monkeypatch.setattr(mod, "store_evidence", guarded)


# ------------------------------------------------------------------ xdist groups (DN-013-R4)
#
# `cc_tasks/2026-10-07_parallel_hosts_and_fast_gate.md` decision 5. The suite runs under
# pytest-xdist with `--dist loadgroup`: every test that shares a mutable resource with another
# carries `xdist_group(<resource>)`, so all of them run on ONE worker, in order, and never
# beside each other. A grouped test is never skipped and never weakened; it only loses
# parallelism with its own kind.
#
# Applied here, at collection, rather than as a `pytestmark` line in each module, so a test
# written tomorrow that opens the database is grouped without anyone remembering this file.
# Two sources:
#
# * `_AUTO_GROUPS`, a static scan of the CODE (comments and docstrings stripped) each test
#   reaches inside its own module: its body, the module helpers it calls and the module
#   fixtures it requests, transitively. A test reaching the live Neo4j database is `neo4j`:
#   the spot scan projects scratch labels into it, and a test reading the database while
#   another holds scratch nodes there would read a graph no serial run shows it. PER TEST, not
#   per module: `test_scan_run_2.py` holds the suite's longest test (1,153 s, Neo4j) and two
#   more of 324 s and 247 s that never open it, and a module-wide group serialized all three
#   (the first xdist run, 1,867 s, was that group's length).
# * `_DECLARED_GROUPS`, modules a static scan cannot see sharing, found by a run that failed
#   under `-n` and passed serially, each with the resource and the reason.
#
# A test the scan puts in one group and the table in another is a collection error: one
# test, one resource group, or the group stops meaning "these never run together".
import ast as _ast  # noqa: E402
import re as _re  # noqa: E402
import textwrap as _textwrap  # noqa: E402

_AUTO_GROUPS = {
    "neo4j": _re.compile(r"get_neo4j_driver|GraphDatabase\.driver|\.session\(database"
                         r"|publish\.project\(|run_cypher|neo4j_driver"),
}

#: module path (repo-relative) -> (group, why). Empty until a run says otherwise.
_DECLARED_GROUPS: dict = {}

_MODULE_SCANS: dict = {}


def _code(segment: str) -> str:
    """A source segment less comments and docstrings, so a test that only TALKS about the
    database (a docstring citing DD-057) is not grouped with the ones that open it. Literals
    are kept: `client_call("run_cypher", ...)` reaches the database through a string."""
    from support.sourcescan import strip_prose
    return strip_prose(_textwrap.dedent(segment), literals=False)


def _scan_module(path: Path) -> dict:
    """`{"module": set(groups), "functions": {name: set(groups)}}` for one test module.

    `functions` is closed over the module's own call and fixture graph: a function is in a
    group if its code matches, or if it names (calls, or takes as a fixture argument) a
    module-level function or method that is. Module-level code outside any function that
    matches puts the whole module in the group."""
    path = Path(path).resolve()
    if path in _MODULE_SCANS:
        return _MODULE_SCANS[path]
    src = path.read_text(encoding="utf-8")
    tree = _ast.parse(src)
    funcs: dict = {}
    for node in _ast.walk(tree):
        if isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
            seg = _ast.get_source_segment(src, node) or ""
            names = {n.id for n in _ast.walk(node) if isinstance(n, _ast.Name)}
            names |= {n.attr for n in _ast.walk(node) if isinstance(n, _ast.Attribute)}
            names |= {a.arg for a in node.args.args + node.args.kwonlyargs}
            hits = {g for g, rx in _AUTO_GROUPS.items() if rx.search(_code(seg))}
            prior = funcs.get(node.name, (set(), set()))
            funcs[node.name] = (prior[0] | hits, prior[1] | (names - {node.name}))
    groups = {name: set(h) for name, (h, _n) in funcs.items()}
    changed = True
    while changed:
        changed = False
        for name, (_h, names) in funcs.items():
            for other in names & groups.keys():
                if not groups[other] <= groups[name]:
                    groups[name] |= groups[other]
                    changed = True
    top = [n for n in tree.body
           if not isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef))]
    top_src = "\n".join(_ast.get_source_segment(src, n) or "" for n in top)
    module = {g for g, rx in _AUTO_GROUPS.items() if rx.search(_code(top_src))}
    out = {"module": module, "functions": groups}
    _MODULE_SCANS[path] = out
    return out


def xdist_group_of(item):
    """The resource group of one collected test, or None."""
    path = Path(item.path).resolve()
    root = Path(__file__).resolve().parents[1]
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    scan = _scan_module(path)
    fn = getattr(item, "originalname", None) or item.name.split("[")[0]
    reached = {fn} | set(getattr(item, "fixturenames", ()) or ())
    auto = set(scan["module"])
    for name in reached:
        auto |= scan["functions"].get(name, set())
    auto = sorted(auto)
    declared = _DECLARED_GROUPS.get(rel, (None, None))[0]
    if len(auto) > 1 or (auto and declared and declared != auto[0]):
        raise pytest.UsageError(
            f"{item.nodeid} belongs to more than one xdist group ({auto} by scan, "
            f"{declared!r} declared); one test, one resource group (tests/conftest.py)")
    return declared or (auto[0] if auto else None)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """Mark every item with its group BEFORE xdist reads the marker (xdist's own hook turns
    it into the `@group` suffix of the node id under `--dist loadgroup`)."""
    for item in items:
        if Path(item.path).suffix != ".py":
            continue
        group = xdist_group_of(item)
        if group:
            item.add_marker(pytest.mark.xdist_group(group))
