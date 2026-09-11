#!/usr/bin/env python3
"""Register the generation-9 re-judgements — only what moved. **Zero spend, no network.**

Task `cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md` decision 3. Three families in one pass,
because they share the one decision that is easy to get wrong and expensive to get wrong once
(`cc_tasks/2026-09-10_rejudge_2_3_4_RESULT.md` §1: six Results bound to a value from the wrong
population, unfixable because a name binds once, AD-028):

* **scan** — the per-cycle families `scripts/scan_report.py` computes;
* **figure inputs** — the intervals, control-fired flags and snapshot counts a figure prints,
  computed by `scripts/register_figure_results.py`, which owns them and is ASKED rather than
  re-implemented;
* **L0** — the report's own populations, from `scripts/build_l0_matrices.py`.

Each family's rows come from the script that owns them, through the same two functions the
harness-v5 pass used. Nothing here computes a statistic.

**What "unchanged" is compared against, and why it is not the previous judgement.**

A figure drawing a re-judged cycle resolves a name it cannot find through
`figures.Reads.__getitem__`, which strips ONE `_rjN` suffix: `scan_a3_pass_2026-09-09_rj2` falls
back to `scan_a3_pass_2026-09-09`, the measured cycle — never to `_rj1`. So the only comparison
that makes that fallback correct is against the name the fallback RESOLVES TO. A value equal to
the previous re-judgement's but different from the measured cycle's must still be registered, or
the figure will quietly draw the measured cycle's number — superseded twice, under the new
cycle's heading. That is the misbound six reached from the other side, and it is why this script
compares against the fallback target and not against the payload it supersedes.

**Cycle 1 registers everything, and that is DD-056 rather than an exception.** The first cycle
bound BARE names (`scan_a3_pass`, no suffix — `cycle_results.FIRST_CYCLE_EXCEPTIONS`), so the
fallback target `scan_a3_pass_2026-09-07` does not exist for them and no fallback is possible in
either direction. Cycle 4 registers everything for the opposite reason: its gate stopped before
§4, so `scan_2026-09-10` bound nothing at all. Neither is a special case in the rule; both are
the rule meeting a cycle whose history is what it is.

    /opt/anaconda3/bin/python3 scripts/register_gen9_rejudged.py --dry-run
    /opt/anaconda3/bin/python3 scripts/register_gen9_rejudged.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, "/Users/brock/GitHub/seldon")

import build_l0_matrices as B                                       # noqa: E402
import cycle_results                                                # noqa: E402
import register_figure_results as F                                 # noqa: E402
import register_l0_rejudged as L                                    # noqa: E402
import register_rejudged_cycles as S                                # noqa: E402

TASK = "cc_tasks/2026-09-11_rejudge_1_2_3_4_gen9.md"

#: (the new cycle, the payload it supersedes, the measured cycle its evidence comes from).
CYCLES = [
    ("scan_2026-09-07_rj2",  "scan_2026-09-07_rj1",  "scan_2026-09-07"),
    ("scan_2026-09-07b_rj3", "scan_2026-09-07b_rj2", "scan_2026-09-07b"),
    ("scan_2026-09-09_rj2",  "scan_2026-09-09_rj1",  "scan_2026-09-09"),
    ("scan_2026-09-10_rj2",  "scan_2026-09-10_rj1",  "scan_2026-09-10"),
]

WHY = ("Re-judged under generation 9 (`RULE-A3-v6`, `RULE-B3-v3`): an ABSENCE claim reached over "
       "a candidate set with a BLIND member is a scope limitation and owes `error`, not `fail` "
       "(ISA 705; DD-052 §6). Same Observations, nothing re-fetched, no Observation created — "
       "the evidence is the measured cycle's and the judgement is generation 9's.")

STANDS = ("Every Result it supersedes is unedited and stands as the record of the judgement "
          "that made it (AD-028).")

RECORDS = {"scan": "state/rejudgement_registration_2026-09-11.json",
           "l0": "state/l0_rejudged_registration_2026-09-11.json",
           "figure_inputs": "state/figure_inputs_registration_2026-09-11.json"}

_RJ = re.compile(r"^(.*)_rj\d+$")


def fallback_target(name: str) -> str | None:
    """The name `figures.Reads` would resolve `name` to, or `None` when it would not try.

    Deliberately a second implementation of `figures._source_name`, with a test asserting the two
    agree on every name this script emits. Importing the renderer into the registrar so one edit
    moves both is the coupling that let three families share one Result name; two implementations
    that a test holds equal is the shape that reports a divergence instead of propagating it.
    """
    m = _RJ.match(name or "")
    return m.group(1) if m else None


def classify(name: str, value, live: dict, pred_name: str | None) -> tuple:
    """`(state, note)` for one candidate, where state is `unchanged` or `moved`.

    `unchanged` means exactly this: a figure of the new cycle, asking for this name, will resolve
    it through the evidence-bound fallback to a registered Result holding THIS value. Nothing
    weaker counts, because nothing weaker makes the fallback safe.
    """
    fb = fallback_target(name)
    fb_val = live.get(fb) if fb else None
    prev = live.get(pred_name) if pred_name else None
    if fb_val is not None and float(fb_val) == float(value):
        return "unchanged", fb
    bits = []
    if pred_name:
        bits.append(f"Supersedes `{pred_name}`"
                    + (f" = {prev}" if prev is not None else ", which was never registered"))
    if fb is not None:
        bits.append(f"a figure of this cycle falls back to `{fb}` = "
                    + (f"{fb_val}, a different value" if fb_val is not None else "nothing")
                    + ", so this number is registered under its own name rather than resolved "
                      "through that one")
    return "moved", ". ".join(bits) + f". {STANDS}"


def global_name(name: str, cycle: str) -> bool:
    """True for a name that carries no cycle — the three framework snapshots F4 draws, which are
    read out of commits and are the same number whoever asks. They are neither moved nor
    unchanged BY THIS CYCLE and are reported in their own column."""
    return not name.endswith("_" + cycle_results.cycle_suffix(cycle))


def split(rows: list, cycle: str, pred: str, live: dict):
    """`(moved, unchanged, globals)` over rows of any of the three family shapes.

    Every family's row is `(name, value, …, description)` — three fields for scan and L0, five
    for the figure inputs — so the name is first, the value second and the emitter's own
    description last. The description is KEPT and this script's supersession note is appended to
    it: the emitter is the only place that knows what the number means, and a registrar that
    replaced it would leave the registry full of Results described by their provenance and not
    by their content.
    """
    moved, unchanged, globals_ = [], [], []
    for row in rows:
        name, value, described = row[0], row[1], row[-1]
        if global_name(name, cycle):
            if live.get(name) is not None and float(live[name]) == float(value):
                globals_.append(name)
                continue
            moved.append((row, f"{described} A framework snapshot, read from its commit and "
                               f"independent of any cycle. ({TASK})"))
            continue
        base = name[: -(len(cycle_results.cycle_suffix(cycle)) + 1)]
        state, note = classify(name, value, live, cycle_results.name_for(base, pred))
        if state == "unchanged":
            unchanged.append(name)
        else:
            moved.append((row, f"{described} {WHY} {note} ({TASK})"))
    return moved, unchanged, globals_


def scan_rows(cycle: str) -> list:
    """The per-cycle families, through the shipped reporter."""
    return S.candidates(cycle)


def l0_rows(cycle: str) -> list:
    """The L0 report's three populations. FIRST EMITTER WINS and the order is
    `build_l0_matrices.main`'s — host, product, tierc — which is the rule
    `scripts/register_l0_rejudged.py` states and the reason it states it."""
    out, seen = [], set()
    for _fam, (counts, prefix, population, family) in L.families(cycle).items():
        for base, value, note in B.leg_results(counts, prefix, cycle, population,
                                               with_upper95=True, family=family):
            if base in seen:
                continue
            seen.add(base)
            out.append((cycle_results.name_for(base, cycle), value, note))
    return out


#: Which cycles' L0 families are registered here, and the reason for each. The L0 families are
#: the REPORT's populations, and the report quotes one cycle at a time.
#:
#: A Result name binds once and cannot be unbound (AD-028), so "register it in case someone wants
#: it" is not a free option: it is 264 permanent names for two cycles the report has never quoted
#: and no figure reads. `scan_l0_*` exists today for cycle 3 alone — 116 under the measured name
#: and 21 under `_rj1` — which is the record of what the report has ever needed. Cycles 1 and 2
#: are declined with their reason on the comparison record rather than silently skipped: the
#: payload is the durable artifact, and any later task that needs those numbers computes them
#: from it in one command.
L0_CYCLES = {
    "scan_2026-09-09_rj2": ("the cycle the L0 report quotes today, whose `_rj1` L0 families are "
                            "in the registry and are superseded by these"),
    "scan_2026-09-10_rj2": ("the cycle the cycle-4 report revision rebuilds the report from "
                            "(decision 5); nothing was ever registered for cycle 4, whose gate "
                            "stopped before §4, so all of it is new"),
}
L0_DECLINED = {
    "scan_2026-09-07_rj2": ("no `scan_l0_*` name has ever been registered for cycle 1 and the "
                            "report has never quoted it, so there is nothing to supersede and "
                            "no consumer; a name binds once (AD-028) and these would be "
                            "permanent"),
    "scan_2026-09-07b_rj3": ("no `scan_l0_*` name has ever been registered for cycle 2 and the "
                             "report has never quoted it; same reasoning as cycle 1"),
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    try:
        from scan.figures import load_results
        live = load_results()
    except Exception as exc:                                        # noqa: BLE001
        raise SystemExit(f"FATAL: cannot read the registry, so 'did this value change' cannot "
                         f"be answered and nothing may be registered: {exc}")

    report = {k: {} for k in RECORDS}
    for cycle, pred, origin in CYCLES:
        suffix = cycle_results.cycle_suffix(cycle)
        matrices = S.write_matrices(cycle) if not a.dry_run else []
        if a.dry_run and not (REPO / "state" / f"scan_matrix_{suffix}.json").is_file():
            print(f"{cycle}: no matrix on disk yet; a dry run cannot compute its candidates")
            continue

        # ---- scan family
        moved, unchanged, _g = split(scan_rows(cycle), cycle, pred, live)
        report["scan"][cycle] = {"candidates": len(moved) + len(unchanged),
                                 "to_register": len(moved), "unchanged": len(unchanged),
                                 "unchanged_names": unchanged,
                                 "moved_names": [r[0][0] for r in moved],
                                 "matrices": matrices,
                                 "supersedes_payload": pred, "derived_from": origin}
        print(f"{cycle} scan: {len(moved)} moved, {len(unchanged)} unchanged")
        if not a.dry_run and moved:
            out = cycle_results.register(
                [(r[0], r[1], note) for r, note in moved],
                cycle=cycle, script="scan_report", data=f"scan_matrix_{suffix}",
                data_path=f"state/scan_matrix_{suffix}.json",
                data_description=(f"The {cycle} matrix: {origin}'s stored Observations "
                                  f"re-judged under generation 9. {WHY} Written by "
                                  f"scripts/scan_report.py. ({TASK})"))
            report["scan"][cycle]["registered"] = out
            print(f"  {json.dumps(out)}")

        # ---- figure inputs
        fmoved, funchanged, fglobals = split(F.rows(cycle), cycle, pred, live)
        report["figure_inputs"][cycle] = {
            "candidates": len(fmoved) + len(funchanged) + len(fglobals),
            "to_register": len(fmoved), "unchanged": len(funchanged),
            "unchanged_names": funchanged, "global_names_already_bound": fglobals,
            "moved_names": [r[0][0] for r in fmoved]}
        print(f"{cycle} figure inputs: {len(fmoved)} moved, {len(funchanged)} unchanged, "
              f"{len(fglobals)} global and already bound")
        if not a.dry_run and fmoved:
            P = F.paths(cycle)
            cycle_results.ensure_data_file(
                P["payload_name"], f"state/{cycle}.json",
                f"The {cycle} payload: {origin}'s stored Observations re-judged under "
                f"generation 9, Findings only. {WHY} ({TASK})")
            F.register([(r[0], r[1], r[2], r[3], note) for r, note in fmoved], cycle)
            report["figure_inputs"][cycle]["registered"] = len(fmoved)

        # ---- L0 families
        if cycle not in L0_CYCLES:
            report["l0"][cycle] = {"registered_here": False,
                                   "reason": L0_DECLINED[cycle],
                                   "candidates": len(l0_rows(cycle))}
            print(f"{cycle} L0: declined — {L0_DECLINED[cycle]}")
            continue
        report["l0"].setdefault(cycle, {})["why_this_cycle"] = L0_CYCLES[cycle]
        lmoved, lunchanged, _lg = split(l0_rows(cycle), cycle, pred, live)
        report["l0"][cycle].update({"registered_here": True,
                                    "candidates": len(lmoved) + len(lunchanged),
                                    "to_register": len(lmoved), "unchanged": len(lunchanged),
                                    "unchanged_names": lunchanged,
                                    "moved_names": [r[0][0] for r in lmoved]})
        print(f"{cycle} L0: {len(lmoved)} moved, {len(lunchanged)} unchanged")
        if not a.dry_run and lmoved:
            out = cycle_results.register(
                [(r[0], r[1], note) for r, note in lmoved],
                cycle=cycle, script="build_l0_matrices", data=f"scan_matrix_{suffix}",
                data_path=f"state/scan_matrix_{suffix}.json",
                data_description=(f"{origin}'s stored Observations re-judged under generation "
                                  f"9. {WHY} ({TASK})"))
            report["l0"][cycle]["registered"] = out
            print(f"  {json.dumps(out)}")

    if not a.dry_run:
        for fam, rel in RECORDS.items():
            (REPO / rel).write_text(json.dumps(report[fam], indent=1) + "\n", encoding="utf-8")
            print(f"-> {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
