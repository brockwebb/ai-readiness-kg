#!/usr/bin/env python3
"""Admit the standards `RULE-A2-v6`, `RULE-D1-v6` and `RULE-A13-v1` already name. **Zero model
spend; no network** (the bytes were fetched before this runs).

Task `cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_a13_standards.md`
decision 1. `ind:A2` and `ind:D1` reached no admitted source, so a report quoting either by
number broke DN-001's citation floor (`2026-10-07_seed_known_locations_verify_RESULT.md` §5.9),
and RFC 9727 was named by `RULE-A13-v1` and not admitted. Each document below is one the rule's
own text (module or the `params.yaml` block the module reads) names:

* `openapi-specification-v2-0` — `RULE-A2-v6`'s fail reason names "the `swagger` field
  (Swagger 2.0)". The "`openapi` field (OpenAPI 3.x)" it names beside it is ALREADY admitted as
  `openapi-specification-core` (OAS 3.2.0, kernel-v03, `events/batch-006.jsonl:21`), and the
  rule accepts any `3.x` (`rule_a2_v5._DESCRIPTION_VERSION`), so no 3.1 copy is fetched: DN-001
  decision 4, corpus before web, as `2026-09-12_a1_a8_b3_d4_sources` declined M-13-13.
* `spdx-license-list` — `params.yaml` `d1_licence.recognised_prefixes` names
  `https://spdx.org/licenses/`.
* `cc-by-4-0-deed`, `cc0-1-0-deed` — the same block names `https://creativecommons.org/` and the
  tokens `CC-BY` and `CC0`. The task allows "licence deeds or the legal-code index"; the index
  (`/licenses/list.en`) renders as a grid of "Deed Legal Code" links whose identifiers live only
  in `href`s, so the two deeds the tokens name are admitted instead: each states its identifier
  and its canonical URL as visible text.
* `rfc-9727-api-catalog` — `RULE-A13-v1` cites RFC 9727 §2 and §3 by number.

**The path is `scripts/admit_commerce_guidance.py`'s** (the task's named precedent), with the
fetch half of `scripts/admit_tool_docs.py`: every byte came through `scripts/fetch_allowlisted.py`
(`FETCH_LOG`), and each capture must still hash to the sha256 that log recorded for its 200
response. Departures, each for a reason:

  1. the capture is HTML or plain text, and the dixie sweep fails a file that sniffs as HTML, so
     the admitted file is a markdown rendering made by `harvest_kernel.DomMarkdown` (the
     converter every kernel standard went through), with a header naming the capture's URL and
     sha256; plain text is wrapped the way `harvest_kernel._fetch_raw` wraps it. The capture
     stays at `CAPTURE_DIR` and both hashes are on the `manifest_add` event;
  2. the files go to `corpus/kernel/`, where `openapi-specification-core` already sits, not to
     `corpus/bulk/`;
  3. `acquisition.licence` records the licence each document states on its own face — the
     Commerce admission had none to record, a U.S. Government work;
  4. no extraction: the task orders admission and binding, not reading. The documents stay at
     `manifest_added`.

    /opt/anaconda3/bin/python3 scripts/admit_a2_d1_a13_standards.py --dry-run
    /opt/anaconda3/bin/python3 scripts/admit_a2_d1_a13_standards.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from kg import manifest                                             # noqa: E402
from dixie.evidence.config import load_config as dixie_config       # noqa: E402
from dixie.evidence.eventlog import EventLog as DixieLog            # noqa: E402
from dixie.evidence.manifest import build_manifest                  # noqa: E402
from dixie.evidence.sweep import Sweep                              # noqa: E402

TASK = ("cc_tasks/2026-10-11_evidence_map_carries_discoverability_and_admits_a2_d1_a13_"
        "standards.md")
EPOCH = "standards-a2-d1-a13-2026-10-11"
SOURCE_ID = "standards_2026-10-11"
FETCH_LOG = REPO / "logs" / "2026-10-11_standards_fetch.jsonl"
CAPTURE_DIR = REPO / "corpus" / "staging" / "standards_2026-10-11"
DEST_DIR = REPO / "corpus" / "kernel"
ACQUISITION_METHOD = "scripted_fetch"
ACQUIRED_BY = "scripts/fetch_allowlisted.py"

#: One entry per document. `capture` is relative to CAPTURE_DIR; `render` is `dom` (HTML through
#: DomMarkdown) or `raw` (plain text, wrapped). `licence` is quoted from the capture itself.
DOCS = [
    dict(
        doc_id="openapi-specification-v2-0",
        url="https://spec.openapis.org/oas/v2.0.html",
        capture="oas-v2.0/v2.0.html", render="dom",
        title="OpenAPI Specification v2.0 (fka Swagger RESTful API Documentation Specification)",
        authors=["OpenAPI Initiative"], pub_date="2014-09-08",
        licence=("Apache-2.0: \"The Swagger specification is licensed under The Apache License, "
                 "Version 2.0.\" (section 2.1)"),
        indicators=["A2"],
        why=("RULE-A2-v6 names the `swagger` field (Swagger 2.0) as one of the two fields that "
             "make a JSON document an API description; section 6.4.1.1 defines it."),
    ),
    dict(
        doc_id="spdx-license-list",
        url="https://spdx.org/licenses/",
        capture="spdx/licenses", render="dom",
        title="SPDX License List (version 3.29.0, 2026-09-16)",
        authors=["SPDX Workgroup, a Linux Foundation Project"], pub_date="2026-09-16",
        licence=("as served: \"© 2018 SPDX Workgroup a Linux Foundation Project. All Rights "
                 "Reserved.\" with a link to terms of use; the page states no open licence for "
                 "the list itself"),
        indicators=["D1"],
        why=("params.yaml d1_licence.recognised_prefixes, which RULE-D1-v6 reads as its test of "
             "a recognised licence identifier, names https://spdx.org/licenses/."),
    ),
    dict(
        doc_id="cc-by-4-0-deed",
        url="https://creativecommons.org/licenses/by/4.0/",
        capture="cc-by-4.0/4.0", render="dom",
        title="Creative Commons Attribution 4.0 International (CC BY 4.0), deed",
        authors=["Creative Commons"], pub_date="n.d.",
        licence=("CC-BY-4.0: \"Except where otherwise noted, content on this site is licensed "
                 "under a Creative Commons Attribution 4.0 International license.\""),
        indicators=["D1"],
        why=("params.yaml d1_licence names the prefix https://creativecommons.org/ and the token "
             "CC-BY; the deed states the identifier CC BY 4.0 and its canonical URL."),
    ),
    dict(
        doc_id="cc0-1-0-deed",
        url="https://creativecommons.org/publicdomain/zero/1.0/",
        capture="cc0-1.0/1.0", render="dom",
        title="Creative Commons CC0 1.0 Universal (CC0 1.0), deed",
        authors=["Creative Commons"], pub_date="n.d.",
        licence=("CC-BY-4.0: \"Except where otherwise noted, content on this site is licensed "
                 "under a Creative Commons Attribution 4.0 International license.\""),
        indicators=["D1"],
        why=("params.yaml d1_licence names the prefix https://creativecommons.org/ and the token "
             "CC0; the deed states the identifier CC0 1.0 and its canonical URL."),
    ),
    dict(
        doc_id="rfc-9727-api-catalog",
        url="https://www.rfc-editor.org/rfc/rfc9727.txt",
        capture="rfc9727/rfc9727.txt", render="raw",
        title=("RFC 9727: api-catalog: A Well-Known URI and Link Relation to Help Discovery of "
               "APIs"),
        authors=["K. Smith (IETF)"], pub_date="2025-06",
        licence=("IETF Trust Legal Provisions (BCP 78): \"Copyright (c) 2025 IETF Trust and the "
                 "persons identified as the document authors. All rights reserved.\"; code "
                 "components under the Revised BSD License"),
        indicators=["A13"],
        why=("RULE-A13-v1 cites RFC 9727 section 2 (the well-known URI) and section 3 (the link "
             "relation) and reads application/linkset+json, its section 4.2 format."),
    ),
]


def fetched() -> dict:
    """`{url: (sha256, ts, bytes)}` for every 200 response the fetch log holds."""
    if not FETCH_LOG.is_file():
        raise SystemExit(f"FATAL: {FETCH_LOG} is missing; nothing here was fetched through "
                         f"the allowlisted helper, so nothing is admitted")
    out = {}
    for line in FETCH_LOG.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r.get("event") == "request" and r.get("status") == 200:
            out[r["url"]] = (r["sha256"], r["ts"], r["bytes"])
    return out


def render(d: dict, body: bytes, sha: str, ts: str) -> bytes:
    """The admitted markdown: a provenance header, then the document as text."""
    if d["render"] == "dom":
        import warnings
        from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
        from harvest_kernel import DomMarkdown
        with warnings.catch_warnings():
            # spec.openapis.org serves XHTML; the HTML parser is what every kernel standard
            # was rendered with, so its output is comparable to `openapi-specification-core`.
            warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
            soup = BeautifulSoup(body, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else d["title"]
        text = DomMarkdown().render(soup.body or soup)
        kind = f"fetch_method=httpx-dom; page_title={title!r}"
    elif d["render"] == "raw":
        text = body.decode("utf-8")
        kind = "fetch_method=httpx-raw"
    else:
        raise SystemExit(f"FATAL: {d['doc_id']}: render {d['render']!r} is not dom or raw")
    header = (f"<!-- standards admission: {TASK}; primary_url={d['url']}; "
              f"capture_sha256={sha}; retrieved_at={ts}; acquired_by={ACQUIRED_BY}; {kind} -->"
              f"\n\n")
    return (header + text).encode("utf-8")


def plan() -> list:
    log = fetched()
    out = []
    for d in DOCS:
        if d["url"] not in log:
            raise SystemExit(f"FATAL: {d['url']} has no 200 line in {FETCH_LOG}")
        sha, ts, n = log[d["url"]]
        cap = CAPTURE_DIR / d["capture"]
        if not cap.is_file():
            raise SystemExit(f"FATAL: {cap} is not in hand")
        body = cap.read_bytes()
        if hashlib.sha256(body).hexdigest() != sha or len(body) != n:
            raise SystemExit(f"FATAL: {cap} is not the body the fetch log recorded for "
                             f"{d['url']} ({sha})")
        md = render(d, body, sha, ts)
        out.append({**d, "capture_sha256": sha, "retrieved_at": ts, "capture_bytes": n,
                    "md": md, "md_sha256": hashlib.sha256(md).hexdigest(),
                    "dest": DEST_DIR / f"{d['doc_id']}.md"})
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    cfg = dixie_config(REPO / "dixie_evidence.yaml")
    if "kernel" not in cfg["document_dirs"]:
        raise SystemExit("FATAL: `kernel` is not a document_dir; the sweep would never "
                         "observe corpus/kernel/")
    dlog = DixieLog(cfg["evidence_dir_abs"] / "decisions.jsonl")
    ledger = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    items = plan()
    for it in items:
        if it["doc_id"] in ledger:
            raise SystemExit(f"FATAL: {it['doc_id']} is already in the ledger")
        if it["dest"].exists():
            raise SystemExit(f"FATAL: {it['dest']} already exists; refusing to overwrite")

    now = datetime.now(timezone.utc).isoformat()
    adds, records = [], []
    for it in items:
        rationale = (f"{TASK} decision 1, implementing DN-001 decision 1 (every check the "
                     f"report quotes reaches an admitted source): {it['why']} Binds to "
                     f"{', '.join('ind:' + c for c in it['indicators'])} only because that "
                     f"rule's text already cites it; no rule changes.")
        acquisition = {
            "acquisition_method": ACQUISITION_METHOD, "acquired_by": ACQUIRED_BY,
            "acquired_at": it["retrieved_at"], "fetch_log": FETCH_LOG.relative_to(REPO).as_posix(),
            "fetched_from": it["url"],
            "capture_path": (CAPTURE_DIR / it["capture"]).relative_to(REPO).as_posix(),
            "capture_sha256": it["capture_sha256"], "capture_bytes": it["capture_bytes"],
            "rendered_by": ("scripts/harvest_kernel.py::DomMarkdown" if it["render"] == "dom"
                            else "verbatim text under a provenance header"),
            "licence": it["licence"],
            "verification": {"sha256": it["md_sha256"]},
            "evaluation": {"identity_check": "pass",
                           "note": "not previously admitted by doc_id, sha256 or primary_url"},
            "indicators": it["indicators"], "task": TASK,
        }
        adds.append(dict(doc_id=it["doc_id"], title=it["title"], authors=it["authors"],
                         pub_date=it["pub_date"], source_type="standard",
                         primary_url=it["url"], inclusion_rationale=rationale,
                         discovered_via=f"named by the rule for {', '.join(it['indicators'])}",
                         grounding_surface="document", acquisition=acquisition))
        records.append({"import_key": it["doc_id"], "normalized": {
            "source_id": SOURCE_ID, "doc_id": it["doc_id"], "doc_id_exact": True,
            "title": it["title"], "authors_or_org": it["authors"],
            "pub_year": it["pub_date"][:4] if it["pub_date"][:1].isdigit() else "n.d.",
            "doc_type": "standard", "source_url": it["url"],
            "local_path": it["dest"].relative_to(REPO).as_posix(),
            "expected_sha256": it["md_sha256"],
            "acquisition_method": ACQUISITION_METHOD, "acquired_by": ACQUIRED_BY,
            "decision": "included", "rationale": rationale,
            "decided_by": "cc", "decided_at": now,
            "notes": (f"fetched robots-first under the identified UA from {it['url']} at "
                      f"{it['retrieved_at']} ({FETCH_LOG.relative_to(REPO).as_posix()}, capture "
                      f"sha256 {it['capture_sha256']}); rendered to markdown for the sweep. "
                      f"Licence: {it['licence']}")}})

    if a.dry_run:
        print(json.dumps([{**{k: v for k, v in it.items() if k not in ("md", "dest")},
                           "dest": str(it["dest"].relative_to(REPO)),
                           "md_bytes": len(it["md"])} for it in items], indent=1,
                         ensure_ascii=False))
        return 0

    for it, fields in zip(items, adds):
        it["dest"].write_bytes(it["md"])
        if hashlib.sha256(it["dest"].read_bytes()).hexdigest() != it["md_sha256"]:
            raise SystemExit(f"FATAL: {it['dest']} does not hash as rendered")
        manifest.add(it["dest"], **fields)
    for r in records:
        dlog.append("screening_imported", r)
    actions = Sweep(cfg, dlog).run()
    entries = build_manifest(dlog, gate_cfg=cfg.get("identity_gate"))
    for it in items:
        e = entries.get(it["doc_id"])
        ok = (e and e["screening"]["decision"] == "included"
              and e["integrity"]["status"] == "verified"
              and e["identity"].get("canonical_path") == it["dest"].relative_to(REPO).as_posix())
        if not ok:
            raise SystemExit(f"FATAL: post-sweep, {it['doc_id']} is not included+verified: "
                             f"{e and (e['screening']['decision'], e['integrity']['status'])}. "
                             f"Nothing is declared for an epoch it did not enter.")
    dlog.append("corpus_epoch_declared", {
        "epoch": EPOCH, "member_doc_ids": [it["doc_id"] for it in items], "declared_by": "cc",
        "task": TASK,
        "note": ("The standards RULE-A2-v6 (Swagger 2.0), RULE-D1-v6 (its params: spdx.org, "
                 "creativecommons.org, CC-BY, CC0) and RULE-A13-v1 (RFC 9727) already name. "
                 "OpenAPI 3.x is openapi-specification-core (kernel-v03), not re-admitted.")})
    out = manifest.rebuild()
    print(json.dumps({"admitted": [it["doc_id"] for it in items], "epoch": EPOCH,
                      "sweep_actions": actions, "manifest": out}, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
