"""In-page JSON-LD: reading schema.org Dataset / DataCatalog markup off an HTML page.

An HTML product page is not in `data.json`, so the catalog metadata probes have
nothing to read for it. Where a page self-describes with schema.org JSON-LD, that
markup IS the machine-readable metadata for that surface. Normalizing it to the
DCAT-US field names `data.json` already uses lets one probe score both surfaces
without a second scoring rule, which keeps the rubric single-valued: D3
metadata_standard asks the same question of a catalog record and of a page.

The normalization is a rename, never an upgrade. A field absent from the JSON-LD
stays absent in the record, so a page with thin markup scores as thin markup.

stdlib only: `html.parser` to find `<script type="application/ld+json">` blocks
(HTMLParser puts script content in CDATA mode, so the JSON arrives unescaped),
`json` to parse them.
"""
from __future__ import annotations

import json
from html.parser import HTMLParser
from typing import List, Tuple

# schema.org types that carry dataset-level descriptive metadata.
DATASET_TYPES = ("dataset",)
CATALOG_TYPES = ("datacatalog",)

# Depth guard for @graph nesting: real markup nests one or two levels; anything
# deeper is either pathological or hostile, and is not worth walking.
_MAX_GRAPH_DEPTH = 4


class _LdJsonCollector(HTMLParser):
    """Collect the raw text of every `<script type="application/ld+json">`."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: List[str] = []
        self._buf: List[str] = []
        self._in_ld = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "script":
            return
        attr = {k.lower(): (v or "") for k, v in attrs}
        if "application/ld+json" in attr.get("type", "").lower():
            self._in_ld = True
            self._buf = []

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self._in_ld:
            self.blocks.append("".join(self._buf))
            self._in_ld = False
            self._buf = []

    def handle_data(self, data):
        if self._in_ld:
            self._buf.append(data)


def extract_jsonld_blocks(html: str) -> Tuple[List[object], int]:
    """Return `(parsed blocks, parse_failure_count)`.

    A block that is not valid JSON is counted, not raised: malformed markup on
    one page must not stop the run, and the count is reportable evidence.
    """
    parser = _LdJsonCollector()
    try:
        parser.feed(html or "")
        parser.close()
    except Exception:  # pragma: no cover - HTMLParser is lenient by design
        pass
    parsed: List[object] = []
    failures = 0
    for raw in parser.blocks:
        text = raw.strip()
        if not text:
            continue
        try:
            parsed.append(json.loads(text))
        except (json.JSONDecodeError, ValueError):
            failures += 1
    return parsed, failures


def _local_types(node: dict) -> List[str]:
    """Lowercased local names of a node's `@type`, with any URI prefix stripped."""
    raw = node.get("@type") or node.get("type") or []
    values = raw if isinstance(raw, list) else [raw]
    out = []
    for v in values:
        if not isinstance(v, str):
            continue
        local = v.rstrip("/").split("/")[-1].split("#")[-1].split(":")[-1]
        out.append(local.strip().lower())
    return out


def flatten_nodes(blocks: List[object], _depth: int = 0) -> List[dict]:
    """Every JSON-LD node in a set of blocks, walking lists and `@graph`."""
    nodes: List[dict] = []
    if _depth > _MAX_GRAPH_DEPTH:
        return nodes
    for block in blocks:
        if isinstance(block, list):
            nodes.extend(flatten_nodes(block, _depth + 1))
        elif isinstance(block, dict):
            nodes.append(block)
            graph = block.get("@graph")
            if isinstance(graph, (list, dict)):
                nodes.extend(flatten_nodes(
                    graph if isinstance(graph, list) else [graph], _depth + 1))
    return nodes


def dataset_nodes(html: str) -> List[dict]:
    """Nodes typed schema.org Dataset or DataCatalog, in document order."""
    blocks, _ = extract_jsonld_blocks(html)
    wanted = DATASET_TYPES + CATALOG_TYPES
    return [n for n in flatten_nodes(blocks)
            if any(t in wanted for t in _local_types(n))]


def has_dataset_markup(nodes: List[dict]) -> bool:
    """True when a page carries a schema.org **Dataset** node specifically.

    Deliberately narrower than `dataset_nodes`: the catalog-completeness signal
    counts pages that describe a dataset, not pages that merely point at a
    catalog.
    """
    return any(t in DATASET_TYPES for n in nodes for t in _local_types(n))


def _as_text(value) -> str:
    """Flatten a schema.org value that may be a string, a node, or a list."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("url", "@id", "name", "identifier"):
            v = value.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return ""
    if isinstance(value, list):
        for item in value:
            text = _as_text(item)
            if text:
                return text
    return ""


def dcat_record_from_nodes(nodes: List[dict]) -> dict:
    """Normalize the best available node to the DCAT-US field names `data.json` uses.

    A Dataset node is preferred over a DataCatalog node: it describes the page's
    own subject, where a DataCatalog describes the collection the page sits in.
    Returns `{}` when no dataset-level node is present, which is what a page with
    no self-description should score as. The record carries one non-DCAT key,
    `_jsonld_types`, so the evidence file names which schema.org type the score
    was read from.
    """
    chosen = None
    for node in nodes:
        types = _local_types(node)
        if any(t in DATASET_TYPES for t in types):
            chosen = node
            break
    if chosen is None:
        for node in nodes:
            if any(t in CATALOG_TYPES for t in _local_types(node)):
                chosen = node
                break
    if chosen is None:
        return {}

    record: dict = {}

    title = _as_text(chosen.get("name"))
    if title:
        record["title"] = title
    description = _as_text(chosen.get("description"))
    if description:
        record["description"] = description

    keywords = chosen.get("keywords")
    if isinstance(keywords, str):
        parsed = [k.strip() for k in keywords.split(",") if k.strip()]
    elif isinstance(keywords, list):
        parsed = [k for k in (_as_text(k) for k in keywords) if k]
    else:
        parsed = []
    if parsed:
        record["keyword"] = parsed

    for source_key in ("publisher", "creator", "provider", "sourceOrganization"):
        publisher = _as_text(chosen.get(source_key))
        if publisher:
            record["publisher"] = {"name": publisher}
            break

    license_value = _as_text(chosen.get("license"))
    if license_value:
        record["license"] = license_value
    # usageInfo / conditionsOfAccess are freeform prose, never a resolvable
    # license, so they map to `rights` and score PARTIAL, matching how DCAT
    # `rights` prose is scored on the catalog side.
    for rights_key in ("usageInfo", "conditionsOfAccess"):
        rights = _as_text(chosen.get(rights_key))
        if rights:
            record["rights"] = rights
            break

    modified = _as_text(chosen.get("dateModified")) or _as_text(chosen.get("datePublished"))
    if modified:
        record["modified"] = modified

    identifier = _as_text(chosen.get("identifier")) or _as_text(chosen.get("url"))
    if identifier:
        record["identifier"] = identifier

    record["_jsonld_types"] = _local_types(chosen)
    return record
