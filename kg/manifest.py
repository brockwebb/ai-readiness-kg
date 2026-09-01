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
_CONTENT_UPDATE = "content_update"
#: Why a document's bytes were legitimately replaced after admission. Closed, because an
#: open reason field is how "the file changed" becomes an explanation instead of a finding.
#: `extent_corrected` — the admitted copy was the wrong extent (a whole statute standing in
#: for one section); `corrupt_source_replaced` — the admitted bytes would not parse;
#: `source_revised` — the publisher silently reissued the document at the same URL;
#: `source_unavailable_disk_adopted` — the primary URL is dead and the disk copy is adopted
#: as the record of what was read, with provenance degraded.
_CONTENT_UPDATE_REASONS = ("extent_corrected", "corrupt_source_replaced", "source_revised",
                           "source_unavailable_disk_adopted")
# Kept in sync with schema.yaml Document.source_type (intergovernmental added 2026-07-03, R1;
# practitioner added 2026-08-21, schema v0.3 / DD-009 — SME or industry-practitioner guidance
# that is not a vendor product page).
_SOURCE_TYPES = ("federal", "academic", "industry", "standard", "intergovernmental", "practitioner")
# Kept in sync with schema.yaml Document.construct_arm / Document.grounding_surface
# (both added 2026-08-24, schema v0.3.3, task 2026-08-24_source_triage). Optional on add():
# construct_arm is required BY that task's rule on its own adds, not by the gate — older
# entries are backfilled via document_annotation events, never re-manifested.
_CONSTRUCT_ARMS = ("publication_actionability", "training_data_readiness", "org_maturity")
_GROUNDING_SURFACES = ("document", "transcript", "slides")
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
    projection — the log is the truth).

    `content_update` events are replayed OVER the admission entry. A document can be
    legitimately re-acquired after admission — wrong extent corrected, corrupt PDF replaced
    — and the corrected bytes then differ from the hash `manifest_add` recorded. That is not
    drift, and the fix is never an edit to the admission event (invariant 1): the entry's
    current hash is the admission hash with each supersession applied in log order.
    """
    entries: dict[str, dict] = {}
    #: Applied after the full replay, because SHARD order is not causal order. `replay()`
    #: yields shards by batch number (DD-008 shards by INGEST batch), so a supersession
    #: written to shard 1 for a document admitted on shard 17 arrives before its own
    #: admission. That happened: the crosswalk lane's admissions live on batch-017, and the
    #: first `content_update` written for one of them made every call to this function raise.
    #: The guard's intent is "no admission EXISTS", not "none seen yet in shard order", and
    #: it still raises below for a genuinely orphaned supersession.
    deferred_updates: list[dict] = []
    for ev in eventlog.replay():
        et = ev.get("event_type")
        if et == _MANIFEST_ADD:
            entry = dict(ev["payload"])
            entries[entry["doc_id"]] = entry
        elif et == _CONTENT_UPDATE:
            deferred_updates.append(ev["payload"])
    for p in deferred_updates:
        base = entries.get(p["doc_id"])
        if base is None:
            # A supersession with no admission ANYWHERE is a corrupt log, not a recoverable
            # state: the entry it claims to correct was never admitted.
            raise ManifestError(
                f"content_update for {p['doc_id']!r} which has no manifest_add event")
        base["content_hash"] = p["content_hash"]
        if p.get("local_path"):
            base["local_path"] = p["local_path"]
        base.setdefault("supersessions", []).append(
            {k: p.get(k) for k in ("superseded_content_hash", "content_hash",
                                   "reason", "evidence", "task")})
    return list(entries.values())


# --------------------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------------------

def _convertibility_gate(doc_id: str, src: Path, entry: dict) -> None:
    """DD-030 at the admission boundary: detection at admission, not in a batch pass.

    `kg.ingest.gate` was built as a corpus-wide sweep (`python -m kg.ingest.gate`), which
    finds a gap in a document admitted last week and none at all in one admitted a minute
    ago. The rule DD-030 installs says *admission* requires convertibility, and this module
    is the only gate into the corpus (project invariant 2), so the check belongs here — a
    sweep someone has to remember to run is the same class of defect as the burn-time
    discovery it replaced.

    Called AFTER the `manifest_add` event and never raising `ManifestError`, because rule (c)
    says a document that cannot be converted is still ADMITTED: refusing would lose a
    document the operator deliberately acquired. The `conversion_gap` event and its
    auto-registered ResearchTask are how the system says the substrate is missing.

    PDFs are delegated to the existing T1 path and are not gapped for a conversion this
    module was never asked to do. The import is local: `kg.ingest.convert` is only needed on
    an add, and `kg.manifest` is imported by every projection and CLI path in the repo.

    An unexpected failure inside the gate propagates. The document IS admitted at that point
    — its event is on the log — and a loud failure naming the document is recoverable by
    `python -m kg.ingest.gate --doc <id>`. Swallowing it would leave a document that looks
    admitted-and-converted while no substrate exists, which is the silent admission this
    whole rule exists to forbid.
    """
    from kg.ingest import convert as _convert, gate as _gate
    if src.suffix.lower() in _convert.DELEGATED:
        return
    _gate.check(doc_id, src, {"source_url": entry.get("primary_url"),
                              "version": entry.get("pub_date")})


def duplicate_adds() -> dict[str, dict]:
    """Log-integrity audit: doc_ids carrying more than one `manifest_add` event.

    `add()` has always refused a duplicate doc_id, and it still does. What it cannot refuse is
    an event written straight to a shard without going through it — and that is what happened
    once, on 2026-08-14, for `introducing-the-oecd-ai-capability-indicators`. That add was an
    operator-cleared EXTENT CORRECTION (CLEARANCE 2, `cc_tasks/2026-08-14_bulk_v1_closeout.md`):
    the corpus held a crawl4ai capture of `component-5.html`, one component of a 56-page OECD
    report, and the full PDF replaced it. The event says so on its face and names the hash it
    replaces in `acquisition.verification.supersedes_sha256`.

    It was written that way because **`content_update` did not exist until 2026-08-29**, fifteen
    days later. With no sanctioned supersession event, the only alternatives were editing the
    admission event (forbidden, invariant 1) or leaving the corpus holding the wrong extent. A
    second `manifest_add` was the least-bad option available at the time, and it lands the right
    state: `_load_entries()` replays in shard order, so the later entry wins.

    So this function is not a duplicate *detector* looking for a bug that got past a guard. It
    is the log-level invariant that `add()`'s per-call check cannot express, and it distinguishes
    an EXPLAINED duplicate (the later event declares what it supersedes) from an unexplained one,
    which is a corrupt log. Today the same correction is a `content_update` with
    `reason="extent_corrected"`, and no new duplicate should ever appear.
    """
    by_doc: dict[str, list[dict]] = {}
    for ev in eventlog.replay():
        if ev.get("event_type") == _MANIFEST_ADD:
            by_doc.setdefault(ev["payload"]["doc_id"], []).append(ev)
    out = {}
    for doc_id, evs in by_doc.items():
        if len(evs) < 2:
            continue
        later = evs[-1]
        acq = (later["payload"].get("acquisition") or {})
        supersedes = (acq.get("verification") or {}).get("supersedes_sha256")
        rationale = later["payload"].get("inclusion_rationale") or ""
        explained = bool(supersedes) or "supersede" in rationale.lower()
        out[doc_id] = {
            "doc_id": doc_id, "n_adds": len(evs),
            "event_ids": [e["event_id"] for e in evs],
            "timestamps": [e["timestamp"] for e in evs],
            "content_hashes": [e["payload"]["content_hash"] for e in evs],
            "explained": explained,
            "supersedes_sha256": supersedes,
            "rationale": rationale,
            "effective_entry": later["payload"]["local_path"],
        }
    return out


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

    # v0.3.3 optional Document fields — validated against the schema enums when supplied.
    construct_arm = fields.get("construct_arm")
    if construct_arm is not None and construct_arm not in _CONSTRUCT_ARMS:
        raise ManifestError(
            f"invalid construct_arm {construct_arm!r}; must be one of {', '.join(_CONSTRUCT_ARMS)}"
        )
    grounding_surface = fields.get("grounding_surface")
    if grounding_surface is not None and grounding_surface not in _GROUNDING_SURFACES:
        raise ManifestError(
            f"invalid grounding_surface {grounding_surface!r}; must be one of "
            f"{', '.join(_GROUNDING_SURFACES)}"
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
    # v0.3.3 Document fields — carried in the event only when supplied, so pre-existing
    # entries (and their replays) stay byte-identical.
    if construct_arm is not None:
        entry["construct_arm"] = construct_arm
    if grounding_surface is not None:
        entry["grounding_surface"] = grounding_surface
    # Optional acquisition/TEVV evidence (fetch provenance, identity check, page count,
    # re-hash confirmation). Carried in the event so the audit trail is self-contained;
    # omitted entirely when not supplied so pre-existing entries stay unchanged.
    if fields.get("acquisition") is not None:
        entry["acquisition"] = fields["acquisition"]
    eventlog.append({"event_type": _MANIFEST_ADD, "payload": entry}, batch=_MANIFEST_BATCH)
    _convertibility_gate(doc_id, path, entry)
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


def _admission_shard(doc_id: str) -> int:
    """The shard holding this document's `manifest_add`, so a supersession lands beside the
    admission it corrects rather than always on shard 1.

    DD-008 shards by INGEST batch, so admissions are spread across shards — the crosswalk
    lane's live on batch-017. `_MANIFEST_BATCH` was written when shard 1 held every
    admission, and it quietly stopped being true, because no document outside shard 1 had
    ever been superseded. `_load_entries` is order-tolerant now, so this is coherence rather
    than correctness: a reader following one document should not have to know its history is
    split across two shards for no reason."""
    pat = re.compile(r"batch-(\d+)$")
    for shard in sorted((q for q in eventlog._EVENTS_DIR.glob("batch-*.jsonl")
                         if pat.fullmatch(q.stem)),
                        key=lambda q: int(pat.fullmatch(q.stem).group(1))):
        for line in shard.read_text(encoding="utf-8").splitlines():
            if doc_id not in line or _MANIFEST_ADD not in line:
                continue
            ev = json.loads(line)
            if (ev.get("event_type") == _MANIFEST_ADD
                    and (ev.get("payload") or {}).get("doc_id") == doc_id):
                return int(pat.fullmatch(shard.stem).group(1))
    return _MANIFEST_BATCH


def content_update(doc_id: str, *, reason: str, superseded_content_hash: str,
                   evidence: dict, local_path: str | None = None,
                   task: str | None = None) -> str:
    """Record that an admitted document's bytes were legitimately replaced. Returns the new
    content hash.

    This is the ONLY sanctioned way for an entry's hash to change. The admission event is
    never edited (invariant 1): a `content_update` event is appended and replayed over it.

    Loud refusals, all checked before anything is written:
      - `doc_id` was never admitted
      - `reason` outside the closed list
      - `superseded_content_hash` is not the entry's CURRENT hash — the caller must name
        what it believes it is replacing and be right, because blind chaining is how a
        supersession silently adopts whatever happens to be on disk
      - the file is missing
    """
    entries = {e["doc_id"]: e for e in _load_entries()}
    entry = entries.get(doc_id)
    if entry is None:
        raise ManifestError(f"content_update: {doc_id!r} is not admitted")
    if reason not in _CONTENT_UPDATE_REASONS:
        raise ManifestError(
            f"content_update: unknown reason {reason!r}; must be one of "
            f"{', '.join(_CONTENT_UPDATE_REASONS)}")
    if superseded_content_hash != entry["content_hash"]:
        raise ManifestError(
            f"content_update: superseded_content_hash {superseded_content_hash[:12]}... does "
            f"not match the current hash {entry['content_hash'][:12]}... for {doc_id!r}")
    rel = local_path or entry["local_path"]
    path = _REPO_ROOT.resolve() / rel
    if not path.is_file():
        raise ManifestError(f"content_update: file not found: {rel}")
    new_hash = _sha256(path)
    if new_hash == superseded_content_hash:
        raise ManifestError(
            f"content_update: {doc_id!r} bytes are unchanged; nothing to supersede")
    # Same envelope shape as manifest_add: the entry state lives under `payload`, so one
    # replay rule reads both event types.
    eventlog.append({"event_type": _CONTENT_UPDATE,
                     "payload": {"doc_id": doc_id, "content_hash": new_hash,
                                 "superseded_content_hash": superseded_content_hash,
                                 "local_path": rel, "reason": reason,
                                 "evidence": evidence,
                                 **({"task": task} if task else {})}},
                    batch=_admission_shard(doc_id))
    return new_hash


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
