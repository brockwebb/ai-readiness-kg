# CC Task: the readiness brief for the 2026-10-16 working group: why, what the public client never does, the sixteen checks in one table, results by agency, and each body's API terms

**Date:** 2026-10-16
**Project:** ai-readiness-kg
**Authored by:** Desktop session.
**Implements:** `docs/design/2026-10-15_DN-016_readiness_diagnostic_package_and_client_ladder.md` (DN-016; verified PASS sha256 7a90b518ab20, committed 976a4346), DN-015.
**Amended by:** none.
**Builds on:** task b6c65bfe and its RESULT: the sixteen MeasurementSpecs with their plain-language fields, `scripts/apply_instrument_fields.py`, `scripts/diagnostic_package_build.py` (build pattern, font, colour, vocabulary and digit checks), the record-derived cascade regeneration (b6c65bfe premise 3, commit 04b948b4). Task ba40cb29 (v3) and the audit db464d5f: `reports/summary/grid.json`, `scripts/summary_grid.py`, the four-state rule, the audit RESULT's Part D counts (four scored checks, 64 cells: 41 not measured, 15 fail, 8 pass; BLS, ORES, BTS, EIA, NASS wholly not measured).
**Supersedes for this meeting:** the 20-page dictionary is kept as the reference; this brief is what the operator hands out. Nothing in `reports/diagnostic/` is overwritten.
**Framework layer served (DN-005 §5 rule 1):** §2.1, a view of the framework for a non-technical reader.
**Fulfils:** its own ResearchTask. **Hand-dispatched** by the operator (DN-006 decision 10); not launched by the dispatcher.
**After:** none
**Model:** author
**Spend:** est. 1.5M tokens. The session writes (role `author`). Page one is read once by role `critic` with the hostile reader's three questions. Role `judge` is not used: it resolves to `claude-fable-5-1`, which returned HTTP 429 `model_requires_usage_credits` on 2026-10-15 (`cc_tasks/2026-10-15_executive_summary_v4_instrument_page_two_RESULT.md`).
**Parts:** A 0.55, B 0.35, C 0.10.
**Part map:** A is the brief's first three pages and their slides; B is the API table; C is the gate.
**Network:** Part B only: WebSearch, and WebFetch to `.gov` hosts. This is desk research by the session, not a measurement by the public client, and the brief labels it so.

**HEADLESS NOTICE.** No next turn. Poll every detached command to its EXIT line.

**Deadline and order.** The operator presents at about 11:00 America/New_York on 2026-10-16. Part A is built, committed and pushed first. Part B starts only after. If Part B cannot finish by 10:40, the Part A brief stands and the RESULT says where B stopped. No partial Part B is committed.

## Step 0

1. The dispatcher must not race this session. Set `dispatch.enabled: false` in `seldon.yaml`, commit that one path, and quote the commit. Then `seldon cc register cc_tasks/2026-10-16_readiness_brief.md` and quote the id. (The file is committed but unregistered, so the dispatcher cannot have launched it.)
2. Confirm the served model equals `seldon models resolve author`; a mismatch stops the task as `model_substituted`.
3. Verify and quote: b6c65bfe `completed`; `get_overview` reports `projection_gate.status: green`; `reports/summary/grid.json` exists and reproduces the audit's Part D counts for the four scored checks.

## Vocabulary and style (every rendered word)

The run is a *readiness diagnostic*; the unit is a *check*; the actor is the *public client*. The states are pass, partial, fail and *not measured*. "Scan", "probe", "crawl", "audit", "ports" and "unmeasurable" appear nowhere. No em dashes or en dashes used as dashes. No phrase repeated across rows: each cell says its own thing. No sentence telling the reader where results go. Plain words; a cell that needs a glossary entry is rewritten instead.

## Part A: the brief (Word, four pages; the same content as slides)

**Page one: why, who, never.**

Why, three short paragraphs, in this order:
1. No new burden. The diagnostic uses what agencies already publish on their public websites. It needs no survey, no data call and no agency staff time.
2. The public data user is the customer. A machine is now one of the main ways members of the public reach federal data, so the diagnostic takes the machine's view as the public's proxy, to show what their experience is and how it could improve.
3. Anyone can do this. Any member of the public with a laptop can make the same requests. The diagnostic writes the questions and the method down, so the answer does not depend on who asks.

Who: the public client, in two sentences: it identifies itself by one fixed name in every request (the user-agent string, quoted from `assessment/harness/scan/params.yaml`, with one line noting the string still carries the earlier word "scanner" and is kept so a log search finds every request), and it holds to the standing rate limit (a result token).

Never, five short lines: no sign-in or password; no form filled in; no challenge or CAPTCHA solved and no block worked around; no page scripts run; nothing taken beyond what the page itself serves. Then one line on *not measured*: the client could not look, and the footnote says why; it is never counted as a fail.

**Pages one and two: the sixteen checks in one table.** Grouped by criterion, in this order, with the plain criterion word as a group header: Accessible (12 checks), Understandable (1), Open (2), Release (1). Read the grouping from the spec ids and `AssessmentCriterion` nodes; do not type it. Within a group, scored checks first, each marked "Scored"; the rest marked "Shown, not scored", with A4 and A11 marked "Declaration" and A12 "Under review". Four columns:

- **Check:** the plain name.
- **What we ask your site for:** one sentence naming the file or page requested, as a person would say it. Where it is true, say who else routinely asks for the same thing (search engines request robots.txt and sitemaps as a matter of course).
- **What it tells us:** one sentence.
- **Why it matters:** one sentence naming the source in plain words (an OMB memo, a W3C practice, a FAIR principle, USAFacts' guide), or "this project's rule".

The author writes the two new short fields (`ask_plain`, `tells_plain`) for each of the sixteen specs and writes them back through `scripts/apply_instrument_fields.py` and `framework_writeback.save`, so the table is a query over the record. "Why it matters" is shortened from the existing field, and the shortened text is written back as `why_short`. One write-back, one cascade regeneration.

**Page three: results by agency.** Sixteen bodies by the four scored checks, from `reports/summary/grid.json` for the cycle of record, cells Pass, Partial, Fail or Not measured. Body names in full with the code beside them, from the record's body nodes or the frame, never typed from memory. Three flagships below a rule, as reference hosts. Every Not measured cell carries a footnote mark; footnotes give the reason class in plain words (the website refused the identified client; the site's robots.txt asked the client not to fetch the page; the client could not confirm an absence, or a server or network error stopped it) and, where the raw receipts under `events/raw/` carry it, the HTTP status the host returned (for example "refused, HTTP 403" or "served a bot-challenge page"). Read the receipts to find out whether they carry it before printing any status; if they do not, the footnote gives the reason class only and the RESULT says so. One summary line above the table, every number a result token: the cell counts by state and the bodies wholly not measured. Register those counts with `seldon result register`, generated by the build script from `grid.json`, before the brief cites them.

**Slides.** Title; why (one slide); the public client and what it never does (one); the check table (two slides, the Accessible group on one, the rest on the other); results by agency (one); the API table (one, from Part B, or a slide saying it follows next week if B does not finish). Calibri, white background, black or grey text, orange accent only. Speaker notes on the results slide name each footnote's reason.

**Read.** Role `critic` reads page one once with three questions: what would I object to; what word would I not understand; what would I say we were secretly doing. Answers go in the RESULT verbatim. A word flagged as not understood is replaced; an objection is recorded, not rewritten.

Build with a new script `scripts/readiness_brief_build.py` patterned on `scripts/diagnostic_package_build.py`, writing `reports/diagnostic/brief/READINESS_BRIEF.md`, `.docx` and `.pptx`. No PDF. Commit path-scoped, push.

- check: the .docx body is at most four pages and the .pptx at most eight slides; quote both counts.
- check: the build's font, colour, vocabulary, digit and dash checks pass on all three files; quote them.
- check: a grep of the Markdown for each banned word and for U+2014 returns zero lines; quote it.
- check: the results table reproduces the audit's Part D counts (64 cells: 41, 15, 8) as a regression test; quote it.
- check: every table cell on pages one to three comes from a graph query or `grid.json`; the build script exits non-zero on a missing field.

## Part B: each body's API, and whether a machine can find it

For each of the sixteen bodies and three flagships, from the agency's own pages only (fetch and quote; a model's answer is not evidence):

- **API:** name and base address, or "no public API found" with the pages searched.
- **How a machine calls it:** no key; a key in the address or header; a key required above a stated limit (give the limit).
- **How a key is obtained:** what the registration asks for (an email, an organization name) and whether it ends in an email step a person completes. State plainly where a person must complete a step; the public client never does.
- **What a key changes:** limits and features, as the agency states them.
- **Where it is announced to machines:** whether the agency serves a developer page (`/developer` or `/developers`), whether its `data.json` inventory lists the API, whether `/.well-known/api-catalog` is served, and whether the roster's data page links to it. Each yes or no with the URL fetched. This is the "how would anyone know it exists" column.
- **Source:** URL and a verbatim passage for each term.

Seeds found by the Desktop session on 2026-10-16, to fetch and quote, not to copy: BLS `https://www.bls.gov/developers/api_faqs.htm`; Census `https://www.census.gov/data/developers/guidance/api-user-guide/help.html`; BEA `https://apps.bea.gov/api/bea_web_service_api_user_guide.htm`; EIA `https://www.eia.gov/opendata/register.php`; NASS `https://quickstats.nass.usda.gov/api/`. Also check whether each body's key is issued through api.data.gov, GSA's shared key service, and say so where it is.

Write the facts to `reports/diagnostic/brief/api_terms.yaml` (one entry per body, every term with URL and passage) and register it as a DataFile. Writing them to the record's Tool and Precondition nodes is a follow-on task, named in the RESULT, not done here (no second cascade under the deadline). Render the table as page four and its slide, titled "Each body's public data interface", with one line under it: "Confirmed from each agency's own pages on 16 October 2026; desk research, not a measured check." Wherever no official page states a term, the cell says "not stated".

- check: every row cites a URL and passage per term or says "not stated"; a script exits non-zero otherwise; quote it.
- check: the BLS row states both API versions' terms and the announcement column; quote the row.

## Part C: gate

`make gate-task` (Part A writes the record), `seldon verify`, protected-paths diff showing only the authorized write-back and its events. Leave `dispatch.enabled: false`; the operator turns it back on.

## RESULT

Under 40 lines: served model; dispatcher-off commit and registration id; the write-back delta; whether receipts carry HTTP status; page and slide counts; the critic's reading verbatim; the results summary line with its result ids; Part B row counts (API with terms, no API found, not stated), how many bodies announce their API in none of the four places, and the BLS row; checks and gates with log paths; where it stopped, if it stopped; follow-on: API terms into the record. Then `seldon cc complete`, commit, push. The operator opens `reports/diagnostic/brief/READINESS_BRIEF.docx` first.
