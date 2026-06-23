"""HTTP fetch layer — stdlib urllib only (zero runtime dependency).

Public endpoints only: GET, a polite identifiable User-Agent, no auth, no API
keys. Network failures are captured into `Fetched.error` (never swallowed,
never raised past the probe — §4: failures are visible, and the harness must keep
going to report what it found and what it could not reach).

`build_fetched` is the pure normalization step (lowercase headers, decode body),
separated from the urllib call so it is testable without the network.
"""
from __future__ import annotations

import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional, Protocol, Tuple

# Default in-memory read cap: a backstop against a pathological endpoint streaming
# unbounded data into memory. Generous enough that real federal DCAT catalogs
# (often multiple MB) are retained WHOLE and parse cleanly — a too-small cap once
# truncated a 2MB catalog mid-JSON and produced a false "no catalog" D1 finding.
# Tunable via config ([http] max_body_bytes); evidence files are truncated
# separately by the EvidenceStore so this can stay large without writing huge files.
_DEFAULT_MAX_BODY_BYTES = 50_000_000


@dataclass
class Fetched:
    """A retrieved (or failed) artifact. This is what probes evaluate."""

    requested_url: str
    final_url: str
    status: Optional[int]
    headers: dict
    body: str
    error: Optional[str] = None
    content_type: str = ""
    elapsed_ms: Optional[int] = None

    @property
    def ok(self) -> bool:
        return self.error is None and self.status is not None and 200 <= self.status < 300

    @property
    def was_redirected(self) -> bool:
        return self.final_url != self.requested_url

    def evidence_text(self) -> str:
        """Human/machine-readable rendering written to the evidence file."""
        lines = [
            f"REQUESTED: {self.requested_url}",
            f"FINAL:     {self.final_url}",
            f"STATUS:    {self.status}",
            f"ERROR:     {self.error}",
            "HEADERS:",
        ]
        for k in sorted(self.headers):
            lines.append(f"  {k}: {self.headers[k]}")
        lines.append("BODY:")
        lines.append(self.body)
        return "\n".join(lines)


def build_fetched(
    requested_url: str,
    final_url: str,
    status: Optional[int],
    raw_headers: List[Tuple[str, str]],
    raw_bytes: bytes,
    error: Optional[str] = None,
    elapsed_ms: Optional[int] = None,
    max_body_bytes: int = _DEFAULT_MAX_BODY_BYTES,
) -> Fetched:
    """Pure: normalize a raw HTTP response into a Fetched (no network)."""
    headers = {k.lower(): v for k, v in (raw_headers or [])}
    content_type = headers.get("content-type", "").split(";")[0].strip()
    try:
        body = (raw_bytes or b"")[:max_body_bytes].decode("utf-8", errors="replace")
    except Exception:  # pragma: no cover - decode with errors='replace' won't raise
        body = ""
    return Fetched(
        requested_url=requested_url,
        final_url=final_url,
        status=status,
        headers=headers,
        body=body,
        error=error,
        content_type=content_type,
        elapsed_ms=elapsed_ms,
    )


class Fetcher(Protocol):
    def get(self, url: str, accept: Optional[str] = None) -> Fetched: ...


class HttpFetcher:
    """Real network fetcher. Polite, identifiable, retrying on transient errors."""

    def __init__(self, user_agent: str, timeout_seconds: int, max_retries: int,
                 politeness_delay_seconds: float,
                 max_body_bytes: int = _DEFAULT_MAX_BODY_BYTES):
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.politeness_delay_seconds = politeness_delay_seconds
        self.max_body_bytes = max_body_bytes
        self._last_request_at = 0.0

    def _be_polite(self):
        elapsed = time.monotonic() - self._last_request_at
        wait = self.politeness_delay_seconds - elapsed
        if wait > 0:
            time.sleep(wait)
        self._last_request_at = time.monotonic()

    def get(self, url: str, accept: Optional[str] = None) -> Fetched:
        headers = {"User-Agent": self.user_agent}
        if accept:
            headers["Accept"] = accept
        last_error = None
        for attempt in range(self.max_retries + 1):
            self._be_polite()
            req = urllib.request.Request(url, headers=headers, method="GET")
            start = time.monotonic()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    # Read one byte past the cap so build_fetched's slice is a true
                    # bound without pulling an unbounded body into memory.
                    raw = resp.read(self.max_body_bytes + 1)
                    elapsed_ms = int((time.monotonic() - start) * 1000)
                    return build_fetched(
                        requested_url=url,
                        final_url=resp.geturl(),
                        status=resp.status,
                        raw_headers=list(resp.headers.items()),
                        raw_bytes=raw,
                        elapsed_ms=elapsed_ms,
                        max_body_bytes=self.max_body_bytes,
                    )
            except urllib.error.HTTPError as exc:
                # An HTTP error status is a real, scoreable response — not a
                # transport failure. Capture it (with body) and return it.
                raw = b""
                try:
                    raw = exc.read(self.max_body_bytes + 1)
                except Exception:
                    pass
                elapsed_ms = int((time.monotonic() - start) * 1000)
                return build_fetched(
                    requested_url=url,
                    final_url=getattr(exc, "url", url) or url,
                    status=exc.code,
                    raw_headers=list(exc.headers.items()) if exc.headers else [],
                    raw_bytes=raw,
                    elapsed_ms=elapsed_ms,
                    max_body_bytes=self.max_body_bytes,
                )
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = f"{type(exc).__name__}: {exc}"
                continue  # transient: retry
        return build_fetched(
            requested_url=url,
            final_url=url,
            status=None,
            raw_headers=[],
            raw_bytes=b"",
            error=last_error or "unknown fetch error",
        )
