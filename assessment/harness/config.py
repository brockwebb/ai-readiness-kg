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
    # d1_sitemap non-stale condition: newest lastmod older than this is PARTIAL.
    sitemap_stale_after_days: int
    # d1_robots_directives: which <meta name> values are robots directives, and
    # which directives withdraw a page from discovery.
    robots_directive_meta_names: tuple
    robots_blocking_directives: tuple
    # crawler-access triad: tokens whose robots.txt eligibility is evaluated,
    # extra identities the harness may send, and observed-leg refusal statuses.
    crawler_declared_user_agents: tuple
    crawler_observe_user_agents: tuple
    crawler_refusal_statuses: tuple
    # G1 declared leg (harness.toml [g1]): field-name pattern tables, each a tuple of
    # dicts {id, regex, class?, pairs_with?} validated at load.
    g1_uncertainty_field_patterns: tuple
    g1_footnote_field_patterns: tuple
    g1_id_field_patterns: tuple
    g1_footnote_uncertainty_vocabulary: tuple
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


def _string_list(d: dict, key: str, where: str, path) -> List[str]:
    """A required list-of-strings key (may be empty). Anything else fails loud."""
    value = _require(d, key, where)
    if not isinstance(value, list) or any(not isinstance(v, str) for v in value):
        raise ConfigError(f"{where} {key} must be a list of strings in {path}; "
                          f"got {value!r}")
    return value


def _pattern_table(d: dict, key: str, where: str, path, require_class: bool) -> tuple:
    """A required list of {id, regex[, class, pairs_with]} tables. Every regex must
    compile at load (a bad pattern is a config defect, not a runtime surprise)."""
    import re as _re
    value = _require(d, key, where)
    if not isinstance(value, list) or not value:
        raise ConfigError(f"{where} {key} must be a non-empty list of tables in {path}")
    out = []
    seen = set()
    for row in value:
        if not isinstance(row, dict) or not row.get("id") or not row.get("regex"):
            raise ConfigError(f"{where} {key}: every entry needs 'id' and 'regex' in {path}; got {row!r}")
        if row["id"] in seen:
            raise ConfigError(f"{where} {key}: duplicate pattern id {row['id']!r} in {path}")
        seen.add(row["id"])
        try:
            _re.compile(row["regex"])
        except _re.error as exc:
            raise ConfigError(f"{where} {key}: pattern {row['id']!r} does not compile: {exc}") from exc
        if require_class and not row.get("class"):
            raise ConfigError(f"{where} {key}: pattern {row['id']!r} needs a 'class' in {path}")
        out.append(dict(row))
    return tuple(out)


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
    sitemap_probe = _require(probes, "d1_sitemap", "harness.toml [probes]")
    stale_days = _require(sitemap_probe, "stale_after_days",
                          "harness.toml [probes.d1_sitemap]")
    if isinstance(stale_days, bool) or not isinstance(stale_days, int) or stale_days < 1:
        raise ConfigError(
            f"[probes.d1_sitemap] stale_after_days must be an integer >= 1 in {path}; "
            f"got {stale_days!r}"
        )
    directives = _require(probes, "d1_robots_directives", "harness.toml [probes]")
    meta_names = _string_list(directives, "directive_meta_names",
                              "harness.toml [probes.d1_robots_directives]", path)
    blocking = _string_list(directives, "discovery_blocking_directives",
                            "harness.toml [probes.d1_robots_directives]", path)
    if not blocking:
        raise ConfigError(
            f"[probes.d1_robots_directives] discovery_blocking_directives must name "
            f"at least one directive in {path}"
        )
    access = _require(probes, "crawler_access", "harness.toml [probes]")
    declared_uas = _string_list(access, "declared_user_agents",
                                "harness.toml [probes.crawler_access]", path)
    observe_uas = _string_list(access, "observe_user_agents",
                               "harness.toml [probes.crawler_access]", path)
    refusal = _require(access, "refusal_statuses", "harness.toml [probes.crawler_access]")
    if (not isinstance(refusal, list) or not refusal
            or any(isinstance(s, bool) or not isinstance(s, int) for s in refusal)):
        raise ConfigError(
            f"[probes.crawler_access] refusal_statuses must be a non-empty list of "
            f"integers in {path}; got {refusal!r}"
        )
    g1 = _require(data, "g1", str(path))
    g1_unc = _pattern_table(g1, "uncertainty_field_patterns", "harness.toml [g1]", path, True)
    g1_fn = _pattern_table(g1, "footnote_field_patterns", "harness.toml [g1]", path, False)
    g1_id = _pattern_table(g1, "id_field_patterns", "harness.toml [g1]", path, False)
    g1_vocab = _string_list(g1, "footnote_uncertainty_vocabulary", "harness.toml [g1]", path)
    if not g1_vocab:
        raise ConfigError(f"[g1] footnote_uncertainty_vocabulary must not be empty in {path}")
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
        sitemap_stale_after_days=stale_days,
        robots_directive_meta_names=tuple(meta_names),
        robots_blocking_directives=tuple(blocking),
        crawler_declared_user_agents=tuple(declared_uas),
        crawler_observe_user_agents=tuple(observe_uas),
        crawler_refusal_statuses=tuple(refusal),
        g1_uncertainty_field_patterns=g1_unc,
        g1_footnote_field_patterns=g1_fn,
        g1_id_field_patterns=g1_id,
        g1_footnote_uncertainty_vocabulary=tuple(g1_vocab),
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
        hook = a.get("enforced_observations_file")
        if hook is not None:
            if not isinstance(hook, str) or not hook.strip():
                raise ConfigError(
                    f"agency {a['id']!r}: enforced_observations_file must be a "
                    f"non-empty path string in {path}; got {hook!r}"
                )
            # Relative to the config directory, so the hook travels with config.
            a["enforced_observations_file"] = str(
                (Path(path).parent / hook).resolve()
            )
    return agencies
