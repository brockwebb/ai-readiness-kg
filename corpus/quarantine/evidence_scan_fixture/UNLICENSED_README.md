# `unlicensed/` — evidence writes redirected out of the committed store

DD-063 decision 3. `corpus/evidence/scan/` is the one `corpus/` lane this repo commits, because
the bytes there are what a Finding cites and a Finding whose evidence the repo does not hold is
not evidence. Only a scan cycle may add to it.

`model.store_evidence` writes there only when `AIRKG_SCAN_CYCLE` is set, and only
`run.py::main` sets it. Any other caller that does not name an explicit root has its bytes
redirected into `unlicensed/` and a line appended to `unlicensed/redirects.jsonl` recording
what was requested, where it went, why, and the argv that did it.

**The directory is gitignored; the finding lives in the log, not in the bodies.** Committing
redirected bytes would recreate one directory over exactly the problem the redirect prevents.

## Why it exists

Twice in two consecutive tasks a fixture driver run from a script filled the committed store
with loopback bodies that no Observation cited: 29 in `2026-09-09_closeout_and_manners`, and
18 more from that task's own control-gate driver. The standing guard is `tests/conftest.py`,
which redirects the store under pytest and cannot see a script.

A redirect rather than a refusal, deliberately: the caller is usually a collector deep inside a
driver with no way to choose another root, and raising would turn "you wrote litter" into
"your script crashed".
