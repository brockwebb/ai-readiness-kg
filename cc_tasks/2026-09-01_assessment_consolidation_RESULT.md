# RESULT — Consolidate the June ai-readiness-fss assessment work into ai-readiness-kg

**Task:** `cc_tasks/2026-09-01_assessment_consolidation.md`. No `_ADDENDUM*.md` siblings existed
at dispatch or at close. **Spend: zero model tokens.** Git operations, file edits, a
deterministic deck rebuild, and registration only.

**Sequencing gate satisfied, and verified rather than assumed.**
`cc_tasks/2026-09-01_machine_diagnostic_stub_RESULT.md` exists, and all seven edits it claims
are live in the skeleton (rows A10 and A11, §6b item 5, the §5d G1 sentence, both §9 entries,
the v0.2.1 status note). Its Seldon task `b1322301` reads `completed`.

## 1. Import (step 1)

`git subtree` was available, so the task's STOP condition did not fire. Worth recording how
close that came to a false stop: `git subtree --help` fails on this machine because no man page
is installed, and taking that as the answer would have halted the whole task. `git subtree -h`
works and `git-subtree` is present in `git --exec-path`.

| step | result |
|---|---|
| split | `brock_projects` branch `airfss-split`, head `60bb339`, 4 commits |
| add | `assessment/` at merge commit `4209e23` |
| history | `git log 4209e23^2` reaches `5524a7b`, `84380dc`, `0173246`, `60bb339` (2026-06-23/24) |
| imported suite | `cd assessment && pytest tests/` — **156 passed** |
| root suite | **594 passed**; `testpaths = ["tests"]` keeps the imported tests out of the root run |

The subtree carried its own `.gitignore`, and it is honored: probe files created under
`assessment/results/` and `assessment/evidence/` show as ignored, so no merge into the root
`.gitignore` was needed. Internals were not flattened or renamed; `harness.*` imports work
unchanged, which the 156 passing tests demonstrate.

## 2. Discrepancies, reported not reconciled

**2.1 `cc_tasks/` did not come across, because it was never tracked.** The task premise lists
`cc_tasks/` among the imported internals. `brock_projects/.gitignore` line 94 ignores
`cc_tasks/`, so those files were never in git and `subtree` could not carry them. Copying them
in would be the plain copy the task forbids, so they were left where they are.

**2.2 The tombstone removed tracked content only.** `cc_tasks/`, `results/` and `evidence/`
remain on disk at the old path alongside `MOVED.md`. They were never tracked, so deleting them
would destroy operator-local material that no import could recover and no history could restore.

**2.3 One pre-existing `seldon verify` issue, untouched.** File hashes are stale for
`kg/schema.yaml` and `corpus/manifest.json`. Both changed during the v038 burn and the extent
remediation, before this task. `corpus/manifest.json` is explicitly out of bounds here, and
resyncing hashes while a burn is writing is not this task's business. Everything else in
`seldon verify` passes.

## 3. Downstream consumer (step 3)

`census-web-concept-inventory/config/rubric_source.yaml` repointed from
`/Users/brock/GitHub/brock_projects/ai-readiness-fss` to
`/Users/brock/GitHub/ai-readiness-kg/assessment`. One line changed; nothing else in that repo
was touched.

The pins are computed at report time rather than stored in the file, so "pins remain valid"
means the hashed content is byte-identical across the move. Verified against the old location
before the tombstone removed it, since afterwards the comparison would have been impossible.
**12 of 12 identical, 0 differing, 0 missing.**

| file | sha256 | status |
|---|---|---|
| `benchmark_rubric.md` | `54a8bc2046af84fd54c67dd168e2254d5d829107088f2380e20a05aba0546884` | unchanged |
| `harness/records.py` | `ab37c39225d6a610130f2571059b750c7f07c94c55f8424c504876eb150f0dbe` | unchanged |
| `harness/jsonld.py` | `462e2d36fd608787a2d94b711cd2858f95498d5c808af56549fa13d8fe6e23ad` | unchanged |
| `harness/probes/base.py` | `a7d2c7ec58889f71e8f7fe22391c5537c17c6ded27fe3d4250a2df9cd7b8f6d2` | unchanged |
| `harness/probes/d1_catalog.py` | `50b2547b77024348b06e8fa30892cc2b0eacfb2e40da604b4d6703b04d5663ea` | unchanged |
| `harness/probes/d1_robots.py` | `4ca0f32adfc297c03ba12f2d6deebe1bb81a8eadca2e593c20a6f6c844090b0f` | unchanged |
| `harness/probes/d1_sitemap.py` | `362bf0d68549905095793917064e264bfa4a50548b6b1badb02c19ac8f99b5e6` | unchanged |
| `harness/probes/d2_no_barriers.py` | `7c83d207f0859a850d85232dc88fb667e6c46609c8849a9da50dd4a901f11b01` | unchanged |
| `harness/probes/d3_metadata_standard.py` | `59f9138a59927a72489d2a172e1d3817841bba0dcd086d77550451582a3d9ba6` | unchanged |
| `harness/probes/d4_license.py` | `de46ffd0953c2ca820e479b0d9a559a9bf6807aa7343c9e734da432135feaa70` | unchanged |
| `harness/probes/frontier_llms_txt.py` | `6edffd014179ce5571c4e65252273937aaff7859d12ce4080d15eadfd608179c` | unchanged |
| `harness/probes/frontier_mcp.py` | `f824acfa5425e084de06a5cb9af4fc64e5c18ace685af6c48215af207d8e22c2` | unchanged |

## 4. The merged protocol (step 4)

`docs/crosswalk/assessment_protocol.md`, 1,422 words, nine sections in the order the task
specifies. No bold in prose, no em-dashes, no one-sentence paragraphs, checked mechanically.

The two substantive merges, since the rest is carried from June unchanged. The unit of analysis
reconciles rather than chooses: the product is the measurement unit and where remediation
happens, the agency is the aggregate and where policy acts, and agency vectors are read within
peer cohorts. Orientation-first replaces June's Part B mechanism naming, and the rule that
survives the replacement is the one underneath it: a mechanism is a hypothesis about how
machines orient, and observed machine behavior admits or retires it, never vintage. That makes
llms.txt and MCP/WebMCP-class endpoints dated frontier candidates under a general rule rather
than named exceptions.

June's documents in `assessment/` were not edited.

## 5. Skeleton and deck (steps 5 and 6)

Skeleton: one pointer paragraph at the top of §6 naming the protocol as governing where the two
differ, plus the `v0.2.2` status note. Nothing else changed.

Deck content bumped to v3 with five edits: slide 5 reframed orientation-first with MCP/A2A
removed and the discovery stack named; slide 8 "agent endpoints" to "discovery surfaces"; slide
9 gains the working reference implementation, run against a live Census product; slide 13 gains
the evidence-criterion rule naming MCP/WebMCP as dated frontier candidates; slide 16 gains the
June work as prior art absorbed rather than compared against.

The deck already existed, so step 6's rebuild condition applied and it was rebuilt with the same
procedure. **18 sections in, 18 slides out, no splits.** Slide 9 moved from 18pt to 17pt to
absorb its new line; slide 13 stayed at 18pt. Open-check confirms slide 5 no longer mentions
MCP/A2A and does mention RFC 9309, and slide 9 mentions `assessment/harness`. This satisfies the
separately dispatched `2026-09-01_framework_deck_build.md`, whose own task was already completed
at 14:48; a note was appended to its RESULT rather than re-completing it.

## 6. Registration (step 7)

`DD-031` appended to `docs/design_decisions.md`: the consolidation, the two-level unit, and the
orientation-first rule with its evidence criterion, including what it supersedes (June probe
depth on the discovery and web surface, per the D0-r2 findings).

Seldon artifacts created: DesignNote `5c5a4a29` (the protocol), DesignNote `a732175e` (the
imported layer), ArchitecturalDecision `bfa03c06` (DD-031). The task said "type per project
conventions"; `Document` is not a valid type in this project's schema, and `DesignNote` and
`ArchitecturalDecision` are, so those were used.

## 7. Burn safety

The v038 burn was running throughout, mid-b008. `git subtree add` refuses a dirty tree, and the
burn writes a raw response file every few seconds, so its in-flight artifacts were committed as
a checkpoint first. Nothing in this task touched the burn process, the spend ledger, the corpus
manifest, or the event log.
