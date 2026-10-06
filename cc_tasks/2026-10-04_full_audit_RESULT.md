# RESULT: full-project audit: 66 findings (7 S1), 19 operationalization items, the three control kinds each caught blind once

**Task:** `cc_tasks/2026-10-04_full_audit.md` (ResearchTask `2d9d2309`). **Ran to the end**, 2026-10-06 02:06Z to 03:35Z. It was hand-dispatched, because the dispatcher refuses this task (§7, items 1 and 3). **Deliverable:** `docs/audit/2026-10-04_full_audit.md`, holding the protocol, inventory, known list, findings, operationalization list, controls, reader gate, limits, and an appendix of each reader's read record. Also `docs/audit/2026-10-04_full_audit_findings.csv` (85 rows, with the verbatim span and the check behind each) and `scripts/plant_audit_controls.py`. Nothing was fixed.

## 1. Method, retrieved versus recalled
- **Protocol first:** written into the audit document before the inventory was read (§1 there).
- **Sources:**
  - Adversarial-review rubric v1.3.0: **retrieved** (sha256 `4e6f51c2…`). Its grounding and anti-anchoring rules govern. Its `code` overlay is a stub that forbids recorded verdicts, so no verdict records were emitted.
  - SFV T1 to T5: **retrieved**, from `brock_projects/sfv-paper` at `ac28c39`.
  - ACM Artifact Review and Badging v1.1: **retrieved verbatim, via a page that reproduces them** (sigir.org), because acm.org returned 403.
  - Wohlin et al. 2012 (DOI 10.1007/978-3-642-29044-2): **metadata retrieved; the four class definitions recalled**, because the text is behind Springer's login.
  - `seldon audit` does not exist, so it was substituted (§7, item 2).
- **Readers:** six fresh readers (A to F) audited a `git archive` copy of HEAD `a5b5134f` with the controls planted. They read the live graph read-only. A seventh (R2) re-ran two controls clean. The session then merged the findings, removed duplicates, applied the 3-point scale, and re-checked every S1 at its locator and in the graph itself. Every `evidence_span` was verified as a verbatim substring of its file by script: 98 of 98.

## 2. Counts
- **Findings:** 66, after removing 4 plant detections and merging 9 duplicates.
  - By severity: **S1 7, S2 28, S3 31**.
  - By primary class: construct 20, internal 29, external 4, conclusion 13. Vibe class: 14.
  - The session raised four readers' S2s to S1 under the declared test: C-04, C-06, C-07 and C-13. Reasons are in the CSV. Nothing was lowered.
- **Known list:** verified, not counted as findings. Open: K1, K6, K7, K8, K10 and K11 `fa40072e`. Changed: K2, K3 and K11 `1267b87d`. Closed: K4, K5 and K9. Detail in §3 of the audit document.

## 3. Top ten
1. **C-01, S1, construct (ACM functional).** `assessment/harness/scan/params.yaml:704`: A1 and A3 fails are absence claims over the first 25 links (`max_links_probed: 25`, `links.py` `break`) of pages with 48 to 244 on-host links. The unprobed links go unrecorded. *Closes:* probe all of them or rank the candidates, record what was not probed, and return error on a truncated absence (task).
2. **C-02, S1, conclusion (SFV T2).** `docs/reports/2026-09_fss_ai_readiness_L0.md:187`: says BLS, BTS and SSA each "publishes a `robots.txt` that grants access". Their own findings say the host "answered HTTP 403 to /robots.txt itself" on every read. *Closes:* reword it to the findings (wording).
3. **C-04, S1, construct.** `rules/rule_d4_v3.py:86`: D4 reads only `<host>/data.json`, where ind:D4 says "data.gov/agency inventory". 28 rows are prescribed "Publish a data.json inventory on the host". *Closes:* resolve the departmental inventory first, or narrow the indicator text (task).
4. **C-06, S1, construct (SFV T4).** `rules/rule_a9.py:1`: ind:A9 is `frontier: true`, yet it is scored for every body (`score.py --json`: `scored: True`), against the firewall `design_decisions.md:537-539` carries forward "unchanged". *Closes:* exclude frontier legs, or rule to retire the firewall (task).
5. **C-07, S1, internal (ACM reproduced).** `framework/ai_readiness_framework.json:18`: the site prints "16/48" measured (`docs/progress/index.html:55`) and the brief "21 of 48" (`G_census_dogfood.md:10`). Every `measured_by` still points at `scan_2026-09-07`. *Closes:* run the measured write-back for rj4, or name the two counts differently (task).
6. **C-13, S1, construct.** `assessment/harness/scan/targets.yaml:96`: the roster says the NCHS host files are CDC's and "not a finding about the statistical agency". NCHS is still scored and ranked 13 of 13 on them, and the L0 report never says so. *Closes:* mark or exclude parent-host cells, or state it beside every rank (ruling).
7. **C-14, S1, construct.** `rules/rule_a2_v3.py:59`: the Census ACS A2 fail ("no OpenAPI/JSON API description served at any probed path") comes from three guessed paths on www.census.gov. The brief then prescribes "Expose the product through an API", while `sources_per_check.json:237` cites api.census.gov. *Closes:* follow the documented API base before judging absence (task).
8. **A-07, S2, vibe, internal.** `docs/design_decisions.md:421`: about 4,400 nodes from the Commerce, DCAT-US 3.0 and A01 runs were projected with no DD-029 SPRT faithfulness sample. *Closes:* run the probe, or record an exemption (task).
9. **A-10, S2, vibe, internal (SFV T2).** `docs/design_decisions.md:686`: DD-040's "every graph figure is a registered Result" is unenforced. October RESULTs quote graph counts that match no Result, and one set did not reproduce. *Closes:* register a dated snapshot and check RESULT numerals against it (task).
10. **D-01, S2, vibe, internal (SFV T2).** `scripts/build_projection.py:557`: unlabelled-endpoint MERGE puts edges on both label twins. 75 Document→Concept ASSERTS edges exist (Cypher), which `kg/schema.yaml:304-307` forbids, and the lint allowlists the line. *Closes:* type endpoints on edge events and MERGE by label (task).

## 4. Controls (decision 6)
- **Run 1** (sealed manifest; opened only after the merged findings were frozen, sha256 `f1db3871…`):
  - **Test with no assertion:** caught **blind** by E-12.
  - **Wrong locator (CL-046):** caught, but **contaminated**. Reader B diffed against the live checkout, against its brief, and said so.
  - **Caption off by one (fig1):** caught, but **contaminated**. Reader A had read this task file, and reader B diffed as above.
- **Run 2** (new draw; `cc_tasks/`, `docs/design/` and `docs/research/` deleted from the copy, and no live checkout or git): the locator plant (CL-004, B2 re-pointed to F2) and the caption plant ("48" made "49") were both caught **blind** (R2-01, R2-02). There were 0 false positives.
- **Removal and limits:** both copies were removed by the script, which confirmed the planted paths equal HEAD (`logs/2026-10-06_full_audit_remove_controls.log`). That is n = 1 per kind, and no rate is claimed.

## 5. Operationalization (decision 5)
- **19 items:** S2 10, S3 9. `712755f8` was read: it covers none of them directly and overlaps F-08 and F-09.
- **Top three:**
  - **F-05:** `pyproject.toml:10` declares pyyaml alone, while the scan imports nine packages and the repo imports seldon and dixie, so `pip install .` does not install a working tool.
  - **F-09:** `adopt.py:231`: a frame with a loopback home and an external flagship passes `check_identity` under this project's identity. Whether a later layer blocks the fetch was not shown.
  - **F-20:** `tests/test_adopter_path.py:510`: the "stranger" gate runs on the author's interpreter, `HOME` and untracked files. No run on a clean machine is on record.

## 6. Reader gate (DN-009 d7): the fresh reader's answer, condensed here; verbatim in §7 of the audit document
1. Absence verdicts are reached over a partial search: 25 links, the host's own data.json, three guessed API paths. So Census is told to build an API it has.
2. The L0 report says three hosts publish a granting robots.txt that every read refused, which casts doubt on every other sentence.
3. The scores break the project's own rules: frontier A9 is scored, and rules called "pre-registered" were written after their data.
4. Rank 1 rests on one data.json fetch feeding five legs, and four bodies are scored on parent-department files.
5. The checks cannot fail: Neo4j skips read as green, the grounding gate passes at zero checked, there is no CI, and the logs are gitignored.

*First:* fix the absence verdicts (C-01, C-04, C-14). Its points were two sentences each (ten in all), quoted as given there.

## 7. Premises wrong
1. **Model.** The session and all eight subagents ran under `claude-opus-5-5`, not `claude-fable-5-1`. Per the task, the operator re-runs it by hand under Fable, into new files, since these are immutable.
2. **`seldon audit` does not exist.** `seldon` 0.1.0 reports "No such command 'audit'". `com.arnold.seldon-audit` is bound to arnold's own repo. It was substituted by `seldon status`, `seldon dispatch status` and `seldon verify`.
3. **"Launched by the dispatcher" cannot happen.** The `Framework layer served` value "all layers; …" fails the layer grammar, and dispatch status reports `framework_layer_names_no_layer` (also finding F-21). This was a hand dispatch while `dispatch.enabled: true`. I touched `.seldon/DISPATCH_STOP` at 02:06:04Z; the dispatcher logged `dispatch_observed_stop` at 02:10:48Z, the one line in this commit's `seldon_events.jsonl` before close. It is removed at close.
4. **"Write the protocol into the README"** was read as the audit document's §1, since `README.md` is outside the write set.
5. **`score.py`** is `scripts/score.py`, not under `assessment/`.
6. **K2 as worded is wrong:** 26 Definitions lack a DEFINES edge; all have an asserting event. **K11 names `1267b87d` as the header-parse defect**, but `fa40072e` carries both defects, and `1267b87d` changed with Seldon `d9ad7d3`.
7. **The write set holds no test file**, so `plant_audit_controls.py` has none. It was exercised by a seeded self-run and its `verify_copy` git-hash check instead.

## 8. Gate (logs under `logs/`, gitignored)
- **`make gate-fast`:** 2958 passed, 0 failed, 3 skipped, 27 deselected, 37 xfailed, EXIT=0, 737.44 s (`2026-10-06_full_audit_gate_fast.log`).
- **`make gate-full`, before push:** 2985 passed, 0 failed, 3 skipped, 0 deselected, 37 xfailed, EXIT=0, 2367.98 s (`2026-10-06_full_audit_gate_full_suite.log`).
- **The 3 skips in both:** `test_dispatch_config.py:373` (dirty tree and the STOP file, expected mid-task), `test_scan_harness.py:283` and `test_g1_preservation.py:337` (both standing).
- **`seldon verify`:** "All checks passed.", EXIT=0 (`2026-10-06_full_audit_verify.log`).
- **Protected paths:** PASS, EXIT=0. Only the write set plus `seldon_events.jsonl` (the dispatcher's stop observation) is changed (`2026-10-06_full_audit_protected.log`).
- **Other logs:** `_fusion_check.log` (D-02 drift, EXIT=1 as found), `_plant.log`, `_plant_r2.log`, `_seldon_status.log`, `_dispatch_status.log`.

## 9. Tokens and model
- **Model:** `claude-opus-5-5` for the session and every subagent.
- **Subagents, measured** (from each completion notice): A 424,258; B 277,565; C 333,520; D 266,401; E 262,565; F 241,929; R2 183,259; reader gate 71,782. That is **2,061,279** in all, against the task's 12M estimate.
- **The main session's own cumulative token count is not visible to the session**, so it is not reported as a number. It consumed about 0.2M of its 15M context window.
- **No `claude -p` or spend-ledger calls were made.**
