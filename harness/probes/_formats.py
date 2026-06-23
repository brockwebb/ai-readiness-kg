"""Shared format/barrier heuristics for the distribution probes."""
from __future__ import annotations

# Machine-consumable structured formats (not HTML/PDF presentation layers).
MACHINE_FORMATS = (
    "csv", "tsv", "json", "geojson", "xml", "parquet", "avro", "arrow",
    "application/vnd.api+json", "application/x-ndjson", "text/csv",
)

# Markers that a response is gated against machines.
BARRIER_MARKERS = (
    "g-recaptcha", "recaptcha", "captcha", "are you human", "verify you are human",
    "please sign in", "please log in", "sign in to continue", "enable javascript",
)

SESSION_MARKERS = ("jsessionid", "phpsessid", "/login", "/signin", "/sso", "sessionid=")


def is_machine_format(media_type: str, content_type: str = "") -> bool:
    blob = f"{media_type} {content_type}".lower()
    return any(fmt in blob for fmt in MACHINE_FORMATS)


def has_barrier_markers(body: str) -> bool:
    b = (body or "").lower()
    return any(m in b for m in BARRIER_MARKERS)


def looks_session_gated(url: str) -> bool:
    u = (url or "").lower()
    return any(m in u for m in SESSION_MARKERS)
