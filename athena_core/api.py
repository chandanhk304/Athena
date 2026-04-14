"""
Athena Core — FastAPI Application
Receives Jira-compatible webhooks from the Project Universe Simulator,
processes them through the Ingestion Pipeline, and exposes metrics.
Also hosts the Agent Brain query, ATL, and approval endpoints.

HLD v0.4.0 Section 2.3.2: Data Processing Layer
Port: 8001
"""
import uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from . import config
from .ingestion import process_event, get_metrics, peek_risks, get_pending_risks
from .graph_syncer import init_schema, get_node_counts, search_graph
from .vector_indexer import get_vector_count, search_docs

app = FastAPI(
    title="Athena Core — Ingestion & Agent Brain API",
    version="0.2.0"
)

# Allow requests from the Next.js frontend (localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── In-memory ATL store (shared across requests) ────────────
# In production this would live in SQLite or Postgres.
_atl_store: list[dict] = []
_pending_approvals: dict[str, dict] = {}  # atl_id → pending_action


@app.on_event("startup")
async def startup():
    """Initialize Neo4j schema indexes on startup."""
    try:
        init_schema()
        print("[Athena Core] Neo4j schema initialized.")
    except Exception as e:
        print(f"[Athena Core] Neo4j schema init failed (will retry on first event): {e}")


# ═══════════════════════════════════════════════════════════════
#  WEBHOOK INGESTION ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/webhook/event")
async def receive_webhook(request: Request):
    """
    Main webhook ingestion endpoint.
    Receives Jira-compatible JSON events from the Simulator's Webhook Dispatcher.
    Processes through: Validate → Deduplicate → Graph Sync → Vector Index → Risk Detect.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    result = process_event(payload)

    if result["code"] == 400:
        raise HTTPException(status_code=400, detail=result["reason"])

    return JSONResponse(
        status_code=result["code"],
        content={
            "status": result["status"],
            "event_id": result.get("event_id"),
            "graph_synced": result.get("graph_synced", False),
            "vector_indexed": result.get("vector_indexed", False),
            "risk_detected": result.get("risk_detected", False),
        }
    )


# ═══════════════════════════════════════════════════════════════
#  HEALTH & METRICS
# ═══════════════════════════════════════════════════════════════

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "healthy",
        "service": "athena-core",
        "version": "HLD-v0.4.0",
        "components": {
            "neo4j": "connected",
            "pinecone": "connected",
            "ingestion_pipeline": "active"
        }
    }


@app.get("/api/v1/metrics")
def get_system_metrics():
    """Return pipeline metrics, graph counts, and vector counts."""
    pipeline = get_metrics()

    # Get graph and vector counts (may be slow; cached in production)
    try:
        graph_counts = get_node_counts()
    except Exception as e:
        graph_counts = {"error": str(e)}

    try:
        vector_count = get_vector_count()
    except Exception as e:
        vector_count = {"error": str(e)}

    return {
        "pipeline": pipeline,
        "neo4j_nodes": graph_counts,
        "pinecone_vectors": vector_count,
    }


# ═══════════════════════════════════════════════════════════════
#  RISK FEED (for Dashboard in future phase)
# ═══════════════════════════════════════════════════════════════

@app.get("/api/v1/risks/active")
def get_active_risks():
    """Return pending risk events detected by the ingestion pipeline."""
    risks = peek_risks()
    return {"total": len(risks), "risks": risks}


# ═══════════════════════════════════════════════════════════════
#  KNOWLEDGE QUERY ENDPOINTS (Agent Tools #11, #12)
# ═══════════════════════════════════════════════════════════════

@app.post("/api/v1/graph/query")
async def query_graph(request: Request):
    """Agent Tool #11: Execute a Cypher query on the knowledge graph."""
    body = await request.json()
    cypher = body.get("query", "")
    params = body.get("params", {})
    if not cypher:
        raise HTTPException(status_code=400, detail="Missing 'query' field")

    try:
        results = search_graph(cypher, params)
        return {"total": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cypher query failed: {e}")


@app.post("/api/v1/vectors/search")
async def query_vectors(request: Request):
    """Agent Tool #12: Semantic similarity search on Pinecone."""
    body = await request.json()
    text = body.get("text", "")
    k = body.get("k", 5)
    filters = body.get("filter", None)
    if not text:
        raise HTTPException(status_code=400, detail="Missing 'text' field")

    try:
        results = search_docs(text, k=k, filter_dict=filters)
        return {"total": len(results), "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {e}")


# ═══════════════════════════════════════════════════════════════
#  AGENT BRAIN ENDPOINTS (Phase 4)
# ═══════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    query: str
    thread_id: Optional[str] = None


class ApprovalRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"


@app.post("/api/v1/query")
async def agent_query(req: QueryRequest):
    """
    Agent Brain Chat Interface.
    Accepts a natural language query, routes it through the LangGraph
    multi-agent pipeline, and returns a markdown-formatted response.
    """
    from agent_brain.graph import get_graph

    thread_id = req.thread_id or str(uuid.uuid4())
    graph = get_graph()

    config_dict = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "messages": [HumanMessage(content=req.query)],
        "input_type": "",
        "context": "",
        "pending_action": None,
        "atl_entries": [],
        "final_response": "",
        "thread_id": thread_id,
    }

    try:
        result = graph.invoke(initial_state, config=config_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {e}")

    # Persist ATL entries to in-memory store
    new_entries = result.get("atl_entries", [])
    _atl_store.extend(new_entries)

    # Check if the Human Gate has paused with a pending action
    pending = result.get("pending_action")
    if pending:
        atl_id = pending.get("atl_id", str(uuid.uuid4()))
        _pending_approvals[atl_id] = {
            "thread_id": thread_id,
            "pending_action": pending
        }
        return {
            "thread_id": thread_id,
            "status": "PENDING_APPROVAL",
            "atl_id": atl_id,
            "response": result.get("final_response", ""),
            "pending_action": pending,
        }

    return {
        "thread_id": thread_id,
        "status": "COMPLETE",
        "response": result.get("final_response", ""),
        "atl_entries": new_entries,
        "input_type": result.get("input_type", ""),
    }


@app.get("/api/v1/atl")
async def get_atl():
    """
    ATL Viewer — Returns the full chronological Action Tracking Log.
    Used by the frontend ATL dashboard panel.
    """
    return {
        "total": len(_atl_store),
        "entries": list(reversed(_atl_store))  # Most recent first
    }


@app.post("/api/v1/approval/{atl_id}")
async def human_approval(atl_id: str, req: ApprovalRequest):
    """
    Human Gate Approval Endpoint.
    APPROVE → resumes LangGraph from the paused Human Gate → Executor runs the write action.
    REJECT  → resumes LangGraph → LogOnly node records the rejection.
    """
    from agent_brain.graph import get_graph

    if atl_id not in _pending_approvals:
        raise HTTPException(status_code=404, detail=f"No pending action found for ATL ID: {atl_id}")

    pending_data = _pending_approvals[atl_id]
    thread_id = pending_data["thread_id"]
    action = req.action.upper()

    if action not in {"APPROVE", "REJECT"}:
        raise HTTPException(status_code=400, detail="action must be 'APPROVE' or 'REJECT'")

    graph = get_graph()
    config_dict = {"configurable": {"thread_id": thread_id}}

    # Update the pending action status before resuming
    state_update = {
        "pending_action": pending_data["pending_action"] if action == "APPROVE" else None,
    }

    try:
        if action == "APPROVE":
            # Resume graph — it will proceed to the Executor node
            result = graph.invoke(state_update, config=config_dict)
            status_msg = "Action approved and executed."
        else:
            # Resume graph — it will route to LogOnly
            state_update["pending_action"] = None
            result = graph.invoke(state_update, config=config_dict)
            status_msg = "Action rejected. Logged to ATL."

        # Persist any new ATL entries
        new_entries = result.get("atl_entries", [])
        _atl_store.extend(new_entries)

        # Remove from pending
        del _pending_approvals[atl_id]

        return {
            "atl_id": atl_id,
            "action": action,
            "status": status_msg,
            "new_atl_entries": new_entries,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval processing error: {e}")
