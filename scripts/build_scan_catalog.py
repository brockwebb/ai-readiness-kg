#!/usr/bin/env python3
"""The scan catalog: every scan the framework could run, who can run it, how, at what effort, and
what each action and enabler unlocks. **Zero spend, no network, reads only.**

`cc_tasks/2026-10-02_scan_catalog.md` with ADDENDUM-01 (task `aaffd0db`), under DN-009 decisions
2, 6 and 8 and DN-010. The catalog is a VIEW: no row is hand-authored. Every table is built from

* the framework record (`framework/ai_readiness_framework.json`): indicators, criteria, measurement
  specs, the requirements layer (`AssessmentTool`, `Precondition`, `REQUIRES`) and the prescription
  layer (`Action`, `REMEDIATES`, notional bands);
* the evidence map (`docs/evidence/claims.yaml`): CL-001's Q1 class per unmeasured indicator and the
  Q6 equal-weight bounds (CL-055 onward), read and never recomputed;
* the declared inputs (`docs/catalog/catalog_inputs.yaml`): value ratings under rubric v1, cheap-pass
  judgements, enabler leads, tool licences and URLs, searched methods, front-door signatures, each
  with its source;
* the stored observations of the cycle of record's source cycle (`state/scan_2026-09-10.json`), for
  the front door only;
* `scan.rules.CURRENT`, for which legs have a built rule.

    /opt/anaconda3/bin/python3 scripts/build_scan_catalog.py           write every output
    /opt/anaconda3/bin/python3 scripts/build_scan_catalog.py --check   regenerate in memory; exit 1 on drift

**The value columns never leave this directory.** DN-010 §2.1: a value rating is not an input to the
score, a rank or a bound. `tests/test_scan_catalog.py` asserts that no scoring, ranking or bound
module mentions them.

**Idempotence.** Nothing reads a clock; every collection is sorted; `--check` compares bytes.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import yaml  # noqa: E402

from scan import load_params                 # noqa: E402
from scan.rules import CURRENT               # noqa: E402

TASK = "cc_tasks/2026-10-02_scan_catalog.md"
RECORD = REPO / "framework" / "ai_readiness_framework.json"
CLAIMS = REPO / "docs" / "evidence" / "claims.yaml"
MANIFEST = REPO / "corpus" / "manifest.json"
OUT = REPO / "docs" / "catalog"
INPUTS = OUT / "catalog_inputs.yaml"
README = OUT / "README.md"
ROLLUPS = OUT / "rollups"

#: The one line DN-010 §2.5 requires on every rendering that shows a value.
VALUE_LABEL = ("Value is a rated judgment under a stated rubric (v1), not a measurement; it enters "
               "no score, rank or bound.")

# ---------------------------------------------------------------- closed vocabularies (README)
WHO = ("public_outside_in", "agency_enabled", "agency_records", "needs_standard")
#: Precedence when a route needs several things: the hardest one decides (README).
WHO_ORDER = ("agency_records", "agency_enabled", "needs_standard", "public_outside_in")
METHOD = ("built_rule", "tool_open_source", "tool_commercial", "roll_your_own", "none_known")
ROW_SOURCE = ("record", "catalog_search", "proposed_link")
Q1 = ("open_tooling", "funding", "no_standard", "agency_cooperation", "not_blocked", "measured", "TBD")
CHEAP = ("yes", "no", "TBD")
GRADE = ("established", "plausible", "unevidenced")
VALUE_BASIS = ("evidence", "rubric", "TBD")
LINK = ("existing_node", "proposed_link", "unsupported")
BAND = ("1", "2", "3", "4", "5", "TBD")
TBD = "TBD"

#: Requirement kind -> who must act. Anything the publisher provides is the agency's; within it,
#: records only it holds are `agency_records` and the rest is something it turns on.
KIND_WHO = {
    "agency_records": "agency_records",
    "site_owner_account": "agency_enabled",
    "platform_account": "agency_enabled",
    "publisher_grant": "agency_enabled",
    "benchmark_set": "needs_standard",
    "open_source": "public_outside_in",
    "hosted_free": "public_outside_in",
    "hosted_paid": "public_outside_in",
    "second_cycle": "public_outside_in",
}
#: Tool kind -> method_kind. A hosted free API is a client this project writes (README).
TOOL_METHOD = {"open_source": "tool_open_source", "hosted_paid": "tool_commercial",
               "platform_account": "tool_commercial", "hosted_free": "roll_your_own"}

SCAN_COLUMNS = (
    "row_id", "indicator", "framework_member", "criterion", "serves", "indicator_text", "why",
    "measurement_tier", "measurement_status", "q1_class", "q1_claim", "route", "method_kind",
    "method", "rule_id", "tool_name", "licence", "url", "locator", "spec_locator", "failed_searches",
    "who_can_run", "requirements", "unlocked_by", "row_source", "staffing_band", "cost_band",
    "effort_level", "band_basis", "value_rating", "value_basis", "value_reason", "evidence_grade",
    "evidence_sources", "rated_by", "operator_override", "cheap_pass", "cheap_pass_basis", "basis")

ACTION_COLUMNS = (
    "action_id", "title", "indicator", "also_moves", "leg", "outcome", "framework_member",
    "criterion", "serves", "technique_class", "record_effort_band", "record_cost_band",
    "staffing_band", "cost_band", "effort_level", "band_basis", "bound_equal_weights_census",
    "bound_claim", "bodies_failing_now", "what_would_have_to_be_done", "who_does_it", "verifies_by",
    "value_rating", "value_basis", "value_reason", "evidence_grade", "evidence_sources", "rated_by",
    "operator_override", "cheap_pass", "cheap_pass_basis", "named_row", "row_source", "basis")

ENABLER_COLUMNS = ("enabler_id", "name", "status", "method_kind", "who_can_run", "who_acts", "url",
                   "step_quote", "step_locator", "indicator", "link", "capability_quote",
                   "capability_locator", "requirement_nodes", "note")

FRONT_DOOR_COLUMNS = ("body", "tier", "hosts", "front_door_observed", "named_by",
                      "n_observations_naming", "n_observations_on_hosts", "observation_ids")


# ======================================================================================= inputs

class Inputs:
    def __init__(self):
        self.record = json.loads(RECORD.read_text(encoding="utf-8"))
        self.claims = yaml.safe_load(CLAIMS.read_text(encoding="utf-8"))
        self.cfg = yaml.safe_load(INPUTS.read_text(encoding="utf-8"))
        self.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))["entries"]
        self.params = load_params()
        self.nodes = {n["id"]: n for n in self.record["nodes"]}
        self.edges = self.record["edges"]

    def label(self, label: str) -> list:
        return [n for n in self.record["nodes"] if label in n["labels"]]

    def out(self, src: str, etype: str) -> list:
        return [e for e in self.edges if e["from"] == src and e["type"] == etype]

    def into(self, dst: str, etype: str) -> list:
        return [e for e in self.edges if e["to"] == dst and e["type"] == etype]

    def manifest_url(self, doc_id: str) -> str:
        e = self.manifest.get(doc_id)
        if not e or not e["identity"].get("source_url"):
            raise SystemExit(f"FATAL: {doc_id} has no source_url in corpus/manifest.json")
        return e["identity"]["source_url"]


def code_key(code: str):
    """A1 < A2 < A10 < A11 < B1 ... with G1-D before G1-O."""
    m = re.match(r"([A-Z])(\d+)(.*)", code)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else (code, 0, "")


def rec_loc(node_id: str) -> str:
    return f"framework/ai_readiness_framework.json#{node_id}"


def band_str(v) -> str:
    return TBD if v in (None, TBD) else str(v)


def effort_level(staff: str, cost: str) -> str:
    if TBD in (staff, cost):
        return TBD
    return str(max(int(staff), int(cost)))


# ===================================================================================== shared

def q1_classes(I: Inputs) -> dict:
    """`{indicator: (class, claim_id)}` from CL-001's evidence notes and the per-indicator Q1
    claims. Read, never recomputed."""
    by_key = {c["key"]: c for c in I.claims["claims"]}
    part = by_key["q1.partition"]
    out = {}
    for ev in part["evidence"]:
        if ev["kind"] == "indicator":
            code = ev["id"].removeprefix("ind:")
            claim = by_key.get(f"q1.{code}")
            out[code] = (ev["note"], claim["id"] if claim else part["id"])
    return out


def q6_bounds(I: Inputs) -> dict:
    """`{action_id: (bound, claim_id)}` for the Census actions Q6 bounds (CL-055 onward)."""
    out = {}
    for c in I.claims["claims"]:
        if c["question"] == "Q6":
            act = "act:" + c["key"].removeprefix("q6.")
            if act not in I.nodes:
                raise SystemExit(f"FATAL: {c['id']} names {act}, which is not in the record")
            out[act] = (c["numbers"][0]["value"], c["id"])
    return out


def criteria(I: Inputs) -> dict:
    return {n["properties"]["code"]: n["properties"]["name"] for n in I.label("AssessmentCriterion")}


def indicators(I: Inputs) -> list:
    return sorted(I.label("AssessmentIndicator"), key=lambda n: code_key(n["properties"]["code"]))


def is_candidate(p: dict) -> bool:
    return bool(p.get("candidate_rationale"))


def source_locator(I: Inputs, key: str, table: str = "sources") -> str:
    s = I.cfg[table][key]
    if s["kind"] in ("corpus", "corpus_pdf"):
        sec = f", {s['section']}" if s.get("section") else ""
        return f"{s['path']} (doc_id {s['doc_id']}){sec}"
    if s["kind"] == "web":
        return s["url"]
    return s["locator"]


def grade_for(I: Inputs, leg: str, has_record_source: bool) -> tuple:
    """`(evidence_grade, sources)` for a leg. A consumer source on file makes it `established`;
    otherwise a record source (EVIDENCED_BY, technique_source) makes it `plausible`."""
    keys = I.cfg["evidence_by_leg"].get(leg, [])
    if any(I.cfg["sources"][k]["consumer"] for k in keys):
        return "established", keys
    return ("plausible" if has_record_source else "unevidenced"), keys


def value_for(I: Inputs, code: str, grade: str, override: dict | None) -> dict:
    if override:
        rating, basis, reason = override["rating"], override["basis"], override["reason"]
    else:
        v = I.cfg["value"][code]
        rating, reason = v["rating"], v["reason"]
        basis = TBD if rating == TBD else ("evidence" if grade == "established" else "rubric")
    return {"value_rating": band_str(rating), "value_basis": basis, "value_reason": reason,
            "rated_by": I.cfg["rated_by"], "operator_override": ""}


def cheap_for(I: Inputs, key: str) -> tuple:
    c = I.cfg["cheap_pass"].get(key)
    if c is None:
        return TBD, "no described case on file"
    return c["value"], c["basis"]


# ================================================================================== scan rows

def scan_rows(I: Inputs) -> list:
    crit = criteria(I)
    q1 = q1_classes(I)
    built_legs = set(CURRENT)
    bands = I.cfg["bands"]
    rows = []
    for n in indicators(I):
        p = n["properties"]
        code = p["code"]
        has_src = bool(I.out(n["id"], "EVIDENCED_BY"))
        base = {
            "indicator": code,
            "framework_member": "no" if is_candidate(p) else "yes",
            "criterion": p["criterion_code"],
            "serves": f"{p['criterion_code']} {crit[p['criterion_code']]}",
            "indicator_text": p["indicator"],
            "why": p.get("candidate_rationale") or TBD,
            "measurement_tier": p.get("measurement_tier") or TBD,
            "measurement_status": p["measurement_status"],
        }
        if p["measurement_status"] == "measured":
            base["q1_class"], base["q1_claim"] = "measured", ""
        elif code in q1:
            base["q1_class"], base["q1_claim"] = q1[code]
        else:
            base["q1_class"], base["q1_claim"] = TBD, ""
        why_basis = ("" if p.get("candidate_rationale") else
                     "why: the record carries no rationale field on the indicator")
        q1_basis = ("q1_class: CL-001 partitions framework indicators only (DD-054)"
                    if base["q1_class"] == TBD else "")

        # 1. Built rules: the indicator's specs whose rule is current, or a harness-mode spec.
        for e in sorted(I.out(n["id"], "MEASURED_BY"), key=lambda e: e["to"]):
            sp = I.nodes[e["to"]]["properties"]
            built = CURRENT.get(sp["leg"]) == sp["rule_id"] or sp["mode"] == "harness"
            if not built:
                continue
            leg = sp["leg"]
            grade, srcs = grade_for(I, leg if leg in I.cfg["evidence_by_leg"] else code, has_src)
            cp, cpb = cheap_for(I, leg)
            rows.append({**base,
                         "row_id": f"S-{code}-rule-{leg}", "route": f"rule:{leg}",
                         "method_kind": "built_rule", "method": sp["signal"],
                         "rule_id": sp["rule_id"], "tool_name": sp["collector"], "licence": "",
                         "url": "", "locator": rec_loc(e["to"]), "spec_locator": rec_loc(e["to"]),
                         "failed_searches": "", "who_can_run": "public_outside_in",
                         "requirements": "", "unlocked_by": "", "row_source": "record",
                         "staffing_band": str(bands["built_rule"]["staffing"]),
                         "cost_band": str(bands["built_rule"]["cost"]),
                         "effort_level": str(max(bands["built_rule"]["staffing"],
                                                 bands["built_rule"]["cost"])),
                         "band_basis": bands["built_rule"]["basis"],
                         **value_for(I, code, grade, None), "evidence_grade": grade,
                         "evidence_sources": ";".join(srcs),
                         "cheap_pass": cp, "cheap_pass_basis": cpb,
                         "basis": "; ".join(x for x in (why_basis, q1_basis) if x)})

        # 2. One row per REQUIRES route (routes are alternatives).
        routes = defaultdict(list)
        for e in I.out(n["id"], "REQUIRES"):
            routes[e["properties"]["route"]].append(e)
        for route in sorted(routes):
            es = sorted(routes[route], key=lambda e: e["to"])
            reqs = [I.nodes[e["to"]] for e in es]
            tools = [r for r in reqs if "AssessmentTool" in r["labels"]]
            kinds = [r["properties"]["kind"] for r in reqs]
            who = next(w for w in WHO_ORDER if w in {
                ("agency_enabled" if r["properties"]["who_provides"] == "publisher"
                 and KIND_WHO[r["properties"]["kind"]] == "public_outside_in"
                 else KIND_WHO[r["properties"]["kind"]]) for r in reqs})
            e0 = es[0]["properties"]
            row = {**base, "row_id": f"S-{code}-{route}", "route": route,
                   "method": e0["test"], "rule_id": "", "failed_searches": "",
                   "who_can_run": who, "requirements": ";".join(e["to"] for e in es),
                   "row_source": "record", "spec_locator": e0.get("source") or rec_loc(n["id"])}
            basis = [why_basis, q1_basis]
            if tools:
                t = tools[0]
                tp = t["properties"]
                tcfg = I.cfg["tools"][t["id"]]
                url = I.manifest_url(tp["doc_id"]) if tcfg["url"] == "manifest" else tcfg["url"]
                row["method_kind"] = TOOL_METHOD[tp["kind"]]
                row["tool_name"] = tp["name"]
                row["licence"] = tcfg["licence"]
                row["url"] = url
                if tp["doc_source"] != "none_on_disk":
                    row["locator"] = tp["doc_source"]
                elif tcfg.get("locator_quote"):
                    row["locator"] = f"{tcfg['url_source']}: \"{tcfg['locator_quote']}\""
                else:
                    # A hosted API the record names without a document: its own note says where.
                    row["locator"] = f"{rec_loc(t['id'])} (doc_source_note); {tcfg['url_source']}"
                if tcfg["licence"] in (TBD,) or tcfg["licence"].startswith("n/a"):
                    basis.append(f"licence: {tcfg['licence_reason']}")
                costs = [band_str(bands["cost_from_cost"][x["properties"]["cost_band"]])
                         for x in tools]
                cost = TBD if TBD in costs else str(max(int(c) for c in costs))
                staff = TBD
                band_basis = ("cost: notional_record (tool cost_band "
                              + ", ".join(x["properties"]["cost_band"] for x in tools)
                              + "); staffing: the record has no staffing band for a tool")
            elif kinds == ["second_cycle"] and code in built_legs:
                row["method_kind"] = "built_rule"
                row["rule_id"] = CURRENT[code]
                row["tool_name"] = ""
                row["licence"] = ""
                row["url"] = ""
                row["locator"] = rec_loc(es[0]["to"])
                staff = str(bands["built_rule"]["staffing"])
                cost = str(bands["built_rule"]["cost"])
                band_basis = bands["built_rule"]["basis"]
            else:
                row["method_kind"] = "roll_your_own"
                row["tool_name"] = ""
                row["licence"] = ""
                row["url"] = ""
                row["locator"] = rec_loc(es[0]["to"])
                staff, cost = TBD, TBD
                band_basis = "no band on a Precondition in the record"
            groups = I.cfg["unlocker_groups"]
            row["unlocked_by"] = "+".join(sorted({groups.get(e["to"], e["to"]) for e in es}))
            grade, srcs = grade_for(I, code, has_src)
            cp, cpb = cheap_for(I, code)
            row.update({"staffing_band": staff, "cost_band": cost,
                        "effort_level": effort_level(staff, cost), "band_basis": band_basis,
                        **value_for(I, code, grade, None), "evidence_grade": grade,
                        "evidence_sources": ";".join(srcs), "cheap_pass": cp,
                        "cheap_pass_basis": cpb, "basis": "; ".join(x for x in basis if x)})
            rows.append(row)

        # 3. Searched or record-named methods for what the record leaves without one.
        for m in [m for m in I.cfg["methods"] if m["indicator"] == code]:
            grade, srcs = grade_for(I, code, has_src)
            cp, cpb = cheap_for(I, code)
            nk = m["method_kind"] == "none_known"
            rows.append({**base, "row_id": f"S-{code}-{m['route']}", "route": m["route"],
                         "method_kind": m["method_kind"], "method": m["method"], "rule_id": "",
                         "tool_name": "", "licence": "", "url": "",
                         "locator": rec_loc(n["id"]),
                         "spec_locator": "" if nk else (
                             m["spec_locator"] + (f": \"{m['spec_quote']}\""
                                                  if m.get("spec_quote") else "")),
                         "failed_searches": m.get("failed_searches", ""),
                         "who_can_run": m["who_can_run"], "requirements": "",
                         "unlocked_by": "" if nk else f"method:{code}:{m['route']}",
                         "row_source": m["row_source"], "staffing_band": TBD, "cost_band": TBD,
                         "effort_level": TBD,
                         "band_basis": "no band in the record and no cited source for one",
                         **value_for(I, code, grade, None), "evidence_grade": grade,
                         "evidence_sources": ";".join(srcs), "cheap_pass": cp,
                         "cheap_pass_basis": cpb,
                         "basis": "; ".join(x for x in (why_basis, q1_basis, m.get("note", ""))
                                            if x)})

    # 4. Enabler leads that would need a new requirement node (decision 4).
    by_code = {n["properties"]["code"]: n for n in indicators(I)}
    for en in sorted(I.cfg["enablers"], key=lambda e: e["id"]):
        for cap in en["capabilities"]:
            if cap["link"] != "proposed_link":
                continue
            for code in cap["indicators"]:
                p = by_code[code]["properties"]
                has_src = bool(I.out(by_code[code]["id"], "EVIDENCED_BY"))
                grade, srcs = grade_for(I, code, has_src)
                cp, cpb = cheap_for(I, code)
                status = p["measurement_status"]
                q = ("measured", "") if status == "measured" else q1_classes(I).get(code, (TBD, ""))
                rows.append({
                    "row_id": f"S-{code}-{en['id'].removeprefix('enabler:')}",
                    "indicator": code, "framework_member": "no" if is_candidate(p) else "yes",
                    "criterion": p["criterion_code"],
                    "serves": f"{p['criterion_code']} {crit[p['criterion_code']]}",
                    "indicator_text": p["indicator"], "why": p.get("candidate_rationale") or TBD,
                    "measurement_tier": p.get("measurement_tier") or TBD,
                    "measurement_status": status, "q1_class": q[0], "q1_claim": q[1],
                    "route": en["id"], "method_kind": en["method_kind"], "method": cap["quote"],
                    "rule_id": "", "tool_name": en["name"],
                    "licence": ("n/a: vendor service" if en["method_kind"] == "tool_commercial"
                                else TBD),
                    "url": en["url"],
                    "locator": enabler_locator(I, cap["source"], cap["quote"]),
                    "spec_locator": "", "failed_searches": "",
                    "who_can_run": en["who_can_run"], "requirements": "",
                    "unlocked_by": en["id"], "row_source": "proposed_link",
                    "staffing_band": TBD, "cost_band": TBD, "effort_level": TBD,
                    "band_basis": "no band in the record and no cited source for one",
                    **value_for(I, code, grade, None), "evidence_grade": grade,
                    "evidence_sources": ";".join(srcs), "cheap_pass": cp, "cheap_pass_basis": cpb,
                    "basis": "; ".join(x for x in (
                        "" if p.get("candidate_rationale") else
                        "why: the record carries no rationale field on the indicator",
                        cap.get("note", ""),
                        "licence: hosted vendor service; terms not read"
                        if en["method_kind"] == "tool_commercial" else
                        "licence: not stated in the source on file")
                        if x)})
    return rows


def enabler_locator(I: Inputs, key: str, quote: str) -> str:
    s = I.cfg["enabler_sources"].get(key) or I.cfg["sources"].get(key)
    if s["kind"] in ("corpus", "corpus_pdf"):
        where = f"{s['path']} (doc_id {s['doc_id']})"
    elif s["kind"] == "web":
        where = s["url"]
    else:
        where = s["locator"]
    return f"{where}: \"{quote}\"" if quote else where


# ================================================================================ action rows

def action_rows(I: Inputs) -> list:
    crit = criteria(I)
    q6 = q6_bounds(I)
    bands = I.cfg["bands"]
    named = I.cfg["named_rows"]
    robots_tags = set(named["robots_txt"]["tags"])
    overrides = I.cfg["action_overrides"]
    rows = []
    for a in sorted(I.label("Action"), key=lambda n: (code_key(n["properties"]["indicator_code"]),
                                                       n["id"])):
        p = a["properties"]
        ind = I.nodes[f"ind:{p['indicator_code']}"]["properties"]
        code = ind["code"]
        staff = band_str(bands["staffing_from_effort"][p["effort_band"]])
        cost = band_str(bands["cost_from_cost"][p["cost_band"]])
        band_basis = (f"notional_record ({p['effort_source']}; {p['cost_source']})"
                      + ("; cost: procurement is open above, no source sizes it"
                         if cost == TBD else ""))
        ov = overrides.get(a["id"])
        if ov:
            grade = "established" if any(I.cfg["sources"][k]["consumer"]
                                         for k in ov["evidence"]) else "plausible"
            srcs = list(ov["evidence"])
        else:
            grade, srcs = grade_for(I, p["leg"], bool(p["technique_source"]))
        if not p["applies_to_publisher"]:
            val = {"value_rating": TBD, "value_basis": TBD,
                   "value_reason": I.cfg["value"][code]["reason"], "rated_by": I.cfg["rated_by"],
                   "operator_override": ""}
        else:
            val = value_for(I, code, grade, ov)
        cp, cpb = cheap_for(I, p["leg"])
        bound, claim = q6.get(a["id"], (TBD, ""))
        basis = []
        if bound == TBD:
            basis.append("bound: not in Q6 of the evidence map (Q6 bounds the Census actions in "
                         "the hours band, CL-055 onward)")
        tags = "robots_txt" if a["id"] in robots_tags else ""
        rows.append({
            "action_id": a["id"], "title": p["title"], "indicator": code, "also_moves": "",
            "leg": p["leg"], "outcome": p["outcome"],
            "framework_member": "no" if is_candidate(ind) else "yes",
            "criterion": ind["criterion_code"],
            "serves": f"{ind['criterion_code']} {crit[ind['criterion_code']]}",
            "technique_class": p["technique_class"], "record_effort_band": p["effort_band"],
            "record_cost_band": p["cost_band"], "staffing_band": staff, "cost_band": cost,
            "effort_level": effort_level(staff, cost), "band_basis": band_basis,
            "bound_equal_weights_census": bound, "bound_claim": claim,
            "bodies_failing_now": str(p["value"]["bodies_failing_now"]),
            "what_would_have_to_be_done": p["description"],
            "who_does_it": "publisher" if p["applies_to_publisher"] else "this_project",
            "verifies_by": p["verifies_by"], **val, "evidence_grade": grade,
            "evidence_sources": ";".join(srcs), "cheap_pass": cp, "cheap_pass_basis": cpb,
            "named_row": tags, "row_source": "record", "basis": "; ".join(basis)})
    # The named row the record has no Action for (addendum decision 11).
    ll = named["llms_txt"]
    ov = overrides[ll["id"]]
    ind = I.nodes[f"ind:{ll['indicator']}"]["properties"]
    bands_cls = {"publish_new_file": ("days", "staff_time")}[ll["technique_class"]]
    staff = band_str(bands["staffing_from_effort"][bands_cls[0]])
    cost = band_str(bands["cost_from_cost"][bands_cls[1]])
    cp, cpb = cheap_for(I, ll["id"])
    rows.append({
        "action_id": ll["id"], "title": ll["title"], "indicator": ll["indicator"],
        "also_moves": ";".join(ll["also_moves"]), "leg": ll["indicator"], "outcome": "",
        "framework_member": "yes", "criterion": ind["criterion_code"],
        "serves": f"{ind['criterion_code']} {crit[ind['criterion_code']]}",
        "technique_class": ll["technique_class"], "record_effort_band": "",
        "record_cost_band": "", "staffing_band": staff, "cost_band": cost,
        "effort_level": effort_level(staff, cost),
        "band_basis": ("notional_record by technique class publish_new_file "
                       "(cc_tasks/2026-09-17_notional_bands.md decision 2 names llms.txt in it)"),
        "bound_equal_weights_census": TBD, "bound_claim": "", "bodies_failing_now": "",
        "what_would_have_to_be_done": ll["what_would_have_to_be_done"],
        "who_does_it": ll["who_does_it"], "verifies_by": "RULE-A5-v2; RULE-A9-v1",
        "value_rating": band_str(ov["rating"]), "value_basis": ov["basis"],
        "value_reason": ov["reason"], "rated_by": I.cfg["rated_by"], "operator_override": "",
        "evidence_grade": "unevidenced", "evidence_sources": ";".join(ll["citations"]),
        "cheap_pass": cp, "cheap_pass_basis": cpb, "named_row": "llms_txt",
        "row_source": "catalog_search",
        "basis": ("evidence_grade: the proposal prescribes the file and no source shows a consumer "
                  "reads it; the measurement on file says 97% of files got zero requests. "
                  "searches: " + ll["searches"]
                  + "; bound: not in Q6 (no record Action)")})
    return rows


# ================================================================================== enablers

def enabler_rows(I: Inputs) -> list:
    rows = []
    for en in sorted(I.cfg["enablers"], key=lambda e: e["id"]):
        links = [c["link"] for c in en["capabilities"]]
        status = ("supported" if any(l in ("existing_node", "proposed_link") for l in links)
                  else "unsupported")
        step = en["step"]
        for cap in en["capabilities"]:
            for code in (cap["indicators"] or [""]):
                rows.append({
                    "enabler_id": en["id"], "name": en["name"], "status": status,
                    "method_kind": en["method_kind"], "who_can_run": en["who_can_run"],
                    "who_acts": en["who_acts"], "url": en["url"], "step_quote": step["quote"],
                    "step_locator": enabler_locator(I, step["source"], ""),
                    "indicator": code, "link": cap["link"], "capability_quote": cap["quote"],
                    "capability_locator": enabler_locator(I, cap["source"], ""),
                    "requirement_nodes": ";".join(en["requirements"]),
                    "note": cap.get("note", "")})
    return rows


# ================================================================================ front door

def front_door(I: Inputs) -> list:
    fd = I.cfg["front_door"]
    payload = json.loads((REPO / "state" / f"{I.cfg['source_cycle']}.json")
                         .read_text(encoding="utf-8"))
    tier_c = {t["name"] for t in I.params["frame"]["tier_c"]}
    hosts = defaultdict(set)
    for m in payload["matrix"]:
        hosts[m["agency"]].add(urlparse(m["url"]).hostname)
    host_body = {h: b for b, hs in hosts.items() for h in hs}
    vendors = fd["vendors"]
    named = defaultdict(lambda: defaultdict(set))   # body -> vendor -> {obs ids}
    how = defaultdict(set)                           # (body, vendor) -> {"header x" | "refusal page"}
    on_host = Counter()
    for o in payload["observations_detail"]:
        body = host_body.get(urlparse(o["request"]["url"]).hostname)
        if body is None:
            continue
        on_host[body] += 1
        resp = o.get("response") or {}
        for k, v in sorted((resp.get("headers") or {}).items()):
            k_l, v_l = k.lower(), str(v).lower()
            for vend in vendors:
                if fd["header_names_read"] and vend in k_l:
                    named[body][vend].add(o["obs_id"])
                    how[(body, vend)].add(f"header name `{k_l}`")
                elif k_l in fd["header_values_read"] and vend in v_l:
                    named[body][vend].add(o["obs_id"])
                    how[(body, vend)].add(f"`{k_l}` value")
        if resp.get("status") in fd["refusal_statuses"] and resp.get("body_path"):
            path = REPO / resp["body_path"]
            if path.is_file():
                text = path.read_bytes()[:65536].decode("utf-8", "replace").lower()
                for vend in vendors:
                    if vend in text:
                        named[body][vend].add(o["obs_id"])
                        how[(body, vend)].add(f"HTTP {resp['status']} refusal page body")
    rows = []
    for body in sorted(hosts, key=lambda b: (b in tier_c, b.lower())):
        vs = sorted(named[body])
        ids = sorted(set().union(*named[body].values())) if vs else []
        rows.append({
            "body": body, "tier": "C" if body in tier_c else "A",
            "hosts": ";".join(sorted(hosts[body])),
            "front_door_observed": ";".join(vs) if vs else "not_observed_in_record",
            "named_by": "; ".join(f"{v}: " + ", ".join(sorted(how[(body, v)])) for v in vs),
            "n_observations_naming": str(len(ids)),
            "n_observations_on_hosts": str(on_host[body]),
            "observation_ids": ";".join(ids[:5]) + (f";(+{len(ids) - 5} more)" if len(ids) > 5
                                                     else "")})
    return rows


# ================================================================================== rollups

def unmeasured_framework(I: Inputs) -> list:
    return [n["properties"]["code"] for n in indicators(I)
            if n["properties"]["measurement_status"] != "measured"
            and not is_candidate(n["properties"])]


def unlockers(I: Inputs, rows: list) -> list:
    U = set(unmeasured_framework(I))
    sets = defaultdict(lambda: {"rows": [], "inds": set(), "who": set(), "kinds": set()})
    for r in rows:
        if not r["unlocked_by"]:
            continue
        s = sets[r["unlocked_by"]]
        s["rows"].append(r["row_id"])
        s["inds"].add(r["indicator"])
        s["who"].add(r["who_can_run"])
        s["kinds"].add(r["method_kind"])
    out = []
    for k, s in sets.items():
        um = sorted(s["inds"] & U, key=code_key)
        out.append({"unlocked_by": k, "who_can_run": ";".join(sorted(s["who"])),
                    "method_kinds": ";".join(sorted(s["kinds"])), "n_rows": str(len(s["rows"])),
                    "n_indicators": str(len(s["inds"])),
                    "indicators": ";".join(sorted(s["inds"], key=code_key)),
                    "n_unmeasured": str(len(um)), "unmeasured_indicators": ";".join(um)})
    out.sort(key=lambda r: (-int(r["n_unmeasured"]), -int(r["n_indicators"]), r["unlocked_by"]))
    return out


#: Who can act alone first. Not WHO_ORDER, which ranks the hardest requirement first.
ACT_ALONE = ("public_outside_in", "needs_standard", "agency_enabled", "agency_records")


def hardest(whos: str) -> int:
    """The position of the hardest who-can-run among an unlocker's rows."""
    return max(ACT_ALONE.index(w) for w in whos.split(";"))


def set_cover(I: Inputs, rows: list, unl: list) -> tuple:
    """Greedy set cover (Chvátal 1979) over the unmeasured framework indicators, ordered by count
    only (DN-009 d3). A tie breaks first on who must act, in the order an outside party can act
    alone (`public_outside_in`, `needs_standard`, `agency_enabled`, `agency_records`: the order
    `scripts/build_evidence_map.py::Q1_ORDER` uses for the same reason), then on the name, so the
    order is deterministic and no tie is broken by a judgment of worth."""
    U = set(unmeasured_framework(I))
    sets = {u["unlocked_by"]: set(filter(None, u["unmeasured_indicators"].split(";")))
            for u in unl}
    who = {u["unlocked_by"]: u["who_can_run"] for u in unl}
    covered, steps = set(), []
    while True:
        best = sorted(((len(s - covered), k) for k, s in sets.items() if s - covered),
                      key=lambda t: (-t[0], hardest(who[t[1]]), t[1]))
        if not best:
            break
        gain, k = best[0]
        new = sorted(sets[k] - covered, key=code_key)
        covered |= sets[k]
        steps.append({"step": str(len(steps) + 1), "unlocked_by": k, "who_can_run": who[k],
                      "newly_covered": ";".join(new), "n_new": str(gain),
                      "cumulative": str(len(covered)), "of_unmeasured": str(len(U))})
    rest = sorted(U - covered, key=code_key)
    reasons = {}
    for code in rest:
        rs = [r for r in rows if r["indicator"] == code]
        kinds = sorted({r["method_kind"] for r in rs})
        reasons[code] = (f"no row offers anything to obtain: method kinds {', '.join(kinds)}"
                         if rs else "no row")
    return steps, [{"indicator": c, "reason": reasons[c]} for c in rest]


def crosstab(rows: list, rkey: str, rvals: list, ckey: str, cvals: list, label: str) -> list:
    out = []
    for rv in rvals:
        line = {label: rv}
        for cv in cvals:
            line[cv] = str(sum(1 for r in rows if r[rkey] == rv and r[ckey] == cv))
        line["total"] = str(sum(1 for r in rows if r[rkey] == rv))
        out.append(line)
    tot = {label: "total"}
    for cv in cvals:
        tot[cv] = str(sum(1 for r in rows if r[ckey] == cv))
    tot["total"] = str(len(rows))
    out.append(tot)
    return out


def grid(rows: list, id_key: str) -> tuple:
    """DN-010 grid, long form: one line per (effort, value) cell, then one per row with a TBD axis."""
    cells, side = [], []
    for e in range(1, 6):
        for v in range(1, 6):
            ids = sorted(r[id_key] for r in rows
                         if r["effort_level"] == str(e) and r["value_rating"] == str(v))
            cells.append({"effort_level": str(e), "value_rating": str(v), "n": str(len(ids)),
                          "row_ids": ";".join(ids), "reason": ""})
    for r in sorted(rows, key=lambda r: r[id_key]):
        if TBD in (r["effort_level"], r["value_rating"]):
            why = []
            if r["effort_level"] == TBD:
                why.append(f"effort TBD (staffing {r['staffing_band']}, cost {r['cost_band']}: "
                           f"{r['band_basis']})")
            if r["value_rating"] == TBD:
                why.append(f"value TBD ({r['value_reason']})")
            side.append({"effort_level": r["effort_level"], "value_rating": r["value_rating"],
                         "n": "1", "row_ids": r[id_key], "reason": "; ".join(why)})
    return cells, side


def flat_lists(rows: list, id_key: str, title_key: str, table: str) -> list:
    out = []
    for r in sorted(rows, key=lambda r: r[id_key]):
        if TBD in (r["effort_level"], r["value_rating"]):
            continue
        e, v = int(r["effort_level"]), int(r["value_rating"])
        if e <= 2 and v >= 4:
            lst = "quick_win"
        elif e <= 2 and v <= 2:
            lst = "clear_out"
        else:
            continue
        out.append({"list": lst, "table": table, "row_id": r[id_key], "effort_level": str(e),
                    "value_rating": str(v), "title": r[title_key],
                    "evidence_grade": r["evidence_grade"], "cheap_pass": r["cheap_pass"]})
    return out


# ================================================================================== rendering

def to_csv(rows: list, columns) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(columns), lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({c: r.get(c, "") for c in columns})
    return buf.getvalue()


def md_cell(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def md_table(rows: list, columns) -> str:
    cols = list(columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        lines.append("| " + " | ".join(md_cell(r.get(c, "")) for c in cols) + " |")
    return "\n".join(lines) + "\n"


HEADER = ("<!-- GENERATED by scripts/build_scan_catalog.py (cc_tasks/2026-10-02_scan_catalog.md). "
          "Do not edit; re-run the generator. -->\n\n")


def render_scans_md(rows: list) -> str:
    cols = ("row_id", "who_can_run", "method_kind", "route", "rule_id", "tool_name", "q1_class",
            "measurement_tier", "effort_level", "value_rating", "evidence_grade", "cheap_pass",
            "row_source")
    return (HEADER + "# Scan catalog\n\n" + f"*{VALUE_LABEL}*\n\n"
            f"{len(rows)} rows, one per (indicator, scan method). Every column, with its locator and "
            "basis, is in `scan_catalog.csv`; vocabularies are in `README.md`.\n\n"
            + md_table(rows, cols))


def render_actions_md(rows: list) -> str:
    cols = ("action_id", "indicator", "who_does_it", "record_effort_band", "record_cost_band",
            "effort_level", "value_rating", "value_basis", "evidence_grade", "cheap_pass",
            "bound_equal_weights_census", "named_row")
    return (HEADER + "# Actions\n\n" + f"*{VALUE_LABEL}*\n\n"
            f"{len(rows)} rows: every Action in the record's prescription layer, plus the named row "
            "the record has no Action for. The bound is Q6 of the evidence map (Census, equal "
            "weights), read and not recomputed; no weighting is asserted, so it is a bound and not a "
            "value. Full columns are in `actions.csv`.\n\n" + md_table(rows, cols))


def render_enablers_md(rows: list) -> str:
    cols = ("enabler_id", "status", "who_can_run", "indicator", "link", "capability_quote",
            "capability_locator", "step_quote")
    return (HEADER + "# Agency-side enablers (decision 4)\n\n"
            "Leads, not facts. Each capability is quoted from the vendor's documentation; "
            "`existing_node` joins through the record's requirements layer, `proposed_link` would "
            "need a new node, `unsupported` is a link no source establishes.\n\n"
            + md_table(rows, cols))


def render_rollups_md(unl, steps, rest, cbw, sbc_s, sbc_a, ms_cells, ms_side, ma_cells, ma_side,
                      flats, n_unmeasured) -> str:
    out = [HEADER, "# Rollups\n\n", f"*{VALUE_LABEL}*\n\n",
           "Generated from the two tables. Nothing is ranked by value, impact or return "
           "(DN-009 decision 3); order is by count or by band.\n\n",
           "## (a) What each tool, enabler or requirement set unlocks\n\n",
           md_table(unl, ("unlocked_by", "who_can_run", "method_kinds", "n_unmeasured",
                          "unmeasured_indicators", "n_indicators", "indicators")),
           f"\n## (a) Greedy set cover over the {n_unmeasured} unmeasured framework indicators\n\n",
           "Greedy set cover (Chvátal 1979): at each step, the unlocker that covers the most "
           "indicators not yet covered; ties break on its name.\n\n",
           md_table(steps, ("step", "unlocked_by", "who_can_run", "n_new", "newly_covered",
                            "cumulative", "of_unmeasured")),
           "\nNo row offers anything to obtain for these (built rule only, or no known method):\n\n",
           md_table(rest, ("indicator", "reason")),
           "\n## (b) Criterion by who can run it (rows)\n\n",
           md_table(cbw, ("criterion",) + WHO + ("total",)),
           "\n## (c) Staffing band by cost band (rows)\n\nScans:\n\n",
           md_table(sbc_s, ("staffing_band",) + BAND + ("total",)),
           "\nActions:\n\n",
           md_table(sbc_a, ("staffing_band",) + BAND + ("total",))]
    for name, cells, side in (("scans", ms_cells, ms_side), ("actions", ma_cells, ma_side)):
        out.append(f"\n## DN-010 effort-by-value grid: {name}\n\n*{VALUE_LABEL}*\n\n")
        out.append("| effort \\ value | 1 | 2 | 3 | 4 | 5 |\n|---|---|---|---|---|---|\n")
        for e in range(5, 0, -1):
            line = [f"**{e}**"]
            for v in range(1, 6):
                c = next(x for x in cells if x["effort_level"] == str(e)
                         and x["value_rating"] == str(v))
                line.append(f"{c['n']}: {c['row_ids']}" if c["n"] != "0" else "0")
            out.append("| " + " | ".join(md_cell(x) for x in line) + " |\n")
        out.append(f"\nBeside the grid ({len(side)} rows with a `TBD` axis):\n\n")
        out.append(md_table(side, ("row_ids", "effort_level", "value_rating", "reason")))
    out.append(f"\n## Quick wins and clear-outs\n\n*{VALUE_LABEL}*\n\n"
               "Quick win: effort at most 2 and value at least 4. Clear it out: effort at most 2 "
               "and value at most 2.\n\n")
    out.append(md_table(flats, ("list", "table", "row_id", "effort_level", "value_rating",
                                "evidence_grade", "cheap_pass", "title")))
    return "".join(out)


#: The summary's label for an unmeasured indicator no row offers anything to obtain for.
NO_ROUTE = "no_route_to_obtain"


def summary_block(I: Inputs, scans: list, unl: list, flats: list) -> str:
    """Computed statements only: each number below is a count over the tables."""
    U = unmeasured_framework(I)
    easiest = {}
    for code in U:
        whos = [r["who_can_run"] for r in scans if r["indicator"] == code and r["unlocked_by"]]
        easiest[code] = min(whos, key=ACT_ALONE.index) if whos else NO_ROUTE
    order = list(ACT_ALONE) + [NO_ROUTE]
    lines = [f"Of the {len(U)} framework indicators the record does not mark measured, the easiest "
             "route on any row needs:\n\n", "| easiest route | n | indicators |\n|---|---|---|\n"]
    for w in order:
        codes = sorted((c for c in U if easiest[c] == w), key=code_key)
        lines.append(f"| `{w}` | {len(codes)} | {', '.join(codes)} |\n")
    lines.append(f"\n`{NO_ROUTE}` means no row offers anything to obtain: the indicator has a built "
                 "rule the record does not mark measured, and its unmeasured half has no known "
                 "method (`none_known`) or nothing stands in its way but the definition of "
                 "measured. It does not mean the indicator needs nothing.\n")
    ens = [u for u in unl if u["unlocked_by"].startswith("enabler:")]
    top_un = max(int(u["n_unmeasured"]) for u in ens)
    top_all = max(int(u["n_indicators"]) for u in ens)
    lines.append(
        f"\nNo agency-side enabler unlocks more than {top_un} unmeasured framework indicator(s): "
        + "; ".join(f"`{u['unlocked_by']}` reaches {u['unmeasured_indicators'] or 'none'}"
                    for u in ens if int(u["n_unmeasured"]) == top_un)
        + f". Counting indicators already measured, the widest reaches {top_all}: "
        + "; ".join(f"`{u['unlocked_by']}` ({u['indicators']})"
                    for u in ens if int(u["n_indicators"]) == top_all)
        + ". Those extra links deepen a measured indicator (its unmeasured half, or its coverage); "
          "they do not add one.\n")
    qa = [f for f in flats if f["list"] == "quick_win" and f["table"] == "actions"]
    qs = [f for f in flats if f["list"] == "quick_win" and f["table"] == "scans"]
    lines.append(
        f"\nThe actions quick-win cell (effort at most 2, value at least 4) holds {len(qa)} "
        f"action(s), {sum(f['evidence_grade'] == 'established' for f in qa)} of them `established` "
        f"and {sum(f['cheap_pass'] == 'yes' for f in qa)} of them with `cheap_pass: yes`: "
        + ", ".join(f"`{f['row_id']}`" for f in qa) + ". The scans quick-win cell holds "
        f"{len(qs)} row(s), all of them `built_rule`: a built rule costs nothing more to run, so "
        "the scan grid says which built rules matter most, not what to build.\n"
        if all(next(r for r in scans if r["row_id"] == f["row_id"])["method_kind"] == "built_rule"
               for f in qs) else
        f"\nThe actions quick-win cell holds {len(qa)} action(s); the scans quick-win cell "
        f"holds {len(qs)} row(s).\n")
    return "".join(lines)


def fill_readme(text: str, blocks: dict) -> str:
    for name, body in blocks.items():
        pat = re.compile(rf"(<!-- BEGIN GENERATED: {name} -->\n).*?(<!-- END GENERATED: {name} -->)",
                         re.S)
        if not pat.search(text):
            raise SystemExit(f"FATAL: README has no generated block `{name}`")
        text = pat.sub(lambda m: m.group(1) + body + m.group(2), text)
    return text


# ======================================================================================= main

def build() -> dict:
    I = Inputs()
    scans = scan_rows(I)
    acts = action_rows(I)
    ens = enabler_rows(I)
    fd = front_door(I)
    unl = unlockers(I, scans)
    steps, rest = set_cover(I, scans, unl)
    crit_codes = sorted(criteria(I))
    cbw = crosstab(scans, "criterion", crit_codes, "who_can_run", list(WHO), "criterion")
    sbc_s = crosstab(scans, "staffing_band", list(BAND), "cost_band", list(BAND), "staffing_band")
    sbc_a = crosstab(acts, "staffing_band", list(BAND), "cost_band", list(BAND), "staffing_band")
    ms_cells, ms_side = grid(scans, "row_id")
    ma_cells, ma_side = grid(acts, "action_id")
    flats = (flat_lists(scans, "row_id", "indicator_text", "scans")
             + flat_lists(acts, "action_id", "title", "actions"))
    n_un = len(unmeasured_framework(I))

    files = {
        OUT / "scan_catalog.csv": to_csv(scans, SCAN_COLUMNS),
        OUT / "scan_catalog.md": render_scans_md(scans),
        OUT / "actions.csv": to_csv(acts, ACTION_COLUMNS),
        OUT / "actions.md": render_actions_md(acts),
        OUT / "enablers.csv": to_csv(ens, ENABLER_COLUMNS),
        OUT / "enablers.md": render_enablers_md(ens),
        OUT / "front_door.csv": to_csv(fd, FRONT_DOOR_COLUMNS),
        ROLLUPS / "unlockers.csv": to_csv(unl, ("unlocked_by", "who_can_run", "method_kinds",
                                                "n_rows", "n_indicators", "indicators",
                                                "n_unmeasured", "unmeasured_indicators")),
        ROLLUPS / "set_cover.csv": to_csv(steps, ("step", "unlocked_by", "who_can_run", "n_new",
                                                  "newly_covered", "cumulative",
                                                  "of_unmeasured")),
        ROLLUPS / "set_cover_uncovered.csv": to_csv(rest, ("indicator", "reason")),
        ROLLUPS / "criterion_by_who.csv": to_csv(cbw, ("criterion",) + WHO + ("total",)),
        ROLLUPS / "staffing_by_cost.csv": (
            to_csv([{"table": "scans", **r} for r in sbc_s]
                   + [{"table": "actions", **r} for r in sbc_a],
                   ("table", "staffing_band") + BAND + ("total",))),
        ROLLUPS / "matrix_scans.csv": to_csv(ms_cells + ms_side, ("effort_level", "value_rating",
                                                                   "n", "row_ids", "reason")),
        ROLLUPS / "matrix_actions.csv": to_csv(ma_cells + ma_side, ("effort_level", "value_rating",
                                                                     "n", "row_ids", "reason")),
        ROLLUPS / "quick_wins.csv": to_csv(flats, ("list", "table", "row_id", "effort_level",
                                                   "value_rating", "evidence_grade", "cheap_pass",
                                                   "title")),
        ROLLUPS / "rollups.md": render_rollups_md(unl, steps, rest, cbw, sbc_s, sbc_a, ms_cells,
                                                  ms_side, ma_cells, ma_side, flats, n_un),
    }

    en_sum = []
    for en in sorted(I.cfg["enablers"], key=lambda e: e["id"]):
        rs = [r for r in ens if r["enabler_id"] == en["id"]]
        links = defaultdict(list)
        for r in rs:
            if r["indicator"]:
                links[r["link"]].append(r["indicator"])
        en_sum.append({"enabler": en["id"], "status": rs[0]["status"],
                       "who_can_run": en["who_can_run"],
                       "existing_node": ";".join(sorted(set(links["existing_node"]), key=code_key)),
                       "proposed_link": ";".join(sorted(set(links["proposed_link"]), key=code_key)),
                       "unsupported": ";".join(sorted(set(links["unsupported"]), key=code_key))})
    counts = [
        f"- Scan rows: {len(scans)}, over {len({r['indicator'] for r in scans})} indicators "
        f"({len(unmeasured_framework(I))} framework indicators are not measured).\n",
        "- By who can run it: " + ", ".join(f"`{w}` {sum(r['who_can_run'] == w for r in scans)}"
                                            for w in WHO) + ".\n",
        "- By method kind: " + ", ".join(f"`{m}` {sum(r['method_kind'] == m for r in scans)}"
                                         for m in METHOD) + ".\n",
        "- By row source: " + ", ".join(f"`{s}` {sum(r['row_source'] == s for r in scans)}"
                                        for s in ROW_SOURCE) + ".\n",
        f"- Action rows: {len(acts)} ({sum(r['row_source'] == 'record' for r in acts)} from the "
        f"record, {sum(r['row_source'] != 'record' for r in acts)} named).\n",
        f"- Greedy set cover: {len(steps)} steps cover "
        f"{steps[-1]['cumulative'] if steps else 0} of {n_un} unmeasured framework indicators; "
        f"for {len(rest)}, no row offers anything to obtain.\n",
    ]
    blocks = {
        "summary": "\n" + summary_block(I, scans, unl, flats) + "\n",
        "codes": "\nCriteria, as the record names them: "
                 + "; ".join(f"`{k}` {v}" for k, v in sorted(criteria(I).items())) + ".\n\n"
                 + md_table(
            [{"code": n["properties"]["code"], "criterion": n["properties"]["criterion_code"],
              "status": n["properties"]["measurement_status"],
              "indicator": n["properties"]["indicator"]
              + (" (candidate, DD-054)" if is_candidate(n["properties"]) else "")}
             for n in indicators(I)], ("code", "criterion", "status", "indicator")) + "\n",
        "enablers": "\n" + md_table(en_sum, ("enabler", "status", "who_can_run", "existing_node",
                                             "proposed_link", "unsupported")) + "\n",
        "front_door": "\n" + md_table(fd, ("body", "tier", "front_door_observed", "named_by",
                                           "n_observations_naming", "observation_ids")) + "\n",
        "counts": "\n" + "".join(counts) + "\n",
    }
    files[README] = fill_readme(README.read_text(encoding="utf-8"), blocks)
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="regenerate in memory and exit 1 on any drift from the files on disk")
    a = ap.parse_args(argv)
    files = build()
    if a.check:
        drift = [str(p.relative_to(REPO)) for p, text in files.items()
                 if not p.is_file() or p.read_text(encoding="utf-8") != text]
        if drift:
            print("DRIFT: " + ", ".join(sorted(drift)))
            return 1
        print(f"no drift in {len(files)} file(s)")
        return 0
    ROLLUPS.mkdir(parents=True, exist_ok=True)
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"wrote {len(files)} file(s) under {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
