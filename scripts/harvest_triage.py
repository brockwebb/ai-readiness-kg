#!/usr/bin/env python3
"""Phases 1–3 of task 2026-08-24_source_triage — bounded, idempotent triage harvest.

Reads scripts/triage_list_2026-08-24.yaml (verdicts + fetch config; never hardcoded here)
and routes every entry by its rule verdict:

  fetch          -> harvest_kernel.fetch_entry (httpx PDF / raw / httpx_dom / crwl with
                    fallback — the kernel machinery is imported, not re-derived). A failed
                    fetch whose blocking host is on settings.paywall_domains (or that died
                    on HTTP 401/403 at such a host) is reclassified access_blocked with the
                    blocking domain recorded (task Phase 1 / Phase 2 routing).
  youtube        -> transcript acquisition via yt-dlp auto/manual captions into staging as
                    markdown with capture provenance (video id, title, channel, upload date,
                    caption track). No established ingest-youtube path exists in this repo
                    or its siblings (searched 2026-08-26 — discrepancy recorded in the
                    RESULT); this is that path's first implementation.
  no_media       -> fetch_failed with the probed reason (ADDENDUM-01 lakefs routing).
  operator_drop  -> awaiting_operator_drop (max.gov decks; Phase 2 writes the download list).
  already_held   -> R5 dedupe hit; recorded, never fetched.
  excluded       -> excluded_by_rule with the matched clause.
  stage_only     -> fetched into staging with provenance, then marked staged_not_admitted
                    with the clause (a cited-but-not-admitted document; 2026-09-02).
  off_construct  -> flagged_off_construct (R4); recorded, never fetched.

Output: files in corpus/staging/inbox/triage_2026-08-24/ plus the machine-readable
_fetch_register.json (one record per entry, carrying verdict, clause, construct_arm,
grounding_surface, and the task's vetting provenance on every input-1 record).
candidate_register.jsonl lines are NOT written here: the dixie sweep imports that register
with a closed status_map (manifested/needs_source/excluded), so the single writer of final
statuses is scripts/manifest_triage.py at Phase 4 — an interim status here would either
crash the sweep or project a wrong screening decision (kernel run defect 2, 2026-08-21).

Zero model calls; refuses to run if ANTHROPIC_API_KEY is set (DD-007 posture).

Usage:
    /opt/anaconda3/bin/python3 scripts/harvest_triage.py [--only DOC_ID ...] [--dry-run] [--force]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import yaml  # noqa: E402
import harvest_kernel as hk  # noqa: E402  (machinery reuse: Fetcher, fetch_entry, helpers)

TRIAGE_LIST = REPO / "scripts" / "triage_list_2026-08-24.yaml"
INBOX = REPO / "corpus" / "staging" / "inbox" / "triage_2026-08-24"
FETCH_REGISTER = INBOX / "_fetch_register.json"
TASK_REF = "cc_tasks/2026-08-24_source_triage.md Phases 1-3"
YT_DLP = "/opt/anaconda3/bin/yt-dlp"

STATUSES = ("fetched", "fetch_failed", "access_blocked", "excluded_by_rule",
            "already_held", "flagged_off_construct", "awaiting_operator_drop",
            "oversize_needs_clearance", "staged_not_admitted")


def _host(url: str | None) -> str:
    m = re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://([^/]+)", url or "")
    return (m.group(1) if m else "").lower().removeprefix("www.")


def classify_access_block(rec: dict, entry: dict, paywall_domains: list[str]) -> None:
    """Reclassify a fetch_failed record as access_blocked when the blocking host is a
    declared paywall/login domain (task Phase 1). Records the blocking domain."""
    if rec.get("candidate_status") != "fetch_failed":
        return
    hosts = {_host(u) for u in (rec.get("urls_tried") or [])}
    hosts.add(_host(rec.get("final_url")))
    hosts.add(_host(entry.get("primary_url")))
    hosts.discard("")
    blocked = sorted(h for h in hosts
                     if any(h == d or h.endswith("." + d) for d in paywall_domains))
    if blocked:
        rec["candidate_status"] = "access_blocked"
        rec["blocking_domain"] = blocked[0]


# ------------------------------------------------------------------ youtube transcripts
_VTT_TS = re.compile(r"^\d{2}:\d{2}:\d{2}\.\d{3} --> ")
_VTT_TAG = re.compile(r"<[^>]+>")


def vtt_to_text(vtt: str) -> str:
    """Cue text only, tags stripped, rolling-caption duplicates collapsed."""
    lines, prev = [], None
    in_cue = False
    for raw in vtt.splitlines():
        line = raw.strip()
        if _VTT_TS.match(line):
            in_cue = True
            continue
        if not line or line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE", "STYLE")):
            in_cue = False
            continue
        if not in_cue:
            continue
        text = _VTT_TAG.sub("", line).strip()
        if text and text != prev:
            lines.append(text)
            prev = text
    return "\n".join(lines) + "\n"


def fetch_youtube_transcript(entry: dict, dry_run: bool) -> dict:
    rec = {
        "doc_id": entry["doc_id"], "title": entry["title"],
        "primary_url": entry["primary_url"], "source_type": entry["source_type"],
        "clause": entry["clause"], "retrieved_at_utc": hk.utc_now(),
        "urls_tried": [entry["primary_url"]], "fetch_method": "yt-dlp-captions",
        "local_path": None, "sha256": None, "bytes": None, "chars": None,
        "as_of": None, "as_of_source": None, "candidate_status": None, "reason": None,
    }
    if dry_run:
        rec["candidate_status"] = "dry_run"
        return rec
    if not os.path.exists(YT_DLP):
        rec["candidate_status"], rec["reason"] = "fetch_failed", f"yt-dlp not found at {YT_DLP}"
        return rec
    with tempfile.TemporaryDirectory(prefix="triage_yt_") as td:
        meta_proc = subprocess.run(
            [YT_DLP, "--no-update", "--skip-download", "-j", entry["primary_url"]],
            capture_output=True, text=True, timeout=180)
        if meta_proc.returncode != 0:
            rec["candidate_status"] = "fetch_failed"
            rec["reason"] = f"yt-dlp metadata failed: {meta_proc.stderr.strip()[-300:]}"
            return rec
        meta = json.loads(meta_proc.stdout.splitlines()[-1])
        sub_proc = subprocess.run(
            [YT_DLP, "--no-update", "--skip-download", "--write-subs", "--write-auto-subs",
             "--sub-langs", "en.*,en", "--sub-format", "vtt",
             "-o", str(Path(td) / "%(id)s"), entry["primary_url"]],
            capture_output=True, text=True, timeout=300)
        vtts = sorted(Path(td).glob("*.vtt"))
        if not vtts:
            rec["candidate_status"] = "fetch_failed"
            rec["reason"] = ("no caption track retrievable: "
                            + (sub_proc.stderr.strip()[-300:] or "no .vtt produced"))
            return rec
        track = vtts[0]
        text = vtt_to_text(track.read_text(encoding="utf-8", errors="replace"))
        if len(text.strip()) < 200:
            rec["candidate_status"] = "fetch_failed"
            rec["reason"] = f"transcript too short ({len(text.strip())} chars) — capture not kept"
            return rec
        upload = meta.get("upload_date")
        as_of = f"{upload[:4]}-{upload[4:6]}-{upload[6:8]}" if upload else None
        # Header carries capture provenance but no retrieval timestamp, so identical caption
        # content hashes identically across re-runs (retrieved_at lives in the registers).
        header = (f"<!-- triage transcript: {TASK_REF}; primary_url={entry['primary_url']}; "
                  f"video_id={meta.get('id')}; video_title={meta.get('title')!r}; "
                  f"channel={meta.get('channel')!r}; upload_date={as_of}; "
                  f"caption_track={track.name!r} (yt-dlp, auto/manual en); "
                  f"grounding_surface=transcript -->\n\n# {entry['title']}\n\n")
        body = (header + text).encode("utf-8")
        INBOX.mkdir(parents=True, exist_ok=True)
        target = INBOX / f"{entry['doc_id']}.md"
        target.write_bytes(body)
        rec.update({
            "local_path": str(target.relative_to(REPO)), "sha256": hk.sha256_bytes(body),
            "bytes": len(body), "chars": len(text), "as_of": as_of,
            "as_of_source": "yt-dlp:upload_date" if as_of else "none",
            "video_id": meta.get("id"), "channel": meta.get("channel"),
            "caption_track": track.name, "candidate_status": "fetched",
        })
    return rec


# ---------------------------------------------------------------------------- registers
def load_fetch_register() -> dict:
    if FETCH_REGISTER.exists():
        return json.loads(FETCH_REGISTER.read_text(encoding="utf-8"))
    return {"task": TASK_REF, "triage_list": str(TRIAGE_LIST.relative_to(REPO)), "records": {}}


def save_fetch_register(reg: dict) -> None:
    reg["updated_at_utc"] = hk.utc_now()
    FETCH_REGISTER.parent.mkdir(parents=True, exist_ok=True)
    FETCH_REGISTER.write_text(json.dumps(reg, indent=1, ensure_ascii=False) + "\n",
                              encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    # Round 2 (task 2026-08-30_acquisition_round2) reuses this harvester against its own
    # list and staging dir. The alternative was a second copy of the fetch/route/register
    # machinery, which would then have to be kept in step with this one — the paywall
    # reclassification and the resume-on-sha rules are exactly the code you do not want two
    # versions of.
    ap.add_argument("--list", default=None,
                    help="candidate list YAML (default: the 2026-08-24 triage list)")
    ap.add_argument("--inbox", default=None,
                    help="staging directory for fetched files and the fetch register")
    ap.add_argument("--task-ref", default=None, help="task reference stamped on captures")
    args = ap.parse_args()

    global TRIAGE_LIST, INBOX, FETCH_REGISTER, TASK_REF
    if args.list:
        TRIAGE_LIST = Path(args.list).resolve()
    if args.inbox:
        INBOX = Path(args.inbox).resolve()
        FETCH_REGISTER = INBOX / "_fetch_register.json"
    if args.task_ref:
        TASK_REF = args.task_ref

    if os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is set; this task runs with zero model spend and refuses "
              "to start (DD-007).", file=sys.stderr)
        return 2
    cfg = yaml.safe_load(TRIAGE_LIST.read_text(encoding="utf-8"))
    settings, entries = cfg["settings"], cfg["entries"]
    ids = [e["doc_id"] for e in entries]
    if len(ids) != len(set(ids)):
        print("duplicate doc_id in triage list", file=sys.stderr)
        return 2
    if args.only:
        entries = [e for e in entries if e["doc_id"] in set(args.only)]

    crwl_path = shutil.which("crwl") or next(
        (p for p in ("/opt/anaconda3/bin/crwl", os.path.expanduser("~/.bun/bin/crwl"))
         if os.path.exists(p)), None)
    hk.log(f"crwl: {crwl_path or 'NOT FOUND (httpx-dom fallback for all HTML)'}")
    # Route the kernel machinery's module paths at this task's staging dir. TASK_REF is
    # read by the capture headers; INBOX by fetch_entry's file writes.
    hk.INBOX = INBOX
    hk.TASK_REF = TASK_REF

    fx_default = hk.Fetcher(settings, crwl_path)
    fx_browser = hk.Fetcher({**settings, "user_agent": settings["browser_user_agent"]},
                            crwl_path)
    reg = load_fetch_register()
    counts: dict[str, int] = {}

    def bump(status: str) -> None:
        counts[status] = counts.get(status, 0) + 1

    try:
        for entry in entries:
            did = entry["doc_id"]
            verdict = entry["verdict"]
            prev = reg["records"].get(did)
            if prev and prev.get("candidate_status") == "fetched" and not args.force:
                p = REPO / prev["local_path"]
                if p.exists() and hk.sha256_bytes(p.read_bytes()) == prev["sha256"]:
                    bump("skipped_already_fetched")
                    hk.log(f"skip (already fetched, sha ok): {did}")
                    continue
            hk.log(f"{did} [{verdict}]")

            if verdict in ("fetch", "stage_only"):
                fx = fx_browser if entry.get("browser_ua") else fx_default
                rec = hk.fetch_entry(entry, fx, settings, args.dry_run)
                if entry.get("browser_ua"):
                    rec["user_agent"] = "browser (settings.browser_user_agent)"
                classify_access_block(rec, entry, settings["paywall_domains"])
                # stage_only (task 2026-09-02_g1_eval_prior_art §3): the bytes are staged
                # with full provenance so the memo's citation is reproducible, but the
                # standing-rule clause on the entry stops admission. manifest_triage never
                # treats this status as admissible; it registers it as `excluded` with the
                # clause, which is what "staged-not-admitted" means on the register.
                if verdict == "stage_only" and rec.get("candidate_status") == "fetched":
                    rec["candidate_status"] = "staged_not_admitted"
                    rec["reason"] = f"staged, not admitted: clause {entry['clause']}"
            elif verdict == "youtube":
                rec = fetch_youtube_transcript(entry, args.dry_run)
            elif verdict in ("no_media", "already_held", "excluded", "off_construct",
                             "operator_drop"):
                status = {"no_media": "fetch_failed", "already_held": "already_held",
                          "excluded": "excluded_by_rule",
                          "off_construct": "flagged_off_construct",
                          "operator_drop": "awaiting_operator_drop"}[verdict]
                rec = {"doc_id": did, "title": entry["title"],
                       "primary_url": entry.get("primary_url"),
                       "source_type": entry.get("source_type"), "clause": entry["clause"],
                       "retrieved_at_utc": hk.utc_now(), "urls_tried": [],
                       "candidate_status": status,
                       "reason": entry.get("notes"),
                       "held_doc_id": entry.get("held_doc_id")}
            else:
                raise SystemExit(f"FATAL: unknown verdict {verdict!r} on {did}")

            # verdict metadata rides in the register record verbatim
            for key in ("row", "verdict", "clause", "construct_arm", "grounding_surface",
                        "year", "authors_or_org", "extent_note", "held_doc_id", "gap",
                        "notes"):
                if entry.get(key) is not None:
                    rec[key] = entry[key]
            if not entry.get("gap"):
                rec["vetting"] = settings["vetting_input1"]
            rec["discovered_via"] = (settings["discovered_via_gap"] if entry.get("gap")
                                     else settings["discovered_via"])
            if args.dry_run:
                print(f"  would handle: {verdict} "
                      f"{entry.get('pdf_url') or entry.get('raw_url') or entry.get('primary_url')}")
                continue
            st = rec["candidate_status"]
            bump(st)
            hk.log(f"  -> {st}"
                   + (f" ({rec.get('reason')})" if rec.get("reason") else "")
                   + (f" chars={rec.get('chars')}" if rec.get("chars") else ""))
            reg["records"][did] = rec
            save_fetch_register(reg)
    finally:
        fx_default.close()
        fx_browser.close()
    if not args.dry_run:
        reg["counts"] = counts
        save_fetch_register(reg)
    hk.log("counts: " + json.dumps(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())
