"""The independent rater's prompt construction and answer parsing (task
2026-09-03_g1_calibration_rating_agreement, step 1).

What actually has to hold, and why each is worth a test rather than a comment:

* **one record per call.** The whole independence claim collapses if a prompt carries a
  second record — the rater could then infer a distribution and rate to it.
* **nothing from the key.** The scorer's level, the reviewer's verdict, the stratum table and
  the seed must not reach the rater; the blind sheet was built to exclude them and the prompt
  builder must not put them back.
* **a blank answer stays blank.** An unparseable rating must leave the sheet's rule untouched,
  so the agreement script reads it as unlabelled. Writing a level there would invent data.
* **the reviewer's own model is refused.** Independence is a property of the run, not of the
  task file that asked for it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "assessment"))

import g1_calibration_rate as rate  # noqa: E402

SHEET = REPO / "assessment/results/g1_calibration_sheet_2026-09-03.md"

SYNTHETIC = """# G1 EVAL v2 — reviewer calibration sheet (blind)

## Draw

- **Seed:** `20260903`
- **Sample:** 2

| stratum (level × verdict) | population | allocated |
|---|---:|---:|
| L0 × genuine | 18 | 4 |

## What to do

Read the response and decide the level.

**The level scale (D2, verbatim from DD-033):** L4 …; L0 corrupted.

**Question, once per record:** which level?

---

## C001

- **Estimate:** the estimate — **1,234**
- **Qualifier family:** `interval` · **published forms:** MOE = 56
- **Mode:** indirect · **Compression:** none

**Prompt shown to the consumer:**

```text
first prompt
```

**Response:**

```text
first response
```

**C001 — Level (L0 / L1 / L2 / L3 / L4 / U):** ______

**C001 — Note:** ______

---

## C002

- **Estimate:** other — **9**
- **Qualifier family:** `vintage` · **published forms:** VINTAGE = 2015
- **Mode:** direct · **Compression:** (n/a — direct mode)

**Prompt shown to the consumer:**

```text
second prompt
```

**Response:**

```text
second response
```

**C002 — Level (L0 / L1 / L2 / L3 / L4 / U):** ______

**C002 — Note:** ______

---
"""


# ---------------------------------------------------------------------------
# sheet parsing
# ---------------------------------------------------------------------------

def test_instruction_block_is_the_sheets_own_wording_and_stops_before_the_records():
    ins = rate.instruction_block(SYNTHETIC)
    assert ins.startswith("## What to do")
    assert "level scale (D2" in ins and "Question, once per record" in ins
    assert "## C001" not in ins
    assert "Seed" not in ins and "stratum" not in ins        # the draw is not the rater's business


def test_record_blocks_split_per_record_and_drop_the_answer_lines():
    blocks = rate.record_blocks(SYNTHETIC)
    assert [sid for sid, _ in blocks] == ["C001", "C002"]
    first = dict(blocks)["C001"]
    assert "first prompt" in first and "first response" in first
    assert "second prompt" not in first                      # one record per block
    assert "Level (L0" not in first and "______" not in first


def test_a_sheet_in_another_shape_fails_loud():
    with pytest.raises(rate.SheetParseError):
        rate.instruction_block("# no instructions here\n")
    with pytest.raises(rate.SheetParseError):
        rate.record_blocks("## What to do\n\nstuff\n\n---\n\nno records\n")


# ---------------------------------------------------------------------------
# the prompt
# ---------------------------------------------------------------------------

def test_prompt_carries_exactly_one_record_and_the_answer_format():
    ins = rate.instruction_block(SYNTHETIC)
    blocks = dict(rate.record_blocks(SYNTHETIC))
    p = rate.build_prompt(ins, "C001", blocks["C001"])
    assert "first prompt" in p and "first response" in p
    assert "second prompt" not in p and "C002" not in p
    assert p.rstrip().endswith("NOTE: <one short sentence; write none if the record is clean>")


def test_prompt_leaks_nothing_from_the_key_on_the_real_sheet():
    """The blind sheet is the only input; if a prompt ever carried a verdict or a level the
    calibration would be measuring the reviewer against itself."""
    text = SHEET.read_text(encoding="utf-8")
    ins = rate.instruction_block(text)
    blocks = rate.record_blocks(text)
    assert len(blocks) == 60
    forbidden = ("claude-opus-5", "claude-haiku", "genuine_loss", "parser_miss", "review_note",
                 "surface_type", "not_in_queue", "Seed:", "allocated")
    for sid, block in blocks:
        p = rate.build_prompt(ins, sid, block)
        for tok in forbidden:
            assert tok not in p, f"{sid} prompt carries {tok!r}"
        # exactly one record heading
        assert p.count("\n## C") == 1


# ---------------------------------------------------------------------------
# answers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text,level,note", [
    ("LEVEL: L4\nNOTE: none", "L4", "none"),
    ("LEVEL: L0\nNOTE: the value is outside the published rounding", "L0",
     "the value is outside the published rounding"),
    ("level: l2\nnote: verbal only", "L2", "verbal only"),
    ("LEVEL: **L3**\nNOTE: converted from bounds", "L3", "converted from bounds"),
    ("LEVEL: U\nNOTE: cannot classify", "U", "cannot classify"),
    ("LEVEL: L1", "L1", ""),                       # a missing NOTE is still a usable rating
])
def test_parse_answer_accepts_the_shapes_a_model_actually_emits(text, level, note):
    assert rate.parse_answer(text) == (level, note)


@pytest.mark.parametrize("text", ["", "I think it is probably fine.", "LEVEL: L7\nNOTE: x",
                                  "The level is L3.", None])
def test_parse_answer_refuses_anything_else(text):
    assert rate.parse_answer(text) == (None, None)


def test_note_is_collapsed_to_one_line():
    level, note = rate.parse_answer("LEVEL: L2\nNOTE: a note\nthat wrapped\n  across lines")
    assert level == "L2" and note == "a note that wrapped across lines"


# ---------------------------------------------------------------------------
# filling the sheet
# ---------------------------------------------------------------------------

def test_fill_sheet_writes_levels_and_leaves_unrated_records_blank():
    answers = {"C001": {"level": "L4", "note": "clean"}, "C002": {"level": None, "note": None}}
    out = rate.fill_sheet(SYNTHETIC, answers, "claude-fable-5-1", "run-1")
    assert "**C001 — Level (L0 / L1 / L2 / L3 / L4 / U):** L4" in out
    assert "**C001 — Note:** clean" in out
    assert "**C002 — Level (L0 / L1 / L2 / L3 / L4 / U):** ______" in out    # blank, not invented
    assert "RATED" in out and "claude-fable-5-1" in out and "1 of 2 records answered" in out


def test_filled_sheet_is_readable_by_the_agreement_script():
    """The filled sheet is the agreement script's input; the two must agree on the format."""
    import g1_calibration_agreement as agreement
    answers = {"C001": {"level": "L4", "note": "clean"}, "C002": {"level": "U", "note": "unclear"}}
    out = rate.fill_sheet(SYNTHETIC, answers, "claude-fable-5-1", "run-1")
    p = Path(__import__("tempfile").mkdtemp()) / "filled.md"
    p.write_text(out, encoding="utf-8")
    got = agreement.read_sheet(p)
    assert got["C001"]["level"] == "L4" and got["C002"]["level"] == "U"


# ---------------------------------------------------------------------------
# independence
# ---------------------------------------------------------------------------

def test_the_reviewers_own_model_is_refused_as_rater():
    with pytest.raises(SystemExit) as e:
        rate.main(["--model", rate.REVIEWER_MODEL, "--ceiling-tokens", "1000"])
    assert "independent" in str(e.value)


def test_reviewer_model_constant_matches_the_pinned_consumer():
    """If the pinned consumer ever changes, this refusal has to move with it."""
    import tomllib
    with (REPO / "assessment/config/g1_consumer.toml").open("rb") as fh:
        assert tomllib.load(fh)["consumer"]["model_id"] == rate.REVIEWER_MODEL
