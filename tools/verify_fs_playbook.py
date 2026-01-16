import requests
import json
import time
import subprocess
import os
import signal
import tarfile
from pathlib import Path

# Configuration
CO_URL = "http://127.0.0.1:8013"
THEATER_ROOT = Path("/home/tyler/dev/ironclaw/theaters/demo").resolve()
WORKTREES_DIR = THEATER_ROOT / "worktrees"

stack_proc = None

def run_stack():
    global stack_proc
    print("Starting stack...")
    
    # Load env from theater
    env_file = THEATER_ROOT / ".env"
    env = os.environ.copy()
    if env_file.exists():
        print(f"Loading env from {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    env[key] = value

    stack_proc = subprocess.Popen(
        ["python3", "garrison/cli/ironclaw.py", "stack", "up", "--theater", "demo"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env
    )
    # Wait for CO to be healthy
    for i in range(30):
        if stack_proc.poll() is not None:
             raise Exception(f"Stack process died early with rc={stack_proc.returncode}")
             
        try:
            if requests.get(f"{CO_URL}/health", timeout=1).json()["status"] == "ok":
                print("Stack is healthy.")
                return
        except:
            pass
        time.sleep(1)
    raise Exception("Stack failed to start")

def stop_stack():
    print("Stopping stack...")
    subprocess.run(["python3", "garrison/cli/ironclaw.py", "stack", "down"], check=True)

def test_scenario(name, payload, expected_mission_type):
    print(f"\n--- Running Scenario: {name} ---")
    print(f"Expected mission_type: {expected_mission_type}")
    
    # Force new request
    payload["request_id"] = f"verify-{name}-{int(time.time())}"
    
    print(f"Sending request to {CO_URL}/chat...")
    resp = requests.post(f"{CO_URL}/chat", json=payload, timeout=60)
    print(f"Response status: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"Error response: {resp.text}")
        return

    data = resp.json()
    order_id = data["order_id"]
    print(f"Order ID: {order_id}")
    
    # Wait for completion (poll archive or check status)
    # The script currently just checks existing archive or active.
    # We need to wait for worker to finish to see the AAR.
    # Since verification involves 'stack up' which is async effectively, we wait a bit.
    
    time.sleep(5) 
    
    # Check archive
    archive_dir = THEATER_ROOT / "archive"
    # Find newest archive for this order
    possible_archives = list(archive_dir.glob(f"*{order_id}*.tar.gz"))
    if not possible_archives:
        print("[FAIL] Archive not found. Worker may have failed or timed out.")
        return

    archive_path = possible_archives[0]
    print(f"Found archive: {archive_path}")
    
    # Inspect AAR in archive
    with tarfile.open(archive_path, "r:gz") as tar:
        try:
            aar_file = tar.extractfile(f"{order_id}/aar.json")
            if aar_file:
                aar = json.load(aar_file)
                actual_mt = aar.get("mission_type")
                if actual_mt == expected_mission_type:
                    print(f"[PASS] AAR mission_type matches: {actual_mt}")
                else:
                    print(f"[FAIL] AAR mission_type mismatch. Expected '{expected_mission_type}', got '{actual_mt}'")
            else:
                print(f"[FAIL] aar.json not found in archive")
        except KeyError:
             print(f"[FAIL] order_id directory not found in archive or structure unexpected")

def test_filesystem_agent():
    # Scenario 1: Default
    payload_default = {
        "message": "Hello world",
        "model_overrides": {}
    }
    test_scenario("default", payload_default, "default")
    
    # Restart stack for clean slate
    stop_stack()
    time.sleep(2)
    run_stack()
    
    # Scenario 2: Filesystem
    payload_fs = {
        "message": "Jane from Acme called...",
        "model_overrides": {
            "mission_type": "filesystem_agent.call_summary",
            "account_name": "Acme Corp",
            "contact_name": "Jane Smith"
        }
    }
    test_scenario("filesystem", payload_fs, "filesystem_agent.call_summary")


if __name__ == "__main__":
    try:
        run_stack()
        test_filesystem_agent()
    finally:
        stop_stack()
