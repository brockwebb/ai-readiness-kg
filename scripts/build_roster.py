#!/usr/bin/env python3
"""The federal statistical system as a parsed roster, with its sources on the log. **Zero spend.**

Task `cc_tasks/2026-09-08_scan_frame_fss.md` §1. The frame decision names two documents and
the task says: *"Fetch and cite; do not type the roster from this file."* So nothing here is a
list of agencies. Both bodies are fetched once, retained content-addressed, and PARSED — and
the count the frame asserts is a thing this script can disagree with, which is the only way an
assertion in a task file can ever be checked.

**It does disagree, and that disagreement is the finding.** Both sources carry the same legend
— `^` a Recognized Statistical Agency or Unit, `*` a designated Statistical Official, `**` the
Chair — so each tier is a parse of a flag rather than a reading of prose:

* The **ICSP charter** flags **16**, including `Social Security Administration, Office of
  Research, Evaluation, and Statistics^*`.
* The live **About page** flags **15**: the same list with SSA/ORES carrying `*` alone, and its
  "Recognized Statistical Agencies and Units" link list has the matching 15 entries.
* The **About page's own prose** says *"a decentralized, interconnected network of 16
  Recognized Statistical Agencies and Units"* — so that page contradicts itself, 16 in the
  sentence and 15 in the list beneath it.

`params.frame.roster_authority` settles it, and it was written before the counts were seen:
membership from the charter (the Council's constitutive document, which enumerates under the
legend), URLs from the About page (the only source carrying one per agency). Every
disagreement is recorded on the roster's face — `tier_a_disagreements` — never resolved
silently.

**Evidence lane.** Bodies go to `corpus/evidence/frame/`, NOT `corpus/evidence/scan/`. That
store is the one DD-058's uncited-body census counts, and a roster body no Observation cites
would make the retained-uncited set GROW — the one thing staging exists to make impossible.
A frame source is cited by a DataFile, not by an Observation, so it needs its own lane.

    /opt/anaconda3/bin/python3 scripts/build_roster.py --dry-run
    /opt/anaconda3/bin/python3 scripts/build_roster.py
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import subprocess
import sys
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

from scan import load_params                                        # noqa: E402

TASK = "cc_tasks/2026-09-08_scan_frame_fss.md"
#: Its own lane. See the module docstring: a frame source is cited by a DataFile, and putting
#: it in the scan evidence store would grow the set DD-058 says can only shrink.
EVIDENCE = REPO / "corpus" / "evidence" / "frame"
OUT = REPO / "state" / "fss_roster_2026-09.json"
DATAFILE = "fss_roster_2026-09"

#: The one entry the charter recognizes and the live About page does not link, so it has no
#: home URL from either source. Carried from this repo's OWN prior record rather than typed
#: from memory or invented — `assessment/harness/scan/targets.yaml` recorded it for cycle 1
#: with its OMB SPD-1 segment, and prior art in this repo is prior art (CLAUDE.md §1.2).
#: Read from that file at run time, never copied here.
CYCLE1_ROSTER = REPO / "assessment" / "harness" / "scan" / "targets.yaml"


def fetch(url: str, fetcher) -> dict:
    """One GET through the harness's own manners: identified UA, 1 req/s per host, robots
    obeyed. Returns the body and its digest; the body is written by `retain`."""
    r = fetcher.raw_get(url)
    return {"url": url, "final_url": r["final_url"], "status": r["status"],
            "bytes": len(r["body"]), "body": r["body"],
            "content_type": (r["headers"].get("content-type") or "").split(";")[0].strip(),
            "sha256": hashlib.sha256(r["body"]).hexdigest(),
            "fetched_at": datetime.now(timezone.utc).isoformat()}


def retain(cap: dict) -> str:
    """Store the body content-addressed and return its repo-relative path."""
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    d = cap["sha256"]
    path = EVIDENCE / d[:2] / d
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(cap["body"])
    return str(path.relative_to(REPO))


# ------------------------------------------------------------------ parsing, per source kind

def _clean(text: str) -> str:
    return " ".join(str(text).split())


def _flagged(line: str, params: dict) -> dict:
    """Split an enumeration line into its name and its flags.

    The flags are SUFFIXES on the affiliation and the legend line itself starts with one, so a
    naive "contains `^`" match would read the legend as a member. `legend_line_tokens` is the
    declared guard.
    """
    f = params["frame"]["flags"]
    low = line.lower()
    if any(t in low for t in params["frame"]["legend_line_tokens"]):
        return {}
    m = re.search(r"([\^\*]+)\s*$", line)
    flags = m.group(1) if m else ""
    return {"name": _clean(line[:m.start()] if m else line),
            "recognized": f["recognized_agency_or_unit"] in flags,
            "official": f["statistical_official"] in flags,
            "chair": flags.count(f["statistical_official"]) >= 2,
            "flags": flags}


def parse_charter(body: bytes, params: dict) -> dict:
    """The charter's membership list, from the PDF text between its own two markers."""
    import pypdf
    text = "\n".join((p.extract_text() or "")
                     for p in pypdf.PdfReader(io.BytesIO(body)).pages)
    start = text.find("ICSP membership currently stands as follows")
    # Cut at the FLAG CHARACTER that opens the legend, not at the word "Denotes". The legend
    # reads `^Denotes a Recognized Statistical Agency…` and runs straight on from the last
    # bullet with no separator, so cutting at "Denotes" leaves that `^` on the final entry —
    # which read `U.S. Agency for International Development* ^` and made USAID a recognized
    # agency. A parse that is one character short is not a smaller error than a wrong list.
    legend = re.search(r"[\^\*]+\s*Denotes a Recognized Statistical Agency", text)
    end = legend.start() if legend else -1
    if start < 0 or end < 0:
        raise SystemExit("REFUSING: the charter does not carry its membership markers; the "
                         "document changed shape and the parse is no longer grounded.")
    entries = []
    for chunk in text[start:end].split("●")[1:]:      # ● bullets
        line = _clean(chunk)
        # A page footer runs into the last bullet on a page break.
        line = re.split(r"Interagency Council on Statistical Policy", line)[0].strip()
        if not line:
            continue
        got = _flagged(line, params)
        if got:
            entries.append(got)
    return {"entries": entries, "chars": len(text)}


def parse_about(body: bytes, params: dict) -> dict:
    """The About page: the flagged member cards, the linked recognized-agency list, and the
    two counts the page states in prose."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(body, "html.parser")
    entries = []
    for h in soup.find_all("h3"):
        p = h.find_next_sibling("p")
        if p is None:
            continue
        line, person = _clean(p.get_text()), _clean(h.get_text())
        if not line or not person:
            continue
        got = _flagged(line, params)
        if got:
            entries.append({**got, "person": person})
    links = []
    head = soup.find(id="statistical-agencies")
    if head is not None:
        for a in head.find_all_next("a", href=True):
            if a.find_previous(["h4"]) is not None and a.find_previous(["h4"]).sourceline > \
                    head.sourceline:
                break                                   # into "Related Federal Websites"
            text = _clean(a.get_text())
            if text and a["href"].startswith("http"):
                links.append({"name": text, "url": a["href"]})
    prose = _clean(re.sub(r"<[^>]+>", " ", body.decode("utf-8", "replace")))
    m = re.search(r"network of (\d+)\s+Recognized Statistical Agencies and Units,\s*(\d+)\s+"
                  r"Statistical Officials", prose)
    return {"entries": entries, "agency_links": links,
            "prose_recognized": int(m.group(1)) if m else None,
            "prose_officials": int(m.group(2)) if m else None}


# ------------------------------------------------------------------ reconciliation

_STOP = re.compile(r"\b(department of the|department of|office of the|office of|division of|"
                   r"board of governors of the|u\.s\.|the)\b", re.I)


def _key(name: str) -> str:
    """A comparison key for an agency name across two documents that write it differently —
    'Bureau of the Census, Department of Commerce' against 'Department of Commerce, Bureau of
    the Census'. Order-free and stop-word-free, so the match is on the distinctive words."""
    words = {w for w in re.sub(r"[^a-z ]", " ", _STOP.sub(" ", name.lower())).split()
             if len(w) > 2}
    return " ".join(sorted(words))


#: A candidate names the SAME agency when it carries MORE THAN HALF of that agency's own
#: distinctive vocabulary, and no other candidate carries as much.
#:
#: Both halves are the rule, not a fitted constant. *Majority of the name* because an agency's
#: name is what identifies it, and the two documents write the same agency in opposite order
#: with different departmental wrappers — `Board of Governors of the Federal Reserve System …
#: Microeconomic Surveys Unit` against `Microeconomic Surveys Units, Board of Directors of the
#: Federal Reserve System` — so order-free containment of most of the name is the comparison
#: and a raw count is not. *Uniqueness* because the question is which candidate names this
#: agency and no other; where two fit equally the vocabulary does not separate them and a
#: guess is how a roster acquires a wrong host.
#:
#: A bare overlap count got this wrong twice in one run, in both directions: at two shared
#: words `Social Security Administration, Office of Research, Evaluation, and Statistics`
#: matched the SAMHSA link on {administration, statistics}, and the same loose test inside the
#: cycle-1 fallback gave the Federal Reserve unit the CDC's home page. A wrong host is worse
#: than a missing one, because the missing one is visible.
_MATCH_MIN_FRACTION = 0.5


def _match(name: str, candidates: list, name_of) -> dict | None:
    """The one candidate whose name is this agency's, or None. ONE comparator, two callers.

    `name_of` reads the comparable name off a candidate, so the About-page link list and this
    repo's own cycle-1 roster go through the same rule. They did not, and the looser of the two
    copies was the one that produced a wrong host.
    """
    k = set(_key(name).split())
    if not k:
        return None
    scored = sorted(((len(k & set(_key(name_of(c)).split())) / len(k), c) for c in candidates),
                    key=lambda t: -t[0])
    if not scored or scored[0][0] <= _MATCH_MIN_FRACTION:
        return None
    if len(scored) > 1 and scored[1][0] == scored[0][0]:
        return None                                    # ambiguous; a guess is not a match
    return scored[0][1]


def _best_link(name: str, links: list) -> dict | None:
    """The About-page link that names the same agency, or None."""
    return _match(name, links, lambda l: l["name"])


def cycle1_host(name: str) -> dict | None:
    """This repo's own cycle-1 roster row for an agency the live source does not link.

    Prior art in the repo IS prior art, and it carries its own citation: the row records the
    OMB SPD-1 segment the agency was read from. Read at run time from `targets.yaml`, never
    copied into this file — a second copy is a second roster.
    """
    import yaml
    cfg = yaml.safe_load(CYCLE1_ROSTER.read_text(encoding="utf-8"))
    row = _match(name, cfg.get("agencies", []),
                 lambda r: f"{r['name']} {r.get('department', '')}")
    if row is None:
        return None
    return {"url": row["host"], "source": (
        f"absent from the live statspolicy.gov recognized-agency link list; carried from this "
        f"repo's cycle-1 roster assessment/harness/scan/targets.yaml (OMB Statistical Policy "
        f"Directive No. 1, segment {row.get('spd1_segment')})")}


def build(params: dict, caps: dict) -> dict:
    charter = parse_charter(caps["icsp_charter"]["body"], params)
    about = parse_about(caps["statspolicy_about"]["body"], params)

    tier_a_src = [e for e in charter["entries"] if e["recognized"]]
    about_recognized = [e for e in about["entries"] if e["recognized"]]

    tier_a = []
    for e in tier_a_src:
        link = _best_link(e["name"], about["agency_links"])
        home = ({"url": link["url"], "source": "statspolicy.gov/about/ recognized-agency list"}
                if link else (cycle1_host(e["name"]) or {}))
        parent, _, unit = e["name"].partition(", ")
        tier_a.append({
            "name": e["name"],
            "parent_department": _clean(parent),
            "unit_name": _clean(unit) or _clean(parent),
            "kind": "unit" if not e["official"] else "principal_or_unit_with_official",
            "statistical_official": e["official"],
            "home_url": home.get("url"),
            "home_url_source": home.get("source"),
            "host": (urllib.parse.urlsplit(home["url"]).netloc if home.get("url") else None),
            # Through `_match`, like every other cross-document comparison here. Exact key
            # equality was a THIRD copy of this question and it was wrong in the other
            # direction: the two documents write the same unit with different departmental
            # wrappers — the About card omits `Division of Research and Statistics` for the
            # Federal Reserve unit and `Animal and Plant Health Inspection Service` for NAHMS —
            # so two agencies that ARE on the About page were reported as disagreements.
            "recognized_on_about_page": _match(e["name"], about_recognized,
                                               lambda x: x["name"]) is not None,
            "linked_on_about_page": bool(link),
        })

    tier_b = [{"name": e["name"], "host": None, "host_source": None,
               "chair": e["chair"],
               "no_host_on_source": True}
              for e in charter["entries"] if e["official"] and not e["recognized"]]

    disagreements = []
    for a in tier_a:
        if not a["recognized_on_about_page"]:
            disagreements.append({
                "entry": a["name"], "charter": "recognized (^)",
                "about_page": "designated Statistical Official (*) only, and absent from the "
                              "page's own recognized-agency link list",
                "resolved_by": params["frame"]["roster_authority"]})
    return {
        "tier_a": tier_a, "tier_b": tier_b,
        "counts": {
            "tier_a_charter": len(tier_a_src),
            "tier_a_about_flags": len(about_recognized),
            "tier_a_about_links": len(about["agency_links"]),
            "tier_a_about_prose": about["prose_recognized"],
            "tier_b_charter": len(tier_b),
            "officials_about_prose": about["prose_officials"],
            "charter_members": len(charter["entries"]),
            "about_members": len(about["entries"]),
        },
        "tier_a_disagreements": disagreements,
        "tier_a_without_home_url": [a["name"] for a in tier_a if not a["home_url"]],
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    params = load_params()
    from scan.manners import Fetcher
    fetcher = Fetcher(params)
    caps = {}
    for src in params["frame"]["roster_sources"]:
        cap = fetch(src["url"], fetcher)
        if cap["status"] != 200:
            raise SystemExit(f"REFUSING: {src['name']} answered HTTP {cap['status']}; the "
                             f"roster is not parsed from a document we were not served.")
        cap["role"], cap["note"] = src["role"], src["note"]
        caps[src["name"]] = cap
        print(f"  {src['name']:22s} HTTP {cap['status']} {cap['bytes']:>8} bytes "
              f"{cap['sha256'][:12]}…", flush=True)

    roster = build(params, caps)
    sources = []
    for name, cap in caps.items():
        entry = {k: v for k, v in cap.items() if k != "body"}
        entry["name"] = name
        entry["retained_path"] = None if a.dry_run else retain(cap)
        sources.append(entry)

    doc = {"task": TASK, "generated_at": datetime.now(timezone.utc).isoformat(),
           "authority": params["frame"]["roster_authority"],
           "authority_reason": (
               "Recognition under CIPSEA 2018 (44 U.S.C. 3561(11), 3562) is a legal status OMB "
               "confers. The ICSP charter is the Council's constitutive document and "
               "enumerates its membership under an explicit flag legend; the About page is a "
               "rendered summary of the same fact and is authoritative only for what it alone "
               "carries, the current home URL of each agency. Declared in params.frame BEFORE "
               "either body was parsed."),
           "sources": sources, **roster}
    if a.dry_run:
        print(json.dumps({"counts": doc["counts"],
                          "tier_a_disagreements": doc["tier_a_disagreements"],
                          "tier_a_without_home_url": doc["tier_a_without_home_url"]}, indent=1))
        for t in doc["tier_a"]:
            print(f"  A {t['name'][:62]:64s} {t['host'] or '-'}")
        for t in doc["tier_b"]:
            print(f"  B {t['name'][:62]:64s} {t['host'] or '(no host on source)'}")
        return 0
    OUT.write_text(json.dumps(doc, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps(doc["counts"], indent=1))
    print(f"-> {OUT.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
