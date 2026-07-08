#!/usr/bin/env python3
"""The manifest: the single gate through which a document becomes corpus (DD-003).

Nothing skips this gate. Harvesters and manual finds are inert until an explicit
``manifest_add`` event exists (schema_v0.1.md §7). ``corpus/manifest.json`` is a projection
rebuilt by replaying those events — the event log is the source of truth (DD-008), the JSON
file is disposable and regenerable.

The gate validates provenance, hashes the stored file, and rejects duplicates before any
event is written, so the log never carries a manifest_add it would have to retract. Discovery
attribution (``discovered_via``) is recorded but never confers provenance authority — that
stays with ``primary_url``, the citable primary source (DD-002). Stdlib only.

CLI:
    python -m kg.manifest add <file> --doc-id ... --title ... --authors ... \\
        --pub-date ... --source-type ... --url ... --rationale ... [--discovered-via ...]
    python -m kg.manifest rebuild
    python -m kg.manifest verify
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from kg import eventlog

# Paths are module globals (read at call time) so tests can redirect them onto tmp_path,
# mirroring the eventlog pattern. Do not inline these into function bodies.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_CORPUS_DIR = _REPO_ROOT / "corpus"
_MANIFEST_PATH = _CORPUS_DIR / "manifest.json"
# Stage-0 rewire (task 2026-07-05_airkg_bulk_extraction_v1): manifest.json is the
# projection of the DIXIE EVIDENCE LEDGER, configured here. The manifest_add event
# stream (batch 1) remains the extraction-admission gate; the evidence ledger is the
# corpus ledger. rebuild() projects from the ledger — never from manifest_add events.
_DIXIE_CONFIG_PATH = _REPO_ROOT / "dixie_evidence.yaml"

# manifest_add events all land in one ingest shard. Sharding (DD-008) is by ingest batch;
# the manifest is a single logical stream, so a fixed shard keeps it self-contained and
# rebuild-order stable. Named constant, not a magic literal, per engineering standard 2.
_MANIFEST_BATCH = 1

_MANIFEST_ADD = "manifest_add"
# Kept in sync with schema.yaml Document.source_type (intergovernmental added 2026-07-03, R1).
_SOURCE_TYPES = ("federal", "academic", "industry", "standard", "intergovernmental")
_DOC_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# Fields the caller must supply (non-empty). local_path and content_hash are computed;
# status defaults to "active"; discovered_via is optional.
_REQUIRED_FIELDS = (
    "doc_id",
    "title",
    "authors",
    "pub_date",
    "source_type",
    "primary_url",
    "inclusion_rationale",
)


class ManifestError(ValueError):
    """A rejected add. Raised loud (standard 4) — the gate never fails silently."""


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------

def _sha256(path: Path) -> str:
    """SHA-256 of a file's bytes, read in chunks."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_url(url: str) -> str:
    """Normalize a URL for duplicate detection: strip whitespace, lowercase scheme+host,
    drop a trailing slash and any fragment. Deliberately conservative — dedup, not
    canonicalization; provenance authority still rides on the stored primary_url."""
    u = url.strip()
    u = u.split("#", 1)[0]
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9+.\-]*://[^/]+)(.*)$", u)
    if m:
        u = m.group(1).lower() + m.group(2)
    return u.rstrip("/")


def _load_entries() -> list[dict]:
    """Current manifest entries, reconstructed from event replay (never read from the JSON
    projection — the log is the truth)."""
    entries: dict[str, dict] = {}
    for ev in eventlog.replay():
        if ev.get("event_type") == _MANIFEST_ADD:
            entry = ev["payload"]
            entries[entry["doc_id"]] = entry
    return list(entries.values())


# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------

def add(filepath, **fields) -> str:
    """Validate, hash, dedup, and admit a document to the corpus. Returns its doc_id.

    Rejections (ManifestError) — checked before any event is written:
      - missing/empty required field
      - file not found, or not under corpus/
      - invalid source_type or malformed doc_id slug
      - duplicate doc_id, content_hash, or normalized primary_url

    On pass: emits a ``manifest_add`` event (event_type + full entry as payload) via
    eventlog.append, then rebuilds manifest.json from replay.

    Optional keyword ``acquisition`` (a dict of TEVV/acquisition evidence) is stored
    verbatim under the entry's ``acquisition`` key when supplied.
    """
    # 1. Required fields present and non-empty.
    missing = []
    for key in _REQUIRED_FIELDS:
        val = fields.get(key)
        if val is None or (isinstance(val, str) and not val.strip()):
            missing.append(key)
    if missing:
        raise ManifestError(f"missing required field(s): {', '.join(missing)}")

    authors = fields["authors"]
    if not isinstance(authors, list) or not authors:
        raise ManifestError("'authors' must be a non-empty list")

    source_type = fields["source_type"]
    if source_type not in _SOURCE_TYPES:
        raise ManifestError(
            f"invalid source_type {source_type!r}; must be one of {', '.join(_SOURCE_TYPES)}"
        )

    doc_id = fields["doc_id"]
    if not _DOC_ID_RE.match(doc_id):
        raise ManifestError(
            f"invalid doc_id {doc_id!r}; must be lowercase, hyphenated slug (e.g. fcsm-25-03)"
        )

    # 2. File must exist and live under corpus/.
    path = Path(filepath).resolve()
    corpus = _CORPUS_DIR.resolve()
    if not path.is_file():
        raise ManifestError(f"file not found: {filepath}")
    if not path.is_relative_to(corpus):
        raise ManifestError(f"file is not under corpus/: {filepath}")

    content_hash = _sha256(path)
    local_path = path.relative_to(_REPO_ROOT.resolve()).as_posix()
    primary_url = fields["primary_url"]
    norm_url = _normalize_url(primary_url)

    # 3. Duplicate checks against the current (replayed) manifest state.
    existing = _load_entries()
    for e in existing:
        if e["doc_id"] == doc_id:
            raise ManifestError(f"duplicate doc_id: {doc_id}")
        if e["content_hash"] == content_hash:
            raise ManifestError(
                f"duplicate content_hash: {content_hash} already held by {e['doc_id']}"
            )
        if _normalize_url(e["primary_url"]) == norm_url:
            raise ManifestError(
                f"duplicate primary_url: {primary_url} already held by {e['doc_id']}"
            )

    # 4. Build the entry (fixed key order) and admit it.
    entry = {
        "doc_id": doc_id,
        "title": fields["title"],
        "authors": authors,
        "pub_date": fields["pub_date"],
        "source_type": source_type,
        "primary_url": primary_url,
        "local_path": local_path,
        "content_hash": content_hash,
        "inclusion_rationale": fields["inclusion_rationale"],
        "discovered_via": fields.get("discovered_via"),
        "status": "active",
    }
    # Optional acquisition/TEVV evidence (fetch provenance, identity check, page count,
    # re-hash confirmation). Carried in the event so the audit trail is self-contained;
    # omitted entirely when not supplied so pre-existing entries stay unchanged.
    if fields.get("acquisition") is not None:
        entry["acquisition"] = fields["acquisition"]
    eventlog.append({"event_type": _MANIFEST_ADD, "payload": entry}, batch=_MANIFEST_BATCH)
    # Stage-0 rewire: add() no longer auto-rebuilds manifest.json. The file is the
    # evidence-ledger projection; refreshing it here would overwrite v2 with state the
    # ledger hasn't recorded yet. After an add, run the Dixie sweep
    # (`dixie-evidence verify --config dixie_evidence.yaml`) to ledger the file, then
    # `python -m kg.manifest rebuild` (or the sweep itself) to refresh the projection.
    return doc_id


def rebuild() -> dict:
    """Regenerate corpus/manifest.json (v2) FROM THE DIXIE EVIDENCE DECISIONS LOG.

    Stage-0 rewire (task 2026-07-05_airkg_bulk_extraction_v1): the decisions log at
    corpus/evidence/decisions.jsonl is truth; this file is its projection. Byte-stable
    on unchanged input (the projection stamps the last event's timestamp, never
    wall-clock). Raises ManifestError — loudly, never a silent no-op — if the dixie
    package or the config instance is missing."""
    try:
        from dixie.evidence.config import load_config as _dixie_load_config
        from dixie.evidence.eventlog import EventLog as _DixieEventLog
        from dixie.evidence.manifest import (
            build_manifest as _dixie_build_manifest,
            last_event_ts as _dixie_last_event_ts,
            write_manifest_json as _dixie_write_manifest_json,
        )
    except ImportError as exc:
        raise ManifestError(
            "corpus/manifest.json is the projection of the Dixie evidence ledger; "
            "rebuilding it requires the 'dixie' package (pip install -e ~/GitHub/dixie). "
            "See cc_tasks/2026-07-05_airkg_bulk_extraction_v1.md Stage 0."
        ) from exc
    if not _DIXIE_CONFIG_PATH.is_file():
        raise ManifestError(
            f"dixie config instance not found: {_DIXIE_CONFIG_PATH} — manifest.json is "
            "the evidence-ledger projection and cannot be rebuilt without it. "
            "See cc_tasks/2026-07-05_airkg_bulk_extraction_v1.md Stage 0."
        )
    cfg = _dixie_load_config(_DIXIE_CONFIG_PATH)
    log = _DixieEventLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    # identity gate (source-access tactical Stage 1): a record whose signals fail the
    # declared thresholds cannot project as `included`. None-safe (pre-gate corpora).
    entries = _dixie_build_manifest(log, gate_cfg=cfg.get("identity_gate"))
    _dixie_write_manifest_json(entries, _MANIFEST_PATH, cfg["project"],
                               generated_at=_dixie_last_event_ts(log))
    return {"manifest_version": 2, "entries": len(entries)}


def verify() -> list[dict]:
    """Re-hash every entry's local_path and report problems. Empty list = clean.

    Each problem is {doc_id, local_path, issue, [expected, actual]} where issue is
    'missing' (file gone) or 'hash_mismatch' (content changed since add)."""
    problems: list[dict] = []
    for entry in _load_entries():
        local_path = entry["local_path"]
        path = (_REPO_ROOT.resolve() / local_path)
        if not path.is_file():
            problems.append(
                {"doc_id": entry["doc_id"], "local_path": local_path, "issue": "missing"}
            )
            continue
        actual = _sha256(path)
        if actual != entry["content_hash"]:
            problems.append({
                "doc_id": entry["doc_id"],
                "local_path": local_path,
                "issue": "hash_mismatch",
                "expected": entry["content_hash"],
                "actual": actual,
            })
    return problems


# --------------------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m kg.manifest",
        description="The corpus manifest gate (DD-003).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Admit a document to the corpus.")
    p_add.add_argument("file", help="Path to the stored copy (must be under corpus/).")
    p_add.add_argument("--doc-id", required=True, help="Lowercase hyphenated slug, e.g. fcsm-25-03.")
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--authors", required=True, help="Comma-separated list.")
    p_add.add_argument("--pub-date", required=True, help="ISO date or year.")
    p_add.add_argument("--source-type", required=True, choices=_SOURCE_TYPES)
    p_add.add_argument("--url", required=True, help="Citable primary source URL.")
    p_add.add_argument("--rationale", required=True, help="Inclusion rationale (1-2 sentences).")
    p_add.add_argument("--discovered-via", default=None, help="Capture provenance, e.g. manual.")

    sub.add_parser("rebuild", help="Rebuild manifest.json from the event log.")
    sub.add_parser("verify", help="Re-hash all entries; report missing/tampered files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command == "add":
        authors = [a.strip() for a in args.authors.split(",") if a.strip()]
        try:
            doc_id = add(
                args.file,
                doc_id=args.doc_id,
                title=args.title,
                authors=authors,
                pub_date=args.pub_date,
                source_type=args.source_type,
                primary_url=args.url,
                inclusion_rationale=args.rationale,
                discovered_via=args.discovered_via,
            )
        except ManifestError as exc:
            print(f"REJECTED: {exc}", file=sys.stderr)
            return 1
        print(f"added: {doc_id}")
        return 0

    if args.command == "rebuild":
        manifest = rebuild()
        print(f"rebuilt {_MANIFEST_PATH} (v{manifest['manifest_version']} evidence-ledger "
              f"projection) with {manifest['entries']} entrie(s)")
        return 0

    if args.command == "verify":
        problems = verify()
        if not problems:
            print("clean: all local files present and unchanged")
            return 0
        for p in problems:
            print(f"PROBLEM [{p['issue']}] {p['doc_id']} -> {p['local_path']}", file=sys.stderr)
        return 1

    return 2  # unreachable: subparser is required


if __name__ == "__main__":
    raise SystemExit(main())
