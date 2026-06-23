"""Target enumeration — mechanical first-pass extraction of candidate public
data-asset endpoints from an agency's machine-readable catalog.

Parses Project Open Data / DCAT-US `data.json`: each dataset's distributions
become candidate targets. An agency with no machine-readable catalog is itself a
D1 (Discovery) finding — recorded as `has_machine_readable_catalog = False`, never
raised as an error (the harness must keep going and report the absence).

Pure parsing: the fetch of the catalog content happens elsewhere; this takes the
already-retrieved string so it is fully testable from fixtures.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List
from urllib.parse import urljoin


@dataclass
class CatalogResult:
    has_machine_readable_catalog: bool
    targets: List[dict] = field(default_factory=list)
    note: str = ""


def _absolutize(url: str, base_url: str) -> str:
    if url.startswith(("http://", "https://")):
        return url
    return urljoin(base_url.rstrip("/") + "/", url.lstrip("/"))


def parse_catalog(content: str, base_url: str) -> CatalogResult:
    """Extract candidate endpoints from data.json content. Returns a CatalogResult
    flagging whether a machine-readable catalog was present at all."""
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        return CatalogResult(
            has_machine_readable_catalog=False,
            note="catalog content is not valid JSON — no machine-readable catalog "
            "(D1 Discovery finding)",
        )

    if not isinstance(data, dict) or "dataset" not in data:
        return CatalogResult(
            has_machine_readable_catalog=False,
            note="JSON present but no Project Open Data / DCAT 'dataset' array — "
            "not a recognized machine-readable catalog (D1 Discovery finding)",
        )

    datasets = data.get("dataset") or []
    targets: List[dict] = []
    for ds in datasets:
        if not isinstance(ds, dict):
            continue
        title = ds.get("title", "")
        modified = ds.get("modified", "")
        for dist in ds.get("distribution", []) or []:
            if not isinstance(dist, dict):
                continue
            # DCAT distributions use downloadURL (direct file) or accessURL (service).
            url = dist.get("downloadURL") or dist.get("accessURL")
            if not url:
                continue
            targets.append(
                {
                    "url": _absolutize(url, base_url),
                    "media_type": dist.get("mediaType", ""),
                    "dataset_title": title,
                    "dataset_modified": modified,
                    "source": "data.json",
                }
            )

    return CatalogResult(
        has_machine_readable_catalog=True,
        targets=targets,
        note=f"parsed {len(datasets)} datasets -> {len(targets)} candidate endpoints",
    )
