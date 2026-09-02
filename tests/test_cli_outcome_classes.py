"""Spend guard (DD-022): a `claude -p` failure is CLASSIFIED before it is settled.

Task 2026-09-02_spend_guard_exit1_and_state_merge, defect 1. On 2026-09-01 five consecutive
chunks exited 1 with an empty stderr and empty stdout (Max usage window closing);
`_looks_rate_limited` matched nothing, so each reservation was settled at the estimate
(140,000 tokens booked for no output) and the driver's systemic-failure rule stopped the
pass. An exit-1 with no output on either stream has produced nothing that could have been
billed: it is released and retried on a configured back-off, and only after the retry cap
is it settled at the estimate and counted as a failure.

No live CLI: every test fakes `subprocess.run` and `time.sleep`.
"""
import json
import textwrap

import pytest

from kg import spend
from kg.extraction import model_stub

CFG = {"model_id": "m", "cli": "claude"}
SCHEDULE = [7, 11, 13]        # deliberately not the production values, so a test that
MAX_RETRIES = 3               # reads the schedule from code instead of config fails


def _controls(path, schedule=SCHEDULE, max_retries=MAX_RETRIES, omit_policy=False):
    policy = "" if omit_policy else (
        f"  empty_failure_backoff_seconds: {json.dumps(schedule)}\n"
        f"  empty_failure_max_retries: {max_retries}\n")
    path.write_text(textwrap.dedent("""\
        schema_version: "0.2"
        spend:
          daily_tokens: 1000000000
          call_class_floors: {cleanup: 36000, extraction: 111000, judge: 36000}
        """) + policy, encoding="utf-8")


@pytest.fixture
def run(tmp_path, monkeypatch):
    """A declared run on a tmp ledger, tmp controls carrying the back-off policy, and a
    recorded (never executed) sleep."""
    controls = tmp_path / "controls.yaml"
    _controls(controls)
    monkeypatch.setattr(spend, "_LEDGER_PATH", tmp_path / "spend_ledger.jsonl")
    monkeypatch.setattr(spend, "_CONTROLS_PATH", controls)
    spend.SpendLedger().declare("cls-run", 100_000_000, declared_by="tests",
                                call_class="extraction")
    monkeypatch.setenv(spend.RUN_ENV, "cls-run")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    slept: list[int] = []
    monkeypatch.setattr(model_stub, "_sleep", slept.append)
    return {"controls": controls, "slept": slept, "run_id": "cls-run"}


def _records():
    return [json.loads(l) for l in spend.SpendLedger().path.read_text().splitlines()
            if l.strip()]


class Proc:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode, self.stdout, self.stderr = returncode, stdout, stderr


OK_STDOUT = json.dumps({"result": '{"ok": 1}',
                        "modelUsage": {"m": {"inputTokens": 10, "outputTokens": 5}}})


class Script:
    """Fake subprocess.run that plays a scripted sequence of outcomes and counts calls."""

    def __init__(self, procs):
        self.procs, self.calls = list(procs), 0

    def __call__(self, cmd, **kw):
        self.calls += 1
        return self.procs.pop(0) if len(self.procs) > 1 else self.procs[0]


# --- 1. the classifier is a pure function with a fixture per class ----------------------
@pytest.mark.parametrize("returncode, stdout, stderr, expected", [
    (0, OK_STDOUT, "", model_stub.CLI_SUCCESS),
    (0, OK_STDOUT, "some warning on stderr", model_stub.CLI_SUCCESS),
    (1, "", "", model_stub.CLI_EMPTY_FAILURE),
    (1, "", "   \n", model_stub.CLI_EMPTY_FAILURE),            # whitespace-only stderr
    (1, "\n", "", model_stub.CLI_EMPTY_FAILURE),               # whitespace-only stdout
    (1, None, None, model_stub.CLI_EMPTY_FAILURE),             # streams not captured
    (2, "", "", model_stub.CLI_EMPTY_FAILURE),                 # any non-zero exit
    (1, "", "Error: rate limit exceeded", model_stub.CLI_RATE_LIMITED),
    (1, "You've hit your limit", "", model_stub.CLI_RATE_LIMITED),
    (1, "", "529 overloaded", model_stub.CLI_RATE_LIMITED),
    (1, "", "Error: something broke", model_stub.CLI_ERROR_WITH_OUTPUT),
    (1, '{"partial": true}', "", model_stub.CLI_ERROR_WITH_OUTPUT),   # output on stdout
    (1, "partial", "trace", model_stub.CLI_ERROR_WITH_OUTPUT),
])
def test_classifier_fixtures(returncode, stdout, stderr, expected):
    assert model_stub.classify_cli_outcome(returncode, stdout, stderr) == expected


def test_the_classifier_is_the_only_rate_limit_matcher():
    """The existing marker matcher is what the classifier uses — one instrument."""
    for marker in model_stub._RATE_LIMIT_MARKERS:
        assert model_stub.classify_cli_outcome(1, "", f"x {marker} y") == \
            model_stub.CLI_RATE_LIMITED


# --- 2. empty_failure: release, back off per config, retry, then succeed ----------------
def test_empty_failure_is_released_backed_off_and_retried(run, monkeypatch):
    stub = Script([Proc(1), Proc(1), Proc(0, OK_STDOUT)])
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    out = model_stub.invoke("d", "", prompt="p", config=CFG)
    assert out["output"] == {"ok": 1}
    assert stub.calls == 3
    assert run["slept"] == SCHEDULE[:2], "back-off comes from controls.yaml, in order"
    recs = _records()
    releases = [r for r in recs if r["record"] == "release"]
    settles = [r for r in recs if r["record"] == "settle"]
    assert [r["outcome_class"] for r in releases] == ["empty_failure", "empty_failure"]
    assert [r["outcome_class"] for r in settles] == ["success"]
    assert settles[0]["actual_tokens"] == 15 and "settled_as_estimate" not in settles[0]
    # capacity: only the successful call is committed
    assert spend.SpendLedger().committed(run["run_id"]) == 15


def test_the_retry_cap_settles_at_the_estimate_and_fails_like_today(run, monkeypatch):
    """After `empty_failure_max_retries` retries the conservative rule returns: settle at the
    estimate, raise the plain invocation error (so the driver's systemic-failure streak counts
    it), and do NOT raise the rate-limit error a driver would back off on forever."""
    stub = Script([Proc(1)])
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    with pytest.raises(model_stub.ModelInvocationError) as exc:
        model_stub.invoke("d", "", prompt="p", config=CFG)
    assert not isinstance(exc.value, model_stub.ModelRateLimitError)
    assert "empty_failure" in str(exc.value)
    assert stub.calls == MAX_RETRIES + 1
    assert run["slept"] == SCHEDULE
    recs = _records()
    releases = [r for r in recs if r["record"] == "release"]
    settles = [r for r in recs if r["record"] == "settle"]
    assert len(releases) == MAX_RETRIES
    assert len(settles) == 1 and settles[0]["settled_as_estimate"] is True
    assert settles[0]["outcome_class"] == "empty_failure"
    assert settles[0]["actual_tokens"] == 111000       # the extraction floor, not zero


def test_a_schedule_shorter_than_the_cap_repeats_its_last_delay(run, monkeypatch):
    _controls(run["controls"], schedule=[5], max_retries=3)
    stub = Script([Proc(1)])
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    with pytest.raises(model_stub.ModelInvocationError):
        model_stub.invoke("d", "", prompt="p", config=CFG)
    assert run["slept"] == [5, 5, 5]


# --- 3. the conservative rule stays for error_with_output --------------------------------
def test_error_with_output_still_settles_at_the_estimate_without_retry(run, monkeypatch):
    stub = Script([Proc(1, "", "Error: model exploded")])
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    with pytest.raises(model_stub.ModelInvocationError, match="exited 1"):
        model_stub.invoke("d", "", prompt="p", config=CFG)
    assert stub.calls == 1 and run["slept"] == []
    settles = [r for r in _records() if r["record"] == "settle"]
    assert len(settles) == 1 and settles[0]["settled_as_estimate"] is True
    assert settles[0]["outcome_class"] == "error_with_output"


def test_rate_limited_is_unchanged_release_and_typed_error(run, monkeypatch):
    stub = Script([Proc(1, "", "429 rate limit")])
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    with pytest.raises(model_stub.ModelRateLimitError):
        model_stub.invoke("d", "", prompt="p", config=CFG)
    assert stub.calls == 1 and run["slept"] == [], "rate-limit back-off is the driver's"
    releases = [r for r in _records() if r["record"] == "release"]
    assert len(releases) == 1 and releases[0]["outcome_class"] == "rate_limited"
    assert spend.SpendLedger().committed(run["run_id"]) == 0


# --- 4. the ledger carries the class; status and reconcile break tokens down by it --------
def test_status_and_reconcile_report_tokens_booked_by_class(run, monkeypatch):
    monkeypatch.setattr(model_stub.subprocess, "run",
                        Script([Proc(1, "", "boom"), Proc(0, OK_STDOUT)]))
    with pytest.raises(model_stub.ModelInvocationError):
        model_stub.invoke("d", "", prompt="p", config=CFG)
    model_stub.invoke("d", "", prompt="p", config=CFG)
    monkeypatch.setattr(model_stub.subprocess, "run", Script([Proc(1, "", "hit your limit")]))
    with pytest.raises(model_stub.ModelRateLimitError):
        model_stub.invoke("d", "", prompt="p", config=CFG)
    ledger = spend.SpendLedger()
    st = ledger.status(run["run_id"])["runs"][run["run_id"]]
    assert st["settled_by_class"] == {"error_with_output": 111000, "success": 15}
    assert st["released_by_class"] == {"rate_limited": 1}
    assert st["settled"] == 111015, "the breakdown sums to the settled total"
    rep = ledger.reconcile(run["run_id"], model_call_tokens=111015)
    assert rep["ok"] and rep["settled_by_class"] == st["settled_by_class"]


def test_pre_classifier_records_are_reported_as_unclassified(run):
    ledger = spend.SpendLedger()
    g = ledger.reserve(run["run_id"], estimate_tokens=100)
    ledger.settle(g, 100)                    # a record written before this task
    st = ledger.status(run["run_id"])["runs"][run["run_id"]]
    assert st["settled_by_class"] == {"unclassified": 100}


# --- 5. the policy is config, and a missing policy fails before dispatch ------------------
def test_a_missing_backoff_policy_refuses_before_the_cli_runs(run, monkeypatch):
    _controls(run["controls"], omit_policy=True)
    stub = Script([Proc(0, OK_STDOUT)])
    monkeypatch.setattr(model_stub.subprocess, "run", stub)
    with pytest.raises(spend.SpendConfigError, match="empty_failure"):
        model_stub.invoke("d", "", prompt="p", config=CFG)
    assert stub.calls == 0


def test_the_production_controls_carry_the_policy():
    schedule, cap = spend.empty_failure_policy()
    assert schedule == [60, 300, 900] and cap == 3, "task-declared defaults"
