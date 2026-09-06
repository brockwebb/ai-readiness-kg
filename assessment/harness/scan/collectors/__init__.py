"""Collectors: they OBSERVE and never judge. **No model client is importable from here** —
a test asserts it, because the AUTO tier's zero-model-spend is a design property of the
harness, not a habit of its operators.

Every collector returns `list[Observation]` and every numeric constant it uses comes from
`params.yaml` (§2.3) — a test greps this package for integer literals outside an allowlist of
HTTP status codes.
"""
from __future__ import annotations

from . import dcat, http, lighthouse, robots, sitemap, structured_data  # noqa: F401

REGISTRY = {
    "http": http, "robots": robots, "sitemap": sitemap,
    "structured_data": structured_data, "dcat": dcat, "lighthouse": lighthouse,
}
