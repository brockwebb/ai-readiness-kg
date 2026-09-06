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
SOFT_404_SHELL = (b"<!doctype html><html><head><title>Page not found</title></head>"
                  b"<body><h1>Sorry, we can't find that page</h1></body></html>")


class _Handler(http.server.SimpleHTTPRequestHandler):
    root: Path = FIXTURES / "passes_all"
    soft_404: bool = False
    hostport: str = "localhost"

    def log_message(self, *a) -> None:            # silence in tests
        pass

    def _serve_bytes(self, body: bytes, ctype: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        if status == 200 and self.path.endswith((".html", ".csv", ".json")):
            self.send_header("Last-Modified", "Tue, 01 Sep 2026 00:00:00 GMT")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:                      # noqa: N802
        rel = self.path.split("?")[0].lstrip("/") or "index.html"
        target = self.root / rel
        if target.is_dir():
            target = target / "index.html"
        if not target.is_file():
            if self.soft_404:
                return self._serve_bytes(SOFT_404_SHELL, "text/html")
            return self._serve_bytes(b"not found", "text/plain", status=404)
        body = target.read_bytes()
        if b"HOSTPORT" in body:
            body = body.replace(b"HOSTPORT", self.hostport.encode())
        ctype = {".html": "text/html", ".json": "application/json", ".csv": "text/csv",
                 ".xml": "application/xml", ".txt": "text/plain",
                 ".pdf": "application/pdf"}.get(target.suffix, "application/octet-stream")
        self._serve_bytes(body, ctype)


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
        self.httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
        port = self.httpd.server_address[1]
        handler.hostport = f"127.0.0.1:{port}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return f"http://127.0.0.1:{port}"

    def __exit__(self, *exc) -> None:
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
