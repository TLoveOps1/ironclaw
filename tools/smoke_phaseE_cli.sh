#!/bin/bash
set -e

# Configuration
IRONCLAW_DIR="/home/tlove96/ironclaw"
CLI_PATH="$IRONCLAW_DIR/garrison/cli/ironclaw.py"
CO_URL="http://127.0.0.1:8013"
LEDGER_URL="http://127.0.0.1:8010"

echo "=== Phase E CLI Smoke Test ==="

# Check if services are running
if ! curl -s "$CO_URL/health" > /dev/null; then
    echo "ERROR: CO service not running at $CO_URL"
    exit 1
fi

export IRONCLAW_CO_URL="$CO_URL"

# 1. Initial Chat
echo "1. Sending initial chat..."
OUTPUT1=$(python3 "$CLI_PATH" chat "Say 'IronClaw' and nothing else." --new)
echo "$OUTPUT1"

REQ_ID1=$(echo "$OUTPUT1" | grep "REQUEST ID" | awk '{print $NF}')
RUN_ID1=$(echo "$OUTPUT1" | grep "RUN ID" | awk '{print $NF}')
ORDER_ID1=$(echo "$OUTPUT1" | grep "ORDER ID" | awk '{print $NF}')

if [ -z "$REQ_ID1" ] || [ -z "$RUN_ID1" ]; then
    echo "ERROR: Failed to capture IDs from output."
    exit 1
fi

# 2. Retry
echo -e "\n2. Retrying with --retry..."
OUTPUT2=$(python3 "$CLI_PATH" chat --retry)
echo "$OUTPUT2"

REQ_ID2=$(echo "$OUTPUT2" | grep "REQUEST ID" | awk '{print $NF}')
RUN_ID2=$(echo "$OUTPUT2" | grep "RUN ID" | awk '{print $NF}')
ORDER_ID2=$(echo "$OUTPUT2" | grep "ORDER ID" | awk '{print $NF}')

if [ "$REQ_ID1" != "$REQ_ID2" ]; then
    echo "ERROR: Request ID mismatch on retry: $REQ_ID1 vs $REQ_ID2"
    exit 1
fi

if [ "$RUN_ID1" != "$RUN_ID2" ] || [ "$ORDER_ID1" != "$ORDER_ID2" ]; then
    echo "ERROR: Run/Order ID mismatch on retry. Expected idempotency."
    exit 1
fi

echo -e "\nIdempotency confirmed (REQ_ID, RUN_ID, ORDER_ID identical)."

# 3. Verify Ledger (No duplicate events)
echo -e "\n3. Verifying Ledger for stable event counts..."
EVENT_COUNT=$(curl -s "$LEDGER_URL/events?order_id=$ORDER_ID1" | python3 -c "import sys, json; print(len([e for e in json.load(sys.stdin) if e['event_type'] == 'ORDER_CREATED']))")

if [ "$EVENT_COUNT" -ne 1 ]; then
    echo "ERROR: Found $EVENT_COUNT ORDER_CREATED events in Ledger. Should be exactly 1."
    exit 1
fi

echo "Ledger verification OK (exactly 1 ORDER_CREATED event)."

echo -e "\nPHASE E CLI SMOKE TEST SUCCESS"
