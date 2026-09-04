#!/usr/bin/env python3
"""Resolve `{{result:NAME:field}}` tokens against registered Seldon Results (task
2026-09-03_g1_freeze_calibration_redefinition_findings, steps 3 and 4). **Zero model calls.**
Stdlib only.

Why this file exists instead of `seldon paper build`. The engineering standard (§13) says
research numbers are written as `{{result:NAME:value}}` and resolved from the graph. Seldon's
own resolver (`seldon/paper/build.py: load_named_artifacts`) matches on an artifact's `name`
property and runs inside a `paper/` project. This repo has no `paper/` directory, and the G1
Results carry their name in the `units` property — `scripts/register_g1_v2_results.py` passes
the Result name as `--units` and puts the derivation path in `--description`, because Seldon's
`result register` has no `--name`. So the lookup path used here is:

    seldon_events.jsonl  ->  artifact_created / artifact_updated / artifact_state_changed
                         ->  Result artifacts  ->  properties.units == NAME  ->  properties.<field>

The event log is the registry's source of truth (a Seldon graph is a replay of it), so this
reads the same facts `seldon result list` would, without a database. Ambiguity is fatal: if two
Results share a name, nothing here guesses which one a document meant.

    /opt/anaconda3/bin/python3 scripts/g1_resolve_results.py --check docs/research/2026-09-03_g1_eval_findings.md
    /opt/anaconda3/bin/python3 scripts/g1_resolve_results.py --render IN.md --out OUT.md
    /opt/anaconda3/bin/python3 scripts/g1_resolve_results.py --get g1_v2_holdout_all_preservation_rate
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVENTS = REPO / "seldon_events.jsonl"
TOKEN_RE = re.compile(r"\{\{result:([A-Za-z0-9_.\-]+):([A-Za-z0-9_]+)\}\}")


class ResolutionError(ValueError):
    """A token that cannot be resolved. Never silently left as-is in a rendered document."""


def load_results(events: Path = EVENTS) -> dict:
    """NAME -> {'value', 'units', 'description', 'state', 'artifact_id'} by replaying the log.

    A name registered twice maps to the string 'AMBIGUOUS' plus the ids, so `--check` fails
    loudly rather than picking one.
    """
    by_id: dict = {}
    for line in events.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        ev = json.loads(line)
        p = ev.get("payload") or {}
        aid = p.get("artifact_id")
        if not aid:
            continue
        if ev["event_type"] == "artifact_created":
            if p.get("artifact_type") != "Result":
                continue
            by_id[aid] = {"artifact_id": aid, "state": p.get("to_state"), **(p.get("properties") or {})}
        elif aid in by_id:
            if ev["event_type"] == "artifact_updated":
                by_id[aid].update(p.get("properties") or {})
            elif ev["event_type"] == "artifact_state_changed":
                by_id[aid]["state"] = p.get("to_state", by_id[aid].get("state"))
    out: dict = {}
    for rec in by_id.values():
        name = rec.get("units")
        if not name:
            continue
        prev = out.get(name)
        if prev is None:
            out[name] = rec
        elif "ambiguous" in prev:
            prev["ambiguous"].append(rec["artifact_id"])
        elif prev["artifact_id"] != rec["artifact_id"]:
            out[name] = {"ambiguous": [prev["artifact_id"], rec["artifact_id"]], "units": name}
    return out


def resolve_text(text: str, results: dict, filename: str = "") -> tuple:
    """Substitute every token. Returns (rendered, errors); an unresolved token is left in place
    and named in `errors` — a document is never shipped with a silently wrong number."""
    errors = []

    def _sub(m):
        name, field = m.group(1), m.group(2)
        line = text.count("\n", 0, m.start()) + 1
        rec = results.get(name)
        if rec is None:
            errors.append(f"{filename}:{line}: no registered Result named {name!r}")
            return m.group(0)
        if "ambiguous" in rec:
            errors.append(f"{filename}:{line}: {name!r} is registered more than once ({rec['ambiguous']})")
            return m.group(0)
        if field not in rec:
            errors.append(f"{filename}:{line}: Result {name!r} has no field {field!r} "
                          f"(has {sorted(k for k in rec if k != 'artifact_id')})")
            return m.group(0)
        v = rec[field]
        # Seldon stores every Result value as a float; a count must not render as "26.0".
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)

    return TOKEN_RE.sub(_sub, text), errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", nargs="*", default=None, help="files whose tokens must all resolve")
    ap.add_argument("--render", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--get", default=None, help="print one Result by name")
    ap.add_argument("--prefix", default=None, help="list every registered Result name with this prefix")
    ap.add_argument("--events", default=str(EVENTS))
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
        print(json.dumps(rec, indent=1, ensure_ascii=False))
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
            print(f"{f}: {n} tokens, {n - len(errors)} resolved")
        return 1 if bad else 0
    ap.error("one of --check / --render / --get / --prefix is required")


if __name__ == "__main__":
    raise SystemExit(main())
