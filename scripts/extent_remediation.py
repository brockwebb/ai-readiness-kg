#!/usr/bin/env python3
"""Re-acquire the six thin-extent documents at their canonical fullest source.

Task `cc_tasks/2026-08-31_extent_remediation.md`. **Zero model tokens** — acquisition is
fetching and conversion is the DD-030 pipeline; any model call is a defect, and the run
declares a ceiling of 0 so the spend guard refuses one at the choke point.

WHY THE LEDGER DANCE (read before changing it)
----------------------------------------------
`corpus/manifest.json` is a projection of the dixie evidence ledger, and the projection is
first-wins for identity: `_on_screening_imported` fills only fields that are still None, and
`_on_file_observed` adopts a path only when `canonical_path` is None or already that path.
So a new file at a NEW path lands in `alternates` and the document keeps pointing at the old
capture — the gate would re-read the navigation page and re-fail it.

The ledger's own designed route is named in `_on_file_observed`'s comment: "a fresh file
observed for an entry whose canonical was quarantined (e.g. a refetch fulfillment replacing a
wrong-extent doc) RECOVERS it". Quarantining the old canonical nulls `canonical_path`, and the
next `file_observed` sets it. `scripts/accept_two_acts.py` did exactly this for a
mis-acquired statute and left the lesson in a comment there: the new file must be OBSERVED and
integrity-CHECKED or the manifest shows no verified file at all.

So, per document: quarantine old (move + reason, never delete) -> write new -> file_observed
-> integrity_checked -> manifest.content_update(reason="extent_corrected") -> rebuild
projection -> DD-030 gate. Two ledgers because they answer two questions (CLAUDE.md invariant
2): the event log is the extraction-admission gate, the dixie ledger is the corpus ledger.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import urllib.request

REPO = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml                                                          # noqa: E402
from kg import eventlog, manifest, spend                             # noqa: E402
from kg.ingest import convert as C                                   # noqa: E402

TASK = "cc_tasks/2026-08-31_extent_remediation.md"
RUN_ID = "extent_remediation_2026_08_31"
CONFIG = REPO / "scripts/extent_remediation.yaml"
QUARANTINE = REPO / "corpus/quarantine"
UA = "ai-readiness-kg/extent-remediation (+https://github.com/brockwebb)"
TIMEOUT = 45


def fetch(url: str, *, binary: bool = False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        raw = r.read()
    return raw if binary else raw.decode("utf-8", errors="replace")


def gh_tree(repo: str, ref: str) -> list[dict]:
    """Every blob in the repo at `ref`, one API call. Walking `contents/` per directory
    costs one call per directory and rate-limits on an unauthenticated client."""
    data = json.loads(fetch(f"https://api.github.com/repos/{repo}/git/trees/{ref}"
                            f"?recursive=1"))
    if data.get("truncated"):
        raise SystemExit(f"FATAL: {repo}@{ref} tree truncated; paginate before trusting it")
    return [e for e in data["tree"] if e["type"] == "blob"]


def gh_raw(repo: str, ref: str, path: str) -> str:
    return fetch(f"https://raw.githubusercontent.com/{repo}/{ref}/{path}")


def pandoc_rst(text: str) -> str:
    r = subprocess.run(["pandoc", "-f", "rst", "-t", "gfm", "--wrap=none"],
                       input=text, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"pandoc rst->md failed: {r.stderr.strip()[:200]}")
    return r.stdout


# ---------------------------------------------------------------- strategies
def acquire_github_markdown(spec: dict) -> list[tuple[str, str, str]]:
    """(section title, source url, markdown) for every .md under the configured paths."""
    repo, ref = spec["repo"], spec["ref"]
    wanted = tuple(p.rstrip("/") + "/" for p in spec["paths"])
    out = []
    for blob in sorted(gh_tree(repo, ref), key=lambda b: b["path"]):
        p = blob["path"]
        if not p.endswith(".md") or not p.startswith(wanted):
            continue
        # examples/ and img/ are excluded by the config's extent_note; enforce it here so
        # the note and the bytes cannot disagree.
        rest = p[len(next(w for w in wanted if p.startswith(w))):]
        if "/" in rest:
            continue
        out.append((pathlib.Path(p).stem,
                    f"https://github.com/{repo}/blob/{ref}/{p}",
                    gh_raw(repo, ref, p)))
    return out


def acquire_github_rst(spec: dict) -> list[tuple[str, str, str]]:
    repo, ref = spec["repo"], spec["ref"]
    wanted = tuple(p.rstrip("/") + "/" for p in spec["paths"])
    out = []
    for blob in sorted(gh_tree(repo, ref), key=lambda b: b["path"]):
        p = blob["path"]
        if not p.endswith(".rst") or not p.startswith(wanted):
            continue
        out.append((p[len(wanted[0]):].removesuffix(".rst"),
                    f"https://github.com/{repo}/blob/{ref}/{p}",
                    pandoc_rst(gh_raw(repo, ref, p))))
    return out


def acquire_llms_txt(spec: dict) -> list[tuple[str, str, str]]:
    """Follow the llms.txt convention the publisher advertises: the root index links section
    indexes, and those link the pages. `.md` on a page URL is the publisher's own native
    markdown, so nothing here converts anything."""
    root = fetch(spec["index"])
    seen, pages = set(), []
    indexes = [spec["index"]] + re.findall(r"\((https://[^)]*?/llms\.txt)\)", root)
    for idx in dict.fromkeys(indexes):
        try:
            body = fetch(idx)
        except Exception as exc:                       # noqa: BLE001 - reported, not hidden
            print(f"    WARN index unreadable {idx}: {exc}")
            continue
        for title, url in re.findall(r"\[([^\]]+)\]\((https://[^)]+?\.md)\)", body):
            if url in seen:
                continue
            seen.add(url)
            pages.append((title, url))
    keep = tuple(spec.get("include_prefixes") or ())
    if keep:
        pages = [(t, u) for t, u in pages if u.startswith(keep)]
    out = []
    for title, url in pages:
        try:
            out.append((title, url, fetch(url)))
        except Exception as exc:                       # noqa: BLE001
            print(f"    WARN page unreadable {url}: {exc}")
    return out


def acquire_sitemap_html(spec: dict) -> list[tuple[str, str, str]]:
    """Fetch the sitemap's in-scope pages and convert each with docling — the DD-030
    registry's own HTML tool, reused rather than reimplemented (Section 7: adopt, don't
    create; and the ingestion RESULT measured docling ahead of pandoc and trafilatura)."""
    xml = fetch(spec["sitemap"])
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", xml)
            if any(u.startswith(p) for p in spec["include_prefixes"])
            and u not in spec.get("exclude", [])]
    tmp = REPO / "state" / "_extent_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    out = []
    for u in sorted(urls):
        slug = (u.rstrip("/").rsplit("/", 1)[-1] or "index")
        f = tmp / f"{slug}.html"
        f.write_text(fetch(u), encoding="utf-8")
        out.append((slug, u, C.TOOLS["docling"](f)))
        f.unlink()
    return out


STRATEGIES = {"github_markdown": acquire_github_markdown, "github_rst": acquire_github_rst,
              "llms_txt": acquire_llms_txt, "sitemap_html": acquire_sitemap_html}


# ---------------------------------------------------------------- assembly + ledgers
def assemble(doc_id: str, spec: dict, sections: list[tuple[str, str, str]]) -> str:
    """One markdown file, sections as H1s so the heading-aware chunker cuts where the source
    pages did, each carrying its own source URL so a grounding span stays citable to a page."""
    head = [f"# {doc_id}", "",
            f"> Extent-corrected acquisition. {spec['version_note']}.", "",
            f"> Extent note: {' '.join(spec['extent_note'].split())}", "",
            f"> Sections: {len(sections)}. Each section below names the source it came from.",
            "", "---", ""]
    body = []
    for title, url, text in sections:
        body += [f"# {title}", "", f"Source: {url}", "", text.strip(), "", "---", ""]
    return "\n".join(head + body).rstrip() + "\n"


def dixie_log():
    from dixie.evidence.config import load_config
    from dixie.evidence.eventlog import EventLog
    cfg = load_config(REPO / "dixie_evidence.yaml")
    return cfg, EventLog(cfg["evidence_dir_abs"] / "decisions.jsonl")


def remediate(doc_id: str, spec: dict, entry: dict, *, apply: bool) -> dict:
    sections = STRATEGIES[spec["strategy"]](spec)
    if not sections:
        raise SystemExit(f"FATAL: {doc_id}: no sections acquired; refusing to write an "
                         f"empty substrate over a real one")
    text = assemble(doc_id, spec, sections)
    old_rel = entry["identity"]["canonical_path"]
    new_rel = f"corpus/{spec['lane']}/{doc_id}.md"
    report = {"doc_id": doc_id, "sections": len(sections), "chars": len(text),
              "old_path": old_rel, "new_path": new_rel,
              "old_visible": len(C.visible_text((REPO / old_rel).read_text(
                  encoding="utf-8", errors="replace"))) if (REPO / old_rel).is_file() else None,
              "new_visible": len(C.visible_text(text))}
    if not apply:
        return report

    from dixie.evidence import integrity as _integrity
    cfg, log = dixie_log()
    old_abs = REPO / old_rel
    # 1. quarantine the wrong-extent capture: move + reason, never delete (invariant 2).
    if old_abs.is_file():
        QUARANTINE.mkdir(parents=True, exist_ok=True)
        old_sha = hashlib.sha256(old_abs.read_bytes()).hexdigest()
        dest = QUARANTINE / f"{doc_id}.thin-extent{old_abs.suffix}"
        old_abs.rename(dest)
        (QUARANTINE / f"{doc_id}.thin-extent.reason.txt").write_text(
            f"thin extent (DD-030 conversion_gap): the capture was the document's navigation "
            f"or landing page, not the document. Superseded by {new_rel} acquired from the "
            f"canonical source per {TASK}. sha256={old_sha}\n", encoding="utf-8")
        log.append("quarantined", {"path": old_rel, "dest": str(dest.relative_to(REPO)),
                                   "reasons": [f"thin_extent_suspected: superseded by {new_rel}"]})
        report["quarantined"] = str(dest.relative_to(REPO))
        report["old_sha256"] = old_sha
    # 2. the new canonical, then OBSERVE and CHECK it — the quarantine nulled canonical_path,
    #    and without both events the projection shows the document with no verified file.
    new_abs = REPO / new_rel
    new_abs.parent.mkdir(parents=True, exist_ok=True)
    new_abs.write_text(text, encoding="utf-8")
    chk = _integrity.run_checks(new_abs, cfg["integrity"])
    log.append("file_observed", {"path": new_rel, "sha256": chk["sha256"], "size": chk["size"],
                                 "claimed_type": chk["claimed_type"],
                                 "detected_type": chk["detected_type"]})
    log.append("integrity_checked", {"path": new_rel, "verdict": chk["verdict"],
                                     "checks": chk["checks"]})
    report["new_sha256"] = chk["sha256"]
    report["integrity"] = chk["verdict"]
    # 3. the extraction-admission side: the admission event is never edited (invariant 1).
    #    Idempotent: a resumed run must not re-supersede a document it already superseded.
    #    `content_update` refuses on a stale `superseded_content_hash`, which is the right
    #    refusal but a bad way to discover that half a batch already ran — this run WAS
    #    resumed, after a crash between slsa's file write and its supersession.
    already = {e["doc_id"]: e for e in manifest._load_entries()}.get(doc_id) or {}
    if already.get("content_hash") == chk["sha256"]:
        report["content_update"] = "already superseded; skipped"
        return report
    manifest.content_update(
        doc_id, reason="extent_corrected",
        superseded_content_hash=entry["identity"]["sha256"],
        local_path=new_rel, task=TASK,
        evidence={"strategy": spec["strategy"], "sections": len(sections),
                  "version_note": spec["version_note"],
                  "extent_note": " ".join(spec["extent_note"].split()),
                  "source_urls": [u for _t, u, _x in sections][:200],
                  "visible_chars_before": report["old_visible"],
                  "visible_chars_after": report["new_visible"]})
    return report


def cut_with_reason(doc_id: str, spec: dict, *, apply: bool) -> dict:
    """A document that cannot be remediated is recorded, never silently left broken."""
    note = " ".join(spec["extent_note"].split())
    if apply:
        eventlog.append({"event_type": "extent_unremediable", "document_id": doc_id,
                         "reason": note, "task": TASK,
                         "searched": ["itu.int epublications landing (en, zh)",
                                      "api/static/<slug>/en/{content.json,toc.json,index.html,"
                                      "document.pdf,main.pdf,en}",
                                      "api/publication/<slug>{,/en}", "api/epub/<slug>/en",
                                      "page HTML link extraction for pdf/download hrefs"]},
                        batch=24)
    return {"doc_id": doc_id, "outcome": "cut_with_reason", "reason": note}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="default is a dry run")
    ap.add_argument("--only", action="append")
    ap.add_argument("--ceiling-tokens", type=int, required=True,
                    help="must be 0: this task makes no model calls")
    a = ap.parse_args()
    if a.ceiling_tokens != 0:
        raise SystemExit("FATAL: acquisition is deterministic; --ceiling-tokens must be 0")
    spend.default_ledger().declare(RUN_ID, 0, declared_by=TASK,
                                   call_class="extraction_chunk")

    specs = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    entries = json.loads((REPO / "corpus/manifest.json").read_text())["entries"]
    reports = []
    for doc_id, spec in specs.items():
        if a.only and doc_id not in a.only:
            continue
        print(f"\n=== {doc_id} [{spec['strategy']}]", flush=True)
        if spec["strategy"] == "unreachable":
            r = cut_with_reason(doc_id, spec, apply=a.apply)
        else:
            r = remediate(doc_id, spec, entries[doc_id], apply=a.apply)
            was = f"{r['old_visible']:,}" if r["old_visible"] is not None else "quarantined"
            print(f"    {r['sections']} sections, {r['chars']:,} chars "
                  f"(visible {was} -> {r['new_visible']:,})"
                  + (f"  [{r['content_update']}]" if r.get("content_update") else ""))
        reports.append(r)
    if a.apply:
        manifest.rebuild()
        print("\nmanifest projection rebuilt")
    (REPO / "state/extent_remediation.json").write_text(
        json.dumps({"task": TASK, "applied": a.apply, "reports": reports}, indent=1) + "\n",
        encoding="utf-8")
    print(f"\n{len(reports)} documents processed (apply={a.apply})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
