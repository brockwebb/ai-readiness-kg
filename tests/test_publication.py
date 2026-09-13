"""The published tree says only what the repository can back up.

`cc_tasks/2026-09-12_publish_l0.md` §3. The site is a build product of
`scripts/build_l0_site.py`, and every property here is one a reader of the SITE would have to
take on trust otherwise:

* a link on the index resolves to a file that is actually in the tree;
* a copy of a record canonical elsewhere still equals that record;
* the citation files at the repository root and inside the tree are one file written twice;
* `robots.txt` admits, by name, every crawler the instrument evaluates other publishers on —
  read from `params.a4_crawlers.user_agents`, so adding a crawler to the instrument and
  forgetting to admit it here is a failure rather than an asymmetry nobody notices;
* the sitemap enumerates files that exist;
* the published Results are the ones the report tags, at the values the graph holds;
* every provenance path a published Result names is either IN the repository or declared
  ephemeral in the registry and actually re-derivable from what the repository does hold
  (`cc_tasks/2026-09-13_ephemeral_provenance.md` decision 2 — the stranger test, as a test);
* both licences are declared, their texts are present, and the corpus exclusion is stated
  (its ADDENDUM_1 decision A5).

The Neo4j-backed test skips when the database is down, which is this repo's convention; the
file-only ones do not, because the tree is on disk either way.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parent.parent
SITE = REPO / "docs"
DATA = SITE / "data"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "assessment" / "harness"))

PUB = yaml.safe_load((SITE / "reports" / "publication.yaml").read_text(encoding="utf-8"))
MANIFEST = json.loads((DATA / "index.json").read_text(encoding="utf-8"))

#: `href="..."` on the index. Absolute URLs are excluded: this test is about the tree.
HREF = re.compile(r'href="([^"#]+)"')


@pytest.fixture
def session():
    """A live Neo4j session, or a skip. The same shape `tests/test_scan_frame.py` uses: the
    file-only assertions in this module stand whether or not the database is up."""
    try:
        sys.path.insert(0, "/Users/brock/GitHub/seldon")
        from seldon.config import get_neo4j_driver, load_project_config
        cfg = load_project_config(REPO)
        driver = get_neo4j_driver(cfg)
        with driver.session(database=cfg["neo4j"]["database"]) as s:
            s.run("RETURN 1").single()
    except Exception as exc:                                          # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {exc}")
    with driver.session(database=cfg["neo4j"]["database"]) as s:
        yield s
    driver.close()


def test_the_site_index_exists_and_names_the_snapshot_cycle():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert PUB["snapshot_cycle"] in html, (
        "the index does not state which cycle it is a view of")
    assert PUB["version"] in html


def test_every_relative_link_on_the_index_resolves_in_the_tree():
    html = (SITE / "index.html").read_text(encoding="utf-8")
    missing = []
    for href in HREF.findall(html):
        if href.startswith(("http://", "https://", "mailto:")):
            continue
        target = SITE / href
        if href.endswith("/"):
            target = target / "index.html"
        if not target.is_file():
            missing.append(href)
    assert not missing, f"the index links {len(missing)} path(s) the tree does not hold: {missing}"


def test_the_index_links_the_data_before_the_views():
    """Decision 1's order is the argument, not a layout preference: a reader who meets the PDF
    first takes the PDF for the product."""
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert html.index("The data") < html.index("The views")
    assert "projection of the data above it" in html


def test_every_copy_still_equals_the_record_it_was_copied_from():
    drifted = []
    for c in MANIFEST["copies"]:
        src, dst = REPO / c["source"], REPO / "docs" / c["published"]
        assert src.is_file(), f"{c['source']} is gone; the copy can no longer be checked"
        assert dst.is_file(), f"{c['published']} is not in the tree"
        if hashlib.sha256(src.read_bytes()).hexdigest() != c["sha256"]:
            drifted.append(f"{c['source']} moved since the site was built")
        elif src.read_bytes() != dst.read_bytes():
            drifted.append(f"{c['published']} differs from {c['source']}")
    assert not drifted, drifted


def test_the_citation_files_are_one_file_written_twice():
    for c in MANIFEST["citation_files"]:
        root = REPO / c["also_written_to"]
        served = REPO / "docs" / c["published"]
        assert root.is_file() and served.is_file()
        assert root.read_bytes() == served.read_bytes(), (
            f"{c['also_written_to']} and {c['published']} have diverged; they are written "
            f"from one string and cannot legitimately differ")


#: CFF 1.2.0's required keys. Asserted from the specification rather than checked against a
#: schema validator, because none is installed and fetching the published schema would spend
#: this task's network budget on a host that is not the published one. `authors` additionally
#: has a required shape: each entry is a person or an entity, and a person needs `family-names`.
CFF_REQUIRED = ("cff-version", "message", "title", "authors")


def test_citation_cff_parses_and_carries_every_required_key():
    doc = yaml.safe_load((REPO / "CITATION.cff").read_text(encoding="utf-8"))
    for key in CFF_REQUIRED:
        assert doc.get(key), f"CITATION.cff carries no {key!r}; CFF 1.2.0 requires it"
    assert isinstance(doc["authors"], list) and doc["authors"]
    for a in doc["authors"]:
        assert a.get("family-names") or a.get("name"), (
            f"author entry {a} is neither a person with family-names nor an entity with name")
    assert doc["cff-version"] == "1.2.0"
    assert doc["title"] == PUB["title"]
    assert doc["version"] == PUB["version"]
    assert doc["authors"] == PUB["authors"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(doc["date-released"]))
    assert "doi" not in doc, (
        "a DOI appeared in CITATION.cff; the mint is the operator's action under his own name "
        "(DN-002 decision 5) and no build step may assert one")


def test_zenodo_metadata_parses_and_mints_nothing():
    """A licence is now declared and a DOI still is not, and the asymmetry is the point: the
    licence is the operator's declaration of 2026-09-13, the mint is an action under his own
    name that no build step may take (DN-002 decision 5)."""
    doc = json.loads((REPO / ".zenodo.json").read_text(encoding="utf-8"))
    assert doc["title"] == PUB["title"]
    assert doc["creators"] == [{"name": "Webb, Brock"}]
    assert "doi" not in doc
    assert doc["license"] == PUB["license_data"]


def test_robots_admits_every_crawler_the_instrument_measures_others_on():
    from scan import load_params
    crawlers = load_params()["a4_crawlers"]["user_agents"]
    text = (SITE / "robots.txt").read_text(encoding="utf-8")
    directives = [l.strip() for l in text.splitlines() if not l.lstrip().startswith("#")]
    named = {l.split(":", 1)[1].strip() for l in directives
             if l.lower().startswith("user-agent:")}
    assert set(crawlers) <= named, (
        f"robots.txt does not name {sorted(set(crawlers) - named)}; A4 evaluates other "
        f"publishers against exactly this list")
    assert not [l for l in directives if l.lower().startswith("disallow:")
                and l.split(":", 1)[1].strip()], (
        "this publication disallows a path to a crawler it measures others for admitting")
    assert f"Sitemap: {PUB['site_url']}sitemap.xml" in text


def test_robots_states_the_authority_limit_rather_than_implying_compliance():
    """RFC 9309 binds robots.txt to an authority. On a project Pages site this file is not at
    the authority root, and a file that did not say so would be a compliance claim it cannot
    make."""
    text = (SITE / "robots.txt").read_text(encoding="utf-8")
    assert "RFC 9309" in text and "authority" in text.lower()


def test_llms_txt_is_in_the_published_shape_and_links_the_same_data():
    text = (SITE / "llms.txt").read_text(encoding="utf-8")
    lines = text.splitlines()
    assert lines[0].startswith("# "), "llms.txt must open with an H1"
    assert any(l.startswith("> ") for l in lines[:6]), "llms.txt must carry a blockquote summary"
    for row in MANIFEST["matrices"]:
        assert PUB["site_url"] + row in text, f"llms.txt does not link {row}"


def test_every_sitemap_entry_is_a_file_the_tree_holds():
    root = ET.fromstring((SITE / "sitemap.xml").read_text(encoding="utf-8"))
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locs = [u.findtext("sm:loc", namespaces=ns) for u in root.findall("sm:url", ns)]
    assert locs, "the sitemap is empty"
    missing = []
    for loc in locs:
        assert loc.startswith(PUB["site_url"]), f"{loc} is not on this site"
        rel = loc[len(PUB["site_url"]):]
        target = SITE / rel if rel else SITE / "index.html"
        if rel.endswith("/"):
            target = SITE / rel / "index.html"
        if not target.is_file():
            missing.append(rel)
    assert not missing, f"the sitemap names {missing}, which the tree does not hold"


def test_the_published_results_are_the_ones_the_report_tags():
    import rederive_tagged_results as rd
    doc = json.loads((DATA / "results_tagged.json").read_text(encoding="utf-8"))
    assert {r["name"] for r in doc["results"]} == set(rd.tagged_names())
    assert doc["count"] == len(doc["results"])
    for r in doc["results"]:
        assert r["generated_by"], f"{r['name']} is published with no generating artifact"
        assert r["computed_from"], f"{r['name']} is published with no input artifact"


def test_the_published_result_values_and_states_match_the_graph(session):
    doc = json.loads((DATA / "results_tagged.json").read_text(encoding="utf-8"))
    live = {r["name"]: (r["value"], r["state"]) for r in session.run(
        "MATCH (r:Result) WHERE r.name IN $names AND r.state <> 'superseded' "
        "RETURN r.name AS name, r.value AS value, r.state AS state",
        names=[r["name"] for r in doc["results"]])}
    drift = [f"{r['name']}: published {r['value']}/{r['state']}, graph {live.get(r['name'])}"
             for r in doc["results"]
             if live.get(r["name"]) != (r["value"], r["state"])]
    assert not drift, drift


def test_the_source_appendix_data_cites_only_admitted_documents():
    doc = json.loads((DATA / "sources_per_check.json").read_text(encoding="utf-8"))
    entries = json.loads((REPO / "corpus" / "manifest.json")
                         .read_text(encoding="utf-8"))["entries"]
    assert doc["rows"], "the appendix is empty"
    assert not doc["legs_without_source"], (
        f"{doc['legs_without_source']} reach no admitted source; DN-001's floor is that every "
        f"published check is cited")
    outside = [r["doc_id"] for r in doc["rows"] if r["doc_id"] and r["doc_id"] not in entries]
    assert not outside, f"the appendix cites documents outside the manifest: {outside[:5]}"


def test_every_published_citation_carries_the_pair_a_stranger_needs():
    """DN-001's floor, made machine-readable: a citation a stranger can follow is a URL AND a
    digest of the bytes that URL served, plus when they were taken. DD-003's provenance pair is
    exactly `primary_url + content_hash`, and `acquisition.acquired_at` is what
    `cc_tasks/2026-09-12_cited_documents_metadata.md` put on every cited document."""
    doc = json.loads((DATA / "sources_per_check.json").read_text(encoding="utf-8"))
    thin = [r["doc_id"] for r in doc["rows"]
            if r["doc_id"] and not (r["source_url"] and r["content_hash"] and r["acquired_at"])]
    assert not thin, f"{len(thin)} published citation(s) carry no URL/hash/date: {thin[:5]}"


def test_the_self_row_is_measured_or_says_it_is_not():
    """Decision 2. The row is a measurement against the published host; until one exists the
    index has to say so in words. What it may never do is print a verdict."""
    import build_l0_site
    html = (SITE / "index.html").read_text(encoding="utf-8")
    assert "This site's own row" in html
    if build_l0_site.self_row(PUB) is None:
        assert "Not measured" in html
        assert "<td class=\"v " not in html, (
            "the self row prints a verdict and no self-scan payload exists")
    else:
        assert "<td class=\"v " in html


# ------------------------------------------------------- the builders behind the tree

def test_the_built_report_carries_the_version_block_the_config_declares():
    """DN-002 decision 5 / task decision 4: the document states its own version. Generated on
    every build rather than written into section prose, so it cannot go stale."""
    md = (SITE / "reports" / "2026-09_fss_ai_readiness_L0.md").read_text(encoding="utf-8")
    head = md.splitlines()[:4]
    assert head[0].startswith("# "), "the report no longer opens with its title"
    block = next(l for l in head if l.startswith("**Version.**"))
    assert f"`{PUB['snapshot_cycle']}`" in block
    assert f"`{PUB['version']}`" in block
    assert "built from commit `" in block


def test_the_version_block_refuses_a_body_with_no_heading():
    import build_l0_report
    with pytest.raises(SystemExit, match="no H1"):
        build_l0_report.insert_version_block("no heading here\n", "BLOCK")


def test_the_version_block_goes_after_the_title_and_before_the_standfirst():
    import build_l0_report
    out = build_l0_report.insert_version_block("# Title\n\n**Draft.** body\n", "BLOCK")
    assert out.splitlines()[:4] == ["# Title", "", "BLOCK", ""]


def test_the_tagged_set_is_read_from_the_report_and_not_typed():
    import rederive_tagged_results as rd
    names = rd.tagged_names()
    assert names
    sources = "\n".join(f.read_text(encoding="utf-8")
                        for f in sorted((SITE / "reports" / "sections").glob("*.md")))
    for n in names:
        assert "{{result:" + n + ":" in sources


def test_a_state_move_refuses_a_rederivation_that_did_not_pass(tmp_path):
    """§1's stop, asserted rather than trusted: a Result that did not re-derive is a stop, and
    the only evidence the transition script will accept is a PASS report."""
    import publish_result_states as ps
    blocked = tmp_path / "blocked.json"
    blocked.write_text(json.dumps({"gate": "BLOCKED", "tagged": 2, "rows": []}))
    with pytest.raises(SystemExit, match="§1 stops"):
        ps.reproducing(blocked)

    short = tmp_path / "short.json"
    short.write_text(json.dumps({"gate": "PASS", "tagged": 2, "rows": [
        {"name": "a", "verdict": "reproduces"}, {"name": "b", "verdict": "disagrees"}]}))
    with pytest.raises(SystemExit, match="cannot both be true"):
        ps.reproducing(short)

    with pytest.raises(SystemExit, match="does not exist"):
        ps.reproducing(tmp_path / "absent.json")


def test_the_state_moves_are_the_ones_the_domain_allows():
    """`proposed -> verified -> published` is Seldon's Result state machine, and this script
    must not invent an edge that the validated path would then refuse."""
    import publish_result_states as ps
    machine = yaml.safe_load(
        (Path("/Users/brock/GitHub/seldon") / "seldon" / "domain" / "research.yaml")
        .read_text(encoding="utf-8"))["state_machines"]["Result"]
    for _verb, (frm, to) in ps.MOVES.items():
        assert to in machine[frm], f"{frm} -> {to} is not a legal Result transition"


# ------------------------------------------- the stranger test: can the chain be followed?

#: One whitespace-normalised sentence, so a declaration that is line-wrapped differently in a
#: licence file, an HTML page and a JSON note still counts as the same sentence.
def _flat(text: str) -> str:
    return " ".join(str(text).split())


def _published_provenance(session) -> dict:
    """name -> the DataFile rows every `published` Result is COMPUTED_FROM, straight from the
    graph. Not read from the published JSON: that file is what is being checked."""
    rows = session.run(
        "MATCH (r:Result {state:'published'})-[:COMPUTED_FROM]->(d:DataFile) "
        "RETURN DISTINCT d.name AS name, d.path AS path, d.materialized AS materialized, "
        "       d.derivable_from AS derivable_from, d.derivation_command AS command, "
        "       collect(DISTINCT r.name) AS dependents").data()
    return {r["name"]: r for r in rows}


def test_every_published_provenance_path_is_held_or_declared_ephemeral(session):
    """`cc_tasks/2026-09-13_ephemeral_provenance.md` decision 2, the stranger test.

    A stranger follows `COMPUTED_FROM` from a published Result to a DataFile and opens its path.
    Two outcomes are acceptable and there is no third: the repository holds the file, or the
    registry says it deliberately does not and names what it is derivable from. A DataFile in
    neither state is a dead provenance path on a published claim, which is what this repo found
    by shipping one (`cc_tasks/2026-09-12_publish_l0_RESULT.md` §5).
    """
    held, ephemeral, dead = [], [], []
    for name, r in sorted(_published_provenance(session).items()):
        if r["path"] and (REPO / r["path"]).exists():
            held.append(name)
        elif r["materialized"] is False and r["derivable_from"] and r["command"]:
            assert (REPO / r["derivable_from"]).is_file(), (
                f"{name} is declared derivable_from {r['derivable_from']}, which the repository "
                f"does not hold either; the chain still ends nowhere")
            ephemeral.append(name)
        else:
            dead.append(f"{name} -> {r['path']} (materialized={r['materialized']!r}, "
                        f"derivable_from={r['derivable_from']!r}) "
                        f"depended on by {sorted(r['dependents'])[:4]}")
    assert not dead, (
        "published Result(s) name provenance the repository does not hold and the registry does "
        "not explain:\n  " + "\n  ".join(dead) +
        "\nEither the repository should hold it, or mark the node with "
        "scripts/mark_ephemeral_datafile.py so the derivation is on the graph.")
    # Both branches are asserted, not just whichever happens to exist today.
    assert held, "no published Result has provenance the repository holds; that cannot be right"
    assert ephemeral, (
        "no published provenance path is declared ephemeral. If the last one was materialised "
        "that is good news and this assertion is what should be deleted — deliberately, in a "
        "task, with the reason on the face of it — rather than left passing vacuously.")


def test_an_ephemeral_datafile_re_derives_and_reproduces_its_dependent_values(session):
    """The other half of decision 2: `materialized: false` is a CLAIM that the value is still
    reachable, and this is the run that shows it.

    Drives the general path — `rederive_tagged_results.rederive_ephemeral`, which reads the set
    of ephemeral DataFiles and each one's `derivation_command` off the graph and names no
    generator — then compares what the generator would register today against what the registry
    holds for every Result that depends on it.
    """
    import rederive_tagged_results as rd
    ephemeral = rd.ephemeral_data_files()
    if not ephemeral:
        pytest.skip("no DataFile is marked materialized: false")

    captured = rd.Captured()
    ran = rd.rederive_ephemeral(captured)
    assert {r["data_file"] for r in ran} == {d["name"] for d in ephemeral}
    for r in ran:
        assert Path(r["path"]).name in r["wrote_into_temporary_tree"], (
            f"{r['generator']} did not write {r['path']} into the temporary tree")
        assert not (REPO / r["path"]).exists(), (
            f"re-deriving {r['data_file']} materialised {r['path']}, whose absence is a "
            f"recorded decision")

    names = [d["name"] for d in ephemeral]
    dependents = session.run(
        "MATCH (r:Result)-[:COMPUTED_FROM]->(d:DataFile) "
        "WHERE d.name IN $names AND r.state <> 'superseded' "
        "RETURN r.name AS name, r.value AS value", names=names).data()
    assert dependents, f"nothing depends on {names}; the check would pass vacuously"

    # A dependent this derivation YIELDS must agree with the registry. A dependent it does not
    # yield is not waved through: it has to be one the standing re-derivation gate covers, i.e.
    # a Result the report tags, which `scripts/rederive_tagged_results.py` re-derives on every
    # run. The gap is real and is a registry imprecision rather than a hole in this check:
    # `fss_scan_netlocs_contacted_2026-09-10` is COMPUTED_FROM this DataFile and its
    # GENERATED_BY names `scan_report`, but the function that computes it lives in
    # `register_l0_report_results.netlocs_contacted` — `cycle_results.register` takes one script
    # per batch, and `scripts/register_measured_collection_facts.py` registered it in the
    # `scan_report` batch. Recorded in `cc_tasks/2026-09-13_ephemeral_provenance_RESULT.md`.
    covered = set(rd.tagged_names())
    drift, unreachable = [], []
    for d in dependents:
        got = captured.get(d["name"])
        if got is None:
            if d["name"] not in covered:
                unreachable.append(d["name"])
        elif got != float(d["value"]):
            drift.append(f"{d['name']}: registry {d['value']}, re-derived {got}")
    assert not drift, (
        "an ephemeral DataFile's dependent Result(s) did not reproduce from the derivation the "
        "registry names, so the path is absent AND the value is unreachable:\n  "
        + "\n  ".join(drift))
    assert not unreachable, (
        f"{unreachable} depend on an ephemeral DataFile, are not produced by the derivation the "
        f"registry names for it, and are not in the tagged set the standing re-derivation gate "
        f"covers either. Nothing re-derives them.")
    assert any(captured.get(d["name"]) is not None for d in dependents), (
        f"the derivation of {names} reproduced none of its own dependents; it may have run but "
        f"it has not been shown to derive anything the registry holds")


def test_the_published_record_separates_a_decided_absence_from_a_defect():
    """Decision 3. One bucket said only "missing"; two buckets say which kind."""
    doc = json.loads((DATA / "results_tagged.json").read_text(encoding="utf-8"))
    assert doc["provenance_paths_absent"] == [], (
        f"the published data names provenance paths that are neither held nor explained: "
        f"{doc['provenance_paths_absent']}")
    for e in doc["provenance_paths_ephemeral"]:
        assert e["derivable_from"] and e["derivation_command"] and e["generated_by"], (
            f"{e['path']} is published as ephemeral with no derivation; that is the dead path "
            f"again with a friendlier key")
        assert e["depended_on_by"], f"{e['path']} is published as ephemeral and nothing uses it"
        assert (REPO / e["derivable_from"]).is_file()
    # Every reference row carries the derivation too, so a reader who never scrolls to the
    # top-level buckets still finds it beside the Result that needs it.
    for r in doc["results"]:
        for ref in r["computed_from"] + r["generated_by"]:
            if ref["present_in_repository"]:
                continue
            assert ref.get("ephemeral") and ref.get("derivation_command"), (
                f"{r['name']} names {ref['path']}, which is not in the repository and carries "
                f"no derivation on its own row")


# ------------------------------------------------------------------------------ the licences

LICENSES = {"license_code": "LICENSE", "license_data": "LICENSE-DATA"}


def test_both_licence_texts_exist_and_the_declaration_names_them():
    """ADDENDUM_1 decision A5. Two licences because this repository publishes two things: the
    code that measures and the measurements. A declared licence with no text is a claim without
    a grant, and a text nothing declares is invisible to every machine that looks."""
    for key, filename in LICENSES.items():
        path = REPO / filename
        assert path.is_file(), f"{filename} is missing and {key} declares it"
        assert PUB[key], f"publication.yaml declares no {key}"
        assert PUB[key] in path.read_text(encoding="utf-8"), (
            f"{filename} does not carry the SPDX identifier {PUB[key]!r} the declaration names")
    assert "MIT License" in (REPO / "LICENSE").read_text(encoding="utf-8")
    data = (REPO / "LICENSE-DATA").read_text(encoding="utf-8")
    assert "Creative Commons Attribution 4.0 International Public License" in data, (
        "LICENSE-DATA does not carry the CC BY 4.0 legal code, only a reference to it")


def test_both_spdx_identifiers_reach_every_generated_consumer():
    """The declaration is read by three generated consumers and none of them may drop half of
    it. CFF and Zenodo each carry ONE licence field, which is the licence of the artefact they
    cite — the data — so the code licence rides in their notes rather than vanishing."""
    cff = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    zen = (REPO / ".zenodo.json").read_text(encoding="utf-8")
    index = (SITE / "index.html").read_text(encoding="utf-8")
    for consumer, text in (("CITATION.cff", cff), (".zenodo.json", zen), ("index.html", index)):
        for key in LICENSES:
            assert PUB[key] in text, f"{consumer} does not state {key} ({PUB[key]})"
    assert yaml.safe_load(cff)["license"] == PUB["license_data"]
    assert json.loads(zen)["license"] == PUB["license_data"]


def test_the_corpus_exclusion_is_stated_wherever_the_licences_are():
    """ADDENDUM_1 decision A3. `corpus/` holds third-party documents retained as evidence; the
    one thing this repository must never appear to license is somebody else's work. One
    sentence, one source — `publication.yaml` — and it travels with the corpus manifest's
    published copy as well as with the licence texts."""
    sentence = _flat(PUB["license_corpus_note"])
    assert sentence
    for where, text in (("LICENSE", (REPO / "LICENSE").read_text(encoding="utf-8")),
                        ("LICENSE-DATA", (REPO / "LICENSE-DATA").read_text(encoding="utf-8")),
                        ("CITATION.cff", (REPO / "CITATION.cff").read_text(encoding="utf-8")),
                        (".zenodo.json", (REPO / ".zenodo.json").read_text(encoding="utf-8")),
                        ("index.html", (SITE / "index.html").read_text(encoding="utf-8"))):
        assert sentence in _flat(text), f"{where} does not carry the corpus exclusion sentence"
    corpus_copy = [c for c in MANIFEST["copies"] if c["source"].startswith("corpus/")]
    assert corpus_copy, "the corpus manifest is no longer published; this check is stale"
    for c in corpus_copy:
        assert _flat(c.get("license_note", "")) == sentence, (
            f"{c['published']} is published without the corpus exclusion on its own entry")
    assert MANIFEST["license"]["code"]["spdx"] == PUB["license_code"]
    assert MANIFEST["license"]["data"]["spdx"] == PUB["license_data"]
