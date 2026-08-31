#!/usr/bin/env python3
"""Extraction queue — admitted → prioritized → extracted, one status surface.

Task `cc_tasks/2026-08-27_extraction_queue.md` with ADDENDUM-01 (binding; it wins on conflict).

The operator wants three sentences true at any moment, from one command, from the ledger:
what is in the corpus and why, whether each admitted document has been extracted and under
what, and what runs next in what order. Two of the three already existed as events
(`manifest_add`; the extraction events). The third — a deliberate, prioritized *request*,
separate from admission — did not.

**Admission is not a request.** Curation pipelines that work at scale keep those stages apart
(Wikidata proposal → review → ingest; UniProt triage → curate), and that separation is what
lets spend follow priority instead of arrival order.

Everything here is DERIVED from the append-only event log plus the spend ledger. Nothing in
this module is a source of truth; delete every projection and it rebuilds.
"""
from __future__ import annotations

import collections
import datetime
import json
import os
from pathlib import Path

from . import eventlog

_REPO = Path(__file__).resolve().parent.parent
#: Read at call time so tests can repoint them (repo convention for module path globals).
_MANIFEST_PATH = _REPO / "corpus/manifest.json"
_PROFILES_PATH = _REPO / "scripts/run_profiles.yaml"
_LEDGER_PATH = _REPO / "state/spend_ledger.jsonl"

#: The graph shard these events live on. Untagged: the queue is part of the graph's history,
#: not an experiment arm.
QUEUE_BATCH = 22

REQUEST = "extraction_request"
WITHDRAWN = "extraction_withdrawn"
#: A deliberate decision NOT to extract an admitted document (task
#: 2026-08-30_bulk_extraction_v038 Phase 0.3). Distinct from WITHDRAWN, which cancels a
#: request that was actually made, and distinct from `not_requested`, which means only that
#: nobody has looked yet. "Admitted, considered, and declined, for this reason" is a third
#: thing, and the operator surface has to be able to tell it from the other two.
DEFERRED = "extraction_deferred"

#: Projected states. Order is the reporting order in `kg queue status`.
STATES = ("extracting", "queued", "stale", "extracted", "failed",
          "skipped_oversize", "deferred", "not_requested", "excluded")


class QueueRefusal(RuntimeError):
    """A request that must not become an event. Carries the reason the operator needs."""


# ---------------------------------------------------------------- sources
def included_documents() -> dict[str, dict]:
    """{doc_id: manifest entry} for admitted documents.

    Read from the manifest PROJECTION, which CLAUDE.md makes the corpus ledger since the
    Stage-0 rewire, and reconciled against `manifest_add` events by `status_totals`. Note the
    erratum recorded 2026-08-30: `source_type` is what you pass to the admission API,
    `doc_type` is what you read back here. Neither is renamed."""
    if not _MANIFEST_PATH.is_file():
        return {}
    entries = (json.loads(_MANIFEST_PATH.read_text(encoding="utf-8")).get("entries") or {})
    rows = entries.values() if isinstance(entries, dict) else entries
    return {r["doc_id"]: r for r in rows
            if (r.get("screening") or {}).get("decision") == "included"}


def manifest_added_ids() -> set[str]:
    """Distinct doc_ids with a `manifest_add` event — the admission gate's own record."""
    out = set()
    for ev in eventlog.replay():
        if ev.get("event_type") == "manifest_add":
            doc = ev.get("doc_id") or (ev.get("payload") or {}).get("doc_id")
            if doc:
                out.add(doc)
    return out


def profiles() -> dict[str, dict]:
    import yaml
    return (yaml.safe_load(_PROFILES_PATH.read_text(encoding="utf-8")) or {}).get("profiles", {})


def pinned_profile() -> str:
    """The currently pinned profile, READ AT CALL TIME from the pin source.

    ADDENDUM-01 §4: never capture this as a constant. The production profile moved from `v1`
    to a v0.3.x arm while this task was being written, and a projection holding a captured pin
    would keep reporting documents as `extracted` after the thing they were extracted under
    stopped being current. Flipping the pin must flip `extracted` -> `stale` with no code
    change; there is a test for exactly that."""
    import yaml
    doc = yaml.safe_load(_PROFILES_PATH.read_text(encoding="utf-8")) or {}
    return doc.get("default") or ""


def profile_for(corpus_epoch: str | None, prompt_version: str | None) -> tuple[str | None, bool]:
    """(profile name, ambiguous?) for an extraction's recorded provenance.

    Legacy extraction events predate profiles and record only `corpus_epoch`. Several profiles
    can share an epoch (`reextract_v034`/`reextract_v035`; the four chunked arms), so epoch
    alone does not identify a profile. `prompt_version` disambiguates where present. Where it
    cannot, the profile is reported as unknown AND flagged ambiguous — never guessed, because a
    guessed profile silently decides `extracted` vs `stale`."""
    if not corpus_epoch:
        return None, False
    candidates = [n for n, p in profiles().items() if p.get("corpus_epoch") == corpus_epoch]
    if len(candidates) == 1:
        return candidates[0], False
    if not candidates:
        return None, False
    if prompt_version:
        exact = [n for n in candidates
                 if str(profiles()[n].get("prompt_version") or "") == str(prompt_version)]
        if len(exact) == 1:
            return exact[0], False
    return None, True


# ---------------------------------------------------------------- events
def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def request(document_id: str, priority: int, requested_by: str, reason: str,
            profile: str | None = None, superseding: bool = False) -> str:
    """Emit one `extraction_request`. Preconditions are enforced HERE, at emit.

    A refusal is a refusal with a reason, not an event: an `extraction_request` for a document
    the corpus never admitted would put a worklist entry on an append-only log that no
    manifest decision backs."""
    included = included_documents()
    if document_id not in included:
        raise QueueRefusal(
            f"{document_id!r} is not manifest-included; admission precedes request "
            f"(refused, not emitted). Admit it via kg.manifest first.")
    prof = profile or pinned_profile()
    known = profiles()
    if prof not in known:
        raise QueueRefusal(f"profile {prof!r} is not in scripts/run_profiles.yaml")
    if not known[prof].get("template_sha256"):
        raise QueueRefusal(
            f"profile {prof!r} is not sha-pinned; refusing to queue work against a prompt "
            f"that can drift under it")
    if int(priority) < 0:
        raise QueueRefusal(f"priority must be >= 0, got {priority}")
    return eventlog.append({
        "event_type": REQUEST, "document_id": document_id, "priority": int(priority),
        "requested_by": requested_by, "reason": reason, "profile": prof,
        "superseding": bool(superseding), "ts": _now()}, batch=QUEUE_BATCH)


def defer(document_id: str, reason: str) -> str:
    """Emit one `extraction_deferred`. Same admission precondition as `request`.

    Refuses while a live request stands: silently deferring queued work would make the
    worklist and the status surface disagree about the same document. Withdraw first, then
    defer — two events, because they are two decisions."""
    if document_id not in included_documents():
        raise QueueRefusal(
            f"{document_id!r} is not manifest-included; there is nothing to defer "
            f"(refused, not emitted).")
    if not reason:
        raise QueueRefusal("a deferral without a reason is an unexplained gap in the corpus")
    if document_id in live_requests():
        raise QueueRefusal(
            f"{document_id!r} has a live extraction_request; withdraw it before deferring")
    return eventlog.append({"event_type": DEFERRED, "document_id": document_id,
                            "reason": reason, "ts": _now()}, batch=QUEUE_BATCH)


def deferrals() -> dict[str, dict]:
    """{doc_id: live deferral}. A later request revives the document; ordinary replay."""
    out: dict[str, dict] = {}
    for ev in eventlog.replay():
        t = ev.get("event_type")
        doc = ev.get("document_id")
        if not doc:
            continue
        if t == DEFERRED:
            out[doc] = ev
        elif t == REQUEST:
            out.pop(doc, None)
    return out


def withdraw(document_id: str, reason: str) -> str:
    return eventlog.append({"event_type": WITHDRAWN, "document_id": document_id,
                            "reason": reason, "ts": _now()}, batch=QUEUE_BATCH)


def live_requests() -> dict[str, dict]:
    """{doc_id: latest live request}. Latest wins; a withdrawal after the latest request
    cancels it, and a request after a withdrawal revives it — both are ordinary replay."""
    out: dict[str, dict] = {}
    for ev in eventlog.replay():
        t = ev.get("event_type")
        doc = ev.get("document_id")
        if not doc:
            continue
        if t == REQUEST:
            out[doc] = ev
        elif t == WITHDRAWN:
            out.pop(doc, None)
    return out


# ---------------------------------------------------------------- extraction history
def extractions() -> dict[str, list[dict]]:
    """{doc_id: [{profile, corpus_epoch, model_id, prompt_version, ts, extraction_event_id}]}.

    One entry per distinct extraction run over the document, newest last. Derived from the
    provenance the extraction events already carry — nothing new is written to record this."""
    seen: dict[str, dict[str, dict]] = collections.defaultdict(dict)
    for ev in eventlog.replay():
        if ev.get("event_type") not in ("node_asserted", "edge_asserted"):
            continue
        doc = ev.get("doc_id") or ev.get("document_id")
        prov = ev.get("provenance") or {}
        eid = prov.get("extraction_event_id")
        if not doc or not eid or eid in seen[doc]:
            continue
        prof, ambiguous = profile_for(prov.get("corpus_epoch"), prov.get("prompt_version"))
        seen[doc][eid] = {
            "extraction_event_id": eid, "profile": prof, "profile_ambiguous": ambiguous,
            "corpus_epoch": prov.get("corpus_epoch"), "model_id": prov.get("model_id"),
            "prompt_version": prov.get("prompt_version"), "ts": prov.get("timestamp")}
    return {d: sorted(v.values(), key=lambda r: r["ts"] or "") for d, v in seen.items()}


CENSUS = "document_chunk_census"


def chunk_unit_profile(name: str) -> bool:
    """A profile whose extraction unit is the chunk, not the document (DD-023)."""
    return (profiles().get(name) or {}).get("emission_contract") == "anchor"


def chunk_census(profile: str) -> dict[str, int]:
    """{doc_id: chunks the document HAS} as recorded by the run that extracted it."""
    out: dict[str, int] = {}
    for ev in eventlog.replay():
        if ev.get("event_type") == CENSUS and ev.get("profile") == profile:
            if ev.get("document_id") and ev.get("n_chunks"):
                out[ev["document_id"]] = int(ev["n_chunks"])
    return out


def chunk_coverage(profile: str) -> dict[str, set]:
    """{doc_id: distinct chunk_ids ingested} under `profile`."""
    out: dict[str, set] = collections.defaultdict(set)
    for ev in eventlog.replay():
        if ev.get("event_type") == "chunk_metrics" and ev.get("purpose") == profile:
            if ev.get("doc_id") and ev.get("chunk_id"):
                out[ev["doc_id"]].add(ev["chunk_id"])
    return out


def failures() -> dict[str, dict]:
    """{doc_id: {status, count, last}} from the burn driver's own failure events."""
    out: dict[str, dict] = {}
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t not in ("bulk_doc_failed", "bulk_doc_quarantine_high", "bulk_run_stop"):
            continue
        doc = ev.get("doc_id")
        if not doc:
            continue
        rec = out.setdefault(doc, {"status": None, "count": 0, "last": None})
        rec["count"] += 1
        rec["status"] = ev.get("stage") or ev.get("reason") or t
        rec["last"] = ev.get("timestamp")
    return out


def oversize() -> set[str]:
    cleared, skipped = set(), set()
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == "bulk_doc_skipped_oversize" and ev.get("doc_id"):
            skipped.add(ev["doc_id"])
        elif t == "bulk_doc_oversize_cleared" and ev.get("doc_id"):
            cleared.add(ev["doc_id"])
    return skipped - cleared


def in_flight_documents() -> set[str]:
    """Documents with an OUTSTANDING spend reservation — a call is dispatched right now.

    Reservations are per-run; `doc_id` is recorded on them additively (see the RESULT's
    discrepancy note), so reservations written before that change contribute nothing here
    rather than being guessed at."""
    if not _LEDGER_PATH.is_file():
        return set()
    open_res: dict[str, str] = {}
    for line in _LEDGER_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = r.get("reservation_id")
        if not rid:
            continue
        if r.get("record") == "reserve":
            if r.get("doc_id"):
                open_res[rid] = r["doc_id"]
        elif r.get("record") in ("settle", "release", "reservation_released"):
            open_res.pop(rid, None)
    return set(open_res.values())


# ---------------------------------------------------------------- the projection
def project() -> dict[str, dict]:
    """{doc_id: row} for every admitted document. The single derivation every surface reads."""
    pin = pinned_profile()
    included = included_documents()
    reqs, exts, fails = live_requests(), extractions(), failures()
    defers = deferrals()
    # Under a CHUNK-UNIT profile, one extraction event does not mean the document is done.
    # Phase A of the bulk task sampled a single chunk from 25 documents; every one of them
    # then read `extracted`, and the worklist those 25 should have led fell from 33 documents
    # to 10. Completeness is coverage against the census the extracting run recorded.
    chunked = chunk_unit_profile(pin)
    census = chunk_census(pin) if chunked else {}
    coverage = chunk_coverage(pin) if chunked else {}
    over, flying = oversize(), in_flight_documents()
    rows: dict[str, dict] = {}
    for doc, entry in included.items():
        under = exts.get(doc, [])
        req = reqs.get(doc)
        matches_pin = [e for e in under if e["profile"] == pin]
        n_have, n_want = len(coverage.get(doc, ())), census.get(doc, 0)
        # No census recorded => n_want is 0 => `n_have >= 0` is already True, so a legacy
        # chunked run with no census is never called incomplete. An explicit `not n_want`
        # clause was here and could not change the outcome; a mutation deleting it killed no
        # test, which is the definition of code that cannot run. The behaviour it was meant
        # to protect is real and tested — it just falls out of the comparison.
        complete = (not chunked) or n_have >= n_want
        if matches_pin and not complete:
            matches_pin = []
        if doc in flying:
            state = "extracting"
        elif doc in over:
            state = "skipped_oversize"
        elif matches_pin:
            state = "extracted"
        elif under and req and req.get("superseding"):
            state = "queued"
        elif doc in defers:
            # A deferral outranks `stale` but never `extracted`. `stale` is a claim that
            # re-extraction is OWED; a deferral is the decision that it is not. Ranking stale
            # first hid 104 of the 159 documents the bulk_v038 cut declined, which made the
            # cut look four times smaller than it was on the status surface.
            state = "deferred"
        elif under:
            state = "stale"
        elif doc in fails and not req:
            state = "failed"
        elif req:
            state = "queued"
        else:
            state = "not_requested"
        ident = entry.get("identity") or {}
        rows[doc] = {
            "doc_id": doc, "title": ident.get("title") or doc,
            "doc_type": ident.get("doc_type"),
            "manifest_reason": ((entry.get("screening") or {}).get("rationale") or "")[:60],
            "extraction_state": state,
            "extracted_under": under,
            "latest_extraction": under[-1] if under else None,
            "priority": (req or {}).get("priority"),
            "requested_profile": (req or {}).get("profile"),
            "superseding": bool((req or {}).get("superseding")),
            "failure": fails.get(doc),
            "deferred_reason": (defers.get(doc) or {}).get("reason"),
            "chunks_extracted": n_have if chunked else None,
            "chunks_total": n_want or None if chunked else None,
            "pinned_profile": pin,
        }
    return rows


def status_totals() -> dict:
    rows = project()
    counts = collections.Counter(r["extraction_state"] for r in rows.values())
    added = manifest_added_ids()
    return {"pinned_profile": pinned_profile(), "included": len(rows),
            "manifest_add_events": len(added),
            "reconciles": len(added) == len(rows),
            "by_state": {s: counts.get(s, 0) for s in STATES if counts.get(s)},
            "total": sum(counts.values())}


# ---------------------------------------------------------------- epochs / backfill
_DIXIE_DECISIONS = _REPO / "corpus/evidence/decisions.jsonl"


def corpus_epochs() -> dict[str, list[str]]:
    """{epoch: member doc_ids} from the DIXIE evidence ledger.

    Epochs are declared there, not on the event shards — `manifest_add` carries no epoch at
    all, which is why the base task's cohorts could not be derived from `events/` (recorded as
    a discrepancy in the RESULT). `run_bulk_extraction.corpus_members` reads the same source."""
    import json as _json
    out: dict[str, list[str]] = {}
    if not _DIXIE_DECISIONS.is_file():
        return out
    for line in _DIXIE_DECISIONS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            ev = _json.loads(line)
        except _json.JSONDecodeError:
            continue
        if ev.get("event_type") == "corpus_epoch_declared":
            p = ev.get("payload") or {}
            if p.get("epoch"):
                out[p["epoch"]] = p.get("member_doc_ids") or p.get("members") or []
    return out


#: Backfill cohorts (base task §6, corrected on measurement — see the RESULT).
#: An epoch's documents are requested under the profile THEIR OWN epoch belongs to. The base
#: prose put all 134 already-extracted documents under `kernel_v03`; 134 is in fact 71 v1
#: plus 63 kernel-v03, and labelling the 71 with the kernel profile would project them stale
#: against a profile they were never extracted under.
BACKFILL = (
    ("v1", "v1", 50, "extracted under the v1 corpus epoch"),
    ("kernel-v03", "kernel_v03", 50, "kernel epoch; extracted under kernel-v03"),
    ("triage-2026-08-24", "reextract_v035", 10,
     "triage batch; awaiting reextract_v035 pilot pass"),
)


def backfill_plan() -> list[dict]:
    """What `backfill` would emit. Idempotent: a document already carrying a live request is
    skipped, so re-running adds nothing."""
    epochs, live, included = corpus_epochs(), live_requests(), included_documents()
    plan = []
    for epoch, profile, priority, reason in BACKFILL:
        for doc in epochs.get(epoch, []):
            if doc not in included or doc in live:
                continue
            plan.append({"document_id": doc, "epoch": epoch, "profile": profile,
                         "priority": priority, "reason": reason})
    return plan


# ---------------------------------------------------------------- worklist
def worklist(arm_profile: str | None = None) -> list[str]:
    """Ledger-derived worklist: included ∧ (queued ∨ (stale ∧ superseding request))
    ∧ not skipped_oversize, ordered by priority then doc_id.

    Nothing may run that is not on the ledger. `run_bulk_extraction.py --docs` emits requests
    precisely so that an operator override still leaves the reason on the log."""
    rows = project()
    out = []
    # NOTE: no explicit skipped_oversize skip here. `project` assigns that state BEFORE any
    # queued/stale branch, so an oversize document can never present as either and the guard
    # could not fire — a mutation deleting it killed no test, which is the definition of code
    # that cannot run. The exclusion is real and lives in `project`, where it is tested.
    for doc, r in rows.items():
        if arm_profile and r.get("requested_profile") not in (None, arm_profile):
            continue
        if r["extraction_state"] == "queued":
            out.append((r["priority"] if r["priority"] is not None else 10**6, doc))
        elif r["extraction_state"] == "stale" and r["superseding"]:
            out.append((r["priority"] if r["priority"] is not None else 10**6, doc))
    return [d for _, d in sorted(out)]
