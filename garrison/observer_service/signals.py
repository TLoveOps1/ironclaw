import os
import json
import time
import requests
import hashlib
from pathlib import Path
from datetime import datetime, timezone

class ObserverSignals:
    def __init__(self, ledger_url: str, theater: str):
        self.ledger_url = ledger_url
        self.theater = theater
        self.audit_log = Path.home() / ".ironclaw" / "observer" / "alerts.jsonl"
        self.audit_log.parent.mkdir(parents=True, exist_ok=True)
        # In-memory dedupe: (type, run_id, order_id) -> ts
        self.dedupe_cache = {}
        self.dedupe_ttl = 3600 # 1 hour default

    def _get_utc_now(self):
        return datetime.now(timezone.utc).isoformat()

    def emit(self, alert_type: str, message: str, run_id: str = None, order_id: str = None, payload_extra: dict = None):
        cache_key = f"{alert_type}:{run_id}:{order_id}"
        now = time.time()
        
        # Dedupe check
        if cache_key in self.dedupe_cache:
            if now - self.dedupe_cache[cache_key] < self.dedupe_ttl:
                return False

        self.dedupe_cache[cache_key] = now
        
        event_type = f"observer.{alert_type}"
        payload = {
            "theater": self.theater,
            "alert_type": alert_type,
            "message": message,
            "run_id": run_id,
            "order_id": order_id,
            "observed_at": self._get_utc_now(),
            **(payload_extra or {})
        }
        
        # 1. Local Audit Stream
        with open(self.audit_log, "a") as f:
            f.write(json.dumps(payload) + "\n")
            
        # 2. Ledger Event
        event_id = f"obs-{alert_type}-{run_id or 'none'}-{order_id or 'none'}-{int(now)}"
        # Optionally use a more stable event_id if we want only ONE alert per episode ever in Ledger
        # But Phase F says "one escalation signal per stall episode", deterministic but unique to the episode.
        
        event = {
            "event_id": event_id,
            "run_id": run_id,
            "order_id": order_id,
            "event_type": event_type,
            "payload": payload
        }
        
        try:
            requests.post(f"{self.ledger_url}/events", json=event, timeout=5)
        except Exception as e:
            print(f"Observer failed to emit alert to Ledger: {e}")
            
        return True
