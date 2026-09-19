#!/usr/bin/env python3
"""One scan cycle: controls first (hard stop), then targets. **Zero model calls.**

Task §4 and §6. The control fixtures run BEFORE any real host is touched, and a control that
does not produce its expected verdict aborts the cycle non-zero — DD-019's decoy discipline,
and the instrument's own E5 made operational: *a cycle with zero fired controls is INVALID.*

    /opt/anaconda3/bin/python3 assessment/harness/scan/run.py --controls-only
    /opt/anaconda3/bin/python3 assessment/harness/scan/run.py --smoke
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
REPO = HARNESS.parents[1]
sys.path.insert(0, str(HARNESS))
sys.path.insert(0, str(REPO))

from scan import errors as _errors                             # noqa: E402
from scan import load_params                                   # noqa: E402
from scan.model import (Observation, SYNTHETIC_PREFIXES,       # noqa: E402
                        params_hash)
from scan.rules import (BODY_LEGS, CANDIDATE_LEGS, CURRENT,       # noqa: E402
                        FRAMEWORK_LEGS, body_groups, consumes, judge as judge_rule)
from scan.runner import collect_leg                            # noqa: E402

FRAMEWORK = REPO / "framework" / "ai_readiness_framework.json"
#: Where a cycle STAGES the bodies it captures, before anything is published.
#: `cc_tasks/2026-09-07_scan_run_2.md` §1.1. The committed store is what a Finding cites, so a
#: byte in it is a claim that some Observation on the log points at it; a run that wrote
#: straight into `corpus/evidence/scan/` made that claim of every body it happened to fetch,
#: including the ones from a diagnostic run that was never published (418 tracked bodies are
#: cited by nothing, and 260 fixture blobs had to be quarantined). Staging inverts the default:
#: bytes enter the committed store only through `publish.promote_evidence`, which copies
#: exactly the digests the published payload's Observations cite.
#:
#: Under `state/` rather than `corpus/` deliberately — `corpus/` is the acquisition lane and
#: invariant 2 protects what is in it. A staging directory is neither an acquisition nor
#: evidence; it is a scratch area that is deleted on publish, and it is gitignored.
EVIDENCE_STAGING = REPO / "state" / "evidence_staging"
#: Where payloads are written and the target DataFile is read, and the corpus manifest the
#: admission check reads. Module globals read at CALL time (the repo convention), so the spot
#: scan's loopback gate can run a whole cycle into a throwaway tree
#: (`cc_tasks/2026-09-19_spot_scan.md` decision 5).
STATE_DIR = REPO / "state"
MANIFEST = REPO / "corpus" / "manifest.json"


def staging_root(params: dict, cycle: str | None = None) -> Path:
    """Per CYCLE, so two cycles staged at once cannot promote each other's bytes. `cycle` is a
    spot cycle's own name; a frame cycle's is `params.cycle.name`."""
    return EVIDENCE_STAGING / (cycle or params["cycle"]["name"])


#: Output paths are derived from `params.cycle.name`, not typed. A cycle that wrote over a
#: previous cycle's payload would destroy the evidence the re-derivation gate compares
#: against, and DD-041's rerun convention exists precisely so a rerun never overwrites a
#: registered measurement. A spot cycle passes its own derived name (`scan.spot.spot_name`).
def out_paths(params: dict, cycle: str | None = None) -> tuple:
    name = cycle or params["cycle"]["name"]
    return (STATE_DIR / f"{name}.json",
            STATE_DIR / f"{name}_controls.json")


def refuse_spot_rerun(path: Path) -> None:
    """A spot payload is never written over, whatever its params.

    `refuse_clobber` keys on `params_hash`, and two spots of one body on one day under one
    `params.yaml` share it — so it would let the second overwrite the first, which may already
    be on the log. The spot's name is the only thing that tells them apart, so a second one
    takes DD-041's rerun letter instead (`--rerun b`).
    """
    if path.is_file():
        raise SystemExit(
            f"REFUSING: {path.name} exists. A spot cycle already measured this scope today; a "
            f"second measurement is a second cycle and takes DD-041's rerun letter "
            f"(`--rerun b` names it {path.stem}b).")


def refuse_clobber(path: Path, params: dict) -> None:
    """Refuse to write over a payload measured under DIFFERENT parameters.

    The output path is derived from `cycle.name`, and a params change that leaves the name
    alone therefore points a NEW cycle at an OLD cycle's file. That is not hypothetical: on
    2026-09-07 a `--controls-only` run under the new `finding_identity`/`link_probe` parameters
    overwrote `state/scan_2026-09-07_controls.json`, which is a registered DataFile and the
    stored evidence the re-derivation gate compares that cycle against
    (`cc_tasks/2026-09-07_scan_harness_v3.md` RESULT §5). It was recovered from git; nothing
    should have to be.

    CLAUDE.md §11: a new version gets a new NAME. So this refuses and names the fix — move
    `cycle.name` — rather than silently destroying the evidence of a measurement that can
    never be taken again.
    """
    if not path.is_file():
        return
    try:
        prior = json.loads(path.read_text(encoding="utf-8")).get("params_hash")
    except (OSError, json.JSONDecodeError):
        return
    now = params_hash(params)
    if prior and prior != now:
        # `relative_to` only where it applies. The guard used to call it unconditionally, so a
        # payload path outside the repo made the REFUSAL itself raise `ValueError` — a guard
        # whose failure path fails is a guard that reports the wrong thing at the one moment
        # it matters. Found by `tests/test_scan_run_2.py` driving it on a tmp_path.
        try:
            shown = path.relative_to(REPO)
        except ValueError:
            shown = path
        raise SystemExit(
            f"REFUSING to overwrite {shown}: it holds a cycle measured under "
            f"params_hash {prior[:12]}… and these params are {now[:12]}…. A measurement under "
            f"different parameters is a different cycle and needs its own `cycle.name` "
            f"(DD-041, CLAUDE.md §11).")


#: The task that FIRST ran a full cycle, and the default when `--task` is not given. It is a
#: default and not the answer: `cc_tasks/2026-09-07_scan_run_2_ADDENDUM-01.md` defect 1 found
#: `scan_2026-09-07b.json` carrying this string, because the cycle-2 run inherited a module
#: constant instead of naming its own task. A payload that misattributes itself is a
#: provenance claim that is simply false, and the RESULT reading it would cite the wrong
#: order. `--task` is how a run says who ordered it, the same flag
#: `scripts/framework_writeback_rules.py` grew for the same reason.
TASK = "cc_tasks/2026-09-07_scan_run.md"
OUT = REPO / "state" / "scan_smoke_2026-09-06.json"
CONTROLS_OUT = REPO / "state" / "scan_controls_2026-09-06.json"
#: Legs the control fixtures are built to exercise. E5 judges the cycle, not a surface.
#: The product legs. E5 judges the cycle, and A12 judges a HOST — running either against a
#: product surface would manufacture a verdict about the wrong subject.
#:
#: A BODY leg (`rules.BODY_LEGS`, B5 since generation 12) is not a leg of any surface either: it
#: is judged once per body after every surface is collected (`judge_bodies`), so it is not in
#: this list and no surface — control or real — is ever judged on it by `run_surface`.
CONTROL_LEGS = [l for l in FRAMEWORK_LEGS if l != "E5" and l not in BODY_LEGS]

#: What the control fixtures are scanned with. A12 is included even though it is a candidate:
#: an unexercised rule in a cycle is an unexercised rule, and DD-019's decoy discipline does
#: not care whether the framework has adopted the indicator yet.
CONTROL_FIXTURE_LEGS = CONTROL_LEGS + sorted(CANDIDATE_LEGS)


def specs() -> dict:
    g = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    return {n["properties"]["leg"]: n["properties"] for n in g["nodes"]
            if "MeasurementSpec" in n["labels"]}


def _collect(leg: str, spec: dict, target: dict, params: dict, fetcher) -> list:
    """One leg's observations, with a collector defect RECORDED rather than raised."""
    try:
        return collect_leg(spec, target, params, fetcher)
    except Exception as exc:                                  # a collector defect, recorded
        return [Observation.make(leg, leg, target["doc_id"], target["url"], "runner", "0.1.0",
                                 params, {"method": "GET", "url": target["url"]},
                                 {"status": None, "headers": {}, "body_sha256": None,
                                  "body_path": None, "bytes": 0, "elapsed_ms": 0,
                                  "error": f"{type(exc).__name__}: {exc}"},
                                 error_class="collector_unavailable")]


def run_surface(sp: dict, target: dict, params: dict, legs: list, fetcher=None) -> tuple:
    """Observe every leg of one surface, then judge each with the rule its leg is CURRENTLY on.

    Shared legs (`rules.SHARED_LEGS`) are collected ONCE and handed to every rule that declares
    it consumes them, which is how A1 and A3 stopped HEADing the same 25 links twice
    (`cc_tasks/2026-09-07_scan_harness_v3.md` §1.3). The grouping is `rules.consumes`, the same
    function `rederive.py` uses — a cycle and a re-derivation that grouped differently would
    produce different `finding_id`s from identical evidence.
    """
    obs, findings = [], []
    # A body leg is never judged here, whoever asks: its group spans surfaces
    # (`rules.scope`), and judging it over one surface's observations would be a verdict about
    # a body from a fraction of its evidence.
    wanted = [l for l in legs if sp.get(l) is not None and l not in BODY_LEGS]
    shared_legs = sorted({c for l in wanted for c in consumes(CURRENT[l])})
    shared: dict = {}
    for sl in shared_legs:
        o = _collect(sl, {"leg": sl}, target, params, fetcher)
        shared[sl] = o
        obs += o
    for leg in wanted:
        # A leg that is BOTH judged in its own right and consumed by another rule — D4, whose
        # catalog the four DCAT-US field rules read (`cc_tasks/2026-09-18_dcat_field_rules.md`)
        # — was collected once above and is not collected again. Its own group is the same
        # observations either way, so its Finding is unchanged; what changes is that the host
        # is not asked for `/data.json` twice.
        if leg in shared:
            o = shared[leg]
        else:
            o = _collect(leg, sp[leg], target, params, fetcher)
            obs += o
        group = o + [x for c in consumes(CURRENT[leg]) for x in shared.get(c, [])]
        findings.append(judge_rule(CURRENT[leg], group, params))
    return obs, findings


def judge_bodies(sp: dict, params: dict, observations: list) -> list:
    """The Findings of every BODY leg, over a cycle's collected observations.

    `cc_tasks/2026-09-18_schema_field_rules.md` decision 5: B5 compares a body's products, so it
    can be judged only after all of them are collected. The groups come from
    `rules.body_groups`, the function `rederive.py` re-derives with; a leg with no
    `MeasurementSpec` is not judged, the same condition `run_surface` applies.
    """
    out = []
    for leg in BODY_LEGS:
        if sp.get(leg) is None:
            continue
        rule_id = CURRENT[leg]
        for _body, group in body_groups(rule_id, observations, params).items():
            out.append(judge_rule(rule_id, group, params))
    return out


def expected_verdict(table, leg: str) -> str:
    """The verdict a fixture's PRE-REGISTERED table expects for one leg.

    A scalar means every leg expects it. A mapping means a `default` plus per-leg exceptions,
    which two of the four fixtures need: on `refuses_identified_client` the legs that behave
    DIFFERENTLY from the rest (A4 and A11-declared read the declared layer, which IS served;
    A12 reads the disagreement) are the whole point of the fixture, and a blanket expectation
    would hide exactly the branches it exists to exercise.

    A mapping with no `default` is a hard error rather than a shrug: a leg the table forgot
    would otherwise be a leg with no expectation, which is a control that cannot fail.
    """
    if not isinstance(table, dict):
        return table
    if "default" not in table:
        raise SystemExit(f"REFUSING: expected-verdict table {sorted(table)} has no `default`; "
                         f"a leg with no expectation is a control that cannot fail")
    return table.get(leg, table["default"])


def run_controls(params: dict, clock=None) -> tuple:
    """§4's gate. Returns (control_findings, e5_finding, control_observations, ok).

    `clock` is threaded to every `Fetcher` this cycle builds and defaults to the real one
    (`cc_tasks/2026-09-10_virtual_time.md` decision 1). A caller passing a `VirtualClock` runs
    the same fixtures, over real loopback sockets, without paying the standing rate limit in
    wall time. `main()` never passes one.
    """
    from scan.fixtures.server import MODES, FixtureServer
    from scan.manners import Fetcher
    sp = specs()
    all_findings, control_obs, fixture_obs = [], [], []
    for fixture, table in params["e5_control"]["expected_verdicts"].items():
        # A fixture that declares `products` is a BODY: each product is scanned as its own
        # surface, then the body legs are judged over all of them (`judge_bodies`, the same
        # function a cycle uses). `cc_tasks/2026-09-18_manners_status_and_b5_control.md`
        # decision 3. `CONTROL_LEGS` itself does not change: a body leg is never a leg of a
        # surface, and the fixture's declaration — not the leg list — is what admits it.
        products = tuple((MODES.get(fixture) or {}).get("products") or ())
        obs, findings = [], []
        with FixtureServer(fixture) as base:
            fetcher = Fetcher(params, clock=clock)
            for path in products or ("/index.html",):
                target = {"doc_id": f"control:{fixture}{path if products else ''}",
                          "url": f"{base}{path}"}
                o, f = run_surface(sp, target, params, CONTROL_FIXTURE_LEGS, fetcher)
                obs += o
                findings += f
        if products:
            findings += judge_bodies(sp, params, obs)
        # Retained, not discarded. The re-derivation gate can only check a Finding whose
        # evidence it still holds, and the control Findings are the ones whose determinism
        # matters most — they are what licenses the cycle.
        fixture_obs += obs
        all_findings += findings
        # Per SURFACE when the fixture has several, so a leg that misfired on the second
        # product is named with the product it misfired on.
        unexpected = [(f"{f.target_doc_id.split(fixture, 1)[-1]}:" if products else "")
                      + f"{f.leg}={f.verdict} (expected {expected_verdict(table, f.leg)})"
                      for f in findings if f.verdict != expected_verdict(table, f.leg)]
        verdicts: dict = {}
        for f in findings:
            verdicts.setdefault(f.leg, set()).add(f.verdict)
        control_obs.append(Observation.make(
            "E5", "E5", f"control:{fixture}", f"fixture://{fixture}", "control_fixture",
            "0.1.0", params, {"method": "FIXTURE", "url": f"fixture://{fixture}"},
            {"status": 200, "headers": {}, "body_sha256": None, "body_path": None,
             "bytes": 0, "elapsed_ms": 0},
            parsed={"fixture": fixture, "expected": table,
                    # One verdict per leg; a leg whose products disagreed reads as the sorted
                    # verdicts joined by `/`, so a collapse cannot hide the disagreement.
                    "verdicts": {leg: "/".join(sorted(v)) for leg, v in verdicts.items()},
                    **({"products": list(products)} if products else {}),
                    # Every error class the fixture produced, so the control gate can assert
                    # that a NEW class is actually reachable — a class nothing can produce is
                    # a class nobody can trust a zero from (§1.2, §1.4).
                    "error_classes": sorted({o.error_class for o in obs if o.error_class}),
                    "unexpected": unexpected}))
    e5 = judge_rule(CURRENT["E5"], control_obs, params)
    return all_findings, e5, control_obs + fixture_obs, e5.verdict == "pass"


#: Legs a synthetic host surface is judged by. A well-known set is not a document: no product
#: page, no download links, no methodology. Running the fifteen product legs against it would
#: manufacture fifteen `fail` verdicts per host about properties a host is not supposed to
#: have, and those would be false negatives in exactly the way DD-052 §6 warns about.
HOST_LEGS = ("A12",)


def withdrawn_on(params: dict, surface_kind: str) -> frozenset:
    """Legs `params.tier0.legs_withdrawn` withdraws from this surface kind. DD-066.

    Config-first: the withdrawal is a declaration in `params.yaml` with its construct, its
    reason and its DD beside it, and this reads it. A leg name in this function's source would
    be the hardcoded threshold CLAUDE.md §2 forbids, and — worse here — it would put the reason
    a leg stopped being measured somewhere a reader of the parameters cannot find it.

    Read at call time and never cached, like every other parameter: the whole point of the
    re-derivation gate is that a stored payload is re-judged under the params it was MADE
    under, recovered from git by hash, so a cached leg set would leak today's instrument into
    yesterday's judgement.
    """
    return frozenset(w["leg"] for w in (params.get("tier0", {}).get("legs_withdrawn") or [])
                     if surface_kind in (w.get("from_surfaces") or []))


def tier0_legs(params: dict) -> list:
    """The headline legs, declared in `params.tier0.legs` before the cycle that uses them."""
    return list((params.get("tier0") or {}).get("legs") or [])


def targets(params: dict, bodies=None) -> list:
    """The scan targets, read from the target DataFile named in `params.cycle.targets`.

    **v2 shape** (`cc_tasks/2026-09-08_scan_run_3b.md` decisions 1 and 3). Every row carries its
    own `doc_id` and the id says what kind of surface it is:

    * `host:<netloc>`    the synthetic well-known surface, UNCHANGED since cycle 1 so A12's
                         Findings stay comparable across cycles;
    * `home:<netloc>`    the host's own page;
    * `machine:<netloc>` a declared machine entry point;
    * `scan-…`           an admitted corpus Document (the operator's cycle-1 flagships).

    Distinct ids are what make "one leg asked once per host" checkable: two rows of one host
    that both judged a leg would mint two Findings with different `target_doc_id`, and the
    re-derivation gate would show it. Cycles 1 and 2 could not express that — the well-known
    row was the only host-level surface — which is why `home` and `machine` rows are new ids
    rather than a second use of `host:`.

    **Legs per row, and why they differ.** A `well_known` row is the host's robots/sitemap
    surface and carries the host legs, as before. A Tier C row is a REFERENCE host and carries
    `tier0.legs` only (DD-059): above tier 0 a catalog has no product vintage and no bulk
    download, so the comparison would stop being like-for-like. Everything else is a Tier A
    product surface and carries the full framework set.

    A row whose corpus `doc_id` was never admitted is SKIPPED with its reason: `OBSERVED_ON`
    requires a `:Document`, so a Finding on it could not be traced, and an Observation on it
    would make `observed_on_missing_document` non-zero — the integrity check that exists to
    catch exactly this. It stays on the target list and is counted as unobservable.

    **`bodies`** restricts the frame to those bodies' rows, for a SPOT cycle
    (`cc_tasks/2026-09-19_spot_scan.md` decision 1). Everything above is unchanged for the rows
    kept: each carries exactly the legs the frame gives it, so a spot measures a body the way
    the full cycle does and not a subset of the way. The restriction is applied to the target
    DataFile's rows BEFORE the admission check, so a spot of one body does not print another
    body's skipped rows; a body the frame does not hold is a refusal naming the ones it does.
    """
    src = STATE_DIR / f"{params['cycle']['targets']}.json"
    doc = json.loads(src.read_text(encoding="utf-8"))
    entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["entries"]
    tier0 = [l for l in tier0_legs(params) if l not in CANDIDATE_LEGS]
    out, skipped = [], []
    rows = doc["rows"] if bodies is None else rows_of_bodies(doc["rows"], bodies)
    for r in rows:
        doc_id, kind, tier = r.get("doc_id"), r["surface_kind"], r.get("tier", "A")
        synthetic = str(doc_id or "").startswith(SYNTHETIC_PREFIXES)
        if not synthetic and doc_id not in entries:
            skipped.append((doc_id or r["url"], r.get("not_admitted") or "not admitted"))
            continue
        if kind == "well_known":
            legs = list(HOST_LEGS)
        elif tier == "C":
            legs = tier0
        else:
            # A tier-A `home` surface is a HOST-LEVEL surface and gets the framework set minus
            # whatever `params.tier0.legs_withdrawn` withdraws from it (DD-066). Dropping the
            # leg from `tier0.legs` alone would not have done it: tier-A home and flagship both
            # fall to `CONTROL_LEGS`, which is derived from the rule REGISTRY, so a leg removed
            # only from the tier-0 list would have gone on being judged on every agency's home
            # page and gone on failing there.
            #
            # `flagship` keeps the full set on purpose. G1-D is a product-tier construct and
            # the same rule passes on product surfaces; what is withdrawn is the LEVEL, not the
            # leg.
            legs = [l for l in CONTROL_LEGS if l not in withdrawn_on(params, kind)]
        url = r["url"]
        if not synthetic:
            url = ((entries[doc_id].get("identity") or {}).get("source_url") or url)
        entry = {"doc_id": doc_id, "url": url, "surface_kind": kind, "tier": tier,
                 "agency": r["agency"], "legs": legs, "admitted": not synthetic,
                 "host": r["host"]}
        if kind == "well_known":
            # A12 compares the declared and enforced layers against the SAME path, so the
            # probe is the host's home rather than /robots.txt.
            entry["probe_url"] = next(
                (x["url"] for x in doc["rows"]
                 if x["host"] == r["host"] and x["surface_kind"] == "home"), r["url"])
        out.append(entry)
    for doc_id, why in skipped:
        print(f"  SKIPPED {str(doc_id)[:52]:54s} {why}", file=sys.stderr)
    return out


def rows_of_bodies(rows: list, bodies) -> list:
    """The target rows of `bodies`, matched on the row's `agency` without regard to case.

    Case-insensitive because a request says `bea` as often as `BEA`, and the frame's names are
    unique under case folding (checked here, not assumed). A name the frame does not hold is a
    refusal that lists the names it does: silently scanning nothing would be a spot cycle of
    zero surfaces, which the controls would license and nobody asked for.
    """
    known: dict = {}
    for r in rows:
        known.setdefault(str(r["agency"]).casefold(), set()).add(r["agency"])
    clash = sorted(sorted(v) for v in known.values() if len(v) > 1)
    if clash:
        raise SystemExit(f"REFUSING: the frame holds agencies equal under case folding: {clash}")
    bodies = list(bodies)
    unknown = sorted(str(b) for b in bodies if str(b).casefold() not in known)
    if unknown or not bodies:
        raise SystemExit(
            f"REFUSING: --target {unknown or '(none)'} names no body in the frame. Bodies: "
            f"{', '.join(sorted(next(iter(v)) for v in known.values()))}")
    wanted = {str(b).casefold() for b in bodies}
    return [r for r in rows if str(r["agency"]).casefold() in wanted]


def canonical_bodies(params: dict, bodies) -> list:
    """The frame's own spelling of each requested body, sorted: what the payload records and
    the spot's name is derived from, so `--target bea` and `--target BEA` are one cycle."""
    doc = json.loads((STATE_DIR / f"{params['cycle']['targets']}.json").read_text(
        encoding="utf-8"))
    return sorted({r["agency"] for r in rows_of_bodies(doc["rows"], bodies)})


def surfaces() -> list:
    """Back-compatible alias for the scaffold's name."""
    from scan import load_params
    return targets(load_params())


def merge_controls(payload_path: Path, params: dict, clock=None) -> int:
    """Re-run the controls and fold them into an existing payload. **No network, no re-scan.**

    The control fixtures are local and free; the seventeen surfaces are neither. When a change
    affects only what a cycle RECORDS about its controls — not what it measured, and not
    `params_hash` — re-scanning the real hosts would fetch every federal page a third time in
    an afternoon and, worse, would move the `obs_id` of every page that changed in between,
    orphaning findings that are already on the log. This is the same principle as the
    re-derivation gate, applied to the control half of a cycle.

    Refuses across a `params_hash` mismatch: merging control records derived under one
    parameter set into a cycle measured under another would produce a payload whose parts
    disagree about the constants that shaped them.

    `clock` is threaded to the control cycle it runs and defaults to the real one
    (`cc_tasks/2026-09-10_harness_small.md` decision 1). Without it this was the single most
    expensive thing in the suite: its test calls it twice, so it ran two complete seven-fixture
    cycles at the standing rate — 594 s, a third of the whole suite, and the one place the
    virtual clock could not reach (`cc_tasks/2026-09-10_virtual_time_RESULT.md` §4).
    """
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    ph = params_hash(params)
    if payload.get("params_hash") != ph:
        print(f"REFUSING: payload params_hash {payload.get('params_hash')!r} != current "
              f"{ph!r}; re-run the whole cycle", file=sys.stderr)
        return 2
    cf, e5, control_obs, ok = run_controls(params, clock=clock)
    print(f"CONTROL GATE: {e5.verdict.upper()} — {e5.reason}")
    if not ok:
        print("cycle INVALID", file=sys.stderr)
        return 2
    # REPLACE, never union. A control run is a whole cycle's worth of canaries, and the
    # fixture server binds an ephemeral port that leaks into every control `target_url` and
    # therefore into every derived control id — so a second control run produces 30 records
    # that are *new* rather than equal. Unioning them made one payload claim two control
    # cycles. The superseded records stay on the append-only log, where an earlier control run
    # belongs; the payload describes the controls this cycle currently stands on.
    payload["control_findings_detail"] = [f.to_dict() for f in cf] + [e5.to_dict()]
    payload["control_findings"] = len(cf) + 1
    payload["observations_detail"] = [
        o for o in payload.get("observations_detail", [])
        if not str(o.get("target_doc_id", "")).startswith("control:")
    ] + [o.to_dict() for o in control_obs]
    payload["control_verdict"], payload["control_reason"] = e5.verdict, e5.reason
    payload_path.write_text(json.dumps(payload, indent=1, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"control_findings": payload["control_findings"],
                      "observations_detail": len(payload["observations_detail"]),
                      "surfaces_rescanned": 0}, indent=1))
    return 0


def run_cycle(params: dict, tgts: list, controls: tuple, fetcher, *, task: str,
              evidence_root: str, cycle: str | None = None, spot_targets=None) -> dict:
    """Measure `tgts` after a control gate that PASSED, and return the cycle's payload.

    Factored out of `main` (`cc_tasks/2026-09-19_spot_scan.md` decision 5) so the spot path can
    be run end to end over the loopback fixtures with a `VirtualClock` fetcher, which `main`
    never builds. Nothing here writes a file; `main` does, through `write_payload`.

    `controls` is `run_controls`' first three values, and the caller has already refused a
    failing gate. `spot_targets` makes this a SPOT cycle: the payload carries `scope: spot`, the
    bodies, and the frame cycle `params` named, and `cycle` is the spot's own name.
    """
    cf, e5, control_obs = controls
    sp = specs()
    rows, all_obs, all_find = [], [], []
    for t in tgts:
        # A12 compares the declared and enforced layers against the same path, so a host
        # surface is collected against its agency's flagship URL rather than /robots.txt.
        tgt = dict(t, url=t.get("probe_url", t["url"]))
        obs, findings = run_surface(sp, tgt, params, t["legs"], fetcher)
        all_obs += obs
        all_find += findings
        rows.append({"doc_id": t["doc_id"], "url": tgt["url"],
                     "surface_kind": t["surface_kind"], "agency": t["agency"],
                     "admitted": t["admitted"],
                     "verdicts": {f.leg: f.verdict for f in findings}})
        marks = (" ".join(f"{f.leg}={f.verdict[0].upper()}" for f in findings)
                 if t["surface_kind"] == "well_known"
                 else " ".join(f.verdict[0].upper() for f in findings))
        print(f"  {t['agency']:8s} {t['surface_kind']:10s} {t['doc_id'][:40]:42s} {marks}",
              flush=True)

    # Body legs, judged once every surface is in (`judge_bodies`). Each Finding's target is the
    # body's well-known row, so its verdict is recorded on that row of the matrix; a Finding
    # whose body has no row is listed rather than dropped.
    body_findings = judge_bodies(sp, params, all_obs)
    all_find += body_findings
    by_doc = {r["doc_id"]: r for r in rows}
    body_without_row = []
    for f in body_findings:
        if f.target_doc_id in by_doc:
            by_doc[f.target_doc_id]["verdicts"][f.leg] = f.verdict
        else:
            body_without_row.append(f.target_doc_id)

    # E5-v2's first clause — "both control fixtures are scanned before any real host" — is
    # only falsifiable against a timestamp. The gate above already ran and already stopped the
    # cycle if a control misfired; this re-judges E5 with the ordering evidence now that there
    # IS a first real host, so the cycle's recorded E5 Finding carries the whole signal rather
    # than the half a pure rule could see beforehand.
    earliest = min((o.captured_at for o in all_obs), default=None)
    if earliest:
        for o in control_obs:
            if o.leg == "E5":
                o.parsed = dict(o.parsed or {}, earliest_surface_captured_at=earliest)
        e5 = judge_rule(CURRENT["E5"], [o for o in control_obs if o.leg == "E5"], params)
        if e5.verdict != "pass":
            print(f"CYCLE INVALID after the fact: {e5.reason}", file=sys.stderr)

    by_leg_err = {leg: sum(1 for r in rows if r["verdicts"].get(leg) == "error")
                  for leg in CONTROL_LEGS}
    summary = {
        "task": task, "cycle": cycle or params["cycle"]["name"],
        # `scope` says what the cycle measured: the frame, or the bodies a spot names. The name
        # says it too (`scan.spot`), and `publish.py` refuses a payload whose two disagree.
        "scope": "spot" if spot_targets else "frame",
        **({"spot_targets": list(spot_targets),
            # The frame cycle `params.yaml` names on the day the spot ran. Recorded, not
            # implied: the spot measured under that cycle's parameters and is not that cycle.
            "params_cycle": params["cycle"]["name"]} if spot_targets else {}),
        "targets": params["cycle"]["targets"],
        "harness_version": _errors.harness_of(params), "params_version": params["params_version"], "params_hash": params_hash(params),
        "control_verdict": e5.verdict, "control_reason": e5.reason,
        #: Where this cycle's bodies are staged. See the controls-only payload above.
        "evidence_root": evidence_root,
        # +1 for E5's own Finding. The cycle's validity verdict is the single most important
        # record the cycle produces and it was NOT on the event log: `rules_built` said 16 and
        # the projected graph held 15 `:Rule` nodes, because RULE-E5-v1 never emitted one.
        # DD-019 says a cycle with zero fired controls is INVALID; the evidence that THIS
        # cycle was valid has to be as durable as the findings it validates.
        "control_findings": len(cf) + 1,
        "surfaces": len(rows), "legs": len(CONTROL_LEGS),
        "findings": len(all_find), "observations": len(all_obs),
        "verdict_counts": {v: sum(1 for f in all_find if f.verdict == v)
                           for v in ("pass", "fail", "not_applicable", "error")},
        # Every class the cycle produced, and `unknown` broken out on its own line
        # (`cc_tasks/2026-09-07_scan_harness_v3.md` §1.2). `unknown` is the ONLY remainder the
        # classifier has, so a cycle that produced any is a cycle whose map is missing a rule —
        # a number that has to be looked at, not a bucket things quietly land in. Every class
        # is listed, zeros included, so a class that stopped appearing is visible too.
        "error_class_counts": {c: sum(1 for o in all_obs if o.error_class == c)
                               for c in _errors.ERROR_CLASSES},
        "error_class_unknown": sum(1 for o in all_obs if o.error_class == "unknown"),
        # What this scanner actually ASKED of each host, counted at the socket
        # (`manners.Fetcher.requests`) rather than inferred from Observations — a link probe
        # issues one HEAD per link inside a single Observation, so the two numbers are not the
        # same and only this one is the manners claim. Controls are excluded: the fixture
        # server is us, and folding 127.0.0.1 in would put our own loopback in a table about
        # federal hosts.
        "requests_per_host": {h: n for h, n in sorted(fetcher.requests.items())},
        "requests_total": sum(fetcher.requests.values()),
        # One line per netloc: its robots.txt status, what RFC 9309 §2.3.1 makes of it, and
        # the decision the fetcher took (`manners.robots_access`). The manners gate replays
        # these from the payload (`cc_tasks/2026-09-18_manners_status_and_b5_control.md`
        # decision 1); an `unreachable` netloc is one every other fetch to was refused.
        "robots_log": fetcher.robots_log,
        "legs_erroring_on_every_surface": [l for l, n in by_leg_err.items()
                                           if rows and n == len(rows)],
        "body_legs": list(BODY_LEGS),
        "body_findings_without_a_row": body_without_row,
        # The legs each surface carried (`targets`), so the re-derivation gate judges each
        # surface on its own legs and nowhere else (`rederive.rederive`). Without it a rule
        # reading a shared leg — `RULE-D2-v1` reads A4 — is re-derived on every surface that
        # holds that leg's evidence, the Tier C reference hosts included, and the gate reports
        # Findings this cycle never recorded (`cc_tasks/2026-09-18_rejudge_seven_legs.md`).
        "surface_legs": {t["doc_id"]: list(t["legs"]) for t in tgts},
        "matrix": rows,
        "control_findings_detail": [f.to_dict() for f in cf] + [e5.to_dict()],
        "findings_detail": [f.to_dict() for f in all_find],
        "observations_detail": [o.to_dict() for o in all_obs] + [o.to_dict() for o in control_obs],
    }
    return summary


def write_payload(path: Path, payload: dict, params: dict) -> None:
    """The one place a cycle payload is written: the clobber guards, then the file.

    A spot payload passes `scan.spot.check_identity` before it is written, so a spot named
    `scan_…` (or the reverse) never reaches `state/` to be refused later by `publish.py`.
    """
    from scan import spot as _spot
    _spot.check_identity(path.stem, payload)
    if _spot.is_spot(path.stem, payload):
        refuse_spot_rerun(path)
    refuse_clobber(path, params)
    path.write_text(json.dumps(payload, indent=1, default=str) + "\n", encoding="utf-8")


def main(argv=None) -> int:
    # THE CYCLE LICENCE (`cc_tasks/2026-09-09_manners_closeout.md` decision 3). Only this
    # entry point may add to the committed evidence store, and it says so by setting the
    # token `model.store_evidence` looks for. Set here rather than at import, so importing
    # this module to reach `run_surface` or `targets` from a driver does NOT license writes:
    # every fixture driver that filled `corpus/evidence/scan/` with loopback bodies did it by
    # importing collectors, and an import-time token would have licensed exactly those.
    import os
    from scan.model import CYCLE_TOKEN_ENV
    os.environ[CYCLE_TOKEN_ENV] = "1"
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--controls-only", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--merge-controls", metavar="PAYLOAD", default=None,
                    help="re-run the control gate ALONE and merge its records into an "
                         "existing cycle payload, without re-measuring a single surface")
    ap.add_argument("--task", default=TASK, metavar="PATH",
                    help="the cc_task that ordered this run. Recorded on the payload so it "
                         "names the order it fulfils rather than the task that wrote the "
                         "runner.")
    ap.add_argument("--evidence-root", default=None, metavar="DIR",
                    help="where captured bodies are STAGED (default "
                         "state/evidence_staging/<cycle.name>/). They enter the committed "
                         "store only through publish.py, and only if this cycle's published "
                         "Observations cite them.")
    ap.add_argument("--target", action="append", default=None, metavar="BODY",
                    help="a SPOT cycle: restrict the frame to this body's surfaces (repeatable; "
                         "matched on the target list's `agency`, case-insensitive). Every leg "
                         "the frame gives those surfaces runs, controls first. The payload is "
                         "state/spot_<body>_<YYYY-MM-DD>.json (spot_multi_… for several) and is "
                         "never the report's snapshot. cc_tasks/2026-09-19_spot_scan.md")
    ap.add_argument("--rerun", default="", metavar="LETTER",
                    help="DD-041's rerun letter for a second spot of the same scope on the "
                         "same UTC day (b, c, …)")
    a = ap.parse_args(argv)
    params = load_params()
    # A spot is decided and VALIDATED before anything runs: an unknown body is a refusal that
    # costs nothing, and discovering it after the control cycle would have cost the controls.
    cycle, spot_targets = None, None
    if a.target:
        if a.controls_only or a.merge_controls:
            raise SystemExit("REFUSING: --target is a spot cycle over surfaces; --controls-only "
                             "and --merge-controls measure no surface")
        from scan import spot as _spot
        spot_targets = canonical_bodies(params, a.target)
        cycle = _spot.spot_name(spot_targets, rerun=a.rerun)
        refuse_spot_rerun(out_paths(params, cycle)[0])
        print(f"SPOT cycle {cycle}: {', '.join(spot_targets)}", file=sys.stderr)
    elif a.rerun:
        raise SystemExit("REFUSING: --rerun names a second SPOT of one day; a frame cycle's "
                         "name is `params.cycle.name`")
    tgts = None if (a.controls_only or a.merge_controls) else targets(params, spot_targets)
    # Redirect the module-path global rather than threading a root through seven collectors:
    # `store_evidence` reads `EVIDENCE_ROOT` at CALL time, which is the repo convention
    # (CLAUDE.md "Conventions specific to this repo") and the same seam `tests/conftest.py`
    # uses. Set before ANY collection, controls included — a fixture body is exactly the kind
    # of byte that has been landing in the committed store uninvited.
    from scan import model as _model
    _model.EVIDENCE_ROOT = (Path(a.evidence_root) if a.evidence_root
                            else staging_root(params, cycle))
    _model.EVIDENCE_ROOT.mkdir(parents=True, exist_ok=True)
    print(f"evidence staged in {_model.EVIDENCE_ROOT}", file=sys.stderr)
    # Recorded repo-RELATIVE where it can be, so a payload moved between checkouts still
    # names a directory that exists. An explicit `--evidence-root` outside the repo is kept
    # absolute, because that is what it is.
    try:
        _staging_rel = str(_model.EVIDENCE_ROOT.relative_to(REPO))
    except ValueError:
        _staging_rel = str(_model.EVIDENCE_ROOT)

    if a.merge_controls:
        return merge_controls(Path(a.merge_controls), params)

    cf, e5, control_obs, ok = run_controls(params)
    print(f"CONTROL GATE: {e5.verdict.upper()} — {e5.reason}")
    if not ok:
        print("cycle INVALID; no real host was touched", file=sys.stderr)
        return 2
    if a.controls_only:
        # A control-only cycle is still a cycle and still has to be re-derivable. Writing the
        # payload is what lets `rederive.py` run its gate over the controls after a rule
        # change without re-scanning seventeen federal hosts — which is the whole point of a
        # rule being pure, and was not usable before because the payload was only written on
        # a full run.
        _, controls_out = out_paths(params)
        payload = {
            "task": a.task,
            "cycle": params["cycle"]["name"], "cycle_kind": "controls_only",
            "harness_version": _errors.harness_of(params), "params_version": params["params_version"], "params_hash": params_hash(params),
            "control_verdict": e5.verdict, "control_reason": e5.reason,
            "control_findings": len(cf) + 1,
            # Where this cycle's bodies are staged, so `publish.promote_evidence` finds them
            # without being told twice. Recorded rather than re-derived: a run with an
            # explicit `--evidence-root` staged somewhere the cycle name does not name.
            "evidence_root": _staging_rel,
            "rules": sorted({f.rule_id for f in cf} | {e5.rule_id}),
            "findings_detail": [],
            "control_findings_detail": [f.to_dict() for f in cf] + [e5.to_dict()],
            "observations_detail": [o.to_dict() for o in control_obs],
        }
        refuse_clobber(controls_out, params)
        controls_out.write_text(json.dumps(payload, indent=1, default=str) + "\n",
                                encoding="utf-8")
        print(json.dumps({k: v for k, v in payload.items()
                          if k not in ("findings_detail", "control_findings_detail",
                                       "observations_detail")}, indent=1))
        print(f"-> {controls_out.relative_to(REPO)}", file=sys.stderr)
        return 0

    if a.limit:
        tgts = tgts[:a.limit]
    from scan.manners import Fetcher
    summary = run_cycle(params, tgts, (cf, e5, control_obs), Fetcher(params), task=a.task,
                        evidence_root=_staging_rel, cycle=cycle, spot_targets=spot_targets)
    cycle_out, _ = out_paths(params, cycle)
    write_payload(cycle_out, summary, params)
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ("matrix", "findings_detail", "observations_detail",
                                   "control_findings_detail")}, indent=1))
    print(f"-> {cycle_out.relative_to(REPO)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
