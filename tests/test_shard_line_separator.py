"""Event shards are JSON Lines: records separated by "\\n" alone, and a reader splits on that.

`cc_tasks/2026-10-07_seed_known_locations_verify.md` (ADDENDUM_01 A): D1 now keeps a terms page
whole, and one of them (BEA's API user guide, a PDF) decoded to text carries U+0085 (NEL), which
RFC 8259 lets a JSON string hold unescaped and which `str.splitlines()` treats as a line break.
The published shard `events/cycle-scan_2026-10-07_seeded.jsonl` holds 56 of them; the readers that
used `splitlines()` (`build_l0_site.release_date` among them) read fragments of a record as
records. jsonlines.org: "the line separator is '\\n'".
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_every_shard_is_json_lines_split_on_newline_alone():
    for shard in sorted((REPO / "events").glob("*.jsonl")):
        for i, line in enumerate(shard.read_text(encoding="utf-8").split("\n"), 1):
            if line.strip():
                json.loads(line)


def test_the_seeded_shard_is_the_case_splitlines_gets_wrong():
    text = (REPO / "events" / "cycle-scan_2026-10-07_seeded.jsonl").read_text(encoding="utf-8")
    by_newline = [l for l in text.split("\n") if l.strip()]
    assert "\x85" in text
    assert len(text.splitlines()) > len(by_newline), "the guard has lost its incident"
