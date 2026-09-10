# Suite tiers. `cc_tasks/2026-09-09_guards_earn_their_keep.md` decision 4.
#
# No test is removed or weakened by the split. A marker decides which tier waits for what:
#
#   gate-fast  the per-task gate. Everything except `slow`, which is the loopback control
#              cycles at the standing 1 req/s and the re-derivation of payloads older than the
#              two most recent cycles.
#   gate-task  what a task's gate actually is: the fast tier PLUS the re-derivation of every
#              payload the task could have touched. If a rule or the engine changed, that is
#              all of them, and `RECENT=` is how you say so.
#   gate-full  the pre-push check, under the long-running protocol (CLAUDE.md): detached,
#              logged to logs/, polled to EXIT.
#
# The point of the split is that a two-minute gate exists at all. The full suite still runs
# before every push, and a green fast tier is never reported as a green suite.

PY := /opt/anaconda3/bin/python3
LOGS := logs

.PHONY: gate-fast gate-task gate-full guards

gate-fast:
	$(PY) -m pytest tests/ assessment/ -q -m "not slow"

## Re-derivation of every stored payload, whatever its age. Run this whenever a rule module,
## the rule registry, or the re-derivation engine changed.
gate-task: gate-fast
	$(PY) -m pytest tests/test_scan_harness_v4.py -q -k re_derives

## Every guard against the incident it was built for.
guards:
	$(PY) -m pytest tests/test_guards_replay_their_incidents.py -q

gate-full:
	@mkdir -p $(LOGS)
	nohup sh -c '$(PY) -m pytest tests/ assessment/ -q; echo EXIT=$$? >> $(LOGS)/suite.log' \
		> $(LOGS)/suite.log 2>&1 & \
	echo "started; poll with: tail -5 $(LOGS)/suite.log"
