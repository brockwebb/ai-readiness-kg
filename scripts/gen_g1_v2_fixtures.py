#!/usr/bin/env python3
"""Generate the G1 v2 product-surface fixtures by VERBATIM anchor slicing of the surfaces
admitted under epoch g1sfc-2026-09-03 (task 2026-09-03_g1_eval_v2_product_surfaces_compression
step 2).

Every passage is the newline-join of `parts`, each part a contiguous block of one captured
file (a table passage = the header row + a contiguous block of rows; a flagged_cell CSV
passage adds the symbol legend block from the table's cube-metadata file; a footnoted
passage = the body span + the appendix-table block, with `footnote_distance_chars` the
distance between them in the captured text). `tests/test_g1_fixtures.py` re-checks every
part against its corpus file and asserts zero passage overlap between the two splits.

Nothing here is typed by hand except the anchors, the estimate/qualifier readings of the
rows (each recorded beside the verbatim row it was read from) and the producer rules.

    /opt/anaconda3/bin/python3 scripts/gen_g1_v2_fixtures.py [--no-network]

Writes assessment/tests/fixtures/g1/v2/propositions.yaml and propositions_holdout.yaml.
`--no-network` skips the Census variables endpoint (the code_map is then read from the
previously generated file, if any).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment"))
from harness.g1_fixtures import is_grounded, load_fixture_set, normalize  # noqa: E402

CORPUS = REPO / "corpus" / "g1eval"
OUT = REPO / "assessment" / "tests" / "fixtures" / "g1" / "v2"
FIXTURE_VERSION = "v2-2026-09-03"
VARIABLES_ENDPOINT = "https://api.census.gov/data/2023/acs/acs5/variables/{code}.json"

_TEXT_CACHE: dict = {}


def source_text(doc_id: str) -> str:
    if doc_id in _TEXT_CACHE:
        return _TEXT_CACHE[doc_id]
    pdf, md = CORPUS / f"{doc_id}.pdf", CORPUS / f"{doc_id}.md"
    if pdf.exists():
        import pypdf
        t = "\n".join((pg.extract_text() or "") for pg in pypdf.PdfReader(str(pdf)).pages)
    elif md.exists():
        t = md.read_text(encoding="utf-8")
    else:
        raise SystemExit(f"FATAL: corpus file for {doc_id} not present under {CORPUS}")
    _TEXT_CACHE[doc_id] = t
    return t


def block(doc_id: str, first_contains: str, last_contains: str, *, after=None) -> str:
    """Verbatim block from the start of the first line containing `first_contains` (searched
    after the line containing `after`, when given) to the end of the first later line
    containing `last_contains`."""
    lines = source_text(doc_id).split("\n")
    start = 0
    for anchor in ([after] if isinstance(after, str) else (after or [])):
        # successive anchors: each searched after the previous one (a table title, then a
        # sub-heading inside that table)
        start = next(i for i in range(start, len(lines)) if anchor in lines[i]) + 1
    i = next(k for k in range(start, len(lines)) if first_contains in lines[k])
    j = next(k for k in range(i, len(lines)) if last_contains in lines[k])
    return "\n".join(lines[i:j + 1])


def line(doc_id: str, contains: str, *, after=None) -> str:
    return block(doc_id, contains, contains, after=after)


def span(doc_id: str, first_contains: str, last_contains: str) -> str:
    """Verbatim substring from `first_contains` to the end of `last_contains`."""
    t = source_text(doc_id)
    i = t.index(first_contains)
    j = t.index(last_contains, i) + len(last_contains)
    return t[i:j]


def distance(doc_id: str, a: str, b: str) -> int:
    t = source_text(doc_id)
    return abs(t.index(b) - t.index(a))


def surface_file(doc_id: str) -> str:
    for ext in (".pdf", ".md"):
        if (CORPUS / f"{doc_id}{ext}").exists():
            return f"corpus/g1eval/{doc_id}{ext}"
    raise SystemExit(f"FATAL: no corpus file for {doc_id}")


# ------------------------------------------------------------------ producer rules (cited)
ACS_RULE = ("census-acs-general-handbook-2020 ch. 7: ACS margins of error are published at the 90 percent "
            "confidence level (B19013_001M is the MOE attribute of B19013_001E per the variables endpoint)")
LFS_RULE = ("statcan-71-543-g-guide-labour-force-survey-2025: the standard error of estimate is published beside each "
            "seasonally adjusted estimate; one standard error = 68 %, two = 95 % confidence")
CCHS_RULE = ("statcan-13-10-0096-01-cube-metadata-csv symbol legend: E = use with caution, F = too unreliable to be "
             "published; Low/High 95% confidence interval rows accompany each percent")
CCHS113_RULE = ("statcan-13-10-0113-01-cube-metadata-csv symbol legend: E = use with caution, F = too unreliable to be "
                "published; Low/High 95% confidence interval rows accompany each percent")
NCHS_TABLE_RULE = ("NCHS Data Brief appendix tables print Percent (95% confidence interval) and Standard error beside "
                   "each estimate; nchs-2017-data-presentation-standards-proportions governs which are shown")
NCHS530_RULE = ("nchs-data-brief-530-perinatal-mortality-2022-2023 Data table for Figure 4: the percent change from 2022 "
                "to 2023 is replaced by † where the change is not significant, legend '† Change not significant (p = 0.05).'")
BLS_RULE = ("bls-employment-situation news release, Technical Note 'Reliability of the estimates': the 90-percent "
            "confidence interval for the monthly change in total nonfarm employment is on the order of plus or minus 122,000")


def code_map(no_network: bool, previous: dict | None) -> dict:
    if no_network:
        if not previous:
            raise SystemExit("FATAL: --no-network but no previously generated code_map to reuse")
        return previous
    out = {"endpoint": VARIABLES_ENDPOINT, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "variables": {}}
    for code in ("B19013_001E", "B19013_001M"):
        with urllib.request.urlopen(VARIABLES_ENDPOINT.format(code=code), timeout=60) as r:
            out["variables"][code] = json.loads(r.read().decode("utf-8"))
    return out


# ------------------------------------------------------------------ passages and propositions
def acs_props(doc_id: str, pid_prefix: str, header: str, rows: list[tuple[str, str, int, int]], passage_id: str, cmap: dict):
    """rows: (county name, verbatim row line, estimate, moe). Estimate label is the CODE form so the
    direct prompt never decodes the surface."""
    props = []
    for county, row, est, moe in rows:
        props.append({
            "id": f"{pid_prefix}-{county.split(' ')[0].lower().replace(',', '')}",
            "source_doc_id": doc_id, "passage": passage_id, "surface_type": "table_coded",
            "surface_file": surface_file(doc_id),
            "grounding_span": row,
            "estimate": {"value": est, "text": str(est), "unit": "currency",
                         "label": f'B19013_001E for "{county}"',
                         "meaning": "median household income in the past 12 months (2023 inflation-adjusted dollars) — fixture metadata from the variables endpoint, never shown to the consumer"},
            "qualifiers": [{"class": "MOE", "value": moe, "text": str(moe), "unit": "currency", "level": 0.90,
                            "field": "B19013_001M"}],
            "binding": {"row": row, "row_key": county},
            "code_map": cmap,
            "producer_rule": ACS_RULE,
            "notes": "table_coded: no vintage on the surface (the year is in the request URL, not the JSON), so no VINTAGE qualifier."})
    return props


def lfs_props(doc_id: str, pid_prefix: str, geo: str, ref: str, rows: list[tuple[str, str, float, float, str]], passage_id: str):
    """rows: (characteristic, unit, estimate, se, decimals-text) read from the Estimate and Standard error rows."""
    props = []
    for char, unit, est, se, txt in rows:
        est_line = [ln for ln in source_text(doc_id).split("\n") if f'"{geo}"' in ln and f'"{char}","Total - Gender"' in ln and '"Estimate"' in ln][0]
        se_line = [ln for ln in source_text(doc_id).split("\n") if f'"{geo}"' in ln and f'"{char}","Total - Gender"' in ln and '"Standard error of estimate"' in ln][0]
        scale = 1000 if unit == "count" else 1
        props.append({
            "id": f"{pid_prefix}-{char.lower().replace(' ', '-')}",
            "source_doc_id": doc_id, "passage": passage_id, "surface_type": "table_labeled",
            "surface_file": surface_file(doc_id),
            "grounding_span": est_line,
            "estimate": {"value": est, "text": txt, "unit": unit, "scale": scale,
                         "label": f"{char.lower()} in {geo}, {ref} (seasonally adjusted)"},
            "qualifiers": [
                {"class": "SE", "value": se, "text": str(se), "unit": unit, "scale": scale, "level": 0.95, "z": 2.0,
                 "row": se_line},
                {"class": "VINTAGE", "as_of": ref, "text": ref},
            ],
            "binding": {"row": est_line, "row_key": f"{geo} / {char}"},
            "producer_rule": LFS_RULE,
            "notes": "long-format labeled table: the 'Statistics' column names the row 'Estimate' or 'Standard error of estimate'; UOM 'Persons in thousands' -> scale 1000 for counts."})
    return props


def cchs_prop(doc_id: str, pid: str, geo: str, ref: str, indicator: str, passage_id: str, *, flagged: bool, label: str,
              legend_on_surface: bool, rule: str, table_note: str):
    lines = source_text(doc_id).split("\n")
    pct = [ln for ln in lines if f'"{geo}"' in ln and f'"{indicator}","Percent"' in ln][0]
    lo = [ln for ln in lines if f'"{geo}"' in ln and f'"{indicator}","Low 95% confidence interval, percent"' in ln][0]
    hi = [ln for ln in lines if f'"{geo}"' in ln and f'"{indicator}","High 95% confidence interval, percent"' in ln][0]

    def value(ln):
        cells = ln.split('","')
        return cells[13].strip('"'), cells[14].strip('"')
    v, status = value(pct)
    lo_v, _ = value(lo)
    hi_v, _ = value(hi)
    quals = [{"class": "CI", "form": "bounds", "level": 0.95, "lower": float(lo_v), "upper": float(hi_v),
              "lower_text": lo_v, "upper_text": hi_v, "unit": "percent", "rows": [lo, hi]}]
    if flagged:
        assert status == "E", (geo, indicator, status)
        quals.append({"class": "RELIABILITY_FLAG", "text": "E", "symbol": "E", "legend": "use with caution",
                      "polarity": "unreliable", "status_column": "STATUS"})
    quals.append({"class": "VINTAGE", "as_of": ref, "text": ref})
    return {
        "id": pid, "source_doc_id": doc_id, "passage": passage_id, "surface_type": "flagged_cell",
        "surface_file": surface_file(doc_id), "grounding_span": pct,
        "estimate": {"value": float(v), "text": v, "unit": "percent", "label": f"{label} in {geo}, {ref} (percent)"},
        "qualifiers": quals, "binding": {"row": pct, "row_key": f"{geo} / {indicator}"},
        "legend_on_surface": legend_on_surface, "producer_rule": rule,
        "notes": table_note + (" This row carries STATUS 'E'." if flagged else " This row carries no flag (unflagged control row in a flagged passage).")}


def nchs_footnoted_prop(doc_id: str, pid: str, label: str, body_span: str, row_contains: str, est: float, est_txt: str,
                        lo: str, hi: str, se: str, passage_id: str, vintage: str, *, row_after=None):
    row = line(doc_id, row_contains, after=row_after)
    return {
        "id": pid, "source_doc_id": doc_id, "passage": passage_id, "surface_type": "footnoted",
        "surface_file": surface_file(doc_id), "grounding_span": body_span,
        "estimate": {"value": est, "text": est_txt, "unit": "percent", "label": label},
        "qualifiers": [
            {"class": "CI", "form": "bounds", "level": 0.95, "lower": float(lo), "upper": float(hi),
             "lower_text": lo, "upper_text": hi, "unit": "percent", "row": row},
            {"class": "SE", "value": float(se), "text": se, "unit": "percent_points", "level": 0.95, "row": row},
            {"class": "VINTAGE", "as_of": vintage, "text": vintage},
        ],
        "footnote_distance_chars": distance(doc_id, body_span, row),
        "binding": {"row": row, "sentence": body_span},
        "producer_rule": NCHS_TABLE_RULE,
        "notes": "footnoted: the estimate is stated in the body text with no uncertainty; its CI and SE appear only in the appendix data table."}


def nchs530_prop(doc_id: str, pid: str, state: str, rate_2023: float, rate_2022: float, passage_id: str):
    row = line(doc_id, f"{state} ", after="Data table for Figure 4") if state != "Delaware" else line(doc_id, "Delaware .", after="Data table for Figure 4")
    assert row.rstrip().endswith("†"), row
    return {
        "id": pid, "source_doc_id": doc_id, "passage": passage_id, "surface_type": "flagged_cell",
        "surface_file": surface_file(doc_id), "grounding_span": row,
        "estimate": {"value": rate_2023, "text": str(rate_2023), "unit": "rate", "label": f"the 2023 perinatal mortality rate for {state} (per 1,000)"},
        "qualifiers": [
            {"class": "RELIABILITY_FLAG", "text": "†", "symbol": "†", "legend": "Change not significant (p = 0.05).",
             "polarity": "unreliable", "applies_to": f"the change from the 2022 rate ({rate_2022}) to the 2023 rate",
             "comparison_value": rate_2022},
            {"class": "VINTAGE", "as_of": "2023", "text": "2023"},
        ],
        "binding": {"row": row, "row_key": state},
        "legend_on_surface": True, "producer_rule": NCHS530_RULE,
        "notes": "flagged_cell: the change column holds † in place of a percent; the legend is printed beneath the table. A restatement that asserts an increase or decrease without the not-significant caveat asserts what the producer withheld."}


def bls_prop(doc_id: str, pid: str, month: str, change: int, change_txt: str, body_line_contains: str, passage_id: str):
    body = line(doc_id, body_line_contains)
    tech = line(doc_id, "employment from the establishment survey is on the order of plus or minus 122,000")
    return {
        "id": pid, "source_doc_id": doc_id, "passage": passage_id, "surface_type": "footnoted",
        "surface_file": surface_file(doc_id), "grounding_span": body,
        "estimate": {"value": change, "text": change_txt, "unit": "count", "label": f"the over-the-month change in total nonfarm payroll employment in {month}"},
        "qualifiers": [
            {"class": "CI", "form": "pm", "level": 0.90, "value": 122000, "text": "122,000", "unit": "count", "row": tech},
            {"class": "VINTAGE", "as_of": month, "text": month.upper()},
        ],
        "footnote_distance_chars": distance(doc_id, body, tech),
        "binding": {"sentence": body},
        "producer_rule": BLS_RULE,
        "notes": "footnoted: the headline change is in the first paragraph; the confidence interval for it is stated only in the Technical Note near the end of the release."}


def build(no_network: bool) -> tuple[dict, dict]:
    prev = None
    prev_path = OUT / "propositions.yaml"
    if prev_path.exists():
        try:
            d = yaml.safe_load(prev_path.read_text(encoding="utf-8"))
            prev = next((p.get("code_map") for p in d["propositions"] if p.get("code_map")), None)
        except Exception:  # noqa: BLE001 — a previous file that does not parse is simply not reused
            prev = None
    cmap = code_map(no_network, prev)

    dev_passages, dev_meta, dev_props = {}, {}, []
    hold_passages, hold_meta, hold_props = {}, {}, []

    # ---------------------------------------------------------------- table_coded
    co = "census-api-acs5-2023-b19013-counties-colorado"
    header = line(co, '[["NAME","B19013_001E","B19013_001M","state","county"],')
    rows = block(co, '["Adams County, Colorado"', '["Boulder County, Colorado"')
    dev_passages["acs-co-block1"] = header + "\n" + rows
    dev_meta["acs-co-block1"] = {"surface_type": "table_coded", "surface_file": surface_file(co), "source_doc_id": co,
                                 "parts": [{"doc_id": co, "text": header}, {"doc_id": co, "text": rows}],
                                 "legend_on_surface": False, "declared_leg_score": None}
    dev_props += acs_props(co, "g1v2-acs-co", header, [
        ("Adams County, Colorado", line(co, '["Adams County, Colorado"'), 91387, 1470),
        ("Alamosa County, Colorado", line(co, '["Alamosa County, Colorado"'), 51445, 6098),
        ("Arapahoe County, Colorado", line(co, '["Arapahoe County, Colorado"'), 97215, 1592),
        ("Archuleta County, Colorado", line(co, '["Archuleta County, Colorado"'), 76524, 6714),
        ("Bent County, Colorado", line(co, '["Bent County, Colorado"'), 49194, 4596),
        ("Boulder County, Colorado", line(co, '["Boulder County, Colorado"'), 102772, 2628),
    ], "acs-co-block1", cmap)

    idh = "census-api-acs5-2023-b19013-counties-idaho"
    header_i = line(idh, '[["NAME","B19013_001E","B19013_001M","state","county"],')
    rows_i = block(idh, '["Ada County, Idaho"', '["Benewah County, Idaho"')
    hold_passages["acs-id-block1"] = header_i + "\n" + rows_i
    hold_meta["acs-id-block1"] = {"surface_type": "table_coded", "surface_file": surface_file(idh), "source_doc_id": idh,
                                  "parts": [{"doc_id": idh, "text": header_i}, {"doc_id": idh, "text": rows_i}],
                                  "legend_on_surface": False, "declared_leg_score": None}
    hold_props += acs_props(idh, "g1v2h-acs-id", header_i, [
        ("Ada County, Idaho", line(idh, '["Ada County, Idaho"'), 88907, 1710),
        ("Bannock County, Idaho", line(idh, '["Bannock County, Idaho"'), 64080, 2470),
        ("Bear Lake County, Idaho", line(idh, '["Bear Lake County, Idaho"'), 67304, 6987),
    ], "acs-id-block1", cmap)

    # ---------------------------------------------------------------- table_labeled
    lfs = "statcan-14-10-0287-01-lfs-2026-07-provinces-estimate-se-csv"
    h = line(lfs, '"REF_DATE","GEO","DGUID","Labour force characteristics"')
    ab = block(lfs, '"2026-07","Alberta","2021A000248","Population"', '"2026-07","Alberta","2021A000248","Employment rate","Total - Gender","15 years and over","Standard error of estimate"')
    dev_passages["lfs-2026-07-alberta"] = h + "\n" + ab
    dev_meta["lfs-2026-07-alberta"] = {"surface_type": "table_labeled", "surface_file": surface_file(lfs), "source_doc_id": lfs,
                                       "parts": [{"doc_id": lfs, "text": h}, {"doc_id": lfs, "text": ab}],
                                       "legend_on_surface": False, "declared_leg_score": None}
    dev_props += lfs_props(lfs, "g1v2-lfs-ab", "Alberta", "2026-07", [
        ("Unemployment rate", "percent", 7.0, 0.4, "7.0"),
        ("Participation rate", "percent", 69.2, 0.5, "69.2"),
        ("Employment rate", "percent", 64.3, 0.5, "64.3"),
        ("Employment", "count", 2670.0, 19.8, "2670.0"),
        ("Unemployment", "count", 202.2, 11.8, "202.2"),
        ("Labour force", "count", 2872.2, 18.8, "2872.2"),
    ], "lfs-2026-07-alberta")

    lfs12 = "statcan-14-10-0287-01-lfs-2025-12-provinces-estimate-se-csv"
    h12 = line(lfs12, '"REF_DATE","GEO","DGUID","Labour force characteristics"')
    bc = block(lfs12, '"2025-12","British Columbia","2021A000259","Population"', '"2025-12","British Columbia","2021A000259","Employment rate","Total - Gender","15 years and over","Standard error of estimate"')
    hold_passages["lfs-2025-12-bc"] = h12 + "\n" + bc
    hold_meta["lfs-2025-12-bc"] = {"surface_type": "table_labeled", "surface_file": surface_file(lfs12), "source_doc_id": lfs12,
                                   "parts": [{"doc_id": lfs12, "text": h12}, {"doc_id": lfs12, "text": bc}],
                                   "legend_on_surface": False, "declared_leg_score": None}
    bc_rows = _lfs_values(lfs12, "British Columbia", "2025-12", ["Unemployment rate", "Employment", "Unemployment"])
    hold_props += lfs_props(lfs12, "g1v2h-lfs-bc", "British Columbia", "2025-12", bc_rows, "lfs-2025-12-bc")

    # ---------------------------------------------------------------- flagged_cell (StatCan letters)
    cchs, cmeta = "statcan-13-10-0096-01-cchs-2022-provinces-percent-ci-csv", "statcan-13-10-0096-01-cube-metadata-csv"
    hc = line(cchs, '"REF_DATE","GEO","DGUID","Age group","Sex","Indicators"')
    legend = block(cmeta, "Symbol Legend", '"suppressed to meet the confidentiality requirements of the Statistics Act","x",')
    youth = "Body mass index, self-reported, youth (12 to 17 years old), overweight or obese"
    obese = "Body mass index, adjusted self-reported, adult (18 years and over), obese"
    nl = block(cchs, f'"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","{obese}","Percent"',
               '"2022","Newfoundland and Labrador","2016A000210","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent"')
    dev_passages["cchs-2022-nl"] = hc + "\n" + nl + "\n" + legend
    dev_meta["cchs-2022-nl"] = {"surface_type": "flagged_cell", "surface_file": surface_file(cchs), "source_doc_id": cchs,
                                "parts": [{"doc_id": cchs, "text": hc}, {"doc_id": cchs, "text": nl}, {"doc_id": cmeta, "text": legend}],
                                "legend_on_surface": True, "legend_file": surface_file(cmeta),
                                "legend_note": "the legend is served in the table's cube-metadata file, not in the data CSV; it is appended to the passage as its own verbatim part so the consumer sees what the download package carries",
                                "declared_leg_score": None}
    note = "flagged_cell (StatCan CSV): STATUS column carries the quality letter; the symbol legend is the passage's last part."
    dev_props.append(cchs_prop(cchs, "g1v2-cchs-nl-youth", "Newfoundland and Labrador", "2022", youth, "cchs-2022-nl", flagged=True,
                               label="overweight or obese youth (12 to 17, self-reported BMI)", legend_on_surface=True, rule=CCHS_RULE, table_note=note))
    dev_props.append(cchs_prop(cchs, "g1v2-cchs-nl-obese", "Newfoundland and Labrador", "2022", obese, "cchs-2022-nl", flagged=False,
                               label="obese adults (18 and over, adjusted self-reported BMI)", legend_on_surface=True, rule=CCHS_RULE, table_note=note))
    pe = block(cchs, f'"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","{obese}","Percent"',
               '"2022","Prince Edward Island","2016A000211","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent"')
    dev_passages["cchs-2022-pe"] = hc + "\n" + pe + "\n" + legend
    dev_meta["cchs-2022-pe"] = dict(dev_meta["cchs-2022-nl"], parts=[{"doc_id": cchs, "text": hc}, {"doc_id": cchs, "text": pe}, {"doc_id": cmeta, "text": legend}])
    dev_props.append(cchs_prop(cchs, "g1v2-cchs-pe-youth", "Prince Edward Island", "2022", youth, "cchs-2022-pe", flagged=True,
                               label="overweight or obese youth (12 to 17, self-reported BMI)", legend_on_surface=True, rule=CCHS_RULE, table_note=note))
    dev_props.append(cchs_prop(cchs, "g1v2-cchs-pe-diabetes", "Prince Edward Island", "2022", "Diabetes", "cchs-2022-pe", flagged=False,
                               label="diabetes (12 and over)", legend_on_surface=True, rule=CCHS_RULE, table_note=note))

    qc, qmeta = "statcan-13-10-0113-01-cchs-2021-2022-quebec-health-regions-percent-ci-csv", "statcan-13-10-0113-01-cube-metadata-csv"
    hq = line(qc, '"REF_DATE","GEO","DGUID","Age group","Sex","Indicators"')
    legend_q = block(qmeta, "Symbol Legend", '"suppressed to meet the confidentiality requirements of the Statistics Act","x",')
    for geo, dg, pid_geo in (("Région de Laval, Quebec", "2015A00072413", "laval"), ("Région de Lanaudière, Quebec", "2015A00072414", "lanaudiere")):
        blk = block(qc, f'"2021/2022","{geo}","{dg}","Total, 12 years and over","Both sexes","{obese}","Percent"',
                    f'"2021/2022","{geo}","{dg}","Total, 12 years and over","Both sexes","Diabetes","High 95% confidence interval, percent"')
        pid_pass = f"cchs113-qc-{pid_geo}"
        hold_passages[pid_pass] = hq + "\n" + blk + "\n" + legend_q
        hold_meta[pid_pass] = {"surface_type": "flagged_cell", "surface_file": surface_file(qc), "source_doc_id": qc,
                               "parts": [{"doc_id": qc, "text": hq}, {"doc_id": qc, "text": blk}, {"doc_id": qmeta, "text": legend_q}],
                               "legend_on_surface": True, "legend_file": surface_file(qmeta),
                               "legend_note": dev_meta["cchs-2022-nl"]["legend_note"], "declared_leg_score": None}
        hold_props.append(cchs_prop(qc, f"g1v2h-cchs113-{pid_geo}-youth", geo, "2021/2022", youth, pid_pass, flagged=True,
                                    label="overweight or obese youth (12 to 17, self-reported BMI)", legend_on_surface=True, rule=CCHS113_RULE, table_note=note))
        hold_props.append(cchs_prop(qc, f"g1v2h-cchs113-{pid_geo}-diabetes", geo, "2021/2022", "Diabetes", pid_pass, flagged=False,
                                    label="diabetes (12 and over)", legend_on_surface=True, rule=CCHS113_RULE, table_note=note))

    # ---------------------------------------------------------------- flagged_cell (NCHS †)
    n530 = "nchs-data-brief-530-perinatal-mortality-2022-2023"
    tbl = block(n530, "Data table for Figure 4. Perinatal mortality rate, by state", "Delaware .")
    leg = line(n530, "Change not significant (p = 0.05)")
    dev_passages["nchs530-fig4-al-de"] = tbl + "\n" + leg
    dev_meta["nchs530-fig4-al-de"] = {"surface_type": "flagged_cell", "surface_file": surface_file(n530), "source_doc_id": n530,
                                      "parts": [{"doc_id": n530, "text": tbl}, {"doc_id": n530, "text": leg}],
                                      "legend_on_surface": True, "declared_leg_score": None,
                                      "legend_note": "the † legend is printed directly beneath the state table; the passage joins the table's first block with that legend line"}
    for state, r23, r22 in (("Alaska", 7.73, 8.39), ("Arizona", 9.28, 9.56), ("Connecticut", 7.63, 6.93), ("Delaware", 8.68, 9.66)):
        dev_props.append(nchs530_prop(n530, f"g1v2-nchs530-{state.lower()}", state, r23, r22, "nchs530-fig4-al-de"))

    # ---------------------------------------------------------------- footnoted (NCHS body -> appendix table)
    n500 = "nchs-data-brief-500-dental-visits-adults-65-2022"
    body1 = span(n500, " ● In 2022, 63.7% of adults age 65 and older had a dental visit in the past 12 months (Figure 1,",
                 "to 53.3% among those age 85 and older.")
    tbl1 = block(n500, "Data table for Figure 1. Percentage of adults age 65 and older who had a dental visit", "85 and older.")
    dev_passages["nchs500-fig1"] = body1 + "\n" + tbl1
    dev_meta["nchs500-fig1"] = {"surface_type": "footnoted", "surface_file": surface_file(n500), "source_doc_id": n500,
                                "parts": [{"doc_id": n500, "text": body1}, {"doc_id": n500, "text": tbl1}],
                                "legend_on_surface": False, "declared_leg_score": None,
                                "footnote_distance_chars": distance(n500, body1, tbl1)}
    dev_props += [
        nchs_footnoted_prop(n500, "g1v2-nchs500-total", "the percentage of adults age 65 and older who had a dental visit in the past 12 months in 2022",
                            "In 2022, 63.7% of adults age 65 and older had a dental visit in the past 12 months", "Total . . .", 63.7, "63.7", "62.4", "65.1", "0.68", "nchs500-fig1", "2022",
                            row_after="Data table for Figure 1"),
        nchs_footnoted_prop(n500, "g1v2-nchs500-men", "the percentage of men age 65 and older who had a dental visit in the past 12 months in 2022",
                            "Men (62.3%) were less likely than women (64.9%) to have had a dental visit.", "Men . . .", 62.3, "62.3", "60.5", "64.2", "0.94", "nchs500-fig1", "2022",
                            row_after="Data table for Figure 1"),
        nchs_footnoted_prop(n500, "g1v2-nchs500-women", "the percentage of women age 65 and older who had a dental visit in the past 12 months in 2022",
                            "Men (62.3%) were less likely than women (64.9%) to have had a dental visit.", "Women  . . .", 64.9, "64.9", "63.1", "66.6", "0.88", "nchs500-fig1", "2022",
                            row_after="Data table for Figure 1"),
        nchs_footnoted_prop(n500, "g1v2-nchs500-65-74", "the percentage of adults ages 65–74 who had a dental visit in the past 12 months in 2022",
                            "decreased from 65.4% among those \nages 65–74", "65–74. . .", 65.4, "65.4", "63.7", "67.1", "0.86", "nchs500-fig1", "2022",
                            row_after="Data table for Figure 1"),
        nchs_footnoted_prop(n500, "g1v2-nchs500-85", "the percentage of adults age 85 and older who had a dental visit in the past 12 months in 2022",
                            "to 53.3% among those age 85 and older.", "85 and older. . .", 53.3, "53.3", "49.2", "57.3", "2.02", "nchs500-fig1", "2022",
                            row_after="Data table for Figure 1"),
    ]

    n515 = "nchs-data-brief-515-high-total-cholesterol-2021-2023"
    body2 = span(n515, "During August 2021–August 2023, the prevalence of low HDL-C was 13.8% in adults", "(Figure 2, Table 2).")
    tbl2 = block(n515, "Data table for Figure 2. Prevalence of low high-density lipoprotein cholesterol", "NOTES:")
    tbl2 = tbl2[: tbl2.rindex("\nNOTES:")]
    hold_passages["nchs515-fig2"] = body2 + "\n" + tbl2
    hold_meta["nchs515-fig2"] = {"surface_type": "footnoted", "surface_file": surface_file(n515), "source_doc_id": n515,
                                 "parts": [{"doc_id": n515, "text": body2}, {"doc_id": n515, "text": tbl2}],
                                 "legend_on_surface": False, "declared_leg_score": None,
                                 "footnote_distance_chars": distance(n515, body2, tbl2)}
    hold_props += [
        nchs_footnoted_prop(n515, "g1v2h-nchs515-lowhdl-total", "the prevalence of low HDL-C in adults age 20 and older during August 2021–August 2023 (crude)",
                            "the prevalence of low HDL-C was 13.8% in adults", "20 and older (crude)", 13.8, "13.8", "12.1", "15.7", "0.8", "nchs515-fig2", "August 2021–August 2023",
                            row_after="Data table for Figure 2. Prevalence of low high-density"),
        nchs_footnoted_prop(n515, "g1v2h-nchs515-lowhdl-men", "the prevalence of low HDL-C in men age 20 and older during August 2021–August 2023 (crude)",
                            "higher in men (21.5%) than in women (6.6%)", "20 and older (crude)", 21.5, "21.5", "18.6", "24.6", "1.4", "nchs515-fig2", "August 2021–August 2023",
                            row_after=["Data table for Figure 2. Prevalence of low high-density", "Men"]),
        nchs_footnoted_prop(n515, "g1v2h-nchs515-lowhdl-women", "the prevalence of low HDL-C in women age 20 and older during August 2021–August 2023 (crude)",
                            "higher in men (21.5%) than in women (6.6%)", "20 and older (crude)", 6.6, "6.6", "5.4", "8.0", "0.6", "nchs515-fig2", "August 2021–August 2023",
                            row_after=["Data table for Figure 2. Prevalence of low high-density", "Women"]),
    ]

    # ---------------------------------------------------------------- footnoted (BLS technical note)
    bls = "bls-employment-situation-2026-08-news-release"
    head = block(bls, "Both nonfarm payroll employment (-23,000)", "education and retail trade. Employment continued to trend up in health care.")
    tech = block(bls, "For example, the confidence interval for the monthly change in total nonfarm",
                 "chance that the true over-the-month change lies within this interval.")
    dev_passages["bls-2026-07-headline-technote"] = head + "\n" + tech
    dev_meta["bls-2026-07-headline-technote"] = {"surface_type": "footnoted", "surface_file": surface_file(bls), "source_doc_id": bls,
                                                 "parts": [{"doc_id": bls, "text": head}, {"doc_id": bls, "text": tech}],
                                                 "legend_on_surface": False, "declared_leg_score": None,
                                                 "footnote_distance_chars": distance(bls, head, tech)}
    dev_props.append(bls_prop(bls, "g1v2-bls-2026-07-payrolls", "July 2026", -23000, "-23,000", "Both nonfarm payroll employment (-23,000)", "bls-2026-07-headline-technote"))

    bls5 = "bls-employment-situation-2026-05-news-release-archive"
    head5 = block(bls5, "Total nonfarm payroll employment increased by 172,000 in May, and the unemployment rate was", "reported today.")
    tech5 = block(bls5, "For example, the confidence interval for the monthly change in total nonfarm",
                  "chance that the true over-the-month change lies within this interval.")
    hold_passages["bls-2026-05-headline-technote"] = head5 + "\n" + tech5
    hold_meta["bls-2026-05-headline-technote"] = {"surface_type": "footnoted", "surface_file": surface_file(bls5), "source_doc_id": bls5,
                                                  "parts": [{"doc_id": bls5, "text": head5}, {"doc_id": bls5, "text": tech5}],
                                                  "legend_on_surface": False, "declared_leg_score": None,
                                                  "footnote_distance_chars": distance(bls5, head5, tech5)}
    hold_props.append(bls_prop(bls5, "g1v2h-bls-2026-05-payrolls", "May 2026", 172000, "172,000", "Total nonfarm payroll employment increased by 172,000 in May, and the unemployment rate was", "bls-2026-05-headline-technote"))

    # declared-leg scores (step 3, scripts/g1_declared_surfaces.py) join on the surface file
    dl = OUT / "declared_leg.json"
    if dl.exists():
        scores = {v["surface_file"]: v["score"] for v in json.loads(dl.read_text(encoding="utf-8"))["surfaces"].values()}
        for meta in (dev_meta, hold_meta):
            for m in meta.values():
                m["declared_leg_score"] = scores.get(m["surface_file"])
    dev = {"passages": dev_passages, "passage_meta": dev_meta, "propositions": dev_props}
    hold = {"passages": hold_passages, "passage_meta": hold_meta, "propositions": hold_props}
    return dev, hold


def _lfs_values(doc_id: str, geo: str, ref: str, chars: list[str]):
    """Read (characteristic, unit, estimate, se, estimate_text) from the captured rows."""
    lines = source_text(doc_id).split("\n")
    out = []
    for ch in chars:
        est = [ln for ln in lines if f'"{ref}","{geo}"' in ln and f'"{ch}","Total - Gender"' in ln and '"Estimate"' in ln][0]
        se = [ln for ln in lines if f'"{ref}","{geo}"' in ln and f'"{ch}","Total - Gender"' in ln and '"Standard error of estimate"' in ln][0]
        ecells, scells = est.split('","'), se.split('","')
        unit = "percent" if ecells[8] == "Percent" else "count"
        out.append((ch, unit, float(ecells[14]), float(scells[14]), ecells[14]))
    return out


HEADER = """# fixture_version: {fv}
# G1 EVAL v2 proposition fixtures — {which} set (task 2026-09-03_g1_eval_v2_product_surfaces_compression
# step 2). GENERATED by scripts/gen_g1_v2_fixtures.py from the product surfaces admitted under epoch
# g1sfc-2026-09-03 — every passage is the newline-join of verbatim `parts` (passage_meta), each a
# contiguous block of one captured corpus file; tests/test_g1_fixtures.py re-checks every part against
# the corpus file and asserts zero passage overlap between the two splits. Do not hand-edit.
#
# Surface types on this file: {surfaces}
# Propositions per surface type: {counts}
# no_declared surfaces (census-quickfacts-denver-county-colorado, …-csv, census-api-dec2020-dhc-p1-counties-colorado)
# carry no observed-leg proposition by construction; they are scored by the declared leg only
# (assessment/tests/fixtures/g1/v2/declared_leg.json).
#
# Schema additions over v1: surface_type, surface_file, binding {{row|sentence, row_key}},
# footnote_distance_chars (footnoted), code_map (table_coded; from the API's variables endpoint, never
# shown to the consumer), legend_on_surface (flagged_cell); RELIABILITY_FLAG gains symbol / legend /
# status_column; the estimate of a table_coded proposition is labelled by its CODE so the direct prompt
# never decodes the surface.
"""


def dump(path: Path, doc: dict, which: str):
    counts: dict = {}
    for p in doc["propositions"]:
        counts[p["surface_type"]] = counts.get(p["surface_type"], 0) + 1
    head = HEADER.format(fv=FIXTURE_VERSION, which=which, surfaces=sorted(counts), counts=counts)
    body = yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=1000)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head + body, encoding="utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-network", action="store_true")
    a = ap.parse_args(argv)
    dev, hold = build(a.no_network)
    dump(OUT / "propositions.yaml", dev, "DEVELOPMENT")
    dump(OUT / "propositions_holdout.yaml", hold, "HELD-OUT")
    for name in ("propositions.yaml", "propositions_holdout.yaml"):
        fs = load_fixture_set(OUT / name)
        print(f"{name}: {len(fs.propositions)} propositions on {len(fs.passage_ids())} passages; "
              f"by surface {fs.counts_by_surface()}; by class {fs.counts_by_class()}")
    # zero passage overlap by normalised text
    d = {normalize(t) for t in dev["passages"].values()}
    h = {normalize(t) for t in hold["passages"].values()}
    print("passage overlap (normalised):", len(d & h))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
