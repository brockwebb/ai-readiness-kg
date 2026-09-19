#!/usr/bin/env python3
"""Render `cc_tasks/templates/spot_scan.md` for one body. **Zero spend, no network.**

`cc_tasks/2026-09-19_spot_scan.md` decision 4. `seldon cadence render` does not exist (Seldon
issue `2026-09-18_cadence_render_on_request`), and when it does it will substitute its four
fields and refuse any other; a spot template needs two more — the body, and the body's hosts for
the `**Network:**` allowlist. So this renders the four through Seldon's own
`seldon.core.cadence.render`, exactly as `cc_tasks/2026-09-18_cadence_off_RESULT.md` §1 does for
the frame's template, and then the two spot fields, each from the one place it is decided:

* `{target}` — the frame's own spelling of the body (`run.canonical_bodies`), so `bea` renders
  as `BEA` and names the cycle `run.py --target` will name;
* `{network_hosts}` — the netlocs of that body's rows on the target list `params.cycle.targets`
  binds today, plus `127.0.0.1` for the control fixtures: the dispatcher's allowlist grammar
  (exact hostnames, comma-separated; DN-006 ADDENDUM_05).

    /opt/anaconda3/bin/python3 scripts/render_spot_scan.py --target BEA          # print it
    /opt/anaconda3/bin/python3 scripts/render_spot_scan.py --target BEA --write  # cc_tasks/<stem>.md
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

TEMPLATE = REPO / "cc_tasks" / "templates" / "spot_scan.md"
#: The template's name as a cadence entry would carry it: the instance stem is
#: `<date>_spot_scan_<body>` and cannot collide with a frame cycle's `<date>_scan_cycle_<date>`.
ENTRY_NAME = "spot_scan"
#: The control fixtures' host. Every cycle, spot or frame, runs them first.
LOOPBACK = "127.0.0.1"
_SPOT_FIELDS = re.compile(r"\{(target|network_hosts)\}")


def body_hosts(params: dict, body: str) -> list:
    """The netlocs the spot of `body` will ask anything of, in first-seen order: each row's
    `host` and the netloc of its URL, then the loopback."""
    from scan import run
    doc = json.loads((run.STATE_DIR / f"{params['cycle']['targets']}.json").read_text(
        encoding="utf-8"))
    hosts: list = []
    for r in run.rows_of_bodies(doc["rows"], [body]):
        for h in (r.get("host"), urllib.parse.urlsplit(r.get("url") or "").netloc):
            if h and h.lower() not in hosts:
                hosts.append(h.lower())
    return hosts + [LOOPBACK]


def render(target: str, now: dt.datetime | None = None) -> tuple:
    """`(text, instance_stem)` for a spot of `target`, as of `now` (UTC)."""
    from seldon.core import cadence as C
    from scan import load_params, run, spot
    params = load_params()
    now = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
    [body] = run.canonical_bodies(params, [target])
    day = now.strftime("%Y-%m-%d")
    stem = C.instance_stem({"name": ENTRY_NAME}, spot.slug(body), now)
    text = C.render(TEMPLATE.read_text(encoding="utf-8"),
                    cycle_name=spot.spot_name([body], day), period=day,
                    cadence_name=ENTRY_NAME, created_at=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    instance_stem=stem)
    values = {"target": body, "network_hosts": ", ".join(body_hosts(params, body))}
    return _SPOT_FIELDS.sub(lambda m: values[m.group(1)], text), stem


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", required=True, metavar="BODY")
    ap.add_argument("--write", action="store_true",
                    help="write cc_tasks/<stem>.md and print its path; refuses to overwrite")
    a = ap.parse_args(argv)
    text, stem = render(a.target)
    if not a.write:
        print(text, end="")
        return 0
    path = REPO / "cc_tasks" / f"{stem}.md"
    if path.exists():
        raise SystemExit(f"REFUSING: {path.relative_to(REPO)} exists; a spot of this body was "
                         f"already rendered today")
    path.write_text(text, encoding="utf-8")
    print(path.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
