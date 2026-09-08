# ADDENDUM-01 to `cc_tasks/2026-09-08_scan_frame_fss.md` — Tier C: non-FSS federal data publishers, tier-0 legs only

**Date:** 2026-09-08
**Authored by:** Desktop session, after the operator restated the purpose of the comparators. The base task's "no external comparators" line was too strict at tier 0 and is amended; everything else in the base task stands.

**Why the base task was wrong at tier 0.** Tier-0 checks (robots.txt served, sitemap / `llms.txt` / well-known discovery, deep link and bogus-route behaviour, declared machine layer, declare-vs-enforce coherence) are properties of a *host that publishes data*, not of a statistical product. At that level a federal data publisher outside the statistical system is the same kind of thing as one inside it, and the comparison is informative: if the government's own catalog is not machine-legible at tier 0, that is a finding in its own right. Above tier 0 (error-measure fields, vintages, bulk download of a product) the comparison stops being like-for-like, and there Tier C does not appear.

**Amendments (numbered against the base task):**
1. **Frame decision, third bullet.** Replace "No external comparators … data.gov enters as a collector, not as a row" with: *Tier C, reference hosts:* `data.gov` (the federal DCAT catalog, GSA-operated; `catalog.data.gov` is its machine entry point), `nist.gov` with NIST's data portal (`data.nist.gov`) as machine entry point, and `open.gsa.gov` (GSA's developer/API landing) with `gsa.gov` as home. **Tier-0 legs only**, on the machine entry point and home only, reported in a block of their own labelled "reference hosts, not statistical agencies", never in a Tier A or Tier B denominator, never on the agencies × legs matrix. The data.gov DCAT-presence **collector** (§4 gap table) is unchanged and separate from data.gov's role as a Tier C host. StatCan remains out (not a federal publisher; the tier-0 comparison holds for federal hosts under one legal regime, which is what makes it a comparison and not decoration).
2. **§1 roster.** Tier C is not on the ICSP source and is not parsed from it; it is declared in `params.frame.tier_c` with the reason above and registered on `fss_roster_2026-09` under its own key, `tier: C`, `source: operator declaration 2026-09-08`.
3. **§2 selection.** Tier C: home and machine entry point as declared; no product listing, no flagship rule.
4. **§3 pre-flight.** Tier C hosts included, same probes, Results suffixed the same way.
5. **§5 DD.** The frame DD records Tier C with the tier-0-only restriction and the reason, and states explicitly that any figure placing a Tier C host beside a Tier A agency above tier 0 is a category error the page refuses to render (assert in the figure test: no Tier C row in F2, no Tier C point in F1 for a leg outside `params.tier0.legs`).
6. **§6 gate.** Add: Tier C hosts have pre-flight Results; F-test assertion from item 5 passes.

Unchanged: §0, §4, everything on manners and network bounds (Tier C adds at most ~6 requests in pre-flight).

**SEQUENCING:** unchanged; Tier C rides along inside §1, §2, §3, §5, §6.
