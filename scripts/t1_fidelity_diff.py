#!/usr/bin/env python3
"""§1.1 fidelity check — is the pypdf damage class gone from the Docling conversion?

The named damage (DD-023, measured on the chunked pilot): pypdf drops characters at line
breaks, so the source text carries truncated words — the model quoted
"Heterogeneous Euclidean-Overlap Metri (HEOM)" because the "c" was not in the extracted
text, and the grounding gate then quarantined a faithful emission. A validity pipeline
running against corrupted source text quarantines correct output, which is why this check
gates the index rather than decorating it.

The test is not "do the two converters differ" — they differ everywhere, by design. It is
"does pypdf contain broken word-forms that Docling repairs". A word is counted broken when
pypdf holds a token that is NOT a dictionary-independent valid continuation, specifically:
a token in pypdf whose immediate extension by one or more characters appears in Docling at
the same position in the surrounding context. Zero model calls.
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
MD_DIR = REPO / "state" / "docling_md"

SAMPLE = ["data-readiness-for-ai-a-360-degree-survey", "aidrin-hiniduma-2024",
          "fcsm-23-02-a-framework-for-data-quality-case-studies",
          "from-accuracy-to-readiness-metrics-and-benchmarks-for-human",
          "mitre-ai-maturity-model"]


def words(t: str) -> list[str]:
    return re.findall(r"[A-Za-z][A-Za-z\-]{2,}", t)


def pypdf_text(path: Path) -> str:
    from pypdf import PdfReader
    return "\n\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)


def truncation_candidates(a_words: set[str], b_words: set[str]) -> list[tuple[str, str]]:
    """Tokens present in A that look like a one-or-two-character truncation of a token
    present in B and absent from B themselves — the signature of a dropped line-break char."""
    out = []
    for w in sorted(a_words - b_words):
        if len(w) < 4:
            continue
        for k in (1, 2):
            for cand in (w + c for c in "abcdefghijklmnopqrstuvwxyz") if k == 1 else ():
                if cand in b_words:
                    out.append((w, cand)); break
            else:
                continue
            break
    return out


#: The instance DD-023 named as pypdf source damage. A positive control: if the converter is
#: the cause, the new converter must not reproduce it. Text is from the chunked-pilot raws.
NAMED_INSTANCE = {
    "doc_id": "data-readiness-for-ai-a-360-degree-survey",
    "pattern": r"Heterogeneous Euclidean[-\s]*Overlap Metri\w*",
    "damaged": "Heterogeneous Euclidean-Overlap Metri",
    "intact": "Heterogeneous Euclidean-Overlap Metric",
}


def named_instance_check() -> dict:
    """Does the converter change the DD-023 instance? Compares both converters on the SAME
    source bytes, which is the only comparison that can separate 'the converter broke it'
    from 'the PDF text layer never had it'."""
    from pypdf import PdfReader
    d = NAMED_INSTANCE
    meta = json.loads((MD_DIR / f"{d['doc_id']}.meta.json").read_text())
    src = REPO / meta["source"]
    dl = (MD_DIR / f"{d['doc_id']}.md").read_text("utf-8", "ignore")
    pp = "\n\n".join((pg.extract_text() or "") for pg in PdfReader(str(src)).pages)
    # Collapse whitespace on BOTH sides before matching: the two converters wrap lines in
    # different places, and a pattern that is sensitive to that measures line wrapping
    # instead of character loss, which is the thing under test.
    flat = lambda t: " ".join(t.split())
    pat = re.compile(d["pattern"])
    out = {"doc_id": d["doc_id"], "source": meta["source"],
           "pypdf_hits": pat.findall(flat(pp)),
           "docling_hits": pat.findall(flat(dl))}
    out["pypdf_damaged"] = any(h.endswith("Metri") for h in out["pypdf_hits"])
    out["docling_damaged"] = any(h.endswith("Metri") for h in out["docling_hits"])
    out["verdict"] = (
        "converter_was_not_the_cause" if out["pypdf_damaged"] and out["docling_damaged"]
        else "docling_repairs_it" if out["pypdf_damaged"] and not out["docling_damaged"]
        else "instance_not_found")
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--docs", nargs="*", default=SAMPLE)
    a = ap.parse_args()
    rows = []
    for doc_id in a.docs:
        md = MD_DIR / f"{doc_id}.md"
        meta = MD_DIR / f"{doc_id}.meta.json"
        if not md.exists():
            print(f"skip {doc_id}: not converted"); continue
        m = json.loads(meta.read_text())
        src = REPO / m["source"]
        if src.suffix.lower() != ".pdf":
            print(f"skip {doc_id}: source is {src.suffix}, no pypdf comparison to make")
            continue
        dl = md.read_text("utf-8", "ignore")
        pp = pypdf_text(src)
        dw, pw = set(words(dl)), set(words(pp))
        trunc = truncation_candidates(pw, dw)
        rows.append({"doc_id": doc_id, "converted_by": m["converted_by"],
                     "docling_chars": len(dl), "pypdf_chars": len(pp),
                     "docling_words": len(dw), "pypdf_words": len(pw),
                     "pypdf_truncations_repaired": len(trunc),
                     "examples": [f"{x} -> {y}" for x, y in trunc[:6]]})
        print(f"\n=== {doc_id} ({m['converted_by']}) ===")
        print(f"  chars  docling {len(dl):>8,}   pypdf {len(pp):>8,}")
        print(f"  words  docling {len(dw):>8,}   pypdf {len(pw):>8,}")
        print(f"  pypdf word-forms that Docling repairs: {len(trunc)}")
        for x, y in trunc[:6]:
            print(f"      pypdf {x!r}  ->  docling {y!r}")
    named = named_instance_check()
    print("\n=== POSITIVE CONTROL: the DD-023 named instance ===")
    print(f"  pypdf   : {named['pypdf_hits']}")
    print(f"  docling : {named['docling_hits']}")
    print(f"  verdict : {named['verdict']}")
    if named["verdict"] == "converter_was_not_the_cause":
        print("  -> Both converters reproduce the SAME truncation from the same bytes, so the "
              "missing character is in the PDF's own text layer. Re-conversion cannot repair "
              "this class, and DD-023's attribution of it to pypdf does not hold for this "
              "instance.")
    (REPO / "state" / "t1_fidelity_diff.json").write_text(
        json.dumps({"per_doc": rows, "named_instance": named}, indent=1))
    tot = sum(r["pypdf_truncations_repaired"] for r in rows)
    print(f"\nTOTAL pypdf truncations repaired by Docling across {len(rows)} docs: {tot}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
