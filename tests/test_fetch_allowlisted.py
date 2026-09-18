"""`scripts/fetch_allowlisted.py`, the session side of a task's declared network allowlist.

`cc_tasks/2026-09-18_network_allowlist.md` decision 3: the helper refuses to run when
`SELDON_NETWORK_ALLOWLIST` is unset, refuses any URL whose host is not on it **before any
socket opens**, fetches robots-first under the identified UA, and writes one log line per
request with URL, status, bytes and sha256.

"Before any socket opens" is asserted at the socket, not inferred: every test here runs with
`socket.socket.connect`, `socket.create_connection` and `socket.getaddrinfo` replaced by a
recorder that raises, so a refusal that happened after a DNS lookup or a connect would fail
the test rather than pass it. The on-list paths use `httpx.MockTransport`, which answers
in-process and never reaches the socket layer either.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import socket
import sys
from pathlib import Path

import httpx
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from scan import load_params                                        # noqa: E402
from scan.clock import VirtualClock                                 # noqa: E402

_spec = importlib.util.spec_from_file_location("fetch_allowlisted",
                                               REPO / "scripts" / "fetch_allowlisted.py")
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)


@pytest.fixture
def sockets(monkeypatch):
    """Every attempt to resolve or connect, recorded and refused."""
    seen: list = []

    def refuse(kind):
        def _f(*a, **k):
            seen.append((kind, a[1:] if kind == "connect" else a))
            raise AssertionError(f"socket {kind} attempted: {a!r}")
        return _f

    monkeypatch.setattr(socket.socket, "connect", refuse("connect"))
    monkeypatch.setattr(socket, "create_connection", refuse("create_connection"))
    monkeypatch.setattr(socket, "getaddrinfo", refuse("getaddrinfo"))
    return seen


def _transport(routes: dict, hits: list):
    def handler(request: httpx.Request):
        hits.append(str(request.url))
        status, body, headers = routes.get(str(request.url), (404, b"", {}))
        return httpx.Response(status, content=body, headers=headers)
    return httpx.MockTransport(handler)


def test_the_env_name_is_the_one_seldon_sets():
    try:
        from seldon.core import dispatch as D
    except ImportError:
        pytest.skip("seldon not importable here")
    assert F.ALLOWLIST_ENV == D.NETWORK_ALLOWLIST_ENV


@pytest.mark.parametrize("env", [{}, {"SELDON_NETWORK_ALLOWLIST": ""},
                                 {"SELDON_NETWORK_ALLOWLIST": " , "}])
def test_refuses_to_run_when_the_allowlist_is_unset(env):
    with pytest.raises(F.AllowlistUnset):
        F.load_allowlist(env)


def test_main_refuses_to_run_without_the_variable(monkeypatch, tmp_path, sockets, capsys):
    monkeypatch.delenv(F.ALLOWLIST_ENV, raising=False)
    code = F.main(["https://github.com/x", "--out-dir", str(tmp_path / "o"),
                   "--log", str(tmp_path / "log.jsonl")])
    assert code == 2
    assert "refused" in capsys.readouterr().err
    assert not (tmp_path / "log.jsonl").exists()
    assert sockets == []


def test_an_off_list_host_is_refused_before_any_socket_opens(monkeypatch, tmp_path, sockets):
    """The test the task names: an off-list host, refused, and nothing reached the socket."""
    monkeypatch.setenv(F.ALLOWLIST_ENV, "github.com,archive.org")
    log_path = tmp_path / "fetch.jsonl"
    code = F.main(["https://www.noaa.gov/sites/default/files/NAO.pdf",
                   "--out-dir", str(tmp_path / "o"), "--log", str(log_path)])
    assert code == 1
    assert sockets == [], "a socket was touched for an off-list host"
    lines = [json.loads(ln) for ln in log_path.read_text().splitlines()]
    assert len(lines) == 1
    assert lines[0]["event"] == "refused" and lines[0]["status"] is None
    assert "'www.noaa.gov' is not on SELDON_NETWORK_ALLOWLIST" in lines[0]["reason"]
    assert not (tmp_path / "o").exists()


@pytest.mark.parametrize("url", [
    "https://api.github.com/repos",     # a subdomain is a different host: no suffix matching
    "https://github.com.evil.example/", # nor prefix matching
    "ftp://github.com/file",            # not an http(s) fetch
    "file:///etc/passwd",
])
def test_check_url_is_exact_host_and_http_only(url):
    with pytest.raises(F.OffAllowlist):
        F.check_url(url, ("github.com",))


def test_check_url_is_case_insensitive_on_the_host():
    assert F.check_url("https://GitHub.COM/a", ("github.com",)) == "github.com"


def test_an_on_list_fetch_is_robots_first_and_logs_every_request(tmp_path, sockets):
    body = b"# the checklist\n"
    routes = {"https://raw.githubusercontent.com/robots.txt": (200, b"User-agent: *\nAllow: /\n",
                                                              {}),
              "https://raw.githubusercontent.com/o/r/main/checklist.md": (200, body, {})}
    hits: list = []
    log = F.FetchLog(tmp_path / "fetch.jsonl")
    rows = F.fetch_all(["https://raw.githubusercontent.com/o/r/main/checklist.md"],
                       tmp_path / "out", log, load_params(), ("raw.githubusercontent.com",),
                       transport=_transport(routes, hits), clock=VirtualClock())
    assert sockets == []
    assert hits == ["https://raw.githubusercontent.com/robots.txt",
                    "https://raw.githubusercontent.com/o/r/main/checklist.md"]
    assert rows[0]["obtained"] and rows[0]["sha256"] == hashlib.sha256(body).hexdigest()
    assert rows[0]["acquired_by"] == "scripts/fetch_allowlisted.py"
    assert (tmp_path / "out" / "checklist.md").read_bytes() == body
    lines = [json.loads(ln) for ln in (tmp_path / "fetch.jsonl").read_text().splitlines()]
    assert [ln["url"] for ln in lines] == hits
    assert all({"url", "status", "bytes", "sha256"} <= set(ln) for ln in lines)
    assert lines[1]["bytes"] == len(body) and lines[1]["status"] == 200


def test_a_redirect_off_the_list_is_refused_at_that_hop(tmp_path, sockets):
    """github.com archives redirect to codeload.github.com. The guard runs on every hop, so a
    list that names only github.com refuses the second host before it is contacted."""
    routes = {"https://github.com/robots.txt": (200, b"", {}),
              "https://github.com/o/r/archive/main.zip":
                  (302, b"", {"location": "https://codeload.github.com/o/r/zip/main"})}
    hits: list = []
    log = F.FetchLog(tmp_path / "fetch.jsonl")
    rows = F.fetch_all(["https://github.com/o/r/archive/main.zip"], tmp_path / "out", log,
                       load_params(), ("github.com",), transport=_transport(routes, hits),
                       clock=VirtualClock())
    assert sockets == []
    assert "https://codeload.github.com/o/r/zip/main" not in hits
    assert not rows[0]["obtained"] and "codeload.github.com" in rows[0]["refused"]
    events = [json.loads(ln) for ln in (tmp_path / "fetch.jsonl").read_text().splitlines()]
    assert events[-1]["event"] == "refused"
    assert events[-1]["url"] == "https://codeload.github.com/o/r/zip/main"


def test_an_existing_file_is_never_overwritten(tmp_path, sockets):
    out = tmp_path / "out"
    out.mkdir()
    (out / "a.md").write_bytes(b"kept")
    rows = F.fetch_all(["https://github.com/a.md"], out, F.FetchLog(tmp_path / "l.jsonl"),
                       load_params(), ("github.com",), transport=_transport({}, []),
                       clock=VirtualClock())
    assert (out / "a.md").read_bytes() == b"kept"
    assert "not overwritten" in rows[0]["error"]
