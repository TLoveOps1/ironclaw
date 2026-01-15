import os
import asyncio
from fastapi import FastAPI
from typing import Dict, Any
from monitor import IronClawMonitor
from signals import ObserverSignals

app = FastAPI(title="IronClaw Observer Service")

# Configuration
CONFIG = {
    "theater": os.environ.get("IRONCLAW_THEATER", "demo"),
    "ledger_url": os.environ.get("IRONCLAW_LEDGER_URL", "http://127.0.0.1:8010"),
    "vault_url": os.environ.get("IRONCLAW_VAULT_URL", "http://127.0.0.1:8011"),
    "stall_seconds": int(os.environ.get("STALL_SECONDS", 1800)), # 30 mins
    "max_wall_seconds": int(os.environ.get("MAX_WALL_SECONDS", 3600)), # 1 hour
    "orphan_ttl_seconds": int(os.environ.get("ORPHAN_TTL_SECONDS", 3600)),
    "poll_interval_seconds": int(os.environ.get("POLL_INTERVAL_SECONDS", 30)),
    "enable_vault_cleanup": os.environ.get("ENABLE_VAULT_CLEANUP", "false").lower() == "true"
}

signals = ObserverSignals(ledger_url=CONFIG["ledger_url"], theater=CONFIG["theater"])
monitor = IronClawMonitor(config=CONFIG, signals=signals)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(polling_loop())

async def polling_loop():
    while True:
        try:
            monitor.poll()
        except Exception as e:
            print(f"Observer loop error: {e}")
        await asyncio.sleep(CONFIG["poll_interval_seconds"])

@app.get("/healthz")
async def healthz():
    return {
        "status": "ok",
        "theater": CONFIG["theater"],
        "poll_interval": CONFIG["poll_interval_seconds"]
    }

@app.get("/status")
async def status():
    return monitor.stats

@app.get("/alerts")
async def alerts():
    # Return deduped alerts (active in cache)
    return signals.dedupe_cache
