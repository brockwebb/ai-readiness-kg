"""The adopter's path: scan your own site, on demand or on a schedule, and read the result.

`cc_tasks/2026-09-19_adopter_path.md`. Decisions 1 to 4 are tested in-process over the loopback
fixtures with a virtual clock; decision 5, the runbook, is run as written — every `bash` block
of `docs/adopt/run_on_your_site.md`, in order, in a copy of the working tree, at the standing
rate limit — and logged to `logs/adopt_runbook.log`, which is where its RESULT quotes it from.

Nothing here writes to `state/`, `corpus/`, `events/` or `docs/reports/`: every run goes to a
throwaway `out/`, and `scripts/check_protected_adopt.sh` asserts the tree afterwards.
"""
from __future__ import annotations

import ast
import datetime as dt
import importlib.metadata
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "mcp"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import adopt, load_params, run                               # noqa: E402
from scan.model import CYCLE_TOKEN_ENV, params_hash                    # noqa: E402

TODAY = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
RUNBOOK = REPO / "docs" / "adopt" / "run_on_your_site.md"
LOG = REPO / "logs" / "adopt_runbook.log"
PROJECT_UA = yaml.safe_load(adopt.PROJECT_FRAME.read_text(encoding="utf-8"))["user_agent"]
ADOPTER_UA = "example-readiness-scan/1.0 (+mailto:webmaster@example.org)"
#: The snapshot whose params_hash the committed params.yaml reproduces today (measured before
#: this task: `0ef2e016fea2…`). Adding `schedule:` must not move it.
SNAPSHOT_PAYLOAD = REPO / "state" / "scan_2026-09-10_rj4.json"


def _frame_file(tmp: Path, text: str, name: str = "my_site.yaml") -> Path:
    p = tmp / name
    p.write_text(text, encoding="utf-8")
    return p


def _loopback_frame(base: str, slug: str = "my-site", body: str = "MYSITE") -> str:
    return (f"frame: {slug}\nbodies:\n  - name: {body}\n    home: {base}/index.html\n"
            f"    flagships:\n      - {base}/index.html\n      - {base}/second.html\n")


# ============================================================ decision 1: the frame file

def test_the_project_frame_is_the_target_datafile_and_the_parameters_it_is_measured_under():
    """`frames/fss16.yaml` names exactly the bodies the registered DataFile holds, by tier, and
    exactly the target name and identity `params.yaml` measures them under."""
    params = load_params()
    frame = adopt.load_frame(adopt.PROJECT_FRAME)
    assert frame["kind"] == adopt.DATAFILE
    adopt.check_project_frame(frame, params)
    assert frame["user_agent"] == params["manners"]["user_agent"]
    rows = json.loads((REPO / "state" / f"{frame['targets']}.json").read_text())["rows"]
    by_tier = {t: sorted({r["agency"] for r in rows if r.get("tier", "A") == t})
               for t in ("A", "C")}
    assert sorted(frame["bodies"]["tier_a"]) == by_tier["A"] and len(by_tier["A"]) == 16
    assert sorted(frame["bodies"]["tier_c"]) == by_tier["C"]


def test_the_schedule_key_moves_no_hash_and_the_identity_does():
    """Decision 2's key is outside `params_hash` (`model.UNHASHED_KEYS`), so the committed
    parameters still hash to the snapshot's and every stored payload keeps its identity;
    the User-Agent is a measurement condition (DD-060) and moves it."""
    params = load_params()
    assert params["schedule"] == {"when": "on_demand",
                                  "frame": "assessment/harness/scan/frames/fss16.yaml"}
    snap = json.loads(SNAPSHOT_PAYLOAD.read_text(encoding="utf-8"))
    assert params_hash(params) == snap["params_hash"]
    without = {k: v for k, v in params.items() if k != "schedule"}
    assert params_hash(without) == params_hash(params)
    assert params_hash({**params, "schedule": {"when": "0 6 * * 1"}}) == params_hash(params)
    other = json.loads(json.dumps(params))
    other["manners"]["user_agent"] = ADOPTER_UA
    assert params_hash(other) != params_hash(params)


def test_run_without_a_frame_reads_the_same_targets_as_before():
    """The frame did not move: `run.targets(params)` still reads the DataFile `params` names,
    and `--frame` refuses this project's frame rather than half-running it."""
    from scan.model import SYNTHETIC_PREFIXES
    params = load_params()
    rows = json.loads((REPO / "state" / f"{params['cycle']['targets']}.json").read_text())["rows"]
    admitted = json.loads((REPO / "corpus" / "manifest.json").read_text())["entries"]
    want = [r["doc_id"] for r in rows if str(r.get("doc_id") or "").startswith(
        SYNTHETIC_PREFIXES) or r.get("doc_id") in admitted]
    assert [t["doc_id"] for t in run.targets(params)] == want
    with pytest.raises(SystemExit, match="is this project's frame"):
        run.main(["--frame", str(adopt.PROJECT_FRAME)])


@pytest.mark.parametrize("text, match", [
    ("frame: My Site\nbodies:\n  - {name: A, home: 'https://a.example/'}\n", "must be lower"),
    ("frame: s\nbodies: []\n", "names no bodies"),
    ("frame: s\nbodies:\n  - {name: A, home: 'a.example'}\n", "not an absolute"),
    ("frame: s\nbodies:\n  - {name: A, home: 'https://a.example/', colour: red}\n",
     "does not read"),
    ("frame: s\nschedule: daily\nbodies:\n  - {name: A, home: 'https://a.example/'}\n",
     "does not read"),
    ("frame: s\nbodies:\n  - {name: A, home: 'https://a.example/'}\n"
     "  - {name: B, home: 'https://a.example/x'}\n", "one body per host"),
    ("frame: s\nbodies:\n  - {name: A, home: 'https://a.example/'}\n"
     "  - {name: a, home: 'https://b.example/'}\n", "repeats the body name"),
    ("frame: s\nbodies:\n  - {name: A, home: 'https://a.example/', tier: B}\n", "tier"),
])
def test_a_frame_that_cannot_run_is_refused_naming_the_defect(tmp_path, text, match):
    with pytest.raises(SystemExit, match=match):
        adopt.load_frame(_frame_file(tmp_path, text))


def test_a_declared_frame_compiles_to_synthetic_rows_with_the_frames_legs(tmp_path,
                                                                          monkeypatch):
    """One body becomes a well-known row, a home row and a row per flagship, all synthetic, and
    `run.targets` gives them exactly the legs this project's rows of the same kind get."""
    f = adopt.load_frame(_frame_file(tmp_path, (
        "frame: s\nbodies:\n  - name: A\n    home: https://a.example/\n    flagships:\n"
        "      - https://a.example/data/p?x=1\n  - name: R\n    home: https://r.example/\n"
        "    tier: C\n")))
    compiled = adopt.compile_rows(f)
    kinds = [(r["agency"], r["surface_kind"], r["doc_id"]) for r in compiled["rows"]]
    assert kinds == [("A", "well_known", "host:a.example"), ("A", "home", "home:a.example"),
                     ("A", "flagship", "flagship:a.example/data/p?x=1"),
                     ("R", "well_known", "host:r.example"), ("R", "home", "home:r.example")]
    project = {t["surface_kind"] + t["tier"]: t["legs"] for t in run.targets(load_params())}
    params = adopt.overlay(load_params(), "scan_s_2026-09-19", adopt.targets_name(f))
    monkeypatch.setattr(run, "STATE_DIR", tmp_path)
    adopt.write_json(tmp_path / f"{adopt.targets_name(f)}.json", compiled)
    legs = {t["doc_id"]: t["legs"] for t in run.targets(params)}
    assert legs["host:a.example"] == ["A12"]
    assert legs["home:a.example"] == project["homeA"]
    assert legs["flagship:a.example/data/p?x=1"] == project["flagshipA"]
    assert legs["home:r.example"] == project["homeC"]
    # The overlay changes the cycle identity and nothing else, and names the frame's bytes.
    assert params["cycle"]["targets"] == f"frame_s_{f['_sha256'][:12]}"


# ============================================================ decision 3: the identity

@pytest.mark.parametrize("ua, host, refused", [
    (PROJECT_UA, "www.example.org", "this project's identity"),
    ("ai-readiness-kg-scanner/0.3 (+https://elsewhere.example)", "www.example.org",
     "this project's identity"),
    ("my-scan/1.0", "www.example.org", "carries no contact"),
    (PROJECT_UA, "127.0.0.1:8080", None),
    (PROJECT_UA, "localhost:9", None),
    (ADOPTER_UA, "www.example.org", None),
    ("my-scan/1.0 (+https://example.org/bot)", "www.example.org", None),
])
def test_the_identity_is_the_adopters_own_off_loopback(ua, host, refused):
    params = json.loads(json.dumps(load_params()))
    params["manners"]["user_agent"] = ua
    rows = [{"host": host}]
    if refused:
        with pytest.raises(SystemExit, match=refused):
            adopt.check_identity(params, rows)
    else:
        adopt.check_identity(params, rows)


def test_the_identity_refusal_comes_before_any_fetch(tmp_path, monkeypatch):
    """`run.py --frame` refuses a non-loopback frame under the project's identity before the
    control gate, so nothing — not even a fixture — is fetched."""
    def forbidden(*a, **k):
        raise AssertionError("the control gate ran before the identity was checked")
    monkeypatch.setattr(run, "run_controls", forbidden)
    monkeypatch.setenv(CYCLE_TOKEN_ENV, "0")
    frame = _frame_file(tmp_path, "frame: ex\nbodies:\n  - {name: EX, home: "
                                  "'https://www.example.org/'}\n")
    with pytest.raises(SystemExit, match="this project's identity"):
        run.main(["--frame", str(frame), "--out", str(tmp_path / "out")])
    assert not (tmp_path / "out" / "ex" / "state").exists() or not any(
        (tmp_path / "out" / "ex" / "state").glob("scan_*.json"))


# ============================================================ decision 2: the schedule

def test_on_demand_installs_nothing(tmp_path):
    """This project's `params.yaml` says `on_demand`, and `make install-schedule` writes no
    crontab and no agent."""
    import install_schedule as S
    cron, agents = tmp_path / "crontab", tmp_path / "agents"
    for kind in ("cron", "launchd"):
        assert S.main(["--kind", kind, "--crontab-file", str(cron),
                       "--launchagents-dir", str(agents)]) == 0
    assert not cron.exists() and not agents.exists()
    out = subprocess.run(["make", "-s", "-C", str(REPO), "-n", "install-schedule"],
                         capture_output=True, text=True, check=True).stdout
    assert "scripts/install_schedule.py" in out


@pytest.mark.parametrize("expr, want", [
    ("0 6 * * 1", [{"Minute": 0, "Hour": 6, "Weekday": 1}]),
    ("30 2 1 * *", [{"Minute": 30, "Hour": 2, "Day": 1}]),
    ("0 */12 * * *", [{"Minute": 0, "Hour": 0}, {"Minute": 0, "Hour": 12}]),
    ("15 3 1 * 0", [{"Minute": 15, "Hour": 3, "Day": 1}, {"Minute": 15, "Hour": 3,
                                                           "Weekday": 0}]),
    ("* * * * *", [{}]),
])
def test_a_cron_expression_becomes_launchd_intervals(expr, want):
    import install_schedule as S
    assert S.calendar_intervals(S.parse_cron(expr)) == want


@pytest.mark.parametrize("expr", ["daily", "@daily", "0 6 * * mon", "61 * * * *",
                                  "0 6 * *", "5-2 * * * *"])
def test_a_schedule_that_is_not_cron_is_refused(expr):
    import install_schedule as S
    with pytest.raises(SystemExit, match="REFUSING"):
        S.parse_cron(expr)


def test_a_schedule_is_written_once_per_frame_and_printed(tmp_path):
    import install_schedule as S
    frame = _frame_file(tmp_path, _loopback_frame("http://127.0.0.1:9"))
    argv, log, slug = S.job(frame, "/usr/bin/python3")
    assert argv[-2:] == [f"FRAME={frame}", "PY=/usr/bin/python3"] and slug == "my-site"
    cron = tmp_path / "crontab"
    cron.write_text("0 1 * * * something else\n", encoding="utf-8")
    first = S.install_cron("0 6 * * 1", argv, log, slug, cron)
    S.install_cron("0 7 * * 1", argv, log, slug, cron)
    lines = cron.read_text().splitlines()
    assert lines[0] == "0 1 * * * something else" and len(lines) == 2
    assert lines[1].startswith("0 7 * * 1 make -C ") and lines[1].endswith("# airkg-scan:my-site")
    assert "0 6 * * 1 make -C" in first
    said = S.install_launchd("0 6 * * 1", argv, log, slug, tmp_path / "agents")
    plist = plistlib.loads((tmp_path / "agents" / "org.airkg.scan.my-site.plist").read_bytes())
    assert plist["ProgramArguments"] == argv
    assert plist["StartCalendarInterval"] == [{"Minute": 0, "Hour": 6, "Weekday": 1}]
    assert "launchctl bootstrap" in said
    with pytest.raises(SystemExit, match="this project's frame"):
        S.job(adopt.PROJECT_FRAME, "/usr/bin/python3")


# ============================================================ decision 4: a run, in-process

@pytest.fixture(scope="module")
def loopback(tmp_path_factory):
    """`run.py --frame` then `render_run_report.py`, over the `body_two_products` fixture as
    "your site", with a virtual clock. Then a second body's spot within a two-body frame."""
    from scan import manners
    from scan.clock import VirtualClock
    from scan.fixtures.server import FixtureServer
    import render_run_report as R

    class VFetcher(manners.Fetcher):
        def __init__(self, params, clock=None, **kw):
            super().__init__(params, clock=VirtualClock(), **kw)

    root = tmp_path_factory.mktemp("adopt_loopback")
    out_dir = root / "out"
    res: dict = {"root": root, "out": out_dir}
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(manners, "Fetcher", VFetcher)
        mp.setenv(CYCLE_TOKEN_ENV, "0")
        with FixtureServer("body_two_products") as base, FixtureServer("passes_all") as other:
            frame = _frame_file(root, _loopback_frame(base))
            res["base"], res["frame"] = base, frame
            res["rc"] = run.main(["--frame", str(frame), "--out", str(out_dir)])
            res["render_rc"] = R.main(["--frame", str(frame), "--out", str(out_dir)])
            with pytest.raises(SystemExit, match="takes DD-041's rerun letter") as e:
                run.main(["--frame", str(frame), "--out", str(out_dir)])
            res["second_run_refusal"] = str(e.value)
            # A two-body frame, its frame run, then a spot of one body within it.
            two = _frame_file(root, _loopback_frame(base, "two", "ONE") + (
                f"  - name: TWO\n    home: {other}/index.html\n"), "two.yaml")
            res["two_rc"] = run.main(["--frame", str(two), "--out", str(out_dir)])
            R.main(["--frame", str(two), "--out", str(out_dir)])
            res["spot_rc"] = run.main(["--frame", str(two), "--out", str(out_dir),
                                       "--target", "two"])
            res["spot_render_rc"] = R.main(["--frame", str(two), "--out", str(out_dir)])
            res["other_netloc"] = other.split("//", 1)[1]
    where = adopt.layout(out_dir, "my-site")
    res["where"] = where
    res["cycle"] = where["latest"].read_text().strip()
    res["payload"] = json.loads((where["state"] / f"{res['cycle']}.json").read_text())
    res["report"] = (where["report"] / f"{res['cycle']}.md").read_text()
    return res


def test_a_run_writes_its_artifacts_under_out_and_nowhere_else(loopback):
    assert loopback["rc"] == 0 and loopback["render_rc"] == 0
    cycle, where = loopback["cycle"], loopback["where"]
    assert cycle == f"scan_my-site_{TODAY}"
    p = loopback["payload"]
    assert p["scope"] == "frame" and p["control_verdict"] == "pass"
    assert p["surfaces"] == 4 and p["verdict_counts"]["error"] == 0
    assert set(p["requests_per_host"]) == {loopback["base"].split("//", 1)[1]}
    assert p["frame"]["name"] == "my-site" and p["params_overlay"]["cycle"]["name"] == cycle
    assert p["base_params_hash"] == params_hash(load_params())
    assert p["targets"] == adopt.targets_name(adopt.load_frame(loopback["frame"]))
    for kind in ("tierA", "tierC", "product"):
        for ext in ("json", "csv"):
            assert (where["reports"] / f"scan_matrix_{kind}_my-site_{TODAY}.{ext}").is_file()
    assert yaml.safe_load(where["publication"].read_text())["snapshot_cycle"] == cycle
    # Every body the run retained is in the run's own evidence directory, by its sha256.
    cited = {o["response"]["body_path"] for o in p["observations_detail"]
             if (o.get("response") or {}).get("body_path")}
    assert cited and all(str(where["evidence"] / cycle) in str(Path(c).resolve())
                         or c.startswith(str(where["evidence"])) for c in cited)
    assert not list((REPO / "state").glob("scan_my-site_*"))
    assert not list((REPO / "state").glob("frame_*"))
    assert "second run of this frame today" in loopback["second_run_refusal"]


def test_the_run_re_derives_under_its_own_overlay(loopback):
    from scan import rederive
    p = loopback["payload"]
    out = rederive.rederive(p, adopt.params_of_run(p, load_params()))
    assert out["identical"], json.dumps(out)[:1500]
    changed = json.loads(json.dumps(load_params()))
    changed["manners"]["user_agent"] = ADOPTER_UA
    with pytest.raises(SystemExit, match="params.yaml changed after the scan"):
        adopt.params_of_run(p, changed)


def test_the_report_is_the_mcp_verbs_answer(loopback):
    """Every section of the report is a verb's answer over the run, with no graph: the body's
    legs with their reasons, the prescriptions for it, the requirements, and the rank sentence."""
    import airkg_tools as T
    rpt, cycle = loopback["report"], loopback["cycle"]
    t = T.Tools(graph=None, run=loopback["where"]["root"])
    assert t.cycle == cycle
    b = t.get_body("MYSITE")
    assert b["summary"] in rpt
    assert all(c["reason"] for c in b["legs"]), "a leg with no reason from the payload"
    for c in b["legs"]:
        assert f"| {c['leg']} | {c['verdict']} | `{c['surface']}` |" in rpt
    assert "### What to fix first" in rpt and "### What the harness could not see" in rpt
    assert t.get_requirements(body="MYSITE")["summary"] + "." in rpt
    assert "MYSITE ranks 1 of 1" in rpt
    ev = t.get_evidence(b["legs"][0]["finding_id"])
    assert ev["observations"] and any(o["sha256_verified"] for o in ev["observations"])
    # The project's own no-graph server is unchanged: it still says the graph is unreachable.
    assert "error" in T.Tools(graph=None).get_evidence(b["legs"][0]["finding_id"])


def test_score_reads_the_run(loopback, capsys):
    import prescriptions as P
    import score
    before = (P.REPORTS, P.PUBLICATION)
    try:
        assert score.main(["--run", str(loopback["where"]["root"]), "--body", "MYSITE"]) == 0
    finally:
        P.REPORTS, P.PUBLICATION = before
    out = capsys.readouterr().out
    assert f"MYSITE: score 1.000 hierarchical" in out


def test_a_spot_within_a_frame_is_read_beside_the_frame_run(loopback):
    assert loopback["two_rc"] == 0 and loopback["spot_rc"] == 0
    assert loopback["spot_render_rc"] == 0
    where = adopt.layout(loopback["out"], "two")
    spot_cycle = where["latest"].read_text().strip()
    assert spot_cycle == f"spot_two_{TODAY}"
    sp = json.loads((where["state"] / f"{spot_cycle}.json").read_text())
    assert sp["scope"] == "spot" and sp["spot_targets"] == ["TWO"]
    assert set(sp["requests_per_host"]) == {loopback["other_netloc"]}
    # The frame's cycle of record is still the frame run, and the spot is TWO's latest.
    assert yaml.safe_load(where["publication"].read_text())["snapshot_cycle"] == \
        f"scan_two_{TODAY}"
    rpt = (where["report"] / f"{spot_cycle}.md").read_text()
    assert "TWO measured again by spot cycle" in rpt and "## ONE" not in rpt


#: A run and its render, alone in a fresh interpreter, printing every repository module it
#: loaded. Measured in its own process because the test process has loaded half the repository.
_LOADED = r"""
import json, sys
from pathlib import Path
repo, out = Path(sys.argv[1]), sys.argv[2]
for d in ("", "scripts", "mcp", "assessment/harness"):
    sys.path.insert(0, str(repo / d))
from scan import manners, run
from scan.clock import VirtualClock
from scan.fixtures.server import FixtureServer
class F(manners.Fetcher):
    def __init__(self, params, clock=None, **kw):
        super().__init__(params, clock=VirtualClock(), **kw)
manners.Fetcher = F
import render_run_report as R
with FixtureServer("body_two_products") as base:
    frame = Path(out) / "f.yaml"
    frame.write_text(f"frame: f\nbodies:\n  - name: F\n    home: {base}/index.html\n"
                     f"    flagships:\n      - {base}/second.html\n")
    assert run.main(["--frame", str(frame), "--out", out]) == 0
assert R.main(["--frame", str(frame), "--out", out]) == 0
print(json.dumps(sorted({str(Path(m.__file__).resolve()) for m in list(sys.modules.values())
                         if getattr(m, "__file__", None)
                         and str(Path(m.__file__).resolve()).startswith(str(repo))})))
"""


def test_the_runbooks_requirements_are_the_imports_the_run_loaded(tmp_path):
    """The requirement list is measured: the third-party modules imported by every repository
    module a run and its render load, less the optional graph driver."""
    env = {k: v for k, v in os.environ.items() if k != CYCLE_TOKEN_ENV}
    done = subprocess.run([sys.executable, "-c", _LOADED, str(REPO), str(tmp_path)], env=env,
                          capture_output=True, text=True, timeout=600)
    assert done.returncode == 0, done.stderr[-3000:]
    loaded = json.loads(done.stdout.strip().splitlines()[-1])
    names = set()
    for f in loaded:
        for n in ast.walk(ast.parse(Path(f).read_text(encoding="utf-8"))):
            if isinstance(n, ast.Import):
                names |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
                names.add(n.module.split(".")[0])
    local = {Path(f).stem for f in loaded} | {"scan", "harness", "kg", "mcp"}
    third = {n for n in names - set(sys.stdlib_module_names) - local
             if not any((REPO / d / f"{n}.py").exists() for d in ("scripts", "mcp"))
             and not (REPO / n).exists()}
    assert "neo4j" in third and "seldon" not in third
    required = third - {"neo4j"}
    dists = importlib.metadata.packages_distributions()
    text = RUNBOOK.read_text(encoding="utf-8")
    listed = re.search(r"Versions are the ones the gate ran under:\n\s+(.*)\n", text).group(1)
    listed = dict(re.findall(r"`([^`]+)` (\d+(?:\.\d+)*)", listed))
    assert set(listed) == {dists[n][0] for n in required}
    for dist, version in listed.items():
        assert importlib.metadata.version(dist) == version
    check = re.search(r"-c 'import ([^;]+);", text).group(1)
    assert {x.strip() for x in check.split(",")} == required


def test_publishing_a_run_keeps_its_evidence_where_the_run_left_it(loopback, tmp_path,
                                                                   monkeypatch):
    """`make project RUN=…`'s first step, into a throwaway log: `--no-promote` leaves every
    `body_path` pointing into `out/`, and the events carry the overlay that re-derives them."""
    from kg import eventlog
    from scan import publish
    monkeypatch.setattr(eventlog, "_EVENTS_DIR", tmp_path / "events")
    where, cycle = loopback["where"], loopback["cycle"]
    src = where["state"] / f"{cycle}.json"
    payload = json.loads(src.read_text())
    before = [o["response"]["body_path"] for o in payload["observations_detail"]]
    out = publish.write_events(payload, src)
    assert out["finding_events_written"] == len(payload["findings_detail"]) + len(
        payload["control_findings_detail"])
    log = list(eventlog.replay())
    assert {e.get("params_overlay", {}).get("cycle", {}).get("name") for e in log
            if e["event_type"] == "finding_derived"} == {cycle}
    assert [o["response"]["body_path"] for o in payload["observations_detail"]] == before


# ============================================================ decision 5: the runbook, as written

def _blocks(text: str) -> list:
    """`(info, body)` of every fenced block, in order."""
    return [(m.group(1).strip(), m.group(2))
            for m in re.finditer(r"^```([^\n]*)\n(.*?)^```\s*$", text, re.S | re.M)]


def test_the_runbook_marks_exactly_what_the_gate_does_not_run():
    blocks = _blocks(RUNBOOK.read_text(encoding="utf-8"))
    skipped = [b for i, b in blocks if i == "bash not-run-by-gate"]
    assert len(skipped) == 2
    assert "git clone" in skipped[0] and "pip install" in skipped[0]
    assert "make project" in skipped[1]
    assert {i for i, _ in blocks} <= {"bash", "bash not-run-by-gate", "yaml", "json"}


def _copy_tree(dst: Path) -> None:
    """What a clone of the pushed commit holds: every tracked file and every untracked file
    that is not ignored (this task's new ones), and nothing the repository ignores."""
    names = subprocess.run(["git", "ls-files", "-co", "--exclude-standard", "-z"], cwd=REPO,
                           capture_output=True, check=True).stdout.decode().split("\0")
    for n in filter(None, names):
        s = REPO / n
        if s.is_file():
            (dst / n).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, dst / n)


def _tree_state(root: Path) -> dict:
    return {str(p.relative_to(root)): p.stat().st_size
            for d in ("state", "corpus", "events", "docs/reports") for p in (root / d).rglob("*")
            if p.is_file()}


@pytest.mark.slow
def test_the_runbook_runs_as_written(tmp_path):
    """Decision 5. Every `bash` block of the runbook, verbatim and in order, in one shell, in a
    copy of the working tree, against the `body_two_products` fixture as "your site", at the
    standing 1 request/s. The log is the RESULT's §0."""
    from scan.fixtures.server import FixtureServer
    blocks = [b for i, b in _blocks(RUNBOOK.read_text(encoding="utf-8")) if i == "bash"]
    clone = tmp_path / "ai-readiness-kg"
    _copy_tree(clone)
    before = _tree_state(clone)
    script = ["set -euo pipefail"]
    for n, b in enumerate(blocks, 1):
        shown = "\n".join(f"$ {ln}" for ln in b.rstrip("\n").split("\n"))
        script += [f"echo '=== runbook block {n} ==='", f"cat <<'__AIRKG_SHOWN__'\n{shown}\n"
                   f"__AIRKG_SHOWN__", b.rstrip("\n")]
    env = {k: v for k, v in os.environ.items() if k not in ("PY", CYCLE_TOKEN_ENV)}
    env["PATH"] = f"/opt/anaconda3/bin:{env.get('PATH', '')}"
    started = dt.datetime.now(dt.timezone.utc)
    with FixtureServer("body_two_products") as base:
        env["SITE_PORT"] = base.rsplit(":", 1)[1]
        done = subprocess.run(["bash", "-c", "\n".join(script)], cwd=clone, env=env,
                              capture_output=True, text=True, timeout=3000)
    finished = dt.datetime.now(dt.timezone.utc)
    LOG.parent.mkdir(exist_ok=True)
    LOG.write_text(
        f"# {RUNBOOK.relative_to(REPO)} run as written by "
        f"tests/test_adopter_path.py::test_the_runbook_runs_as_written\n"
        f"# started {started.isoformat()} finished {finished.isoformat()} "
        f"({(finished - started).total_seconds():.1f} s); copy of the tree at {clone}; "
        f"SITE_PORT={env['SITE_PORT']}\n# exit {done.returncode}\n"
        f"# ---- stdout\n{done.stdout}\n# ---- stderr\n{done.stderr}\n", encoding="utf-8")
    assert done.returncode == 0, done.stdout[-3000:] + done.stderr[-3000:]
    o = done.stdout
    assert "requirements OK" in o
    assert "REFUSING: params.yaml manners.user_agent is this project's identity" in done.stderr
    assert "refused, as it should be" in o
    assert f'user_agent: "{ADOPTER_UA}"' in o
    assert "CONTROL GATE: PASS" in o
    assert "schedule.when is on_demand: nothing installed." in o
    assert "RE-DERIVATION GATE: PASS" in o
    cycle = f"scan_my-site_{TODAY}"
    report = (clone / "out" / "my-site" / "report" / f"{cycle}.md").read_text()
    assert report in o, "the runbook's `cat` of the report is the report"
    assert "## MYSITE" in report and f"robots.txt permits {ADOPTER_UA}" in report
    payload = json.loads((clone / "out" / "my-site" / "state" / f"{cycle}.json").read_text())
    assert set(payload["requests_per_host"]) == {f"127.0.0.1:{env['SITE_PORT']}"}
    assert payload["control_verdict"] == "pass"
    assert f"judged on {cycle}" in o and "MYSITE: score" in o
    # The run wrote nothing into the copy's own record.
    assert _tree_state(clone) == before
