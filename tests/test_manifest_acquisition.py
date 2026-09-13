"""Acquisition provenance on the real corpus manifest, and the correction verb that writes it.

`cc_tasks/2026-09-12_cited_documents_metadata_2.md` decision 4, corrected against what the
ledger actually holds (see that task's RESULT §1).

The task asked for "no null `acquired_at` on every entry". That is not the right invariant and
the ledger says so: 93 of 377 entries are `screening_imported` candidates the corpus never
acquired — stage `cataloged`, no canonical path, no `file_observed` event of any kind. A
timestamp on those would be invented, and dixie's doctrine is that a field may be null and may
not be guessed. The invariant that IS right, and that these tests hold:

    an entry the ledger attests a file for carries the time it was attested.

Before 2026-09-12 that held for 0 of 284 such entries, because only `_on_inbox_ingested` wrote
the field and this ledger has no inbox events at all.

These read the real `corpus/manifest.json`. The refusal cases call `metadata_update` against
the real ledger; every one of them raises before anything is appended, so they write nothing.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from kg import manifest as M

REPO = Path(__file__).resolve().parents[1]
ENTRIES = json.loads((REPO / "corpus" / "manifest.json").read_text(encoding="utf-8"))["entries"]

#: A document admitted from here on must name the channel it came through. `unknown` is the
#: blank template's value and `attested_by_file_observed` is the projection's fallback for the
#: pre-2026-09-12 corpus — neither is a channel, and a new admission that lands on one means a
#: connector stopped recording how it fetched.
METHOD_REQUIRED_FROM = "2026-09-12"
_FALLBACK_METHODS = ("unknown", "attested_by_file_observed")


def _acquired(entry: dict) -> bool:
    """The ledger attests that bytes for this entry were on disk, at any point.

    Not just `canonical_path`: a document whose only file was quarantined with no verified
    alternate has its canonical cleared, and it was still acquired — the acquisition time
    stays true after the file is taken away.
    """
    return bool(entry["identity"].get("canonical_path")
                or entry["extra"].get("observed_files")
                or entry["files"].get("quarantined"))


def test_every_acquired_entry_carries_an_acquisition_time():
    missing = sorted(d for d, e in ENTRIES.items()
                     if _acquired(e) and not e["acquisition"].get("acquired_at"))
    assert not missing, (
        f"{len(missing)} entries have a file on disk and no acquired_at — the ledger holds "
        f"the timestamp and the projection is dropping it: {missing[:10]}")


def test_an_entry_with_no_file_is_null_rather_than_guessed():
    """The other side of the same invariant: never-acquired entries are not backfilled."""
    invented = sorted(d for d, e in ENTRIES.items()
                      if not _acquired(e) and e["acquisition"].get("acquired_at"))
    assert not invented, (
        f"{len(invented)} entries have an acquisition time and no file the ledger ever saw; "
        f"that timestamp came from somewhere other than an attestation: {invented[:10]}")


def test_an_acquisition_time_never_stands_beside_an_unknown_method():
    both = sorted(d for d, e in ENTRIES.items()
                  if e["acquisition"].get("acquired_at")
                  and e["acquisition"].get("method") == "unknown")
    assert not both, (
        f"{len(both)} entries are timestamped as acquired but claim the method is unknown — "
        f"the two fields are written by the same attestation: {both[:10]}")


def test_documents_admitted_from_2026_09_12_name_their_acquisition_channel():
    late = sorted(d for d, e in ENTRIES.items()
                  if (e["acquisition"].get("acquired_at") or "") >= METHOD_REQUIRED_FROM
                  and e["acquisition"].get("method") in _FALLBACK_METHODS)
    assert not late, (
        f"{len(late)} entries acquired on or after {METHOD_REQUIRED_FROM} carry a fallback "
        f"method instead of the channel they came through: {late[:10]}")


# ------------------------------------------------------- the correction verb's refusals ----
# Each of these raises before any append; the ledger is not written by this module.

def test_metadata_update_refuses_a_doc_id_the_ledger_does_not_hold():
    with pytest.raises(M.ManifestError, match="not in the corpus ledger"):
        M.metadata_update("no-such-document-anywhere", provenance="page 1",
                          identity={"pub_year": "2020"})


@pytest.mark.parametrize("section", ["screening", "lifecycle", "integrity", "extra"])
def test_metadata_update_refuses_a_section_outside_identity_and_acquisition(section):
    with pytest.raises(M.ManifestError, match="is not correctable"):
        M.metadata_update("rfc-9309-robots-exclusion-protocol", provenance="page 1",
                          **{section: {"decision": "included"}})


def test_metadata_update_refuses_a_field_the_entry_does_not_have():
    with pytest.raises(M.ManifestError, match="not a field of the manifest entry"):
        M.metadata_update("rfc-9309-robots-exclusion-protocol", provenance="page 1",
                          identity={"pub_yr": "2022"})


@pytest.mark.parametrize("provenance", ["", "   "])
def test_metadata_update_refuses_a_correction_with_no_provenance(provenance):
    with pytest.raises(M.ManifestError, match="provenance is required"):
        M.metadata_update("rfc-9309-robots-exclusion-protocol", provenance=provenance,
                          identity={"pub_year": "2022"})


def test_metadata_update_refuses_an_empty_section():
    with pytest.raises(M.ManifestError, match="non-empty mapping"):
        M.metadata_update("rfc-9309-robots-exclusion-protocol", provenance="page 1",
                          identity={})


@pytest.mark.parametrize("assignment,match", [
    ("identity.pub_year", "SECTION.FIELD=VALUE"),
    ("pub_year=2022", "must be SECTION.FIELD"),
])
def test_the_cli_set_parser_refuses_a_malformed_assignment(assignment, match):
    with pytest.raises(M.ManifestError, match=match):
        M._parse_set(assignment, None)


def test_the_cli_set_parser_keeps_values_as_strings_and_splits_lists():
    assert M._parse_set("identity.pub_year=2022", None) == ("identity", "pub_year", "2022")
    assert M._parse_set("identity.authors_or_org=A,B", None) == (
        "identity", "authors_or_org", ["A", "B"])
    assert M._parse_set("identity.title=Data Quality, Revisited", False) == (
        "identity", "title", "Data Quality, Revisited")
