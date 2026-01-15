#!/usr/bin/env python3
import argparse
import json
import os
import sys
import uuid
import hashlib
from pathlib import Path
import requests

DEFAULT_CO_URL = os.environ.get("IRONCLAW_CO_URL", "http://127.0.0.1:8013")
STATE_DIR = Path.home() / ".ironclaw" / "client"
LAST_REQUEST_FILE = STATE_DIR / "last_request.json"
HISTORY_FILE = STATE_DIR / "history.jsonl"

def ensure_state_dir():
    STATE_DIR.mkdir(parents=True, exist_ok=True)

def save_last_request(payload: dict, co_url: str):
    ensure_state_dir()
    data = {
        "payload": payload,
        "co_url": co_url,
        "timestamp": os.environ.get("CURRENT_TIME_TS") or str(uuid.uuid4()) # Better than nothing
    }
    tmp_file = LAST_REQUEST_FILE.with_suffix(".tmp")
    with open(tmp_file, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_file, LAST_REQUEST_FILE)

def load_last_request():
    if not LAST_REQUEST_FILE.exists():
        return None
    try:
        return json.loads(LAST_REQUEST_FILE.read_text())
    except:
        return None

def append_history(request_id, message, status):
    ensure_state_dir()
    entry = {
        "ts": os.environ.get("CURRENT_TIME_TS") or str(uuid.uuid4()),
        "request_id": request_id,
        "msg_hash": hashlib.sha256(message.encode()).hexdigest()[:8],
        "status": status
    }
    with open(HISTORY_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

def print_human(data, request_id=None):
    print("=" * 40)
    print(f"REQUEST ID: {request_id or data.get('request_id')}")
    print(f"STATUS    : {data.get('status')}")
    if data.get("run_id"):
        print(f"RUN ID    : {data.get('run_id')}")
    if data.get("order_id"):
        print(f"ORDER ID  : {data.get('order_id')}")
    if data.get("archive_path"):
        print(f"ARCHIVE   : {data.get('archive_path')}")
    
    if data.get("answer"):
        print("-" * 40)
        print("REPLY:")
        print(data.get("answer"))
    elif data.get("error"):
        print("-" * 40)
        print("ERROR:")
        print(data.get("error"))
    print("=" * 40)

def main():
    parser = argparse.ArgumentParser(description="IronClaw CLI client")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    chat_p = subparsers.add_parser("chat", help="Send a message to the CO")
    chat_p.add_argument("message", nargs="?", help="Message text")
    chat_p.add_argument("--co-url", default=DEFAULT_CO_URL, help="CO service URL")
    chat_p.add_argument("--theater", help="Theater hint")
    chat_p.add_argument("--request-id", help="Explicit request ID")
    chat_p.add_argument("--retry", action="store_true", help="Retry the last request")
    chat_p.add_argument("--new", action="store_true", help="Force new request ID")
    chat_p.add_argument("--json", action="store_true", help="Print raw JSON output")
    chat_p.add_argument("--timeout", type=int, default=900, help="HTTP timeout in seconds")
    
    args = parser.parse_args()
    
    if args.command == "chat":
        co_url = args.co_url.rstrip("/")
        
        if args.retry:
            last = load_last_request()
            if not last:
                print("Error: No last request found to retry.", file=sys.stderr)
                sys.exit(1)
            payload = last["payload"]
            # Override co_url if explicitly provided in args, otherwise use last
            if args.co_url != DEFAULT_CO_URL:
                co_url = args.co_url.rstrip("/")
            else:
                co_url = last["co_url"].rstrip("/")
        else:
            if not args.message:
                print("Error: Message text is required unless using --retry.", file=sys.stderr)
                sys.exit(1)
            
            request_id = args.request_id
            if args.new or not request_id:
                request_id = str(uuid.uuid4())
            
            payload = {
                "message": args.message,
                "request_id": request_id,
            }
            if args.theater:
                payload["theater"] = args.theater
        
        # Atomically persist intent before calling
        save_last_request(payload, co_url)
        
        try:
            resp = requests.post(f"{co_url}/chat", json=payload, timeout=args.timeout)
            resp.raise_for_status()
            data = resp.json()
            
            # Update history
            append_history(payload["request_id"], payload.get("message", "retry"), data.get("status", "unknown"))
            
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                print_human(data, request_id=payload.get("request_id"))
                
        except requests.exceptions.RequestException as e:
            if args.json:
                print(json.dumps({"error": str(e), "status": "network_error"}, indent=2))
            else:
                print(f"Network Error: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
