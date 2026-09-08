#!/usr/bin/env python3
"""Move control-fixture test litter out of the committed scan evidence store. **Zero spend.**

Task `cc_tasks/2026-09-07_scan_hygiene.md` §2. `corpus/evidence/scan/` is the one `corpus/`
lane that is COMMITTED (see the note in `.gitignore`), and until
`tests/conftest.py::no_writes_to_the_real_evidence_store` existed, every run of
`tests/test_scan_harness.py` stored a fresh set of control-fixture bodies into it. Content
addressing did not dedupe them: the fixture server binds an EPHEMERAL port which is
substituted into every body carrying `HOSTPORT`, so each run minted new digests.

**The discriminator is NOT "the body names the fixture host".** The task file assumed it was,
and it over-selects: the control cycle's OWN evidence — the bytes its Observations cite and
the re-derivation gate depends on — are fixture bodies too, and eight of them carry the port.
Quarantining those would strand live Observations, which is precisely the defect §1 of the
same task exists to annotate. So the test is BOTH conditions:

    the stored body names the fixture host  AND  no Observation on the event log cites its
    digest

An unreferenced blob is litter by construction: the event log is the source of truth
(invariant 1), and a body no event points at is a body no Finding can ever cite.

**A second category, added 2026-09-07 by `cc_tasks/2026-09-07_scan_harness_v3.md`:** a blob
that git does not track AND no Observation cites was never part of the corpus at all, whatever
its content — so the fixture-host marker is not needed to recognise it. That is not a wider net
thrown at tracked evidence: a pending cycle's bodies become cited the moment its payload is
published, and until then they are not corpus either. It exists because the `refuses_identified_client`
fixture answers 403 with an EMPTY body, and a zero-length blob carries no marker to match on.

Litter that git TRACKS is moved, never deleted (invariant 2): the bytes go to
`corpus/quarantine/evidence_scan_fixture/` under their own digest, with one `reason.txt`
naming every one of them. Litter git does not track is REMOVED, and the distinction is
invariant 2's own: it protects bad *acquisitions*, and an uncommitted test output was never
an acquisition — quarantining it would ADD scratch to the tracked tree, which is the thing
this sweep exists to take out of it. The two counts are reported separately.

    /opt/anaconda3/bin/python3 scripts/quarantine_fixture_evidence.py --dry-run
    /opt/anaconda3/bin/python3 scripts/quarantine_fixture_evidence.py
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

from kg import eventlog                                              # noqa: E402
from scan.fixtures.server import BIND_HOST                           # noqa: E402
from scan.model import EVIDENCE_ROOT                                 # noqa: E402

TASK = "cc_tasks/2026-09-07_scan_hygiene.md"
QUARANTINE = REPO / "corpus" / "quarantine" / "evidence_scan_fixture"
REASON = QUARANTINE / "reason.txt"
#: A stored body that names the loopback host and a port is fixture output: no federal surface
#: this harness measures serves a loopback URL. `BIND_HOST` is imported from the fixture server
#: rather than repeated, so there is one definition of what the fixtures look like.
MARKER = f"{BIND_HOST}:".encode()
OBS_EVENT = "observation_recorded"


def cited_digests() -> set:
    """Every `body_sha256` any Observation on the event log cites. The log is the source of
    truth about what is evidence; the filesystem is not."""
    out = set()
    for ev in eventlog.replay():
        if ev.get("event_type") != OBS_EVENT:
            continue
        h = (ev.get("response") or {}).get("body_sha256")
        if h:
            out.add(h)
    return out


def tracked_paths() -> set:
    """Every path under the evidence root that git tracks, absolute. A blob git holds is part
    of the committed corpus and is preserved; one it does not was never in it."""
    root = EVIDENCE_ROOT.relative_to(REPO)
    out = subprocess.run(["git", "ls-files", "-z", "--", str(root)],
                         capture_output=True, text=True, cwd=REPO)
    if out.returncode:
        raise SystemExit(f"FATAL: git ls-files failed: {out.stderr.strip()}")
    return {REPO / p for p in out.stdout.split("\0") if p}


def classify(root: Path | None = None) -> dict:
    """`{litter, cited_fixture_blobs, other}` as sorted path lists, relative to the repo."""
    root = root or EVIDENCE_ROOT
    cited = cited_digests()
    tracked = tracked_paths()
    litter, cited_fixture, orphan, other = [], [], [], []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        try:
            body = path.read_bytes()
        except OSError as exc:                       # a blob we cannot read is not a blob we
            raise SystemExit(f"FATAL: cannot read {path}: {exc}")   # may silently pass over
        if path.name in cited:
            (cited_fixture if MARKER in body else other).append(path)
        elif MARKER in body:
            litter.append(path)
        elif path not in tracked:
            orphan.append(path)
        else:
            other.append(path)
    return {"litter": litter, "cited_fixture_blobs": cited_fixture, "orphan_untracked": orphan,
            "other": other, "cited_total": len(cited)}


#: What wrote the litter, when the caller does not say. It was `tests/test_scan_harness.py`
#: for every sweep to 2026-09-07, and the sentence was written as a constant — so the
#: 2026-09-08 sweep recorded that attribution for 54 blobs written by
#: `scan/rederive.control_gate_record`, which had reached `run_controls` directly and
#: inherited the DEFAULT evidence root. A quarantine record that names the wrong writer sends
#: the next reader to the wrong file, so the source is now an ARGUMENT with the old value as
#: its default, and `--wrote-by` is how a caller says otherwise.
DEFAULT_WRITER = ("`tests/test_scan_harness.py` before "
                  "`tests/conftest.py::no_writes_to_the_real_evidence_store` redirected the "
                  "evidence root under test")


def sweep(apply: bool, root: Path | None = None, wrote_by: str | None = None) -> dict:
    c = classify(root)
    tracked = tracked_paths()
    litter = c["litter"]
    committed = [p for p in litter if p in tracked]
    # Untracked litter and untracked orphans are removed the same way and for the same reason:
    # neither was ever in the corpus.
    uncommitted = [p for p in litter if p not in tracked] + c["orphan_untracked"]
    if apply and litter:
        QUARANTINE.mkdir(parents=True, exist_ok=True)
        for p in committed:
            dest = QUARANTINE / p.name
            if dest.exists():                        # same digest, same bytes: already swept
                p.unlink()
                continue
            shutil.move(str(p), str(dest))
        for p in uncommitted:
            p.unlink()
        # One reason file for the batch, appended to rather than rewritten: a later sweep is
        # a later finding and must not erase the record of the first.
        stamp = datetime.now(timezone.utc).isoformat()
        with REASON.open("a", encoding="utf-8") as fh:
            fh.write(
                f"# swept {stamp} by scripts/quarantine_fixture_evidence.py ({TASK})\n"
                f"# control-fixture test litter: the stored body names the fixture host "
                f"{BIND_HOST} AND no `observation_recorded` event cites its digest, so no "
                f"Finding can ever cite it. Written by {wrote_by or DEFAULT_WRITER}. "
                f"Moved, not deleted (project invariant 2). "
                f"{len(uncommitted)} of them were untracked when swept and were removed "
                f"rather than moved (see this script's docstring). "
                f"{len(c['cited_fixture_blobs'])} fixture-host blobs ARE cited by "
                f"Observations on the log and were left in place — they are the control "
                f"cycle's own evidence.\n")
            for p in committed:
                fh.write(f"{p.name}\n")
            for p in uncommitted:
                fh.write(f"{p.name}\t(untracked when swept; removed, not moved)\n")
        # Empty digest-prefix directories left behind are noise of the same kind.
        for d in sorted((root or EVIDENCE_ROOT).glob("*")):
            if d.is_dir() and not any(d.iterdir()):
                d.rmdir()
    return {"quarantined": len(committed), "untracked_litter_removed": len(uncommitted),
            "untracked_orphans_included": len(c["orphan_untracked"]),
            "cited_fixture_blobs_left_in_place":
            len(c["cited_fixture_blobs"]), "non_fixture_blobs": len(c["other"]),
            "distinct_body_hashes_cited_by_the_log": c["cited_total"],
            "applied": bool(apply)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--wrote-by", default=None, metavar="TEXT",
                    help="what produced this litter, recorded verbatim in reason.txt. "
                         "Defaults to the writer every sweep to 2026-09-07 had; a sweep after "
                         "a different writer must say so, or the record sends the next reader "
                         "to the wrong file.")
    a = ap.parse_args(argv)
    out = sweep(apply=not a.dry_run, wrote_by=a.wrote_by)
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
