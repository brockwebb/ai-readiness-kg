#!/usr/bin/env python3
"""Emit the `manifest_add` events the two tool READMEs were admitted without. **Zero spend, no
network, nothing fetched.**

`cc_tasks/2026-09-19_resnapshot_rj4.md` decision 6, closing
`cc_tasks/2026-09-18_requirements_layer_RESULT.md` §3 premise 7 and "Open" item 1.

`scripts/admit_tool_docs.py` admitted `oasdiff-readme` and `wayback-cdx-server-api-readme`
through the dixie ledger only, reasoning that the event stream is the extraction-admission gate
and these are reference documents, not extraction inputs. The consequence it did not price: the
KG projection makes a `Document` node from a `manifest_add` event and from nothing else
(`scripts/build_projection.py`), so the requirements layer cites two documents the graph does
not hold, and the MCP had to learn a manifest fallback to resolve them.

**Emitting the event does not enrol either document for extraction.** The extraction queue is
the membership of a declared corpus epoch (`corpus_epoch_declared` in the ledger, read by
`scripts/run_bulk_extraction.py` through `kg.queue.corpus_epochs`), and neither README is a
member of an extraction epoch; `tool-docs-2026-09-18` is the admission epoch.
`extruct-readme`, the tool README admitted before these, carries a `manifest_add` on
`events/batch-006.jsonl` under the same terms.

**Every field comes from the ledger entry**, through `kg.manifest.add`, the one writer of the
event, so its checks run: the file exists under `corpus/`, it hashes to what the ledger
recorded (checked here first, and `add` re-hashes it), no admitted document already holds the
doc_id, the hash or the URL. A document already carrying the event is skipped, so a second run
writes nothing.

    /opt/anaconda3/bin/python3 scripts/emit_tool_doc_manifest_adds.py [--dry-run]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

TASK = "cc_tasks/2026-09-19_resnapshot_rj4.md"
DOC_IDS = ("oasdiff-readme", "wayback-cdx-server-api-readme")


def ledger_entries() -> dict:
    doc = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))
    out = {}
    for d in DOC_IDS:
        e = doc["entries"].get(d)
        if e is None:
            raise SystemExit(f"FATAL: {d} is not in corpus/manifest.json; decision 6 emits the "
                             f"event FROM the ledger entry and there is none")
        if e["screening"]["decision"] != "included" or e["integrity"]["status"] != "verified":
            raise SystemExit(f"FATAL: {d} is {e['screening']['decision']}/"
                             f"{e['integrity']['status']} in the ledger, not included/verified")
        path = REPO / e["identity"]["canonical_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != e["identity"]["sha256"]:
            raise SystemExit(f"FATAL: {path} does not hash to the ledger's sha256 for {d}")
        out[d] = e
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    from kg import eventlog, manifest
    entries = ledger_entries()
    evented = {ev["payload"]["doc_id"] for ev in eventlog.replay()
               if ev.get("event_type") == "manifest_add"}
    done = []
    for d, e in entries.items():
        if d in evented:
            print(f"  {d}: manifest_add already on the log")
            continue
        ident, acq = e["identity"], e["acquisition"]
        fields = dict(
            doc_id=d, title=ident["title"], authors=ident["authors_or_org"],
            pub_date=ident["pub_year"], source_type=ident["doc_type"],
            primary_url=ident["source_url"],
            inclusion_rationale=e["screening"]["rationale"],
            discovered_via=(f"dixie ledger entry ({', '.join(e['provenance_sources'])}); event "
                            f"emitted by {TASK} decision 6 so the projection holds its Document "
                            f"node"),
            acquisition={"acquisition_method": acq["method"],
                         "acquired_at": acq["acquired_at"], "acquired_by": acq["acquired_by"],
                         "ledger_sha256": ident["sha256"], "notes": e["extra"].get("notes")})
        if not a.dry_run:
            manifest.add(str(REPO / ident["canonical_path"]), **fields)
        done.append(d)
    print(json.dumps({"emitted": done, "dry_run": a.dry_run}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
