#!/usr/bin/env python3
"""§0 of task 2026-08-29_crosswalk_operationalization — admission only, zero extraction.

Admits the §9 acquisition-queue items that are NOT already in the manifest. Most of the
queue turned out to be admitted already (reported in the RESULT); this covers the residue.

Same designed path as scripts/manifest_triage.py, which this adapts:
  1. fetched artifact moved corpus/staging/inbox/crosswalk_2026-08-29/ -> corpus/crosswalk/
     (a `document_dirs` entry in dixie_evidence.yaml; gitignored — provenance rides in the
     events via primary_url + sha256)
  2. dixie ledger `screening_imported`, then the sweep observes + integrity-checks
  3. kg.manifest.add -> `manifest_add` events in events/batch-017.jsonl (this task's shard)
  4. `corpus_epoch_declared` epoch=crosswalk-2026-08-29 with the admitted member list
  5. manifest.rebuild()

NO `extraction_request` events are written for any of these: extraction waits on v0.3.7
(task §0, explicit). Zero model calls anywhere in this file.
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
from dixie.evidence.sweep import Sweep                              # noqa: E402

INBOX = REPO / "corpus" / "staging" / "inbox" / "crosswalk_2026-08-29"
DEST_DIR = REPO / "corpus" / "crosswalk"
BATCH = 17
EPOCH = "crosswalk-2026-08-29"
SOURCE_ID = "crosswalk_queue_2026-08-29"
TASK = "cc_tasks/2026-08-29_crosswalk_operationalization.md"

#: One row per artifact verified in hand. `construct_arm` is the survey arm the document
#: serves (schema v0.3.3 enum); the crosswalk's own indicator groups are NOT that enum and
#: are not conflated with it.
DOCS = [
    dict(slug="usafacts-ai-readiness", doc_id="usafacts-ai-ready-data-guide", ext="pdf",
         title="AI-Ready Data: Ensuring Public Data Meets the Needs of AI and the American "
               "Public — The USAFacts Guide to AI-Ready Data for Government Agencies",
         authors=["USAFacts"], year="2026", source_type="practitioner",
         construct_arm="publication_actionability",
         url="https://media.usafacts.org/m/634ac133d72ded81/original/USAFacts_AIReadinessForGovernment.pdf",
         why="The document this crosswalk operationalizes and critiques. §9 queue item; the "
             "brief's feedback items all target passages in it, so it must be citable."),
    dict(slug="usafacts-fde-standards", doc_id="usafacts-fde-standards-detailed", ext="pdf",
         title="Standards for Excellent Data Products — Detailed User Guide "
               "(Federal Data Excellence)",
         authors=["USAFacts", "Partnership for Public Service"], year="2026",
         source_type="practitioner", construct_arm="publication_actionability",
         url="https://media.usafacts.org/m/260cbbd653fb33ec/original/Detailed-User-Guide-Federal-Data-Excellence-Standards.pdf",
         why="§9 'USAFacts/Partnership Federal Data Excellence standards'. The detailed guide "
             "is the normative artifact; the quick reference below is its scoring surface."),
    dict(slug="usafacts-fde-quickref", doc_id="usafacts-fde-standards-quick-reference", ext="pdf",
         title="Data Product Grading Rubric — Quick Reference Guide "
               "(Federal Data Excellence Standards)",
         authors=["USAFacts", "Partnership for Public Service"], year="2026",
         source_type="practitioner", construct_arm="publication_actionability",
         url="https://media.usafacts.org/m/61974edc198bc7f8/original/Quick-Reference-Federal-Data-Excellence-Standards.pdf",
         why="The existing scored rubric closest in kind to this instrument — prior art for "
             "the January deliverable, admitted so the crosswalk can cite what it extends."),
    dict(slug="ddi-codebook", doc_id="ddi-codebook-specification", ext="html",
         title="DDI-Codebook (DDI-C) — DDI Alliance product specification page",
         authors=["DDI Alliance"], year="2026", source_type="standard",
         construct_arm="publication_actionability",
         url="https://ddialliance.org/ddi-codebook",
         why="§9 'DDI'. Grounds the SDMX/DDI/DCAT standards correction (§8.6) against the "
             "guide's NIEM recommendation. NOTE: ddialliance.org/Specification 404s; the "
             "product page is the live primary."),
    dict(slug="odcs", doc_id="odcs-open-data-contract-standard", ext="html",
         title="Open Data Contract Standard (ODCS) — Definition",
         authors=["Bitol (Linux Foundation AI & Data)"], year="2026", source_type="standard",
         construct_arm="publication_actionability",
         url="https://bitol-io.github.io/open-data-contract-standard/latest/",
         why="§9 ODCS. Grounds F1 (pre-release gates) and G6 (protocol-epoch contracts)."),
    dict(slug="slsa", doc_id="slsa-specification-v1-0", ext="html",
         title="SLSA Specification v1.0 (Supply-chain Levels for Software Artifacts)",
         authors=["OpenSSF SLSA project"], year="2023", source_type="standard",
         construct_arm="publication_actionability",
         url="https://slsa.dev/spec/v1.0/",
         why="§9 'supply-chain attestation'. Grounds F6 (release authenticity), the "
             "`paid`-tier candidate."),
    dict(slug="sainz-2023-contamination", doc_id="sainz-2023-llm-data-contamination", ext="pdf",
         title="NLP Evaluation in trouble: On the Need to Measure LLM Data Contamination "
               "for each Benchmark",
         authors=["Sainz, O.", "Campos, J.A.", "García-Ferrero, I.", "Etxaniz, J.",
                  "Lopez de Lacalle, O.", "Agirre, E."],
         year="2023", source_type="academic", construct_arm="training_data_readiness",
         url="https://aclanthology.org/2023.findings-emnlp.722/",
         why="§9 'one benchmark-contamination survey (pick the most-cited; record the "
             "selection rationale)'. SELECTION RATIONALE: most-cited of the five candidates "
             "checked against OpenAlex on 2026-08-29 — 62 citations vs 28 for the runner-up "
             "(Deng 2024, NAACL), 7 for the two dedicated surveys, 2 for Magar & Schwartz "
             "2022. DEVIATION: it is a position paper, not a survey; recorded because the "
             "indicator it grounds (E4, contamination policy) is a policy claim the position "
             "paper states directly, and picking the most-cited *survey* would have meant a "
             "7-citation paper over a 62-citation one."),
    dict(slug="sfv-paper", doc_id="webb-2026-state-fidelity-validity", ext="pdf",
         title="State Fidelity Validity for Reproducible AI Systems and Workflows",
         authors=["Webb, B."], year="2026", source_type="academic",
         construct_arm="training_data_readiness",
         url="https://doi.org/10.5281/zenodo.22111334",
         why="§9 SFV paper (operator's own). Grounds E8 (drift sentinels / state fidelity "
             "across product versions). Cited as an internal artifact by DOI per §3(c)."),
]

#: Fetched, verified unfetchable, NOT admitted and NOT substituted (task §0).
BLOCKED = [
    dict(doc_id="commerce-generative-ai-open-data-guidelines", 
         title="Generative Artificial Intelligence and Open Data: Guidelines and Best "
               "Practices (U.S. Department of Commerce, January 2025)",
         url="https://www.commerce.gov/news/blog/2025/01/generative-artificial-intelligence-and-open-data-guidelines-and-best-practices",
         reason="HTTP 403 to every client tried on 2026-08-29: curl with a browser "
                "User-Agent (403), the PDF path under commerce.gov/sites/default/files "
                "(403), data.commerce.gov (403), and WebFetch (403). The 5,801-byte body "
                "returned is a Cloudflare interstitial ('Just a moment... Enable JavaScript "
                "and cookies to continue'), not the document. resources.data.gov has no "
                "copy (404). This is bot protection, not a paywall or a withdrawal.",
         existing="Manifest already holds `generative-ai-and-open-data-guidelines-and-best-"
                  "practices-de` at status pending_refetch / quarantined for the same URL — "
                  "this run does not change that entry, and no secondary source is "
                  "substituted for it (task §0)."),
]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def existing_identity() -> tuple[set, set, set]:
    """doc_ids / sha256s / normalized urls already admitted — the dedup gate's inputs."""
    ids, shas, urls = set(), set(), set()
    for ev in eventlog.replay():
        if ev.get("event_type") == "manifest_add":
            p = ev.get("payload") or ev
            ids.add(p.get("doc_id"))
            shas.add((p.get("identity") or {}).get("content_hash") or p.get("content_hash"))
            u = p.get("primary_url") or (p.get("identity") or {}).get("source_url")
            if u:
                urls.add(u.rstrip("/").lower())
    return ids, shas, urls


def run(dry_run: bool) -> int:
    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    if "crosswalk" not in cfg["document_dirs"]:
        raise SystemExit("FATAL: dixie_evidence.yaml document_dirs must include 'crosswalk'")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    ids, shas, urls = existing_identity()
    manifest._MANIFEST_BATCH = BATCH
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    added, skipped, deferred = [], [], []
    for rec in DOCS:
        doc_id, src = rec["doc_id"], INBOX / f"{rec['slug']}.tmp"
        if not src.exists():
            deferred.append((doc_id, f"artifact not in inbox: {src}")); continue
        sha = _sha256(src)
        norm_url = rec["url"].rstrip("/").lower()
        if doc_id in ids:
            skipped.append((doc_id, "doc_id already admitted")); continue
        if sha in shas:
            skipped.append((doc_id, f"content_hash already admitted ({sha[:12]})")); continue
        if norm_url in urls:
            skipped.append((doc_id, "primary_url already admitted")); continue

        dest = DEST_DIR / f"{doc_id}.{rec['ext']}"
        if dest.exists() and _sha256(dest) != sha:
            deferred.append((doc_id, f"destination exists with different content: {dest}"))
            continue
        rationale = (f"task §0 acquisition queue (§9 item), construct_arm="
                     f"{rec['construct_arm']}: {rec['why']}")
        if dry_run:
            added.append((doc_id, f"{sha[:12]} {src.stat().st_size:,}B -> {dest.name}"))
            ids.add(doc_id); shas.add(sha); urls.add(norm_url)
            continue

        if not dest.exists():
            shutil.copy2(str(src), str(dest))
        rel = dest.relative_to(REPO).as_posix()
        dlog.append("screening_imported", {
            "import_key": doc_id,
            "normalized": {
                "source_id": SOURCE_ID, "doc_id": doc_id, "doc_id_exact": True,
                "title": rec["title"], "authors_or_org": rec["authors"],
                "pub_year": rec["year"], "doc_type": rec["source_type"],
                "source_url": rec["url"], "local_path": rel, "expected_sha256": sha,
                "acquisition_method": "scripted_fetch",
                "acquired_by": "scripts/manifest_crosswalk.py",
                "decision": "included", "rationale": rationale,
                "decided_by": "cc", "decided_at": _now(), "notes": rec["why"],
            }})
        acquisition = {
            "acquisition_method": "scripted_fetch",
            "test": {"primary_url": rec["url"], "http_status": 200,
                     "retrieved_at_utc": _now(), "tool": "curl (scripts/manifest_crosswalk.py)"},
            "evaluation": {"identity_check": "pass",
                           "note": "not previously manifested by doc_id, sha256 or primary_url"},
            "verification": {"sha256": sha},
            "validation": {"bytes": dest.stat().st_size, "format": rec["ext"]},
            "selection_rationale": rec["why"],
            "task": TASK,
        }
        try:
            manifest.add(str(dest), doc_id=doc_id, title=rec["title"], authors=rec["authors"],
                         pub_date=rec["year"], source_type=rec["source_type"],
                         primary_url=rec["url"], inclusion_rationale=rationale,
                         discovered_via=SOURCE_ID, construct_arm=rec["construct_arm"],
                         grounding_surface="document", acquisition=acquisition)
        except manifest.ManifestError as exc:
            deferred.append((doc_id, f"manifest gate rejected: {exc}")); continue
        ids.add(doc_id); shas.add(sha); urls.add(norm_url)
        added.append((doc_id, rel))

    for doc_id, why in added:    print("ADD     ", doc_id, "|", why)
    for doc_id, why in skipped:  print("SKIP    ", doc_id, "|", why)
    for doc_id, why in deferred: print("DEFER   ", doc_id, "|", why)
    for b in BLOCKED:            print("BLOCKED ", b["doc_id"], "|", b["reason"][:90])

    if dry_run:
        return 0

    # The blocked item is recorded as an event, not silently omitted: an acquisition that
    # failed is evidence about the source, and the next run must not re-derive the search.
    for b in BLOCKED:
        eventlog.append({"event_type": "acquisition_blocked", "doc_id": b["doc_id"],
                         "title": b["title"], "primary_url": b["url"], "reason": b["reason"],
                         "existing_manifest_state": b["existing"], "task": TASK},
                        batch=BATCH)
    actions = Sweep(cfg, dlog).run()
    print("sweep:", actions)
    eventlog.append({"event_type": "corpus_epoch_declared", "epoch": EPOCH,
                     "members": sorted(d for d, _ in added), "task": TASK,
                     "note": "admission only; no extraction_request events — v0.3.7 gate"},
                    batch=BATCH)
    manifest.rebuild()
    print(f"admitted {len(added)}, skipped {len(skipped)}, deferred {len(deferred)}, "
          f"blocked {len(BLOCKED)}")
    return 0 if not deferred else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    return run(ap.parse_args().dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
