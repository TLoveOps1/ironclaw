#!/usr/bin/env python3
import argparse
import json
import os
import sys
import uuid
import hashlib
import time
import signal
import subprocess
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests

# Standards
BASE_DIR = Path(__file__).parent.parent.parent.resolve()
DEFAULT_CO_URL = os.environ.get("IRONCLAW_CO_URL", "http://127.0.0.1:8013")
CLIENT_STATE_DIR = Path.home() / ".ironclaw" / "client"
STACK_STATE_DIR = Path.home() / ".ironclaw" / "stack"
STACK_LOGS_DIR = STACK_STATE_DIR / "logs"
STACK_STATE_FILE = STACK_STATE_DIR / "stack_state.json"

# Persistence Helpers
def ensure_dirs():
    CLIENT_STATE_DIR.mkdir(parents=True, exist_ok=True)
    STACK_LOGS_DIR.mkdir(parents=True, exist_ok=True)

def save_last_request(payload: dict, co_url: str):
    ensure_dirs()
    data = {
        "payload": payload,
        "co_url": co_url,
        "timestamp": str(time.time())
    }
    tmp_file = (CLIENT_STATE_DIR / "last_request.json").with_suffix(".tmp")
    with open(tmp_file, "w") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp_file, CLIENT_STATE_DIR / "last_request.json")

def load_last_request():
    p = CLIENT_STATE_DIR / "last_request.json"
    if not p.exists(): return None
    try: return json.loads(p.read_text())
    except: return None

# Status Display
def print_human(data, request_id=None):
    print("=" * 40)
    print(f"REQUEST ID: {request_id or data.get('request_id')}")
    print(f"STATUS    : {data.get('status')}")
    if data.get("run_id"): print(f"RUN ID    : {data.get('run_id')}")
    if data.get("order_id"): print(f"ORDER ID  : {data.get('order_id')}")
    if data.get("archive_path"): print(f"ARCHIVE   : {data.get('archive_path')}")
    if data.get("answer"):
        print("-" * 40)
        print("REPLY:")
        print(data.get("answer"))
    elif data.get("error"):
        print("-" * 40)
        print("ERROR:")
        print(data.get("error"))
    print("=" * 40)

# Stack Management
class StackManager:
    SERVICES = {
        "ledger": {"port": 8010, "path": "garrison/ledger_service", "health_endpoint": "/health"},
        "vault": {"port": 8011, "path": "garrison/vault_service", "health_endpoint": "/health"},
        "worker": {"port": 8012, "path": "garrison/worker_service", "health_endpoint": "/health"},
        "co": {"port": 8013, "path": "garrison/co_service", "health_endpoint": "/health"},
        "observer": {"port": 8014, "path": "garrison/observer_service", "health_endpoint": "/healthz"}
    }

    def __init__(self, theater: str = "demo"):
        self.theater = theater
        self.state = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        if STACK_STATE_FILE.exists():
            try: return json.loads(STACK_STATE_FILE.read_text())
            except: pass
        return {"pids": {}, "ports": {}, "theater": self.theater, "active": False}

    def _save_state(self):
        ensure_dirs()
        with open(STACK_STATE_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

    def up(self, detach: bool = False):
        if self.state.get("active"):
            print("Stack is already marked as active. Use 'status' to check or 'down' to reset.")
            return

        print(f"Launching IronClaw Stack for theater '{self.theater}'...")
        self.state["active"] = True
        self.state["theater"] = self.theater

        for name, info in self.SERVICES.items():
            port = info["port"]
            path = BASE_DIR / info["path"]
            
            # Check port
            if self._is_port_in_use(port):
                print(f"Error: Port {port} is already in use. Cannot start {name}.")
                self.down()
                sys.exit(1)

            print(f"Starting {name} on port {port}...")
            log_file = STACK_LOGS_DIR / f"{name}.log"
            
            env = os.environ.copy()
            env["IRONCLAW_THEATER"] = self.theater
            env["LEDGER_URL"] = f"http://127.0.0.1:8010"
            env["VAULT_URL"] = f"http://127.0.0.1:8011"
            env["WORKER_URL"] = f"http://127.0.0.1:8012"
            env["CO_URL"] = f"http://127.0.0.1:8013"
            
            # Use theater venv if it exists
            venv_python = BASE_DIR / "theaters" / self.theater / ".venv" / "bin" / "python"
            executable = str(venv_python) if venv_python.exists() else sys.executable
            
            cmd = [executable, "-m", "uvicorn", "main:app", "--port", str(port), "--host", "127.0.0.1"]
            
            proc = subprocess.Popen(
                cmd,
                cwd=str(path),
                stdout=open(log_file, "w"),
                stderr=subprocess.STDOUT,
                env=env,
                preexec_fn=os.setsid
            )
            
            self.state["pids"][name] = proc.pid
            self.state["ports"][name] = port
            self._save_state()

            # Wait for health
            if not self._wait_for_health(name, port, info["health_endpoint"]):
                print(f"Error: {name} failed to become healthy. Check logs at {log_file}")
                self.down()
                sys.exit(1)

        print("Stack is UP and healthy.")

    def down(self):
        print("Stopping IronClaw Stack...")
        for name, pid in self.state["pids"].items():
            if self._is_pid_alive(pid):
                print(f"Stopping {name} (PID {pid})...")
                try: os.killpg(os.getpgid(pid), signal.SIGTERM)
                except: pass
        
        # Grace period
        time.sleep(2)
        
        for name, pid in self.state["pids"].items():
            if self._is_pid_alive(pid):
                print(f"Force killing {name} (PID {pid})...")
                try: os.killpg(os.getpgid(pid), signal.SIGKILL)
                except: pass

        self.state["active"] = False
        self.state["pids"] = {}
        self._save_state()
        print("Stack is DOWN.")

    def status(self):
        print(f"IronClaw Stack Status (Theater: {self.state.get('theater')})")
        print("-" * 40)
        any_alive = False
        for name, info in self.SERVICES.items():
            pid = self.state["pids"].get(name)
            port = self.state["ports"].get(name, info["port"])
            alive = self._is_pid_alive(pid) if pid else False
            
            status_str = "ALIVE" if alive else "DEAD"
            health_str = "N/A"
            if alive:
                any_alive = True
                try:
                    r = requests.get(f"http://127.0.0.1:{port}{info['health_endpoint']}", timeout=1)
                    health_str = "HEALTHY" if r.status_code == 200 else f"UNHEALTHY ({r.status_code})"
                except:
                    health_str = "UNREACHABLE"
            
            print(f"{name:10} | {status_str:6} | PID: {str(pid):6} | Port: {port} | {health_str}")
        
        if not any_alive and self.state.get("active"):
            print("-" * 40)
            print("Note: Stack is marked active in state but no processes are alive.")

    def logs(self, service: str = "all", tail: int = 20, follow: bool = False):
        log_files = []
        if service == "all":
            log_files = [(name, STACK_LOGS_DIR / f"{name}.log") for name in self.SERVICES.keys()]
        elif service in self.SERVICES:
            log_files = [(service, STACK_LOGS_DIR / f"{service}.log")]
        else:
            print(f"Error: Unknown service '{service}'")
            return

        if follow:
            self._tail_follow(log_files)
        else:
            for name, path in log_files:
                if path.exists():
                    print(f"--- {name} logs ---")
                    lines = path.read_text().splitlines()[-tail:]
                    for line in lines:
                        print(f"[{name.upper()}] {line}")

    def _wait_for_health(self, name: str, port: int, endpoint: str, timeout: int = 20) -> bool:
        start = time.time()
        while time.time() - start < timeout:
            try:
                r = requests.get(f"http://127.0.0.1:{port}{endpoint}", timeout=1)
                if r.status_code == 200: return True
            except: pass
            time.sleep(1)
        return False

    def _is_pid_alive(self, pid: Optional[int]) -> bool:
        if not pid: return False
        try:
            os.kill(pid, 0)
            return True
        except: return False

    def _is_port_in_use(self, port: int) -> bool:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('127.0.0.1', port)) == 0

    def _tail_follow(self, log_files):
        print(f"Tailing logs for {', '.join(n for n, p in log_files)}... (Ctrl+C to stop)")
        files = {name: open(path, "r") for name, path in log_files if path.exists()}
        for f in files.values(): f.seek(0, 2)
        
        try:
            while True:
                for name, f in files.items():
                    line = f.readline()
                    if line: print(f"[{name.upper()}] {line.strip()}")
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass

# CLI Main
def main():
    parser = argparse.ArgumentParser(description="IronClaw CLI client")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # chat command
    chat_p = subparsers.add_parser("chat", help="Send a message to the CO")
    chat_p.add_argument("message", nargs="?", help="Message text")
    chat_p.add_argument("--co-url", default=DEFAULT_CO_URL, help="CO service URL")
    chat_p.add_argument("--theater", help="Theater hint")
    chat_p.add_argument("--request-id", help="Explicit request ID")
    chat_p.add_argument("--retry", action="store_true", help="Retry the last request")
    chat_p.add_argument("--profile", help="Model profile name")
    chat_p.add_argument("--overrides", help="JSON string of model overrides")
    chat_p.add_argument("--template", help="Prompt template path")
    chat_p.add_argument("--new", action="store_true", help="Force new request ID")
    chat_p.add_argument("--json", action="store_true", help="Print raw JSON output")
    chat_p.add_argument("--timeout", type=int, default=900, help="HTTP timeout in seconds")
    
    # stack command
    stack_p = subparsers.add_parser("stack", help="Manage the IronClaw stack")
    stack_sub = stack_p.add_subparsers(dest="stack_command", help="Stack commands")
    
    up_p = stack_sub.add_parser("up", help="Start the full stack")
    up_p.add_argument("--theater", default="demo", help="Theater ID (default: demo)")
    
    stack_sub.add_parser("down", help="Stop the stack")
    stack_sub.add_parser("status", help="Check stack status")
    
    logs_p = stack_sub.add_parser("logs", help="View stack logs")
    logs_p.add_argument("service", nargs="?", default="all", help="Service name or 'all'")
    logs_p.add_argument("-f", "--follow", action="store_true", help="Follow logs")
    logs_p.add_argument("--tail", type=int, default=20, help="Number of lines to tail")

    args = parser.parse_args()
    
    if args.command == "chat":
        co_url = args.co_url.rstrip("/")
        if args.retry:
            last = load_last_request()
            if not last:
                print("Error: No last request found to retry.", file=sys.stderr)
                sys.exit(1)
            payload = last["payload"]
            co_url = args.co_url if args.co_url != DEFAULT_CO_URL else last["co_url"]
        else:
            if not args.message:
                print("Error: Message text is required unless using --retry.", file=sys.stderr)
                sys.exit(1)
            request_id = args.request_id or str(uuid.uuid4())
            if args.new: request_id = str(uuid.uuid4())
            payload = {"message": args.message, "request_id": request_id}
            if args.theater: payload["theater"] = args.theater
            if args.profile: payload["model_profile"] = args.profile
            if args.template: payload["prompt_template"] = args.template
            if args.overrides:
                try: payload["model_overrides"] = json.loads(args.overrides)
                except: print(f"Warning: Failed to parse overrides as JSON: {args.overrides}")

        save_last_request(payload, co_url)
        try:
            resp = requests.post(f"{co_url}/chat", json=payload, timeout=args.timeout)
            resp.raise_for_status()
            data = resp.json()
            if args.json: print(json.dumps(data, indent=2))
            else: print_human(data, request_id=payload.get("request_id"))
        except Exception as e:
            if args.json: print(json.dumps({"error": str(e)}, indent=2))
            else: print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)

    elif args.command == "stack":
        mgr = StackManager(theater=getattr(args, "theater", "demo"))
        if args.stack_command == "up": mgr.up()
        elif args.stack_command == "down": mgr.down()
        elif args.stack_command == "status": mgr.status()
        elif args.stack_command == "logs": mgr.logs(service=args.service, tail=args.tail, follow=args.follow)
        else: stack_p.print_help()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
