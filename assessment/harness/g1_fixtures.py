"""Proposition fixtures for the G1 EVAL family (design D1).

A proposition is one published estimate plus its qualifier set, cited to an ADMITTED
document by `source_doc_id`, with a verbatim `grounding_span` and the verbatim
`context_passage` that is supplied to the consumer in place of retrieval (design D4).
The unit of analysis is the proposition / atomic claim (FActScore, Min 2023; Du 2026) —
not the document, not the number alone (memo §4.1).

Fixture files: `assessment/tests/fixtures/g1/propositions.yaml` (development set — the
parser was built against it) and `propositions_holdout.yaml` (held out for the pilot).
YAML needs pyyaml, which the root project already requires; the public probe families
stay stdlib-only, and this loader imports yaml lazily so importing the harness does not.

Validation is loud (standard 4): unknown qualifier classes, missing producer rules,
missing spans, or a grounding span that is not verbatim inside its own context passage
fail at load. Grounding against the SOURCE DOCUMENT itself (invariant 3) is a test in
`tests/test_g1_fixtures.py`, because the corpus binaries are local-only.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .records import QualifierClass

_HYPHEN_LINEBREAK = re.compile(r"-\s*\n\s*")
_WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """The grounding normalisation of kg/extraction/grounding.py, reproduced here so the
    loader has no cross-package import: NFKC, de-hyphenate line breaks, collapse whitespace.
    Case-preserving. tests/test_g1_fixtures.py asserts the two agree."""
    text = unicodedata.normalize("NFKC", text)
    text = _HYPHEN_LINEBREAK.sub("", text)
    text = _WHITESPACE.sub(" ", text)
    return text.strip()


def is_grounded(span: str, source_text: str) -> bool:
    if not span or not span.strip():
        return False
    return normalize(span) in normalize(source_text)


# The closed surface-type vocabulary (task 2026-09-03_g1_eval_v2 step 2, skeleton G1 note).
SURFACE_TYPES = ("table_coded", "table_labeled", "footnoted", "flagged_cell", "no_declared", "prose_labeled")


class FixtureError(ValueError):
    """A fixture that does not meet the D1 schema. Names the proposition."""


@dataclass(frozen=True)
class Qualifier:
    cls: QualifierClass
    fields: dict            # class-specific: value/text/unit/scale/level/lower/upper/… (see D1)

    @property
    def value(self) -> Optional[float]:
        v = self.fields.get("value")
        return None if v is None else float(v)

    @property
    def text(self) -> Optional[str]:
        return self.fields.get("text")

    @property
    def unit(self) -> Optional[str]:
        return self.fields.get("unit")

    @property
    def scale(self) -> float:
        return float(self.fields.get("scale", 1))

    @property
    def level(self) -> Optional[float]:
        lv = self.fields.get("level")
        return None if lv is None else float(lv)


@dataclass(frozen=True)
class Proposition:
    id: str
    source_doc_id: str
    passage_id: str
    grounding_span: str
    context_passage: str
    estimate: dict          # value, text, unit, label, scale?
    qualifiers: Tuple[Qualifier, ...]
    producer_rule: str
    vintage: Optional[dict] = None
    notes: str = ""
    # v2 (task 2026-09-03_g1_eval_v2 step 2): the product surface the passage was cut from.
    # `prose_labeled` for the v1 handbook stratum (the default when a v1 file carries none).
    surface_type: str = "prose_labeled"
    surface_file: Optional[str] = None
    # footnoted surfaces: characters between the body span and the qualifier's span in the
    # captured surface text (D11 covariate, never scored).
    footnote_distance_chars: Optional[int] = None
    # table_coded: code -> meaning from the surface's own metadata endpoint; fixture
    # metadata only, never rendered into a prompt.
    code_map: Optional[dict] = None
    # flagged_cell: whether the flag legend is part of the passage the consumer sees.
    legend_on_surface: Optional[bool] = None
    # the row / sentence the estimate sits in (D10 binding window anchor)
    binding: Optional[dict] = None
    # v1 propositions re-split by passage in v2 keep where they came from
    split_origin: Optional[str] = None

    @property
    def estimate_value(self) -> float:
        return float(self.estimate["value"])

    @property
    def estimate_text(self) -> str:
        return str(self.estimate["text"])

    @property
    def estimate_scale(self) -> float:
        return float(self.estimate.get("scale", 1))

    @property
    def estimate_label(self) -> str:
        return str(self.estimate["label"])

    def qualifiers_of(self, cls: QualifierClass) -> List[Qualifier]:
        return [q for q in self.qualifiers if q.cls is cls]


@dataclass
class FixtureSet:
    path: str
    propositions: List[Proposition]
    passages: Dict[str, str] = field(default_factory=dict)
    empty_classes: Dict[str, str] = field(default_factory=dict)   # class -> recorded reason
    # v2: per-passage metadata — surface_type, surface files, verbatim `parts` (each a
    # contiguous block of one captured file; the passage is the parts joined by a newline),
    # legend_on_surface, declared_leg_score (filled by the declared-leg run, step 3).
    passage_meta: Dict[str, dict] = field(default_factory=dict)
    fixture_version: str = ""

    def by_id(self, pid: str) -> Proposition:
        for p in self.propositions:
            if p.id == pid:
                return p
        raise KeyError(pid)

    def by_passage(self, passage_id: str) -> List[Proposition]:
        return [p for p in self.propositions if p.passage_id == passage_id]

    def counts_by_class(self) -> Dict[str, int]:
        out = {c.value: 0 for c in QualifierClass}
        for p in self.propositions:
            for q in p.qualifiers:
                out[q.cls.value] += 1
        return out

    def counts_by_surface(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for p in self.propositions:
            out[p.surface_type] = out.get(p.surface_type, 0) + 1
        return out

    def passage_ids(self) -> List[str]:
        seen: List[str] = []
        for p in self.propositions:
            if p.passage_id not in seen:
                seen.append(p.passage_id)
        return seen


_REQUIRED_ESTIMATE = ("value", "text", "unit", "label")
_CLASS_REQUIRED = {
    QualifierClass.MOE: ("value", "text", "unit"),
    QualifierClass.CI: ("level", "form"),
    QualifierClass.SE: ("value", "text", "unit"),
    QualifierClass.CV: ("value", "text", "unit"),
    QualifierClass.RELIABILITY_FLAG: ("text", "polarity"),
    QualifierClass.SUPPRESSION: ("text",),
    QualifierClass.DP_NOISE: ("parameter", "value", "text"),
    QualifierClass.VINTAGE: ("as_of",),
}


def _load_yaml(path: Path):
    try:
        import yaml  # noqa: WPS433 — lazy: the public probe families stay stdlib-only
    except ImportError as exc:  # pragma: no cover
        raise FixtureError("pyyaml is required to load G1 fixtures (pip install pyyaml)") from exc
    with Path(path).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_fixture_set(path) -> FixtureSet:
    path = Path(path)
    doc = _load_yaml(path)
    if not isinstance(doc, dict) or "propositions" not in doc or "passages" not in doc:
        raise FixtureError(f"{path}: expected top-level keys 'passages' and 'propositions'")
    passages = doc["passages"] or {}
    if not isinstance(passages, dict):
        raise FixtureError(f"{path}: 'passages' must be a mapping id -> verbatim text")
    empty = doc.get("empty_classes") or {}
    meta = doc.get("passage_meta") or {}
    if not isinstance(meta, dict):
        raise FixtureError(f"{path}: 'passage_meta' must be a mapping passage id -> metadata")
    for pid_, m in meta.items():
        if pid_ not in passages:
            raise FixtureError(f"{path}: passage_meta names unknown passage {pid_!r}")
        parts = m.get("parts")
        if parts:
            # every part is verbatim inside the passage text, and their join IS the passage
            for part in parts:
                if not is_grounded(part["text"], passages[pid_]):
                    raise FixtureError(f"{path}: passage {pid_!r} part from {part.get('doc_id')} is not verbatim in the passage")
            if normalize("\n".join(part["text"] for part in parts)) != normalize(passages[pid_]):
                raise FixtureError(f"{path}: passage {pid_!r} is not the newline-join of its parts")
    fixture_version = ""
    first = path.read_text(encoding="utf-8").splitlines()[0] if path.exists() else ""
    if first.startswith("# fixture_version:"):
        fixture_version = first.split(":", 1)[1].strip()
    props: List[Proposition] = []
    seen = set()
    for raw in doc["propositions"] or []:
        pid = raw.get("id")
        if not pid or pid in seen:
            raise FixtureError(f"{path}: missing or duplicate proposition id {pid!r}")
        seen.add(pid)
        for key in ("source_doc_id", "passage", "grounding_span", "estimate", "qualifiers", "producer_rule"):
            if key not in raw or raw[key] in (None, "", []):
                raise FixtureError(f"{pid}: missing required field {key!r}")
        if raw["passage"] not in passages:
            raise FixtureError(f"{pid}: unknown passage id {raw['passage']!r}")
        context = passages[raw["passage"]]
        if not is_grounded(raw["grounding_span"], context):
            raise FixtureError(f"{pid}: grounding_span is not verbatim inside passage {raw['passage']!r}")
        est = raw["estimate"]
        for key in _REQUIRED_ESTIMATE:
            if key not in est:
                raise FixtureError(f"{pid}: estimate missing {key!r}")
        quals = []
        for q in raw["qualifiers"]:
            try:
                cls = QualifierClass(q["class"])
            except (KeyError, ValueError) as exc:
                raise FixtureError(f"{pid}: qualifier class {q.get('class')!r} not in the closed enum") from exc
            for key in _CLASS_REQUIRED[cls]:
                if key not in q:
                    raise FixtureError(f"{pid}: {cls.value} qualifier missing {key!r}")
            quals.append(Qualifier(cls, {k: v for k, v in q.items() if k != "class"}))
        if not quals:
            raise FixtureError(f"{pid}: a proposition carries at least one qualifier")
        pmeta = meta.get(raw["passage"], {})
        surface = raw.get("surface_type") or pmeta.get("surface_type") or "prose_labeled"
        if surface not in SURFACE_TYPES:
            raise FixtureError(f"{pid}: unknown surface_type {surface!r} (not in {SURFACE_TYPES})")
        fd = raw.get("footnote_distance_chars")
        if fd is not None and (not isinstance(fd, int) or fd < 0):
            raise FixtureError(f"{pid}: footnote_distance_chars must be a non-negative integer")
        props.append(Proposition(
            id=pid, source_doc_id=raw["source_doc_id"], passage_id=raw["passage"],
            grounding_span=raw["grounding_span"], context_passage=context, estimate=est,
            qualifiers=tuple(quals), producer_rule=raw["producer_rule"],
            vintage=raw.get("vintage"), notes=raw.get("notes", "") or "",
            surface_type=surface, surface_file=raw.get("surface_file") or pmeta.get("surface_file"),
            footnote_distance_chars=fd, code_map=raw.get("code_map"),
            legend_on_surface=raw.get("legend_on_surface", pmeta.get("legend_on_surface")),
            binding=raw.get("binding"), split_origin=raw.get("split_origin")))
    return FixtureSet(path=str(path), propositions=props, passages=dict(passages),
                      empty_classes={str(k): str(v) for k, v in empty.items()},
                      passage_meta={str(k): dict(v) for k, v in meta.items()}, fixture_version=fixture_version)


__all__ = ["FixtureSet", "Proposition", "Qualifier", "FixtureError", "load_fixture_set",
           "normalize", "is_grounded", "SURFACE_TYPES"]
