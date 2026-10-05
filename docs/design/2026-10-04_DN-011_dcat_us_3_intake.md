# DN-011: DCAT-US 3.0 enters both policy graphs before the operator's Thursday meeting; G4 is brought current

**Date:** 2026-10-04. Desktop session. Implemented by DCAT-001 (icsp_notebook, fss-policy-kg) and DCAT-002 (this
repository).

## Context

The operator was asked by a colleague to brief OMB on DCAT-US 3.0 (a 101 and next steps). The colleague's report:
3.0 does not serve findability and fitness-for-use assessment for statistical uses, because the minimum elements omit
what FCSM advocated, and the FCSM members who worked on it have left.

Checked against the published schema (https://resources.data.gov/standards/catalog/dcat-us-3/dataset/):
- Only `title`, `description`, `identifier` and `contactPoint` are Mandatory.
- `hasQualityMeasurement`, `provenance`, `wasGeneratedBy`, `conformsTo`, `temporalResolution` and
  `accrualPeriodicity` are Optional.
- v1.1's `dataQuality` is dropped.
- `bureauCode` and `programCode` are outside the core schema.

The earlier working draft (https://doi-do.github.io/dcat-us/) carried more at Recommended and a Data Quality
Vocabulary section. The EU solved the same gap with StatDCAT-AP, a statistical application profile of DCAT-AP.

## Decisions

- **DN-011-R1.** The fss-policy-kg lock of 2026-09-13 is lifted (operator, 2026-10-04). Additions go through its
  admission machinery again.
- **DN-011-R2.** The DCAT-US 3.0 documents enter fss-policy-kg (DCAT-001) and this graph (DCAT-002) before Thursday
  2026-10-08, through each graph's own admission machinery; neither manifest is hand-edited (operator, 2026-10-04).
  - fss-policy-kg gets the overview, the M-25-05 crosswalk and the Implementation Guide. The policy hook is M-25-05's
    Phase 2 guidance pointing agencies to DCAT-US 3.0.
  - This graph gets those three plus the supporting-class pages, Dataset Series, the earlier working draft (kept
    distinct from the final), StatDCAT-AP 1.0.1 and W3C DQV, so that draft-against-final and US-against-EU can be
    queried.
- **DN-011-R3.** Indicator G4 is brought current to DCAT-US 3.0.
  - It checks issuing authority in `publisher`, `bureauCode` and `programCode`.
  - In 3.0, `publisher` is Recommended and the two codes are tolerated but not defined.
  - The change goes through the framework's own change path, citing the 3.0 Dataset page.
