"""Evidence capture — write the raw artifact behind each score to disk.

A score is auditable, never asserted (CC task standing principle): the reviewer
opens the evidence file the score points at and confirms the verdict by eye,
without re-running the harness. Files are organized per agency so one agency's
evidence forms a browsable bundle.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

# Keep filenames readable but filesystem-safe: keep word chars, dot, dash; collapse
# everything else. A short hash of the full target disambiguates collisions.
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _slug(text: str, max_len: int = 60) -> str:
    cleaned = _UNSAFE.sub("-", text).strip("-")
    return cleaned[:max_len] if cleaned else "x"


# Default per-file evidence cap (bytes) when none is configured.
_DEFAULT_MAX_BYTES = 524288


class EvidenceStore:
    def __init__(self, root, max_bytes: int = _DEFAULT_MAX_BYTES):
        self.root = Path(root)
        self.max_bytes = max_bytes

    def write(self, agency_id: str, probe_id: str, target: str, content: str) -> str:
        """Write `content` (the raw artifact) and return the file path as a string.

        Content over `max_bytes` is truncated with an explicit marker — the harness
        may hold a large catalog in memory to parse it, but the evidence file stays
        browsable. The marker makes truncation visible (never a silent cut)."""
        agency_dir = self.root / _slug(agency_id)
        agency_dir.mkdir(parents=True, exist_ok=True)
        # Short, stable hash of the full target so distinct targets never collide
        # even after slug truncation.
        digest = hashlib.sha1(target.encode("utf-8")).hexdigest()[:8]
        fname = f"{_slug(probe_id)}__{_slug(target)}__{digest}.txt"
        path = agency_dir / fname
        text = content if content is not None else ""
        if len(text) > self.max_bytes:
            marker = (
                f"\n\n... [EVIDENCE TRUNCATED at {self.max_bytes} chars of "
                f"{len(text)} total — raw response was larger; re-fetch the target "
                f"to see the remainder]"
            )
            text = text[: self.max_bytes] + marker
        path.write_text(text)
        return str(path)
