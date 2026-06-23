# Inventory-as-Pointer — a HARD scope constraint for the probe harness
*CC task 2026-06-23, Stage 3. This is design history that must survive: the
constraint is easy to violate by accident and expensive to walk back.*

## The constraint
**M-25-21 AI use-case inventories are SELF-REPORTED and inflation-prone. They are
NEVER a scored metric in this harness.** No score is computed from inventory
contents — not directly, not as a feature, not as a tiebreaker. The scored
instrument is reality-based probing of public endpoints only (no PMT: if a human
types it, it is not a benchmark input).

## Why an inventory cannot be scored
A thin or empty AI use-case inventory is **ambiguous by construction**. It can mean:
- genuine under-use (the agency really does little AI), OR
- under-reporting (they do more than they wrote down), OR
- a conservative definition of "AI use case" (they scope the term narrowly).

The probe cannot distinguish these from the inventory alone. Scoring it would
manufacture a number whose meaning we cannot defend — exactly the performative
metric theater the whole design exists to burn down. A self-attested artifact
scored as if it were measured is the cleanest possible Goodhart target.

## What an inventory MAY be used for (later, not here)
An inventory is a legitimate **pointer**: *where to look*, not *how good it is*. A
thin inventory is a **lead** for a future internal-assessment instrument (the thin
practitioner layer in the design memo — symptom-based, collected direct from
practitioners, anti-laundering). It tells a human investigator which agencies and
which programs to ask about. It is out of scope for the scored harness and is
recorded here as future internal-assessment input only.

## How this is enforced in code
There is no inventory probe, no inventory module, no inventory field in any
`ProbeResult`, and no inventory term in any rollup. The absence is the enforcement.
If a future change proposes reading an inventory, it must route through a separate
internal-assessment tool and must not emit a score — re-read this note first.

See also: `benchmark_rubric.md` (no self-attested fields; anti-PMT exclusions) and
the design memo's "thin practitioner instrument" layer.
