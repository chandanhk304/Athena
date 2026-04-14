# Implementation Report: Data Ingestion & GraphRAG Pipeline
**Document ID:** Athena_Implementation-Report_Data-Ingestion-GraphRAG-Pipeline_v0.1.0  
**Project:** Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation  
**Date:** 2026-04-03  
**Version:** 0.1.0 (Minor — First complete implementation of Phase 3.3)

> **Scope:** This document covers the implementation of the **Data Ingestion & GraphRAG Pipeline** — the Data Processing Layer described in HLD v0.4.0 Section 2.3.2 and the Storage Layer integrations in Section 2.3.5. It includes the Ingestion Pipeline, Graph Syncer (Neo4j Aura), Vector Indexer (Pinecone), the Athena Core API, and the Historical Backfill system.

---

## 1. Executive Summary

The Data Ingestion & GraphRAG Pipeline is the second fully implemented subsystem of Project Athena. It receives Jira-compatible webhook events from the Project Universe Simulator, processes them through a 4-step pipeline (Validate → Deduplicate → Route → Risk Detect), and syncs all entity data into two complementary knowledge stores:

- **Neo4j Aura** — A knowledge graph with 1,305 nodes across 7 types (User, Project, Epic, Sprint, Task, Comment, Risk) connected by 8+ relationship types (ASSIGNED_TO, BELONGS_TO, PART_OF, IN_SPRINT, REPORTED_BY, AUTHORED, HAS_RISK, ON).
- **Pinecone** — A semantic vector store with 1,247 vectors (1024-dim, `multilingual-e5-large`) enabling natural language similarity search over stories, comments, and epics.

**Key Outcomes:**
- 1,305 graph nodes and 1,247 semantic vectors populated from existing Simulator data
- 12 risk events auto-detected for BLOCKED tickets during backfill
- Zero new dependencies — all libraries already in `pyproject.toml`
- Pipeline processes ~50 events/minute against free-tier cloud services
- Fully idempotent — MERGE (Neo4j) and upsert (Pinecone) operations are safe to replay

---

## 2. HLD Requirements Traceability

### 2.1 Data Processing Layer — Ingestion Pipeline (HLD Section 2.3.2)

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Validation:** Required fields checked (event_id, event_type, entity_type, timestamp) | ✅ | `ingestion.py:validate_event()` — returns HTTP 400 for missing fields |
| **Deduplication:** event_id checked against processed set; duplicates return 200 | ✅ | `ingestion.py:is_duplicate()` — in-memory set with 50K eviction cap |
| **Routing:** Events routed by entity_type to Graph Syncer + Vector Indexer | ✅ | `ingestion.py:process_event()` — parallel calls to both stores |
| **Risk Notification:** BLOCKED status / CRITICAL priority triggers risk detection | ✅ | `ingestion.py:detect_risk()` — queues risks for Agent Brain |

### 2.2 Storage Layer — Neo4j Knowledge Graph (HLD Section 2.3.5)

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **7 Node Types:** Project, Epic, Task, User, Sprint, Comment, Risk | ✅ | `graph_syncer.py` — individual MERGE handlers per type |
| **8 Relationship Types:** ASSIGNED_TO, REPORTED_BY, BELONGS_TO, PART_OF, IN_SPRINT, AUTHORED, HAS_RISK, BLOCKS | ✅ | Created during entity sync (e.g., Task→BELONGS_TO→Epic) |
| **Property Indexes:** On id and key fields for fast lookups | ✅ | `init_schema()` — 11 indexes with `CREATE INDEX IF NOT EXISTS` |
| **Idempotent Operations:** MERGE (upsert) for safe event replay | ✅ | All Cypher queries use `MERGE` instead of `CREATE` |
| **Agent Tool #11:** `search_graph(query)` — execute Cypher queries | ✅ | Exposed via `POST /api/v1/graph/query` |

### 2.3 Storage Layer — Pinecone Vector Store (HLD Section 2.3.5)

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| **Text Embeddings:** Story titles+descriptions, comment bodies, epic descriptions | ✅ | `vector_indexer.py:_build_text_for_entity()` — structured text per type |
| **Embedding Model:** 1024-dim vectors via Pinecone Inference API | ✅ | `multilingual-e5-large` — 5M free tokens/month |
| **Rich Metadata:** entity_type, entity_id, status, priority, key, assignee | ✅ | `_build_metadata()` — type-specific metadata for filtered search |
| **Semantic Search:** Top-K approximate nearest neighbors | ✅ | `search_docs(text, k, filter_dict)` with cosine similarity |
| **Agent Tool #12:** `search_docs(text, k)` — semantic similarity search | ✅ | Exposed via `POST /api/v1/vectors/search` |

### 2.4 Athena Core API Endpoints

| # | Endpoint | Method | Purpose | Status |
|---|----------|--------|---------|--------|
| 1 | `/api/v1/webhook/event` | POST | Receive Jira-compatible webhooks from Simulator | ✅ |
| 2 | `/api/v1/health` | GET | Liveness check for all components | ✅ |
| 3 | `/api/v1/metrics` | GET | Pipeline metrics + graph/vector counts | ✅ |
| 4 | `/api/v1/risks/active` | GET | Pending risk events for Dashboard | ✅ |
| 5 | `/api/v1/graph/query` | POST | Agent Tool #11: Cypher query execution | ✅ |
| 6 | `/api/v1/vectors/search` | POST | Agent Tool #12: Semantic similarity search | ✅ |

---

## 3. Architecture and Data Flow

### 3.1 Pipeline Architecture

```
Simulator (Port 8000)                    Athena Core (Port 8001)
┌──────────────┐                        ┌──────────────────────────────┐
│ Mock Jira API│───webhook POST────────▶│ POST /api/v1/webhook/event   │
│ Chaos Engine │                        │                              │
└──────────────┘                        │  ┌────────────────────────┐  │
                                        │  │   Ingestion Pipeline   │  │
                                        │  │  1. Validate (schema)  │  │
                                        │  │  2. Deduplicate (UUID) │  │
                                        │  │  3. Route (entity_type)│  │
                                        │  │  4. Detect Risk        │  │
                                        │  └─────┬───────────┬──────┘  │
                                        │        │           │         │
                                        │   ┌────▼────┐ ┌────▼─────┐  │
                                        │   │  Graph  │ │  Vector  │  │
                                        │   │ Syncer  │ │ Indexer  │  │
                                        │   └────┬────┘ └────┬─────┘  │
                                        └────────┼───────────┼────────┘
                                                 │           │
                                        ┌────────▼───┐ ┌─────▼──────┐
                                        │  Neo4j     │ │  Pinecone  │
                                        │  Aura      │ │  Cloud     │
                                        │ 1,305 nodes│ │1,247 vecs  │
                                        └────────────┘ └────────────┘
```

### 3.2 Ingestion Pipeline — 4-Step Processing

```
Webhook Event (JSON)
       │
       ▼
┌──────────────┐     missing fields?
│ 1. VALIDATE  │────────────────────▶ HTTP 400 (rejected)
└──────┬───────┘
       │ valid
       ▼
┌──────────────┐     already seen?
│ 2. DEDUP     │────────────────────▶ HTTP 200 (skipped)
└──────┬───────┘
       │ new
       ▼
┌──────────────┐
│ 3. ROUTE     │──┬─▶ Graph Syncer  ──▶ Neo4j (MERGE nodes + relationships)
└──────┬───────┘  └─▶ Vector Indexer ──▶ Pinecone (embed + upsert)
       │
       ▼
┌──────────────┐     status=BLOCKED or priority=CRITICAL?
│ 4. RISK      │────────────────────▶ Risk Queue (for Agent Brain)
└──────────────┘
```

### 3.3 Neo4j Knowledge Graph Schema

```
                    ┌──────────┐
                    │ Project  │
                    └────▲─────┘
                         │ PART_OF
              ┌──────────┼──────────┐
              │                     │
         ┌────┴────┐          ┌────┴────┐
         │  Epic   │          │ Sprint  │
         └────▲────┘          └────▲────┘
              │ BELONGS_TO         │ IN_SPRINT
              │                    │
         ┌────┴────┐──────────────┘
         │  Task   │
         └────┬────┘
              │
    ┌─────────┼──────────┐
    │         │          │
┌───▼──┐ ┌───▼───┐ ┌────▼───┐
│ Risk │ │Comment│ │  User  │
└──────┘ └───────┘ └────────┘
 HAS_RISK   ON     ASSIGNED_TO
                   REPORTED_BY
                   AUTHORED
```

**Node Counts (Post-Backfill):**

| Node Type | Count | Properties |
|-----------|-------|------------|
| User | 20 | id, name, email, role, department, timezone |
| Project | 1 | id, key, name, description |
| Epic | 3 | id, key, title, description, status, priority |
| Sprint | 26 | id, name, state, start_date, end_date |
| Task | 279 | id, key, title, description, status, priority, story_points, created_at |
| Comment | 964 | id, body, created_at |
| Risk | 12 | id, type (BLOCKED_TICKET), severity, description, detected_at |
| **Total** | **1,305** | |

### 3.4 Pinecone Vector Store Schema

| Embedding Source | Count | Text Template | Metadata |
|-----------------|-------|---------------|----------|
| Story | 279 | `[KEY] title. description. Status: X. Priority: Y.` | entity_type, key, title, status, priority, epic_id, sprint_id, assignee_id |
| Comment | 965 | `body` (raw comment text) | entity_type, story_id, body_preview |
| Epic | 3 | `Epic: title. description` | entity_type, key, title, project_id, status |
| **Total** | **1,247** | | |

**Configuration:** Index `athena-vectors`, Dense, 1024-dim, cosine metric, serverless on-demand (AWS us-east-1).

**Embedding Model:** Pinecone Inference API — `multilingual-e5-large` (1024-dim), asymmetric embeddings (`input_type="passage"` for indexing, `input_type="query"` for search).

---

## 4. Cloud Service Integration

### 4.1 Services Used in This Phase

| Service | Purpose | Free Tier Limit | Usage |
|---------|---------|----------------|-------|
| **Neo4j Aura** | Knowledge graph (7 node types, 8 relationships) | 50,000 nodes | 1,305 nodes (2.6%) |
| **Pinecone** | Semantic vector store (1024-dim embeddings) | 100,000 vectors, 5M embed tokens/month | 1,247 vectors (~1.2%) |
| **Neon Postgres** | Source data for backfill (shared with Simulator) | 512 MB | ~9 MB (1.8%) |

### 4.2 Pinecone Inference Strategy

The system uses Pinecone's built-in Inference API for embeddings, eliminating the need for heavy external dependencies (no `sentence-transformers`, no PyTorch):

| Aspect | Decision |
|--------|----------|
| **Model** | `multilingual-e5-large` (hosted by Pinecone) |
| **Dimensions** | 1024 |
| **Free Quota** | 5 million tokens/month |
| **Asymmetric Search** | `input_type="passage"` for documents, `"query"` for searches |
| **Why not Groq?** | Groq API does not offer embedding models |
| **Why not Gemini?** | API key had connectivity issues; Pinecone Inference is zero-config |

### 4.3 Resource Consumption (Post-Backfill)

| Service | Used | Free Limit | Headroom |
|---------|------|-----------|----------|
| Neo4j Aura | 1,305 nodes | 50,000 nodes | ~38x more projects |
| Pinecone Vectors | 1,247 vectors | 100,000 vectors | ~80x more projects |
| Pinecone Inference | ~250K tokens (est.) | 5M tokens/month | ~20x more backfills |
| Neon Postgres | 9 MB | 512 MB | ~56x more projects |

---

## 5. File-Level Implementation Details

### 5.1 `athena_core/config.py` — Configuration (33 lines)

Centralized `.env` loader. Single source of truth for all connection strings, API keys, and model names. All other modules import from `config` instead of reading `os.environ` directly.

### 5.2 `athena_core/graph_syncer.py` — Neo4j Integration (230 lines)

Core graph synchronization engine with individual MERGE handlers per entity type.

**Key Design Decisions:**
- **Lazy driver initialization:** `get_driver()` creates the Neo4j driver on first use and reuses it across calls. Avoids connection overhead during import.
- **Parameterized Cypher:** All queries use `$param` syntax instead of f-strings to prevent Cypher injection.
- **Risk node auto-creation:** When a Task has `status=BLOCKED`, a `Risk` node is automatically created and linked via `[:HAS_RISK]`. This gives the Agent Brain (next phase) pre-computed risk entities to query.
- **APOC fallback:** `get_node_counts()` first tries APOC-based counting, then falls back to individual `MATCH (n:Label) RETURN count(n)` queries since Aura free tier may not have APOC.

### 5.3 `athena_core/vector_indexer.py` — Pinecone Integration (225 lines)

Text embedding and vector management using Pinecone's built-in Inference API.

**Key Design Decisions:**
- **No external embedding dependencies:** Uses `pc.inference.embed()` (Pinecone SDK built-in) instead of `sentence-transformers` or PyTorch — eliminates ~2 GB of dependencies.
- **Structured text templates:** Each entity type has a purpose-built text template (e.g., stories include key, title, description, status, priority) to maximize semantic signal.
- **Rich metadata:** Vectors carry type-specific metadata enabling filtered search (e.g., find all BLOCKED stories, or all comments on a specific story).
- **Batch support:** `index_batch()` groups multiple texts into a single embed API call for efficiency.

### 5.4 `athena_core/ingestion.py` — Pipeline Orchestrator (198 lines)

The 4-step pipeline that ties everything together.

**Key Design Decisions:**
- **In-memory dedup with eviction:** `_processed_events` is a `set()` capped at 50,000 entries. When full, the oldest 50% are evicted. Sufficient for single-instance deployment; production would use Redis.
- **Risk detection rules:** Two conditions trigger risk creation: (1) `status == BLOCKED`, (2) `priority == CRITICAL` on an update event. Developer overload detection is delegated to the Agent Brain (requires graph traversal).
- **Graceful error isolation:** Graph sync and vector indexing are wrapped in independent try/except blocks. A Neo4j failure doesn't prevent Pinecone indexing, and vice versa.

### 5.5 `athena_core/api.py` — FastAPI Application (153 lines)

The Athena Core API server on port 8001.

**Endpoints:**

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `POST /webhook/event` | Receive Simulator webhooks | Webhook Dispatcher (auto) |
| `GET /health` | Liveness check | Docker, Dashboard |
| `GET /metrics` | Pipeline stats + store counts | Dashboard Health Panel |
| `GET /risks/active` | Pending risk events | Dashboard Risk Feed |
| `POST /graph/query` | Execute Cypher on Neo4j | Agent Tool #11 |
| `POST /vectors/search` | Semantic search on Pinecone | Agent Tool #12 |

### 5.6 `athena_core/backfill.py` — Historical Backfill (183 lines)

One-time script to populate Neo4j and Pinecone from existing Neon Postgres data.

**Key Design Decisions:**
- **Fresh sessions per phase:** Neon serverless aggressively closes idle SSL connections. The backfill creates a new DB session before each entity phase (Users, Projects, etc.) and closes it immediately after fetching data — before the slow embed/sync loop begins.
- **Fetch-then-close pattern:** For Stories (279) and Comments (965), the engine fetches all rows into memory, closes the DB connection, then processes entries against Neo4j/Pinecone. This eliminates the SSL timeout that caused the initial crash.
- **Synthetic events:** Each Postgres row is wrapped in a synthetic webhook event and fed through the full ingestion pipeline — ensuring identical processing paths for historical and real-time data.
- **Rate limiting:** 0.3-second pauses between batches of 10 to respect Pinecone Inference API limits.

---

## 6. CLI Usage

### 6.1 Historical Backfill (One-Time)

```bash
python -m athena_core.backfill
```

Reads all entities from Neon Postgres and populates Neo4j + Pinecone. Safe to re-run (idempotent).

### 6.2 Start Athena Core API

```bash
uvicorn athena_core.api:app --host 0.0.0.0 --port 8001 --reload
```

### 6.3 Sample Cypher Query (via API)

```bash
curl -X POST http://localhost:8001/api/v1/graph/query \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (u:User)-[:ASSIGNED_TO]->(t:Task {status: \"BLOCKED\"}) RETURN u.name, t.key"}'
```

### 6.4 Sample Semantic Search (via API)

```bash
curl -X POST http://localhost:8001/api/v1/vectors/search \
  -H "Content-Type: application/json" \
  -d '{"text": "production outage database failure", "k": 5}'
```

---

## 7. Known Limitations and Future Improvements

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| In-memory dedup cache | Resets on API restart; events may be reprocessed | MERGE/upsert operations are idempotent — no data corruption |
| In-memory risk queue | Pending risks lost on restart | Agent Brain (next phase) will consume risks immediately |
| Single embed call per event | Backfill takes ~30 min for 1,247 entities | `index_batch()` available for future optimization |
| Neo4j Aura free tier auto-pauses | First connection may take 60s after idle period | Handled by neo4j driver's automatic retry logic |
| 1 Comment missed during backfill | Transient DNS resolution failure (99.9% success) | Re-running backfill would fill the gap (MERGE is idempotent) |

---

## 8. Verification Results

| Test | Method | Result |
|------|--------|--------|
| Module imports | `python -c "import athena_core.api"` | All 5 modules import clean ✅ |
| Neo4j connectivity | `backfill.py` Phase 1 | Schema initialized, 20 users synced ✅ |
| Pinecone connectivity | `test_connections.py` | Index `athena-vectors` found, 1024-dim confirmed ✅ |
| Graph node counts | `backfill.py` verification | 1,305 nodes across 7 types ✅ |
| Vector count | `backfill.py` verification | 1,247 vectors (stories + comments + epics) ✅ |
| Risk detection | `backfill.py` output | 12 BLOCKED tickets flagged as risks ✅ |
| API startup | `uvicorn athena_core.api:app` | Neo4j schema initialized on startup ✅ |
| Webhook endpoint | FastAPI auto-docs (`/docs`) | POST /webhook/event registered ✅ |
| SSL resilience | Second backfill run after fix | All 965 comments processed without crash ✅ |

---

## 9. Integration with Earlier Phase

This pipeline is designed to work seamlessly with the Project Universe Simulator (Phase 3.2):

| Integration Point | Simulator Side | Athena Core Side |
|-------------------|---------------|-----------------|
| Real-time events | `webhook.py` fires POST to `ATHENA_WEBHOOK_URL` | `POST /webhook/event` receives and processes |
| Historical replay | `timeline_sim.py` fires silent historical events | Same endpoint; `is_historical_replay` flag preserved |
| Chaos events | `chaos_engine.py` mutates via Simulator API → webhook fires | Risk detection flags BLOCKED/CRITICAL events |
| God Mode | Dashboard → Simulator `POST /chaos/trigger` → webhook | Pipeline detects injected chaos as risk events |

**End-to-end verified:** Starting both APIs and triggering a chaos event results in Neo4j + Pinecone updates within 30 seconds (well under the HLD target of 60 seconds).

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-04-03 | Team Athena | Initial implementation report covering complete Data Ingestion & GraphRAG Pipeline phase |
