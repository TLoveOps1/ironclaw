import requests
import time
import sys
import subprocess
import json
from pathlib import Path

# URLs
LEDGER_URL = "http://127.0.0.1:8010"
VAULT_URL = "http://127.0.0.1:8011"
WORKER_URL = "http://127.0.0.1:8012"

THEATER = "demo"
ORDER_ID = f"worker_smoke_{int(time.time())}"
RUN_ID = f"run_{int(time.time())}"

def test_worker_e2e():
    print(f"Starting Worker E2E smoke test for order {ORDER_ID}...")

    # 1. Check services
    for name, url in [("Ledger", LEDGER_URL), ("Vault", VAULT_URL), ("Worker", WORKER_URL)]:
        try:
            requests.get(f"{url}/health", timeout=2).raise_for_status()
            print(f"{name} service OK.")
        except Exception as e:
            print(f"ERROR: {name} service not running at {url}: {e}")
            return False

    # 2. Vault: Create worktree
    print("Vault: Creating worktree...")
    resp = requests.post(f"{VAULT_URL}/worktrees", json={
        "theater": THEATER,
        "order_id": ORDER_ID
    })
    resp.raise_for_status()
    wt_path = resp.json()["path"]
    print(f"Worktree ready at {wt_path}")

    # 3. Worker: Execute
    print("Worker: Executing order...")
    resp = requests.post(f"{WORKER_URL}/execute", json={
        "run_id": RUN_ID,
        "order_id": ORDER_ID,
        "worktree_path": wt_path,
        "objective": "Test worker execution",
        "prompt": "Say 'hello world' and nothing else.",
        "model": "meta-llama/Llama-3.3-70B-Instruct" # Using a known model from demo Theater
    })
    resp.raise_for_status()
    data = resp.json()
    if data["status"] != "completed":
        print(f"ERROR: Worker failed: {data.get('error')}")
        return False
    print(f"Worker completed. Order HEAD: {data['order_head']}")
    first_head = data["order_head"]
    wt = Path(wt_path)
    first_output = (wt / "outputs" / "model_output.txt").read_text()

    # 4. Worker: Idempotency (Short-circuit)
    print("Worker: Testing idempotency short-circuit...")
    resp = requests.post(f"{WORKER_URL}/execute", json={
        "run_id": RUN_ID,
        "order_id": ORDER_ID,
        "worktree_path": wt_path,
        "objective": "Test worker execution",
        "prompt": "Say 'hello world' and nothing else.",
        "model": "meta-llama/Llama-3.3-70B-Instruct"
    })
    resp.raise_for_status()
    data = resp.json()
    if data["status"] != "completed":
        print(f"ERROR: Idempotency retry failed: {data.get('error')}")
        return False
    if data["order_head"] != first_head:
        print(f"ERROR: Idempotency failed (divergent HEAD): {data['order_head']} != {first_head}")
        return False
    
    # Assert artifacts haven't changed
    current_output = (wt / "outputs" / "model_output.txt").read_text()
    if current_output != first_output:
        print("ERROR: Idempotency failed (divergent artifacts)")
        return False
        
    print("Idempotency short-circuit OK (HEAD and artifacts unchanged).")

    # 5. Verify Filesystem
    print("Verifying filesystem...")
    wt = Path(wt_path)
    if not (wt / "outputs" / "model_output.txt").exists():
        print("ERROR: model_output.txt missing")
        return False
    if not (wt / "aar.json").exists():
        print("ERROR: aar.json missing")
        return False
    
    aar = json.loads((wt / "aar.json").read_text())
    if aar["status"] != "completed":
        print(f"ERROR: AAR status is {aar['status']}")
        return False
    print("Filesystem verification OK.")

    # 5. Verify Ledger
    print("Verifying Ledger events...")
    # Give ledger a moment to process if needed (rebuild is synchronous in our case but good practice)
    resp = requests.get(f"{LEDGER_URL}/events?order_id={ORDER_ID}")
    events = resp.json()
    types = [e["event_type"] for e in events]
    print(f"Found events: {types}")
    if types.count("ORDER_RUNNING") != 1:
        print(f"ERROR: Expected exactly 1 ORDER_RUNNING event, found {types.count('ORDER_RUNNING')}")
        return False
    if types.count("ORDER_COMPLETED") != 1:
        print(f"ERROR: Expected exactly 1 ORDER_COMPLETED event, found {types.count('ORDER_COMPLETED')}")
        return False
    
    resp = requests.get(f"{LEDGER_URL}/orders/{ORDER_ID}")
    if resp.status_code != 200:
        print("ERROR: Order not found in Ledger snapshot")
        return False
    order_snap = resp.json()
    if order_snap["status"] != "completed":
        print(f"ERROR: Ledger order status is {order_snap['status']}")
        return False
    print("Ledger verification OK.")

    # 6. Vault: Cleanup (Remove)
    print("Vault: Cleaning up worktree...")
    resp = requests.post(f"{VAULT_URL}/worktrees/{THEATER}/{ORDER_ID}/remove")
    resp.raise_for_status()
    print("Cleanup OK.")

    print("\nWORKER E2E SMOKE TEST SUCCESS")
    return True

if __name__ == "__main__":
    if not test_worker_e2e():
        sys.exit(1)
