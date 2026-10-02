# DN-010: a value-by-effort prioritization view, kept apart from the score

**Date:** 2026-10-02
**Status:** operator decision 2026-10-02, recorded by the Desktop session
**Amends:** DN-009 decision 3 (no ROI language). Decision 3 stands for the composite score and for any claim of impact or return; this note carves out one view.

## 1. What was decided

The operator's position: the project is a decision support system, not only a diagnosis. A result that names a failing indicator must lead to an action, and a decision maker must be able to see which actions are cheap and which are worth doing. Cheap, free things are defined as the lowest effort. Effort and value are each rated on a five-point ordinal scale, and the two form a matrix. His example: a well-formed `robots.txt` and an `llms.txt` are low effort and high value.

## 2. The arrangement

1. **Two objects, never mixed.** The score stays as DN-009 decision 3 and page H say: equal weights, no weighting asserted, every rank resting on one leg. The prioritization view is a separate table with its own columns. A value rating is never an input to the score, a rank or a bound.
2. **Effort, two dimensions.** `staffing_band` and `cost_band` each 1 to 5 or `TBD`. The matrix axis `effort_level` is the higher of the two when both are known; a row with either `TBD` is listed beside the matrix, not placed in it. Free and no staffing beyond running it is 1.
3. **Value, one dimension, defined by a rubric written before any rating.** Value is how much a failing result keeps a reader or a machine from reaching, understanding or using the data (discovery, access, interpretation, fitness for use). 5: the data is unreachable or unusable by a machine reader. 1: cosmetic. Prior art is searched for the rubric's shape (impact and effort matrices, the Eisenhower grid this project already uses for issues, composite-indicator practice) and cited.
4. **Every value carries its grounds.** `value_basis` is `evidence` (a cited source says the action does what is claimed), `rubric` (rated by the rubric with no outside evidence) or `TBD`. An `evidence_grade` of `established`, `plausible` or `unevidenced` rides with it. An example of why: whether crawlers read `llms.txt` is a claim that needs a source; `robots.txt` has RFC 9309. A high rating on an unevidenced action is shown as exactly that.
5. **A judgment is labelled as one.** `rated_by` names the rubric version and who applied it; `operator_override` is a separate column, empty until used. The view says in one line on every rendering that value is a rated judgment under a stated rubric, not a measurement.
6. **Wording.** "Quick win", "effort" and "value rating" are allowed in this view, and in the summary only with that one-line label. "ROI", "impact" and "return" remain forbidden anywhere, because they imply a weighting the score does not have.
7. **Gaming.** Cheap-pass exposure (can the pass condition be met without serving a reader?) is a column beside the value rating, so a high-value, cheap-to-fake action is visible as that.

## 3. What this does not decide

Who sets the rubric's anchors beyond version 1; whether any weighting is ever adopted for the score (that still needs its own note); costs in dollars or hours (bands only, `TBD` allowed).

## 4. Where it lands

The scan catalog task (`aaffd0db`) carries it by addendum. The matrix covers scans and, more importantly, the actions the record prescribes when a scan fails. The one-page summary may draw its single table from the quick-win cell; the operator dictates it.
