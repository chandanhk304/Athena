"""
Ingestion Pipeline — Validates, deduplicates, and routes webhook events.
Coordinates Graph Syncer (Neo4j) and Vector Indexer (Pinecone).
Detects risk events for the Agent Brain.

HLD v0.4.0 Section 2.3.2: Data Processing Layer
"""
import time
from datetime import datetime, timezone

from . import graph_syncer
from . import vector_indexer

# ─── Deduplication ──────────────────────────────────────────
# In-memory set of processed event_ids (sufficient for single-instance deployment)
# Production: use Redis or a Postgres table for distributed dedup
_processed_events: set[str] = set()
_MAX_DEDUP_CACHE = 50_000  # Prevent unbounded memory growth

# ─── Risk Detection Queue ───────────────────────────────────
# In-memory queue for risk events (consumed by Agent Brain in next phase)
_risk_queue: list[dict] = []

# ─── Metrics ────────────────────────────────────────────────
_metrics = {
    "events_received": 0,
    "events_processed": 0,
    "events_deduplicated": 0,
    "events_invalid": 0,
    "graph_synced": 0,
    "vectors_indexed": 0,
    "risks_detected": 0,
}

# Required fields per HLD v0.4.0
REQUIRED_FIELDS = {"event_id", "event_type", "webhookEvent", "timestamp"}
RISK_STATUSES = {"BLOCKED"}
RISK_PRIORITIES = {"CRITICAL"}


def validate_event(event: dict) -> tuple[bool, str]:
    """
    Step 1: Validate incoming webhook event against required schema.
    Returns (is_valid, error_message).
    """
    missing = REQUIRED_FIELDS - set(event.keys())
    if missing:
        return False, f"Missing required fields: {missing}"

    if "issue" not in event or not isinstance(event["issue"], dict):
        return False, "Missing 'issue' object"

    if "id" not in event["issue"]:
        return False, "Missing 'issue.id'"

    return True, ""


def is_duplicate(event_id: str) -> bool:
    """
    Step 2: Check if event was already processed (idempotent dedup).
    """
    if event_id in _processed_events:
        return True

    # Evict oldest entries if cache is too large
    if len(_processed_events) >= _MAX_DEDUP_CACHE:
        # Simple eviction: clear half the cache
        # Production: use LRU cache or Redis TTL
        to_remove = list(_processed_events)[:_MAX_DEDUP_CACHE // 2]
        for item in to_remove:
            _processed_events.discard(item)

    _processed_events.add(event_id)
    return False


def detect_risk(event: dict) -> dict | None:
    """
    Step 4: Check if this event represents a risk.
    Risk conditions (from HLD):
    - Status change to BLOCKED
    - Priority escalation to CRITICAL
    - Developer overload (detected by Agent Brain via graph queries)
    """
    fields = event.get("issue", {}).get("fields", {})
    event_type = event.get("event_type", "")

    risk = None

    # Check for BLOCKED status
    if fields.get("status") in RISK_STATUSES:
        risk = {
            "risk_type": "BLOCKED_TICKET",
            "severity": fields.get("priority", "HIGH"),
            "entity_id": event["issue"]["id"],
            "entity_key": fields.get("key", "UNKNOWN"),
            "description": f"Ticket {fields.get('key', 'UNKNOWN')} is BLOCKED",
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "source_event": event["event_id"]
        }

    # Check for CRITICAL priority (especially if escalated)
    elif fields.get("priority") in RISK_PRIORITIES and "updated" in event_type:
        risk = {
            "risk_type": "PRIORITY_ESCALATION",
            "severity": "CRITICAL",
            "entity_id": event["issue"]["id"],
            "entity_key": fields.get("key", "UNKNOWN"),
            "description": f"Ticket {fields.get('key', 'UNKNOWN')} escalated to CRITICAL",
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "source_event": event["event_id"]
        }

    return risk


# ═══════════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════

def process_event(event: dict) -> dict:
    """
    Main ingestion pipeline: Validate → Deduplicate → Route → Detect Risk.
    Returns a result dict with status and details.
    """
    _metrics["events_received"] += 1

    # Step 1: Validate
    is_valid, error = validate_event(event)
    if not is_valid:
        _metrics["events_invalid"] += 1
        return {"status": "rejected", "reason": error, "code": 400}

    event_id = event["event_id"]

    # Step 2: Deduplicate
    if is_duplicate(event_id):
        _metrics["events_deduplicated"] += 1
        return {"status": "duplicate", "event_id": event_id, "code": 200}

    # Step 3: Route to Graph Syncer + Vector Indexer
    graph_ok = False
    vector_ok = False

    try:
        graph_ok = graph_syncer.sync_event(event)
        if graph_ok:
            _metrics["graph_synced"] += 1
    except Exception as e:
        print(f"[Ingestion] Graph sync error: {e}")

    try:
        vector_ok = vector_indexer.index_event(event)
        if vector_ok:
            _metrics["vectors_indexed"] += 1
    except Exception as e:
        print(f"[Ingestion] Vector index error: {e}")

    # Step 4: Detect Risk
    risk = detect_risk(event)
    if risk:
        _risk_queue.append(risk)
        _metrics["risks_detected"] += 1
        print(f"[Ingestion] ⚠️  RISK DETECTED: {risk['risk_type']} — {risk['description']}")

    _metrics["events_processed"] += 1

    return {
        "status": "processed",
        "event_id": event_id,
        "graph_synced": graph_ok,
        "vector_indexed": vector_ok,
        "risk_detected": risk is not None,
        "code": 200
    }


# ═══════════════════════════════════════════════════════════════
#  ACCESSORS
# ═══════════════════════════════════════════════════════════════

def get_metrics() -> dict:
    """Return pipeline processing metrics."""
    return dict(_metrics)


def get_pending_risks() -> list[dict]:
    """Return and clear the risk queue (consumed by Agent Brain)."""
    risks = list(_risk_queue)
    _risk_queue.clear()
    return risks


def peek_risks() -> list[dict]:
    """Return risks without clearing (for dashboard display)."""
    return list(_risk_queue)
