# ADDENDUM 01 — `cc_tasks/2026-09-15_standing_dispatcher.md`

**Date:** 2026-09-15. **Amends, does not supersede.** Authored from `cc_tasks/2026-09-15_claude_md_cites_dn005_RESULT.md` §6 item 1: DN-005 §5 rule 1 (every task file names the framework layer it advances, or says it is hygiene) is now cited from the bootloader and binds authorship, and nothing enforces it.

**Amendment to decision 2 (candidate set).** A task is a candidate only when its file carries all three headers: `**Spend:**`, `**Network:**` and `**Framework layer served`. The third is parsed for presence and for one of: a DN-005 §2 layer reference (`§2.1` to `§2.5`, or the word `Tier` followed by `M`, `O` or `D`), or the word `none` (a hygiene task). A file with the header but none of those values is not a candidate and `seldon dispatch status` says which header failed. The dispatcher does not judge whether the named layer is the right one; it asserts that a layer was named, which is what the rule requires and what a reader would otherwise have to check by hand. Add a fixture task file failing exactly this criterion to the §1 test set, and the header value to the `dispatch_launched` event's criteria vector.

**Amendment to decision 3 (`CLAUDE.md` sentences).** The sentence recording the supersession marker also states the three-header candidacy rule in one clause, so the bootloader says what makes a task dispatchable.

Nothing else in the base task changes. DN-006 gains no addendum for this: decision 2's table is extended by one row in the implementing code, and the RESULT records the row.
