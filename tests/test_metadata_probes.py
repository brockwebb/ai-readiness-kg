"""D3/D4 probes that score a single DCAT dataset record (pure, no network)."""
from harness.records import Score, Track
from harness.probes.d3_metadata_standard import MetadataStandardProbe
from harness.probes.d3_provenance import ProvenanceProbe
from harness.probes.d3_schema import SchemaProbe
from harness.probes.d3_access_tier import AccessTierProbe
from harness.probes.d4_versioning import VersioningProbe
from harness.probes.d4_cadence import CadenceProbe
from harness.probes.d4_license import LicenseProbe
from harness.probes.d4_integrity import IntegrityProbe


RICH = {
    "title": "Resident Population",
    "description": "Annual estimates.",
    "identifier": "https://x.gov/d/pop",
    "keyword": ["population"],
    "modified": "2026-01-15",
    "issued": "2010-01-01",
    "publisher": {"name": "Census Bureau"},
    "contactPoint": {"fn": "Data Desk", "hasEmail": "mailto:data@x.gov"},
    "accessLevel": "public",
    "license": "https://creativecommons.org/publicdomain/zero/1.0/",
    "rights": None,
    "accrualPeriodicity": "R/P1Y",
    "bureauCode": ["006:07"],
    "programCode": ["006:002"],
    "distribution": [
        {"mediaType": "text/csv", "downloadURL": "https://x.gov/pop.csv",
         "describedBy": "https://x.gov/pop-schema.json"},
    ],
}

SPARSE = {"title": "Mystery dataset"}

RESTRICTED_NO_REASON = {"title": "R", "accessLevel": "restricted public"}
RESTRICTED_WITH_REASON = {
    "title": "R", "accessLevel": "restricted public",
    "rights": "Access restricted under Title 13 U.S.C.; aggregate only.",
}


# --- D3 metadata standard ---------------------------------------------------
def test_metadata_standard_pass_with_dcat_required_fields():
    assert MetadataStandardProbe().evaluate(RICH)[0] == Score.PASS


def test_metadata_standard_fail_when_essentially_absent():
    assert MetadataStandardProbe().evaluate(SPARSE)[0] == Score.FAIL


def test_metadata_standard_is_core_d3():
    assert MetadataStandardProbe().track is Track.CORE
    assert MetadataStandardProbe().dimension == "D3"


# --- D3 provenance ----------------------------------------------------------
def test_provenance_pass_with_publisher_and_modified():
    assert ProvenanceProbe().evaluate(RICH)[0] == Score.PASS


def test_provenance_partial_with_only_one_signal():
    assert ProvenanceProbe().evaluate({"publisher": {"name": "X"}})[0] == Score.PARTIAL


def test_provenance_fail_with_neither():
    assert ProvenanceProbe().evaluate(SPARSE)[0] == Score.FAIL


# --- D3 schema (folds in semantic-clarity + units/types: all need the schema) -
def test_schema_pass_when_distribution_describedby_present():
    assert SchemaProbe().evaluate(RICH)[0] == Score.PASS


def test_schema_fail_when_no_described_by_anywhere():
    assert SchemaProbe().evaluate(SPARSE)[0] == Score.FAIL


# --- D3 access-tier metadata ------------------------------------------------
def test_access_tier_pass_when_public_level_declared():
    assert AccessTierProbe().evaluate(RICH)[0] == Score.PASS


def test_access_tier_pass_when_restricted_with_machine_readable_reason():
    assert AccessTierProbe().evaluate(RESTRICTED_WITH_REASON)[0] == Score.PASS


def test_access_tier_partial_when_restricted_without_reason():
    assert AccessTierProbe().evaluate(RESTRICTED_NO_REASON)[0] == Score.PARTIAL


def test_access_tier_fail_when_no_access_level():
    assert AccessTierProbe().evaluate(SPARSE)[0] == Score.FAIL


# --- D4 versioning ----------------------------------------------------------
def test_versioning_pass_with_modified_date():
    assert VersioningProbe().evaluate(RICH)[0] == Score.PASS


def test_versioning_partial_with_only_issued():
    assert VersioningProbe().evaluate({"issued": "2010-01-01"})[0] == Score.PARTIAL


def test_versioning_fail_without_dates():
    assert VersioningProbe().evaluate(SPARSE)[0] == Score.FAIL


# --- D4 cadence -------------------------------------------------------------
def test_cadence_pass_with_accrual_periodicity():
    assert CadenceProbe().evaluate(RICH)[0] == Score.PASS


def test_cadence_fail_without_accrual_periodicity():
    assert CadenceProbe().evaluate(SPARSE)[0] == Score.FAIL


# --- D4 license -------------------------------------------------------------
def test_license_pass_with_license_url():
    assert LicenseProbe().evaluate(RICH)[0] == Score.PASS


def test_license_partial_with_only_rights_prose():
    assert LicenseProbe().evaluate({"rights": "public domain"})[0] == Score.PARTIAL


def test_license_fail_without_license_or_rights():
    assert LicenseProbe().evaluate(SPARSE)[0] == Score.FAIL


# --- D4 integrity -----------------------------------------------------------
def test_integrity_pass_with_checksum():
    ds = {"distribution": [{"downloadURL": "https://x.gov/a.csv",
                            "checksum": "sha256:abc"}]}
    assert IntegrityProbe().evaluate(ds)[0] == Score.PASS


def test_integrity_partial_with_canonical_identifier_only():
    ds = {"identifier": "https://doi.org/10.1234/x", "landingPage": "https://x.gov/d"}
    assert IntegrityProbe().evaluate(ds)[0] == Score.PARTIAL


def test_integrity_fail_with_neither():
    assert IntegrityProbe().evaluate(SPARSE)[0] == Score.FAIL
