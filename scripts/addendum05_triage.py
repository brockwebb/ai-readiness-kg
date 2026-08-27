#!/usr/bin/env python3
"""ADDENDUM-05 §3a — mechanical triage of suppressed semantic-edge candidates. ZERO spend.

Two populations, both over the 5 pilot docs:
  P1: every proposed_relationships entry from the v0.3.5b (opus-5) pilot extractions
      (re-parsed from the persisted raws — the lane did not stage them separately).
  P2: every kernel/v1-era semantic edge still live in the projection for the same docs.

For each candidate: locate both endpoint surface forms (name, or a recorded alias) and a
predicate cue (kg/extraction/edge_cues.yaml, sha-pinned in the report) in the normalized
document text. Classify:
  single_span   endpoints + cue inside ONE sentence  -> the v0.3.5 rule should have
                admitted it (model over-diverted)
  evidence_set  endpoints + cue within <= 3 consecutive sentences and <= 800 chars
  unlocatable   some element not found within the 800-char window anywhere

Outputs: corpus/staging/metrics/edge_suppression_candidates.jsonl (one record per
candidate with its class and located evidence) and
docs/research/2026-08-27_edge_suppression_triage.md (counts per doc and pooled).
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "scripts"))

import yaml                                              # noqa: E402
from kg import eventlog                                  # noqa: E402
from kg.extraction import model_stub, parser             # noqa: E402
from kg.extraction.grounding import normalize            # noqa: E402
from kg.extraction.pipeline import _apply_provenance_ownership  # noqa: E402
import run_bulk_extraction as rbe                        # noqa: E402

PILOT_DOCS = ["data-readiness-for-ai-a-360-degree-survey", "aidrin-hiniduma-2024",
              "fcsm-23-02-a-framework-for-data-quality-case-studies",
              "from-accuracy-to-readiness-metrics-and-benchmarks-for-human",
              "mitre-ai-maturity-model"]
RAW_DIR = REPO / "events/raw/reextract_v035b_pilot"
CUES_PATH = REPO / "kg/extraction/edge_cues.yaml"
OUT_JSONL = REPO / "corpus/staging/metrics/edge_suppression_candidates.jsonl"
OUT_MD = REPO / "docs/research/2026-08-27_edge_suppression_triage.md"
WINDOW_CHARS = 800
WINDOW_SENTS = 3
SEMANTIC = parser.SEMANTIC_EDGE_TYPES

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


def sentences(norm_text: str) -> list[tuple[int, int, str]]:
    """(start, end, text) per sentence over the normalized doc."""
    out, pos = [], 0
    for part in _SENT_SPLIT.split(norm_text):
        start = norm_text.find(part, pos)
        if start < 0:
            start = pos
        out.append((start, start + len(part), part))
        pos = start + len(part)
    return out


def merged_pilot_output(raw_result: str) -> dict | None:
    """Re-derive the parsed output from a persisted raw (single-pass or per-layer)."""
    parts = raw_result.split("\n\n---PER_LAYER_TURN---\n\n")
    merged: dict = {}
    for part in parts:
        if not part.strip():
            continue
        try:
            out = model_stub._extract_json(part)
        except model_stub.ModelInvocationError:
            continue
        if isinstance(out, dict):
            for k, v in out.items():
                if isinstance(v, list) and v:
                    merged[k] = v
    return merged or None


def surface_forms(item: dict | None, fallback_id: str) -> list[str]:
    forms = []
    for key in ("name", "term", "text"):
        v = (item or {}).get(key)
        if isinstance(v, str) and v.strip():
            forms.append(v)
    for a in (item or {}).get("aliases") or []:
        if isinstance(a, str) and a.strip():
            forms.append(a)
    if not forms and fallback_id:
        # id like c-data-quality -> "data quality" (last-resort surface form)
        forms.append(re.sub(r"^[a-z]{1,3}[-_]", "", fallback_id).replace("-", " ").replace("_", " "))
    return forms


def find_all(hay: str, needle: str) -> list[int]:
    out, i = [], hay.find(needle)
    while i >= 0:
        out.append(i)
        i = hay.find(needle, i + 1)
    return out


def classify(norm: str, sents, from_forms, to_forms, cues) -> tuple[str, dict | None]:
    low = norm.lower()
    f_pos = [p for f in from_forms for p in find_all(low, normalize(f).lower())]
    t_pos = [p for f in to_forms for p in find_all(low, normalize(f).lower())]
    c_pos = [p for c in cues for p in find_all(low, c)]
    if not f_pos or not t_pos or not c_pos:
        return "unlocatable", None
    best = None
    for fp in f_pos:
        for tp in t_pos:
            if abs(fp - tp) > WINDOW_CHARS:
                continue
            lo, hi = min(fp, tp), max(fp, tp)
            near_cues = [cp for cp in c_pos if lo - 200 <= cp <= hi + 200
                         and max(fp, tp, cp) - min(fp, tp, cp) <= WINDOW_CHARS]
            if not near_cues:
                continue
            cp = near_cues[0]
            span_lo, span_hi = min(lo, cp), max(hi, cp)
            covering = [i for i, (s, e, _) in enumerate(sents) if e > span_lo and s < span_hi]
            n_sent = (covering[-1] - covering[0] + 1) if covering else 99
            cand = (n_sent, span_hi - span_lo, covering)
            if best is None or cand[:2] < best[0][:2]:
                best = (cand, covering)
    if best is None:
        return "unlocatable", None
    (n_sent, width, covering), _ = best
    if not covering:
        return "unlocatable", None
    ev_sents = [sents[i][2] for i in range(covering[0], covering[-1] + 1)]
    evidence = {"n_sentences": n_sent, "char_width": width, "sentences": ev_sents[:4]}
    if n_sent == 1:
        return "single_span", evidence
    if n_sent <= WINDOW_SENTS and width <= WINDOW_CHARS:
        return "evidence_set", evidence
    return "unlocatable", None


def main() -> int:
    cues_doc = yaml.safe_load(CUES_PATH.read_text(encoding="utf-8"))
    cues_by_type = {k: [c.lower() for c in v] for k, v in cues_doc["cues"].items()}
    cues_sha = hashlib.sha256(CUES_PATH.read_bytes()).hexdigest()

    members = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof)
        members.update(rbe.corpus_members())

    # live node names per doc (P2 endpoint resolution)
    live_nodes: dict[str, dict[str, dict]] = defaultdict(dict)
    live_sem_edges: dict[str, list[dict]] = defaultdict(list)
    for ev in eventlog.replay():
        if ev.get("purpose") in ("tevv_retest", "probe", "benchmark", "reextract"):
            continue
        p = ev.get("payload") or {}
        if ev.get("event_type") == "node_asserted" and ev.get("doc_id") in PILOT_DOCS:
            live_nodes[ev["doc_id"]][p.get("id")] = p.get("item") or {}
        elif ev.get("event_type") == "edge_asserted" and ev.get("doc_id") in PILOT_DOCS \
                and p.get("type") in SEMANTIC:
            live_sem_edges[ev["doc_id"]].append(p)

    records = []
    for d in PILOT_DOCS:
        if d not in members:
            print(f"WARN: {d} not in corpus members; skipped", flush=True)
            continue
        norm = normalize(rbe.doc_text(members[d]))
        sents = sentences(norm)
        # P1: proposed_relationships from the opus-5 pilot raws
        raws = sorted(RAW_DIR.glob(f"{d}.*.json"))
        n_p1 = 0
        if raws:
            raw = json.loads(raws[-1].read_text())
            out = merged_pilot_output(raw.get("raw_result") or "")
            if out:
                out = _apply_provenance_ownership(out, d)
                res = parser.parse_extraction(out, norm, enforce_span_coverage=True)
                id_items = {n["id"]: n["item"] for n in res.nodes}
                # also include quarantined nodes' items for surface forms
                for q in res.quarantined:
                    it = q.get("item") or {}
                    if it.get("id") and it["id"] not in id_items:
                        id_items[it["id"]] = it
                for pr in res.proposed_relationships:
                    et = pr.get("suggested_edge")
                    if et not in SEMANTIC:
                        continue
                    n_p1 += 1
                    ff = surface_forms(id_items.get(pr.get("from_id")), pr.get("from_id") or "")
                    tf = surface_forms(id_items.get(pr.get("to_id")), pr.get("to_id") or "")
                    cls, ev_ = classify(norm, sents, ff, tf, cues_by_type[et])
                    records.append({"population": "p1_proposed_v035b", "doc_id": d,
                                    "edge_type": et, "from": ff[:1], "to": tf[:1],
                                    "class": cls, "evidence": ev_,
                                    "source": pr.get("source")})
        # P2: kernel/v1-era live semantic edges
        for e in live_sem_edges.get(d, []):
            et = e["type"]
            ff = surface_forms(live_nodes[d].get(e.get("from_id")), e.get("from_id") or "")
            tf = surface_forms(live_nodes[d].get(e.get("to_id")), e.get("to_id") or "")
            cls, ev_ = classify(norm, sents, ff, tf, cues_by_type[et])
            records.append({"population": "p2_live_kernel_era", "doc_id": d,
                            "edge_type": et, "from": ff[:1], "to": tf[:1],
                            "class": cls, "evidence": ev_})
        print(f"{d}: P1 {n_p1} proposed, P2 {len(live_sem_edges.get(d, []))} live", flush=True)

    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records),
                         encoding="utf-8")
    # report
    def block(pop: str) -> list[str]:
        rows = [r for r in records if r["population"] == pop]
        pooled = Counter(r["class"] for r in rows)
        lines = [f"### {pop} (n={len(rows)})", "",
                 "| doc | single_span | evidence_set | unlocatable |", "|---|---|---|---|"]
        for d in PILOT_DOCS:
            c = Counter(r["class"] for r in rows if r["doc_id"] == d)
            lines.append(f"| `{d}` | {c.get('single_span', 0)} | {c.get('evidence_set', 0)} "
                         f"| {c.get('unlocatable', 0)} |")
        lines.append(f"| **pooled** | **{pooled.get('single_span', 0)}** | "
                     f"**{pooled.get('evidence_set', 0)}** | **{pooled.get('unlocatable', 0)}** |")
        return lines

    pooled_all = Counter(r["class"] for r in records)
    locatable = pooled_all.get("single_span", 0) + pooled_all.get("evidence_set", 0)
    md = ["# Edge-suppression mechanical triage (ADDENDUM-05 §3a) — zero spend", "",
          f"Cue list: `kg/extraction/edge_cues.yaml` sha256 `{cues_sha[:16]}…` "
          f"(version {cues_doc['edge_cues_version']}). Window: ≤ {WINDOW_SENTS} sentences "
          f"and ≤ {WINDOW_CHARS} chars. Candidates: `{OUT_JSONL.relative_to(REPO)}`.", "",
          *block("p1_proposed_v035b"), "", *block("p2_live_kernel_era"), "",
          f"**Pooled locatable (single_span + evidence_set): {locatable}** "
          f"(3b proceeds iff ≥ 20; single_span pooled = "
          f"{pooled_all.get('single_span', 0)} would indicate model over-diversion under "
          f"the current rule).", ""]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"pooled: {dict(pooled_all)} | locatable {locatable}")
    print("report:", OUT_MD.relative_to(REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
