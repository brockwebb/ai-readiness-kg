"""G1 declared leg — are error measures published as structured FIELDS beside estimates?

The A11 triad's first leg for uncertainty (skeleton §5d G1 note): declared uncertainty
= structured MOE/CV/SE/CI/flag/DP fields in the distribution itself, "not footnotes".
This is a HEURISTIC ON FIELD NAMES: it reads a CSV header or the keys of a JSON record
and matches them against the pattern table in harness.toml `[g1]`. It says that a field
named like an uncertainty measure exists; it says nothing about whether the values in it
are right (that is the producer's rule and the observed leg's business). The pattern id
that matched travels in the observations so every verdict is traceable to its rule.

PASS    uncertainty fields present AND each pairs with an estimate field (by the
        producer's naming convention where one is configured — ACS `_E`/`_M` — or, for
        unconventioned names, at least one uncertainty field per non-identifier field
        set); i.e. the estimates carry structured error measures.
PARTIAL uncertainty fields present for only some estimate fields, or uncertainty
        mentioned only in a notes/footnote column or in the body text (skeleton G1:
        "not footnotes").
FAIL    no uncertainty field and no mention at all.

Sources: catalog distributions only (a product page is not a table).
"""
from __future__ import annotations

import csv
import io
import json
import re
from typing import Iterable, List, Optional, Sequence, Tuple

from ..fetch import Fetched
from ..records import SOURCE_CATALOG, Score, Track
from .base import DistributionProbe

_MAX_HEADER_BYTES = 65536


def _compiled(rows: Sequence[dict]) -> List[Tuple[dict, "re.Pattern"]]:
    return [(row, re.compile(row["regex"])) for row in rows]


def header_fields(fetched: Fetched, distribution: dict) -> Tuple[List[str], str]:
    """(field names, how they were read). CSV: first row. JSON: keys of the first record
    (a list of objects, or an object with a `fields`/`columns`/`variables` table, or the
    object's own keys)."""
    body = (fetched.body or "")[:_MAX_HEADER_BYTES]
    media = ((distribution or {}).get("mediaType") or fetched.content_type or "").lower()
    url = (fetched.final_url or fetched.requested_url or "").lower()
    if "json" in media or url.endswith(".json"):
        try:
            data = json.loads(fetched.body or "")
        except (json.JSONDecodeError, ValueError):
            return [], "json_unparseable"
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, list):            # Census API shape: header row then rows
                return [str(x) for x in first], "json_header_row"
            if isinstance(first, dict):
                return [str(k) for k in first.keys()], "json_first_record_keys"
        if isinstance(data, dict):
            for key in ("fields", "columns", "variables", "schema"):
                tbl = data.get(key)
                if isinstance(tbl, dict):
                    return [str(k) for k in tbl.keys()], f"json_{key}_keys"
                if isinstance(tbl, list) and tbl and isinstance(tbl[0], dict):
                    names = [str(x.get("name") or x.get("id") or x.get("field") or "") for x in tbl]
                    return [n for n in names if n], f"json_{key}_names"
            return [str(k) for k in data.keys()], "json_object_keys"
        return [], "json_no_records"
    if "csv" in media or url.endswith(".csv") or "text/plain" in media:
        first_line = body.splitlines()[0] if body.strip() else ""
        try:
            fields = next(csv.reader(io.StringIO(first_line)))
        except (csv.Error, StopIteration):
            return [], "csv_no_header"
        return [f.strip() for f in fields if f.strip()], "csv_header"
    return [], "unsupported_media"


class G1DeclaredProbe(DistributionProbe):
    probe_id = "g1_declared"
    dimension = "G1"
    track = Track.CORE
    sources = (SOURCE_CATALOG,)

    def __init__(self, uncertainty_patterns: Sequence[dict], footnote_patterns: Sequence[dict],
                 id_patterns: Sequence[dict], footnote_vocabulary: Iterable[str]):
        self._unc = _compiled(uncertainty_patterns)
        self._fn = _compiled(footnote_patterns)
        self._id = _compiled(id_patterns)
        self._vocab = tuple(v.lower() for v in footnote_vocabulary)

    def _classify(self, fields: List[str]):
        uncertainty, footnote, ids, estimates = [], [], [], []
        pairs = []
        for f in fields:
            hit = None
            for row, rx in self._unc:
                m = rx.search(f)
                if m:
                    hit = row
                    partner = None
                    if row.get("pairs_with"):
                        try:
                            partner = m.expand(row["pairs_with"])
                        except (re.error, IndexError):
                            partner = None
                    uncertainty.append({"field": f, "pattern_id": row["id"], "class": row["class"],
                                        "pairs_with": partner})
                    break
            if hit:
                continue
            if any(rx.search(f) for _, rx in self._fn):
                footnote.append(f)
            elif any(rx.search(f) for _, rx in self._id):
                ids.append(f)
            else:
                estimates.append(f)
        field_set = set(fields)
        for u in uncertainty:
            if u["pairs_with"] and u["pairs_with"] in field_set:
                pairs.append((u["field"], u["pairs_with"]))
        return uncertainty, footnote, ids, estimates, pairs

    def evaluate(self, fetched: Fetched, distribution: dict):
        if not fetched.ok or not (fetched.body or "").strip():
            return Score.FAIL, f"distribution not retrievable (status={fetched.status})", {
                "read_from": "none", "fields": []}
        fields, how = header_fields(fetched, distribution)
        uncertainty, footnote, ids, estimates, pairs = self._classify(fields)
        body_lower = (fetched.body or "")[:_MAX_HEADER_BYTES].lower()
        vocab_hits = [v for v in self._vocab if v in body_lower]
        obs = {
            "read_from": how,
            "n_fields": len(fields),
            "uncertainty_fields": uncertainty,
            "footnote_fields": footnote,
            "id_fields": ids,
            "candidate_estimate_fields": estimates,
            "paired": [{"uncertainty": a, "estimate": b} for a, b in pairs],
            "unpaired_estimate_fields": [e for e in estimates if e not in {b for _, b in pairs}],
            "footnote_vocabulary_hits": vocab_hits,
            "heuristic": "field-name patterns from harness.toml [g1]; values not inspected",
        }
        if not fields:
            if vocab_hits:
                return Score.PARTIAL, (f"no readable field header ({how}); uncertainty mentioned only in "
                                       f"body text: {', '.join(vocab_hits)}"), obs
            return Score.FAIL, f"no readable field header ({how}) and no uncertainty vocabulary", obs
        if uncertainty:
            conventioned = [u for u in uncertainty if u["pairs_with"] is not None]
            if conventioned:
                paired_est = {b for _, b in pairs}
                coverage_pool = [e for e in estimates if re.search(r"_E$", e)] or estimates
                unpaired = [e for e in coverage_pool if e not in paired_est]
                if pairs and not unpaired:
                    return Score.PASS, (f"{len(pairs)} estimate field(s) carry a paired uncertainty field "
                                        f"({', '.join(sorted({u['pattern_id'] for u in conventioned}))})"), obs
                if pairs:
                    return Score.PARTIAL, (f"{len(pairs)} paired, {len(unpaired)} estimate field(s) without "
                                           f"an uncertainty companion"), obs
            classes = sorted({u["class"] for u in uncertainty})
            if estimates:
                # Unconventioned names: one uncertainty field per estimate field is the
                # bar for PASS; fewer is PARTIAL (present for some).
                if len(uncertainty) >= len(estimates):
                    return Score.PASS, (f"{len(uncertainty)} uncertainty field(s) ({', '.join(classes)}) "
                                        f"beside {len(estimates)} estimate field(s)"), obs
                return Score.PARTIAL, (f"{len(uncertainty)} uncertainty field(s) ({', '.join(classes)}) "
                                       f"for {len(estimates)} estimate field(s)"), obs
            return Score.PARTIAL, (f"uncertainty field(s) present ({', '.join(classes)}) but no "
                                   f"estimate field to pair them with"), obs
        if footnote and vocab_hits:
            return Score.PARTIAL, (f"uncertainty only in a notes/footnote column ({', '.join(footnote)}): "
                                   f"{', '.join(vocab_hits)}"), obs
        if vocab_hits:
            return Score.PARTIAL, f"uncertainty mentioned in body text only: {', '.join(vocab_hits)}", obs
        return Score.FAIL, f"no uncertainty field among {len(fields)} field(s) and no footnote mention", obs


__all__ = ["G1DeclaredProbe", "header_fields"]
