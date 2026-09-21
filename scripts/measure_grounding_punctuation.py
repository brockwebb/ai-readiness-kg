#!/usr/bin/env python3
"""Read-only count: how many grounding-miss quarantines flip to grounded under a punctuation fold.

Task cc_tasks/2026-09-20_g4_resourcing_release_date_grounding_fold.md decision 7. This does NOT
change ``kg.extraction.grounding.normalize``; it only measures what a fold WOULD do, applied to
both span and source. Prior art for the fold classes: Unicode confusables / compatibility
foldings; W3C Web Annotation TextQuoteSelector anchoring.

Population: the bulk-v1 raw responses (``events/raw/bulk_v1``), re-parsed with the live parser;
every item quarantined with reason "grounding_span not found in source text" (parser.py:234,
277, 324). Source text is the substrate the run extracted from (DD-030 substrate, else pypdf on
corpus/bulk/<doc>.pdf, via run_bulk_extraction.doc_text). Runtime is seconds (no model or network calls), so no checkpoint
machinery (~/GitHub/CLAUDE.md §15 scope: >2 min or paid/networked loops only).

Usage: python scripts/measure_grounding_punctuation.py [--out PATH] [--seed N] [--sample N]
"""
from __future__ import annotations

import argparse
import collections
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from kg.extraction import grounding, parser, schema_loader  # noqa: E402
from kg.extraction.model_stub import _extract_json  # noqa: E402

RAW_DIR = ROOT / "events" / "raw" / "bulk_v1"
MISS = "grounding_span not found in source text"

# Fold classes (task decision 7). Order is reporting order.
FOLD_CLASSES = {
    "single_quote": ("‘’‛′", "'"),
    "double_quote": ("“”‟″", '"'),
    "dash": ("‐‑‒–—―−", "-"),
    "space": ("  ", " "),
    "ellipsis": ("…", "..."),
}


def fold(text: str, classes=None) -> str:
    for name, (chars, repl) in FOLD_CLASSES.items():
        if classes is not None and name not in classes:
            continue
        for c in chars:
            text = text.replace(c, repl)
    return text


def grounded_folded(span: str, source: str) -> bool:
    return grounding.is_grounded(fold(span), fold(source))


def classes_present(span: str) -> list[str]:
    return [n for n, (chars, _) in FOLD_CLASSES.items() if any(c in span for c in chars)]


_TEXT_CACHE: dict[str, tuple[str, str] | None] = {}


def load_source(doc_id: str):
    """(text, rendering) exactly as the bulk runner read it: run_bulk_extraction.doc_text (DD-030
    substrate when present, else pypdf for a PDF). None when the binary is not on disk."""
    if doc_id not in _TEXT_CACHE:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_rbe", ROOT / "scripts" / "run_bulk_extraction.py")
        rbe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rbe)
        path = next((p for d in ("corpus/bulk", "corpus/bulk_md") for p in sorted((ROOT / d).glob(f"{doc_id}.*"))), None)
        if path is None:
            _TEXT_CACHE[doc_id] = None
        else:
            rendering = "pypdf" if path.suffix.lower() == ".pdf" else "substrate/md"
            _TEXT_CACHE[doc_id] = (rbe.doc_text(path, doc_id), rendering)
    return _TEXT_CACHE[doc_id]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "logs" / "grounding_punctuation.json"))
    ap.add_argument("--seed", type=int, default=20260920)
    ap.add_argument("--sample", type=int, default=20)
    a = ap.parse_args()
    t0 = time.time()
    schema = schema_loader.load_schema()
    rng = random.Random(a.seed)

    pop, flips, controls, skipped = [], [], [], []
    n_docs = 0
    for raw in sorted(RAW_DIR.glob("*.json")):
        rec = json.loads(raw.read_text())
        doc_id = rec["doc_id"]
        loaded = load_source(doc_id)
        if loaded is None or rec.get("error") or not rec.get("raw_result"):
            skipped.append({"doc_id": doc_id, "why": "no source on disk" if loaded is None else "no raw_result/error"})
            continue
        source, rendering = loaded
        try:
            output = _extract_json(rec["raw_result"])
            output["document_id"] = doc_id
            res = parser.parse_extraction(output, source, schema)
        except Exception as e:  # noqa: BLE001 - recorded as a row, not swallowed
            skipped.append({"doc_id": doc_id, "why": f"parse failed: {type(e).__name__}: {e}"})
            continue
        n_docs += 1
        for q in res.quarantined:
            if q["reason"] != MISS:
                continue
            item = q["item"]
            span = item.get("grounding_span", "")
            row = {"doc_id": doc_id, "kind": q["kind"], "span": span,
                   "rendering": rendering, "classes": classes_present(span)}
            pop.append(row)
            if grounded_folded(span, source):
                flips.append(row)
        # inverse control: spans that ARE grounded must stay grounded under the fold
        for layer in output.values():
            for it in (layer if isinstance(layer, list) else []):
                sp = it.get("grounding_span", "") if isinstance(it, dict) else ""
                if sp and grounding.is_grounded(sp, source):
                    controls.append((sp, source))

    by_class = collections.Counter()
    for r in flips:
        src = load_source(r["doc_id"])[0]
        alone = [c for c in FOLD_CLASSES if grounding.is_grounded(fold(r["span"], {c}), fold(src, {c}))]
        r["flips_under_single_class"] = alone
        for c in (alone or ["combination"]):
            by_class[c] += 1

    rng.shuffle(controls)
    ctl = controls[:500]
    lost = sum(1 for sp, src in ctl if grounding.is_grounded(sp, src) and not grounded_folded(sp, src))

    sample = rng.sample(flips, min(a.sample, len(flips)))
    for r in sample:
        src = load_source(r["doc_id"])[0]
        n = grounding.normalize(fold(r["span"]))
        ns = grounding.normalize(fold(src))
        i = ns.find(n)
        r["source_passage"] = ns[max(0, i - 40): i + len(n) + 40] if i >= 0 else None

    out = {
        "population_scope": str(RAW_DIR.relative_to(ROOT)),
        "docs_parsed": n_docs, "docs_skipped": skipped,
        "grounding_miss_population": len(pop),
        "flip_to_grounded": len(flips),
        "flip_rate": round(len(flips) / len(pop), 4) if pop else None,
        "flips_by_single_class": dict(by_class),
        "flips_by_document": dict(collections.Counter(r["doc_id"] for r in flips)),
        "flips_by_rendering_dir": dict(collections.Counter(r["rendering"] for r in flips)),
        "population_by_kind": dict(collections.Counter(r["kind"] for r in pop)),
        "inverse_control": {"n": len(ctl), "grounded_lost_under_fold": lost},
        "sample_seed": a.seed, "sample": sample,
        "seconds": round(time.time() - t0, 1),
    }
    Path(a.out).parent.mkdir(exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in out.items() if k not in ("sample", "docs_skipped", "flips_by_document")}, indent=1))
    print("skipped:", len(skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
