#!/usr/bin/env python3
"""Phase 4 of task 2026-08-24_source_triage — rule-based manifest adds (AUTH-2 pattern).

Admits every `fetched` triage candidate that passed R1–R3 through the repo's designed path
(same shape as scripts/manifest_kernel.py, which this adapts):
  1. file moved corpus/staging/inbox/triage_2026-08-24/ -> corpus/triage/<doc_id>.<ext>
     (document_dir in dixie_evidence.yaml; gitignored — provenance rides in the events
     via primary_url + sha256)
  2. dixie ledger: `screening_imported` (source_id fss_research_group_2026-08 for input-1
     rows, seo_aio_gap_2026-08-24 for Phase 3 items; decision included, rationale = the
     matched rule clause), then the dixie sweep observes + integrity-checks the files.
  3. kg.manifest.add -> `manifest_add` events in events/batch-014.jsonl (the triage shard)
     carrying construct_arm, grounding_surface, and acquisition evidence including the
     matched clause and the task's vetting provenance (signal_not_verdict — recorded,
     never treated as satisfying the inclusion rule by itself).
  4. `corpus_epoch_declared` epoch=triage-2026-08-24 with the admitted member list.
  5. manifest.rebuild(), then ONE final candidate_register.jsonl line per triage entry
     with the dixie-legal status (manifested / needs_source / excluded) and the task's
     full candidate_status carried as a field. already_held entries get NO register line:
     the sweep re-imports the register merged by URL/title-slug, and a duplicate line
     whose URL differs from the holding entry's would mint a phantom ledger record
     (kernel run defect 2, 2026-08-21, is the precedent for this caution).

Items awaiting_operator_drop / access_blocked / fetch_failed are NOT manifested — manifest
admission requires the artifact in hand with its hash (task Phase 4, no exceptions).

Zero model calls. Stdlib + pyyaml + dixie.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402
from kg import eventlog, manifest                                   # noqa: E402
from dixie.evidence.config import load_config as dixie_config       # noqa: E402
from dixie.evidence.eventlog import EventLog as DixieLog            # noqa: E402
from dixie.evidence.manifest import build_manifest                  # noqa: E402
from dixie.evidence.sweep import Sweep                              # noqa: E402

TRIAGE_LIST = REPO / "scripts" / "triage_list_2026-08-24.yaml"
FETCH_REGISTER = REPO / "corpus" / "staging" / "inbox" / "triage_2026-08-24" / "_fetch_register.json"
CANDIDATE_REGISTER = REPO / "corpus" / "staging" / "candidate_register.jsonl"
TRIAGE_DIR = REPO / "corpus" / "triage"
BATCH = 14                       # events/batch-014.jsonl — the 2026-08-24 triage shard
EPOCH = "triage-2026-08-24"
SOURCE_INPUT1 = "fss_research_group_2026-08"
SOURCE_GAP = "seo_aio_gap_2026-08-24"
TASK = "cc_tasks/2026-08-24_source_triage.md"
#: Mutable one-element list so `run()` reads the CURRENT doc-dir name (module globals are
#: read at call time in this repo; a bare str rebound in main() would not be seen through
#: a `from ... import` in a test).
DOC_DIR_NAME = ["triage"]
SUMMARY_OUT = REPO / "docs" / "research" / "2026-08-24_triage_phase4_manifest_summary.json"
EPOCH_NOTE = ("2026-08-24 SME source-list triage + SEO/AIO gap harvest; "
              "rule-based adds per AUTH-2; schema v0.3.3 construct_arm carried")
MAX_DOC_CHARS = 250000           # AUTH-4 oversize guard, same value the harvest enforced

# candidate_status -> dixie-legal register status (the import status_map is closed:
# manifested/needs_source/excluded — dixie fails loud on anything else).
REGISTER_STATUS = {
    "fetched": "needs_source",              # overwritten with "manifested" on admission
    "fetch_failed": "needs_source",
    "access_blocked": "needs_source",
    "awaiting_operator_drop": "needs_source",
    "oversize_needs_clearance": "needs_source",
    "excluded_by_rule": "excluded",
    "flagged_off_construct": "excluded",
    "staged_not_admitted": "excluded",      # bytes staged for citation; clause stops admission
}


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_records() -> dict[str, dict]:
    if not FETCH_REGISTER.is_file():
        raise SystemExit(f"FATAL: fetch register not found: {FETCH_REGISTER} (Phase 1 output)")
    return json.loads(FETCH_REGISTER.read_text(encoding="utf-8"))["records"]


def existing_identity() -> tuple[set[str], set[str], set[str]]:
    ids, shas, urls = set(), set(), set()
    for ev in eventlog.replay():
        if ev.get("event_type") == "manifest_add":
            p = ev["payload"]
            ids.add(p["doc_id"]); shas.add(p["content_hash"])
            urls.add(manifest._normalize_url(p["primary_url"]))
    return ids, shas, urls


def dedup_key(rec: dict) -> str:
    url = rec.get("primary_url") or ""
    m = re.search(r"(\d{4}\.\d{5})", url) if "arxiv.org" in url else None
    if m:
        return "arxiv:" + m.group(1)
    if url:
        return "url:" + re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
    return "docid:" + rec["doc_id"]


def register_line(rec: dict, status: str, reason: str) -> dict:
    return {
        "title": rec["title"], "primary_url": rec.get("primary_url"),
        "authors": rec.get("authors_or_org") or [], "year": rec.get("year"),
        "source_type": rec.get("source_type"),
        "discovered_via": [rec.get("discovered_via")],
        "notes": (rec.get("notes") or "")[:400],
        "dedup_key": dedup_key(rec), "status": status,
        "decision_reason": reason, "decided_at": _now()[:10], "decided_by": "cc",
        "candidate_status": rec["candidate_status"], "clause": rec.get("clause"),
        "doc_id": rec["doc_id"], "local_path": rec.get("local_path"),
        "sha256": rec.get("sha256"), "chars": rec.get("chars"), "as_of": rec.get("as_of"),
        "retrieved_at_utc": rec.get("retrieved_at_utc"), "final_url": rec.get("final_url"),
        "urls_tried": rec.get("urls_tried", []), "http_status": rec.get("http_status"),
        "construct_arm": rec.get("construct_arm"),
        "grounding_surface": rec.get("grounding_surface"),
        "blocking_domain": rec.get("blocking_domain"),
        "vetting": rec.get("vetting"),
        "task": TASK,
    }


def run(dry_run: bool, finalize: bool = False) -> int:
    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    if DOC_DIR_NAME[0] not in cfg["document_dirs"]:
        raise SystemExit(f"FATAL: dixie_evidence.yaml document_dirs must include "
                         f"{DOC_DIR_NAME[0]!r}")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    records = load_records()
    ids, shas, urls = existing_identity()
    manifest._MANIFEST_BATCH = BATCH   # module global, read at call time (kg/manifest.py)

    added, skipped, deferred = [], [], []
    TRIAGE_DIR.mkdir(parents=True, exist_ok=True)
    admitted_status: dict[str, str] = {}
    if finalize:
        shard = REPO / "events" / f"batch-{BATCH:03d}.jsonl"
        for line in shard.read_text(encoding="utf-8").splitlines():
            ev = json.loads(line)
            if ev.get("event_type") == "manifest_add":
                added.append((ev["payload"]["doc_id"], ev["payload"]["local_path"]))
        records_iter = []
    else:
        records_iter = list(records.values())

    for rec in records_iter:
        doc_id = rec["doc_id"]
        if rec["candidate_status"] != "fetched":
            continue                       # non-fetched classes register in the final step
        if rec.get("verdict") not in ("fetch", "youtube"):
            deferred.append((doc_id, f"unexpected verdict {rec.get('verdict')!r} on a fetched item"))
            continue
        if not rec.get("construct_arm"):
            deferred.append((doc_id, "no construct_arm on include verdict")); continue
        src = REPO / rec["local_path"]
        if not src.is_file():
            deferred.append((doc_id, f"file missing: {rec['local_path']}")); continue
        sha = _sha256(src)
        if sha != rec["sha256"]:
            deferred.append((doc_id, f"sha256 mismatch vs register ({sha[:12]} != {rec['sha256'][:12]})"))
            continue
        if int(rec["chars"]) > MAX_DOC_CHARS and not rec.get("extent_note"):
            deferred.append((doc_id, "oversize without extent_note (AUTH-4)")); continue
        norm_url = manifest._normalize_url(rec["primary_url"])
        if doc_id in ids:
            skipped.append((doc_id, "already manifested: doc_id")); continue
        if sha in shas:
            skipped.append((doc_id, "already manifested: content_hash")); continue
        if norm_url in urls:
            skipped.append((doc_id, "already manifested: primary_url")); continue

        dest = TRIAGE_DIR / f"{doc_id}{src.suffix.lower()}"
        if dry_run:
            added.append((doc_id, f"would add -> {dest.relative_to(REPO)}")); continue
        if dest.exists() and _sha256(dest) != sha:
            deferred.append((doc_id, f"destination exists with different content: {dest}")); continue
        if not dest.exists():
            shutil.move(str(src), str(dest))
        rel = dest.relative_to(REPO).as_posix()

        source_id = SOURCE_GAP if rec.get("gap") else SOURCE_INPUT1
        rationale = (f"triage inclusion rule clause ({rec['clause']}), "
                     f"construct_arm={rec['construct_arm']}: "
                     f"{(rec.get('notes') or 'see ' + TASK).splitlines()[0][:220]}")
        dlog.append("screening_imported", {
            "import_key": doc_id,
            "normalized": {
                "source_id": source_id, "doc_id": doc_id, "doc_id_exact": True,
                "title": rec["title"],
                "authors_or_org": rec.get("authors_or_org") or ["(unspecified)"],
                "pub_year": rec.get("year") or rec.get("as_of") or "n.d.",
                "doc_type": rec["source_type"],
                "source_url": rec["primary_url"], "local_path": rel,
                "expected_sha256": sha,
                "acquisition_method": rec.get("fetch_method") or "scripted_fetch",
                "acquired_by": "scripts/harvest_triage.py",
                "decision": "included", "rationale": rationale,
                "decided_by": "cc", "decided_at": _now(),
                "notes": rec.get("extent_note"),
            }})

        acquisition = {
            "acquisition_method": rec.get("fetch_method") or "scripted_fetch",
            "clause": rec["clause"],
            "as_of": rec.get("as_of"),
            "as_of_source": rec.get("as_of_source"),
            "vetting": rec.get("vetting"),      # signal_not_verdict — provenance, not authority
            "test": {"primary_url": rec["primary_url"], "final_url": rec.get("final_url"),
                     "urls_tried": rec.get("urls_tried"),
                     "http_status": rec.get("http_status"),
                     "retrieved_at_utc": rec["retrieved_at_utc"],
                     "tool": "scripts/harvest_triage.py"},
            "evaluation": {"identity_check": "pass",
                           "note": "not previously manifested by doc_id, sha256 or primary_url"},
            "verification": {"sha256": sha},
            "validation": {"chars": int(rec["chars"]), "bytes": dest.stat().st_size,
                           "format": dest.suffix.lstrip(".")},
            "task": TASK,
        }
        if rec.get("extent_note"):
            acquisition["extent_note"] = rec["extent_note"]
        if rec.get("video_id"):
            acquisition["capture"] = {"video_id": rec["video_id"],
                                      "channel": rec.get("channel"),
                                      "caption_track": rec.get("caption_track")}
        try:
            manifest.add(
                str(dest), doc_id=doc_id, title=rec["title"],
                authors=rec.get("authors_or_org") or ["(unspecified)"],
                pub_date=str(rec.get("year") or rec.get("as_of") or "n.d."),
                source_type=rec["source_type"], primary_url=rec["primary_url"],
                inclusion_rationale=rationale, discovered_via=source_id,
                construct_arm=rec["construct_arm"],
                grounding_surface=rec.get("grounding_surface") or "document",
                acquisition=acquisition)
        except manifest.ManifestError as exc:
            deferred.append((doc_id, f"manifest gate rejected: {exc}")); continue
        ids.add(doc_id); shas.add(sha); urls.add(norm_url)
        added.append((doc_id, rel))

    if dry_run:
        for d, why in added: print("ADD     ", d, why)
        for d, why in skipped: print("SKIP    ", d, why)
        for d, why in deferred: print("DEFER   ", d, why)
        return 0

    # sweep BEFORE any register write: the sweep re-imports candidate_register, so the
    # register must never hold an interim status the import map cannot resolve.
    sweep = Sweep(cfg, dlog)
    actions = sweep.run()
    entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    members = []
    for d, _ in added:
        e = entries.get(d)
        ok = e and e["screening"]["decision"] == "included" and \
            e["integrity"]["status"] == "verified" and e["identity"].get("canonical_path")
        if ok:
            members.append(d)
        else:
            deferred.append((d, f"post-sweep not verified/included: "
                                f"{e and (e['screening']['decision'], e['integrity']['status'])}"))
    added = [(d, p) for d, p in added if d in members]
    for d in members:
        admitted_status[d] = "manifested"
    if members:
        dlog.append("corpus_epoch_declared", {
            "epoch": EPOCH, "member_doc_ids": sorted(members),
            "declared_by": "cc", "task": TASK,
            "note": EPOCH_NOTE})
    manifest.rebuild()

    # final candidate_register lines (single writer, final statuses; no already_held lines)
    deferred_ids = {d for d, _ in deferred}
    lines_written = 0
    with CANDIDATE_REGISTER.open("a", encoding="utf-8") as fh:
        for rec in records.values():
            st = rec["candidate_status"]
            if st == "already_held":
                continue
            if st == "fetched":
                doc_id = rec["doc_id"]
                if doc_id in admitted_status:
                    status, reason = "manifested", (
                        f"manifest-added by rule (clause {rec.get('clause')}, "
                        f"construct_arm {rec.get('construct_arm')})")
                elif doc_id in deferred_ids:
                    status, reason = "needs_source", (
                        "fetched but deferred at the manifest gate: "
                        + next(w for d, w in deferred if d == doc_id))
                else:
                    status, reason = "needs_source", "fetched; not admitted this run"
            else:
                status = REGISTER_STATUS[st]
                reason = (rec.get("reason") or rec.get("notes")
                          or f"{st} (clause {rec.get('clause')})")[:400]
            fh.write(json.dumps(register_line(rec, status, reason), ensure_ascii=False) + "\n")
            lines_written += 1

    print(f"sweep: {actions}")
    print(f"added {len(added)} | skipped {len(skipped)} | deferred {len(deferred)} | "
          f"epoch {EPOCH} members {len(members)} | register lines {lines_written}")
    summary = {"added": added, "skipped": skipped, "deferred": deferred,
               "epoch": EPOCH, "members": sorted(members), "batch": BATCH,
               "register_lines": lines_written, "ts": _now()}
    out = SUMMARY_OUT
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("summary:", out.relative_to(REPO))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--finalize", action="store_true",
                    help="skip adds; run sweep + epoch + rebuild + register lines for the "
                         "manifest_add events already in the shard")
    # Round 2 (task 2026-08-30_acquisition_round2 §3) admits through this same path against
    # its own register, shard, document dir and epoch. Parameterizing beats copying: the
    # dedupe-by-doc_id/sha/url gate, the sweep-before-register ordering, and the
    # no-line-for-already_held rule are exactly the invariants a second copy would drift on.
    ap.add_argument("--register", help="fetch register JSON (default: the 2026-08-24 one)")
    ap.add_argument("--doc-dir", help="corpus/<name> document dir; must be in "
                                      "dixie_evidence.yaml document_dirs")
    ap.add_argument("--batch", type=int, help="event shard number")
    ap.add_argument("--epoch", help="corpus epoch to declare")
    ap.add_argument("--source-id", help="dixie source_id for this run's admissions")
    ap.add_argument("--task", help="task reference stamped on every record")
    ap.add_argument("--summary-out", help="path for the run summary JSON")
    ap.add_argument("--epoch-note", help="note recorded on the corpus_epoch_declared event")
    a = ap.parse_args()

    global FETCH_REGISTER, TRIAGE_DIR, BATCH, EPOCH, SOURCE_INPUT1, SOURCE_GAP, TASK
    global SUMMARY_OUT, EPOCH_NOTE
    if a.epoch_note:
        EPOCH_NOTE = a.epoch_note
    if a.register:
        FETCH_REGISTER = Path(a.register).resolve()
    if a.doc_dir:
        TRIAGE_DIR = REPO / "corpus" / a.doc_dir
        DOC_DIR_NAME[0] = a.doc_dir
    if a.batch is not None:
        BATCH = a.batch
    if a.epoch:
        EPOCH = a.epoch
    if a.source_id:
        SOURCE_INPUT1 = SOURCE_GAP = a.source_id
    if a.task:
        TASK = a.task
    if a.summary_out:
        SUMMARY_OUT = Path(a.summary_out).resolve()
    return run(a.dry_run, finalize=a.finalize)


if __name__ == "__main__":
    raise SystemExit(main())
