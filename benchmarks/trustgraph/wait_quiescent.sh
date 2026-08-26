#!/bin/sh
# Wait until the onto-bench extraction is quiescent: no new usage-JSONL line
# AND no new kg-extract-ontology "Extracting" line for IDLE_SECS.
# Usage: wait_quiescent.sh [IDLE_SECS] [MAX_SECS]
IDLE=${1:-180}
MAX=${2:-7200}
USAGE=/tmp/claude-cli-backend-usage.jsonl
start=$(date +%s)
last_n=$(wc -l < $USAGE)
last_e=$(docker logs trustgraph-ingest-1 2>&1 | grep -c "Extracting ontology-based")
last_change=$(date +%s)
while :; do
  sleep 20
  n=$(wc -l < $USAGE)
  e=$(docker logs trustgraph-ingest-1 2>&1 | grep -c "Extracting ontology-based")
  now=$(date +%s)
  if [ "$n" != "$last_n" ] || [ "$e" != "$last_e" ]; then
    last_n=$n; last_e=$e; last_change=$now
  fi
  if [ $((now - last_change)) -ge "$IDLE" ]; then
    echo "QUIESCENT n=$n extracting=$e at $now"
    exit 0
  fi
  if [ $((now - start)) -ge "$MAX" ]; then
    echo "TIMEOUT n=$n extracting=$e at $now"
    exit 1
  fi
done
