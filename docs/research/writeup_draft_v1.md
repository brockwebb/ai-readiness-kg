DRAFT v1, not for circulation. State as of 2026-09-01T03:10Z. A production burn was running
when these numbers were read; figures marked [as of 2026-09-01T03:10Z; final at burn close]
will move.

# Measuring what a knowledge graph got wrong: pre-registered gates and acceptance sampling for LLM extraction

## 1. The problem, and why a statistical agency should care

The current generation of agent-memory and knowledge-graph patterns ships quality operations
without quality measurement. The clearest example is the LLM wiki pattern, in which an agent
maintains a markdown knowledge base and a lint step runs continuously over it. That lint is a
real quality mechanism and it should be described accurately. It detects contradictions, stale
claims, orphaned entries, and missing cross-references, and ecosystem extensions add provenance
fields, confidence levels, and recency-based contradiction resolution. What it does not do is
compare the wiki to its sources with a denominator. Every check runs the artifact against
itself. There is no error rate, no threshold, and no gate. The design intent that every claim
traces back to a source is stated but never verified or reported as a rate, and a lint-clean
wiki can be consistently fabricated. The community that built the pattern says as much: a wiki
can become perfectly consistent around one stale claim.

The interchange formats have the same shape and are more candid about it. The open knowledge
format is explicitly quality-agnostic and states its own limits, that markdown does not fix
knowledge quality and that it performs no conflict detection or resolution. Enrichment
pipelines built on it add their own lint, which is a set of specification-conformance rules,
format checks with zero content measurement, refreshed by unvalidated model extraction on every
commit. Later versions add trust, provenance, and freshness fields. Those are a vocabulary for
trust signals with no mechanism to earn them.

The analogy for a federal statistics audience is exact. These systems publish estimates without
margins of error. The estimate may be good. Nobody can tell, including the people who produced
it, because nothing in the system measures correspondence to a source.

This paper reports what happens when the measurement layer is built. The system is a knowledge
graph over federal AI-readiness gray literature and adjacent standards, built to support an
instrument-design effort. Extraction is done by a large language model under a version-pinned
prompt. The contribution is not the graph. It is the measurement apparatus around it, and more
usefully, the record of what that apparatus got wrong. Every finding in section 5 is a failure
of our own quality layer, caught by the quality layer, and each one generalizes.

## 2. The system in one page

Documents enter through a manifest gate that records why each was admitted and hashes its
bytes. Admission and extraction are separate events, because a curated corpus that conflates
them spends in arrival order rather than in priority order. A document is admitted with a
reason, and it is separately requested for extraction with a priority and a reason. A document
that is not worth extracting is cut with a reason, which is an event, not a silence. At the
time of writing, 159 documents are deferred because they carry no demand from the consuming
instrument, and each of those 159 is measured at zero demand rather than assumed to be at zero.

Admission also requires convertibility. Every acquired document must convert to a uniform
markdown substrate carrying its own provenance, and the conversion is checked for extent rather
than for exit status. This matters more than it sounds. A converter can succeed perfectly and
produce a faithful rendering of a table of contents, and no exit code will say so. The extent
check uses the two shallow features the boilerplate-detection literature settled on, text
density and link density, applied at document level as an admission judgment rather than at
block level for removal. When a document fails, admission still records it, and the system
emits a gap event and registers a follow-up task. Refusing admission would lose a document
someone deliberately acquired; admitting silently is the original defect.

Extraction operates on chunks, not whole documents, and the emission contract is anchors rather
than quoted spans. Every node and edge carries a verbatim grounding span validated against the
source text, and a span that does not validate is quarantined at parse rather than admitted.
Relation types that no consumer has asked for are refused at two independent layers, at
admission and again at projection, so the graph does not accumulate relation classes nobody has
validated. That guard has refused 93 proposed relations to date.

State is event-sourced. The append-only event log is the only source of truth, and the graph,
the manifest, and every report are disposable projections rebuilt by replay. An event is never
edited or deleted. Corrections are new events replayed over old ones. This is unremarkable
architecture, and section 5 reports the one place it took four attempts to apply correctly.

## 3. Qualification: three arms and a floor that measured the wrong thing

The extraction profile was qualified before production through a pilot comparing chunked
against whole-document extraction, then three successive prompt arms against a pre-registered
yield floor and a faithfulness gate. Each arm changed one instruction and held the model, the
schema, the chunks, and the grounding contract constant, so that a difference between arms is
attributable to the instruction.

The faithfulness instrument decomposes each extracted item into atomic facts, then asks two
independent judge models whether each fact is entailed by the source chunk. Labels are
aggregated by a Dawid-Skene consensus model. The reported quantity is a fabrication rate with a
Wilson 95 percent interval, plus an item-level faithfulness rate. Fabrication is a specific
class, separate from truncated spans and dropped subjects, which are recorded and not counted
as confabulation.

The pilot arms all passed faithfulness and all failed yield. Arm A measured a fabrication upper
bound of 0.0385 over 96 facts with 60 of 60 items faithful, at 15.70 admitted items per chunk.
Arm A2 measured 0.0243 over 154 facts with 72 of 73 faithful, at 24.30 per chunk. Arm A3
measured 0.0000 with a 95 percent upper bound of 0.0464 over 79 facts, 46 of 46 faithful, at
25.34 per chunk. The pre-registered floor was 27.14 admitted items per chunk, so all three
arms failed by ratios of 0.35, 0.54, and 0.56, and the pilot closed on under-extraction.

That closure was wrong, and the reason is the paper's first substantive finding. The floor was
derived as 0.60 of a comparator's measured yield of 45.23 items per chunk. That 45.23 was a
combined count of nodes and edges. The ground-truth rubric that would validate it annotates
items and does not annotate relations at all. Decomposed, the comparator emitted 16.95 nodes
and 28.27 edges per chunk, so 62.5 percent of the target was a quantity no instrument of this
kind could ever measure. Restated on the node basis the old target was 10.17 per chunk, not
27.14.

Three arms were designed to close what was mostly an edge-volume gap. The comparator that the
floor treated as a wild over-extractor sits at 0.93 times ground truth on nodes, which is not
over-extraction at all. Its apparent supremacy is edge volume, and one chunk shows it cleanly:
on a pure references block, the comparator emitted 0 nodes and 21 edges against a ground truth
of 0 items. Those edges are citations, and a bibliography does contain citations, so this is
not fabrication. It is a component the rubric cannot see and the floor silently counted. Across
the shared 44 chunks the comparator emitted 1,244 edges to Arm A2's 382.

The re-derivation built the ground truth the floor never had. A rubric was written and hashed
before any annotation, and the sample was drawn from a committed seed before any model call.
Two independent annotation passes ran per chunk, with adjudication of disagreements against
cited rules. The result was a mean of 8.60 items per chunk, median 1, range 0 to 28, standard
deviation 12.2 at n equal to 5. The spread is reported instead of a tidier summary because the
mean is not a stable quantity at that n. The re-derived floor is 0.60 times 8.60, or 5.16 node
items per chunk, and all four arms clear it by 1.47 to 1.74 times. The production candidate was
selected on measurement rather than recency, which mattered because the later arm lost: Arm A2
won five of seven comparisons including both ground-truth measures, and its extra items were
more often justified than the later arm's.

## 4. Production: a qualification that licenses starting, not finishing

A one-time qualification licenses starting a burn. It does not license finishing one
unmonitored, because the qualification measures a sample drawn once and the burn continues
after that sample is exhausted. Production therefore has two instruments.

The first is a stratified held-out confirmation gate, run before any production extraction on
documents no arm had seen. Thresholds were fixed in advance: a fabrication rate whose Wilson 95
percent upper bound falls below 0.10, and item-level faithfulness at or above 0.70. The gate
passed at a fabrication upper bound of 0.0715 and item faithfulness of 0.7705, which is 94 of
122 items, over 160 judged facts drawn from 30 chunks across 28 documents in four strata. The
minimum sample for a reachable decision was derived rather than assumed, because a threshold
whose precondition makes it unsatisfiable is a gate that cannot fail honestly.

The second is per-batch acceptance sampling. Every production batch is tested on its own before
its content is allowed to stand, using Wald's sequential probability ratio test with parameters
fixed before any production data existed: an acceptable fabrication rate of 0.05, a rejectable
rate of 0.10, and both error rates at 0.05. The plan's expected sample number at the acceptable
rate is 158.6 facts, against a budget of 463, and no batch can be accepted on fewer than 55
facts. A rejected batch is quarantined out of the projection automatically by an event, with no
human triage step. The sequential design is not a refinement. A fixed-sample test at this
budget would cost roughly 9.4 million tokens per batch in judging alone.

Three batches have posted verdicts and all three were accepted [as of 2026-09-01T03:10Z; final
at burn close]. The first accepted at 3 fabrications in 110 facts, with a pooled fabrication
rate of 0.0273 and a 95 percent interval of 0.0093 to 0.0771. The second accepted at the first
increment with 0 fabrications in 55 facts, upper bound 0.0653. The third accepted at 5 in 165,
upper bound 0.0690. Two of the three stopped well short of the budget, which is the sequential
saving arriving as designed.

Spend is governed by a preemptive ledger rather than by post-hoc accounting. Every run declares
a token ceiling before dispatch, every model call reserves against it before the call is made,
and the reservation settles at the observed cost. A run without a declaration is refused. The
daily band is a separate cap that the burn cannot move. This is bookkeeping, and it is reported
here only because it produced a finding in section 5.

The corpus state at the time of writing is 194 documents admitted, 94 converted to substrate,
and 31 extracted across 308 chunks, producing 4,838 nodes and 6,075 edges [as of
2026-09-01T03:10Z; final at burn close]. The extracted nodes are dominated by concepts and
claims, with definitions, practices, standards, and instruments behind them, which reflects the
schema's purpose rather than any property of the extractor.

## 5. What the measurement layer got wrong

The apparatus above is the contribution only if its failures are reported, so this section is
the paper. Each finding was produced by the measurement layer catching itself.

### 5.1 A gate's unit must be commensurable with its validating instrument

The floor saga in section 3 is the central case. The pipeline had pre-registration, a
threshold, a gate, and a recorded decision branch for failure. All of it worked as specified,
and it manufactured a phantom defect, because 62.5 percent of what the gate counted was a
quantity the validating instrument could not see. Having quality measurement is not sufficient.
The gate's unit must be measurable by the instrument that would validate it, or the measurement
layer produces exactly the failure it exists to prevent. The Census analogy sharpens here from
an estimate without a margin of error to a margin of error computed on a different universe
than the estimate.

The rule was adopted as a numbered decision and now binds every gate in the system. The
production gate states its unit explicitly: atomic facts of admitted node items. It says
nothing about relations, and the paper claims nothing about relation validation anywhere.

### 5.2 The same defect, wearing a safe face

The commensurability defect recurred in a form that looks like a coding error. The production
gate read two fields from its aggregator by name. The aggregator writes those quantities under
different names. Both reads returned nothing, and nothing resolved to a failing verdict, so the
gate reported failure on a run that had passed. A gate that cannot read its own instrument is
the same class of defect as a gate whose unit its instrument cannot measure. It now raises when
the instrument is unreadable rather than resolving an absent value to a verdict in either
direction.

### 5.3 Pre-registration does not remove judgment; it records the sequencing

The inter-pass agreement metric changed convention mid-task. The first implementation scored
the Jaccard similarity of two empty sets as 0. With three near-empty chunks in the draw, that
would have dragged the mean to 0.59 and, on a slightly different sample, fired the incident
stop on a rubric that was working perfectly. Two annotators who both find nothing in a
bibliography agree completely, so the convention was corrected to 1, and chunks where neither
pass proposed anything were excluded from the mean the threshold reads, because they are
uninformative about whether the rubric is specified finely enough.

The change is mathematically correct and it was made after per-pass counts were visible and
before any agreement value had been computed. That sequencing is recorded in the result file,
along with a mutation confirming the stop still fires when the informative chunks disagree.
Pre-registration cannot eliminate mid-task instrument judgment. What it can do is force the
judgment to be recorded with its sequencing, so a reader can audit whether it could have
rescued a failure. The informative agreement was 0.9421 against a stop threshold of 0.50.

This pairs with a second species of the same genus, a pre-registered threshold whose
precondition made it unsatisfiable. Both are gate arithmetic diverging from gate intent, and
both were found by working the arithmetic rather than by running the gate.

### 5.4 Impossible values are the cheapest bug detectors available

Two scorer defects were caught only because their outputs were impossible. One arm scored a
precision of 1.091, which cannot occur; containment matching is many-to-one in both directions
and the numerator and denominator had been drawn from different populations. The other was a
set of totals that did not reconcile, which is how the unit error in section 5.1 was found at
all. Neither defect had a test. A range assertion and a reconciliation assertion are nearly
free, and they caught what 440 tests did not.

### 5.5 Tests that measure artifacts instead of generators

Nine times in this project, a test has measured a committed artifact, or a helper adjacent to
the thing under test, instead of driving the generator that produces the behavior. The pattern
is stable across instances. A sample test reads the committed sample file rather than driving
the draw, so a mutation that ignores the seed survives. A gate test drives the gate's own entry
point rather than the admission path that is supposed to call it, so the two modules can be
wholly unconnected and every test still passes, which is precisely what had happened. A test
names the right principle in its docstring and then selects a fixture that the code under test
would have handled anyway.

The count is worth reporting plainly as an empirical observation about model-authored test
suites rather than as a confession. Every instance was caught by mutation testing, at a cost of
one rework cycle each, and none was caught by the tests themselves passing or failing. The
standing rule that emerged is to drive the real entry point and to pair every negative control
with a positive one, because a gate that rejects everything passes a suite composed only of
rejections.

The task file that governs this draft states eight instances. The live record is nine; the
ninth was recorded earlier today in the ingestion result. The discrepancy is reported rather
than reconciled.

### 5.6 Derived identity moves under provenance

Production batches carry an identifier that is stamped into the provenance of every event they
produce, and that identifier is what a quarantine names. It was derived from live state, and it
moved four times.

It was first cut from the count of chunks remaining, so completing a batch renamed it. That was
caught mid-dispatch, with 2,504 events already carrying the old meaning. It was then cut from
the worklist, so a document dropping out on completion renumbered every batch after it. It was
then cut from the set of live extraction requests, so deferring six documents for scope
renumbered everything after the fourth batch. It was finally cut from the set of readable
documents, and a corpus repair that converted five unreadable captures into real markdown
renumbered the plan while a burn was running.

Each fix made the derivation cleverer. The correct reading is that a value stamped into
provenance is a fact about the world and not a value to be re-derived from state that
legitimately changes. The plan is now cut once and recorded as an event, and later cuts append
batches after the highest existing identifier rather than renumbering. The reconstruction was
verified against the identifiers already stamped on ingested events before it was frozen.

There is a companion finding about the check that should have caught this. A live consistency
test compared provenance against the raw cut rather than against the plan actually in force,
and it checked only the first batch. It caught the fourth failure by luck, because the
renumbering happened to reach the first batch. It now checks every stamped identifier against
the plan in force.

### 5.7 A guard that stops cleanly, and one that did not

The spend guard refused a batch that had exhausted its declared ceiling, which is the guard
working. The refusal was raised inside a worker thread, propagated out of the extraction call,
and killed the process, leaving a partly extracted batch with no acceptance verdict. Events in
the graph with no acceptance decision are the unmonitored state the acceptance-sampling design
exists to forbid. The exception's own documentation already said callers should treat it as a
clean stop. The caller did not. It now halts at the seam between batches.

The ceiling that refused the batch was itself mis-set, and the diagnosis is worth one sentence
because it is a general trap. The ceiling is a multiple of a running mean, and the mean was
estimated from the last ten observations. Per-batch means across the burn span a narrow range
of roughly 49,000 to 54,000 tokens per chunk, so the underlying quantity is stable, but a
ten-observation window landed on the short closing chunks of two short documents and returned a
value 21 percent below the pooled mean. The 1.3 multiplier exists to absorb variation in the
batch. It cannot also absorb error in the estimator.

## 6. What the field should adopt

Four practices generalize beyond this system. None of them is expensive, and each was learned
by the corresponding failure rather than designed in advance.

The first is gate-unit commensurability. Before pre-registering a threshold, state the unit the
threshold counts and the instrument that will validate it, and confirm the instrument can
measure that unit. This is a one-line check that would have saved three arms of work here.

The second is mutation-verified monitors. A quality gate is code, and untested gate code fails
silently in the direction of passing. Every gate and monitor in this system is mutation-tested,
and the mutation matrix has caught defects in the monitors at a rate that the test suite alone
never approached. The recurring failure is a test that measures an artifact rather than the
generator, and mutation testing is what surfaces it.

The third is recorded sequencing for mid-task instrument judgment. Pre-registration is not a
promise that no decision will be made after data are seen. It is a mechanism for making the
timing of those decisions auditable. State what changed, when it changed relative to what was
visible, and what mutation confirms the change could not have rescued a failure.

The fourth is identity as a logged fact. Any identifier that is stamped into provenance should
be written to the log at the moment it is assigned, not re-derived later from state that can
move. This is the event-sourcing discipline applied to one more class of value, and it took
four failures here to see that the class included batch identity.

Two of these speak directly to the foils. The wiki pattern's lint and the interchange format's
conformance rules are both coherence instruments, and coherence and correspondence dissociate
in both directions. The pilot's chunked arm demonstrated one direction, with perfect
correspondence at a fabrication rate of 0.0000 and poor completeness at 0.347 of the target
yield. A lint-clean fabricated wiki is the other. The trust and provenance vocabularies those
formats now carry are the right fields with no mechanism to earn them, and a measured evidence
class, an instrument version, and an adjudication state can populate them honestly.

## 7. Limitations

The ground truth is model-defined. A stronger model annotating under a hashed rubric, in a
different task posture from extraction, is not a human gold standard. It is a better
instrumented judgment than the unvalidated comparator count it replaced, which was no judgment
at all, and that is the whole of the claim.

The ground-truth sample is small and unrepresentative of its own comparator, measurably. At n
equal to 5, three chunks are references or boilerplate with ground truth of 0, 0, and 1, so the
arm comparison rests on two informative chunks holding 42 of the 43 ground-truth items. The
comparator admits 12.0 nodes per chunk on those five against 16.95 across all 44, so the draw
sits 29 percent below the comparator's own average because it is reference-heavy. A sound floor
needs stratification by chunk type, which five chunks cannot supply.

Nothing here validates relation extraction. That is 63 percent of the original target and the
whole of the arms' remaining gap, and the system's response was to close bulk relation
extraction rather than to validate it. No claim in this paper covers semantic relations.

The corpus is single-domain and the profile is a single model under a single pinned prompt.
Generalization to other corpora, other models, and other schemas is untested. The production
acceptance sampling is running and its results here are partial [as of 2026-09-01T03:10Z; final
at burn close].

Finally, the judges are models, and the two judge models are from the same family as the
extractor. Rater agreement with the aggregated label runs between 0.909 and 1.000 across runs,
which measures consistency rather than correctness. A human-adjudicated subsample is the
obvious next instrument and it has not been built.

## Prior art

The annotation rubric adapts three published guideline sets, each verified against its source
rather than recalled: most-specific-span conventions from SciERC, the entity class distinction
from ACE 2005 with a recorded divergence in that this rubric excludes on genericity rather than
tagging it, and slot-fill justification with no-outside-knowledge rules from TAC KBP. Each
adaptation is recorded with what was taken and what was deliberately changed.

One convergence is worth reporting against ourselves. The TAC KBP provenance rule, that a
justification span must include some mention of the subject and object and some text supporting
the predicate connecting them, is independently this system's semantic-edge rule, derived from
probe failures at full cost some weeks earlier. The repository re-derived a published guideline
that a literature search would have supplied. The later task adopted the published rule by
citation. Same rule, once expensive and once free, which is the argument for reading the field
before building in it.

Acceptance sampling here follows Dodge and Romig for lot acceptance and Wald for the sequential
test. The extent gate's two features are the text-density and link-density features from the
shallow-text boilerplate detection literature, applied at document level rather than block
level. The consensus labeling is Dawid-Skene.
