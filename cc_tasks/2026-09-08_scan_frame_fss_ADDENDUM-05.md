# ADDENDUM-05 to `cc_tasks/2026-09-08_scan_frame_fss.md` — scope correction from the operator: 16 + 3 hosts, nothing else. Supersedes ADDENDUM-02, -03, -04 and every Tier B clause.

**Date:** 2026-09-08
**Authored by:** Desktop session after the operator stopped the drift. The base task's §2 selection rule, ADDENDUM-02 (inventory derivation), ADDENDUM-03 (CISA registry, data.gov API), ADDENDUM-04 (derivable-host inventory), and Tier B (14 departments, then 26) were all Desktop's additions in pursuit of *deriving* machine entry points. The operator did not ask for any of it and tier 0 does not need it. **Those addenda are withdrawn**; nothing already on the log is edited.

**The frame, final for this task and for cycle 3:**
- **Tier A: the 16 OMB-recognized statistical agencies and units** (roster as registered in `fss_roster_2026-09`, Tier A entries only).
- **Tier C: three reference hosts, tier-0 legs only:** `data.gov` / `catalog.data.gov`, `nist.gov` / `data.nist.gov`, `gsa.gov` / `open.gsa.gov` (ADDENDUM-01 stands).
- **No Tier B.** Remove Tier B from the targets, the pre-flight, the page and the DD. The roster DataFile keeps its Tier B entries as parsed (immutable); `fss_departments_tier_b` stands as a registered fact and is not used.
- **Nothing outside those 19 hosts is contacted by this task or by cycle 3.** No CISA registry, no department domains, no data.gov CKAN API probing beyond what the A11 leg does on `catalog.data.gov` as a Tier C host in cycle 3.

**Surfaces per host, declared not derived:**
- Every host: home, `robots.txt`, the `.well-known` and discovery probes the collectors already run. Tier 0 needs nothing more.
- **Machine entry point and flagships are declared.** The 26 cycle-1 flagship surfaces and the cycle-1 machine entry points stand as the operator's declaration, carried with their `doc_id`s. For the three units and any Tier A agency with no cycle-1 entry, the row carries home and probes only, marked `pending_operator_declaration`, and `docs/design/fss_flagship_shortlist.md` (already written) is where the operator declares. No rule selects a surface in this task.
- `frame.py`'s token matcher and the inventory lookup are removed from the selection path (leave the code if tests depend on it, but nothing in the target build calls it).

**What stands from earlier work:** §0 (suite green), §1 roster (Tier A 16), ADDENDUM-01 Tier C, the cycle-1 carry-forward from §2.b. The three DataFiles / Results already registered from the withdrawn addenda (`fss_department_domains_2026-09`, the CISA and data.gov counts) are facts on the log; supersede the DataFile with the reason "outside the frame per ADDENDUM-05" and leave the Results, which are not used.

**Remaining steps, in order, then stop:**
1. Regenerate `state/scan_targets_fss_2026-09.json` from the roster (Tier A) + Tier C + cycle-1 declarations, register it as `scan_targets_fss_2026-09` with `derived_from: fss_roster_2026-09`, admit with `purpose: scan_surface`, assert zero conversion-gap tasks. Expected shape: 19 hosts, 16 + 3 home rows, 26 carried flagship rows, cycle-1 machine entry points, pending markers for the rest.
2. §3 pre-flight over exactly the 19 hosts.
3. §4 tool map (drop the `/data.json` collector row; keep the DCAT-catalog-presence gap named in the gap table, not built).
4. §5 DDs: frame = 16 + 3, declared surfaces, no Tier B, no derivation; the sentence that the government publishes no machine-readable department → inventory map may stay as a recorded observation. Client identity DD as written.
5. §6 gate, amended: roster Tier A = 16; every target row's `selection_source` is `operator declaration` or `roster host`; zero rows outside the 19 hosts; zero conversion-gap tasks; pre-flight Results for exactly 19 hosts; tool map regenerates byte-identically; suite green.
6. §7 RESULT, `cc complete` if the gate passed, commit, push. **If anything blocks, write the RESULT with the block on top, commit, push, and stop.** No further addenda.
