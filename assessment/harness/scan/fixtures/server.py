"""Test-only static server for the two control fixtures. **Localhost, no network egress.**

Task §4. `passes_all` behaves like a well-formed surface: unknown paths are a real 404.
`fails_all` behaves like the failure mode A10 exists to catch — a **soft-404**, HTTP 200 with
an error shell for any path, which is precisely what makes an invalid route indistinguishable
from a valid one to a machine.

`HOSTPORT` in a fixture body is substituted at serve time, because a sitemap that must list an
absolute URL cannot know the ephemeral port until the server binds.
"""
from __future__ import annotations

import http.server
import socketserver
import threading
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent
#: Loopback only, and named once because two things need it: the bind call below, and the
#: sweep that recognises a stored body as fixture output rather than a measurement
#: (`scripts/quarantine_fixture_evidence.py`). A second literal in the sweep would be a
#: second definition of "what a fixture body looks like", and the one that drifted would be
#: the one that mattered.
BIND_HOST = "127.0.0.1"
SOFT_404_SHELL = (b"<!doctype html><html><head><title>Page not found</title></head>"
                  b"<body><h1>Sorry, we can't find that page</h1></body></html>")


class _Handler(http.server.SimpleHTTPRequestHandler):
    root: Path = FIXTURES / "passes_all"
    soft_404: bool = False
    hostport: str = "localhost"

    def log_message(self, *a) -> None:            # silence in tests
        pass

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
        rel = self.path.split("?")[0].lstrip("/") or "index.html"
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
        self.fixture = fixture
        self.httpd = None
        self.thread = None

    def __enter__(self) -> str:
        handler = type("H", (_Handler,), {
            "root": FIXTURES / self.fixture,
            "soft_404": self.fixture == "fails_all"})
        socketserver.TCPServer.allow_reuse_address = True
        self.httpd = socketserver.TCPServer((BIND_HOST, 0), handler)
        port = self.httpd.server_address[1]
        handler.hostport = f"{BIND_HOST}:{port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return f"http://{BIND_HOST}:{port}"

    def __exit__(self, *exc) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
