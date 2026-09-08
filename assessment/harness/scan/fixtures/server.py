"""Test-only static server for the control fixtures. **Localhost, no network egress.**

Task §4, extended by `cc_tasks/2026-09-07_scan_harness_v3.md` §1.4 and
`cc_tasks/2026-09-08_scan_harness_v4.md` §1.2. Five fixtures, because a
control that cannot FAIL is not a control: a rule that returns `error` for every input passes a
two-fixture gate made only of `pass` and `fail` cases, and the two branches that mattered most
in the 2026-09-07 cycle — a host that refuses an identified client, and a host that resets the
connection — had no fixture at all. A12's central branch (*robots permits and the host refuses*)
was tested by a hand-built observation pair instead, which tests the rule and not the harness.

* `passes_all` — a well-formed surface; unknown paths are a real 404.
* `fails_all` — the failure mode A10 exists to catch: a **soft-404**, HTTP 200 with an error
  shell for any path, which is what makes an invalid route indistinguishable from a valid one.
* `refuses_identified_client` — robots.txt is served and PERMITS every crawler; every content
  path answers 403 to this scanner. The declared and enforced layers disagree, which is exactly
  what A12 measures and what `www.bls.gov` did to the first smoke run.
* `resets_connection` — the socket is accepted and reset (RFC 9293 RST) before a byte of
  response. Nothing is observable, including robots.txt.
* `invalid_route_unobserved` — everything `passes_all` serves, and the connection reset on
  A10's invented invalid route ALONE. PARTIAL blindness, which is the state no other fixture
  can reach: `resets_connection` blinds every leg at once, so it cannot reproduce the surface
  that produced `RULE-A10-v2`'s false `pass` — deep link served, invalid route never observed.

`HOSTPORT` in a fixture body is substituted at serve time, because a sitemap that must list an
absolute URL cannot know the ephemeral port until the server binds.

Every request is appended to the server's `requests` log, so a test can assert what the cycle
actually FETCHED rather than what it meant to — which is how §1.3's "one probe per object per
cycle" becomes checkable instead of asserted.
"""
from __future__ import annotations

import http.server
import socket
import socketserver
import struct
import threading
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent
#: Loopback only, and named once because two things need it: the bind call below, and the
#: sweep that recognises a stored body as fixture output rather than a measurement
#: (`scripts/quarantine_fixture_evidence.py`). A second literal in the sweep would be a
#: second definition of "what a fixture body looks like", and the one that drifted would be
#: the one that mattered.
BIND_HOST = "127.0.0.1"
#: The request-line cap `http.server` itself uses (`BaseHTTPRequestHandler.handle_one_request`
#: reads `65537` and calls anything longer a 414). Named because the reset fixture reads the
#: request line by hand before killing the socket, and an unnamed 65537 in a fixture is the
#: same unswept constant the collectors' integer-literal lint exists to refuse.
MAX_REQUEST_LINE = 65537
SOFT_404_SHELL = (b"<!doctype html><html><head><title>Page not found</title></head>"
                  b"<body><h1>Sorry, we can't find that page</h1></body></html>")


#: fixture name -> how the server behaves. A table, not four branches: a fifth fixture is one
#: entry, and the behaviour of each is readable in one place beside its name.
MODES = {
    "passes_all": {},
    "fails_all": {"soft_404": True},
    "refuses_identified_client": {"refuse_status": 403, "served_paths": ("/robots.txt",)},
    "resets_connection": {"reset": True},
    # Everything `passes_all` serves, EXCEPT the one path A10 invents to test the shell.
    # `resets_connection` cannot stand in for this: it resets every path, so every leg is
    # `error` and the surface is uniformly unobservable — it cannot isolate "the invalid route
    # was never observed and everything else was served", which is exactly the state
    # `scan-eia-flagship-1-open-data` was in when `RULE-A10-v2` scored it `pass`
    # (`cc_tasks/2026-09-07_scan_run_2_RESULT.md` §6.2). A control that cannot reproduce the
    # defect cannot certify the fix.
    #
    # `serves_as` rather than a copied directory: duplicating eleven fixture files would make
    # two definitions of "a well-formed surface", and the copy that drifted would be the one
    # that mattered. The fixture's own directory holds only its README.
    "invalid_route_unobserved": {"serves_as": "passes_all", "reset_on_invalid_route": True},
}


class _Handler(http.server.SimpleHTTPRequestHandler):
    root: Path = FIXTURES / "passes_all"
    soft_404: bool = False
    hostport: str = "localhost"
    #: When set, every path outside `served_paths` answers this status with no body — the
    #: shape of a WAF or bot manager refusing an identified client on a path robots permits.
    refuse_status: int | None = None
    served_paths: tuple = ()
    #: When true the connection is RESET before any response. `SO_LINGER` with a zero timeout
    #: is what makes `close()` send RST rather than FIN, so the client sees ECONNRESET — the
    #: failure `www150.statcan.gc.ca` produced 92 times and the closed set had no name for.
    reset: bool = False
    #: Same reset, scoped to A10's invented invalid route alone. The suffix is NOT a literal
    #: here: it is read from `params.a10_soft404.invalid_path_suffix` when the server binds, so
    #: the fixture and the collector can never disagree about which path is "the invalid one".
    reset_on_invalid_route: bool = False
    invalid_route_suffix: str = ""
    #: Appended to by every request. A list on the CLASS, handed in by `FixtureServer`, so the
    #: log outlives the per-request handler instance.
    requests: list = []

    def log_message(self, *a) -> None:            # silence in tests
        pass

    def _reset(self) -> None:
        """Send RST rather than FIN, so the client sees ECONNRESET / a server disconnect."""
        try:
            self.connection.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER,
                                       struct.pack("ii", 1, 0))
            self.connection.close()
        except OSError:                            # already gone; the client sees the same
            pass

    def handle(self) -> None:
        if self.reset:
            # The request line is READ first, then the socket is reset without a byte of
            # response. Resetting before the read is what the fixture used to do, and it made
            # the control non-deterministic: the client sometimes failed at CONNECT time with
            # `ConnectError: [Errno 22] Invalid argument` (EINVAL — a local socket-state
            # failure, not a statement by the peer), which `errors.classify_exception`
            # correctly declines to name and files as `unknown`. That is a real `unknown` on a
            # control fixture — the condition `cc_tasks/2026-09-07_scan_harness_v3.md` §1.4
            # makes a gate — arising from macOS socket state rather than from anything the
            # instrument measures, at roughly one observation in a hundred.
            #
            # A control that produces its declared failure only most of the time is not a
            # control. Reading the request first puts the client in an established connection
            # waiting on a response, so the RST always arrives as ECONNRESET / a server
            # disconnect and always classifies as `connection_reset`. The fixture's declared
            # behaviour is unchanged and is now what it declares: *reset before a byte of
            # response*, RFC 9293. `invalid_route_unobserved` resets at this same point, which
            # is why it was deterministic from its first run.
            try:
                self.rfile.readline(MAX_REQUEST_LINE)
            except OSError:
                pass
            self._reset()
            return
        super().handle()

    def _resets_this_path(self, path: str) -> bool:
        """True when this fixture kills the connection for THIS path and serves every other.

        The suffix comes from params, so a change to `a10_soft404.invalid_path_suffix` moves
        the fixture with the collector; a literal here would leave the control silently
        serving a 404 on the path it exists to make unobservable.
        """
        return bool(self.reset_on_invalid_route and self.invalid_route_suffix
                    and path.endswith(self.invalid_route_suffix))

    _head_only: bool = False

    def _serve_bytes(self, body: bytes, ctype: str, status: int = 200,
                     head_only: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        # Content-Length is the size of the REPRESENTATION, sent on a HEAD too (RFC 9110
        # §9.3.2). A3-v2 sizes a candidate download from it, so a HEAD that omitted it would
        # make every whole-product archive look like a file of unknown size.
        self.send_header("Content-Length", str(len(body)))
        if status == 200 and self.path.endswith((".html", ".csv", ".json", ".zip")):
            self.send_header("Last-Modified", "Tue, 01 Sep 2026 00:00:00 GMT")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def do_GET(self) -> None:                      # noqa: N802
        path = self.path.split("?")[0]
        # Logged BEFORE the reset: the request WAS received, and a request log that omitted it
        # would make the fixture look like a host that never heard from us.
        self.requests.append({"method": "HEAD" if self._head_only else "GET", "path": path})
        if self._resets_this_path(path):
            return self._reset()
        if self.refuse_status is not None and path not in self.served_paths:
            return self._serve_bytes(b"", "text/plain", status=self.refuse_status,
                                     head_only=self._head_only)
        rel = path.lstrip("/") or "index.html"
        target = self.root / rel
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            if self.soft_404:
                return self._serve_bytes(SOFT_404_SHELL, "text/html",
                                         head_only=self._head_only)
            return self._serve_bytes(b"not found", "text/plain", status=404,
                                     head_only=self._head_only)
        body = target.read_bytes()
        if b"HOSTPORT" in body:
            body = body.replace(b"HOSTPORT", self.hostport.encode())
        ctype = {".html": "text/html", ".json": "application/json", ".csv": "text/csv",
                 ".xml": "application/xml", ".txt": "text/plain",
                 ".pdf": "application/pdf", ".zip": "application/zip"}.get(
                     target.suffix, "application/octet-stream")
        self._serve_bytes(body, ctype, head_only=self._head_only)

    def do_HEAD(self) -> None:                     # noqa: N802
        """A1-v2 and A3-v2 HEAD every download link — their specs say to read the served
        Content-Type rather than the href suffix — so a control fixture that answered only GET
        would fail them for a reason that is about the fixture, not the rule."""
        self._head_only = True
        try:
            self.do_GET()
        finally:
            self._head_only = False


class FixtureServer:
    """`with FixtureServer('passes_all') as base_url:`"""

    def __init__(self, fixture: str) -> None:
        if fixture not in MODES:
            raise KeyError(f"no fixture mode {fixture!r}; known: {sorted(MODES)}")
        self.fixture = fixture
        self.httpd = None
        self.thread = None
        #: Every request this server answered, in order. Read by the test that asserts a
        #: surface's links are HEADed ONCE per cycle (§1.3).
        self.requests: list = []

    def __enter__(self) -> str:
        from .. import load_params
        mode = dict(MODES[self.fixture])
        # A fixture may SERVE another's tree (`invalid_route_unobserved` serves `passes_all`)
        # so that "a well-formed surface" has exactly one definition on disk.
        served_by = mode.pop("serves_as", self.fixture)
        handler = type("H", (_Handler,), {
            "root": FIXTURES / served_by,
            "requests": self.requests,
            "invalid_route_suffix": load_params()["a10_soft404"]["invalid_path_suffix"],
            **mode})
        socketserver.TCPServer.allow_reuse_address = True
        self.httpd = socketserver.TCPServer((BIND_HOST, 0), handler)
        port = self.httpd.server_address[1]
        handler.hostport = f"{BIND_HOST}:{port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        #: Also kept on the object, because `__enter__` returns the URL (every existing caller
        #: binds it that way) and a caller that also wants `requests` needs to hold the server.
        self.base_url = f"http://{BIND_HOST}:{port}"
        return self.base_url

    def __exit__(self, *exc) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
