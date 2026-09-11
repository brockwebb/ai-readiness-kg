#!/usr/bin/env python3
"""Register the ESIP crosswalk's coverage counts. **Zero spend, no network.**

Task `cc_tasks/2026-09-10_corpus_noaa_esip.md` §2. Every number is READ from
`state/crosswalk_esip_ai_readiness_2026-09-10.json`, never typed here — the same discipline the
suite-tier and frame registrars use, and for the same reason: a count retyped into a registrar
is a count that can disagree with the thing it counts. `docs/design/2026-09-08_l0_product_shape.md`
now quotes these numbers, so they need names.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment" / "harness"))
sys.path.insert(0, str(REPO / "scripts"))

import cycle_results                                                # noqa: E402

TASK = "cc_tasks/2026-09-10_corpus_noaa_esip.md"
SCRIPT_ARTIFACT = "register_esip_crosswalk_results"
DATA = "crosswalk_esip_ai_readiness_2026-09-10"
DATA_PATH = f"state/{DATA}.json"
EPOCH = "2026-09-10"
NOAA: dict = {}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    p = REPO / DATA_PATH
    if not p.is_file():
        raise SystemExit(f"FATAL: {p} does not exist; §2 builds before §4 registers")
    d = json.loads(p.read_text(encoding="utf-8"))
    m = d["by_measured"]
    noaa_path = REPO / "state" / "crosswalk_noaa_ai_ready_2026-09-10.json"
    if not noaa_path.is_file():
        raise SystemExit(f"FATAL: {noaa_path} does not exist; decision 3 builds before §4")
    global NOAA
    NOAA = json.loads(noaa_path.read_text(encoding="utf-8"))

    rows = [
        ("esip_checklist_items", d["items"],
         f"Assessable questions in the ESIP checklist v.1.0 ({d['source_doc_id']}): "
         f"{d['items']}. The document's apparatus — About, History, the citation block, the "
         f"appendix definitions, the references — is excluded: it says what the checklist is "
         f"and asks nothing about a dataset. Task {TASK} decision 4."),
        ("esip_items_measured_full", m["full"],
         f"ESIP checklist items a measured leg of this instrument measures EXACTLY: {m['full']} "
         f"of {d['items']}. Six of the nine are Data Access. Task {TASK} §2."),
        ("esip_items_measured_partial", m["partial"],
         f"ESIP checklist items measured by a public-surface PROXY rather than the property "
         f"itself: {m['partial']} of {d['items']}. Task {TASK} §2."),
        ("esip_items_not_measured", m["none"],
         f"ESIP checklist items NO measured leg sees: {m['none']} of {d['items']}. Not a gap in "
         f"the framework — {len(d['indicators_cited_not_measured'])} framework indicators cover "
         f"them — but the difference between reading a SURFACE and reading the DATA: "
         f"completeness, consistency, bias, resolution, gridding, labels, provenance and the "
         f"data dictionary are properties of the dataset. Data Quality is 0 full of 18 and Data "
         f"Preparation 0 of 4. Task {TASK} §2."),
        # The DENOMINATOR, added when the L0 report came to quote "3 of 5" in prose
        # (`cc_tasks/2026-09-11_l0_report_cycle4_revision.md` decision 3c). Every numeral in
        # that report is a tag or it is not written, and the component count had no name; the
        # value is read from the crosswalk like every other row here.
        ("noaa_ai_ready_components", NOAA["components"],
         f"Components of the AI-Ready Data definition in NAO 216-128 §3.01, counted from the "
         f"verbatim definition on the crosswalk: {NOAA['components']} — discoverable; "
         f"machine-readable and machine-understandable; sufficient quality; documentation; "
         f"access methods. The denominator of "
         f"`noaa_ai_ready_components_measured_full_{EPOCH}`. Grounded in an OCR reading of a "
         f"scanned image; the span, the engine and its confidence are on the record. "
         f"Task {TASK} decision 3."),
        ("noaa_ai_ready_components_measured_full", NOAA["by_measured"]["full"],
         f"Components of NAO 216-128 §3.01's AI-Ready Data definition that this instrument "
         f"measures EXACTLY: {NOAA['by_measured']['full']} of {NOAA['components']} — "
         f"discoverable, machine-readable/understandable, and access methods. Documentation is "
         f"partial (licence and vintage, not variable-level metadata) and quality is none: the "
         f"definition's word is SUFFICIENT, a judgement about the data against a use, and no "
         f"leg inspects the data. Grounded in an OCR reading of a scanned image; the span, the "
         f"engine and its confidence are on the record. Task {TASK} decision 3."),
        ("esip_indicators_cited_unmeasured", len(d["indicators_cited_not_measured"]),
         f"Framework indicators the crosswalk cites that no cycle measures: "
         f"{', '.join(d['indicators_cited_not_measured'])}. They are the instrument's declared "
         f"reach, not its blind spot — the framework names them and the scan does not run them. "
         f"Task {TASK} §2."),
    ]

    if a.dry_run:
        for b, v, n in rows:
            print(f"  {cycle_results.name_for(b, EPOCH):48s} {v}\n      {n[:150]}")
        return 0

    from seldon_artifacts import live_artifact
    if not live_artifact(SCRIPT_ARTIFACT):
        import subprocess
        r = subprocess.run(
            ["seldon", "artifact", "create", "Script", "--actor", "cc",
             "-p", f"name={SCRIPT_ARTIFACT}",
             "-p", "path=scripts/register_esip_crosswalk_results.py",
             "-p", f"description=Reads the ESIP crosswalk's coverage counts from the crosswalk "
                   f"file and registers them. Task {TASK}."],
            capture_output=True, text=True, cwd=REPO)
        if r.returncode:
            raise SystemExit(f"FATAL: cannot create Script artifact: {r.stderr[-300:]}")

    out = cycle_results.register(
        [(cycle_results.name_for(b, EPOCH), v, n) for b, v, n in rows],
        cycle=EPOCH, script=SCRIPT_ARTIFACT, data=DATA, data_path=DATA_PATH,
        data_description=(f"The ESIP AI-ready checklist v.1.0 crosswalked item by item to the "
                          f"framework's indicators, with what this instrument can measure of "
                          f"each. Task {TASK} decision 4."))
    print(json.dumps(out, indent=1))
    return 1 if out["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
