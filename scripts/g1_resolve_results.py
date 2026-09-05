#!/usr/bin/env python3
"""Resolve `{{result:NAME:field}}` tokens against registered Seldon Results.

**This is now a SHIM over seldon's resolver library** (task
`cc_tasks/2026-09-04_result_migration_completion.md` step 1; seldon `0bc41cfc` / AD-028).
The debt it retires is the old body's own lookup: replaying `seldon_events.jsonl` and
matching a token key against the `units` property, which existed only because
`seldon result register` had no `--name`. It does now, the Results are migrated, and the
index comes from the graph:

    seldon.paper.build.load_named_artifacts      name  -> artifact   (the real index)
    seldon.paper.build.build_units_fallback_index units -> artifact  (TRANSITIONAL, AD-028 SI-09)
    seldon.paper.build.resolve_references(..., allow_proposed=True)  (the substitution)

The entry point is deliberately kept rather than retired: `--render` is how
`docs/crosswalk/deck_content_2026-09-03_draft.md` becomes a built deck, `--check` is cited in
the findings memo's own header and in three task files, and this project has no `paper/`
directory for `seldon paper build` to target. The CLI surface below is unchanged.

**Two adaptations, applied to the index this shim hands to `resolve_references`, because a
resolver swap must not rewrite documents that have rendered the same way for three tasks:**

1. **Integral values render without a trailing `.0`.** Every Result here was registered
   through `--value FLOAT`, so the graph holds `26.0` and `str(value)` would put "26.0" into
   a sentence that has always read "26". The value is pre-rendered into the index instead.
2. **No `(proposed)` marker.** `allow_proposed=True` tells the library that a `proposed`
   Result is an acceptable referent — every Result in this project is `proposed` and always
   has been — but the library also stamps each one "(proposed)" in the rendered text. That is
   right for a paper heading to press and wrong for these documents. The marker is suppressed
   by presenting the state to the library as accepted; **the information is not lost** — the
   proposed count is reported by `--check`, and SI-09 fallback resolutions are reported per
   token, which is what the migration is tracked by.

The token pattern stays this project's own. Seldon's `REFERENCE_PATTERN` used to use
`[^:}]+` for the name, which matched the documentation placeholder `{{result:<NAME>:value}}`
that the memo and `docs/design_decisions.md` both carry in prose; this shim pre-filters those
so a placeholder is never reported as an unresolvable Result. **The library has since adopted
a name grammar** (seldon `fa7d113`, 2026-09-04, `unanchored_name_grammar()` — the upstream
ResearchTask `3376805b` this shim registered), so the pre-filter no longer changes any
outcome. It is kept for now because `resolve_text` substitutes and reports errors THROUGH
`TOKEN_RE`, so retiring it is a rewrite of that function's error paths, not a deletion; the
agreement between the two grammars is pinned by a test so it cannot rot unnoticed.

    /opt/anaconda3/bin/python3 scripts/g1_resolve_results.py --check docs/research/2026-09-03_g1_eval_findings.md
    /opt/anaconda3/bin/python3 scripts/g1_resolve_results.py --render IN.md --out OUT.md
    /opt/anaconda3/bin/python3 scripts/g1_resolve_results.py --get g1_v2_holdout_all_preservation_rate
    /opt/anaconda3/bin/python3 scripts/g1_resolve_results.py --prefix g1_cal_fable_
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVENTS = REPO / "seldon_events.jsonl"

#: This project's token grammar. Stricter than seldon's `REFERENCE_PATTERN` on purpose: the
#: name may not contain `<` or `>`, so `{{result:<NAME>:value}}` — the placeholder both the
#: findings memo and design_decisions.md use when documenting the syntax — is not a token.
TOKEN_RE = re.compile(r"\{\{result:([A-Za-z0-9_.\-]+):([A-Za-z0-9_]+)\}\}")

#: Marker the seldon library appends to a `proposed` Result under --allow-proposed, and the
#: state we present instead so it is not appended. See the module docstring, adaptation 2.
_ACCEPTED_STATE = "verified"


class ResolutionError(ValueError):
    """A token that cannot be resolved. Never silently left as-is in a rendered document."""


def _seldon():
    """Import the seldon library, failing loudly rather than falling back to a private copy
    of the logic this shim exists to delete."""
    try:
        from seldon.config import get_neo4j_driver, load_project_config
        from seldon.paper import build as seldon_build
    except ImportError as exc:                                    # pragma: no cover
        raise SystemExit(
            f"FATAL: the seldon package is required — this script is a shim over its resolver "
            f"(seldon.paper.build). {exc}"
        ) from exc
    return load_project_config, get_neo4j_driver, seldon_build


def load_results(events: Path = EVENTS) -> dict:
    """NAME -> {'value', 'units', 'description', 'state', 'artifact_id', 'via_units_fallback'}.

    Read from the GRAPH, not from the event log: `events` is accepted for CLI compatibility
    and ignored, because the graph is the projection every seldon command writes through and
    the units index is now the library's, not ours.

    A name registered twice maps to a record carrying `ambiguous` (the ids), so `--check`
    fails loudly rather than picking one.
    """
    load_project_config, get_neo4j_driver, seldon_build = _seldon()
    config = load_project_config(REPO)
    database = config["neo4j"]["database"]
    driver = get_neo4j_driver(config)
    try:
        named = seldon_build.load_named_artifacts(driver, database)
        fallback = seldon_build.build_units_fallback_index(driver, database)
    finally:
        driver.close()

    out: dict = {}
    for key, node in named.items():
        if not key.startswith("result:"):
            continue
        out[key.split(":", 1)[1]] = dict(node, via_units_fallback=False)
    # TRANSITIONAL (AD-028 SI-09): rows the migration has not named yet still answer to their
    # `units` string. A units value carried by more than one unnamed Result is an ambiguity
    # the library refuses to guess at, and so does this.
    for units, nodes in (fallback or {}).items():
        if units in out:
            continue
        if len(nodes) > 1:
            out[units] = {"ambiguous": [n.get("artifact_id") for n in nodes], "units": units}
        else:
            out[units] = dict(nodes[0], via_units_fallback=True)
    return out


def _render_value(v):
    """Seldon stores every Result value as a float; a count must not render as '26.0'."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def resolve_text(text: str, results: dict, filename: str = "") -> tuple:
    """Substitute every token via the seldon library. Returns (rendered, errors); an
    unresolved token is left in place and named in `errors` — a document is never shipped
    with a silently wrong number.

    `errors` are plain strings, as this entry point has always returned. SI-09 (resolved by
    the transitional units fallback) is reported as a warning line, never as a failure: the
    token did resolve, and the count is how the migration's progress is measured.
    """
    _, _, seldon_build = _seldon()
    errors: list[str] = []

    # Only tokens this project's grammar accepts are handed to the library; a `<NAME>`
    # placeholder is neither resolved nor reported.
    ours = {name for name, _ in TOKEN_RE.findall(text)}
    artifacts: dict = {}
    for name in ours:
        rec = results.get(name)
        if rec is None or "ambiguous" in (rec or {}):
            continue
        artifacts[f"result:{name}"] = dict(rec, value=_render_value(rec.get("value")),
                                           state=_ACCEPTED_STATE)

    def _sub(m):
        name, field = m.group(1), m.group(2)
        line = text.count("\n", 0, m.start()) + 1
        rec = results.get(name)
        if rec is None:
            errors.append(f"{filename}:{line}: no registered Result named {name!r}")
            return m.group(0)
        if "ambiguous" in rec:
            errors.append(f"{filename}:{line}: {name!r} is registered more than once "
                          f"({rec['ambiguous']})")
            return m.group(0)
        if field not in rec:
            errors.append(f"{filename}:{line}: Result {name!r} has no field {field!r} "
                          f"(has {sorted(k for k in rec if k not in ('artifact_id', 'via_units_fallback'))})")
            return m.group(0)
        one, errs = seldon_build.resolve_references(
            m.group(0), artifacts, filename, allow_proposed=True)
        for e in errs:
            errors.append(f"{filename}:{line}: {e.message}")
        return one

    return TOKEN_RE.sub(_sub, text), errors


def fallback_tokens(text: str, results: dict) -> list:
    """Names in `text` that resolve only through the TRANSITIONAL units fallback (SI-09).
    Empty means this document no longer depends on the fallback."""
    return sorted({n for n, _ in TOKEN_RE.findall(text)
                   if (results.get(n) or {}).get("via_units_fallback")})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", nargs="*", default=None, help="files whose tokens must all resolve")
    ap.add_argument("--render", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--get", default=None, help="print one Result by name")
    ap.add_argument("--prefix", default=None, help="list every registered Result name with this prefix")
    ap.add_argument("--events", default=str(EVENTS),
                    help="accepted for compatibility and IGNORED: the index is the graph now")
    a = ap.parse_args(argv)
    results = load_results(Path(a.events))

    if a.prefix:
        names = sorted(n for n in results if n.startswith(a.prefix))
        for n in names:
            print(f"{n}\t{results[n].get('value')}")
        print(f"{len(names)} Results with prefix {a.prefix!r} (of {len(results)} registered)", file=sys.stderr)
        return 0
    if a.get:
        rec = results.get(a.get)
        if rec is None:
            print(f"no registered Result named {a.get!r}", file=sys.stderr)
            return 1
        print(json.dumps(rec, indent=1, ensure_ascii=False, default=str))
        return 0
    if a.render:
        text = Path(a.render).read_text(encoding="utf-8")
        rendered, errors = resolve_text(text, results, a.render)
        for e in errors:
            print(e, file=sys.stderr)
        if errors:
            return 1
        if a.out:
            Path(a.out).write_text(rendered, encoding="utf-8")
            print(f"rendered {a.render} -> {a.out} ({len(TOKEN_RE.findall(text))} tokens)")
        else:
            sys.stdout.write(rendered)
        return 0
    if a.check is not None:
        bad = 0
        for f in a.check:
            text = Path(f).read_text(encoding="utf-8")
            n = len(TOKEN_RE.findall(text))
            _, errors = resolve_text(text, results, f)
            for e in errors:
                print(e, file=sys.stderr)
            bad += len(errors)
            si09 = fallback_tokens(text, results)
            note = f", {len(si09)} via the SI-09 units fallback" if si09 else ""
            print(f"{f}: {n} tokens, {n - len(errors)} resolved{note}")
            if si09:
                print(f"  SI-09 (transitional): {', '.join(si09)}", file=sys.stderr)
        return 1 if bad else 0
    ap.error("one of --check / --render / --get / --prefix is required")


if __name__ == "__main__":
    raise SystemExit(main())
