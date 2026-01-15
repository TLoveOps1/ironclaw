#!/bin/bash
set -e

# Configuration
IRONCLAW_DIR="/home/tlove96/ironclaw"
OBSERVER_URL="http://127.0.0.1:8014"
LEDGER_URL="http://127.0.0.1:8010"
THEATER_ROOT="/home/tlove96/ironclaw/theaters"

echo "=== Phase F Observer Smoke Test ==="

# Check health
if ! curl -s "$OBSERVER_URL/healthz" > /dev/null; then
    echo "ERROR: Observer service not running at $OBSERVER_URL"
    exit 1
fi

echo "1. Testing Orphan Detection..."
mkdir -p "$THEATER_ROOT/demo/worktrees/orphan_test_$(date +%s)"
# Wait for one poll cycle (we'll set it short in the test run)
sleep 5

# Check Observer status
ALERTS=$(curl -s "$OBSERVER_URL/alerts")
if [[ "$ALERTS" == *"orphan_worktree"* ]]; then
    echo "Orphan detection OK."
else
    echo "ERROR: Orphan alert not found in $ALERTS"
    # exit 1 (We'll continue to see other errors)
fi

echo "2. Testing Stall Detection (Simulated)..."
# Inject a 'running' event into Ledger without a following completion
STALL_OID="order_stall_$(date +%s)"
curl -s -X POST "$LEDGER_URL/events" -H "Content-Type: application/json" -d "{
    \"event_id\": \"stall-sim-$STALL_OID\",
    \"event_type\": \"ORDER_RUNNING\",
    \"order_id\": \"$STALL_OID\",
    \"payload\": {
        \"status\": \"running\",
        \"theater\": \"demo\",
        \"objective\": \"Simulated stall\"
    }
}" > /dev/null

echo "Waiting for stall detection (STALL_SECONDS should be low)..."
sleep 5

ALERTS=$(curl -s "$OBSERVER_URL/alerts")
if [[ "$ALERTS" == *"stalled"* ]]; then
    echo "Stall detection OK."
else
    echo "ERROR: Stall alert not found in $ALERTS"
fi

echo "3. Testing Integrity Failure (Simulated)..."
INTEGRITY_OID="order_integrity_$(date +%s)"
WT_DIR="$THEATER_ROOT/demo/worktrees/$INTEGRITY_OID"
mkdir -p "$WT_DIR"
# Inject a 'completed' event but NO aar.json exists
curl -s -X POST "$LEDGER_URL/events" -H "Content-Type: application/json" -d "{
    \"event_id\": \"integrity-sim-$INTEGRITY_OID\",
    \"event_type\": \"ORDER_COMPLETED\",
    \"order_id\": \"$INTEGRITY_OID\",
    \"payload\": {
        \"status\": \"completed\",
        \"theater\": \"demo\",
        \"worktree\": \"$WT_DIR\"
    }
}" > /dev/null

sleep 5

ALERTS=$(curl -s "$OBSERVER_URL/alerts")
if [[ "$ALERTS" == *"integrity_failed"* ]]; then
    echo "Integrity failure detection OK."
else
    echo "ERROR: Integrity alert not found in $ALERTS"
fi

echo -e "\nPHASE F OBSERVER SMOKE TEST FINISHED"
