## Three bodies will not serve a compliant machine

{{result:fss_hosts_refusing_identified_client_2026-09:value}} bodies of
{{result:fss_agencies_tier_a:value}} decline to answer a client that identifies itself, says where to complain about
it, asks for no more than one page per second, and obeys the `robots.txt` those same hosts
publish. They are the Bureau of Labor Statistics, the Bureau of Transportation Statistics and
the Social Security Administration's research office. Each returns a refusal status on
effectively every request. Their rows above read `error` throughout, which is the correct
reading: this instrument did not find those sites wanting, it was not allowed to look.

The behaviour is neither a transient nor a sampling accident. It has now been recorded in
{{result:scan_refusal_consecutive_measurements_2026-09-10_rj2:value}} separate measurements,
taken on four different days under two different user-agent strings. The count survives a change in how this project names errors: the earliest
filed the refusal under a general client-error class, because the closed set of names had no
member for a refusal until later. The number of bodies refusing has not moved, standing at
{{result:fss_hosts_refusing_identified_client_2026-09:value}} on the first look and the same on
the most recent.

Two things follow, and only two. First, the coherence check fails on all three: each publishes
a `robots.txt` that grants access and then refuses the client that honours it. Whatever the
intent, the machine-readable statement and the machine-observable behaviour disagree, and a
client has no way to discover which one is real except by being turned away. Second, no rate in
this report describes them, and none can. They are in the frame, they are counted in the
denominator of nothing, and the space they occupy in the matrix is the shape of what is not
known.

What does not follow is any account of why. This scanner sees a status code. Bot management, a
content delivery configuration, a deliberate policy and an unnoticed default all look identical
from outside, and the only honest thing to report is the behaviour and its persistence.
Distinguishing them needs either the operator's own logs or a request made from a different
vantage point, and both are named as future research rather than guessed at here.

In the previous cycle a fourth body could not be observed either, for an unrelated reason: its
host timed out or closed the connection on most probes. It answered this time, and the three
refusing bodies are now the whole of the unobserved column — which is why the `error` counts in
the matrix are lower here than a reader of the last cycle would expect, and why they still are
not zero.
