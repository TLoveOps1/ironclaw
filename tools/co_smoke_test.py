import requests
import time
import os
import uuid
from pathlib import Path

LEDGER_URL = "http://127.0.0.1:8010"
VAULT_URL = "http://127.0.0.1:8011"
WORKER_URL = "http://127.0.0.1:8012"
CO_URL = "http://127.0.0.1:8013"

def check_health(name, url):
    try:
        resp = requests.get(f"{url}/health", timeout=5)
        if resp.status_code == 200:
            print(f"{name} service OK.")
            return True
    except Exception as e:
        print(f"ERROR: {name} service not running at {url}: {e}")
    return False

def test_co_e2e():
    if not all([
        check_health("Ledger", LEDGER_URL),
        check_health("Vault", VAULT_URL),
        check_health("Worker", WORKER_URL),
        check_health("CO", CO_URL)
    ]):
        return False

    REQUEST_ID = f"co_smoke_{int(time.time())}"
    print(f"Starting CO E2E smoke test for request {REQUEST_ID}...")

    # 1. First Call
    print("CO: Sending /chat request...")
    payload = {
        "message": "Say 'IronClaw' and nothing else.",
        "request_id": REQUEST_ID,
        "model": "meta-llama/Llama-3.3-70B-Instruct"
    }
    resp = requests.post(f"{CO_URL}/chat", json=payload, timeout=900)
    resp.raise_for_status()
    data = resp.json()
    
    print(f"CO Response Status: {data['status']}")
    if data["status"] != "completed":
        print(f"ERROR: CO failed: {data.get('error')}")
        return False
    
    print(f"CO Answer: {data['answer']}")
    if "ironclaw" not in data["answer"].lower():
        print(f"ERROR: Unexpected answer: {data['answer']}")
        return False

    RUN_ID = data["run_id"]
    ORDER_ID = data["order_id"]
    FIRST_HEAD = data["order_head"]
    ARCHIVE_PATH = data.get("archive_path")
    
    if not ARCHIVE_PATH:
        print("ERROR: Missing archive_path in response (cleanup should have happened)")
        return False
    
    print(f"Run {RUN_ID} Order {ORDER_ID} completed. Head: {FIRST_HEAD}")
    print(f"Archive created at: {ARCHIVE_PATH}")

    # 2. Idempotency Test
    print("CO: Testing idempotency with same request_id...")
    resp = requests.post(f"{CO_URL}/chat", json=payload, timeout=900)
    resp.raise_for_status()
    data2 = resp.json()
    
    if data2["run_id"] != RUN_ID or data2["order_id"] != ORDER_ID:
        print(f"ERROR: Idempotency failed (ID mismatch): {data2['run_id']} != {RUN_ID}")
        return False
        
    if data2["order_head"] != FIRST_HEAD:
        print(f"ERROR: Idempotency failed (Divergent HEAD): {data2['order_head']} != {FIRST_HEAD}")
        return False
    
    print("Idempotency OK (same IDs and same HEAD returned).")

    # 3. Verify Ledger Events
    print("Verifying Ledger events...")
    resp = requests.get(f"{LEDGER_URL}/events?order_id={ORDER_ID}")
    resp.raise_for_status()
    events = resp.json()
    types = [e["event_type"] for e in events]
    print(f"Found events: {types}")
    
    expected = [
        "RUN_CREATED", "ORDER_CREATED", "ORDER_QUEUED", 
        "ORDER_WORKTREE_REQUESTED", "ORDER_WORKTREE_READY",
        "ORDER_RUNNING", "ORDER_COMPLETED", "RUN_COMPLETED",
        "ORDER_ARCHIVED"
    ]
    
    missing = [t for t in expected if t not in types]
    if missing:
        print(f"ERROR: Missing expected events: {missing}")
        return False
    
    # Assert stable event counts (exactly 1 of each lifecycle type)
    for t in expected:
        count = types.count(t)
        if count != 1:
            print(f"ERROR: Event {t} has count {count} in Ledger (expected 1)")
            return False

    print("Ledger verification OK (exactly 1 of each event, no duplication).")
    print("\nCO E2E SMOKE TEST SUCCESS")
    return True

if __name__ == "__main__":
    if not test_co_e2e():
        exit(1)
