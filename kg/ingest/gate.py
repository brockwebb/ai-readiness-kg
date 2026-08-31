#!/usr/bin/env python3
"""The admission convertibility gate and its auto-task mechanism.

Task `cc_tasks/2026-08-31_ingestion_conversion.md`. **Zero model calls.**

The rule this installs
----------------------
Canonical substrate format is markdown with YAML frontmatter. Admission requires
convertibility. A document is admitted only when (a) it is already markdown, or (b) the
registry declares its format and conversion succeeds *adequately*, or (c) it fails either
test -- in which case admission STILL RECORDS the document, and the system emits
`conversion_gap` and registers a ResearchTask naming the gap.

(c) is the whole point. The alternative designs both fail:
  - refusing admission loses a document the operator deliberately acquired;
  - admitting silently is what produced the counterexample -- `slsa-specification-v1-0`
    entered the corpus, converted "successfully" to 514 characters of navigation, and was
    only noticed when a burn tried to extract it eight days later.
Detection at admission, improvement launched by the system, per-item operator review nowhere.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from kg import eventlog
from kg.ingest import convert as C

_REPO = Path(__file__).resolve().parent.parent.parent

#: Ingestion/conversion shard. Untagged: substrate provenance is graph history, not an arm.
INGEST_BATCH = 24
GAP_EVENT = "conversion_gap"
OK_EVENT = "substrate_converted"


def _existing_gap_tasks() -> dict[str, str]:
    """{doc_id: artifact_id} for gaps that already launched a task, so a re-run does not mint
    a duplicate ResearchTask. Read from the event log, which is the durable record; the
    Seldon graph is queried through it rather than the other way round."""
    out = {}
    for ev in eventlog.replay():
        if ev.get("event_type") == GAP_EVENT and ev.get("research_task_id"):
            out[ev["doc_id"]] = ev["research_task_id"]
    return out


def register_gap_task(doc_id: str, gap_class: str, detail: dict) -> str | None:
    """Create the ResearchTask that IS the improvement launch. Returns its artifact id.

    A failure to reach Seldon is reported, never swallowed: the gap event still lands, and the
    absent task id on it is the visible signal that the launch did not happen."""
    desc = (f"Conversion gap [{gap_class}] on {doc_id}: "
            f"{json.dumps(detail, sort_keys=True)[:900]} "
            f"-- emitted by the admission convertibility gate "
            f"(cc_tasks/2026-08-31_ingestion_conversion.md). Resolve by extending the "
            f"converter registry, or by re-acquiring the document at the correct extent, "
            f"then re-run `python -m kg.ingest.gate --doc {doc_id}`.")
    r = subprocess.run(
        ["seldon", "artifact", "create", "ResearchTask", "--actor", "cc",
         "-p", f"description={desc}"],
        capture_output=True, text=True, cwd=_REPO)
    if r.returncode != 0:
        print(f"  WARN seldon task registration failed for {doc_id}: "
              f"{(r.stderr or r.stdout).strip()[:200]}")
        return None
    line = (r.stdout or "").strip().splitlines()[-1]
    return line.split(":")[-1].strip() or None


def check(doc_id: str, src: Path, meta: dict | None = None, *,
          write: bool = True, launch_task: bool = True) -> dict:
    """Run the gate for one admitted document. Emits exactly one event either way."""
    try:
        dest, report = C.convert(doc_id, src, meta, write=write)
    except C.ConversionGap as gap:
        known = _existing_gap_tasks()
        task_id = known.get(doc_id)
        if launch_task and not task_id:
            task_id = register_gap_task(doc_id, gap.gap_class, gap.detail)
        eventlog.append({"event_type": GAP_EVENT, "doc_id": doc_id,
                         "gap_class": gap.gap_class, "detail": gap.detail,
                         "source_path": C._rel(src),
                         "research_task_id": task_id,
                         "task": "cc_tasks/2026-08-31_ingestion_conversion.md"},
                        batch=INGEST_BATCH)
        return {"doc_id": doc_id, "ok": False, "gap_class": gap.gap_class,
                "detail": gap.detail, "research_task_id": task_id}
    eventlog.append({"event_type": OK_EVENT, "doc_id": doc_id,
                     "substrate_path": report.get("substrate_path"),
                     "converter": report.get("converter"),
                     "source_sha256": report.get("source_sha256"),
                     "visible_chars": report.get("visible_chars"),
                     "link_density": report.get("link_density"),
                     "converted_chars": report.get("converted_chars"),
                     "task": "cc_tasks/2026-08-31_ingestion_conversion.md"},
                    batch=INGEST_BATCH)
    return {"doc_id": doc_id, "ok": True, **report}


def gaps() -> dict[str, dict]:
    """{doc_id: latest gap} for documents whose substrate is still missing.

    A later `substrate_converted` for the same doc closes the gap -- that is how a re-acquired
    document stops being reported without any event being edited."""
    out: dict[str, dict] = {}
    for ev in eventlog.replay():
        t = ev.get("event_type")
        if t == GAP_EVENT:
            out[ev["doc_id"]] = ev
        elif t == OK_EVENT:
            out.pop(ev.get("doc_id"), None)
    return out


def substrate_path(doc_id: str) -> Path | None:
    """The converted substrate for a document, if the gate produced one."""
    p = C._SUBSTRATE_DIR / f"{doc_id}.md"
    return p if p.is_file() else None


def main(argv=None) -> int:
    import argparse
    from kg import queue
    ap = argparse.ArgumentParser(prog="python -m kg.ingest.gate")
    ap.add_argument("--doc", action="append", help="doc_id (repeatable); default: all admitted")
    ap.add_argument("--dry-run", action="store_true", help="assess, write nothing, emit nothing")
    ap.add_argument("--no-task", action="store_true", help="do not register ResearchTasks")
    a = ap.parse_args(argv)

    included = queue.included_documents()
    targets = a.doc or sorted(included)
    rows = []
    for doc_id in targets:
        entry = included.get(doc_id)
        if not entry:
            print(f"SKIP  {doc_id}: not manifest-included"); continue
        rel = (entry.get("identity") or {}).get("canonical_path")
        if not rel:
            print(f"SKIP  {doc_id}: no canonical_path"); continue
        src = _REPO / rel
        if src.suffix.lower() in C.DELEGATED:
            continue                      # PDFs: existing T1 path, out of scope
        meta = {"source_url": (entry.get("identity") or {}).get("source_url"),
                "version": (entry.get("identity") or {}).get("pub_year"),
                "acquired_at": (entry.get("acquisition") or {}).get("acquired_at")}
        if a.dry_run:
            try:
                _, rep = C.convert(doc_id, src, meta, write=False)
                print(f"OK    {doc_id}: {rep['converter']} "
                      f"visible={rep['visible_chars']:,} link_density={rep['link_density']:.2f}")
            except C.ConversionGap as g:
                print(f"GAP   {doc_id}: {g.gap_class} — {g.detail.get('why') or g.detail}")
            continue
        r = check(doc_id, src, meta, launch_task=not a.no_task)
        rows.append(r)
        print(("OK    " if r["ok"] else "GAP   ") + doc_id +
              (f": {r['converter']} -> {r['substrate_path']}" if r["ok"]
               else f": {r['gap_class']} — {r['detail'].get('why') or r['detail']}"
                    f"  task={r.get('research_task_id')}"))
    if rows:
        print(f"\nconverted {sum(1 for r in rows if r['ok'])}, "
              f"gaps {sum(1 for r in rows if not r['ok'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
