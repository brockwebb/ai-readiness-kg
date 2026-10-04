#!/usr/bin/env python3
"""Admit Commerce's "Generative AI and Open Data" guidance. **Zero model spend, no network.**

Task `cc_tasks/2026-10-02_commerce_guidance_admission.md` decisions 1-2. Every byte comes from
the FSS policy graph's stored copy on this machine (`~/GitHub/icsp_notebook`, the
`fss-policy-kg` working copy), which is read and never written. commerce.gov is not contacted:
its CDN answered 403 to this repo's harness on 2026-07-04, 2026-08-29 and 2026-10-02.

**A refetch fulfillment, not a second doc_id.** The dixie ledger has held this document since
2026-07-05 as `generative-ai-and-open-data-guidelines-and-best-practices-de`, decision
`pending_refetch`, because the bulk acquisition stored a 5,908-byte Cloudflare interstitial
that the sweep quarantined (magic bytes html). Admitting the PDF under a fresh doc_id would
leave two ledger entries for one `source_url`, one of them forever owed a refetch. The repo's
own precedent for this exact state is `scripts/accept_two_acts.py`: same doc_id, new bytes,
the new file observed and integrity-checked, then `included`.

The path is otherwise `scripts/admit_tool_docs.py`'s, plus the `manifest_add` event that
makes the document an extraction input (CLAUDE.md invariant 2; `admit_tool_docs` skipped it
because those were reference documents, this one is read):

  1. hash the FSS copy against the FSS ledger's recorded sha256 — unequal stops everything;
  2. copy it to `corpus/bulk/<doc_id>.pdf`, the path the failed acquisition targeted;
  3. `kg.manifest.add` — the `manifest_add` event on batch 1, provenance in `acquisition`;
  4. dixie `screening_imported` (`doc_id_exact`, decision `included`), then the sweep
     observes and integrity-checks the new file;
  5. `corpus_epoch_declared` `commerce-guidance-2026-10-02`;
  6. `manifest.rebuild()`.

**There is no fetch log, because there is no fetch.** The standing rule routes acquisition
through `scripts/fetch_allowlisted.py` so every admitted document traces to one fetch log; a
copy of a file another repo already holds and hashes has no request to log, so the FSS ledger
entry and its sha256 stand in that place.

    /opt/anaconda3/bin/python3 scripts/admit_commerce_guidance.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_commerce_guidance.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from kg import manifest                                             # noqa: E402
from dixie.evidence.config import load_config as dixie_config       # noqa: E402
from dixie.evidence.eventlog import EventLog as DixieLog            # noqa: E402
from dixie.evidence.manifest import build_manifest                  # noqa: E402
from dixie.evidence.sweep import Sweep                              # noqa: E402

TASK = "cc_tasks/2026-10-02_commerce_guidance_admission.md"
EPOCH = "commerce-guidance-2026-10-02"
SOURCE_ID = "fss_policy_kg_ledger"
ACQUISITION_METHOD = "local_copy_from_fss_policy_kg"

#: The FSS policy graph's working copy and its ledger. Both resolved from the machine, never
#: assumed: the task called the repo `fss-policy-kg`; on disk it is `icsp_notebook`
#: (its package is `fss_policy_kg`).
FSS_REPO = Path.home() / "GitHub" / "icsp_notebook"
FSS_LEDGER = FSS_REPO / "corpus" / "manifest.yaml"
FSS_DOC_ID = "doc_genai_open_data_2025"

#: The entry this fulfils. Present in the ledger as `pending_refetch` since 2026-07-05.
DOC_ID = "generative-ai-and-open-data-guidelines-and-best-practices-de"
DEST = REPO / "corpus" / "bulk" / f"{DOC_ID}.pdf"

#: The landing page is the citable primary source: it is the FSS ledger's `source_url`, the
#: existing ledger entry's `source_url`, and the URL `usdc-mcp-federal-open-data-pilot-2026`
#: cites. The PDF path (from the FSS ledger's notes) is recorded as what was downloaded.
PRIMARY_URL = ("https://www.commerce.gov/news/blog/2025/01/"
               "generative-artificial-intelligence-and-open-data-guidelines-and-best-practices")
PDF_URL = "https://www.commerce.gov/sites/default/files/2025-01/GenerativeAI-Open-Data.pdf"


def fss_entry() -> dict:
    """The FSS ledger entry for the document, and the sha256 its notes record."""
    data = yaml.safe_load(FSS_LEDGER.read_text(encoding="utf-8"))
    docs = data.get("documents") if isinstance(data, dict) else data
    hits = [d for d in docs if isinstance(d, dict) and d.get("id") == FSS_DOC_ID]
    if len(hits) != 1:
        raise SystemExit(f"FATAL: {FSS_LEDGER} holds {len(hits)} entries for {FSS_DOC_ID}")
    e = hits[0]
    notes = e.get("notes") or ""
    marker = "sha256 "
    if marker not in notes:
        raise SystemExit(f"FATAL: the FSS entry for {FSS_DOC_ID} records no sha256")
    e["_ledger_sha256"] = notes.split(marker, 1)[1].split()[0].strip(".,;")
    return e


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    fe = fss_entry()
    src = FSS_REPO / fe["local_path"]
    if not src.is_file():
        raise SystemExit(f"FATAL: {src} is not on disk")
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    if sha != fe["_ledger_sha256"]:
        raise SystemExit(f"FATAL: {src} hashes to {sha}; the FSS ledger recorded "
                         f"{fe['_ledger_sha256']}. Decision 1: unequal stops the task.")

    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    ledger = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    prior = ledger.get(DOC_ID)
    if not prior or prior["screening"]["decision"] != "pending_refetch":
        raise SystemExit(f"FATAL: {DOC_ID} is not a pending_refetch ledger entry "
                         f"({prior and prior['screening']['decision']}); this script fulfils "
                         f"exactly that state and nothing else")
    if DEST.exists():
        raise SystemExit(f"FATAL: {DEST} already exists; refusing to overwrite")

    now = datetime.now(timezone.utc).isoformat()
    rationale = (f"{TASK} decision 2, implementing DN-009 decision 8 (the corpus is searched "
                 f"first; a corpus that lacks the most relevant federal document is a defect "
                 f"in the corpus). Commerce's January 2025 guidance carries a glossary "
                 f"definition of AI-ready data. Refetch fulfillment of the 2026-07-05 "
                 f"pending_refetch entry, whose acquisition stored a Cloudflare interstitial.")
    acquisition = {
        "acquisition_method": ACQUISITION_METHOD,
        "acquired_by": TASK,
        "source_repository": str(FSS_REPO),
        "source_path": fe["local_path"],
        "fss_doc_id": FSS_DOC_ID,
        "fss_ledger": "corpus/manifest.yaml",
        "fss_retrieved_date": str(fe.get("retrieved_date")),
        "downloaded_from": PDF_URL,
        "as_of": str(fe.get("effective_date")),
        "fetch_log": None,
        "fetch_log_note": ("no fetch: a copy of a file the FSS policy graph already holds and "
                           "hashes, so the FSS ledger entry stands where a fetch log would"),
        "verification": {"sha256": sha, "fss_ledger_sha256": fe["_ledger_sha256"],
                         "supersedes_sha256": prior["identity"].get("sha256")},
        "evaluation": {"identity_check": "pass",
                       "note": ("PDF /Title 'Generative Artificial Intelligence and Open "
                                "Data: Guidelines and Best Practices'; page 1 'Version: 1 "
                                "Last Updated: January 16, 2025'; 79 pages")},
        "task": TASK,
    }
    add_fields = dict(
        doc_id=DOC_ID,
        title="Generative Artificial Intelligence and Open Data: Guidelines and Best Practices",
        authors=["U.S. Department of Commerce, Commerce Data Governance Board",
                 "AI and Open Government Data Assets Working Group"],
        pub_date="2025-01-16", source_type="federal", primary_url=PRIMARY_URL,
        inclusion_rationale=rationale, discovered_via="fss-policy-kg ledger",
        grounding_surface="document", acquisition=acquisition)
    record = {"import_key": DOC_ID, "normalized": {
        "source_id": SOURCE_ID, "doc_id": DOC_ID, "doc_id_exact": True,
        "title": add_fields["title"], "authors_or_org": add_fields["authors"],
        "pub_year": "2025", "doc_type": "federal", "source_url": PRIMARY_URL,
        "local_path": DEST.relative_to(REPO).as_posix(), "expected_sha256": sha,
        "acquisition_method": ACQUISITION_METHOD, "acquired_by": TASK,
        "decision": "included", "rationale": rationale,
        "decided_by": "cc", "decided_at": now,
        "notes": (f"copied from {FSS_REPO.name}/{fe['local_path']} (FSS doc "
                  f"{FSS_DOC_ID}, sha256 equal to the FSS ledger's); downloaded there from "
                  f"{PDF_URL} on {fe.get('retrieved_date')}")}}

    if a.dry_run:
        print(json.dumps({"source": str(src), "sha256": sha,
                          "fss_ledger_sha256": fe["_ledger_sha256"], "dest": str(DEST),
                          "manifest_add": add_fields, "screening_imported": record},
                         indent=1, ensure_ascii=False))
        return 0

    DEST.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, DEST)
    if hashlib.sha256(DEST.read_bytes()).hexdigest() != sha:
        raise SystemExit(f"FATAL: {DEST} does not hash to {sha} after the copy")
    manifest.add(DEST, **add_fields)
    dlog.append("screening_imported", record)
    actions = Sweep(cfg, dlog).run()
    entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    e = entries.get(DOC_ID)
    ok = (e and e["screening"]["decision"] == "included"
          and e["integrity"]["status"] == "verified"
          and e["identity"].get("canonical_path") == DEST.relative_to(REPO).as_posix())
    if not ok:
        raise SystemExit(f"FATAL: post-sweep, {DOC_ID} is not included+verified at {DEST}: "
                         f"{e and (e['screening']['decision'], e['integrity']['status'], e['identity'].get('canonical_path'))}. "
                         f"Nothing is declared for an epoch it did not enter.")
    dlog.append("corpus_epoch_declared", {
        "epoch": EPOCH, "member_doc_ids": [DOC_ID], "declared_by": "cc", "task": TASK,
        "note": ("Commerce Data Governance Board, 'Generative Artificial Intelligence and Open "
                 "Data: Guidelines and Best Practices' (v1, 2025-01-16), from the FSS policy "
                 "graph's stored copy; refetch fulfillment of a 2026-07-05 pending_refetch.")})
    out = manifest.rebuild()
    print(json.dumps({"admitted": DOC_ID, "epoch": EPOCH, "sha256": sha,
                      "sweep_actions": actions, "manifest": out}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
