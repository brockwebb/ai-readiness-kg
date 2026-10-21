# DN-017: commercial tool trial protocol (Semrush), pre-registered

**Date:** 2026-10-21
**Status:** Draft protocol for the operator to follow by hand. Not a CC task. Becomes the data-gathering step of the tool crosswalk task when registered.
**Depends on:** DN-015 (the sixteen checks and the four states), DN-016 (the public client, the two kinds of user), the scan catalog (task aaffd0db) and the Tool and Precondition nodes (task 8f8861ce).
**Question it answers:** does a commercial web-optimization tool measure anything the readiness diagnostic needs that it does not already measure, get through the hosts the public client could not, or produce a defensible signal for the Understandable and Accurate criteria, which have no automated check today.

## 1. Why pre-register

The operator's time is the scarce resource. The trial is written down before it starts so that every number recorded was decided in advance, the stop rule is fixed, and "it looked interesting" cannot extend it. If the protocol cannot be followed as written, the deviation is recorded and the protocol is amended by ADDENDUM, not improvised. The practice follows the project's own pre-registered gate rule (a failed pre-registered gate triggers investigation, never retuning) and the squiddy extraction design's decision-rule pattern.

## 2. Hypotheses, each with its measure and its decision rule

**H1. Coverage.** Semrush Site Audit measures none of the sixteen checks beyond four: the sitemap (3), the two robots.txt reads (5, 10), structured-data validity (part of 6) and soft-404 handling (9).
Measure: a sixteen-row crosswalk, one row per check, with the Semrush issue or report name that corresponds, graded yes, partial or no, and the Semrush report screen it came from.
Decision: H1 holds if the crosswalk has at most five yes-or-partial rows. If it fails (a sixth check is measured), that check's row becomes a candidate for a "who else runs this" entry in the record, and the crosswalk task is scheduled.

**H2. Access.** Semrush's crawler is refused by the hosts that refused the public client on the cycle of record (BLS, BTS, ORES: all four scored checks not measured, HTTP 403).
Measure: for each of five hosts (www.bls.gov, www.bts.gov, www.ssa.gov, www.census.gov, ncses.nsf.gov), the Site Audit's crawled-page count, its reported crawl errors, and whether the audit completed. Census and NCSES are the controls: both answered the public client.
Decision: H2 holds if the three refusing hosts return under 10 crawled pages or an access-denied class error, and both controls complete. If a refusing host completes for Semrush, the difference in client identity is a finding and the client-identity cycle (ae58c74e) moves up.

**H3. Signal for Understandable and Accurate.** AI Visibility reports give product-level citation data that is reproducible across two runs on consecutive days.
Measure: for five named products (CPI, ACS 1-year, GDP quarterly, unemployment rate, Statistics of Income individual returns), across the engines the toolkit covers, record per run: is the agency cited as a source (yes/no), which URL is cited, and does the headline figure in the engine's answer match the agency's current published value (match / mismatch / no figure given). Run on day one and again on day two, same prompts, same settings.
Decision: H3 holds if citation presence agrees across the two days on at least 4 of 5 products per engine and the figure-match column is fillable from the report without manual prompting. If it holds, a measurement for the Accurate criterion is specified as its own task with its own pre-registration. If it fails, AI Visibility is recorded as not reproducible enough to measure with, and the Accurate criterion stays unmeasured.

## 3. Constraints

- No agency credentials, no keys, no sign-in to any agency site. The tool is pointed at public hosts only, exactly as the public client is.
- Nothing Semrush reports enters the record as a measured check. It is desk research and is labelled so wherever it is quoted (DN-016 ruling on desk research).
- The trial runs on the operator's personal account and personal machine, not on a Census account or device.
- Time box: two sessions of at most ninety minutes, on consecutive days. Day two exists only for the H3 repeat and for anything day one could not finish. A third session needs an ADDENDUM.
- If the free trial does not include the AI Visibility toolkit, H3 is recorded as not testable at this tier, with the plan name and price that would include it, and the trial stops after H1 and H2. Do not buy a tier to test H3; that is a decision with a cost and goes to the crosswalk task.

## 4. Steps, in order

Day one.

1. Create the folder `docs/research/2026-10-21_semrush_trial/` and in it `log.md`. Every step below ends with one line in the log: time, what was done, the file saved. Screenshots and CSV exports go in the same folder, named `NN_<what>.png` or `.csv`.
2. Sign up for the free trial. Record in the log: the plan name, the trial length, the stated limits (projects, pages per audit, AI Visibility included yes or no), and the date the trial ends. Set a calendar reminder to cancel the day before.
3. Create five Site Audit projects, one per host in H2, with the crawl limited to 500 pages, crawl source "website", user agent left at the tool's default, and robots.txt respected (the default; confirm and screenshot the setting). Start all five.
4. While they run, open the Site Audit issue list for the first host that completes and build the H1 crosswalk: for each of the sixteen checks, search the issue catalogue for the corresponding item. Record the Semrush issue name verbatim or "none". Export the issue list as CSV.
5. When all five audits finish or stall (give them one hour), record the H2 table: host, pages crawled, completion status, errors reported. Screenshot each project's overview.
6. If AI Visibility is included: set up the five products as tracked topics or prompts, in the engines offered. Run. Export. Record the H3 day-one table. If it is not included, record that and stop.
7. Write the day-one block in the log: H1 result and verdict, H2 result and verdict, H3 status.

Day two (only if H3 is testable).

8. Re-run the same five AI Visibility prompts with the same settings. Export. Fill the H3 day-two table and the agreement column.
9. Write the day-two block: H3 verdict.
10. Cancel the trial or note the cancellation date.

## 5. What comes out

`docs/research/2026-10-21_semrush_trial/RESULT.md`, under forty lines: the three verdicts with the tables, the deviations from this protocol if any, and one sentence per hypothesis on what it changes. The crosswalk task is registered only if H1 or H3 fails in the direction that adds a measurement. Otherwise the result is recorded, the tool is entered in the scan catalog with its coverage, and the question is closed.

## 6. Out of scope here

The data-quality framing (SI readiness as the accessibility dimension of the FCSM data quality framework, measured for a machine user) is its own design note and prior-art search; it is named in the handoff, not here.

## Prior art

Searched 2026-10-21 through `seldon_prior_art_search`. No prior tool crosswalk exists in any repository (the "scan catalog commercial tool coverage" query is a recorded miss; the scan catalog itself is task aaffd0db). Pre-registration as a practice is held in the library only through papers that apply it (arXiv 2602.22302, 2510.11595); none is a methods source for this protocol, and the project's own gate rule is the governing precedent. The library has no SEO or site-audit literature; the hits for that query are retrieval-agent papers and are recorded as off-topic.

### Internal

- internal receipt: query "pre-registered protocol hypothesis decision rule" | repo seldon@9ea24f12e32634a3474c4276ca6f235f7f979f69 | hits none
- internal receipt: query "pre-registered protocol hypothesis decision rule" | repo squiddy@805e33318f8e7db086a875abe9e189cd94344407 | hits docs/decisions/REGISTER.md:9, docs/EXTRACTION_DESIGN_SPEC.md:342
- internal receipt: query "pre-registered protocol hypothesis decision rule" | repo ai-readiness-kg@3e7cf9ecb38847ac8f9219c671b132e87415cea8 | hits none
- internal receipt: query "pre-registered protocol hypothesis decision rule" | repo arnold@f089fc8c79403a5371c823c6c3f2aec30fa90e57 | hits none
- internal receipt: query "pre-registered protocol hypothesis decision rule" | repo icsp_notebook@97e7fb6d014acc38757928205984a30be1f131f2 | hits none
- internal receipt: query "pre-registered protocol hypothesis decision rule" | repo wintermute@2a78c392f4d998227d2433338ea45aee82c67f1e | hits none
- internal receipt: query "pre-registered protocol hypothesis decision rule" | repo workbench-audit@tree:c03bc86f0e4d7087c6f9cc417ee42ef66f7bc07268d5316448b4344c744b5412 | hits none
- internal receipt: query "scan catalog commercial tool coverage" | repo seldon@9ea24f12e32634a3474c4276ca6f235f7f979f69 | hits none
- internal receipt: query "scan catalog commercial tool coverage" | repo squiddy@805e33318f8e7db086a875abe9e189cd94344407 | hits none
- internal receipt: query "scan catalog commercial tool coverage" | repo ai-readiness-kg@208e3fbd88e74a855686fd3f4dfc5e3bf4e9a304 | hits none
- internal receipt: query "scan catalog commercial tool coverage" | repo arnold@f089fc8c79403a5371c823c6c3f2aec30fa90e57 | hits none
- internal receipt: query "scan catalog commercial tool coverage" | repo icsp_notebook@97e7fb6d014acc38757928205984a30be1f131f2 | hits none
- internal receipt: query "scan catalog commercial tool coverage" | repo wintermute@2a78c392f4d998227d2433338ea45aee82c67f1e | hits none
- internal receipt: query "scan catalog commercial tool coverage" | repo workbench-audit@tree:c03bc86f0e4d7087c6f9cc417ee42ef66f7bc07268d5316448b4344c744b5412 | hits none

### External

- library receipt: query "pre-registered protocol hypothesis decision rule" | release library_graph_20261017_sq018_02_2026-10-17.json sha256:99984ba3da90146a73ab4e9d8ddf15687551cb2cc2659be90d16e525253ecfb5 | rows lesson:2026-05-09_arXiv_2605_06161#p20:388:3285-3524, lesson:2026-05-09_arXiv_2605_06161#p17:344:3099-3426, lesson:2026-05-09_arXiv_2605_06161#p9:154:0-453, lesson:2026-05-04_arXiv_2510_11595#p4:77:3782-3859, lesson:2026-05-04_arXiv_2510_11595#p5:79:0-1155, lesson:2026-05-04_arXiv_2510_11595#p8:141:1253-1497, lesson:2026-06-16_arXiv_2605_31468#p13:183:586-610, lesson:2026-06-16_arXiv_2605_31468#p22:326:1054-1126, lesson:2026-06-16_arXiv_2605_31468#p21:320:1634-1896, lesson:2026-02-22_arXiv_2407_07086#p5:61:693-1765, lesson:2026-02-22_arXiv_2407_07086#p5:72:2599-4283, lesson:2026-02-22_arXiv_2407_07086#p7:84:46-1000, lesson:2026-02-22_arXiv_2507_21206#p69:756:1727-1865, lesson:2026-05-09_arXiv_2602_22302#p31:512:1942-2549, lesson:2026-05-09_arXiv_2602_22302#p32:527:451-1229, lesson:2026-05-09_arXiv_2602_22302#p26:442:2090-2398, lesson:2026-04-07_arXiv_2506_14092#p25:257:108-128, lesson:2026-04-07_arXiv_2506_14092#p26:262:108-128, lesson:2026-04-07_arXiv_2506_14092#p32:304:108-128, lesson:2026-02-22_arXiv_2507_02616#p5:124:1638-2639, lesson:2026-02-22_arXiv_2507_02616#p6:138:2259-3420, lesson:2026-07-09_arXiv_2602_06448#p23:984:1451-3259, lesson:2026-07-09_arXiv_2602_06448#p12:450:2615-3243, lesson:2026-07-09_arXiv_2602_06448#p4:99:2224-3127, lesson:2026-02-22_arXiv_2505_15047#p30:791:474-1908, lesson:2026-02-22_arXiv_2505_15047#p3:48:2189-2646, lesson:2026-02-22_arXiv_2505_15047#p39:917:0-481, lesson:2026-03-27_arXiv_2407_10239#p5:48:1852-2200, lesson:2026-03-27_arXiv_2407_10239#p6:53:113-123, lesson:2026-02-11_arXiv_2504_14765#p90:828:900-1134, lesson:2026-02-11_arXiv_2504_14765#p10:49:703-1095, lesson:2026-02-11_arXiv_2504_14765#p15:139:948-1617, lesson:2026-02-22_arXiv_2502_11133#p4:116:4368-4617, lesson:2026-02-22_arXiv_2510_18798#p5:165:2627-3180, lesson:2026-06-16_arXiv_2506_11068#p16:227:0-524, lesson:2026-06-16_arXiv_2506_11068#p15:226:2177-2476, lesson:2026-03-17_arXiv_2601_04748#p9:159:27-184, lesson:2026-03-17_arXiv_2601_04748#p3:41:4236-4289, lesson:2026-02-21_arXiv_2510_08558#p8:338:4455-4700, lesson:2026-06-09_arXiv_2512_22471#p25:340:1280-1493, lesson:2026-06-09_arXiv_2512_22471#p23:307:82-108, lesson:2026-02-22_arXiv_2507_23773#p5:120:1518-1634, lesson:2026-02-22_arXiv_2507_23773#p4:101:1576-1698, lesson:2026-02-22_arXiv_2506_08007#p8:163:183-350, lesson:2026-02-22_arXiv_2506_08007#p2:19:4057-4282, lesson:2026-02-22_arXiv_2506_08007#p4:83:2430-3388
- library receipt: query "search engine optimization crawler site audit" | release library_graph_20261017_sq018_02_2026-10-17.json sha256:99984ba3da90146a73ab4e9d8ddf15687551cb2cc2659be90d16e525253ecfb5 | rows lesson:2026-02-22_arXiv_2505_03906#p6:68:3691-4278, lesson:2026-02-22_arXiv_2505_03906#p6:66:2694-3324, lesson:2026-02-22_arXiv_2505_03906#p6:69:4280-4593, lesson:2026-02-22_arXiv_2503_09516#p4:68:347-2894, lesson:2026-02-22_arXiv_2503_09516#p13:265:2915-3361, lesson:2026-02-22_arXiv_2503_09516#p4:65:273-307, lesson:2026-03-17_arXiv_2207_01206#p5:81:1654-1999, lesson:2026-03-17_arXiv_2207_01206#p16:290:1587-1604, lesson:2026-03-17_arXiv_2207_01206#p24:405:226-779, lesson:2026-02-22_arXiv_2505_04588#p3:24:3768-3966, lesson:2026-02-22_arXiv_2505_04588#p4:41:49-97, lesson:2026-02-22_arXiv_2505_04588#p5:72:47-80, lesson:2026-02-22_arXiv_2510_18798#p7:210:1282-1485, lesson:2026-02-22_arXiv_2510_18798#p7:221:2416-3462, lesson:2026-02-03_arXiv_2005_14165#p43:443:203-1090, lesson:2026-02-03_arXiv_2005_14165#p43:442:37-201, lesson:2026-02-03_arXiv_2005_14165#p8:70:2533-3745, lesson:2026-02-22_arXiv_2501_07572#p9:193:1213-2512, lesson:2026-02-22_arXiv_2501_07572#p5:92:1402-2333, lesson:2026-02-22_arXiv_2501_07572#p1:8:277-1116, lesson:2026-02-22_arXiv_2409_12959#p4:63:1308-1315, lesson:2026-02-22_arXiv_2409_12959#p4:65:1323-1336, lesson:2026-02-22_arXiv_2409_12959#p21:435:2377-2441, lesson:2026-02-22_arXiv_2505_22648#p18:383:3004-3182, lesson:2026-02-22_arXiv_2505_22648#p3:62:991-3833, lesson:2026-02-22_arXiv_2505_22648#p8:204:1390-1880, lesson:2026-02-22_arXiv_2505_20286#p2:26:3093-3100, lesson:2026-02-22_arXiv_2505_20286#p12:186:407-469, lesson:2026-02-22_arXiv_2505_20286#p5:98:1204-1581, lesson:2026-02-22_arXiv_2306_07863#p15:279:3203-3216, lesson:2026-02-22_arXiv_2306_07863#p31:723:867-937, lesson:2026-02-22_arXiv_2306_07863#p31:725:1181-1309, lesson:2026-02-22_arXiv_2308_00675#p3:47:819-836, lesson:2026-02-22_arXiv_2406_07496#p3:62:673-686, lesson:2026-02-22_arXiv_2504_12679#p3:25:19-47, lesson:2026-02-22_arXiv_2504_12679#p4:93:4749-5729, lesson:2026-02-22_arXiv_2505_15872#p34:656:386-832, lesson:2026-02-22_arXiv_2505_15872#p29:576:2454-2586, lesson:2026-02-22_arXiv_2505_15872#p4:85:1028-2310, lesson:2026-02-22_arXiv_2504_03160#p6:122:316-3789, lesson:2026-02-22_arXiv_2504_03160#p12:351:3260-3466, lesson:2026-02-22_arXiv_2504_03160#p3:94:4136-4855, lesson:2026-02-22_arXiv_2507_22606#p17:222:619-641, lesson:2026-02-22_arXiv_2507_22606#p4:23:0-379, lesson:2026-02-22_arXiv_2508_04903#p18:447:575-1076, lesson:2026-02-22_arXiv_2509_02547#p22:281:2170-3102, lesson:2026-02-22_arXiv_2509_02547#p31:361:1261-2876, lesson:2026-02-22_arXiv_2509_02547#p22:283:3136-4291, lesson:2026-02-22_arXiv_2401_13919#p13:243:2548-3004, lesson:2026-02-22_arXiv_2401_13919#p5:89:2834-3503
