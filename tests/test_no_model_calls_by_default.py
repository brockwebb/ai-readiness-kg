"""Seldon AD-036-R9 (task PA-001 Part E): a test never spends unasked, proved by a PATH shim.

A test that can reach a model launcher without a fake carries `@pytest.mark.live_model` and is
skipped unless `LIVE_MODEL_CALLS=1` (`tests/conftest.py`). This module proves the default is
zero model calls, rather than asserting it:

* a directory first on `PATH` holds an executable named `claude` that appends one line per
  invocation to a record file (and then refuses, exit 97, as the fixture lock's CLI does);
* `SELDON_MODELS_HOME` points at a fixture models home whose lock names that same shim, so a
  launcher that reads the lock outside the autouse fixture (collection-time code, the
  `assessment/` tests, which no conftest guards) is recorded too;
* `AIRKG_TEST_MODEL_CLI` names the shim, so the autouse fixture lock in `tests/conftest.py`
  names it as well: a test that reaches the lock's CLI is COUNTED, not only refused;
* a nested pytest run, WITHOUT `LIVE_MODEL_CALLS`, then runs the selection below, and the
  record file must be empty.

**The selection** (the full suite is not nested: it would double the gate's wall clock and run
every test beside its own outer copy): every `assessment/` test file, because no conftest puts
a fixture lock under them, plus every `tests/` file that carries `live_model`, imports a
launcher (`kg.extraction.model_stub`, `harness.consumers`, `seldon.models`,
`seldon.commands.dispatch`, `tests/model_lock.py`), imports a repository module that imports
one, or names such a module's script file (a subprocess launch). Computed at run time from
the source, so a file written tomorrow is covered without anyone editing this list. This
module is excluded, so the run never recurses.

**What it cannot see**: a child started under `env -i` with an absolute CLI path reads the live
lock and the live CLI and never consults `PATH`; that is why the two dispatch-pass tests in
`tests/test_dispatch_config.py` are gated rather than shimmed.

The module is in the `neo4j` xdist group (`tests/conftest.py` `_DECLARED_GROUPS`): the nested run
may include a test that opens the live database, and it must not run beside an outer one.
"""
from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

from model_lock import (FIXTURE_CLI_ENV, LIVE_MODEL_ENV as LIVE_ENV, MODELS_HOME_ENV,
                        build_models_home, write_cli)

REPO = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

#: Modules that launch, or stand in for, a model call. A test importing one is launcher-adjacent.
LAUNCHER_MODULES = ("kg.extraction.model_stub", "harness.consumers", "seldon.models",
                    "seldon.commands.dispatch", "model_lock")
#: Where repository code that might import a launcher lives (tests excluded).
CODE_ROOTS = ("kg", "scripts", "assessment", "mcp")
#: The nested run's own ceiling, and its worker count: a nested run beside an outer xdist run
#: shares the machine, so it takes a few workers rather than `auto`.
NESTED_TIMEOUT_S = 1500
NESTED_WORKERS = "4"


def _imports(path: Path) -> set:
    names = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names |= {f"{node.module}.{a.name}" for a in node.names}
    return names


def _names_a_launcher(names: set) -> bool:
    return any(n == m or n.startswith(m + ".") for n in names for m in LAUNCHER_MODULES)


def _launcher_code_modules() -> set:
    """Stems of the repository's non-test modules that import a launcher (one level)."""
    stems = set()
    for root in CODE_ROOTS:
        for path in (REPO / root).rglob("*.py"):
            if path.name.startswith("test_") or "tests" in path.relative_to(REPO).parts:
                continue
            try:
                names = _imports(path)
            except SyntaxError:
                continue
            if _names_a_launcher(names):
                stems.add(path.stem)
    return stems


def selection() -> list:
    """The test files the nested run covers (module docstring), repo-relative, sorted."""
    code = _launcher_code_modules()
    picked = {p for p in (REPO / "assessment").rglob("test_*.py")}
    for path in (REPO / "tests").glob("test_*.py"):
        text = path.read_text(encoding="utf-8")
        names = _imports(path)
        stems = {part for n in names for part in n.split(".")}
        if ("live_model" in text or _names_a_launcher(names) or stems & code
                or any(f"{stem}.py" in text for stem in code)):
            picked.add(path)
    picked.discard(SELF)
    return sorted(str(p.relative_to(REPO)) for p in picked)


def _shim(bindir: Path, record: Path) -> Path:
    bindir.mkdir(parents=True, exist_ok=True)
    return write_cli(bindir / "claude", (
        "#!/bin/sh\n"
        f"printf '%s\\n' \"claude $*\" >> '{record}'\n"
        "echo 'PATH shim: tests make no model calls by default (seldon AD-036-R9)' >&2\n"
        "exit 97\n"))


def _shim_env(tmp_path: Path) -> tuple:
    """The nested run's environment and its record file: the shim first on PATH, the lock and
    the fixture lock naming it, LIVE_MODEL_CALLS absent, and no outer pytest/xdist state."""
    record = tmp_path / "claude_invocations.log"
    record.write_text("", encoding="utf-8")
    shim = _shim(tmp_path / "shim_bin", record)
    home = build_models_home(tmp_path / "shim_models_home", cli_path=shim)
    env = {k: v for k, v in os.environ.items()
           if k != LIVE_ENV and not k.startswith("PYTEST_")}
    env["PATH"] = f"{shim.parent}{os.pathsep}{os.environ.get('PATH', '')}"
    env[MODELS_HOME_ENV] = str(home)
    env[FIXTURE_CLI_ENV] = str(shim)
    return env, record, shim


def test_the_shim_records_an_invocation(tmp_path):
    """Positive control on the instrument (kg_construction_methodology 7.6): a `claude` found on
    the shimmed PATH writes exactly one line per call. Without this, an empty record could mean
    the shim was never on PATH."""
    env, record, shim = _shim_env(tmp_path)
    r = subprocess.run(["claude", "-p", "positive control"], env=env, capture_output=True,
                       text=True)
    assert r.returncode == 97 and "PATH shim" in r.stderr
    assert record.read_text(encoding="utf-8").splitlines() == ["claude -p positive control"]


def test_the_selection_covers_the_gated_and_launcher_tests():
    picked = selection()
    for must in ("tests/test_dispatch_config.py", "tests/test_model001_launch.py",
                 "tests/test_extraction_model_stub.py", "tests/test_spend_guard.py"):
        assert must in picked, must
    assert str(SELF.relative_to(REPO)) not in picked              # the run never recurses
    assert any(p.startswith("assessment/") for p in picked)


def test_the_default_suite_makes_zero_claude_invocations(tmp_path):
    """The nested run over `selection()` without `LIVE_MODEL_CALLS`: the record must be empty,
    and every `live_model` test must have reported the opt-in as its skip reason."""
    env, record, _shim_path = _shim_env(tmp_path)
    files = selection()
    r = subprocess.run([sys.executable, "-m", "pytest", *files, "-q", "-rs",
                        "-p", "no:cacheprovider", "-n", NESTED_WORKERS, "--dist", "loadgroup"],
                       cwd=REPO, env=env, capture_output=True, text=True,
                       timeout=NESTED_TIMEOUT_S)
    tail = (r.stdout + r.stderr)[-4000:]
    # 0 all passed, 1 some failed: either way the tests RAN. Anything else (usage error,
    # interrupted, nothing collected) means the run proves nothing.
    assert r.returncode in (0, 1), tail
    calls = record.read_text(encoding="utf-8").splitlines()
    assert calls == [], (f"{len(calls)} `claude` invocation(s) under the default test run "
                         f"(seldon AD-036-R9): {calls[:5]}\n{tail}")
    assert f"set {LIVE_ENV}=1 to run" in r.stdout, (
        "no test reported the live_model opt-in as its skip reason; the gate is not active\n"
        + tail)


if __name__ == "__main__":  # pragma: no cover - a reader's aid
    print("\n".join(selection()))
