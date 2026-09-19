"""Scanning a site that is not this project's: frames, identity, and where the results go.

`cc_tasks/2026-09-19_adopter_path.md` decisions 1, 3 and 4. **Pure except for the files it is
asked to read or write. No network.** `run.py --frame` is the one caller that measures anything.

**A frame file is the unit of adoption.** A publisher who wants to know where their own site
stands writes one YAML file naming each body, its home page and its flagship pages, and runs
`make scan-now FRAME=<file>`. Nothing else in this repository has to change: the controls, the
legs, the rules, the manners and the rate limits are the ones every cycle here runs under, and
the frame is compiled into exactly the row shape `run.targets` already reads (the v2 target
DataFile, `cc_tasks/2026-09-08_scan_run_3b.md`). One body is the normal case:

    frame: my-site
    bodies:
      - name: MYSITE
        home: https://www.example.gov/
        flagships:
          - https://www.example.gov/data/product-one

**Where a run's results go** (decision 4). Everything an adopter run writes is under
`out/<frame>/`, in the same shape as this project's own tree so the same readers work on it:

    out/<frame>/state/<cycle>.json            the payload: every Observation and Finding
    out/<frame>/state/<targets>.json          the frame as compiled for that run
    out/<frame>/evidence/<cycle>/             every response body the run retained, by sha256
    out/<frame>/reports/scan_matrix_*.json|csv  the matrices (`scripts/render_run_report.py`)
    out/<frame>/reports/publication.yaml      which run is the frame's cycle of record
    out/<frame>/report/<cycle>.md             the rendered report
    out/<frame>/LATEST                        the name of the last run

Nothing is written to `state/`, `corpus/`, `events/` or `docs/reports/`: an adopter's run is
theirs, and this project's record is this project's.

**Parameters.** An adopter run is measured under the committed `params.yaml` with its cycle
IDENTITY overlaid in memory, which is `scripts/run_self_scan.py`'s method (the self row, 2026-09-13)
and for the same reason: the instrument must be the same instrument. The overlay's `targets`
name carries the frame file's sha256, so `params_hash` moves when the frame's content does — "a
measurement of a different set of surfaces is a different measurement" (`params.cycle`).
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import ipaddress
import json
import re
import urllib.parse
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[1]
FRAMES = Path(__file__).resolve().parent / "frames"
#: This project's own frame (decision 1). Its `user_agent` is the identity refused to anyone
#: else's frame against a non-loopback host (decision 3).
PROJECT_FRAME = FRAMES / "fss16.yaml"

#: The two frame kinds. `declared` is an adopter's; `target_datafile` is this project's, which
#: refers to a registered DataFile rather than listing its rows (`frames/fss16.yaml`).
DECLARED, DATAFILE = "declared", "target_datafile"
#: Tiers a declared body may take. `A` gets the framework set, `C` the tier-0 legs only
#: (DD-059), exactly as the rows of this project's frame do.
TIERS = ("A", "C")
#: Keys a declared body may carry. Anything else is refused rather than ignored: a key the
#: harness does not read is a setting the author believes is in force and is not.
BODY_KEYS = {"name", "home", "flagships", "tier"}
FRAME_KEYS = {"frame", "kind", "bodies", "note"}

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9.\-]*$")
#: A contact a host operator can use, which RFC 9309 practice and DD-060 both expect a crawler's
#: identity to carry: a URL, or an address.
_CONTACT_RE = re.compile(r"(https?://\S+|mailto:\S+|[^\s@()]+@[^\s@()]+\.[^\s@()]+)")


# ------------------------------------------------------------------ frames

def load_frame(path: Path) -> dict:
    """The frame file at `path`, validated. Refuses, naming the defect, anything it cannot run.

    Returns the parsed document plus `_path` and `_sha256` (of the file's bytes), which is what
    names the compiled targets and so what `params_hash` sees.
    """
    import yaml
    path = Path(path)
    if not path.is_file():
        raise SystemExit(f"REFUSING: frame file {path} does not exist")
    raw = path.read_bytes()
    doc = yaml.safe_load(raw.decode("utf-8"))
    if not isinstance(doc, dict):
        raise SystemExit(f"REFUSING: {path} is not a YAML mapping; a frame names `frame:` and "
                         f"`bodies:` (docs/adopt/run_on_your_site.md)")
    kind = doc.get("kind", DECLARED)
    if kind == DATAFILE:
        return {**doc, "kind": kind, "_path": str(path),
                "_sha256": hashlib.sha256(raw).hexdigest()}
    if kind != DECLARED:
        raise SystemExit(f"REFUSING: {path} has kind {kind!r}; a frame is `{DECLARED}` (yours) "
                         f"or `{DATAFILE}` (this project's)")
    extra = sorted(set(doc) - FRAME_KEYS)
    if extra:
        raise SystemExit(f"REFUSING: {path} carries keys the harness does not read: {extra}. "
                         f"A frame has {sorted(FRAME_KEYS)}.")
    name = str(doc.get("frame") or "")
    if not _SLUG_RE.match(name):
        raise SystemExit(f"REFUSING: {path} `frame: {name!r}` must be lower case letters, "
                         f"digits, `.` and `-`: it names the output directory and every cycle")
    bodies = doc.get("bodies")
    if not isinstance(bodies, list) or not bodies:
        raise SystemExit(f"REFUSING: {path} names no bodies; a frame measures at least one")
    seen_names, seen_hosts = set(), {}
    for i, b in enumerate(bodies):
        where = f"{path} bodies[{i}]"
        if not isinstance(b, dict):
            raise SystemExit(f"REFUSING: {where} is not a mapping with `name` and `home`")
        extra = sorted(set(b) - BODY_KEYS)
        if extra:
            raise SystemExit(f"REFUSING: {where} carries keys the harness does not read: "
                             f"{extra}. A body has {sorted(BODY_KEYS)}.")
        bname = str(b.get("name") or "").strip()
        if not bname:
            raise SystemExit(f"REFUSING: {where} has no `name`")
        if bname.casefold() in seen_names:
            raise SystemExit(f"REFUSING: {where} repeats the body name {bname!r}")
        seen_names.add(bname.casefold())
        home = _url(b.get("home"), f"{where}.home")
        netloc = urllib.parse.urlsplit(home).netloc.lower()
        if netloc in seen_hosts:
            # One body per host, because the host surfaces are keyed on the host
            # (`home:<netloc>`, `host:<netloc>`), and two bodies on one host would be one
            # well-known set judged twice under two names.
            raise SystemExit(f"REFUSING: {where} shares host {netloc} with "
                             f"{seen_hosts[netloc]!r}; a frame holds one body per host")
        seen_hosts[netloc] = bname
        for j, f in enumerate(b.get("flagships") or []):
            _url(f, f"{where}.flagships[{j}]")
        if str(b.get("tier", "A")) not in TIERS:
            raise SystemExit(f"REFUSING: {where} tier {b.get('tier')!r} is not one of {TIERS}")
    return {**doc, "kind": kind, "_path": str(path),
            "_sha256": hashlib.sha256(raw).hexdigest()}


def _url(value, where: str) -> str:
    u = str(value or "").strip()
    parts = urllib.parse.urlsplit(u)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        raise SystemExit(f"REFUSING: {where} {value!r} is not an absolute http(s) URL")
    return u


def targets_name(frame: dict) -> str:
    """The compiled frame's name: the frame and the first twelve hex of its file's sha256. It
    is what `params.cycle.targets` is overlaid with, so it is what `params_hash` covers."""
    return f"frame_{frame['frame']}_{frame['_sha256'][:12]}"


def compile_rows(frame: dict) -> dict:
    """The frame as a v2 target DataFile: one `home:`, one `host:` (the well-known set) and one
    `flagship:` row per declared page, per body. Every doc id is synthetic
    (`model.SYNTHETIC_PREFIXES`), so no row needs a corpus admission — an adopter's pages are
    not this project's corpus and never will be."""
    rows = []
    for b in frame["bodies"]:
        home = b["home"].strip()
        parts = urllib.parse.urlsplit(home)
        netloc = parts.netloc.lower()
        base = {"agency": b["name"].strip(), "agency_name": b["name"].strip(),
                "tier": str(b.get("tier", "A")), "host": netloc}
        rows.append({**base, "surface_kind": "well_known",
                     "url": f"{parts.scheme}://{netloc}/robots.txt",
                     "doc_id": f"host:{netloc}",
                     "selected_as": "the host's well-known set (synthetic surface)",
                     "selection_source": f"{frame['_path']}: home"})
        rows.append({**base, "surface_kind": "home", "url": home, "doc_id": f"home:{netloc}",
                     "selected_as": "home", "selection_source": f"{frame['_path']}: home"})
        for f in b.get("flagships") or []:
            fp = urllib.parse.urlsplit(f.strip())
            tail = fp.path or "/"
            if fp.query:
                tail += f"?{fp.query}"
            rows.append({**base, "surface_kind": "flagship", "url": f.strip(),
                         "doc_id": f"flagship:{fp.netloc.lower()}{tail}",
                         "selected_as": "flagship", "selection_source":
                         f"{frame['_path']}: flagships"})
    ids = [r["doc_id"] for r in rows]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise SystemExit(f"REFUSING: the frame declares one surface twice: {dup}")
    return {"frame": frame["frame"], "kind": DECLARED, "frame_path": frame["_path"],
            "frame_sha256": frame["_sha256"], "rows": rows,
            "note": ("Compiled from an adopter's frame by assessment/harness/scan/adopt.py "
                     "(cc_tasks/2026-09-19_adopter_path.md decision 1). Every doc id is "
                     "synthetic; nothing here is this project's corpus.")}


def check_project_frame(frame: dict, params: dict) -> None:
    """This project's frame agrees with the parameters that measure it. Called by the test that
    holds `frames/fss16.yaml` to `params.yaml`, and by `run.py` when it is handed the file."""
    if frame.get("targets") != params["cycle"]["targets"]:
        raise SystemExit(f"REFUSING: {frame['_path']} names targets {frame.get('targets')!r} "
                         f"and params.cycle.targets is {params['cycle']['targets']!r}")


# ------------------------------------------------------------------ identity (decision 3)

def is_loopback(netloc: str) -> bool:
    host = urllib.parse.urlsplit(f"//{netloc}").hostname or ""
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def product_token(ua: str) -> str:
    """`ai-readiness-kg-scanner` of `ai-readiness-kg-scanner/0.2 (+https://...)`: the name an
    operator reading a log would take the client for (RFC 9110 §10.1.5, `product`)."""
    return str(ua or "").strip().split("/", 1)[0].split(" ", 1)[0].casefold()


def check_identity(params: dict, rows: list, project_frame: Path | None = None) -> None:
    """Refuse to scan a non-loopback host in someone else's frame as this project, or as nobody.

    DD-060 holds for every scan, whoever runs it: ONE identity, with a contact a host operator
    can reach. For an adopter that identity is THEIRS. A run that goes out as
    `ai-readiness-kg-scanner` puts this project's name and contact in the target's logs for a
    measurement this project did not make, and a run with no contact leaves the operator no one
    to ask. Loopback is exempt: nothing outside the machine sees the header, and the controls
    and the runbook's own exercise run there.
    """
    import yaml
    outside = sorted({r["host"] for r in rows if not is_loopback(r["host"])})
    if not outside:
        return
    ua = str(params["manners"].get("user_agent") or "")
    ours = yaml.safe_load(Path(project_frame or PROJECT_FRAME).read_text(
        encoding="utf-8"))["user_agent"]
    if product_token(ua) == product_token(ours):
        raise SystemExit(
            f"REFUSING: params.yaml manners.user_agent is this project's identity ({ua!r}) and "
            f"this frame reaches {', '.join(outside)}. Set it to your own: a product name and a "
            f"contact a host operator can reach, e.g. "
            f"\"my-org-readiness-scan/1.0 (+mailto:webmaster@example.org)\" "
            f"(DD-060; docs/adopt/run_on_your_site.md step 2).")
    if not _CONTACT_RE.search(ua):
        raise SystemExit(
            f"REFUSING: params.yaml manners.user_agent {ua!r} carries no contact. A host "
            f"operator reading their logs must be able to reach whoever is scanning them: add a "
            f"URL or an address (DD-060; docs/adopt/run_on_your_site.md step 2).")


# ------------------------------------------------------------------ names and places

def cycle_name(frame: dict, day: str | None = None, rerun: str = "") -> str:
    """`scan_<frame>_<YYYY-MM-DD>[letter]`. The frame is IN the name so an adopter's cycle can
    never be read as one of this project's (`scan_<YYYY-MM-DD>`), and the day is where every
    reader of a cycle name looks for it (`spot.measured_on`)."""
    day = day or _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d")
    if rerun and not re.fullmatch(r"[b-z]", rerun):
        raise SystemExit(f"REFUSING: rerun suffix {rerun!r} is not one letter b..z (DD-041)")
    return f"scan_{frame['frame']}_{day}{rerun}"


def frame_dir(out_root: Path, frame_slug: str) -> Path:
    return Path(out_root) / frame_slug


def layout(out_root: Path, frame_slug: str) -> dict:
    d = frame_dir(out_root, frame_slug)
    return {"root": d, "state": d / "state", "evidence": d / "evidence",
            "reports": d / "reports", "report": d / "report", "latest": d / "LATEST",
            "publication": d / "reports" / "publication.yaml"}


def overlay(base: dict, cycle: str, targets: str) -> dict:
    """`base` with the cycle identity replaced, and nothing else. `run_self_scan.overlaid`'s
    rule, asserted rather than trusted: an overlay that touched a threshold would make the run
    a different instrument from the one whose findings it is compared with."""
    import copy
    params = copy.deepcopy(base)
    params["cycle"] = {"name": cycle, "targets": targets}
    differing = sorted(k for k in set(base) | set(params) if base.get(k) != params.get(k))
    if differing not in ([], ["cycle"]):
        raise SystemExit(f"FATAL: the overlay changes {differing}; only 'cycle' may differ")
    return params


def params_of_run(payload: dict, base: dict) -> dict:
    """The parameters an adopter run was measured under: `base` plus the payload's overlay,
    REFUSED unless it hashes to what every Observation of the run carries. A `params.yaml`
    edited between the scan and the render is a different instrument, and matrices built under
    it would be judgements the run never made."""
    from scan.model import params_hash
    ov = payload.get("params_overlay") or {}
    params = {**base, **ov}
    if params_hash(params) != payload["params_hash"]:
        raise SystemExit(
            f"REFUSING: params.yaml plus this run's overlay hashes to "
            f"{params_hash(params)[:12]}… and the run was measured under "
            f"{payload['params_hash'][:12]}…: params.yaml changed after the scan. Restore it "
            f"(the run records base_params_hash {str(payload.get('base_params_hash'))[:12]}…) "
            f"or scan again.")
    return params


def write_json(path: Path, doc: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8")
