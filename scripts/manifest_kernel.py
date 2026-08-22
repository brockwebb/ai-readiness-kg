#!/usr/bin/env python3
"""Phase 3 of task 2026-08-21_v03_visibility_kernel — rule-based manifest adds (AUTH-2).

Admits every `fetched` kernel candidate through the repo's designed path, in order:
  1. file moved from corpus/staging/inbox/kernel/ to corpus/kernel/<doc_id>.<ext>
     (a document_dir in dixie_evidence.yaml; gitignored like bulk/ — provenance rides
     in the events via primary_url + sha256)
  2. dixie ledger: `screening_imported` (source_id kernel_list_2026-08-21, decision
     included, rationale = clause matched) so the entry has identity + provenance, then
     the dixie sweep observes + integrity-checks the file (file_observed /
     integrity_checked). Integrity failures quarantine through dixie and are reported.
  3. kg.manifest.add -> `manifest_add` event (batch per --batch; default 6 = the kernel
     shard) carrying clause, as_of, sha256, retrieval evidence, extent_note.
  4. `corpus_epoch_declared` epoch=kernel-v03 in the dixie ledger with the admitted
     member list, so the runner (profile kernel_v03) can select exactly this set.

Identity check: anything whose doc_id, sha256 or normalized primary_url is already
manifested is SKIPPED and reported (never re-added). Per-doc failure = record and
continue. Stdlib + pyyaml + dixie. Max OAuth irrelevant — zero model calls.
"""
from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kg import eventlog, manifest                                   # noqa: E402
from dixie.evidence.config import load_config as dixie_config       # noqa: E402
from dixie.evidence.eventlog import EventLog as DixieLog            # noqa: E402
from dixie.evidence.manifest import build_manifest, normalize_url   # noqa: E402
from dixie.evidence.sweep import Sweep                              # noqa: E402

FETCH_REGISTER = REPO / "corpus" / "staging" / "inbox" / "kernel" / "_fetch_register.json"
KERNEL_DIR = REPO / "corpus" / "kernel"
EPOCH = "kernel-v03"
SOURCE_ID = "kernel_list_2026-08-21"
TASK = "cc_tasks/2026-08-21_v03_visibility_kernel.md"
REQUIRED = ("doc_id", "title", "primary_url", "source_type", "clause", "local_path",
            "sha256", "chars", "retrieved_at_utc", "candidate_status")


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_register() -> list[dict]:
    if not FETCH_REGISTER.is_file():
        raise SystemExit(f"FATAL: fetch register not found: {FETCH_REGISTER} (Phase 2 output)")
    doc = json.loads(FETCH_REGISTER.read_text(encoding="utf-8"))
    recs = doc.get("records") if isinstance(doc, dict) else doc
    items = list(recs.values()) if isinstance(recs, dict) else recs
    if not isinstance(items, list):
        raise SystemExit("FATAL: fetch register must be a list or {records: {...}}")
    for it in items:
        # only fetched items need file/hash fields; excluded/failed carry nulls by design
        need = REQUIRED if it.get("candidate_status") == "fetched" else ("doc_id", "candidate_status")
        missing = [k for k in need if it.get(k) in (None, "")]
        if missing:
            raise SystemExit(f"FATAL: register item {it.get('doc_id')!r} missing {missing}")
    return items


def existing_identity() -> tuple[set[str], set[str], set[str]]:
    ids, shas, urls = set(), set(), set()
    for ev in eventlog.replay():
        if ev.get("event_type") == "manifest_add":
            p = ev["payload"]
            ids.add(p["doc_id"]); shas.add(p["content_hash"])
            urls.add(manifest._normalize_url(p["primary_url"]))
    return ids, shas, urls


def kernel_members_from_events(batch: int) -> list[tuple[str, str]]:
    """(doc_id, local_path) for every manifest_add in the kernel shard."""
    shard = REPO / "events" / f"batch-{batch:03d}.jsonl"
    out = []
    for line in shard.read_text(encoding="utf-8").splitlines():
        ev = json.loads(line)
        if ev.get("event_type") == "manifest_add":
            out.append((ev["payload"]["doc_id"], ev["payload"]["local_path"]))
    return out


def run(batch: int, dry_run: bool, finalize: bool = False) -> int:
    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    if "kernel" not in cfg["document_dirs"]:
        raise SystemExit("FATAL: dixie_evidence.yaml document_dirs must include 'kernel'")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    items = load_register()
    ids, shas, urls = existing_identity()
    manifest._MANIFEST_BATCH = batch   # module global, read at call time (see kg/manifest.py)

    added, skipped, deferred = [], [], []
    KERNEL_DIR.mkdir(parents=True, exist_ok=True)
    if finalize:
        # Resume after a crash between the manifest_add events and the sweep/epoch step:
        # members come from the shard, nothing is re-added or re-imported.
        added = kernel_members_from_events(batch)
        items = []
    for it in items:
        doc_id = it["doc_id"]
        if it["candidate_status"] != "fetched":
            deferred.append((doc_id, f"candidate_status={it['candidate_status']}"))
            continue
        src = REPO / it["local_path"]
        if not src.is_file():
            deferred.append((doc_id, f"file missing: {it['local_path']}")); continue
        sha = _sha256(src)
        if sha != it["sha256"]:
            deferred.append((doc_id, f"sha256 mismatch vs register ({sha[:12]} != {it['sha256'][:12]})"))
            continue
        norm_url = manifest._normalize_url(it["primary_url"])
        if doc_id in ids:
            skipped.append((doc_id, "already manifested: doc_id")); continue
        if sha in shas:
            skipped.append((doc_id, "already manifested: content_hash")); continue
        if norm_url in urls:
            skipped.append((doc_id, "already manifested: primary_url")); continue
        if int(it["chars"]) > 250_000 and not it.get("extent_note"):
            deferred.append((doc_id, "oversize without extent_note (AUTH-4)")); continue

        dest = KERNEL_DIR / f"{doc_id}{src.suffix.lower()}"
        if dry_run:
            added.append((doc_id, f"would add -> {dest.relative_to(REPO)}")); continue
        if dest.exists() and _sha256(dest) != sha:
            deferred.append((doc_id, f"destination exists with different content: {dest}")); continue
        if not dest.exists():
            shutil.move(str(src), str(dest))
        rel = dest.relative_to(REPO).as_posix()

        # 2. dixie ledger identity + decision (clause = the rule match, AUTH-2)
        rationale = (f"kernel inclusion rule clause ({it['clause']}): {it.get('task_item') or ''} — "
                     f"{it.get('task_note') or it.get('extent_note') or 'see ' + TASK}")
        dlog.append("screening_imported", {
            "import_key": doc_id,
            "normalized": {
                "source_id": SOURCE_ID, "doc_id": doc_id, "doc_id_exact": True,
                "title": it["title"], "authors_or_org": it.get("authors_or_org") or it.get("authors") or ["(unspecified)"],
                "pub_year": it.get("as_of") or "n.d.", "doc_type": it["source_type"],
                "source_url": it["primary_url"], "local_path": rel, "expected_sha256": sha,
                "acquisition_method": it.get("fetch_method") or "scripted_fetch",
                "acquired_by": "scripts/harvest_kernel.py",
                "decision": "included", "rationale": rationale,
                "decided_by": "cc", "decided_at": _now(),
                "notes": it.get("extent_note"),
            }})

        # 3. manifest_add (the extraction-admission gate) with full acquisition evidence
        acquisition = {
            "acquisition_method": it.get("fetch_method") or "scripted_fetch",
            "clause": it["clause"],
            "as_of": it.get("as_of"),
            "as_of_source": it.get("as_of_source"),
            "test": {"primary_url": it["primary_url"], "final_url": it.get("final_url"),
                     "urls_tried": it.get("urls_tried"),
                     "http_status": it.get("http_status"),
                     "retrieved_at_utc": it["retrieved_at_utc"],
                     "tool": "scripts/harvest_kernel.py"},
            "evaluation": {"identity_check": "pass",
                           "note": "not previously manifested by doc_id, sha256 or primary_url"},
            "verification": {"sha256": sha},
            "validation": {"chars": int(it["chars"]), "bytes": dest.stat().st_size,
                           "format": dest.suffix.lstrip(".")},
            "task": TASK,
        }
        if it.get("extent_note"):
            acquisition["extent_note"] = it["extent_note"]
            acquisition["excluded_sections"] = it.get("extent_dropped_sections") or []
        try:
            manifest.add(
                str(dest), doc_id=doc_id, title=it["title"],
                authors=it.get("authors_or_org") or it.get("authors") or ["(unspecified)"],
                pub_date=str(it.get("as_of") or "n.d."), source_type=it["source_type"],
                primary_url=it["primary_url"], inclusion_rationale=rationale,
                discovered_via=SOURCE_ID, acquisition=acquisition)
        except manifest.ManifestError as exc:
            deferred.append((doc_id, f"manifest gate rejected: {exc}")); continue
        ids.add(doc_id); shas.add(sha); urls.add(norm_url)
        added.append((doc_id, rel))

    if dry_run:
        for d, why in added: print("ADD     ", d, why)
        for d, why in skipped: print("SKIP    ", d, why)
        for d, why in deferred: print("DEFER   ", d, why)
        return 0

    # sweep: file_observed + integrity_checked for the new files; quarantine failures
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
    if members:
        dlog.append("corpus_epoch_declared", {
            "epoch": EPOCH, "member_doc_ids": sorted(members),
            "declared_by": "cc", "task": TASK,
            "note": "machine-visibility kernel, schema v0.3; rule-based adds per AUTH-2"})
    manifest.rebuild()
    print(f"sweep: {actions}")
    print(f"added {len(added)} | skipped {len(skipped)} | deferred {len(deferred)} | "
          f"epoch {EPOCH} members {len(members)}")
    summary = {"added": added, "skipped": skipped, "deferred": deferred,
               "epoch": EPOCH, "members": sorted(members), "batch": batch, "ts": _now()}
    out = REPO / "docs" / "research" / "2026-08-21_v03_phase3_manifest_summary.json"
    out.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("summary:", out.relative_to(REPO))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=6, help="event shard for manifest_add (kernel profile = 6)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--finalize", action="store_true",
                    help="skip adds; run sweep + corpus_epoch_declared + rebuild for the "
                         "manifest_add events already in the shard")
    a = ap.parse_args()
    return run(a.batch, a.dry_run, finalize=a.finalize)


if __name__ == "__main__":
    raise SystemExit(main())
