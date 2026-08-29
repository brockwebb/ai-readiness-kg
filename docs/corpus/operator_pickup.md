# Operator pickup list

Things only a human can get. **Projected by `scripts/t1_build_index.py --phase pickup` — do not hand-edit.** Regenerated alongside `manifest_table.md`.

Ordered by `t2_priority` (crosswalk demand, then T0 centrality). That ordering is **provisional — T0 coverage 38/178**; the demand component is coverage-independent and already final, the centrality component is not. `python -m kg.biblio resume` refreshes both.

| doc / candidate | state | why | best-known URL | demand | centrality | detail |
|---|---|---|---|---|---|---|
| `advancing-american-ai-act-ndaa-fy2023-div-g` | fidelity: degraded | Docling could not convert this PDF; text came from pypdf, the converter DD-023 names as damaged. A clean or born-digital copy would restore layout fidelity. | https://www.govinfo.gov/app/details/PLAW-117publ263 | 0 | 0 |  |
| `ai-real-toolkit-ai-readiness-assessment-guide` | fidelity: degraded | Docling could not convert this PDF; text came from pypdf, the converter DD-023 names as damaged. A clean or born-digital copy would restore layout fidelity. | https://ai-real.dco.org/assets/frontend/images/AI-Readiness-Assessment-Guide.pdf | 0 | 0 |  |
| `commerce-generative-ai-open-data-guidelines` | acquisition_blocked | HTTP 403 to every client tried on 2026-08-29: curl with a browser User-Agent (403), the PDF path under commerce.gov/sites/default/files (403), data.commerce.gov (403), and WebFetch (403). The 5,801-byte body returned is a Cloudflare interstitial ('Just a moment... Enable JavaScript and cookies to co | https://www.commerce.gov/news/blog/2025/01/generative-artificial-intelligence-and-open-data-guidelines-and-best-practices | 0 | 0 |  |
| `foundations-for-evidence-based-policymaking-act-of-2018-evid` | fidelity: degraded | Docling could not convert this PDF; text came from pypdf, the converter DD-023 names as damaged. A clean or born-digital copy would restore layout fidelity. | https://www.govinfo.gov/app/details/PLAW-115publ435 | 0 | 0 |  |
| `webb-fcsm-nist-crosswalk` | fidelity: degraded | Docling could not convert this PDF; text came from pypdf, the converter DD-023 names as damaged. A clean or born-digital copy would restore layout fidelity. | https://doi.org/10.5281/zenodo.18772590 | 0 | 0 | `state/convert_errors/webb-fcsm-nist-crosswalk.err.txt` |

## Not listed here

Closed-access candidates from the coupling expansion: the candidate list (`acquisition_candidates.md`) currently reaches no work cited by 3+ corpus members, because reference lists exist for only 2 of 178 documents. When `kg.biblio resume` lifts T0 coverage, re-run this phase and the closed-access candidates will appear.
