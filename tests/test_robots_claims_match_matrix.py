"""No shown surface says a body publishes a `robots.txt` this instrument never read.

`cc_tasks/2026-10-06_l0_report_robots_wording.md` decision 5, closing audit C-02
(`docs/audit/2026-10-04_full_audit.md`). The L0 report said BLS, BTS and SSA each "publishes a
`robots.txt` that grants access", and that the scanner "obeys the `robots.txt` those same hosts
publish". Every one of the 42 reads of those three files answered HTTP 403; their A4 cells read
`error` ("robots.txt could not be observed: refused"). The sentence asserted an observation the
event log shows was never made.

**Generated from the matrix, not from a list of names.** The bodies under restriction are the
rows whose A4 cell is `error` in the published matrices of the cycle of record
(`publication.yaml` `snapshot_cycle`). A future cycle that observes a grant moves the cell, and
the restriction lifts by itself; a new body that is refused enters it the same way.

**What the detector is, and what it is not.** It is lexical and conservative, in three parts:

* a CLAIM is a sentence asserting a host publishes or serves a `robots.txt`, or that a
  `robots.txt` grants, permits or allows (`CLAIM` below; "serves no `robots.txt`" is not one);
* a claim is ABOUT a restricted body when the sentence or its paragraph names the body, or when
  it refers to a group inside an H1/H2 section that names the body anywhere, its tables
  included. The claim sentence itself may refer by any group anaphor ("each", "they", "all
  three"); its paragraph only by an explicit one ("of them", "all three", "those same"),
  because a paragraph saying "each body's home page" is not thereby about three bodies;
* a body is NAMED by its frame code, its frame name, its host, its parent department when no
  other body in the frame shares it, or the upper-cased label of its host ("SSA" for
  `www.ssa.gov`) — every form read from the frame DataFile, none typed here.

It does not parse English. A claim joined to its bodies by nothing but a count in another
paragraph, or by a pronoun in another sentence of its paragraph, is not caught. The positive
control below runs the detector over the snapshot that carried C-02 and asserts it finds all
three of its sentences, so a negative here is a negative from an instrument shown to fire.

**Surfaces.** The views a reader is shown: the built report and its section sources, the brief
pack, the deck's markdown, the site index, `llms.txt` and the progress page. Not shown, and
deliberately excluded: `docs/reports/snapshots/` (a superseded snapshot kept unchanged under
DN-004 — it is the positive control here, and rewriting it would rewrite history), the audit
and design records (they quote the defect in order to name it), and `cc_tasks/`.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SITE = REPO / "docs"
REPORTS = SITE / "reports"
PUB = yaml.safe_load((REPORTS / "publication.yaml").read_text(encoding="utf-8"))

#: The frame's names for every body. The DataFile the frame file refers to
#: (`assessment/harness/scan/frames/fss16.yaml` `targets`).
FRAME = yaml.safe_load((REPO / "assessment" / "harness" / "scan" / "frames" / "fss16.yaml")
                       .read_text(encoding="utf-8"))
TARGETS = REPO / "state" / f"{FRAME['targets']}.json"

#: The superseded snapshot this task kept (decision 3). Its text is the C-02 defect verbatim.
PRIOR = REPORTS / "snapshots" / "2026-09_fss_ai_readiness_L0.688451fb.md"

CLAIM = [
    # "publishes a `robots.txt`", "serve their own robots.txt" — an article or possessive is
    # required, so "publishes no `robots.txt`" and "serves no such file" are not claims.
    re.compile(r"\b(?:publish(?:es|ed|ing)?|serves?|served|serving)\s+"
               r"(?:a|an|its|their|the|own)\s+(?:[\w'-]+\s+){0,2}?`?robots\.txt", re.I),
    # "a `robots.txt` that grants access", "`robots.txt` granting access".
    re.compile(r"robots\.txt`?\s+(?:that\s+|which\s+)?"
               r"(?:grants?|granting|permits?|permitting|allows?|allowing)\b", re.I),
    # "the `robots.txt` those same hosts publish".
    re.compile(r"robots\.txt`?\s+(?:those|these|that)\s+(?:same\s+)?"
               r"(?:hosts?|bodies|sites?|agencies)\s+publish", re.I),
]

#: Group reference that carries a named set into a sentence that does not name it. `ANAPHOR`
#: is read in the claim sentence; `GROUP`, the explicit subset, in the rest of its paragraph.
ANAPHOR = re.compile(r"\b(?:each|they|them|those same|all three|of them|these (?:bodies|hosts))\b",
                     re.I)
GROUP = re.compile(r"\b(?:those same|all three|of them|these (?:bodies|hosts))\b", re.I)

_SECTION = re.compile(r"^#{1,2}\s", re.M)
_SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z`\"*{])")


# ------------------------------------------------------------------ what the matrix restricts

def matrix_rows(cycle: str) -> list:
    """Every row of the published host-level matrices of `cycle`, both tiers."""
    suffix = cycle.removeprefix("scan_")
    rows = []
    for tier in ("tierA", "tierC"):
        path = REPORTS / f"scan_matrix_{tier}_{suffix}.json"
        if not path.is_file():
            raise AssertionError(f"{path.relative_to(REPO)} does not exist: the cycle of record "
                                 f"{cycle!r} has no published {tier} matrix to read A4 from")
        rows.extend(json.loads(path.read_text(encoding="utf-8"))["rows"])
    return rows


def frame_names() -> dict:
    """`{code: [name forms]}` for every body in the frame, from the DataFile only."""
    doc = json.loads(TARGETS.read_text(encoding="utf-8"))
    detail = doc["agency_detail"]
    depts = [d.get("parent_department") for d in detail]
    out = {}
    for d in detail:
        host = d["host"]
        forms = {d["agency"], d["agency_name"], host, host.removeprefix("www."),
                 host.removeprefix("www.").split(".")[0].upper()}
        if d.get("parent_department") and depts.count(d["parent_department"]) == 1:
            forms.add(d["parent_department"])
        out[d["agency"]] = sorted(forms, key=len, reverse=True)
    return out


def restricted(rows: list, names: dict) -> dict:
    """`{code: [name forms]}` for every body whose A4 cell is `error`. A row the frame does not
    name (a reference host) is named by its code and its host."""
    out = {}
    for r in rows:
        if r["verdicts"].get("A4") != "error":
            continue
        code = r["agency"]
        host = r["host_surface"].split(":", 1)[1]
        out[code] = names.get(code) or sorted({code, host, host.removeprefix("www.")},
                                              key=len, reverse=True)
    return out


# ------------------------------------------------------------------ the detector

def _names_any(text: str, forms: list) -> bool:
    return any(re.search(rf"(?<![\w.-]){re.escape(f)}(?![\w-])", text) for f in forms)


def _prose(text: str, suffix: str) -> str:
    if suffix != ".html":
        return text
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
    text = re.sub(r"(?i)</?(?:p|li|h\d|tr|div|section|br)\b[^>]*>", "\n\n", text)
    return html.unescape(re.sub(r"<[^>]+>", " ", text))


def violations(text: str, bodies: dict, suffix: str = ".md") -> list:
    """`(code, sentence)` for every claim sentence about a restricted body."""
    found = []
    text = _prose(text, suffix)
    starts = [m.start() for m in _SECTION.finditer(text)]
    for a, b in zip([0] + starts, starts + [len(text)]):
        section = text[a:b]
        for para in re.split(r"\n\s*\n", section):
            lines = [l for l in para.splitlines()
                     if l.strip() and not l.lstrip().startswith(("|", "#"))]
            if not lines:
                continue
            para_text = " ".join(l.strip() for l in lines)
            for sentence in _SENTENCE.split(para_text):
                if not any(p.search(sentence) for p in CLAIM):
                    continue
                anaphoric = bool(ANAPHOR.search(sentence) or GROUP.search(para_text))
                for code, forms in bodies.items():
                    if (_names_any(sentence, forms) or _names_any(para_text, forms)
                            or (anaphoric and _names_any(section, forms))):
                        found.append((code, sentence.strip()[:240]))
    return found


def shown_surfaces() -> list:
    paths = [REPORTS / "2026-09_fss_ai_readiness_L0.md",
             *sorted((REPORTS / "sections").glob("*.md")),
             *sorted((SITE / "brief").rglob("*.md")),
             *sorted((SITE / "deck").glob("*.md")),
             SITE / "index.html", SITE / "llms.txt", SITE / "progress" / "index.html"]
    missing = [p for p in paths if not p.is_file()]
    assert not missing, f"shown surfaces absent from the tree: {missing}"
    return paths


# ------------------------------------------------------------------ the tests

def test_the_cycle_of_record_restricts_the_bodies_whose_robots_txt_was_refused():
    """The restriction is read from the matrix; on `scan_2026-09-10_rj4` it is the three
    refusing hosts, and nothing in this file names them."""
    bodies = restricted(matrix_rows(PUB["snapshot_cycle"]), frame_names())
    assert bodies, "no A4 `error` cell on the cycle of record: the restriction is empty"
    for code, forms in bodies.items():
        assert code in forms and len(forms) >= 3, (code, forms)


def test_no_shown_surface_says_a_restricted_body_publishes_a_robots_txt():
    bodies = restricted(matrix_rows(PUB["snapshot_cycle"]), frame_names())
    bad = []
    for path in shown_surfaces():
        for code, sentence in violations(path.read_text(encoding="utf-8"), bodies, path.suffix):
            bad.append(f"{path.relative_to(REPO)}: [{code}] {sentence}")
    assert not bad, ("a shown surface asserts a robots.txt the instrument never read for a "
                     "body whose A4 cell is `error`:\n  " + "\n  ".join(bad))


def test_positive_control_the_detector_finds_the_c02_sentences_in_the_prior_snapshot():
    """The negative above means something only if the detector finds the defect it was built
    for: the three C-02 sentences, in the report as published before the correction. The A12
    definition is the hard one — it names no body and is joined to its instances only by the
    next sentence's "Three of them are the bodies discussed in the next section" and by the
    matrix rows in its section."""
    bodies = restricted(matrix_rows(PUB["snapshot_cycle"]), frame_names())
    found = [s for _c, s in violations(PRIOR.read_text(encoding="utf-8"), bodies)]
    assert any("obeys the `robots.txt` those same hosts" in s for s in found), found
    assert any("each publishes a `robots.txt` that grants access" in s for s in found), found
    assert any("An incoherent host publishes a `robots.txt` granting access" in s
               for s in found), found
    # And nothing else in that snapshot: the general sentences about robots.txt are not claims
    # about a refused body.
    assert len(set(found)) == 3, sorted(set(found))


def test_the_restriction_lifts_when_a_cycle_observes_the_file():
    """Generated from the matrix: a row whose A4 cell is no longer `error` is no longer
    restricted, with no edit to this file."""
    rows = matrix_rows(PUB["snapshot_cycle"])
    names = frame_names()
    code = next(iter(restricted(rows, names)))
    lifted = [dict(r, verdicts=dict(r["verdicts"], A4="pass")) if r["agency"] == code else r
              for r in rows]
    assert code not in restricted(lifted, names)
    claim = f"The {names[code][-1]} host publishes a `robots.txt` that grants access."
    assert violations(claim, restricted(rows, names))
    assert not [v for v in violations(claim, restricted(lifted, names)) if v[0] == code]


@pytest.mark.parametrize("sentence", [
    "Each host serves no `robots.txt` at all.",
    "A4 asks whether the host serves a `robots.txt` and whether it permits a client.",
])
def test_a_negation_or_a_definition_naming_no_body_is_not_a_claim_about_one(sentence):
    bodies = restricted(matrix_rows(PUB["snapshot_cycle"]), frame_names())
    assert not violations(sentence, bodies)


# ------------------------------------------------------------------ the change line (decision 3)

def _builder():
    import sys
    sys.path.insert(0, str(REPO / "scripts"))
    import build_l0_report
    return build_l0_report


def test_the_built_report_states_its_correction_and_points_at_the_kept_text():
    """The corrected snapshot says what was corrected and when, on its face, and names the
    kept prior text, which exists. Read from the declaration, so a second correction is one
    more entry and no edit here."""
    entries = PUB["corrections"][PUB["version"]]
    head = (REPORTS / "2026-09_fss_ai_readiness_L0.md").read_text(encoding="utf-8").splitlines()[:4]
    block = next(l for l in head if l.startswith("**Version.**"))
    for c in entries:
        assert f"**Corrected `{c['date']}`**" in block
        assert f"`{c['finding']}`" in block
        for key in ("prior_md", "prior_pdf"):
            assert (REPO / c[key]).is_file(), c[key]
            assert f"`{c[key].removeprefix('docs/')}`" in block


@pytest.mark.parametrize("change, message", [
    ({"date": "2026-09-01"}, "before the version's release"),
    ({"prior_md": "docs/reports/snapshots/absent.md"}, "does not exist"),
    ({"summary": ""}, "declares no 'summary'"),
])
def test_a_correction_that_points_at_nothing_or_predates_the_release_is_refused(change, message):
    B = _builder()
    entry = dict(PUB["corrections"][PUB["version"]][0], **change)
    pub = dict(PUB, corrections={PUB["version"]: [entry]})
    with pytest.raises(SystemExit, match=message):
        B.correction_lines(pub, PUB["released"][PUB["version"]])


def test_a_version_with_no_corrections_renders_no_change_line():
    B = _builder()
    pub = {k: v for k, v in PUB.items() if k != "corrections"}
    assert B.correction_lines(pub, PUB["released"][PUB["version"]]) == ""
