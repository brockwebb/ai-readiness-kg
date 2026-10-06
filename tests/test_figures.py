"""The summary figures are a generated view: `cc_tasks/2026-10-02_summary_figures.md`.

What is asserted, and why each is the right test:

* **Idempotence** (decision 1): re-render and compare with what is on disk, the guard every
  generated view here uses (`scripts/build_brief_pack.py --check`, `scripts/score.py --check`).
  SVG, captions, CSV and the number ledger by bytes; PNG by decoded pixels, because PNG encoders
  are not byte-stable and the task says so.
* **Every numeral on a figure is on that figure's ledger**: each text element the figure draws
  is read back from the live matplotlib figure, and a numeral the ledger does not hold for that
  figure fails with the figure and the text named.
* **Every count equals an independent computation**: the counts are re-derived here from the
  record, `scripts/score.py`, the manifest and the cycle's shard by code that does not go through
  the figure script's `compute`, so a wrong walk in `compute` cannot agree with itself.
* **Every claim id in a caption exists** in `docs/evidence/claims.yaml`.
"""
from __future__ import annotations

import csv
import io
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

import build_figures as BF  # noqa: E402

#: A standalone numeral: not part of an identifier (`A10`, `G1-D`, `scan_2026-09-10_rj4`).
NUMERAL = re.compile(r"(?<![\w.\-])\d[\d,]*(?:\.\d+)?(?![\w\-])")


@pytest.fixture(scope="module")
def rendered():
    files, figs, d = BF.render()
    yield files, figs, d
    import matplotlib.pyplot as plt
    for f in figs.values():
        plt.close(f)


def test_check_is_a_no_op_over_the_committed_files(rendered):
    files, _, _ = rendered
    for name, data in files.items():
        p = BF.OUT / name
        assert p.is_file(), f"{name} is not on disk; run scripts/build_figures.py"
        if name.endswith(".png"):
            old, new = BF.png_pixels(p.read_bytes()), BF.png_pixels(data)
            assert old.shape == new.shape and (old == new).all(), f"{name}: pixels drifted"
        else:
            assert p.read_bytes() == data, f"{name}: bytes drifted"


def test_svg_is_byte_stable_across_renders(rendered):
    files, _, _ = rendered
    again, figs, _ = BF.render()
    import matplotlib.pyplot as plt
    for f in figs.values():
        plt.close(f)
    for name in BF.FIGURES:
        assert again[f"{name}.svg"] == files[f"{name}.svg"], f"{name}.svg is not deterministic"


def test_every_numeral_on_a_figure_is_on_its_ledger(rendered):
    files, figs, _ = rendered
    ledger = json.loads(files["numbers.json"])
    for name, fig in figs.items():
        held = {e["value"] for e in ledger[name]}
        texts = [t.get_text() for ax in fig.axes for t in ax.texts]
        assert texts, f"{name} drew no text"
        for t in texts:
            for num in NUMERAL.findall(t):
                assert num in held, f"{name}: numeral {num!r} in {t!r} is not on its ledger"


def _independent_counts() -> dict:
    """The figure-1 and figure-2 counts, walked here without `BF.compute`."""
    import score as S
    from framework_writeback import _candidate_ids
    from scan import rules as R
    rec = json.loads(BF.RECORD.read_text(encoding="utf-8"))
    cand = _candidate_ids(rec)
    code = {n["id"]: n["properties"].get("code") for n in rec["nodes"]}
    crit_of_con = {e["to"]: code[e["from"]] for e in rec["edges"]
                   if e["type"] == "DECOMPOSES_INTO" and e["from"].startswith("crit:")}
    per = {}
    for e in rec["edges"]:
        if e["type"] == "DECOMPOSES_INTO" and e["from"] in crit_of_con and e["to"] not in cand:
            per[crit_of_con[e["from"]]] = per.get(crit_of_con[e["from"]], 0) + 1
    r = S.compute()
    rule_codes = {R.parse_rule_id(x)["indicator_code"] for x in R.CURRENT.values()}
    fw = [n for n in rec["nodes"] if "AssessmentIndicator" in n["labels"] and n["id"] not in cand]
    man = json.loads(BF.MANIFEST.read_text(encoding="utf-8"))["entries"]
    return {
        "per_criterion": per,
        "framework_indicators": len(fw),
        "rule_indicators": sum(n["properties"]["code"] in rule_codes for n in fw),
        "specified": sum(n["properties"].get("measurement_status") == "specified" for n in fw),
        # `cc_tasks/2026-10-06_scoring_frontier_parent_host_counts.md` decision 3: figure 1's
        # "measured" is the record's, and "on the cycle of record" is the record's
        # `measured_by.cycle` (DD-069), counted here from the nodes rather than through the
        # figure's own classification.
        "measured_cycle": sum(n["properties"].get("measurement_status") == "measured"
                              and (n["properties"].get("measured_by") or {}).get("cycle")
                              == r["cycle"]["name"] for n in fw),
        "measured": rec["counts"]["indicators_measured"],
        "documents": sum(v["screening"]["decision"] == "included" for v in man.values()),
        "rules": len(set(R.CURRENT.values())),
        "bodies": len(r["bodies"]),
        "ranked": sum(v["rank"] is not None for v in r["bodies"].values()),
        "score": r,
    }


def test_figure_counts_equal_an_independent_computation(rendered):
    _, figs, d = rendered
    ind = _independent_counts()
    assert {c["code"]: c["indicators"] for c in d["criteria"]} == ind["per_criterion"]
    for k in ("framework_indicators", "rule_indicators", "specified", "measured_cycle",
              "measured", "documents", "rules", "bodies", "ranked"):
        assert d[k] == ind[k], f"{k}: figure says {d[k]}, independent count {ind[k]}"
    for c in d["criteria"]:
        assert sum(len(v) for v in c["states"].values()) == c["indicators"], c["code"]
    # The counts are on the figures, not only in `compute`.
    t1 = " ".join(t.get_text() for t in figs[BF.FIG1].axes[0].texts)
    assert f"{ind['measured']} of {ind['framework_indicators']} indicators measured" in t1
    t2 = " ".join(t.get_text() for t in figs[BF.FIG2].axes[0].texts)
    for k in ("documents", "rules", "bodies", "ranked", "framework_indicators"):
        assert re.search(rf"(?<![\d,]){ind[k]:,}(?![\d,])", t2), f"figure 2 lacks {k}"


def test_figure3_cells_and_csv_match_the_score_model(rendered):
    files, _, d = rendered
    r = _independent_counts()["score"]
    rows = list(csv.DictReader(io.StringIO(files[f"{BF.FIG3}.csv"].decode("utf-8"))))
    assert [x["body"] for x in rows] == sorted(r["bodies"]), "rows are not in roster order"
    crit_legs: dict = {}
    for l in r["structure"]:
        if l["scored"]:
            crit_legs.setdefault(l["criterion"], []).append(l["leg"])
    for x in rows:
        b = r["bodies"][x["body"]]
        for c in r["framework"]["criteria"]:
            judged = [b["legs"][leg] for leg in crit_legs.get(c, [])
                      if b["legs"].get(leg, {}).get("judged")]
            want = "" if not judged else (
                f"{sum(j['pass'] == j['judged'] for j in judged)}/{len(judged)}")
            assert x[c] == want, f"{x['body']} {c}: csv {x[c]!r}, score model {want!r}"
        if b["score"] is None:
            assert x["hierarchical_score"] == "" and x["rank"] == ""
        else:
            assert x["hierarchical_score"] == format(b["score"], ".3f")
            assert int(x["rank"]) == b["rank"]
            assert x["rank_rests_on_leg"] == b["concentration"]["leg"]
            assert int(x["rank_if_leg_reversed"]) == b["concentration"]["rank_if_reversed"]


def test_every_caption_claim_id_exists():
    ids = {c["id"] for c in yaml.safe_load(BF.CLAIMS.read_text(encoding="utf-8"))["claims"]}
    for name in BF.FIGURES:
        text = (BF.OUT / f"{name}.caption.md").read_text(encoding="utf-8")
        cited = re.findall(r"CL-\d{3}", text)
        assert cited, f"{name}: caption cites no claim id"
        missing = sorted(set(cited) - ids)
        assert not missing, f"{name}: caption cites {missing}, not in claims.yaml"


def test_caption_is_rendered_from_the_figure_data(rendered):
    files, _, d = rendered
    cap = files[f"{BF.FIG1}.caption.md"].decode("utf-8")
    assert (f"{d['measured']} are measured, {d['measured_cycle']} of them on the cycle of "
            f"record") in cap
    assert "**What this shows.**" in cap
