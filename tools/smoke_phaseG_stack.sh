#!/bin/bash
set -e

# Configuration
IRONCLAW_DIR="/home/tlove96/ironclaw"
CLI_PATH="$IRONCLAW_DIR/garrison/cli/ironclaw.py"
THEATER="demo"

echo "=== Phase G Stack Smoke Test ==="

# 1. Clean up any existing state/procs (safety first)
python3 "$CLI_PATH" stack down || true
rm -f "$IRONCLAW_DIR/garrison/ledger_service/ledger.db"

# 2. Stack UP
echo "1. Starting the stack..."
python3 "$CLI_PATH" stack up --theater "$THEATER"

# 3. Verify status
echo -e "\n2. Verifying status..."
python3 "$CLI_PATH" stack status

# 4. Run a mission through the CLI
echo -e "\n3. Running mission through CLI..."
export IRONCLAW_CO_URL="http://127.0.0.1:8013"
export IOINTELLIGENCE_API_KEY=io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjUxMGYzNjFkLWVjY2UtNGQ1My05ZWM2LWUyYjVlNGEzMjY5NCIsImV4cCI6NDkyMjAzNzQ1NH0.JL9NQMxZwhINHsc-d6eNZjBPK_-EfnX_DXJH353SvXebGmzbPYPb9t3LN5PNXTPTlEVL8Ecpjk3abDLuSKUH1A
python3 "$CLI_PATH" chat "Say 'Stack Success' and nothing else." --new

# 5. Check logs
echo -e "\n4. Checking logs..."
python3 "$CLI_PATH" stack logs all --tail 10

# 6. Stack DOWN
echo -e "\n5. Stopping the stack..."
python3 "$CLI_PATH" stack down

# 7. Final check
echo -e "\n6. Final status check..."
python3 "$CLI_PATH" stack status

echo -e "\nPHASE G STACK SMOKE TEST SUCCESS"
