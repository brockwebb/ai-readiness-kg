"""The shared source scanner reads code, not prose.

`cc_tasks/2026-09-10_harness_small.md` decision 4. Four source-scanning checks in this repo
have matched a comment, a docstring or a string literal and reported it as a finding; this is
the helper they all use now, and this is the test that plants the needle in each of those three
places and asserts silence, then plants it in code and asserts a hit.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from support.sourcescan import scan, strip_prose                  # noqa: E402

NEEDLE = "tld" + "extract"


def test_a_needle_in_prose_is_not_a_match(tmp_path):
    """Comment, docstring and string literal: three ways to write about a thing without using
    it, and each one has produced a false finding in this repo."""
    (tmp_path / "in_a_comment.py").write_text(
        f"import os  # we retired {NEEDLE} in DD-063\n", encoding="utf-8")
    (tmp_path / "in_a_docstring.py").write_text(
        f'"""This module no longer needs {NEEDLE}."""\nimport os\n', encoding="utf-8")
    (tmp_path / "in_a_string.py").write_text(
        f'MESSAGE = "the {NEEDLE} dependency is gone"\n', encoding="utf-8")
    assert scan([tmp_path], [NEEDLE]) == []


def test_a_needle_in_code_is_a_match(tmp_path):
    """And the scanner must still find the thing, or it is silent for the wrong reason."""
    (tmp_path / "imports_it.py").write_text(f"import {NEEDLE}\n", encoding="utf-8")
    (tmp_path / "calls_it.py").write_text(
        f"import x\nv = x.{NEEDLE}.extract('http://a.test')\n", encoding="utf-8")
    hits = {Path(h[0]).name for h in scan([tmp_path], [NEEDLE])}
    assert hits == {"imports_it.py", "calls_it.py"}, hits


def test_stripping_preserves_line_numbers():
    """A finding that cannot be located is a finding nobody acts on."""
    src = '# a\n"""b"""\nx = 1\ny = "c"\nz = 2\n'
    out = strip_prose(src)
    assert len(out.splitlines()) == len(src.splitlines())
    assert "x = 1" in out.splitlines()[2] and "z = 2" in out.splitlines()[4]


def test_a_file_that_does_not_tokenise_is_returned_unchanged(tmp_path):
    """Returning nothing would make every check pass on a file nobody can parse, which is the
    wrong direction for a guard."""
    broken = "def f(:\n    pass\n"
    assert strip_prose(broken) == broken


def test_the_suffix_list_check_uses_the_shared_helper():
    """Decision 4 says every source-scanning check uses one helper. Asserted over source so a
    fifth check cannot be written with its own text search."""
    src = (REPO / "tests" / "test_manners_robots_first.py").read_text(encoding="utf-8")
    assert "sourcescan" in src, (
        "the suffix-list retirement check does not use the shared scanner")


def test_a_check_whose_needle_is_quoted_data_keeps_its_literals():
    """`literals=False`: comments and docstrings still go, string literals stay.

    Decision 4 prescribed blanking string literals, and that is right for a check whose needle
    is a NAME — `tldextract`, `time.sleep`. It is wrong for the self-licensing lint, whose
    needle is a subscript KEY: `os.environ["AIRKG_SCAN_CYCLE"] = "1"` is the offence itself, and
    a scanner that blanks it sees a clean file. So the switch exists, with one caller, and this
    test pins both sides of it — the prose still goes, the data does not.
    """
    needle = "AIRKG" + "_SCAN_CYCLE"
    src = (f'"""A docstring naming {needle}."""\n'
           f'import os\n'
           f'# a comment naming {needle}\n'
           f'os.environ["{needle}"] = "1"\n')
    kept = strip_prose(src, literals=False)
    assert kept.count(needle) == 1, "exactly the granting line should survive"
    assert needle in kept.splitlines()[3]
    assert needle not in strip_prose(src), "the default still blanks the key"
