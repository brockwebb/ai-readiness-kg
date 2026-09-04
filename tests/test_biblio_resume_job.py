"""Scheduled biblio-resume job (task 2026-08-29_biblio_cron).

The task's §5 guardrail is the reason this file exists: a scheduled entrypoint must be unable
to spend against the model budget, and "unable" is a claim that needs a seeded known-bad to
fire it (methodology §7.5 — no monitor is trusted until one does). So every guard here has a
positive control: the spend-ledger detector is shown catching a leg that really does append
to the ledger, the module detector is shown catching a closure that really does contain
`model_stub`, and the retention sweep is shown deleting a genuinely old file while sparing a
file it does not own.

The two guards cover different holes and neither subsumes the other:
  * import closure — PREVENTIVE, makes a reservation unreachable;
  * ledger fingerprint — DETECTIVE, catches spend arriving by a route the import check
    cannot see (a subprocess, a lazy import).
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "jobs"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "launchd"))
import biblio_resume_job as job  # noqa: E402
import install as installer  # noqa: E402

#: Fixture config mirrors the shipped bounds. An artificially small line cap here truncated
#: the very FATAL message the guard tests assert on — the fixture was hiding the evidence.
#: Truncation is exercised directly against `Log` instead, where the bound is the subject.
CONTROLS = {"jobs": {"biblio_resume": {"hour": 2, "minute": 30, "log_max_line_chars": 2000,
                                       "log_max_run_bytes": 2097152,
                                       "log_retention_days": 30}}}

#: Captured before any fixture patches it, so the completion tests can put the real one back.
_REAL_COVERAGE_NOTE = job.coverage_note


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Hermetic repo: controls, ledger, and log dir all on tmp_path."""
    (tmp_path / "controls.yaml").write_text(yaml.safe_dump(CONTROLS), encoding="utf-8")
    ledger = tmp_path / "state" / "spend_ledger.jsonl"
    ledger.parent.mkdir(parents=True)
    ledger.write_text('{"record":"reserve"}\n', encoding="utf-8")
    logs = tmp_path / "state" / "logs" / "biblio_resume"
    monkeypatch.setattr(job, "REPO", tmp_path)
    monkeypatch.setattr(job, "CONTROLS", tmp_path / "controls.yaml")
    monkeypatch.setattr(job, "LEDGER", ledger)
    monkeypatch.setattr(job, "LOG_DIR", logs)
    monkeypatch.setattr(job, "coverage_note", lambda log: None)
    return tmp_path


def _log(tmp_path) -> str:
    d = tmp_path / "state" / "logs" / "biblio_resume"
    return "".join(f.read_text(encoding="utf-8") for f in sorted(d.glob("*.log")))


# --------------------------------------------------------------------- config is not optional

def test_missing_jobs_block_is_fatal(tmp_path, monkeypatch):
    (tmp_path / "controls.yaml").write_text("forage: off\n", encoding="utf-8")
    monkeypatch.setattr(job, "CONTROLS", tmp_path / "controls.yaml")
    with pytest.raises(SystemExit, match="no jobs.biblio_resume block"):
        job.controls()


def test_missing_key_is_fatal_not_defaulted(tmp_path, monkeypatch):
    """A silent default is a retention window the operator never chose (~/GitHub §4)."""
    cfg = {"jobs": {"biblio_resume": {"hour": 2, "minute": 30, "log_max_line_chars": 10,
                                      "log_max_run_bytes": 10}}}
    (tmp_path / "controls.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setattr(job, "CONTROLS", tmp_path / "controls.yaml")
    with pytest.raises(SystemExit, match="log_retention_days"):
        job.controls()


def test_shipped_controls_yaml_carries_the_block():
    """The real file, not a fixture — the job is scheduled against this one."""
    cfg = yaml.safe_load((Path(job.__file__).resolve().parent.parent.parent
                          / "controls.yaml").read_text(encoding="utf-8"))
    blk = cfg["jobs"]["biblio_resume"]
    assert blk["log_retention_days"] == 30 and blk["log_max_line_chars"] == 2000


# ------------------------------------------------------------------------- log-bomb guard

def test_long_line_truncated_short_line_untouched(tmp_path):
    log = job.Log(tmp_path / "x.log", max_line=20, max_run=10_000)
    log.line("short")
    log.line("y" * 500)
    log.close()
    lines = (tmp_path / "x.log").read_text(encoding="utf-8").splitlines()
    assert lines[0] == "short"
    assert lines[1].startswith("y" * 20) and "480 chars truncated" in lines[1]
    assert len(lines[1]) < 100


def test_run_byte_cap_stops_a_flood(tmp_path):
    """Positive control: the line cap does not bound a flood of ordinary lines."""
    log = job.Log(tmp_path / "x.log", max_line=100, max_run=200)
    for i in range(5000):
        log.line(f"ordinary line {i}")
    log.close()
    text = (tmp_path / "x.log").read_text(encoding="utf-8")
    assert len(text) < 1000, "run cap did not bound the flood"
    assert "run log cap 200 bytes reached" in text
    assert text.count("run log cap") == 1, "cap notice repeated per line"


# ---------------------------------------------------------------------------- retention

def test_retention_deletes_old_keeps_recent(env, tmp_path):
    d = tmp_path / "state" / "logs" / "biblio_resume"
    d.mkdir(parents=True, exist_ok=True)
    today = dt.date(2026, 8, 29)
    old = today - dt.timedelta(days=31)
    young = today - dt.timedelta(days=29)
    for stamp in (old, young):
        (d / f"{stamp.isoformat()}.log").write_text("x", encoding="utf-8")
    log = job.Log(d / "run.tmp", 100, 10_000)
    removed = job.prune(log, 30, today)
    log.close()
    assert removed == [f"{old.isoformat()}.log"]
    assert not (d / f"{old.isoformat()}.log").exists()
    assert (d / f"{young.isoformat()}.log").exists()


#: Filenames that are NOT this job's output but that `date.fromisoformat` still parses as a
#: long-past date. These are the only cases where the DATED_LOG ownership filter does any
#: work the date parse does not already do — and so the only ones that can prove it works.
#: `20200101` and `2020-W01-1` are accepted by fromisoformat on Python 3.11+ (basic and week
#: ISO forms); this job only ever writes `YYYY-MM-DD.log`.
FOREIGN_BUT_DATE_PARSEABLE = ("20200101.log", "2020-W01-1.log")
FOREIGN_UNPARSEABLE = ("launchd.log", "operator-saved-2020-01-01.log", "notes.log")


def test_retention_never_deletes_files_it_does_not_own(env, tmp_path):
    """Positive control for the DATED_LOG guard: a sweep that deletes what it did not
    write is a data-loss bug waiting for a slow week.

    Amended after a mutation check: the first version listed only names `fromisoformat`
    rejects anyway, so deleting the ownership filter outright left it green — it was
    measuring the date parse, not the guard (methodology §7.9). The date-parseable foreign
    names below are what actually separate the two."""
    d = tmp_path / "state" / "logs" / "biblio_resume"
    d.mkdir(parents=True, exist_ok=True)
    keep = FOREIGN_BUT_DATE_PARSEABLE + FOREIGN_UNPARSEABLE
    for name in keep:
        (d / name).write_text("keep me", encoding="utf-8")
    log = job.Log(d / "run.tmp", 100, 10_000)
    assert job.prune(log, 0, dt.date(2026, 8, 29)) == []
    log.close()
    for name in keep:
        assert (d / name).exists(), f"{name} deleted by a sweep that does not own it"


# ------------------------------------------------------- §5 guardrail: spend is impossible

def test_module_detector_catches_a_seeded_spend_module():
    """Positive control for the detector itself. A checker that has never returned a hit is
    indistinguishable from `return []`."""
    assert job.spend_modules_loaded({"json": 1, "kg.biblio": 1}) == []
    assert job.spend_modules_loaded(
        {"json": 1, "kg.extraction.model_stub": 1}) == ["kg.extraction.model_stub"]
    assert job.spend_modules_loaded({"kg.spend.foo": 1}) == ["kg.spend.foo"]
    assert job.spend_modules_loaded({"kg.spendthrift": 1}) == [], "prefix matched too greedily"


def test_leg_output_is_streamed_unbuffered(tmp_path):
    """A leg's stdout goes to a pipe, so Python block-buffers it: without PYTHONUNBUFFERED a
    long leg shows nothing until exit and a killed leg loses its output entirely. The log is
    the only artifact a scheduled run leaves, so buffering it away is losing the record."""
    log = job.Log(tmp_path / "x.log", 2000, 100_000)
    code = "import sys,os; print('child-unbuffered=' + os.environ.get('PYTHONUNBUFFERED',''))"
    assert job.run_leg("probe", [sys.executable, "-c", code], log) == 0
    log.close()
    assert "child-unbuffered=1" in (tmp_path / "x.log").read_text(encoding="utf-8")


def test_leg_that_cannot_start_is_reported_not_raised(tmp_path):
    """A missing interpreter must land in the log as a failure, not an unhandled traceback
    that leaves the run with no record of why it died."""
    log = job.Log(tmp_path / "x.log", 2000, 100_000)
    assert job.run_leg("probe", ["/nonexistent/python", "-c", ""], log) == 127
    log.close()
    assert "FAILED to start" in (tmp_path / "x.log").read_text(encoding="utf-8")


def test_module_check_is_a_delta_not_an_absolute_reading(env, tmp_path, monkeypatch):
    """Regression, found by running the full suite: the check first read `sys.modules`
    absolutely, so ANY other test that imported `kg.spend` for its own reasons failed this
    job with rc=4. That is a false alarm, and it also hid the real point — the legs are
    subprocesses, so their imports are never in this process at all. Only what appears
    DURING the run is attributable to the run."""
    # already resident before the run: not this job's doing, must not fire
    assert job.spend_modules_loaded({"kg.spend": 1}, baseline={"kg.spend"}) == []
    # appeared during the run: attributable, must fire
    assert job.spend_modules_loaded({"kg.spend": 1}, baseline=set()) == ["kg.spend"]

    monkeypatch.setattr(job, "run_leg", lambda name, cmd, log: 0)
    monkeypatch.setitem(sys.modules, "kg.spend", object())   # pollute as a test runner would
    assert job.main(["--no-commit"]) == 0, "pre-existing import misattributed to the scheduled run"
    assert "guardrail: this run imported no spend-path module" in _log(tmp_path)


def test_module_check_fires_when_the_run_itself_imports_a_spend_path(env, tmp_path,
                                                                     monkeypatch):
    """Positive control for the delta form: a leg that imports a spend module mid-run."""
    sys.modules.pop("kg.spend", None)

    def importing_leg(name, cmd, log):
        sys.modules["kg.spend"] = object()
        return 0
    monkeypatch.setattr(job, "run_leg", importing_leg)
    try:
        assert job.main(["--no-commit"]) == 4
        assert "this run imported spend-path module(s): kg.spend" in _log(tmp_path)
    finally:
        sys.modules.pop("kg.spend", None)


def test_real_scheduled_legs_import_no_spend_path():
    """The PREVENTIVE half, against the real modules the unit actually runs. If someone
    later adds a model call to the harvest or the projection, this fails."""
    import subprocess
    repo = Path(job.__file__).resolve().parent.parent.parent
    code = ("import sys; sys.path[:0]=['.','scripts'];"
            "import kg.biblio, t1_build_index;"
            "import json;print(json.dumps(sorted(m for m in sys.modules "
            "if 'model_stub' in m or m=='kg.spend')))")
    r = subprocess.run([sys.executable, "-c", code], cwd=repo, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "[]", f"spend path reachable from a scheduled leg: {r.stdout}"


def test_ledger_change_fails_the_job(env, tmp_path, monkeypatch):
    """POSITIVE CONTROL for the detective guard: a leg that really appends to the shared
    spend ledger must take the job down nonzero, whatever the legs' own exit codes say."""
    def spending_leg(name, cmd, log):
        if name == "biblio-resume":
            with (tmp_path / "state" / "spend_ledger.jsonl").open("a", encoding="utf-8") as f:
                f.write('{"record":"reserve","tokens":111000}\n')
        return 0
    monkeypatch.setattr(job, "run_leg", spending_leg)
    assert job.main(["--no-commit"]) == 3
    text = _log(tmp_path)
    assert "FATAL: spend ledger changed" in text
    assert "unbudgeted by construction" in text


def test_clean_run_is_green_and_says_both_guards_held(env, tmp_path, monkeypatch):
    monkeypatch.setattr(job, "run_leg", lambda name, cmd, log: 0)
    assert job.main(["--no-commit"]) == 0
    text = _log(tmp_path)
    assert "guardrail: spend ledger unchanged" in text
    assert "guardrail: this run imported no spend-path module" in text
    assert "rc=0" in text


def test_leg_failure_propagates_but_does_not_mask_the_guard(env, tmp_path, monkeypatch):
    monkeypatch.setattr(job, "run_leg", lambda name, cmd, log: 2 if name == "t1-project" else 0)
    assert job.main(["--no-commit"]) == 2


def test_api_credentials_are_dropped_on_every_invocation(env, monkeypatch):
    """DD-007: subscription OAuth only. The bash wrapper this replaces protected one caller."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-not-survive")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "tok")
    monkeypatch.setattr(job, "run_leg", lambda name, cmd, log: 0)
    import os
    assert job.main(["--no-commit"]) == 0
    assert "ANTHROPIC_API_KEY" not in os.environ
    assert "ANTHROPIC_AUTH_TOKEN" not in os.environ


def test_dry_run_executes_no_leg_and_writes_no_ledger_change(env, tmp_path, monkeypatch):
    monkeypatch.setattr(job, "run_leg",
                        lambda *a, **k: pytest.fail("dry run dispatched a leg"))
    assert job.main(["--dry-run"]) == 0
    assert "dry run: legs not executed" in _log(tmp_path)


# ------------------------------------------------------------------- completion behaviour

def test_coverage_complete_is_noted_but_nothing_self_disables(env, tmp_path, monkeypatch):
    """Task §4: at full coverage the job keeps running and says so. Removal is an operator
    choice — a job that deletes itself on a threshold takes its evidence with it."""
    monkeypatch.setattr(job, "run_leg", lambda name, cmd, log: 0)
    monkeypatch.setattr(job, "coverage_note", _REAL_COVERAGE_NOTE)
    import types
    fake = types.SimpleNamespace(coverage=lambda: {"resolved": 178, "total": 178,
                                                   "retryable": 0, "partial_finding": 0,
                                                   "blocked": 0})
    monkeypatch.setitem(sys.modules, "kg.biblio", fake)
    monkeypatch.setattr(sys.modules["kg"], "biblio", fake, raising=False)
    assert job.main(["--no-commit"]) == 0
    assert "coverage: COMPLETE" in _log(tmp_path)


def test_coverage_incomplete_says_nothing_about_completion(env, tmp_path, monkeypatch):
    monkeypatch.setattr(job, "run_leg", lambda name, cmd, log: 0)
    monkeypatch.setattr(job, "coverage_note", _REAL_COVERAGE_NOTE)
    import types
    fake = types.SimpleNamespace(coverage=lambda: {"resolved": 29, "total": 178,
                                                   "retryable": 149, "partial_finding": 0,
                                                   "blocked": 1})
    monkeypatch.setitem(sys.modules, "kg.biblio", fake)
    monkeypatch.setattr(sys.modules["kg"], "biblio", fake, raising=False)
    assert job.main(["--no-commit"]) == 0
    text = _log(tmp_path)
    assert "coverage: resolved=29/178" in text and "COMPLETE" not in text


# ------------------------------------------------------------------------ the launchd unit

def test_render_substitutes_every_placeholder():
    text = installer.render(sys.executable)
    assert "@" not in text.replace("@HOUR@", ""), "placeholder markers survived"
    assert "<string>com.brock.aikg.biblio-resume</string>" in text
    assert "biblio_resume_job.py" in text


def test_render_reads_the_schedule_from_controls_not_the_template(monkeypatch, tmp_path):
    """Schedule is config, not a literal in a committed XML file (~/GitHub §2)."""
    cfg = {"jobs": {"biblio_resume": {"hour": 5, "minute": 7}}}
    (tmp_path / "controls.yaml").write_text(yaml.safe_dump(cfg), encoding="utf-8")
    monkeypatch.setattr(installer, "REPO", tmp_path)
    text = installer.render(sys.executable)
    assert "<integer>5</integer>" in text and "<integer>07</integer>" in text


def test_render_refuses_a_nonexistent_interpreter():
    with pytest.raises(SystemExit, match="interpreter does not exist"):
        installer.render("/nope/python3")


def test_render_fails_loud_on_an_unsubstituted_placeholder(monkeypatch, tmp_path):
    """Positive control: a renamed placeholder must not ship into a loaded unit."""
    bad = tmp_path / "t.template"
    # @TYPO_LABEL@ is exactly the hazard: a marker no substitution key matches. The first
    # version of this guard only looked for keys it already knew, so it saw nothing here.
    bad.write_text("<string>@REPO@</string><string>@TYPO_LABEL@</string>", encoding="utf-8")
    monkeypatch.setattr(installer, "TEMPLATE", bad)
    with pytest.raises(SystemExit, match="unsubstituted placeholders"):
        installer.render(sys.executable)


# --- Lane 2 of cc_tasks/2026-09-03_hygiene_sweep_post_g1_freeze.md -----------------------
# The job now commits its own writes. The risk this creates is bigger than the one it fixes:
# a scheduled `git` caller that stages the wrong thing commits an operator's half-finished
# work at 2:30am under this job's name. So the path list is pinned, the wildcard is proven
# absent, and the failure modes are shown failing.

class _RecordingLog:
    def __init__(self): self.lines = []
    def line(self, text): self.lines.append(str(text).rstrip())
    @property
    def text(self): return "\n".join(self.lines)


def _job():
    import importlib, sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "jobs"))
    return importlib.import_module("biblio_resume_job")


def test_commit_paths_are_exactly_the_legs_write_set():
    """If a leg gains an output, this list must gain it too — otherwise the new file becomes
    the next permanently-dirty file, which is the defect this lane exists to remove."""
    job = _job()
    assert job.COMMIT_PATHS == (
        "docs/corpus/acquisition_candidates.md",
        "docs/corpus/manifest_table.md",
        "docs/corpus/operator_pickup.md",
        "state/t2_priority.json",
        "events/batch-024.jsonl",
    )
    # the gitignored provider cache must never be staged
    assert "state/candidate_oa.json" not in job.COMMIT_PATHS


def test_the_job_never_stages_by_wildcard():
    """A positive control on the source itself: `git add -A`/`-u`/`.` would defeat every
    other guard in this file, and no test of behaviour catches it if the paths happen to be
    the only dirty files on the day the test runs."""
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "scripts" / "jobs"
           / "biblio_resume_job.py").read_text(encoding="utf-8")
    code = "\n".join(ln for ln in src.splitlines()
                     if not ln.lstrip().startswith("#") and not ln.lstrip().startswith("#:"))
    for forbidden in ('"add", "-A"', '"add", "-u"', '"add", "."', "add -A", "add -u"):
        assert forbidden not in code, f"job stages by wildcard: {forbidden}"
    assert '_git(log, "add", "--", *present)' in src      # explicit, and `--` ends the options


def test_nothing_to_commit_is_a_clean_no_op(monkeypatch):
    job = _job()
    calls = []

    def fake_git(log, *args):
        calls.append(args)
        return (0, "") if args[0] in ("add", "diff") else (0, "")
    monkeypatch.setattr(job, "_git", fake_git)
    monkeypatch.setattr(job.Path, "exists", lambda self: True, raising=False)
    log = _RecordingLog()
    import datetime as dt
    assert job.commit_own_writes(log, dt.date(2026, 9, 4)) == 0
    assert "nothing to commit" in log.text
    assert not any(a[0] == "commit" for a in calls)       # never committed an empty index


def test_a_failing_commit_fails_the_run(monkeypatch):
    job = _job()

    def fake_git(log, *args):
        if args[0] == "diff":
            return 0, "docs/corpus/operator_pickup.md"
        if args[0] == "status":
            return 0, ""
        if args[0] == "commit":
            return 1, "nothing added / hook rejected"
        return 0, ""
    monkeypatch.setattr(job, "_git", fake_git)
    monkeypatch.setattr(job.Path, "exists", lambda self: True, raising=False)
    log = _RecordingLog()
    import datetime as dt
    assert job.commit_own_writes(log, dt.date(2026, 9, 4)) == 5
    assert "FATAL: git commit failed" in log.text


def test_a_failing_push_fails_the_run_and_says_the_commit_survived(monkeypatch):
    job = _job()

    def fake_git(log, *args):
        if args[0] == "diff":
            return 0, "state/t2_priority.json"
        if args[0] == "status":
            return 0, ""
        if args[0] == "push":
            return 1, "could not read from remote"
        return 0, ""
    monkeypatch.setattr(job, "_git", fake_git)
    monkeypatch.setattr(job.Path, "exists", lambda self: True, raising=False)
    log = _RecordingLog()
    import datetime as dt
    assert job.commit_own_writes(log, dt.date(2026, 9, 4)) == 6
    assert "FATAL: git push failed" in log.text
    assert "will go out with the next successful push" in log.text


def test_files_dirty_outside_the_write_set_are_reported_and_left_alone(monkeypatch):
    job = _job()
    staged_arg = {}

    def fake_git(log, *args):
        if args[0] == "add":
            staged_arg["paths"] = args[2:]
            return 0, ""
        if args[0] == "diff":
            return 0, "docs/corpus/operator_pickup.md"
        if args[0] == "status":
            return 0, " M scripts/some_operator_edit.py\n M docs/corpus/operator_pickup.md"
        return 0, ""
    monkeypatch.setattr(job, "_git", fake_git)
    monkeypatch.setattr(job.Path, "exists", lambda self: True, raising=False)
    log = _RecordingLog()
    import datetime as dt
    assert job.commit_own_writes(log, dt.date(2026, 9, 4)) == 0
    assert "scripts/some_operator_edit.py" in log.text
    assert "left alone" in log.text
    assert "scripts/some_operator_edit.py" not in staged_arg["paths"]


def test_a_guardrail_breach_skips_the_commit():
    """Output produced by a run that reached a spend path must not be published by that run."""
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent / "scripts" / "jobs"
           / "biblio_resume_job.py").read_text(encoding="utf-8")
    assert "if breach:" in src and "commit skipped: guardrail breach" in src


def test_the_scheduled_unit_does_not_pass_no_commit():
    """--no-commit exists for manual runs. If it ever reached the plist the nightly job would
    go back to leaving a dirty tree, silently."""
    from pathlib import Path
    plist = (Path(__file__).resolve().parent.parent / "scripts" / "launchd"
             / "com.brock.aikg.biblio-resume.plist.template")
    assert plist.exists(), f"plist template missing at {plist}"
    text = plist.read_text(encoding="utf-8")
    assert "--no-commit" not in text
    assert "biblio_resume_job.py" in text
