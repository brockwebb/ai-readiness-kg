# SI readiness on the USAFacts ladder: a working-group explainer

## The bottom line

- USAFacts built a ladder for making federal data usable by SI (superintelligence), the federal term that replaced AI on 29 September 2026: three tracks, three levels on each, and three basics that come first.
- We put a working check behind each step, then measure sixteen federal statistical agencies against it from the outside, the way a member of the public's assistant would, and place each one on the ladder.
- Eleven of the sixteen reach the first level of the Access track; almost none has reached a higher level, and one whole track, checking the answers the data gives, is not measured yet.

## The ladder

The ladder has three tracks, each a short climb of three levels, with three basics that must hold before any level counts.

- Access: can a program get the data?
- Context: can it understand what it got?
- Evaluation: has anyone checked the answers it gives?

An agency climbs at its own pace, and the first level is worth having on its own. The three basics are that the data is open by default, that it can be found on the open web, and that it carries a clear licence on its page.

```{=typst}
#align(center, image("reports/figures/dn020/1.svg", height: 3.4cm))
```

*Figure one. Three tracks, three levels on each, and three basics that come first.*

## Where it comes from

```{=typst}
#align(center, image("reports/figures/dn020/2.svg", height: 3.4cm))
```

*Figure two. FAIR in 2016, the USAFacts guide in 2025, the USAFacts framework in 2026, and this diagnostic's check on each step.*

**FAIR, 2016.** A set of principles that data should be easy to find, to get, to combine and to reuse, by machines as much as by people.
**The USAFacts guide, 2025.** USAFacts, a heavy user of federal data, set out four plain qualities it wanted: data that is accessible, understandable, accurate and open.
**The USAFacts framework, August 2026.** The same four ideas, rebuilt as three tracks with levels borrowed from SLSA, a maturity ladder from the software industry where each level is a short list of things you can check. Accessible became the Access track, understandable became Context, accurate became Evaluation, and open moved down into the basics.
**This diagnostic.** We put a working check behind each step, test the basics instead of taking them on trust, and mark the parts we cannot yet reach rather than scoring them.

## One check, start to finish

Take the simplest check to follow: does a data page announce, in a form built for machines, that it is a dataset with a name and a description? It needs only one request and follows no links. This is the check the earlier draft walked through, and it is still the plainest, so we keep it.

```{=typst}
#align(center, image("reports/figures/dn020/4.svg", height: 3.8cm))
```

*Figure four. One check from start to finish: the question, what we look at, the reading, the result.*

**What we ask.** Does the page carry a built-in, machine-readable label that says it is a dataset, with a name and a description?
**Where we look.** At the data page itself, reading the label the page sends, without running any of the page's scripts.
**What counts as a pass.** Every data page we looked at carries that label, naming the dataset and describing it.
**What the four results mean.** A check comes back as a pass, a partial pass (some pages carry the label, some do not), a fail, or not measured, when we could not read the page and the reason is recorded. Not measured is never a fail.

## The basics, before the ladder

| Basic check | What it asks | Agencies passing | The bar |
|---|---|---|---|
| The data page is in the site's list of pages | Is the data page listed in the site's own index of pages? | three of sixteen | a published requirement |
| The page labels itself as a dataset | Does the page carry a built-in, machine-readable label naming it a dataset? | one of sixteen | this project's reading |
| The product is listed in the agency's data inventory | Is the product listed in the agency's official data inventory? | zero of sixteen | a published requirement |
| The terms of reuse, under a recognised name | Are the terms of reuse stated on the page under a recognised name? | zero of sixteen | this project's reading |

A basic is passed only when every one of the agency's pages meets it; a page we could not read is left out, never counted as a fail. A check marked a published requirement rests on USAFacts' own words; one marked this project's reading is a bar we set from them.

## The ladder, level by level

| Level | What USAFacts asks for | Our checks | Agencies passing every check | What the next step up asks for |
|---|---|---|---|---|
| Access, level 1 | “Data is published in machine-readable files” | Data offered as a file a program can read; The whole dataset in one download; Whether the site's visitor rules let SI tools in; The interactive data tool answers honestly; What the site states about automated access; The site serves what its own rules permit | eleven of sixteen | “Stable, documented endpoints agents can crawl” |
| Access, level 2 | “Stable, documented endpoints agents can crawl” | A published description of the agency's data service; A front door built for programs; From a data page to the data service, terms, change log and inventory; A change history a program can follow | one of sixteen | “Agent-native interface for live, structured queries” |
| Context, level 1 | “Definitions and units documented for humans” | The methods are readable as plain text | two of sixteen | “Methodology and caveats travel with each dataset” |
| Context, level 2 | “Methodology and caveats travel with each dataset” | The release date, and a link to the latest release | one of sixteen | “Context is machine-readable and citable in an answer” |
| Access level 3, Context level 3, and all of Evaluation | not measured yet | | | |

A count is read level by level on its own, not as a climb, so a higher level can show more agencies than a lower one; a check we could not measure for an agency is left out of that level for it, never a fail.

## What we kept, what we changed

Kept, as USAFacts wrote it: the three tracks and their names, the three levels, the three basics, the ladder shape, and the idea that an agency places itself and decides where to invest next.
Changed: we test the basics instead of taking them on trust, because a basic that is only claimed cannot anchor a level.
Changed: every check has a written rule for what counts as a pass, so two agencies cannot claim the same level for different reasons.
Changed: a level is reported per check, and an agency's place is the highest level where every check we could measure passes; a check we could not measure is left out, never a fail.
Changed: the Evaluation track is shown empty and said to be empty, because building its test is a programme of its own that this diagnostic does not attempt.

## For more

The full check-by-check sheet, the one-page roll-up of this ladder, and the one-page summary for the Council are available on request.

---

*How this was made. These pages were produced by a program from the project's framework record and its most recent round of public web requests, made in October 2026; every count on them is read from that record, not typed by hand. The wording was drafted with Anthropic's Claude Opus 4.8, through Claude Code under a commercial subscription, on 13 November 2026, and is the project's own. This note follows FCSM 26-01 on disclosing the use of generative SI.*

*Built by scripts/dn020_documents_build.py from the framework record at commit b5c940ce3aff.*
