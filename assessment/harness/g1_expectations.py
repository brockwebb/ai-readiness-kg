"""Pre-registered v2 statements (design D14, task 2026-09-03_g1_eval_v2 step 3) tested
against family-level records — written BEFORE any v2 data, frozen at g1-v2-frozen.

Each test reports `supported` / `not supported` / `underpowered` with the counts behind it.
Rates are L3+ preservation shares of SCORED family records (unparseable excluded) with a
Wilson 95 % interval; "loss" = 1 − preservation. A comparison is `supported` when the
intervals of the two cells do not overlap in the expected direction, `not supported` when
they do not overlap in the opposite direction (or, for E6, when the phenomenon is absent
everywhere), and `underpowered` when a cell has n < 5 or the intervals overlap.
Stdlib only.
"""
from __future__ import annotations

from typing import Callable, Iterable, List, Optional

from .records import UNPARSEABLE, Level
from .rollup import wilson_interval

MIN_N = 5


def _cell(records: Iterable, pred: Callable) -> dict:
    sel = [r for r in records if pred(r) and r.outcome != UNPARSEABLE]
    k = sum(1 for r in sel if r.level >= Level.PRESERVED_TRANSFORMED)
    lo, hi = wilson_interval(k, len(sel))
    return {"n": len(sel), "preserved": k, "lost": len(sel) - k,
            "preservation_rate": (round(k / len(sel), 6) if sel else None),
            "loss_rate": (round(1 - k / len(sel), 6) if sel else None), "wilson95_preservation": [lo, hi]}


def _verdict_less_preserved(a: dict, b: dict) -> str:
    """Expected: a is LESS preserved (more lost) than b."""
    if a["n"] < MIN_N or b["n"] < MIN_N or a["preservation_rate"] is None or b["preservation_rate"] is None:
        return "underpowered"
    lo_a, hi_a = a["wilson95_preservation"]
    lo_b, hi_b = b["wilson95_preservation"]
    if hi_a < lo_b:
        return "supported"
    if lo_a > hi_b:
        return "not supported"
    return "underpowered"


def _verdict_differ(a: dict, b: dict) -> str:
    if a["n"] < MIN_N or b["n"] < MIN_N or a["preservation_rate"] is None or b["preservation_rate"] is None:
        return "underpowered"
    lo_a, hi_a = a["wilson95_preservation"]
    lo_b, hi_b = b["wilson95_preservation"]
    return "supported" if (hi_a < lo_b or hi_b < lo_a) else "underpowered"


def _is_opus(r, model: Optional[str]) -> bool:
    return model is None or r.model_id == model


def expectations_v2(records: List, consumer_model: str, control_model: Optional[str] = None) -> dict:
    """E4–E6, H3–H5, C1 over family records. `consumer_model` is the pinned consumer; the
    control arm's records are those under `control_model` (reported beside, never pooled)."""
    opus = [r for r in records if r.model_id == consumer_model]
    ctl = [r for r in records if control_model and r.model_id == control_model]
    ind = [r for r in opus if r.mode == "indirect"]
    by_level = {c: _cell(ind, lambda r, c=c: r.compression_level == c) for c in ("none", "short", "tight")}
    rates = [by_level[c]["loss_rate"] for c in ("none", "short", "tight")]
    ordering = all(x is not None for x in rates) and rates[0] <= rates[1] <= rates[2] and rates[0] < rates[2]
    e4_v = _verdict_less_preserved(by_level["tight"], by_level["none"])
    e4 = {"statement": "family loss rate rises monotonically none -> short -> tight (Lee 2026)",
          "by_level": by_level, "loss_rates": rates, "ordering_holds": ordering,
          "verdict": e4_v if ordering or e4_v == "underpowered" else "not supported"}

    tight = [r for r in ind if r.compression_level == "tight" and r.outcome != UNPARSEABLE and r.level < Level.PRESERVED_TRANSFORMED]
    lv = {"L0": sum(1 for r in tight if r.level == 0), "L1": sum(1 for r in tight if r.level == 1),
          "L2": sum(1 for r in tight if r.level == 2)}
    fc = {}
    for r in tight:
        fc[r.failure_class] = fc.get(r.failure_class, 0) + 1
    e5 = {"statement": "under tight, omission (L1) is the modal failure (Peters & Chin-Yee 2025; Ansari 2026)",
          "failures_at_tight": len(tight), "by_level": lv, "failure_classes": fc,
          "verdict": ("underpowered" if len(tight) < MIN_N else
                      ("supported" if lv["L1"] > lv["L0"] and lv["L1"] > lv["L2"] else "not supported"))}

    def l2_cell(comp):
        sel = [r for r in ind if r.compression_level == comp and r.outcome != UNPARSEABLE]
        k = sum(1 for r in sel if r.level == Level.DEGRADED_VERBAL)
        lo, hi = wilson_interval(k, len(sel))
        return {"n": len(sel), "L2": k, "rate": (round(k / len(sel), 6) if sel else None), "wilson95": [lo, hi]}
    l2n, l2t = l2_cell("none"), l2_cell("tight")
    if l2n["n"] < MIN_N or l2t["n"] < MIN_N:
        e6_v = "underpowered"
    elif l2t["L2"] == 0 and l2n["L2"] == 0:
        e6_v = "not supported (no L2 at any compression level: the form-shift mechanism does not appear in this consumer)"
    elif l2t["wilson95"][0] > l2n["wilson95"][1]:
        e6_v = "supported"
    elif l2t["rate"] > l2n["rate"]:
        e6_v = "underpowered"
    else:
        e6_v = "not supported"
    e6 = {"statement": "L2 rate at tight > L2 rate at none (van der Bles 2019)", "none": l2n, "tight": l2t, "verdict": e6_v}

    coded = _cell(opus, lambda r: r.surface_type == "table_coded")
    prose = _cell(opus, lambda r: r.surface_type == "prose_labeled")
    h3 = {"statement": "table_coded and prose_labeled differ in family loss rate (two-sided; no prior art)",
          "table_coded": coded, "prose_labeled": prose,
          "direction": (None if coded["loss_rate"] is None or prose["loss_rate"] is None else
                        ("table_coded lost more" if coded["loss_rate"] > prose["loss_rate"] else
                         "prose_labeled lost more" if coded["loss_rate"] < prose["loss_rate"] else "equal")),
          "verdict": _verdict_differ(coded, prose)}

    flags = _cell(opus, lambda r: r.surface_type == "flagged_cell" and r.family == "reliability")
    intervals = _cell(opus, lambda r: r.family == "interval")
    h4 = {"statement": "flagged_cell reliability markers are lost at a higher rate than numeric interval qualifiers",
          "flagged_cell_reliability": flags, "interval_all_surfaces": intervals, "verdict": _verdict_less_preserved(flags, intervals)}

    foot = _cell(opus, lambda r: r.surface_type == "footnoted")
    inline = _cell(opus, lambda r: r.surface_type in ("table_coded", "table_labeled", "flagged_cell", "prose_labeled"))
    fd = sorted({r.observations.get("covariates", {}).get("footnote_distance_chars") for r in opus
                 if r.surface_type == "footnoted" and r.observations.get("covariates", {}).get("footnote_distance_chars") is not None})
    terciles = {}
    if fd:
        cut1, cut2 = fd[len(fd) // 3], fd[(2 * len(fd)) // 3]
        for name, pred in (("low", lambda d: d < cut1), ("mid", lambda d: cut1 <= d < cut2), ("high", lambda d: d >= cut2)):
            terciles[name] = _cell(opus, lambda r, pred=pred: r.surface_type == "footnoted"
                                   and r.observations.get("covariates", {}).get("footnote_distance_chars") is not None
                                   and pred(r.observations["covariates"]["footnote_distance_chars"]))
        terciles["cuts"] = [cut1, cut2]
    h5 = {"statement": "footnoted qualifiers are lost more than inline ones; loss increases with footnote_distance_chars (Lee 2026)",
          "footnoted": foot, "inline": inline, "by_distance_tercile": terciles, "verdict": _verdict_less_preserved(foot, inline)}

    c1 = {"statement": "the control consumer's loss rate >= the pinned consumer's at every compression level",
          "by_level": {}, "verdict": "not run"}
    if ctl:
        ctl_ind = [r for r in ctl if r.mode == "indirect"]
        holds, any_sep, fails = True, False, False
        for comp in ("none", "short", "tight", "direct"):
            if comp == "direct":
                a = _cell(ctl, lambda r: r.mode == "direct")
                b = _cell(opus, lambda r: r.mode == "direct" and r.surface_type != "" )
            else:
                a = _cell(ctl_ind, lambda r, c=comp: r.compression_level == c)
                b = _cell(ind, lambda r, c=comp: r.compression_level == c)
            v = _verdict_less_preserved(a, b)
            c1["by_level"][comp] = {"control": a, "consumer": b, "verdict": v}
            if a["loss_rate"] is not None and b["loss_rate"] is not None and a["loss_rate"] < b["loss_rate"]:
                holds = False
            any_sep = any_sep or v == "supported"
            fails = fails or v == "not supported"
        c1["verdict"] = "not supported" if fails or not holds else ("supported" if any_sep else "underpowered")
        c1["note"] = "the control arm's records are compared on the HOLDOUT grid only (the arm ran nowhere else); consumer cells here are the pinned consumer's records passed in"
    return {"E4": e4, "E5": e5, "E6": e6, "H3": h3, "H4": h4, "H5": h5, "C1": c1}


__all__ = ["expectations_v2"]
