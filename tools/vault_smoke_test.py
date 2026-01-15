import requests
import sys
import os
import time
import subprocess

BASE_URL = "http://127.0.0.1:8001"
THEATER = "demo"
ORDER_ID = f"smoke_test_{int(time.time())}"

def test_vault():
    print(f"Starting Vault smoke test for order {ORDER_ID}...")

    # 1. Health check
    try:
        resp = requests.get(f"{BASE_URL}/health")
        resp.raise_for_status()
        print("Health check OK.")
    except Exception as e:
        print(f"ERROR: Service not running at {BASE_URL}: {e}")
        return False

    # 2. Create worktree
    print("Creating worktree...")
    resp = requests.post(f"{BASE_URL}/worktrees", json={
        "theater": THEATER,
        "order_id": ORDER_ID
    })
    if resp.status_code != 200:
        print(f"ERROR: Failed to create worktree: {resp.text}")
        return False
    data = resp.json()
    print(f"Worktree created at {data['path']}")
    wt_path = data['path']

    # 3. Idempotency check
    print("Checking idempotency...")
    resp = requests.post(f"{BASE_URL}/worktrees", json={
        "theater": THEATER,
        "order_id": ORDER_ID
    })
    data = resp.json()
    if data['created'] is not False:
        print("ERROR: Idempotency check failed (created should be false)")
        return False
    print("Idempotency OK.")

    # 4. Get status
    print("Checking status...")
    resp = requests.get(f"{BASE_URL}/worktrees/{THEATER}/{ORDER_ID}")
    data = resp.json()
    if not data['exists']:
        print("ERROR: Status check failed (should exist)")
        return False
    print("Status OK.")

    # 5. Archive
    print("Archiving...")
    resp = requests.post(f"{BASE_URL}/worktrees/{THEATER}/{ORDER_ID}/archive")
    if resp.status_code != 200:
        print(f"ERROR: Archiving failed: {resp.text}")
        return False
    data = resp.json()
    print(f"Archive created at {data['archive_path']}")
    
    # 6. Remove (archive-first)
    print("Removing worktree (archive-first)...")
    resp = requests.post(f"{BASE_URL}/worktrees/{THEATER}/{ORDER_ID}/remove")
    if resp.status_code != 200:
        print(f"ERROR: Removal failed: {resp.text}")
        return False
    data = resp.json()
    print(f"Worktree removed. Final archive at {data['archive_path']}")

    # 7. Path traversal attempt
    print("Testing path traversal rejection...")
    resp = requests.post(f"{BASE_URL}/worktrees", json={
        "theater": THEATER,
        "order_id": "../../../danger"
    })
    if resp.status_code == 400:
        print("Path traversal rejected OK.")
    else:
        print(f"ERROR: Path traversal NOT rejected (status {resp.status_code})")
        return False

    print("\nSMOKE TEST SUCCESS")
    return True

if __name__ == "__main__":
    if not test_vault():
        sys.exit(1)
