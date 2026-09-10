# Flagship declarations for the agencies pending after scan-frame-fss

**Date:** 2026-09-10 (revised same day: NCSES removed; it had the Annual Business Survey declared in cycle 3 and keeps it. Declarations do not replace an existing flagship.). Desktop declaration. Supersedes "pending operator declaration" in `docs/design/fss_flagship_shortlist.md` for the bodies below.

**Ground.** The inventory (`data.json`) cannot rank products and was right not to. A different source does: OMB's annual *Statistical Programs of the United States Government* lists each recognized agency's principal programs, and each agency names its principal product on its own site. The flagship declared here is the product the agency itself presents as principal. Where an agency presents a compendium and a data portal, the compendium is declared (it is the product; the portal is a surface of it). One flagship per body, on the body's own site key (DD-063).

**URLs are declared, not yet verified.** The cycle-4 frame task fetches each landing page robots-first under the identified client and records the status; a declared URL that does not resolve is a finding about the declaration and a stop for re-declaration, not a reason to substitute another product silently.

| body | flagship product | landing page (declared) | why this one |
|---|---|---|---|
| DRSMSU (Federal Reserve Board) | Survey of Consumer Finances | https://www.federalreserve.gov/econres/scfindex.htm | The unit's principal survey; the Board's own "Survey of Consumer Finances" program page |
| NAHMSAPHIS | NAHMS national studies | https://www.aphis.usda.gov/aphis/ourfocus/animalhealth/monitoring-and-surveillance/nahms | The program is the product; APHIS presents NAHMS studies as its statistical output |
| NCES | Digest of Education Statistics | https://nces.ed.gov/programs/digest/ | NCES's principal compendium; the Condition of Education is the report, the Digest is the data product |
| SAMHSACBHS | National Survey on Drug Use and Health | https://www.samhsa.gov/data/data-we-collect/nsduh-national-survey-drug-use-and-health | CBHSQ's principal survey by its own description |
| BLS | Consumer Price Index | https://www.bls.gov/cpi/ | The principal federal price statistic; BLS's own flagship designation. Host refuses the identified client; the row is measured as refused, per DD-060 |
| BTS | National Transportation Statistics | https://www.bts.gov/topics/national-transportation-statistics | BTS's principal compendium; TranStats is its portal surface. Host refuses the identified client |
| ORES (SSA) | Annual Statistical Supplement | https://www.ssa.gov/policy/docs/statcomps/supplement/ | ORES's principal compendium. Host refuses the identified client |

Body codes as they appear in `scan_targets_fss_2026-09` v4.

**Operator override.** Any row above may be replaced by naming the product and the URL; the ground column then reads "operator declaration". Nothing here changes cycle 3 or the report built from it; these enter the frame at targets v5 in the cycle-4 frame task.
