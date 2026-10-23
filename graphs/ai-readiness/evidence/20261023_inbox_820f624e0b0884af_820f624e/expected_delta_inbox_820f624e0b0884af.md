# Expected delta: admitting `inbox_820f624e0b0884af`

Written from the scratch slice against the pre-append baseline. The canary compares against it.

| kind | label / type | expected |
|---|---|---:|
| node | `Document` | +1 |

- a node is +1 iff its (class, id) was not in the pre-append ledger and -1 iff a retraction names one that was; an edge the same by (type, subject, object). Written BEFORE the projection is compared.
