"""The readiness diagnostic package's data layer and vocabulary (DN-016; task b6c65bfe).

Part B checks: the vocabulary test (no "scan", "probe", "crawl" or "audit" as a word in any
rendered text), the roster row count (frame body count plus flagships), and the rung-two listing
(every row cites a node id or says "to be confirmed"). The rendered products (.docx/.pptx and the
Markdown source) are checked too, when Part D has built them.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import diagnostic_package as D  # noqa: E402


def _rendered_vocab_strings(v: dict) -> list[str]:
    """The vocab's rendered term VALUES (not the forbidden_words list, which is config naming the
    banned words on purpose)."""
    s = [v["run"], v["unit"], v["actor"]]
    st = v["states"]
    s += [st["pass"], st["partial"], st["fail"], st["not_measured"]["label"],
          st["not_measured"]["meaning"], *st["not_measured"]["reasons"]]
    s += [v["rungs"]["rung_one"], v["rungs"]["rung_two"]]
    return s


def test_vocab_block_has_dn016_terms():
    v = D.load_vocab()
    assert v["run"] == "readiness diagnostic"
    assert v["unit"] == "check"
    assert v["actor"] == "public client"
    assert v["states"]["not_measured"]["label"] == "not measured"
    assert len(v["states"]["not_measured"]["reasons"]) == 3
    assert v["forbidden_words"] == ["scan", "probe", "crawl", "audit"]


def test_no_banned_word_in_rendered_dictionary_fields():
    """DN-016 ruling 1: the plain-language fields a product renders carry no banned word. A9's
    instrument plain name carries 'probed'; the diagnostic renders the vocab override instead,
    which this asserts is clean."""
    vocab = D.load_vocab()
    bad = []
    for s in D.instrument_specs():
        texts = [D.rendered_plain_name(s, vocab)] + [str(s.get(f) or "") for f in D.RENDERED_DICT_FIELDS]
        for t in texts:
            for w, ctx in D.banned_hits(t):
                bad.append(f"{s['leg']}: {w!r} in {ctx!r}")
    assert not bad, "banned words in rendered dictionary fields:\n  " + "\n  ".join(bad)


def test_no_banned_word_in_rendered_vocab_strings():
    bad = [f"{w!r} in {ctx!r}" for s in _rendered_vocab_strings(D.load_vocab())
           for w, ctx in D.banned_hits(s)]
    assert not bad, "banned words in vocabulary term strings:\n  " + "\n  ".join(bad)


def test_a9_override_removes_the_forbidden_word():
    a9 = next(s for s in D.instrument_specs() if s["leg"] == "A9")
    assert "probed" in (a9["rf_plain_name"] or "").lower(), "A9's instrument name still has 'probed'"
    assert not D.banned_hits(D.rendered_plain_name(a9)), "the A9 override still trips the vocabulary rule"


def test_roster_row_count_is_frame_bodies_plus_flagships():
    d = D.load_frame()
    rows = D.roster_rows()
    assert len(rows) == d["tier_a_agencies"] + d["tier_c_hosts"]
    assert sum(1 for r in rows if r["flagship"]) == d["tier_c_hosts"]
    assert sum(1 for r in rows if not r["flagship"]) == d["tier_a_agencies"]
    # every row names a body and a host, and carries at least one surface
    for r in rows:
        assert r["body"] and r["host"] and r["surfaces"]


def test_rung_two_rows_each_cite_a_node_or_to_be_confirmed():
    rows = D.rung_two_rows()
    assert rows, "the roster has no key-bearing surfaces; this proves nothing"
    assert not D.rung_two_is_well_formed(rows)
    # the record holds no per-surface key fact today, so each cell is 'to be confirmed' (ruling 3)
    for r in rows:
        assert r["source"] == "to be confirmed" or r["source"].strip()


# ----------------------------------------------------------------- the rendered products (Part D)

def _product_texts() -> list[tuple[str, str]]:
    """(label, text) for each built product, or [] if Part D has not built them yet."""
    try:
        import diagnostic_package_build as B
    except Exception:
        return []
    out = []
    md = REPO / "reports" / "diagnostic" / "READINESS_DIAGNOSTIC.md"
    docx = REPO / "reports" / "diagnostic" / "READINESS_DIAGNOSTIC.docx"
    pptx = REPO / "reports" / "diagnostic" / "READINESS_DIAGNOSTIC.pptx"
    if md.is_file():
        out.append(("markdown", md.read_text(encoding="utf-8")))
    if docx.is_file() and hasattr(B, "docx_text"):
        out.append(("docx", B.docx_text(docx)))
    if pptx.is_file() and hasattr(B, "pptx_text"):
        out.append(("pptx", B.pptx_text(pptx)))
    return out


def test_no_banned_word_in_any_rendered_product():
    products = _product_texts()
    if not products:
        pytest.skip("diagnostic package not built yet (Part D)")
    bad = []
    for label, text in products:
        for w, ctx in D.banned_hits(text):
            bad.append(f"{label}: {w!r} in {ctx!r}")
    assert not bad, "banned words in a rendered product:\n  " + "\n  ".join(bad)
