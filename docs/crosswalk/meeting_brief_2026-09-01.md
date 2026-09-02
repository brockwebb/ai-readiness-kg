# AI-Readiness Knowledge Graph: what it holds, and what it can answer

State as of 2026-09-01T03:00Z, with the corpus, extraction and quality figures re-measured on
2026-09-02 after the production extraction run closed (derivations in
`cc_tasks/2026-09-02_deck_numbers_post_burn_RESULT.md`). Every number below comes from the
event log, the spend ledger, the burn state file, or the graph projection.

## What exists

The graph covers the federal AI-readiness gray literature and the adjacent standards it leans
on. 194 documents are admitted, each with a recorded reason for admission and a content hash. 94
have been converted to a uniform markdown substrate whose provenance survives conversion, so a
reader holding only the substrate can say what it derives from and re-verify it. 35 documents
have been extracted under a single version-pinned profile, across 1,198 chunks, placing
10,305 nodes and 11,914 edges in the live graph. The nodes are 4,211 Concepts, 3,069 Claims,
708 Definitions, 673 Measures, 645 Practices, 399 Standards, 215 Instruments, 170 Frameworks,
120 Platforms and 95 Tools. Nothing enters the graph without a verbatim grounding span from the source text, and no
batch enters without passing an acceptance test described below.

## Coverage against the operationalization skeleton

The skeleton defines 45 candidate indicators in seven groups and names, for each, the source
documents that would evidence it. The table maps those named documents to what the graph now
holds. This is the skeleton's own mapping rather than a judgment call about which concepts touch
which indicator, which keeps the honest ambiguity where it belongs.

| Group | Indicators | Marked gap in skeleton | Evidence docs named | Extracted | Nodes |
|---|---:|---:|---:|---:|---:|
| A Accessible | 9 | 5 | 14 | 11 | 1,040 |
| B Understandable | 6 | 3 | 5 | 5 | 2,169 |
| C Accurate | 5 | 1 | 6 | 5 | 1,706 |
| D Open | 4 | 4 | 0 | 0 | 0 |
| E TEVV loop | 9 | 2 | 5 | 5 | 583 |
| F Release engineering | 6 | 2 | 3 | 1 | 91 |
| G Statistical-product semantics | 6 | 3 | 7 | 5 | 679 |

Two cells are findings rather than progress reports. Group D, openness, names no evidence
document at all: all four of its indicators are marked as gaps in the skeleton, and the corpus
holds nothing against them. License clarity, reuse permissions for AI training, provenance
completeness and public inventory completeness are the thinnest part of the picture, and that is
a corpus gap rather than an extraction gap. Group F is thin for a different and temporary
reason. Two of its three named documents are the data-contract and release-attestation
standards, and both were acquired at the wrong extent originally. Both have now been re-acquired
at their canonical source, both clear the substrate quality check, and both hold reserved batch
identifiers awaiting one request event.

On the demand ledger: 41 units of crosswalk demand are spread across 35 documents. The batches
in the current scoped burn account for 31 of those units, or 75.6 percent, and complete when the
run finishes. The two re-acquired standards add 4 more, bringing the total to 35 units or 85.4
percent. What remains deferred is six documents carrying 6 units between them, three of them
long specifications that drive the cost, set aside because that group is 58 percent of the
remaining extraction work for 16 percent of the remaining demand. A further 159 documents are
deferred because they carry no demand from this operationalization at all, and every one of
those 159 is measured at zero demand rather than assumed to be. Nothing deferred is lost. The
extraction unit is the chunk, so any deferred content is one request event away, and a request
can name individual sections rather than a whole document.

## The quality line

Extraction quality here is measured rather than asserted. Before any production extraction, the
profile had to pass a pre-registered faithfulness gate whose thresholds were fixed before the
data were seen: a fabrication rate whose 95 percent upper bound must fall below 0.10, and an
item-level faithfulness rate at or above 0.70. It passed, at a fabrication upper bound of 0.0715
and item faithfulness of 0.7705, over 160 judged facts drawn from 28 documents. Every production
batch since is then tested on its own before its content is allowed to stand, using sequential
acceptance sampling with parameters fixed in advance. Fifteen batches were judged; fourteen were
accepted and one was sampling-inconclusive, meaning it yielded 33 admitted items against the
55-fact minimum the plan needs to reach any decision, so it stands under the pre-registered
accept-with-flag rule. None was rejected or quarantined. Pooled over the burn, 37 of 1,480
judged facts were fabrications, a rate of 0.025 with a 95 percent interval of 0.018 to 0.034,
against the 0.10 line. A batch that failed would be quarantined out of the graph
automatically rather than reviewed by hand. Separately, a two-layer guard has refused 93
proposed relations of types that no consumer has yet asked for, at both the admission and the
projection stage, so the graph does not accumulate relation types nobody has validated. The
framing will be familiar to this audience. Federal estimates ship with a measure of their own
error; this graph ships with the same discipline.

## On uncertainty legibility

The skeleton's flagship indicator, G1, asks that error measures travel as structured fields
beside the estimates rather than as footnotes. Every quality number in the paragraph above
carries either its interval or its n, because the same argument applies to a knowledge graph as
to an estimate. That is one observation about practice, not a claim of novelty.

## What this enables next

Instrument items can be drafted against extracted evidence rather than recollection, with each
item tracing to a document, a chunk and a verbatim span. Per-indicator evidence lookup becomes a
query rather than a reading assignment. And the table above already identifies where the corpus
itself is thin, which is the openness group first and release engineering second, so the next
acquisition round has a target chosen by measurement rather than by intuition.
