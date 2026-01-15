#!/bin/bash
# Phase v1.1 Smoke Test
set -e

# Configuration
export IRONCLAW_CO_URL="http://127.0.0.1:8013"
export IO_INTELLIGENCE_API_KEY="sk-smoke-test"
export IO_INTELLIGENCE_BASE_URL="http://127.0.0.1:8099/v1"
REPO_DIR=$(pwd)
CLI="./garrison/cli/ironclaw.py"

echo "--- 1. Starting Mock Model Server ---"
python3 tools/mock_model_server.py &
MOCK_PID=$!
sleep 2

echo "--- 2. Starting IronClaw Stack ---"
$CLI stack down || true
fuser -k 8010/tcp 8011/tcp 8012/tcp 8013/tcp 8014/tcp || true

export KEEP_WORKTREE="true"
export IRONCLAW_THEATER="default"
rm -rf theaters/default/vault_cache || true
$CLI stack up --theater default

# Ensure sample prompt exists
mkdir -p theaters/default/repo/prompts
echo "Hello from template. Message: {{message}}" > theaters/default/repo/prompts/hello.txt

echo "--- 3. First Execution (External Model Call) ---"
REQ_ID="smoke-$(date +%s)"
$CLI chat "First message" --request-id "$REQ_ID" --theater default --profile executor_default --template hello.txt --json > first_res.json
RES_1=$(cat first_res.json)
ORDER_ID=$(python3 -c "import sys, json; print(json.load(sys.stdin)['order_id'])" < first_res.json)
echo "Order ID: $ORDER_ID"

echo "--- 4. Verify First Execution Events ---"
sleep 2 # Give it time to settle
EVENTS=$(curl -s "http://127.0.0.1:8010/events?order_id=$ORDER_ID")
# Debug: echo "$EVENTS"
STARTED_COUNT=$(python3 -c "import sys, json; events=json.load(sys.stdin); print(len([e for e in events if e['event_type'] == 'worker.model_call.started']))" <<< "$EVENTS")
COMPLETED_COUNT=$(python3 -c "import sys, json; events=json.load(sys.stdin); print(len([e for e in events if e['event_type'] == 'worker.model_call.completed']))" <<< "$EVENTS")

if [ "$STARTED_COUNT" -ne 1 ]; then 
    echo "FAILED: Expected 1 started event, got $STARTED_COUNT"; 
    echo "Recent Ledger events for $ORDER_ID:"
    echo "$EVENTS" | python3 -m json.tool
    exit 1; 
fi
if [ "$COMPLETED_COUNT" -ne 1 ]; then echo "FAILED: Expected 1 completed event, got $COMPLETED_COUNT"; exit 1; fi

MOCK_CALLS_1=$(curl -s http://127.0.0.1:8099/calls | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])")
echo "Mock calls after first run: $MOCK_CALLS_1"
if [ "$MOCK_CALLS_1" -ne 1 ]; then echo "FAILED: Expected 1 mock call, got $MOCK_CALLS_1"; exit 1; fi

echo "--- 5. Second Execution (New Order, Same Fingerprint) ---"
REQ_ID_2="smoke-2-$(date +%s)"
$CLI chat "First message" --request-id "$REQ_ID_2" --theater default --profile executor_default --template hello.txt --json > second_res.json
RES_2=$(cat second_res.json)
ORDER_ID_2=$(python3 -c "import sys, json; print(json.load(sys.stdin)['order_id'])" < second_res.json)
echo "Order ID 2: $ORDER_ID_2"

echo "--- 6. Verify Caching ---"
sleep 2
MOCK_CALLS_2=$(curl -s http://127.0.0.1:8099/calls | python3 -c "import sys, json; print(json.load(sys.stdin)['count'])")
echo "Mock calls after second run: $MOCK_CALLS_2"

if [ "$MOCK_CALLS_2" -ne 1 ]; then echo "FAILED: Expected still 1 mock call (fingerprint cache hit), got $MOCK_CALLS_2"; exit 1; fi

# Check theater-global vault_cache (Requirement confirmation)
CACHE_DIR="theaters/default/vault_cache/intelligence"
if [ ! -d "$CACHE_DIR" ]; then echo "FAILED: Global cache dir $CACHE_DIR not found"; exit 1; fi
CACHE_FILE_COUNT=$(ls -1 "$CACHE_DIR" | wc -l)
if [ "$CACHE_FILE_COUNT" -eq 0 ]; then echo "FAILED: No files found in global cache $CACHE_DIR"; exit 1; fi
echo "Global cache verified: $CACHE_FILE_COUNT files in $CACHE_DIR"

# Check AAR 2 for cache_hit: true
WT_PATH_2="theaters/default/worktrees/$ORDER_ID_2"
if [ ! -d "$WT_PATH_2" ]; then
    WT_PATH_2="theaters/demo/worktrees/$ORDER_ID_2"
fi

CACHE_HIT=$(python3 -c "import sys, json; print(json.load(sys.stdin).get('cache_hit', ''))" < "$WT_PATH_2/aar.json")
echo "AAR 2 cache_hit: $CACHE_HIT"
if [ "$CACHE_HIT" != "True" ] && [ "$CACHE_HIT" != "true" ]; then echo "FAILED: Expected cache_hit: true in AAR 2, got '$CACHE_HIT'"; exit 1; fi

echo "--- 7. Verify Ledger Events ---"
EVENTS_2=$(curl -s "http://127.0.0.1:8010/events?order_id=$ORDER_ID_2")
COMPLETED_COUNT_2=$(python3 -c "import sys, json; events=json.load(sys.stdin); print(len([e for e in events if e['event_type'] == 'worker.model_call.completed']))" <<< "$EVENTS_2")
CACHE_HIT_EVENT=$(python3 -c "import sys, json; events=json.load(sys.stdin); e=[e for e in events if e['event_type'] == 'worker.model_call.completed'][0]; print(json.loads(e['payload'])['cache_hit'])" <<< "$EVENTS_2")

if [ "$COMPLETED_COUNT_2" -ne 1 ]; then echo "FAILED: Expected 1 completed event for order 2, got $COMPLETED_COUNT_2"; exit 1; fi
if [ "$CACHE_HIT_EVENT" != "True" ] && [ "$CACHE_HIT_EVENT" != "true" ]; then echo "FAILED: Expected cache_hit: true in Ledger event for order 2"; exit 1; fi

echo "--- 8. Verify Ledger Payload Constraints ---"
# Check that no raw text is in the NEW model Ledger events
MODEL_EVENTS=$(echo "$EVENTS" | python3 -c "import sys, json; events=json.load(sys.stdin); print(json.dumps([e for e in events if 'worker.model_call' in e['event_type']]))")
RAW_COUNT=$(echo "$MODEL_EVENTS" | grep -i "First message" | wc -l)
if [ "$RAW_COUNT" -gt 0 ]; then echo "FAILED: Raw prompt text found in new Ledger model events"; exit 1; fi

echo "--- SMOKE TEST PASSED ---"

# Cleanup
$CLI stack down
kill $MOCK_PID || true
