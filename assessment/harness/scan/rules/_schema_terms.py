"""What the schema.org structured-field rules (B1's schema.org half, B2, B5) share. Pure.

`cc_tasks/2026-09-18_schema_field_rules.md`. Each rule reads the markup A6 already extracts
(`CONSUMES = ("A6",)`): `structured_data.fetch` runs `extruct` over the product page and keeps
the whole extraction on the Observation as `parsed["raw"]`, so a rule can read `DefinedTerm` and
`variableMeasured` from it without a second request and without reading a stored body. Every
A6 Observation on the log since cycle 1 carries `raw`, which is why these rules — unlike the
DCAT-US field rules, which needed a new block on D4's observation — can be exercised on the
cycle of record as it was collected.

This module finds nodes and properties and says nothing: every sentence a Finding carries is
written in the rule module, because the prescription layer anchors on reason fragments checked
against the CURRENT rule module's own source (`scripts/tag_prescriptions.py` `OUTCOMES`).

**Three syntaxes, one reading.** `extruct` with `uniform=True` gives JSON-LD as written (compact,
often under `@context: https://schema.org`, sometimes in an `@graph`), microdata in the same
compact shape, and RDFa EXPANDED — full IRIs for types and properties, values as `{"@value": …}`
or `{"@id": …}`, nodes linked by `@id` rather than nested. A name is read as schema.org's only
when it is bare or carries a schema.org prefix (`local`), so `http://xmlns.com/foaf/0.1/Image`
never reads as `Image`, and a node reached by `@id` is followed within its own syntax.

**The terms the rules read**, each named by a document on disk:

* `DefinedTerm`, `termCode`, `inDefinedTermSet`, `description`, `name` —
  `corpus/kernel/schema-org-definedterm.md` (doc_id `schema-org-definedterm`): "Use the name
  property for the term being defined, use termCode if the term has an alpha-numeric code
  allocated, use description to provide the definition of the term."
* `Dataset`, `variableMeasured`, `measurementTechnique` — `corpus/kernel/schema-org-dataset.md`
  (doc_id `schema-org-dataset`): "The variableMeasured property can indicate (repeated as
  necessary) the variables that are measured in some dataset", and `measurementTechnique`
  expects a `DefinedTerm`.
"""
from __future__ import annotations

from . import _common as c

#: The prefixes under which a type or property name is schema.org's. A bare name is read as
#: schema.org's too, because that is what a compact JSON-LD document under a schema.org
#: `@context` and `extruct`'s uniform microdata both produce.
SCHEMA_PREFIXES = ("http://schema.org/", "https://schema.org/", "schema:")

#: How deep a walk from a `Dataset` follows nested nodes and `@id` references before it stops.
#: A bound, not a threshold: markup is a graph and may contain a cycle, and the terms a rule
#: looks for sit at depth 1 (`measurementTechnique`) or 2 (`variableMeasured` →
#: `measurementTechnique`, `propertyID`) in every example the schema.org pages give.
MAX_DEPTH = 6


def local(name) -> str | None:
    """`termCode` for `termCode`, `schema:termCode` or `http://schema.org/termCode`; None for a
    name in any other vocabulary."""
    if not isinstance(name, str):
        return None
    for p in SCHEMA_PREFIXES:
        if name.startswith(p):
            return name[len(p):]
    if "/" in name or "#" in name or ":" in name:
        return None
    return name


def types_of(node: dict) -> set:
    t = node.get("@type")
    t = t if isinstance(t, list) else [t]
    return {x for x in (local(v) for v in t) if x}


def props(node: dict, name: str) -> list:
    """Every value of the schema.org property `name` on one node, as a flat list."""
    out = []
    for k, v in node.items():
        if k.startswith("@") or local(k) != name:
            continue
        out += v if isinstance(v, list) else [v]
    return [v for v in out if v not in (None, "", [], {})]


def text(v) -> str | None:
    """A value as text: a string, a `{"@value": …}`, or an `{"@id": …}` IRI."""
    if isinstance(v, str):
        return v.strip() or None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return str(v)
    if isinstance(v, dict):
        for k in ("@value", "@id"):
            if isinstance(v.get(k), str) and v[k].strip():
                return v[k].strip()
    return None


def _walk(node, out: list) -> None:
    if isinstance(node, dict):
        if "@type" in node or "@id" in node:
            out.append(node)
        for k, v in node.items():
            if k != "@context":
                _walk(v, out)
    elif isinstance(node, list):
        for v in node:
            _walk(v, out)


def syntax_nodes(raw) -> list:
    """`[(syntax, [node, …])]` — every node of each syntax's extraction, nested ones included."""
    out = []
    for syntax, items in sorted((raw or {}).items()) if isinstance(raw, dict) else []:
        nodes: list = []
        _walk(items, nodes)
        out.append((syntax, nodes))
    return out


def _reachable(start: dict, by_id: dict) -> list:
    """Nodes reachable from `start` through property values, nested or by `@id`, to MAX_DEPTH."""
    seen, out, frontier = {id(start)}, [], [start]
    for _ in range(MAX_DEPTH):
        nxt = []
        for n in frontier:
            for k, v in n.items():
                if k.startswith("@"):
                    continue
                for x in v if isinstance(v, list) else [v]:
                    if not isinstance(x, dict):
                        continue
                    target = x
                    ref = x.get("@id")
                    if set(x) == {"@id"} and isinstance(ref, str) and ref in by_id:
                        target = by_id[ref]
                    if id(target) in seen:
                        continue
                    seen.add(id(target))
                    out.append(target)
                    nxt.append(target)
        frontier = nxt
    return out


def _set_of(term: dict, by_id: dict) -> str | None:
    """The `inDefinedTermSet` a term names, as one identifier: the IRI or URL when there is one,
    else the set's name. The property expects "DefinedTermSet or URL"."""
    for v in props(term, "inDefinedTermSet"):
        if isinstance(v, dict):
            ref = v.get("@id")
            node = by_id.get(ref, v) if isinstance(ref, str) else v
            for key in ("url", "name"):
                for x in props(node, key):
                    if text(x):
                        return text(x)
            if text(v):
                return text(v)
        elif text(v):
            return text(v)
    return None


def read(raw) -> dict:
    """What the product page's markup carries for these rules. Deterministic: lists are sorted.

    * `datasets` — schema.org `Dataset` nodes;
    * `variable_measured` — how many of them carry a non-empty `variableMeasured`;
    * `terms` — every `DefinedTerm`, as `{name, code, set, described, linked}` where `linked`
      means the term is reachable from a `Dataset` node (through `variableMeasured`,
      `measurementTechnique` or any other property path), which is B2's "linked from
      variables" read at the only place markup can express it.
    """
    datasets = variable_measured = 0
    terms = []
    for _syntax, nodes in syntax_nodes(raw):
        by_id = {n["@id"]: n for n in nodes if isinstance(n.get("@id"), str)
                 and set(n) != {"@id"}}
        linked: set = set()
        for n in nodes:
            if "Dataset" in types_of(n):
                datasets += 1
                if props(n, "variableMeasured"):
                    variable_measured += 1
                linked |= {id(x) for x in _reachable(n, by_id)}
        seen_terms: set = set()
        for n in nodes:
            if set(n) == {"@id"} and n["@id"] in by_id:
                continue
            if "DefinedTerm" not in types_of(n) or id(n) in seen_terms:
                continue
            seen_terms.add(id(n))
            name = next((text(v) for v in props(n, "name") if text(v)), None)
            code = next((text(v) for v in props(n, "termCode") if text(v)), None)
            terms.append({"name": name, "code": code, "set": _set_of(n, by_id),
                          "described": any(text(v) for v in props(n, "description")),
                          "linked": id(n) in linked})
    terms.sort(key=lambda t: tuple(str(t[k]) for k in ("name", "code", "set", "described",
                                                         "linked")))
    return {"datasets": datasets, "variable_measured": variable_measured, "terms": terms}


def state(o, params: dict) -> dict:
    """One A6 observation as one of these `kind`s:

    * `blind`         — the page was not observed (`_common.unobserved`);
    * `not_html`      — the surface is not HTML, so it carries no embedded markup (A6's own
                        `not_applicable` reading, for the same reason: it would score the format);
    * `unextracted`   — the page was served and the extraction did not run or failed;
    * `markup`        — `read(raw)` is in `markup`.
    """
    if c.unobserved(o, params):
        return {"kind": "blind"}
    p = o.parsed or {}
    ct = p.get("content_type") or ""
    if ct and not ct.startswith("text/html"):
        return {"kind": "not_html", "content_type": ct}
    if p.get("error") or not isinstance(p.get("raw"), dict):
        return {"kind": "unextracted", "reason": p.get("error") or "no extraction recorded"}
    return {"kind": "markup", "markup": read(p["raw"])}


def concept(name: str | None) -> str | None:
    """The concept a term names, for comparison across products: the name, case-folded, with
    whitespace collapsed. schema.org's own reading — "Use the name property for the term being
    defined" — makes the name the concept and `termCode` within `inDefinedTermSet` its
    identifier, which is the pair B5 compares."""
    if not name:
        return None
    return " ".join(name.split()).casefold() or None
