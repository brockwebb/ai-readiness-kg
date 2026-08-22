#!/usr/bin/env python3
"""Populate Document.is_platform_operator for every manifested document (task
2026-08-22_kernel_tevv Phase 0; schema v0.3.1; DD-014).

Rule and lexicon: scripts/platform_operators.yaml. One `document_annotation` event per doc is
appended to events/batch-007.jsonl (never rewritten — re-running appends a new annotation
only when the value or rule version changed). Writes the per-doc decision table to
docs/research/2026-08-22_tevv_platform_operator_decisions.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import yaml  # noqa: E402
from kg import eventlog  # noqa: E402

LEXICON = REPO / "scripts" / "platform_operators.yaml"
ANNOTATION_BATCH = 7          # events/batch-007.jsonl — document annotations (task-declared)
RULE_VERSION = "2026-08-22.1"
OUT = REPO / "docs" / "research" / "2026-08-22_tevv_platform_operator_decisions.md"


def load_lexicon() -> list[dict]:
    doc = yaml.safe_load(LEXICON.read_text(encoding="utf-8"))
    if not doc.get("operators"):
        raise SystemExit(f"FATAL: no operators in {LEXICON}")
    return doc["operators"]


def decide(authors: list[str], lexicon: list[dict]) -> tuple[bool, str]:
    text = " ; ".join(authors).lower() + " "
    for entry in lexicon:
        if entry["match"].lower() in text:
            why = f"author matches '{entry['match']}' — operates {entry['operates']}"
            if entry.get("note"):
                why += f" [{entry['note']}]"
            return True, why
    return False, "no operator organization among authors"


def current_docs() -> dict[str, dict]:
    docs = {}
    for ev in eventlog.replay():
        if ev.get("event_type") == "manifest_add":
            p = ev["payload"]; docs[p["doc_id"]] = p        # latest manifest_add wins
    return docs


def existing_annotations() -> dict[str, dict]:
    out = {}
    for ev in eventlog.replay():
        if ev.get("event_type") == "document_annotation" and \
                ev.get("property") == "is_platform_operator":
            out[ev["doc_id"]] = ev
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    lex = load_lexicon()
    docs = current_docs()
    prior = existing_annotations()
    rows, written, unchanged = [], 0, 0
    for doc_id in sorted(docs):
        p = docs[doc_id]
        value, why = decide(p.get("authors") or [], lex)
        rows.append((doc_id, p["source_type"], "; ".join(p.get("authors") or [])[:60], value, why))
        prev = prior.get(doc_id)
        if prev and prev.get("value") == value and prev.get("rule_version") == RULE_VERSION:
            unchanged += 1
            continue
        if not a.dry_run:
            eventlog.append({"event_type": "document_annotation", "doc_id": doc_id,
                             "property": "is_platform_operator", "value": value,
                             "rule": "scripts/platform_operators.yaml",
                             "rule_version": RULE_VERSION, "rationale": why,
                             "task": "cc_tasks/2026-08-22_kernel_tevv.md"},
                            batch=ANNOTATION_BATCH)
        written += 1
    n_true = sum(1 for r in rows if r[3])
    lines = ["# Document.is_platform_operator — rule decisions (task 2026-08-22_kernel_tevv, Phase 0)", "",
             f"Rule version `{RULE_VERSION}`, lexicon `scripts/platform_operators.yaml`, events `events/batch-007.jsonl`.",
             f"Documents: {len(rows)} · true: {n_true} · false: {len(rows) - n_true}.", "",
             "| doc_id | source_type | authors | is_platform_operator | rationale |", "|---|---|---|---|---|"]
    for d, st, au, v, why in rows:
        lines.append(f"| `{d}` | {st} | {au} | **{str(v).lower()}** | {why} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"docs {len(rows)} | true {n_true} | events written {written} | unchanged {unchanged} | {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
