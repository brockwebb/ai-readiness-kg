"""Result-token resolution for the G1 findings memo, the deck draft and the skeleton.

`scripts/g1_resolve_results.py` became a SHIM over seldon's resolver library on 2026-09-04
(task `cc_tasks/2026-09-04_result_migration_completion.md` step 1). The old body replayed
`seldon_events.jsonl` and matched a token key against the `units` property; the index is now
the graph, through `seldon.paper.build`. So the three tests that pinned the event-log replay
are gone — they described machinery that no longer exists, and keeping them would have meant
keeping the machinery.

What replaces them are tests of the CONTRACT the entry point owes its callers, which is what
a shim has to preserve and what a library swap can silently break:

* an unresolved token is never replaced by a plausible number;
* an ambiguous name is never resolved to whichever row was seen last;
* a count renders as "26", not "26.0" — the library's `str(value)` on a float would rewrite
  every count in three documents;
* no `(proposed)` marker leaks into documents that have always rendered bare numbers, even
  though every Result here is `proposed` and the call passes `allow_proposed=True`;
* the documentation placeholder `{{result:<NAME>:value}}` is not a token — the two documents
  that explain the syntax in prose depend on that. Seldon's own pattern used to match it
  (registered upstream as seldon ResearchTask `3376805b`); as of seldon `fa7d113`, 2026-09-04,
  it does not, so the pre-filter is redundant rather than load-bearing and the control below
  pins the agreement instead of the divergence.

The index-loading tests inject a fake index rather than standing up Neo4j, so the suite stays
runnable without a database; the one test that does touch the real graph is the end-to-end
guard on the committed memo, which is the assertion that actually protects the documents.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import g1_resolve_results as res  # noqa: E402


def _index(**names):
    """A resolver index of the shape load_results() returns."""
    out = {}
    for name, value in names.items():
        out[name] = {"artifact_id": f"id-{name}", "name": name, "value": value,
                     "state": "proposed", "via_units_fallback": False}
    return out


# ---------------------------------------------------------------------------
# the token grammar
# ---------------------------------------------------------------------------

def test_the_placeholder_is_not_a_token_but_a_real_name_is():
    """`{{result:<NAME>:value}}` appears in the memo header and in DD-036 while explaining
    the syntax. Seldon's REFERENCE_PATTERN matches it; this shim's must not."""
    assert res.TOKEN_RE.findall("{{result:<NAME>:value}}") == []
    assert res.TOKEN_RE.findall("{{result:g1_a-b.c:value}}") == [("g1_a-b.c", "value")]


def test_the_library_adopted_a_name_grammar_so_the_pre_filter_is_redundant():
    """This test was written as a positive control that FAILED on the day seldon tightened
    `REFERENCE_PATTERN`, saying in its own docstring that the pre-filter could then go. It
    fired: seldon `fa7d113` (2026-09-04) rebuilt the pattern on `unanchored_name_grammar()`,
    which is the upstream ResearchTask `3376805b` this shim registered. So the control is
    inverted rather than deleted — it now pins the *agreement*, and it is the thing that must
    keep holding for the pre-filter to stay removable.

    The pre-filter itself is NOT removed here: `resolve_text` reports errors and substitutes
    through `TOKEN_RE`, so retiring it is a rewrite of that function's error paths and belongs
    to the resolver-migration task, not to an extraction task that merely has to keep the
    suite honest."""
    sys.path.insert(0, "/Users/brock/GitHub/seldon")
    from seldon.paper.build import REFERENCE_PATTERN
    # The placeholder both documents carry in prose: neither grammar accepts it any more.
    assert REFERENCE_PATTERN.findall("{{result:<NAME>:value}}") == []
    assert res.TOKEN_RE.findall("{{result:<NAME>:value}}") == []
    # A real name: both accept it, which is what makes the pre-filter redundant and not load-bearing.
    assert REFERENCE_PATTERN.findall("{{result:g1_a-b.c:value}}") == [("result", "g1_a-b.c", "value")]
    assert res.TOKEN_RE.findall("{{result:g1_a-b.c:value}}") == [("g1_a-b.c", "value")]


# ---------------------------------------------------------------------------
# the rendering contract
# ---------------------------------------------------------------------------

def test_integral_values_render_without_a_trailing_zero():
    """Every Result was registered through --value FLOAT, so the graph holds 26.0 and the
    library's str(value) would write '26.0' into a sentence that reads '26'."""
    out, errors = res.resolve_text(
        "{{result:g1_n:value}} records at {{result:g1_r:value}}",
        _index(g1_n=26.0, g1_r=0.5457), "f.md")
    assert out == "26 records at 0.5457"
    assert errors == []


def test_no_proposed_marker_leaks_into_a_document():
    """allow_proposed=True is right — a proposed Result IS the referent here — but the
    library also stamps '(proposed)' into the text, and these documents render bare numbers."""
    out, errors = res.resolve_text("{{result:g1_r:value}}", _index(g1_r=0.392), "f.md")
    assert out == "0.392"
    assert "(proposed)" not in out
    assert errors == []


def test_a_string_value_survives_unchanged():
    out, _ = res.resolve_text("{{result:g1_s:value}}", _index(g1_s="PASS"), "f.md")
    assert out == "PASS"


# ---------------------------------------------------------------------------
# failure behaviour
# ---------------------------------------------------------------------------

def test_unknown_name_and_unknown_field_leave_the_token_and_report():
    out, errors = res.resolve_text(
        "{{result:g1_missing:value}} {{result:g1_n:median}}", _index(g1_n=26.0), "f.md")
    assert "{{result:g1_missing:value}}" in out          # never silently replaced
    assert "{{result:g1_n:median}}" in out
    assert len(errors) == 2
    assert "no registered Result named" in errors[0] and "has no field" in errors[1]


def test_an_ambiguous_name_is_reported_not_guessed():
    idx = {"count": {"ambiguous": ["id-a", "id-b"], "units": "count"}}
    out, errors = res.resolve_text("{{result:count:value}}", idx, "f.md")
    assert out == "{{result:count:value}}"
    assert len(errors) == 1 and "more than once" in errors[0]


def test_error_lines_name_the_line_number():
    _, errors = res.resolve_text("line one\nline two\n{{result:nope:value}}\n", {}, "memo.md")
    assert errors[0].startswith("memo.md:3:")


# ---------------------------------------------------------------------------
# the SI-09 transitional fallback
# ---------------------------------------------------------------------------

def test_fallback_tokens_names_only_the_rows_resolved_by_units():
    idx = _index(named_one=1.0)
    idx["unnamed_one"] = {"artifact_id": "id-x", "units": "unnamed_one", "value": 2.0,
                          "state": "proposed", "via_units_fallback": True}
    text = "{{result:named_one:value}} {{result:unnamed_one:value}}"
    assert res.fallback_tokens(text, idx) == ["unnamed_one"]
    out, errors = res.resolve_text(text, idx, "f.md")
    assert out == "1 2" and errors == []          # a fallback resolution is not an error


# ---------------------------------------------------------------------------
# end to end, against the real graph
# ---------------------------------------------------------------------------

def test_the_real_memo_resolves_end_to_end():
    """The guard that actually protects the documents: every token in the committed memo
    resolves through the shim, against the live graph."""
    memo = REPO / "docs/research/2026-09-03_g1_eval_findings.md"
    results = res.load_results()
    text = memo.read_text(encoding="utf-8")
    _, errors = res.resolve_text(text, results, str(memo))
    assert errors == [], errors
    assert len(res.TOKEN_RE.findall(text)) > 100
