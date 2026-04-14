"""
Webhook Dispatcher — Fires Jira-compatible HTTP POST webhooks.
Handles both real-time dispatch and historical event replay.
Gracefully no-ops if Athena Core is not running (simulator continues independently).
"""
import os
import uuid
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ATHENA_WEBHOOK_URL = os.environ.get("ATHENA_WEBHOOK_URL", "http://localhost:8001/api/v1/webhook/event")

# Track webhook stats (visible in logs at end of simulation)
_webhook_stats = {"dispatched": 0, "dropped": 0}

def dispatch_webhook(event_type: str, entity_type: str, entity_id: str, new_state: dict):
    """
    Fires an HTTP webhook simulating Jira's outbound event structure.
    Used by the simulator API and Chaos Engine to notify Athena of state changes.
    """
    payload = {
        "event_id": f"evt_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "webhookEvent": entity_type,
        "issue": {
            "id": entity_id,
            "fields": new_state if isinstance(new_state, dict) else {}
        }
    }
    _send_payload(payload)

def replay_historical_event(event_type: str, entity_type: str, entity_id: str, historical_state: dict, historical_timestamp: datetime):
    """
    Fires a historical webhook used by the timeline generator so the downstream
    Neo4j / Pinecone GraphRAG ingestion pipelines can build their databases retroactively.
    """
    payload = {
        "event_id": f"evt_hist_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "timestamp": historical_timestamp.isoformat() + "Z",
        "webhookEvent": entity_type,
        "is_historical_replay": True,
        "issue": {
            "id": entity_id,
            "fields": historical_state if isinstance(historical_state, dict) else {}
        }
    }
    _send_payload(payload, silent=True)  # Silent during timeline sim (thousands of events)

def _send_payload(payload: dict, silent: bool = False):
    """
    Sends the webhook payload. Gracefully handles Athena Core being offline.
    silent=True suppresses per-event logging during bulk historical replay.
    """
    try:
        response = requests.post(
            ATHENA_WEBHOOK_URL, json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        _webhook_stats["dispatched"] += 1
        if not silent:
            print(f"[Webhook] Dispatched {payload['event_type']} -> {payload['issue']['id']}")
    except requests.exceptions.ConnectionError:
        # Expected if Athena Core is not running yet; simulator continues independently
        _webhook_stats["dropped"] += 1
    except requests.exceptions.Timeout:
        _webhook_stats["dropped"] += 1
    except Exception as e:
        _webhook_stats["dropped"] += 1
        if not silent:
            print(f"[Webhook] Error: {e}")

def get_webhook_stats() -> dict:
    return dict(_webhook_stats)