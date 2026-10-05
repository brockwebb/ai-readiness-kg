# DCAT-002: DCAT-US 3.0 and its statistical prior art into ai-readiness-kg; indicator G4 brought current

**Due:** before Thursday 2026-10-08. The operator meets on DCAT-US 3.0 and wants these documents queryable here.
**Implements:** `docs/design/2026-10-04_DN-011_dcat_us_3_intake.md`, DN-011-R2 and DN-011-R3. Commit DN-011 with this
task's first commit.
**Read first:** DN-011, `CLAUDE.md` and the repository's corpus admission path (its runbook or DD notes). The corpus already
holds `dcat-us-3-dataset-schema` and `dcat-us-1-1-schema`. Glob and read sibling `*DCAT-002*ADDENDUM*.md`.
**Model spend:** whatever the admission path's extraction spends, under the repository's `kg/spend.py` controls.
Report estimate and actual.
**Network:** fetch the public documents below; git push.

1. **Catalog** all nine through the corpus machinery, zero spend first. Never hand-edit `corpus/manifest.json`.
   1. DCAT-US 3.0 overview: https://resources.data.gov/resources/dcat-us3/
   2. Agency Implementation Guide: https://resources.data.gov/assets/documents/dcat-us-3-implementation-guide.pdf
   3. M-25-05 crosswalk: https://resources.data.gov/resources/dcat-us-3-crosswalk/
   4. Quality and Governance: https://resources.data.gov/standards/catalog/dcat-us-3/quality-governance/
   5. Temporal, Spatial and Metrics (QualityMeasurement): https://resources.data.gov/standards/catalog/dcat-us-3/temporal-spatial-metrics/
   6. Dataset Series: https://resources.data.gov/standards/catalog/dcat-us-3/dataset-series/
   7. The earlier DCAT-US 3 working draft: https://doi-do.github.io/dcat-us/ . Keep it a distinct document from the
      final, so draft and final can be compared. It is richer: describedBy and the geographic bounding box are
      Recommended, and it has a DQV data-quality section.
   8. StatDCAT-AP 1.0.1, the EU statistical application profile of DCAT-AP (`stat:dimension`, `stat:attribute`,
      `statUnitMeasure`, `numSeries`, `dqv:hasQualityAnnotation`, SDMX mapping): https://interoperable-europe.ec.europa.eu/collection/semic-support-centre/solution/statdcat-application-profile-data-portals-europe/release/101
   9. W3C Data Quality Vocabulary: https://www.w3.org/TR/vocab-dqv/
2. **Admit** what the repository's criterion passes; a decline is recorded with its reason.
3. **Bring G4 current.**
   - Indicator G4 checks issuing authority in the DCAT-US fields `publisher`, `bureauCode` and `programCode`.
   - In DCAT-US 3.0, `publisher` is Recommended, and `bureauCode` and `programCode` are outside the core schema
     (tolerated, not defined). Source: https://resources.data.gov/standards/catalog/dcat-us-3/dataset/
   - Change G4 through the repository's own change path for framework records, citing that page. Do not edit an
     accepted record in place. Report what changed and any scan results it affects.
4. **Check by query.** Run `search_text` for "hasQualityMeasurement", "DatasetSeries" and "stat:dimension" and report
   the hits.
5. **Close.** Suite green, commit, push, `seldon cc complete`. Write a short delivery report: admitted or declined
   with reasons, the G4 change, and spend.
