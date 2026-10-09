"""A fixture model lock for tests (seldon AD-035, task MODEL-001 Part C).

Tests never read the live lock (`~/GitHub/seldon/models/models.lock.yaml`): a lock bump would
otherwise change what a test asserts, and a test that reached the live lock's CLI would make a
paid call. Every test runs under `SELDON_MODELS_HOME` pointed at a directory built here:

* `registry.yaml` is a COPY of seldon's own registry, so the roles a launcher names are the
  roles that exist (an unknown role still fails loudly, as it would in production);
* `models.lock.yaml` names ids that cannot be confused with a real model, and a CLI path that
  is either a script that refuses to run (the autouse default in `conftest.py`) or a fake CLI
  a test writes to stand in for `claude -p`.
"""
from __future__ import annotations

import json
import shutil
import stat
from pathlib import Path

import yaml

from seldon import models

#: The fixture lock's ids, one per family. Deliberately not shaped like a real model id.
FIXTURE_IDS = {"fable": "fixture-fable-1", "opus": "fixture-opus-1",
               "sonnet": "fixture-sonnet-1", "haiku": "fixture-haiku-1"}
FIXTURE_CLI_VERSION = "0.0.0-fixture"

#: The default CLI: refuses, so a test that reaches a real exec without meaning to fails loudly
#: instead of spending. Exit code 97 is not one the classifier treats as a rate limit.
_REFUSING_CLI = "#!/bin/sh\necho 'fixture CLI: tests make no model calls (MODEL-001)' >&2\nexit 97\n"


def seldon_registry() -> Path:
    """Seldon's registry, read from the seldon checkout before any test repoints the variable."""
    return models.models_home() / models.REGISTRY_FILE


def write_cli(path: Path, body: str) -> Path:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def fake_cli_serving(path: Path, served: str, result: str = '{"ok": 1}') -> Path:
    """A stand-in for `claude -p --output-format json` whose envelope says `served` answered,
    whatever `--model` asked for. It also writes its argv and the four family variables beside
    itself, so a test can read what the launcher passed."""
    envelope = json.dumps({"type": "result", "is_error": False, "result": result,
                           "session_id": "fixture-session",
                           "usage": {"output_tokens": 7},
                           "modelUsage": {served: {"inputTokens": 11, "outputTokens": 7}}})
    seen = path.with_suffix(".seen")
    body = ("#!/bin/sh\n"
            f"printf '%s\\n' \"$@\" > '{seen}.argv'\n"
            f"env | grep '^ANTHROPIC_DEFAULT_' | sort > '{seen}.env'\n"
            "cat > /dev/null\n"
            f"cat <<'ENVELOPE'\n{envelope}\nENVELOPE\n")
    return write_cli(path, body)


def build_models_home(home: Path, cli_path: Path | None = None,
                      registry: Path | None = None) -> Path:
    """A models home: a copy of seldon's registry plus a fixture lock naming `cli_path`."""
    home.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(registry or seldon_registry(), home / models.REGISTRY_FILE)
    if cli_path is None:
        cli_path = write_cli(home / "refusing-claude", _REFUSING_CLI)
    lock = {"schema": 1, "resolved_on": "2026-10-09", "resolved_at": "2026-10-09T00:00:00Z",
            "cli": {"version": FIXTURE_CLI_VERSION, "path": str(cli_path),
                    "npm_package": "fixture"},
            "families": {f: {"alias": f, "model": m} for f, m in FIXTURE_IDS.items()},
            "evidence": "fixture"}
    (home / models.LOCK_FILE).write_text(yaml.safe_dump(lock, sort_keys=False), encoding="utf-8")
    return home


def env_lines(seen_cli: Path) -> dict:
    """The `ANTHROPIC_DEFAULT_*` variables a fake CLI saw."""
    text = seen_cli.with_suffix(".seen.env").read_text(encoding="utf-8")
    return dict(line.split("=", 1) for line in text.splitlines() if "=" in line)


def argv_lines(seen_cli: Path) -> list:
    return seen_cli.with_suffix(".seen.argv").read_text(encoding="utf-8").splitlines()


#: The variable the accessor reads; re-exported so tests name it once.
MODELS_HOME_ENV = models.MODELS_HOME_ENV

__all__ = ["FIXTURE_IDS", "FIXTURE_CLI_VERSION", "MODELS_HOME_ENV", "build_models_home",
           "fake_cli_serving", "write_cli", "env_lines", "argv_lines", "seldon_registry"]
