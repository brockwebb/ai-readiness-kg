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
    # confidence level (as a string key, e.g. "0.90") -> z factor (harness.toml [g1.z_by_level])
    g1_z_by_level: dict
    # qualifier families (harness.toml [g1.families], design D9) — checked against records.FAMILIES
    g1_families: dict
    # D10 binding window: {window_chars, label_min_tokens, label_stop_words}
    g1_binding: dict
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
    z_tbl = _require(g1, "z_by_level", "harness.toml [g1]")
    if not isinstance(z_tbl, dict) or not z_tbl:
        raise ConfigError(f"[g1.z_by_level] must be a non-empty table of level -> z in {path}")
    g1_z = {}
    for k, v in z_tbl.items():
        try:
            lvl = float(k)
        except ValueError as exc:
            raise ConfigError(f"[g1.z_by_level] key {k!r} is not a confidence level in {path}") from exc
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            raise ConfigError(f"[g1.z_by_level] {k} must be a positive number in {path}; got {v!r}")
        g1_z[round(lvl, 4)] = float(v)
    fam_tbl = _require(g1, "families", "harness.toml [g1]")
    if not isinstance(fam_tbl, dict) or not fam_tbl:
        raise ConfigError(f"[g1.families] must be a non-empty table family -> [classes] in {path}")
    from .records import FAMILIES as _FAMILIES  # the code-side table the config must agree with
    g1_families = {}
    for fam, classes in fam_tbl.items():
        if not isinstance(classes, list) or not classes or not all(isinstance(c, str) for c in classes):
            raise ConfigError(f"[g1.families] {fam} must be a non-empty list of class names in {path}")
        g1_families[str(fam)] = tuple(classes)
    if {k: tuple(v) for k, v in g1_families.items()} != {k: tuple(v) for k, v in _FAMILIES.items()}:
        raise ConfigError(f"[g1.families] in {path} disagrees with harness.records.FAMILIES: "
                          f"{g1_families} vs {_FAMILIES}")
    bind = _require(g1, "binding", "harness.toml [g1]")
    if not isinstance(bind, dict):
        raise ConfigError(f"[g1.binding] must be a table in {path}")
    wc = bind.get("window_chars")
    lm = bind.get("label_min_tokens")
    sw = bind.get("label_stop_words")
    if not isinstance(wc, int) or isinstance(wc, bool) or wc < 1:
        raise ConfigError(f"[g1.binding] window_chars must be a positive integer in {path}; got {wc!r}")
    if not isinstance(lm, int) or isinstance(lm, bool) or lm < 1:
        raise ConfigError(f"[g1.binding] label_min_tokens must be a positive integer in {path}; got {lm!r}")
    if not isinstance(sw, list) or not all(isinstance(x, str) for x in sw):
        raise ConfigError(f"[g1.binding] label_stop_words must be a list of strings in {path}")
    g1_binding = {"window_chars": wc, "label_min_tokens": lm, "label_stop_words": tuple(w.lower() for w in sw)}
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
        g1_z_by_level=g1_z,
        g1_families=g1_families,
        g1_binding=g1_binding,
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
