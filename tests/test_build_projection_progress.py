"""build_projection.py progress (task cc_tasks/2026-09-21_projection_progress.md decision 4):
progress lines at the configured interval against a fake session, a log file that ends with
the per-phase timing table, and a `--dry-run` that never opens a Neo4j driver."""
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import build_projection as bp  # noqa: E402


class _FakeSession:
    """Stands in for a neo4j session: records every query, returns nothing. `build()` never
    reads back a write, so an empty result is faithful."""

    def __init__(self):
        self.calls = 0

    def run(self, query, **params):
        self.calls += 1
        return []


class _Clock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def _log_with(events_dir: Path, n_nodes: int) -> None:
    rows = [{"event_type": "manifest_add",
             "payload": {"doc_id": "d1", "title": "t", "source_type": "academic",
                         "pub_date": "2026", "primary_url": "u", "content_hash": "h"}}]
    rows += [{"event_type": "node_asserted", "doc_id": "d1",
              "provenance": {"model_id": "m", "source_sha256": "sha"},
              "payload": {"type": "Claim", "id": f"cl_{i}",
                          "item": {"grounding_span": "a span"}}} for i in range(n_nodes)]
    (events_dir / "batch-001.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


@pytest.fixture
def events(tmp_path, monkeypatch):
    from kg import eventlog
    d = tmp_path / "events"
    d.mkdir()
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", d)
    return d


def _replay_lines(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if "phase kg_replay " in ln and " start" not in ln]


def test_progress_lines_appear_every_n_items(events, tmp_path):
    _log_with(events, n_nodes=9)            # 10 events: 1 manifest_add + 9 node_asserted
    out = io.StringIO()
    prog = bp.Progress(tmp_path / "p.log", every=4, clock=_Clock(), out=out)
    counts = bp.build(_FakeSession(), ["Document", "Claim"], set(), progress=prog)
    prog.finish(counts)
    lines = _replay_lines(out.getvalue())
    # items 4 and 8 of 10, and nothing else: the clock never moved, so only the item half fires
    assert [ln.split("phase kg_replay ")[1].split()[0] for ln in lines] == ["4/10", "8/10"]
    assert "nodes=" in lines[-1] and "edges=" in lines[-1]
    assert counts["nodes"] == 9


def test_progress_lines_appear_on_the_time_interval(events, tmp_path):
    _log_with(events, n_nodes=5)
    clock = _Clock()

    class _SlowSession(_FakeSession):
        def run(self, query, **params):
            clock.t += 30.0                  # every write "takes" 30 s
            return super().run(query, **params)

    out = io.StringIO()
    prog = bp.Progress(None, every=10_000, interval_s=60, clock=clock, out=out)
    bp.build(_SlowSession(), ["Document", "Claim"], set(), progress=prog)
    # the item half never fires (10,000 > 6 events); the 60 s half does, inside the replay
    assert _replay_lines(out.getvalue()), out.getvalue()


def test_every_phase_boundary_is_logged(events, tmp_path):
    _log_with(events, n_nodes=2)
    out = io.StringIO()
    prog = bp.Progress(None, every=1000, clock=_Clock(), out=out)
    bp.build(_FakeSession(), ["Document", "Claim"], set(), progress=prog)
    started = [ln.split("phase ")[1].split()[0] for ln in out.getvalue().splitlines()
               if ln.endswith(" start") or " start " in ln]
    assert started == ["prepass", "reset", "document_skeletons", "vocabulary", "kg_replay",
                       "overlays", "restorations", "resolutions", "thin_spans"]


def test_log_file_exists_and_ends_with_the_timing_table(events, tmp_path):
    _log_with(events, n_nodes=3)
    log = tmp_path / "logs" / "projection_x.log"
    prog = bp.Progress(log, every=1, clock=_Clock(), out=None)
    counts = bp.build(_FakeSession(), ["Document", "Claim"], set(), progress=prog)
    prog.phase("fingerprint", counts=counts)
    prog.finish(counts)
    text = log.read_text(encoding="utf-8").splitlines()
    assert text[-1].startswith("TOTAL")
    table = text[text.index("phase timing"):]
    for phase in ("prepass", "reset", "kg_replay", "overlays", "fingerprint"):
        assert any(row.startswith(phase + " ") for row in table), phase


def test_build_without_progress_is_silent(events, capsys):
    """Existing callers pass no `progress`; they must see nothing new on stdout."""
    _log_with(events, n_nodes=2)
    bp.build(_FakeSession(), ["Document", "Claim"], set())
    assert "[projection" not in capsys.readouterr().out


def test_dry_run_touches_no_graph(events, monkeypatch, capsys):
    import neo4j

    def refuse(*a, **k):
        raise AssertionError("--dry-run opened a Neo4j driver")

    monkeypatch.setattr(neo4j.GraphDatabase, "driver", refuse)
    monkeypatch.setattr(bp, "_neo4j_creds", refuse)
    _log_with(events, n_nodes=2)
    assert bp.main(["--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "kg_replay" in out and "total=3" in out and "framework_layer" in out


def test_progress_every_is_required_config(tmp_path, monkeypatch):
    cfg = tmp_path / "controls.yaml"
    cfg.write_text("projection:\n  replay_script: x\n  stale_marker: y\n  python: null\n",
                   encoding="utf-8")
    monkeypatch.setattr(bp, "CONTROLS_PATH", cfg)
    with pytest.raises(SystemExit, match="progress_every"):
        bp.progress_every()
    cfg.write_text("projection:\n  progress_every: 250\n", encoding="utf-8")
    assert bp.progress_every() == 250
