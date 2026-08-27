#!/usr/bin/env python3
"""Backfill Document.construct_arm for the pre-existing corpus (task 2026-08-24_source_triage
Phase 0; schema v0.3.3).

Rule and per-document assignments: scripts/construct_arm_backfill.yaml. One
`document_annotation` event per included document is appended to events/batch-014.jsonl
(the triage shard) — never rewritten; a re-run appends a new annotation only when the value
or rule version changed (same idempotence contract as annotate_platform_operator.py).
Writes the per-doc decision table to docs/research/2026-08-24_triage_backfill_report.md.

Coverage is validated before any event is written: every included v1-epoch doc must appear
in exactly one arm list; a kernel override must name a kernel member; any gap is a hard
error (standard 4 — fail loud, write nothing).
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

RULE_FILE = REPO / "scripts" / "construct_arm_backfill.yaml"
DIXIE_LEDGER = REPO / "corpus" / "evidence" / "decisions.jsonl"
MANIFEST = REPO / "corpus" / "manifest.json"
ANNOTATION_BATCH = 14         # events/batch-014.jsonl — the 2026-08-24 triage shard
TASK = "cc_tasks/2026-08-24_source_triage.md"
OUT = REPO / "docs" / "research" / "2026-08-24_triage_backfill_report.md"
ARMS = ("publication_actionability", "training_data_readiness", "org_maturity")


def epoch_members() -> dict[str, set[str]]:
    epochs: dict[str, set[str]] = {}
    for line in DIXIE_LEDGER.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        ev = json.loads(line)
        if ev.get("event_type") == "corpus_epoch_declared":
            p = ev["payload"]
            epochs[p["epoch"]] = set(p["member_doc_ids"])
    return epochs


def included_docs() -> dict[str, str]:
    """doc_id -> title for every entry the evidence-ledger projection includes."""
    m = json.loads(MANIFEST.read_text(encoding="utf-8"))["entries"]
    return {d: e["identity"]["title"] for d, e in m.items()
            if e["screening"]["decision"] == "included"}


def existing_annotations() -> dict[str, dict]:
    out = {}
    for ev in eventlog.replay():
        if ev.get("event_type") == "document_annotation" and \
                ev.get("property") == "construct_arm":
            out[ev["doc_id"]] = ev
    return out


def build_assignments(rule: dict, included: dict[str, str],
                      epochs: dict[str, set[str]]) -> dict[str, tuple[str, str]]:
    """doc_id -> (arm, rationale). Hard-errors on any coverage gap."""
    kernel = epochs.get("kernel-v03", set())
    v1 = set(included) - kernel
    overrides = rule.get("kernel_overrides") or {}
    for doc_id in overrides:
        if doc_id not in kernel:
            raise SystemExit(f"FATAL: kernel override {doc_id!r} is not a kernel-v03 member")

    listed: dict[str, str] = {}
    for arm, ids in (rule.get("v1_assignments") or {}).items():
        if arm not in ARMS:
            raise SystemExit(f"FATAL: unknown arm {arm!r} in v1_assignments")
        for doc_id in ids or []:
            if doc_id in listed:
                raise SystemExit(f"FATAL: {doc_id!r} listed under both "
                                 f"{listed[doc_id]!r} and {arm!r}")
            listed[doc_id] = arm
    missing = sorted(v1 - set(listed))
    extra = sorted(set(listed) - v1)
    if missing or extra:
        raise SystemExit(f"FATAL: v1 assignment coverage gap — missing={missing} extra={extra}")

    out: dict[str, tuple[str, str]] = {}
    for doc_id in sorted(included):
        if doc_id in kernel:
            ov = overrides.get(doc_id)
            if ov:
                out[doc_id] = (ov["arm"], f"kernel override: {ov['reason'].strip()}")
            else:
                out[doc_id] = (rule["kernel_default"],
                               "kernel-v03 default: " + rule["kernel_default_rationale"].strip())
        else:
            out[doc_id] = (listed[doc_id],
                           f"v1 title/abstract rule — listed under {listed[doc_id]} in "
                           f"{RULE_FILE.relative_to(REPO)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    rule = yaml.safe_load(RULE_FILE.read_text(encoding="utf-8"))
    included = included_docs()
    assignments = build_assignments(rule, included, epoch_members())
    prior = existing_annotations()

    rows, written, unchanged = [], 0, 0
    for doc_id, (arm, why) in assignments.items():
        rows.append((doc_id, arm, why))
        prev = prior.get(doc_id)
        if prev and prev.get("value") == arm and prev.get("rule_version") == rule["rule_version"]:
            unchanged += 1
            continue
        if not a.dry_run:
            eventlog.append({
                "event_type": "document_annotation",
                "doc_id": doc_id,
                "property": "construct_arm",
                "value": arm,
                "rule": str(RULE_FILE.relative_to(REPO)),
                "rule_version": rule["rule_version"],
                "rationale": why,
                "task": TASK,
            }, batch=ANNOTATION_BATCH)
        written += 1

    if not a.dry_run:
        counts = {arm: sum(1 for _, x, _ in rows if x == arm) for arm in ARMS}
        lines = [
            "# construct_arm backfill decision table — task 2026-08-24_source_triage Phase 0",
            "",
            f"Rule: `{RULE_FILE.relative_to(REPO)}` version {rule['rule_version']}; "
            f"events in `events/batch-{ANNOTATION_BATCH:03d}.jsonl`.",
            "",
            f"Documents: {len(rows)} | written: {written} | unchanged: {unchanged} | "
            + " | ".join(f"{k}: {v}" for k, v in counts.items()),
            "",
            "| doc_id | construct_arm | rationale |",
            "|---|---|---|",
        ]
        for doc_id, arm, why in rows:
            lines.append(f"| {doc_id} | {arm} | {why.splitlines()[0][:160]} |")
        OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"report: {OUT.relative_to(REPO)}")
    print(f"docs {len(rows)} | annotations written {written} | unchanged {unchanged}"
          + (" (dry-run: no events appended)" if a.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
