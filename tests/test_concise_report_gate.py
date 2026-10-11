"""The concise report's checks by code (`scripts/concise_report_gate.py`,
cc_tasks/2026-10-07_concise_report_prose.md decisions 4 and 5): markers, the digit check,
dashes, the banned list, the short-clarification pair rule and the repetition warnings. Each
rule is tested on a case it must catch and a case it must pass."""
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import concise_report_gate as G  # noqa: E402
import dcat_faq_lint  # noqa: E402

CFG = yaml.safe_load((REPO / "reports" / "concise" / "report_config.yaml").read_text(encoding="utf-8"))
GATE = CFG["gate"]
CLAIMS = {
    "CL-035": {"id": "CL-035", "text": "Of the 1,055 findings, 341 are access denials and 177 pass.",
               "numbers": [{"value": "1,055"}, {"value": "341"}, {"value": "177"}]},
    "CL-053": {"id": "CL-053", "text": "`CENSUS` ranks 7 of 13 (0.143).", "numbers": [{"value": "0.143"}]},
}


def test_markers_are_read_and_stripped():
    s = "Most findings fail [c:CL-035][c:cl-053, CL-035]."
    assert G.marker_ids(s) == ["CL-035", "CL-053"]
    assert G.strip_markers(s) == "Most findings fail."


def test_digit_check_passes_numbers_its_cited_claims_hold():
    r = G.digit_check("Of 1,055 findings, 177 pass, and the score is 0.143 [c:CL-035, CL-053].", CLAIMS)
    assert r["ok"], r


def test_digit_check_fails_a_number_no_cited_claim_holds():
    r = G.digit_check("Of 1,055 findings, 512 pass [c:CL-035].", CLAIMS)
    assert not r["ok"] and r["missing"] == ["512"]


def test_digit_check_fails_a_number_held_only_by_an_uncited_claim():
    assert not G.digit_check("The score is 0.143 [c:CL-035].", CLAIMS)["ok"]


def test_digit_check_fails_a_digit_with_no_marker_and_an_unknown_id():
    assert not G.digit_check("Of 1,055 findings, most fail.", CLAIMS)["ok"]
    assert G.digit_check("Most fail [c:CL-999].", CLAIMS)["unknown_ids"] == ["CL-999"]


def test_em_dash_always_and_en_dash_only_as_a_dash():
    assert [f["rule"] for f in G.dash_findings("a — b")] == ["em_dash"]
    assert [f["rule"] for f in G.dash_findings("a – b")] == ["en_dash_as_dash"]
    assert G.dash_findings("pages 3–5") == []


def test_banned_list_is_the_operators_file_and_the_lint_reads_it():
    doc = yaml.safe_load((REPO / "docs" / "style" / "operator_banned_words.yaml").read_text(encoding="utf-8"))
    terms = [e["term"] for e in doc["words"]] + [e["term"] for e in doc["flagged_sources"]]
    assert terms == ["load-bearing", "load bearing", "hallucinate", "delve", "testament", "Gartner"]
    assert all(e["source"] == "operator, stated preferences, recorded 2026-10-07"
               for e in doc["words"] + doc["flagged_sources"])
    text = "This load-bearing claim, a testament to Gartner, hallucinated as we delved."
    rules = sorted(f["rule"] for f in dcat_faq_lint.lint(text))
    assert rules == ["banned_word"] * 4 + ["flagged_source"]
    assert sorted(f["match"] for f in G.banned_findings(text)) == ["Gartner", "delved", "hallucinated",
                                                                    "load-bearing", "testament"]
    assert G.banned_findings("The model confabulated a number.") == []


def test_a_missing_banned_list_fails_loud(tmp_path):
    with pytest.raises(SystemExit, match="banned list"):
        dcat_faq_lint.banned_rules(tmp_path / "absent.yaml")


LONG = "The scanner asked every host for the same pages with one plain identity and recorded each answer."


@pytest.mark.parametrize("second,why", [
    ("Not a browser.", "opens with qualifier 'Not'"),
    ("Only the public pages.", "opens with qualifier 'Only'"),
    ("That is, a plain client.", "opens with qualifier 'That is'"),
    ("Every page, every host.", "no finite verb"),
])
def test_the_short_clarification_pair_is_flagged(second, why):
    p = G.flagged_pairs([LONG, second], GATE["pair"])
    assert len(p) == 1 and p[0]["why"] == why


@pytest.mark.parametrize("second", [
    "Most hosts answered.",                                     # short, finite verb, no qualifier
    "Only the public pages were read, and each page was kept whole on disk.",  # too long
])
def test_a_pair_the_rule_does_not_name_passes(second):
    assert G.flagged_pairs([LONG, second], GATE["pair"]) == []


def test_the_first_sentence_must_be_twice_as_long():
    # 5 words then 3: 5 < 2 x 3, so not flagged; 6 words then 3 is.
    assert G.flagged_pairs(["The scanner read six pages.", "Not more pages."], GATE["pair"]) == []
    assert len(G.flagged_pairs(["The scanner read six long pages.", "Not more pages."], GATE["pair"])) == 1


def test_a_section_with_three_flagged_pairs_fails_and_two_passes():
    two = [LONG, "Not a browser.", LONG, "Only public pages."]
    three = two + [LONG, "No login."]
    assert G.section_measures(two, GATE)["pass"]
    m = G.section_measures(three, GATE)
    assert m["flagged_pair_count"] == 3 and not m["pass"]


def test_repetition_warnings_name_repeated_3grams_and_overused_lemmas():
    s1 = ["Hosts refused plain clients often [c:CL-035].", "Hosts refused plain clients again."]
    s2 = ["Hosts refused plain clients here too."]
    rep = G.gate_report({1: s1, 2: s2}, GATE)
    g = rep["repeated_3grams"]
    assert g["host refuse plain"]["count"] == 3 and g["host refuse plain"]["sections"] == [1, 2]
    many = ["The host refused the request."] * 6
    assert G.section_measures(many, GATE)["lemmas_over_limit"]["host"] == 6
    assert "host" not in G.section_measures(many[:5], GATE)["lemmas_over_limit"]


def test_reported_measures_are_present_and_bounded():
    m = G.section_measures([LONG, "However, two hosts refused it, so their rows are errors.",
                            "The scanner kept every answer."], GATE)
    assert m["connectives_per_sentence"] > 0 and 0 < m["sentences_with_a_connective"] <= 1
    assert 0 <= m["adjacent_content_overlap_mean_jaccard"] <= 1
    assert m["sentence_length_sd"] > 0 and m["finite_verbs_per_sentence"] >= 1


def test_the_gate_fails_a_section_with_a_dash_or_a_banned_word():
    rep = G.gate_report({1: ["The host refused — twice."], 2: ["This is a testament."]}, GATE)
    assert not rep["sections"][1]["pass"] and not rep["sections"][2]["pass"]
    assert rep["tagger"].startswith("spaCy en_core_web_sm")
