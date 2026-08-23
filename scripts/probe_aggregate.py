#!/usr/bin/env python3
"""Probe Phase 5 — multi-rater aggregation and the pre-registered decision rule
(task 2026-08-22_faithfulness_probe).

Raters: every agent with judge_label events in the probe shard (run=main), the sidecar
rater (tevv_human_subset_labels.jsonl, item-level label mapped onto each fact of the item —
coarse), and cross-family ingests if present. Dawid & Skene (1979) EM via crowd-kit
(DawidSkene) on the binary label at fact level; class by MAP over the not_entailed raters'
classes (majority, tie -> highest mean confidence). Wilson (1927) 95% intervals for proportions.
F = fabrication share with doc_level_attribute and grade_misassigned removed from the
denominator. Writes corpus/staging/metrics/probe_aggregate.json.
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from kg import eventlog  # noqa: E402

SAMPLE = REPO / "corpus/staging/metrics/probe_sample.jsonl"
FACTS = REPO / "corpus/staging/metrics/probe_facts.jsonl"
SIDECAR = REPO / "corpus/staging/metrics/tevv_human_subset_labels.jsonl"
CROSS = REPO / "corpus/staging/inbox/probe_crossfamily"
OUT = REPO / "corpus/staging/metrics/probe_aggregate.json"
EXCLUDED_FROM_F = {"doc_level_attribute", "grade_misassigned"}
Z = 1.959964


def wilson(k: int, n: int, z: float = Z) -> tuple[float | None, float | None, float | None]:
    if n == 0:
        return None, None, None
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0.0, c - h), min(1.0, c + h)


def load_labels() -> tuple[list[dict], dict[str, str]]:
    """Fact-level labels from all raters: [{fact_id, rater, label, class, confidence}]."""
    rows, rater_kind = [], {}
    for ev in eventlog.replay(tag="probe_judge"):
        if ev.get("event_type") != "judge_label" or ev.get("run") != "main":
            continue
        r = ev["agent"]["id"]; rater_kind[r] = ev["agent"]["type"]
        rows.append({"fact_id": ev["fact_id"], "rater": r, "label": ev["label"],
                     "class": ev.get("class"), "confidence": ev.get("confidence")})
    facts = [json.loads(l) for l in FACTS.read_text().splitlines() if l.strip()]
    by_event = defaultdict(list)
    for f in facts: by_event[f["event_id"]].append(f["fact_id"])
    if SIDECAR.is_file():
        for l in SIDECAR.read_text().splitlines():
            if not l.strip(): continue
            s = json.loads(l); r = s.get("rater", "claude-desktop-fable5"); rater_kind[r] = "prov:SoftwareAgent"
            for fid in by_event.get(s["event_id"], []):
                rows.append({"fact_id": fid, "rater": r, "label": s["human_label"], "class": None, "confidence": None})
    if CROSS.is_dir():
        for p in sorted(CROSS.glob("*.jsonl")):
            for l in p.read_text().splitlines():
                if not l.strip(): continue
                s = json.loads(l); r = s.get("agent") or "unknown_crossfamily"; rater_kind[r] = s.get("agent_type", "prov:SoftwareAgent")
                rows.append({"fact_id": s["fact_id"], "rater": r, "label": s["label"], "class": s.get("class"), "confidence": s.get("confidence")})
    return rows, rater_kind


def dawid_skene(rows: list[dict]) -> tuple[dict[str, float], dict[str, dict], str]:
    """P(entailed) per fact and per-rater confusion (estimated). crowd-kit if importable,
    else a plain EM implementation of the same model."""
    tasks = sorted({r["fact_id"] for r in rows}); raters = sorted({r["rater"] for r in rows})
    try:
        import pandas as pd
        from crowdkit.aggregation import DawidSkene
        df = pd.DataFrame([{"task": r["fact_id"], "worker": r["rater"], "label": r["label"]} for r in rows])
        ds = DawidSkene(n_iter=100).fit(df)
        probas = ds.probas_
        post = {t: float(probas.loc[t].get("entailed", 0.0)) for t in probas.index}
        err = ds.errors_   # MultiIndex (worker, label) x true-label columns
        conf = {}
        for w in raters:
            m = {}
            for true in ("entailed", "not_entailed"):
                for obs in ("entailed", "not_entailed"):
                    try: m[f"P(obs={obs}|true={true})"] = float(err.loc[(w, obs), true])
                    except KeyError: m[f"P(obs={obs}|true={true})"] = None
            conf[w] = m
        return post, conf, "crowd-kit DawidSkene(n_iter=100)"
    except ImportError:
        # minimal EM: init by majority, iterate class prior + per-rater confusion
        by_task = defaultdict(list)
        for r in rows: by_task[r["fact_id"]].append((r["rater"], r["label"]))
        post = {t: (sum(l == "entailed" for _, l in v) / len(v)) for t, v in by_task.items()}
        for _ in range(50):
            pi = sum(post.values()) / len(post)
            cm = {w: {"e|e": 1.0, "n|e": 1.0, "e|n": 1.0, "n|n": 1.0} for w in raters}  # Laplace
            for t, v in by_task.items():
                for w, l in v:
                    cm[w][("e" if l == "entailed" else "n") + "|e"] += post[t]
                    cm[w][("e" if l == "entailed" else "n") + "|n"] += 1 - post[t]
            for w in raters:
                se = cm[w]["e|e"] + cm[w]["n|e"]; sn = cm[w]["e|n"] + cm[w]["n|n"]
                cm[w] = {"e|e": cm[w]["e|e"] / se, "n|e": cm[w]["n|e"] / se, "e|n": cm[w]["e|n"] / sn, "n|n": cm[w]["n|n"] / sn}
            for t, v in by_task.items():
                pe, pn = pi, 1 - pi
                for w, l in v:
                    k = "e" if l == "entailed" else "n"
                    pe *= cm[w][k + "|e"]; pn *= cm[w][k + "|n"]
                post[t] = pe / (pe + pn) if (pe + pn) else 0.5
        conf = {w: {"P(obs=entailed|true=entailed)": cm[w]["e|e"], "P(obs=not_entailed|true=entailed)": cm[w]["n|e"],
                    "P(obs=entailed|true=not_entailed)": cm[w]["e|n"], "P(obs=not_entailed|true=not_entailed)": cm[w]["n|n"]} for w in raters}
        return post, conf, "in-repo EM (crowd-kit not importable)"


def map_class(rows_for_fact: list[dict]) -> str | None:
    votes = [(r["class"], r.get("confidence") or 0.5) for r in rows_for_fact if r["label"] == "not_entailed" and r.get("class")]
    if not votes: return None
    c = Counter(v for v, _ in votes); top = max(c.values())
    tied = [k for k, n in c.items() if n == top]
    if len(tied) == 1: return tied[0]
    mean = {k: sum(conf for v, conf in votes if v == k) / c[k] for k in tied}
    return max(mean, key=mean.get)


def doc_check_reclassify(per_fact: dict, facts: dict, items: dict) -> dict:
    """Task class definition: `fabrication` = absent from the span AND from the document.
    Judges saw a ±400-char window, not the document, so a MAP `fabrication` on a literal
    attribute fact ("steward: W3C", "year: 2020") is re-checked mechanically against the
    full normalized document text: value found -> `filled_attribute` (populated without span
    support, but document-supported), flagged doc_check=value_found_in_document. Free-text
    propositions are not substring-checkable and keep the judge's window-based call."""
    import run_bulk_extraction as rbe
    from kg.extraction.grounding import normalize
    members = {}
    for prof in ("v1", "kernel_v03"):
        rbe.apply_profile(prof); members.update(rbe.corpus_members())
    texts = {}
    stats = {"checked": 0, "reclassified": 0}
    for fid, v in per_fact.items():
        if v["class"] != "fabrication":
            continue
        f = facts[fid]
        if f.get("source") != "deterministic" or not f.get("attribute"):
            continue
        val = f["fact_text"].split(": ", 1)[1] if ": " in f["fact_text"] else f["fact_text"]
        doc = items[f["event_id"]]["doc_id"]
        if doc not in texts:
            texts[doc] = normalize(rbe.doc_text(members[doc]))
        stats["checked"] += 1
        if normalize(str(val)) and normalize(str(val)) in texts[doc]:
            v["class"] = "filled_attribute"; v["doc_check"] = "value_found_in_document"; stats["reclassified"] += 1
        else:
            v["doc_check"] = "value_absent_from_document"
    return stats


def main() -> int:
    rows, rater_kind = load_labels()
    if not rows:
        raise SystemExit("FATAL: no judge labels found")
    facts = {f["fact_id"]: f for f in (json.loads(l) for l in FACTS.read_text().splitlines() if l.strip())}
    items = {it["event_id"]: it for it in (json.loads(l) for l in SAMPLE.read_text().splitlines() if l.strip())}
    post, conf, method = dawid_skene(rows)
    by_fact = defaultdict(list)
    for r in rows: by_fact[r["fact_id"]].append(r)
    per_fact = {}
    for fid, p in post.items():
        f = facts[fid]; it = items[f["event_id"]]
        cls = map_class(by_fact[fid]) if p < 0.5 else None
        per_fact[fid] = {"p_entailed": p, "entailed": p >= 0.5, "class": cls, "stratum": it["stratum"],
                         "event_id": f["event_id"], "n_raters": len(by_fact[fid])}
    doc_check = doc_check_reclassify(per_fact, facts, items)
    # class proportions + F per stratum and pooled
    def summarize(fids):
        n = len(fids); cls = Counter(per_fact[x]["class"] or ("entailed" if per_fact[x]["entailed"] else "unclassified") for x in fids)
        denom = [x for x in fids if (per_fact[x]["class"] not in EXCLUDED_FROM_F)]
        fab = sum(1 for x in denom if per_fact[x]["class"] == "fabrication")
        F, lo, hi = wilson(fab, len(denom))
        props = {c: dict(zip(("p", "lo", "hi"), wilson(k, n))) for c, k in cls.items()}
        return {"n_facts": n, "n_in_F_denominator": len(denom), "fabrication": fab, "F": F, "F_lo": lo, "F_hi": hi,
                "classes": dict(cls), "class_props": props}
    strata = defaultdict(list)
    for fid, v in per_fact.items(): strata[v["stratum"]].append(fid)
    per_stratum = {s: summarize(v) for s, v in sorted(strata.items())}
    pooled = summarize(list(per_fact))
    # decision rule
    verdicts = {}
    for s, r in per_stratum.items():
        if r["F_hi"] is None: verdicts[s] = "not_evaluable"
        elif r["F_lo"] is not None and r["F_lo"] > 0.10: verdicts[s] = "reextract_required"
        elif r["F_hi"] < 0.05: verdicts[s] = "repair"
        else: verdicts[s] = "repair_then_rejudge"
    if all(v == "repair" for v in verdicts.values()): overall = "repair_path (F_upper < 0.05 in every stratum)"
    elif any(v == "reextract_required" for v in verdicts.values()): overall = "repair_path for other strata; reextract_required strata flagged"
    else: overall = "repair_path for all strata; re-judge after repair decides"
    # item roll-up
    by_item = defaultdict(list)
    for fid, v in per_fact.items(): by_item[v["event_id"]].append(v)
    item_faithful = {e: all(v["entailed"] or v["class"] == "doc_level_attribute" for v in vs) for e, vs in by_item.items()}
    # per-rater accuracy vs MAP
    acc = {}
    for r in sorted({x["rater"] for x in rows}):
        rr = [x for x in rows if x["rater"] == r]
        agree = sum(1 for x in rr if (x["label"] == "entailed") == per_fact[x["fact_id"]]["entailed"])
        acc[r] = {"n": len(rr), "agreement_with_map": agree / len(rr), "type": rater_kind.get(r)}
    out = {"method": method, "n_facts": len(per_fact), "n_labels": len(rows), "raters": acc, "rater_confusion": conf,
           "doc_check": doc_check,
           "pooled": pooled, "per_stratum": per_stratum, "verdicts": verdicts, "overall": overall,
           "items": {"n": len(item_faithful), "faithful": sum(item_faithful.values()),
                     "faithful_rate": sum(item_faithful.values()) / len(item_faithful)},
           "per_fact": per_fact}
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(method, "| facts", len(per_fact), "labels", len(rows), "| doc_check", doc_check)
    print("pooled F = %.4f [%.4f, %.4f] over %d facts; classes %s" % (pooled["F"], pooled["F_lo"], pooled["F_hi"], pooled["n_in_F_denominator"], pooled["classes"]))
    print("items faithful: %d/%d = %.3f" % (out["items"]["faithful"], out["items"]["n"], out["items"]["faithful_rate"]))
    for s, v in verdicts.items(): print(f"  {s:36s} F={per_stratum[s]['F']:.3f} [{per_stratum[s]['F_lo']:.3f},{per_stratum[s]['F_hi']:.3f}] n={per_stratum[s]['n_in_F_denominator']} -> {v}")
    print("overall:", overall)
    for r, a in acc.items(): print(f"  rater {r}: n={a['n']} agreement={a['agreement_with_map']:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
