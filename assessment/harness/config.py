"""Configuration loading (read-only, stdlib tomllib — zero runtime dependency).

All tunable values (HTTP behavior, evidence location, track dating, agency URLs)
live in config/*.toml, never in source (Engineering Standards §2). A missing or
malformed config file fails loud and early, naming the file (§4); it never falls
through to a silent default.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import List


class ConfigError(Exception):
    """Raised when configuration is missing or malformed. Carries the offending
    path so the operator sees exactly what to fix."""


def _read_toml(path: Path) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"config file not found: {path}")
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"malformed TOML in {path}: {exc}") from exc


@dataclass(frozen=True)
class HarnessConfig:
    user_agent: str
    timeout_seconds: int
    max_retries: int
    politeness_delay_seconds: float
    max_body_bytes: int
    evidence_root: str
    max_evidence_bytes: int
    # Web-surface (sitemap) enumeration sampling. Seeded and recorded so the
    # same seed redraws the same pages.
    sitemap_sample_per_section: int
    sitemap_max_sections: int
    sitemap_sample_seed: int
    # Fetches per target for d2_no_barriers. > 1 measures refusal intermittency.
    no_barriers_attempts: int
    # track label -> as_of_date string
    _track_as_of: dict

    def track_as_of_date(self, track_label: str) -> str:
        if track_label not in self._track_as_of:
            raise ConfigError(f"no track '{track_label}' defined in harness config")
        return self._track_as_of[track_label]


def _require(d: dict, key: str, where: str):
    if key not in d:
        raise ConfigError(f"missing required key '{key}' in {where}")
    return d[key]


def load_harness_config(path: Path) -> HarnessConfig:
    data = _read_toml(path)
    http = _require(data, "http", str(path))
    evidence = _require(data, "evidence", str(path))
    tracks = _require(data, "tracks", str(path))
    sitemap = _require(data, "sitemap", str(path))
    probes = _require(data, "probes", str(path))
    no_barriers = _require(probes, "d2_no_barriers", "harness.toml [probes]")

    attempts = _require(no_barriers, "attempts", "harness.toml [probes.d2_no_barriers]")
    if not isinstance(attempts, int) or attempts < 1:
        raise ConfigError(
            f"[probes.d2_no_barriers] attempts must be an integer >= 1 in {path}; "
            f"got {attempts!r}"
        )
    per_section = _require(sitemap, "sample_per_section", "harness.toml [sitemap]")
    if not isinstance(per_section, int) or per_section < 1:
        raise ConfigError(
            f"[sitemap] sample_per_section must be an integer >= 1 in {path}; "
            f"got {per_section!r}"
        )

    track_as_of = {}
    for label, spec in tracks.items():
        track_as_of[label] = spec.get("as_of_date", "")

    return HarnessConfig(
        user_agent=_require(http, "user_agent", "harness.toml [http]"),
        timeout_seconds=_require(http, "timeout_seconds", "harness.toml [http]"),
        max_retries=_require(http, "max_retries", "harness.toml [http]"),
        politeness_delay_seconds=_require(
            http, "politeness_delay_seconds", "harness.toml [http]"
        ),
        max_body_bytes=_require(http, "max_body_bytes", "harness.toml [http]"),
        evidence_root=_require(evidence, "root_dir", "harness.toml [evidence]"),
        max_evidence_bytes=_require(
            evidence, "max_evidence_bytes", "harness.toml [evidence]"
        ),
        sitemap_sample_per_section=per_section,
        sitemap_max_sections=_require(sitemap, "max_sections", "harness.toml [sitemap]"),
        sitemap_sample_seed=_require(sitemap, "sample_seed", "harness.toml [sitemap]"),
        no_barriers_attempts=attempts,
        _track_as_of=track_as_of,
    )


def load_agencies(path: Path) -> List[dict]:
    data = _read_toml(path)
    agencies = data.get("agency", [])
    if not agencies:
        raise ConfigError(f"no [[agency]] entries found in {path}")
    required = ("id", "name", "base_url")
    for a in agencies:
        for key in required:
            if key not in a:
                raise ConfigError(
                    f"agency entry missing required key '{key}' in {path}: {a}"
                )
    return agencies
