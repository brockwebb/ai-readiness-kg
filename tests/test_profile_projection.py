"""The projection profiler's accounting (task 2026-10-12_projection_replay_measured_then_batched
decision 1): per-phase query counts, wall and server time, split by query template."""
import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("profile_projection",
                                               REPO / "scripts" / "profile_projection.py")
pp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pp)


class _Res:
    def __init__(self, t_first, t_last):
        self._metadata = {"t_first": t_first, "t_last": t_last}


def test_template_collapses_whitespace_and_truncates():
    q = "MERGE (a {key: $k})\n   SET a.x = $x " + "y" * 500
    t = pp._template(q)
    assert "\n" not in t and "  " not in t and len(t) == pp.TEMPLATE_CHARS


def test_record_accumulates_per_phase_and_template(monkeypatch, tmp_path):
    monkeypatch.setattr(pp, "_stats", type(pp._stats)(pp._stats.default_factory))
    monkeypatch.setattr(pp, "_state", {"phase": "kg_replay"})
    pp._record("MERGE (n {key: $k})", 0.0, _Res(10, 5), autocommit=True)
    pp._record("MERGE (n {key: $k})", 0.0, _Res(20, 0), autocommit=False)
    st = pp._stats["kg_replay"]
    assert st["queries"] == 2 and st["autocommit_tx"] == 1
    assert abs(st["server_s"] - 0.035) < 1e-9          # (10+5+20+0) ms
    tp = st["templates"]["MERGE (n {key: $k})"]
    assert tp["n"] == 2
    out = tmp_path / "p.json"
    pp._dump(out, {"kg_replay": 1.0})
    import json
    row = json.loads(out.read_text())["kg_replay"]
    assert row["phase_wall_s"] == 1.0 and row["templates"][0]["n"] == 2
    assert row["round_trip_s"] == round(row["wall_s"] - row["server_s"], 3)
