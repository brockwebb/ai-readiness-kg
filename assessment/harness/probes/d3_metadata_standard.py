"""D3 Interpretability — metadata standard (DCAT-US / Project Open Data).

Scores whether a dataset record carries the DCAT-required descriptive fields, so a
machine has standardized metadata rather than ad-hoc prose.

Two surfaces, one scoring rule. On the catalog side the record is a data.json
dataset entry. On a web surface there is no catalog entry, so `evaluate_page`
reads the page's in-page JSON-LD schema.org Dataset / DataCatalog markup and
`harness/jsonld.py` normalizes it to these same field names. A page that
self-describes in JSON-LD is machine-readable metadata by any reasonable reading
of the rubric; a page that does not carries none, and scores accordingly.

PASS    all four anchor fields present (title, description, keyword, and a
        publisher or contactPoint).
PARTIAL some but not all present.
FAIL    essentially none (title only / empty record).
"""
from __future__ import annotations

from ..records import SOURCE_CATALOG, SOURCE_SITEMAP, Score, Track
from .base import MetadataProbe

# DCAT-US required/expected descriptive fields used as the conformance anchors.
_ANCHORS = ("title", "description", "keyword")


class MetadataStandardProbe(MetadataProbe):
    probe_id = "d3_metadata_standard"
    dimension = "D3"
    track = Track.CORE
    # On a web surface the record comes from in-page JSON-LD (see evaluate_page).
    sources = (SOURCE_CATALOG, SOURCE_SITEMAP)

    def evaluate(self, dataset: dict):
        present = [f for f in _ANCHORS if dataset.get(f)]
        has_contact = bool(dataset.get("publisher") or dataset.get("contactPoint"))
        score_count = len(present) + (1 if has_contact else 0)
        if score_count == len(_ANCHORS) + 1:
            return Score.PASS, f"DCAT anchors present: {present} + publisher/contactPoint"
        # Title alone (or nothing) is essentially no machine metadata.
        if score_count <= 1:
            return Score.FAIL, "essentially no DCAT descriptive metadata (title at most)"
        return Score.PARTIAL, (
            f"partial DCAT metadata: {present}"
            f"{' + contact' if has_contact else ''}")
