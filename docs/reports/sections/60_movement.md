## What moved since the previous cycle, and what moved it

The instrument moved, and the frame moved with it. Four checks changed rule between the two
cycles, and the frame went from thirteen bodies plus a foreign statistical office to
{{result:fss_agencies_tier_a:value}} plus three reference hosts. A reader who compares a rate
across the two is comparing two instruments over two populations.

![Pass rate per check, previous cycle beside this one]({{figure:cycle_over_cycle_2026-09-09:path}})

The figure marks every check whose rule changed as not comparable, and it draws no line and no
arrow between the two points. A difference between two measurements is not a direction of
travel, and two cycles taken a day apart on federal publication schedules are not a rate of
change.

The rule changes were all instances of one defect, found three times and fixed three times: a
check was reaching a verdict about a probe nobody had observed. A connection closed mid-request
was being read as a product failing rather than as the scanner failing to see. Each fix turns
those cases into `error`, which is why the `error` counts in this report are larger than a
naive reading of a previous cycle would suggest, and why they should be. Each change was
demonstrated against local fixtures before the cycle ran. Those fixtures' expected verdicts are
now derived from what each collector actually dispatches, rather than written by hand, because
a hand-written expectation turned out once to be wrong.
