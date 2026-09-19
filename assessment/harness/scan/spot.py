"""What a SPOT cycle is, in one place. **Pure. No network, no files but the payload named.**

`cc_tasks/2026-09-19_spot_scan.md` decisions 1 and 2. A spot cycle is a measurement of one body
(or a few), run on request — a publisher who has fixed something and wants it seen — through the
same controls, legs and rules as a full cycle over the frame. It is a first-class measurement of
its subject and a degraded measurement of nothing: Lighthouse runs one origin, a CIS assessor
scans one host, a Scrapy crawl starts from the URLs it is given. What it must never do is stand
in for the frame's cycle of record, and every rule below exists to make that impossible rather
than unlikely:

* its NAME says it is a spot (`spot_<body>_<YYYY-MM-DD>`, `spot_multi_<YYYY-MM-DD>` for more
  than one body), never `scan_…`, so no reader of a file name, a Result suffix or a shard name
  can take it for a frame cycle;
* its PAYLOAD says so too (`scope: spot`, `spot_targets`), and a name and a payload that
  disagree are refused where they meet (`check_identity`), because either alone can be wrong;
* it is never the report's snapshot (`refuse_as_snapshot`), and it neither supersedes nor is
  superseded by a full cycle's Findings (`scan/publish.py::write_supersession`).

Every reader imports these rather than testing a prefix of its own, for the reason
`model.SYNTHETIC_PREFIXES` is one definition: a second copy of an identity rule is the copy that
drifts.
"""
from __future__ import annotations

import datetime as _dt
import re

#: The name prefix of every spot cycle, and the `scope` value its payload carries.
SPOT_PREFIX = "spot_"
SCOPE = "spot"
#: The name of a spot over more than one body. The bodies are on the payload (`spot_targets`),
#: not in the name, so a three-body spot does not become a file name nobody can type.
MULTI = "multi"

#: `spot_<slug>_<YYYY-MM-DD>` with DD-041's rerun letter allowed after the date
#: (`spot_bea_2026-09-20b`), and a re-judgement's `_rjN` after that — a spot is re-judged under a
#: later rule exactly as a full cycle is, within its own chain.
_NAME_RE = re.compile(r"^spot_(?P<slug>[a-z0-9][a-z0-9.\-]*)_(?P<date>\d{4}-\d{2}-\d{2})"
                      r"(?P<rerun>[a-z]?)(?:_rj\d+)?$")
_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def slug(body: str) -> str:
    """A body's name as it appears in a cycle name: lower case, and nothing a shard name or a
    Result name could not carry. `NAHMSAPHIS` -> `nahmsaphis`, `data.gov` -> `data.gov`."""
    s = re.sub(r"[^a-z0-9.\-]+", "-", str(body).strip().lower()).strip("-")
    if not s:
        raise SystemExit(f"REFUSING: {body!r} has no characters a cycle name can carry")
    return s


def spot_name(bodies, day: str | None = None, rerun: str = "") -> str:
    """The cycle name of a spot over `bodies`, measured on UTC `day` (today by default).

    `rerun` is DD-041's letter for a second spot of the same scope on the same day: the name is
    what every output path, shard and Result suffix keys on, so two measurements under one name
    would be one measurement destroying the other.
    """
    bodies = sorted({str(b) for b in bodies})
    if not bodies:
        raise SystemExit("REFUSING: a spot cycle names at least one body (--target)")
    day = day or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise SystemExit(f"REFUSING: {day!r} is not a YYYY-MM-DD day")
    if rerun and not re.fullmatch(r"[b-z]", rerun):
        raise SystemExit(f"REFUSING: rerun suffix {rerun!r} is not one letter b..z (DD-041)")
    head = slug(bodies[0]) if len(bodies) == 1 else MULTI
    return f"{SPOT_PREFIX}{head}_{day}{rerun}"


def is_spot(cycle: str, payload: dict | None = None) -> bool:
    """True when the NAME or the PAYLOAD says spot. Either is enough to treat it as one; that
    they agree is `check_identity`'s question, not this one's."""
    return str(cycle or "").startswith(SPOT_PREFIX) or bool(
        payload and payload.get("scope") == SCOPE)


def check_identity(cycle: str, payload: dict) -> None:
    """Refuse a payload whose name and scope disagree, in either direction.

    A spot payload named `scan_…` is the failure decision 1 exists to prevent: a measurement of
    one body filed under the name the frame's cycles use, where every glob over `scan_*` and
    every reader of `publication.yaml` would take it for the frame. A `spot_…` name on a payload
    that does not say `scope: spot` is the same disagreement the other way round, and a name
    that does not parse is a spot nobody can date.
    """
    named = str(cycle or "").startswith(SPOT_PREFIX)
    scoped = payload.get("scope") == SCOPE
    if scoped and not named:
        raise SystemExit(
            f"REFUSING: {cycle} carries `scope: spot` (targets {payload.get('spot_targets')}) "
            f"and is not named `{SPOT_PREFIX}…`. A spot cycle is named "
            f"`spot_<body>_<YYYY-MM-DD>` so it can never be read as a cycle over the frame "
            f"(cc_tasks/2026-09-19_spot_scan.md decision 1).")
    if named and not scoped:
        raise SystemExit(
            f"REFUSING: {cycle} is named as a spot cycle and its payload does not carry "
            f"`scope: spot`. A name and a payload that disagree about what was measured are "
            f"refused rather than reconciled.")
    if named and not _NAME_RE.match(cycle):
        raise SystemExit(
            f"REFUSING: {cycle!r} is not `spot_<body>_<YYYY-MM-DD>[letter][_rjN]`; a spot whose "
            f"name does not parse has no date a view can order it by.")
    if scoped and not payload.get("spot_targets"):
        raise SystemExit(f"REFUSING: {cycle} is a spot payload with no `spot_targets`; a spot "
                         f"that does not say which bodies it measured measured nothing citable.")


def refuse_as_snapshot(cycle: str, payload: dict | None = None) -> None:
    """Decision 2: a spot cycle is never the report's snapshot. Called by every builder that
    reads `docs/reports/publication.yaml:snapshot_cycle`."""
    if is_spot(cycle, payload):
        raise SystemExit(
            f"REFUSING: docs/reports/publication.yaml names the spot cycle {cycle!r} as "
            f"`snapshot_cycle`. A spot measures the bodies it names and nothing else; the "
            f"report is a view of the frame, so its snapshot is a full cycle "
            f"(cc_tasks/2026-09-19_spot_scan.md decision 2).")


def measured_on(cycle: str) -> str | None:
    """The UTC day a cycle's evidence was collected, read off its name: `2026-09-10` for
    `scan_2026-09-10_rj4` and for `spot_bea_2026-09-10`. `None` for a name with no day."""
    m = _DATE_RE.search(str(cycle or ""))
    return m.group(1) if m else None
