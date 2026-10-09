"""Seldon AD-035 at this repository's launchers (task MODEL-001 Part C).

* R3: the choke point (`kg/extraction/model_stub.invoke`) execs the LOCK's CLI, passes
  `--model <lock id>` for its role and `--settings` with `switchModelsOnFlag: false`, and lays
  all four `ANTHROPIC_DEFAULT_*_MODEL` ids over the child's environment.
* R6: every call carries a served-model receipt in its durable record (the spend ledger's
  settle); a served model other than the requested one stops the unit as `model_substituted`
  and the output is not used.
* R4: the configs name roles. A config naming a model id or an alias is refused at load.

Every test runs under a fixture lock (`tests/model_lock.py`); none reads the live lock and none
makes a model call.
"""
from __future__ import annotations

import json
import sys
import textwrap
import tomllib
from pathlib import Path

import pytest

from model_lock import (FIXTURE_IDS, MODELS_HOME_ENV, argv_lines, build_models_home,
                        env_lines, fake_cli_serving)
from seldon import models

from kg import spend
from kg.extraction import model_stub

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment"))
sys.path.insert(0, str(REPO / "scripts"))

FAMILY_ENV = ("ANTHROPIC_DEFAULT_OPUS_MODEL", "ANTHROPIC_DEFAULT_SONNET_MODEL",
              "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_FABLE_MODEL")


@pytest.fixture
def declared_run(tmp_path, monkeypatch):
    """A declared spend-ledger run on tmp_path (DD-022): invoke refuses undeclared runs."""
    controls = tmp_path / "controls.yaml"
    controls.write_text(textwrap.dedent("""\
        schema_version: "0.2"
        spend:
          daily_tokens: 1000000000
          call_class_floors: {cleanup: 36000, extraction: 111000, judge: 36000, g1_eval: 36000}
          empty_failure_backoff_seconds: [60, 300, 900]
          empty_failure_max_retries: 3
        """), encoding="utf-8")
    monkeypatch.setattr(spend, "_LEDGER_PATH", tmp_path / "spend_ledger.jsonl")
    monkeypatch.setattr(spend, "_CONTROLS_PATH", controls)
    spend.SpendLedger().declare("model001-test-run", 100_000_000,
                                declared_by="tests", call_class="extraction")
    monkeypatch.setenv(spend.RUN_ENV, "model001-test-run")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    return "model001-test-run"


@pytest.fixture
def fake_cli_home(tmp_path, monkeypatch):
    """A models home whose lock names a fake CLI. `serve(model)` rewrites the fake so its
    envelope reports `model` as the one that answered. PATH holds nothing else, so a launcher
    that ran `claude` from PATH instead of the lock's CLI could not reach a real one."""
    cli = tmp_path / "bin" / "fake-claude"
    cli.parent.mkdir()
    home = build_models_home(tmp_path / "models_home", cli_path=cli)
    monkeypatch.setenv(MODELS_HOME_ENV, str(home))
    monkeypatch.setenv("PATH", f"{cli.parent}:/usr/bin:/bin")

    def serve(served: str, result: str = '{"ok": 1}') -> Path:
        return fake_cli_serving(cli, served, result)
    return cli, serve


def _settles(ledger_path: Path) -> list:
    return [json.loads(l) for l in ledger_path.read_text().splitlines()
            if json.loads(l).get("record") == "settle"]


# --------------------------------------------------------------------------- R3: the launch

def test_invoke_execs_the_lock_cli_with_the_role_model_settings_and_env(monkeypatch,
                                                                       declared_run,
                                                                       fixture_models_home):
    """The extraction config's role is `document_extractor` (opus, effort high): the child is
    the lock's CLI, argv carries `--model <lock opus id>`, the switchModelsOnFlag settings and
    `--effort high`, and its environment carries all four lock ids."""
    captured = {}

    def fake_run(cmd, **kw):
        captured["cmd"], captured["env"] = cmd, kw.get("env")
        requested = cmd[cmd.index("--model") + 1]

        class R:
            returncode = 0
            stdout = json.dumps({"result": '{"ok": 1}', "usage": {"output_tokens": 2},
                                 "modelUsage": {requested: {"inputTokens": 3, "outputTokens": 2}}})
            stderr = ""
        return R()

    monkeypatch.setattr(model_stub.subprocess, "run", fake_run)
    meta = model_stub.invoke("d", "", prompt="p", config=model_stub.load_model_config())
    cmd = captured["cmd"]
    assert cmd[0] == str(fixture_models_home / "refusing-claude")          # the lock's CLI
    assert cmd[cmd.index("--model") + 1] == FIXTURE_IDS["opus"]
    settings = json.loads(cmd[cmd.index("--settings") + 1])
    assert settings == {"switchModelsOnFlag": False}
    assert cmd[cmd.index("--effort") + 1] == "high"
    env = captured["env"]
    assert env is not None
    assert {k: env[k] for k in FAMILY_ENV} == {
        "ANTHROPIC_DEFAULT_OPUS_MODEL": FIXTURE_IDS["opus"],
        "ANTHROPIC_DEFAULT_SONNET_MODEL": FIXTURE_IDS["sonnet"],
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": FIXTURE_IDS["haiku"],
        "ANTHROPIC_DEFAULT_FABLE_MODEL": FIXTURE_IDS["fable"]}
    assert meta["model_id"] == FIXTURE_IDS["opus"]
    assert meta["model_receipt"] == {"requested": FIXTURE_IDS["opus"],
                                     "served": FIXTURE_IDS["opus"], "side_models": [], "ok": True}


def test_a_real_child_sees_the_lock_env_and_argv(declared_run, fake_cli_home):
    """End to end through a real subprocess: the fake CLI records what it was given."""
    cli, serve = fake_cli_home
    serve(FIXTURE_IDS["fable"])
    cfg = model_stub.config_for_role("judge")
    meta = model_stub.invoke("d", "", prompt="p", config=cfg)
    argv = argv_lines(cli)
    assert argv[argv.index("--model") + 1] == FIXTURE_IDS["fable"]
    assert json.loads(argv[argv.index("--settings") + 1]) == {"switchModelsOnFlag": False}
    assert "--effort" not in argv                      # the judge role's effort is `default`
    assert env_lines(cli) == {
        "ANTHROPIC_DEFAULT_FABLE_MODEL": FIXTURE_IDS["fable"],
        "ANTHROPIC_DEFAULT_HAIKU_MODEL": FIXTURE_IDS["haiku"],
        "ANTHROPIC_DEFAULT_OPUS_MODEL": FIXTURE_IDS["opus"],
        "ANTHROPIC_DEFAULT_SONNET_MODEL": FIXTURE_IDS["sonnet"]}
    assert meta["output"] == {"ok": 1} and meta["model_receipt"]["ok"] is True
    settle = _settles(spend.SpendLedger().path)[-1]
    assert settle["model_receipt"] == meta["model_receipt"]
    assert settle["outcome_class"] == model_stub.CLI_SUCCESS


# ------------------------------------------------------------------------- R6: the receipt

def test_a_substituted_model_stops_the_unit_and_the_output_is_not_used(declared_run,
                                                                        fake_cli_home):
    cli, serve = fake_cli_home
    serve("some-other-model", result='{"concepts": [{"name": "must never be used"}]}')
    cfg = model_stub.load_model_config()
    with pytest.raises(model_stub.ModelSubstitutionError) as exc:
        model_stub.invoke("d", "", prompt="p", config=cfg)
    err = exc.value
    assert isinstance(err, models.ModelSubstituted)            # the accessor's named failure
    assert err.reason == "model_substituted"
    assert err.receipt == {"requested": FIXTURE_IDS["opus"], "served": "some-other-model",
                           "side_models": [], "ok": False}
    assert "must never be used" not in str(err)
    # The durable per-call record names the failure and carries the receipt; the tokens the
    # substituted call really spent are still booked (they were spent).
    settle = _settles(spend.SpendLedger().path)[-1]
    assert settle["outcome_class"] == "model_substituted"
    assert settle["model_receipt"]["served"] == "some-other-model"
    assert settle["actual_tokens"] == 18 and not settle.get("settled_as_estimate")


def test_the_g1_consumer_path_stops_on_substitution_too(declared_run, fake_cli_home):
    from harness.consumers import ClaudeCLIConsumer, load_consumer_config
    cli, serve = fake_cli_home
    serve("some-other-model", result="prose that must never be scored")
    consumer = ClaudeCLIConsumer(load_consumer_config(REPO / "assessment/config/g1_consumer.toml"))
    assert consumer.model_id == FIXTURE_IDS["opus"]
    with pytest.raises(models.ModelSubstituted):
        consumer.complete("restate this", call_id="g1.x")
    serve(FIXTURE_IDS["opus"], result="a restatement")
    done = consumer.complete("restate this", call_id="g1.y")
    assert done.text == "a restatement" and done.receipt["ok"] is True


def test_a_side_model_beside_the_served_one_still_stops_under_invariant_5(declared_run,
                                                                          monkeypatch):
    """This repo's invariant 5 is stricter than R6's minimum: the envelope reports EXACTLY the
    pinned model. A side call the CLI made is recorded in the receipt and stops the unit."""
    def fake_run(cmd, **kw):
        requested = cmd[cmd.index("--model") + 1]

        class R:
            returncode = 0
            stdout = json.dumps({"result": '{"ok": 1}', "usage": {"output_tokens": 50},
                                 "modelUsage": {"side-haiku": {"inputTokens": 5, "outputTokens": 1},
                                                requested: {"inputTokens": 9, "outputTokens": 50}}})
            stderr = ""
        return R()

    monkeypatch.setattr(model_stub.subprocess, "run", fake_run)
    with pytest.raises(model_stub.ModelSubstitutionError) as exc:
        model_stub.invoke("d", "", prompt="p", config=model_stub.load_model_config())
    assert exc.value.reason == "model_side_call"
    assert exc.value.receipt["ok"] is True and exc.value.receipt["side_models"] == ["side-haiku"]
    settle = _settles(spend.SpendLedger().path)[-1]
    assert settle["outcome_class"] == "model_side_call"


# ------------------------------------------------------------------- R4: configs name roles

def test_the_extraction_config_names_roles_and_resolves_them_through_the_lock():
    cfg = model_stub.load_model_config()
    assert cfg["role"] == "document_extractor"
    assert cfg["model_id"] == models.resolve("document_extractor") == FIXTURE_IDS["opus"]
    assert cfg["primary_judge_model_id"] == models.resolve(cfg["primary_judge_role"])
    assert cfg["secondary_judge_model_id"] == models.resolve(cfg["secondary_judge_role"])
    assert cfg["cleanup_model_id"] == models.resolve(cfg["cleanup_role"])
    assert "cli" not in cfg


def test_probe_raters_never_share_a_model_with_the_extractor():
    """model_config.yaml's standing constraint: neither probe rater shares the extractor's
    model. Under a family lock two roles of one family resolve to ONE id, so the constraint is
    a property of the roles' families, checked here against the real registry."""
    cfg = model_stub.load_model_config()
    ids = [cfg["model_id"], cfg["primary_judge_model_id"], cfg["secondary_judge_model_id"]]
    assert len(set(ids)) == 3, ids


@pytest.mark.parametrize("line", ["model_id: claude-opus-5", "model_id: opus",
                                  "primary_judge_model_id: claude-opus-4-8",
                                  "cleanup_model_id: claude-haiku-4-5-20251001",
                                  "cli: claude"])
def test_a_model_config_naming_a_model_or_cli_is_refused_at_load(tmp_path, line):
    p = tmp_path / "model_config.yaml"
    p.write_text("role: document_extractor\nprimary_judge_role: judge\n"
                 "secondary_judge_role: secondary_rater\ncleanup_role: background\n"
                 f"provider: claude_max_oauth\n{line}\n", encoding="utf-8")
    with pytest.raises(model_stub.ModelConfigError, match="AD-035"):
        model_stub.load_model_config(p)


@pytest.mark.parametrize("role", ["opus", "claude-opus-5-5", "no_such_role"])
def test_a_role_that_is_an_alias_an_id_or_unknown_is_refused(tmp_path, role):
    p = tmp_path / "model_config.yaml"
    p.write_text(f"role: {role}\nprimary_judge_role: judge\n"
                 "secondary_judge_role: secondary_rater\ncleanup_role: background\n"
                 "provider: claude_max_oauth\n", encoding="utf-8")
    with pytest.raises(model_stub.ModelConfigError, match="AD-035"):
        model_stub.load_model_config(p)


def test_the_g1_consumer_config_names_roles(tmp_path):
    from harness.config import ConfigError
    from harness.consumers import load_consumer_config
    real = REPO / "assessment/config/g1_consumer.toml"
    with real.open("rb") as fh:
        data = tomllib.load(fh)
    assert data["consumer"]["role"] == "consumer" and data["control"]["role"] == "background"
    assert "model_id" not in data["consumer"] and "cli" not in data["consumer"]
    assert load_consumer_config(real).model_id == FIXTURE_IDS["opus"]
    assert load_consumer_config(real, table="control").model_id == FIXTURE_IDS["haiku"]
    bad = tmp_path / "g1_consumer.toml"
    bad.write_text('[consumer]\nmodel_id = "claude-opus-5"\nprovider = "claude_max_oauth"\n'
                   'timeout_seconds = 60\ncall_class = "g1_eval"\n', encoding="utf-8")
    with pytest.raises(ConfigError, match="AD-035"):
        load_consumer_config(bad)


def test_invoke_refuses_a_config_without_a_role_or_with_a_stale_model_id(declared_run,
                                                                          monkeypatch):
    def must_not_run(*a, **k):
        raise AssertionError("a refused config reached the CLI")
    monkeypatch.setattr(model_stub.subprocess, "run", must_not_run)
    with pytest.raises(model_stub.ModelConfigError, match="role"):
        model_stub.invoke("d", "", prompt="p", config={"model_id": FIXTURE_IDS["opus"]})
    stale = {**model_stub.load_model_config(), "model_id": "claude-opus-5"}
    with pytest.raises(model_stub.ModelConfigError, match="AD-035"):
        model_stub.invoke("d", "", prompt="p", config=stale)


def test_a_kept_model_argument_must_be_a_lock_id_of_a_configured_role():
    cfg = model_stub.load_model_config()
    assert model_stub.role_for_model(FIXTURE_IDS["fable"], cfg) == cfg["primary_judge_role"]
    with pytest.raises(model_stub.ModelConfigError, match="lock"):
        model_stub.role_for_model("claude-opus-4-8", cfg)


# ----------------------------------------------------- independence guards follow the roles

def test_the_g1_calibration_rater_refuses_the_reviewer_role_model():
    import g1_calibration_rate as rate
    with pytest.raises(SystemExit, match="reviewer"):
        rate.main(["--role", "primary", "--ceiling-tokens", "1000"])


def test_the_er_gold_rater_refuses_the_pipeline_role_model():
    import er_gold_rate as erg
    with pytest.raises(SystemExit, match="independent"):
        erg.main(["--role", "document_extractor", "--ceiling-tokens", "1000"])


def test_scripts_take_roles_not_model_ids():
    """No script default names a model id any more (AD-035 R4)."""
    import er_gold_rate, g1_calibration_rate, homograph_judge, link_judge, rule_review
    for mod in (er_gold_rate, g1_calibration_rate, homograph_judge, link_judge, rule_review):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        assert 'add_argument("--model"' not in src, mod.__name__
        assert 'add_argument("--role"' in src, mod.__name__
