# System Architecture and Design Specification
**Document ID:** Athena_HLD_System-Architecture_v0.2.0  
**Project:** Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation  
**Date:** 2026-02-19  
**Version:** 0.2.0 (Minor - Comprehensive Architecture with Detailed Design)

---

## 1. Introduction

### 1.1 Purpose
This document provides a comprehensive system architecture and design specification for Project Athena. It describes the high-level architecture, component specifications, inter-component communication, data flows, API contracts, agent workflow design, deployment topology, and security model.

### 1.2 Design Philosophy
The system follows a **Dual-Architecture** approach with strict separation of concerns:

1. **Project Universe** — A high-fidelity enterprise simulator (the data source)
2. **Athena Core** — The multi-agent reasoning engine (the intelligence)

These two systems communicate exclusively via HTTP webhooks and REST APIs, mirroring how a real AI agent would integrate with enterprise tools. This separation ensures that Athena Core's architecture is production-portable — it could connect to real Jira APIs without code changes to its core logic.

### 1.3 Architecture Principles

| Principle | Description | Implementation |
|-----------|-------------|---------------|
| Air-Gapped Capable | Supports fully offline deployment via Ollama | All services CAN run locally via Docker Compose |
| Dual-Mode LLM | Pluggable LLM backend for dev (cloud) and demo (local) | `LLMProvider` abstraction with Gemini and Ollama implementations |
| Event-Driven Processing | React to state changes, not polling | Webhook-driven ingestion pipeline |
| Dual Knowledge Store | Structured + unstructured knowledge | Neo4j (graph) + ChromaDB (vector) |
| Human-in-the-Loop | No autonomous external action without approval | Human Gate node in LangGraph |
| Citation-First Responses | Every factual claim backed by data source | Mandatory source references in all outputs |
| Stateful Agent Orchestration | Recoverable, inspectable agent workflows | LangGraph with checkpointing |

---

## 2. System Architecture Overview

### 2.1 C4 Level 1 — System Context

```
                           ┌──────────────────────┐
                           │    HUMAN USERS        │
                           │                       │
                           │  PMO Leader           │
                           │  Program Manager      │
                           │  Scrum Master         │
                           │  Evaluator            │
                           └───────────┬───────────┘
                                       │
                              Chat / Dashboard
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │                           │
                         │    ATHENA SYSTEM           │
                         │                           │
                         │  Monitors enterprise      │
                         │  data, detects risks,     │
                         │  answers queries,         │
                         │  alerts stakeholders      │
                         │                           │
                         └───────────────────────────┘
                                       ▲
                              Webhooks │
                                       │
                         ┌───────────────────────────┐
                         │    PROJECT UNIVERSE        │
                         │    (Enterprise Simulator)  │
                         │                           │
                         │  Generates realistic      │
                         │  project events and       │
                         │  enterprise failures      │
                         └───────────────────────────┘
```

### 2.2 C4 Level 2 — Container Diagram

```
+==============================================================================+
||                          DOCKER COMPOSE NETWORK                             ||
+==============================================================================+
|                                                                               |
|  +---------------------------------+     +---------------------------------+  |
|  |       PROJECT UNIVERSE          |     |          ATHENA CORE            |  |
|  |         (Simulator)             |     |           (Agent)               |  |
|  +---------------------------------+     +---------------------------------+  |
|  |                                 |     |                                 |  |
|  |  ┌───────────┐  ┌───────────┐  |     |  ┌───────────┐  ┌───────────┐  |  |
|  |  │ Jira-Sim  │  │  Chaos    │  |     |  │ Ingestion │  │  Agent    │  |  |
|  |  │ API       │  │  Engine   │  |     |  │ Pipeline  │  │  Brain    │  |  |
|  |  │ (FastAPI) │  │ (cron)    │  |     |  │ (FastAPI) │  │(LangGraph)│  |  |
|  |  │ Port:8001 │  │          │  |     |  │ Port:8000 │  │          │  |  |
|  |  └─────┬─────┘  └─────┬────┘  |     |  └─────┬─────┘  └─────┬────┘  |  |
|  |        │              │        |     |        │              │        |  |
|  |        └───────┬──────┘        |     |        └───────┬──────┘        |  |
|  |                │               |     |                │               |  |
|  +----------------|---------------+     +----------------|---------------+  |
|                   │                                      │                   |
|                   │  Webhook (HTTP POST)                 │                   |
|                   └─────────────────────────────────────>│                   |
|                                                          │                   |
|  +---------------------------------+     +---------------------------------+  |
|  |          DATA LAYER             |     |       INFERENCE LAYER           |  |
|  +---------------------------------+     +---------------------------------+  |
|  |                                 |     |                                 |  |
|  |  ┌─────────┐  ┌─────────┐      |     |  ┌──────────────────────────┐   |  |
|  |  │ SQLite  │  │  Neo4j  │      |     |  │     LLMProvider          │   |  |
|  |  │ (Mock   │  │ (Graph  │      |     |  │     (Abstraction)        │   |  |
|  |  │ Jira DB)│  │  Store) │      |     |  ├──────────────────────────┤   |  |
|  |  │         │  │Port:7474│      |     |  │ Dev:  GeminiProvider     │   |  |
|  |  └─────────┘  │    7687 │      |     |  │       (Gemini 1.5 Flash  │   |  |
|  |               └─────────┘      |     |  │        via Google AI     │   |  |
|  |  ┌─────────┐                   |     |  │        Studio free tier) │   |  |
|  |  │ChromaDB │                   |     |  ├──────────────────────────┤   |  |
|  |  │(Vector  │                   |     |  │ Demo: OllamaProvider     │   |  |
|  |  │ Store)  │                   |     |  │       (Ollama + Llama 3  │   |  |
|  |  │Port:8002│                   |     |  │        8B Q4, Port:11434)│   |  |
|  |  └─────────┘                   |     |  └──────────────────────────┘   |  |
|  +---------------------------------+     +---------------------------------+  |
|                                                                               |
|  +------------------------------------------------------------------------+  |
|  |                        PRESENTATION LAYER                               |  |
|  +------------------------------------------------------------------------+  |
|  |  ┌────────────────┐  ┌─────────────────┐  ┌────────────────────────┐   |  |
|  |  │ Chat Interface │  │ Health Dashboard │  │   God Mode Console    │   |  |
|  |  │ (Next.js)      │  │ (Next.js)       │  │   (Next.js)           │   |  |
|  |  │                │  │ RAG indicators  │  │   Chaos injection UI  │   |  |
|  |  └────────────────┘  └─────────────────┘  └────────────────────────┘   |  |
|  |                         Port: 3000                                      |  |
|  +------------------------------------------------------------------------+  |
+===============================================================================+
```

---

## 3. Component Specifications

### 3.1 Project Universe (Simulator Layer)

#### 3.1.1 Jira-Sim API

| Attribute | Specification |
|-----------|--------------|
| **Framework** | FastAPI (Python 3.11) |
| **Port** | 8001 |
| **Database** | SQLite (file-based) |
| **Purpose** | Simulate Jira REST API for CRUD operations on project entities |

**API Endpoints:**

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|-------------|----------|
| GET | `/api/v1/tickets` | List all tickets (paginated) | — | `[{id, title, status, priority, assignee, ...}]` |
| POST | `/api/v1/tickets` | Create a new ticket | `{title, description, priority, assignee_id, epic_id}` | `{id, ...created_ticket}` |
| GET | `/api/v1/tickets/{id}` | Get ticket details | — | `{id, title, status, priority, assignee, history, ...}` |
| PUT | `/api/v1/tickets/{id}` | Update a ticket | `{fields_to_update}` | `{id, ...updated_ticket}` |
| DELETE | `/api/v1/tickets/{id}` | Delete a ticket | — | `{success: true}` |
| GET | `/api/v1/users` | List all users | — | `[{id, name, email, role, active_tasks}]` |
| GET | `/api/v1/epics` | List all epics | — | `[{id, name, project, stories_count, progress}]` |
| GET | `/api/v1/sprints` | List all sprints | — | `[{id, name, start, end, status, tickets}]` |
| GET | `/api/v1/projects` | List all projects | — | `[{id, name, status, health, milestones}]` |
| GET | `/api/v1/risks` | List detected risks | — | `[{id, type, severity, affected_entity, status}]` |
| GET | `/api/v1/health` | System health check | — | `{status: "ok", uptime, stats}` |
| POST | `/api/v1/chaos/trigger` | Manually trigger chaos event | `{chaos_type}` | `{event_id, type, affected_entities}` |

#### 3.1.2 Chaos Engine

| Attribute | Specification |
|-----------|--------------|
| **Scheduler** | APScheduler (BackgroundScheduler) |
| **Frequency** | Configurable (default: every 5 minutes) |
| **Chaos Types** | 6 failure injection patterns |

**Chaos Event Types:**

```
CHAOS ENGINE — FAILURE INJECTION PATTERNS
═════════════════════════════════════════════

1. TICKET_BLOCKER
   ├─ Action: Set random CRITICAL ticket to status="BLOCKED"
   ├─ Creates: [:BLOCKS] relationship in downstream sync
   └─ Frequency: ~40% of chaos events

2. DEVELOPER_OVERLOAD
   ├─ Action: Assign >5 CRITICAL tasks to one developer
   ├─ Creates: Multiple [:ASSIGNED_TO] relationships
   └─ Frequency: ~15% of chaos events

3. MILESTONE_DELAY
   ├─ Action: Set milestone.due_date to past date
   ├─ Creates: Overdue flag on Milestone node
   └─ Frequency: ~15% of chaos events

4. DEPENDENCY_CYCLE
   ├─ Action: Create circular DEPENDS_ON chain (A→B→C→A)
   ├─ Creates: Cycle in [:DEPENDS_ON] graph
   └─ Frequency: ~10% of chaos events

5. PRIORITY_ESCALATION
   ├─ Action: Escalate LOW/MEDIUM ticket to CRITICAL
   ├─ Creates: Priority change event
   └─ Frequency: ~10% of chaos events

6. CONFLICTING_UPDATE
   ├─ Action: Simultaneously update same ticket with
   │         conflicting status values
   ├─ Creates: Data reconciliation challenge
   └─ Frequency: ~10% of chaos events
```

#### 3.1.3 Webhook Dispatcher

| Attribute | Specification |
|-----------|--------------|
| **HTTP Client** | httpx (async) |
| **Target URL** | `http://athena-core:8000/api/v1/webhook/event` |
| **Retry Policy** | 3 retries with exponential backoff (1s, 2s, 4s) |
| **Timeout** | 10 seconds per request |

**Webhook Payload Format:**

```json
{
  "event_id": "uuid-v4",
  "event_type": "ticket_updated",
  "entity_type": "ticket",
  "entity_id": "TICKET-789",
  "changed_fields": {
    "status": {
      "old_value": "In Progress",
      "new_value": "Blocked"
    },
    "blocked_by": {
      "old_value": null,
      "new_value": "TICKET-456"
    }
  },
  "timestamp": "2026-03-15T14:00:00Z",
  "source": "chaos_engine",
  "metadata": {
    "chaos_rule": "TICKET_BLOCKER",
    "project_id": "PROJECT-1"
  }
}
```

---

### 3.2 Athena Core (Agent Layer)

#### 3.2.1 Ingestion Pipeline

```
INGESTION PIPELINE — PROCESSING FLOW
════════════════════════════════════════

  Webhook POST
       │
       ▼
  ┌─────────────────┐
  │  1. VALIDATE     │──── Invalid ──> HTTP 400 + log error
  │  (JSON schema)   │
  └────────┬─────────┘
           │ Valid
           ▼
  ┌─────────────────┐
  │  2. DEDUPLICATE  │──── Duplicate ──> HTTP 200 + skip
  │  (event_id check)│
  └────────┬─────────┘
           │ New event
           ▼
  ┌─────────────────┐
  │  3. ROUTE        │
  │  (entity_type)   │
  └────────┬─────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
  ┌───────┐  ┌────────┐
  │ Graph │  │ Vector │
  │ Syncer│  │ Indexer│
  └───┬───┘  └───┬────┘
      │          │
      ▼          ▼
  ┌───────┐  ┌────────┐
  │ Neo4j │  │ChromaDB│
  └───────┘  └────────┘
           │
           ▼
  ┌─────────────────┐
  │  4. NOTIFY       │
  │  Agent Brain     │──── If risk event, trigger analysis
  └─────────────────┘
```

#### 3.2.2 Graph Syncer (Neo4j)

**Node Types and Properties:**

| Node Label | Properties | Primary Key |
|-----------|------------|-------------|
| Project | id, name, status, health, start_date, end_date | id |
| Epic | id, name, project_id, status, progress_pct | id |
| Story/Task | id, title, description, status, priority, created_at, updated_at | id |
| User | id, name, email, role, team | id |
| Risk | id, type, severity, description, status, detected_at | id |
| Milestone | id, name, due_date, status, completion_pct | id |
| Sprint | id, name, start_date, end_date, status | id |

**Relationship Types:**

| Relationship | From → To | Properties |
|-------------|-----------|------------|
| ASSIGNED_TO | Task → User | assigned_at |
| BLOCKS | Task → Task | blocked_since |
| DEPENDS_ON | Task → Task | dependency_type |
| PART_OF | Task → Epic | — |
| BELONGS_TO | Epic → Project | — |
| HAS_RISK | Task → Risk | detected_at |
| IMPACTS | Risk → Milestone | impact_level |
| OWNS | User → Project | role |
| MEMBER_OF | User → Sprint | — |
| TARGETS | Sprint → Milestone | — |

**Knowledge Graph Schema Diagram:**

```
                         ┌──────────┐
                         │ PROJECT  │
                         └────┬─────┘
                              │ BELONGS_TO
                    ┌─────────┼─────────┐
                    ▼                   ▼
              ┌──────────┐       ┌───────────┐
              │   EPIC   │       │ MILESTONE │
              └────┬─────┘       └─────┬─────┘
                   │ PART_OF           │ IMPACTS
                   ▼                   ▲
              ┌──────────┐       ┌──────────┐
              │  TASK    │──────>│   RISK   │
              │          │HAS_   │          │
              └──┬───┬───┘RISK   └──────────┘
  ASSIGNED_TO ┌──┘   └──┐ BLOCKS / DEPENDS_ON
              ▼          ▼
         ┌────────┐  ┌────────┐
         │  USER  │  │  TASK  │ (another task)
         └────────┘  └────────┘
```

#### 3.2.3 Vector Indexer (ChromaDB)

| Collection | Content Source | Metadata Fields |
|-----------|--------------|----------------|
| `ticket_context` | Ticket titles + descriptions + comments | source_id, entity_type, priority, status, timestamp |
| `meeting_notes` | Generated risk summaries + agent analysis | source_id, analysis_type, severity, timestamp |

#### 3.2.4 LangGraph Agent Brain — State Machine Design

```
                              ┌──────────┐
                              │  START   │
                              └────┬─────┘
                                   │
                                   ▼
                         ┌──────────────────┐
                    ┌────│ SEMANTIC ROUTER   │────┐
                    │    │ (Classify input)  │    │
                    │    └──────────────────┘    │
                    │              │              │
              query/event    risk_event     general
                    │              │              │
                    ▼              ▼              ▼
          ┌──────────────┐ ┌────────────┐ ┌────────────┐
          │   PLANNER    │ │  PLANNER   │ │  PLANNER   │
          │ type:QUERY   │ │ type:RISK  │ │ type:GEN   │
          └──────┬───────┘ └─────┬──────┘ └─────┬──────┘
                 │               │              │
                 ▼               ▼              │
          ┌──────────────┐ ┌────────────┐       │
          │  RESEARCHER  │ │ RESEARCHER │       │
          │              │ │            │       │
          │ Tools:       │ │ Tools:     │       │
          │ search_graph │ │ search_    │       │
          │ search_docs  │ │ graph      │       │
          │ get_user_    │ │ search_    │       │
          │ info         │ │ docs       │       │
          └──────┬───────┘ │ get_user_  │       │
                 │         │ info       │       │
                 │         └─────┬──────┘       │
                 │               │              │
                 │               ▼              │
                 │         ┌────────────┐       │
                 │         │  ALERTER   │       │
                 │         │            │       │
                 │         │ Tools:     │       │
                 │         │ draft_     │       │
                 │         │ message    │       │
                 │         │ classify_  │       │
                 │         │ severity   │       │
                 │         └─────┬──────┘       │
                 │               │              │
                 └───────┬───────┘              │
                         ▼                      │
                 ┌──────────────┐               │
                 │  RESPONDER   │<──────────────┘
                 │              │
                 │  Format with │
                 │  citations   │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │  HUMAN GATE  │
                 │              │
                 │  If type is  │
                 │  RISK or     │
                 │  ACTION:     │
                 │  PAUSE for   │
                 │  approval    │
                 └──────┬───────┘
                        │
              ┌─────────┼─────────┐
              │         │         │
          Approved   Rejected   Auto
              │         │      (queries)
              ▼         ▼         │
        ┌──────────┐ ┌──────┐    │
        │ EXECUTOR │ │ LOG  │    │
        │          │ │ ONLY │    │
        │ Execute  │ └──┬───┘    │
        │ + log    │    │        │
        └────┬─────┘    │        │
             │          │        │
             └──────┬───┘────────┘
                    ▼
              ┌──────────┐
              │   END    │
              │ (Return  │
              │ response)│
              └──────────┘
```

**Agent State TypedDict:**

```python
class AgentState(TypedDict):
    session_id: str           # Unique session ID
    input: str                # User query or webhook event
    input_type: str           # STATUS_QUERY | RISK_ALERT | ACTION_REQUEST | GENERAL
    messages: list            # Conversation history (multi-turn)
    graph_results: list       # Neo4j Cypher query results
    vector_results: list      # ChromaDB semantic search results
    draft_response: str       # Generated response text
    citations: list           # Source entity IDs [TICKET-123, EPIC-7, ...]
    confidence: float         # 0.0 to 1.0
    severity: str             # CRITICAL | HIGH | MEDIUM | LOW | NONE
    requires_approval: bool   # Whether Human Gate should pause
    approval_status: str      # PENDING | APPROVED | REJECTED | AUTO
    atl_entry: dict           # ATL log entry data
    error: str                # Error message if any
```

**Agent Tool Specifications:**

| Tool | Input Params | Action | Returns |
|------|-------------|--------|---------|
| `search_graph(query)` | Cypher query string | Execute on Neo4j via py2neo | List of node/relationship dicts |
| `search_docs(text, k)` | Search text, top-K | Semantic search on ChromaDB | List of {text, metadata, score} |
| `get_user_info(user_id)` | User ID string | Lookup in Neo4j | {name, email, role, active_tasks} |
| `draft_message(context, template)` | Context dict, template name | LLM generates from template | Formatted alert/response string |
| `classify_severity(risk_data)` | Risk context dict | Rule-based + LLM classification | Severity level enum |
| `log_action(entry)` | ATL entry dict | Insert into ATL table | {entry_id, timestamp} |

---

### 3.3 Presentation Layer (Dashboard)

| Component | Technology | Features |
|-----------|-----------|----------|
| Chat Interface | Next.js + WebSocket | NL query input, streaming responses, citation links, conversation history |
| Health Dashboard | Next.js + REST polling | RAG indicators per project, risk count, blocked count, health score |
| God Mode Console | Next.js + REST | Chaos type selector, inject button, real-time event log, agent state viewer |

---

## 4. Sequence Diagrams

### 4.1 End-to-End: Chaos Event → Detection → Alert

```
 Chaos     Jira-Sim    Webhook     Ingestion   Graph    Vector   Agent    Human    Dashboard
 Engine      API       Dispatch    Pipeline    Syncer   Indexer   Brain    Gate
   │          │          │           │           │        │        │        │         │
   │ mutate   │          │           │           │        │        │        │         │
   │ ticket   │          │           │           │        │        │        │         │
   │─────────>│          │           │           │        │        │        │         │
   │          │          │           │           │        │        │        │         │
   │          │ state    │           │           │        │        │        │         │
   │          │ changed  │           │           │        │        │        │         │
   │          │─────────>│           │           │        │        │        │         │
   │          │          │           │           │        │        │        │         │
   │          │          │ HTTP POST │           │        │        │        │         │
   │          │          │──────────>│           │        │        │        │         │
   │          │          │           │           │        │        │        │         │
   │          │          │           │ upsert    │        │        │        │         │
   │          │          │           │──────────>│        │        │        │         │
   │          │          │           │           │        │        │        │         │
   │          │          │           │ embed     │        │        │        │         │
   │          │          │           │──────────────────>│        │        │         │
   │          │          │           │           │        │        │        │         │
   │          │          │           │ notify    │        │        │        │         │
   │          │          │           │──────────────────────────>│        │         │
   │          │          │           │           │        │        │        │         │
   │          │          │           │           │  query │        │        │         │
   │          │          │           │           │<───────────────│        │         │
   │          │          │           │           │  results       │        │         │
   │          │          │           │           │───────────────>│        │         │
   │          │          │           │           │        │        │        │         │
   │          │          │           │           │        │  query │        │         │
   │          │          │           │           │        │<───────│        │         │
   │          │          │           │           │        │results │        │         │
   │          │          │           │           │        │───────>│        │         │
   │          │          │           │           │        │        │        │         │
   │          │          │           │           │        │        │ hold   │         │
   │          │          │           │           │        │        │ alert  │         │
   │          │          │           │           │        │        │───────>│         │
   │          │          │           │           │        │        │        │         │
   │          │          │           │           │        │        │        │ show    │
   │          │          │           │           │        │        │        │ pending │
   │          │          │           │           │        │        │        │────────>│
   │          │          │           │           │        │        │        │         │
```

### 4.2 User Query Processing

```
  User        Dashboard      Athena API      Planner      Researcher     LLM        Responder
    │             │              │              │             │           │            │
    │ NL query    │              │              │             │           │            │
    │────────────>│              │              │             │           │            │
    │             │ POST /query  │              │             │           │            │
    │             │─────────────>│              │             │           │            │
    │             │              │ classify     │             │           │            │
    │             │              │─────────────>│             │           │            │
    │             │              │              │             │           │            │
    │             │              │              │ tool calls  │           │            │
    │             │              │              │────────────>│           │            │
    │             │              │              │             │           │            │
    │             │              │              │             │ Cypher    │            │
    │             │              │              │             │ + search  │            │
    │             │              │              │             │──────────>│            │
    │             │              │              │             │           │            │
    │             │              │              │             │ context   │            │
    │             │              │              │             │<──────────│            │
    │             │              │              │             │           │            │
    │             │              │              │ results     │           │            │
    │             │              │              │<────────────│           │            │
    │             │              │              │             │           │            │
    │             │              │ format       │             │           │            │
    │             │              │──────────────────────────────────────>│            │
    │             │              │              │             │           │  cited     │
    │             │              │              │             │           │  response  │
    │             │              │<─────────────────────────────────────────────────── │
    │             │ response     │              │             │           │            │
    │             │<─────────────│              │             │           │            │
    │ display     │              │              │             │           │            │
    │<────────────│              │              │             │           │            │
    │             │              │              │             │           │            │
```

---

## 5. Deployment Architecture

### 5.1 Docker Compose Service Topology

```
+=========================================================================+
|                       docker-compose.yml                                |
+=========================================================================+
|                                                                         |
|  SERVICE           IMAGE              PORT     DEPENDS_ON     VOLUMES   |
|  ─────────────     ────────────────   ─────    ──────────     ────────  |
|                                                                         |
|  sim-api           athena/sim:latest  8001     sim-db         ./data/   |
|  sim-chaos         athena/chaos:latest  —      sim-api        —        |
|  athena-core       athena/core:latest 8000     graph-db,      ./logs/  |
|                                                vector-db               |
|  graph-db          neo4j:5-community  7474,    —              neo4j_   |
|                                       7687                   data/     |
|  vector-db         chromadb/chroma    8002     —              chroma_  |
|                                                              data/     |
|  ollama            ollama/ollama      11434    —              ollama_  |
|  (DEMO MODE ONLY)                                            models/   |
|  dashboard         athena/ui:latest   3000     athena-core    —        |
|                                                                         |
+=========================================================================+

NETWORK: athena-network (bridge)
  All services communicate via Docker internal DNS
  Only exposed ports: 3000 (Dashboard), 8001 (Simulator, optional)

DEPLOYMENT MODES:
  Dev mode:   docker compose --profile dev up -d       (no Ollama)
  Demo mode:  docker compose --profile demo up -d      (includes Ollama)
  LLM_BACKEND env var controls which LLMProvider is active
```

### 5.2 Service Dependency Graph

```
                    ┌──────────┐
                    │ dashboard│
                    │ :3000    │
                    └────┬─────┘
                         │ depends_on
                         ▼
                    ┌──────────┐
                    │ athena-  │
                    │ core     │
                    │ :8000    │
                    └──┬─┬─┬──┘
           ┌───────────┘ │ └───────────┐
           ▼             ▼             ▼
      ┌──────────┐  ┌──────────┐  ┌──────────────┐
      │ graph-db │  │vector-db │  │    ollama    │
      │ (Neo4j)  │  │(ChromaDB)│  │  (Llama 3)   │
      │ :7474    │  │ :8002    │  │  :11434      │
      └──────────┘  └──────────┘  │ DEMO MODE    │
                                  │ ONLY (opt.)  │
                                  └──────────────┘

  Dev Mode:  athena-core → Gemini API (external, free tier)
  Demo Mode: athena-core → ollama container (local, air-gapped)

     ┌──────────┐
     │sim-chaos │──────────┐
     └──────────┘          │ depends_on
                           ▼
                    ┌──────────┐
                    │ sim-api  │
                    │ :8001    │
                    └────┬─────┘
                         │ depends_on
                         ▼
                    ┌──────────┐
                    │  sim-db  │
                    │ (SQLite) │
                    └──────────┘
```

---

## 6. API Contracts

### 6.1 Athena Core API

| Method | Endpoint | Purpose | Auth |
|--------|----------|---------|------|
| POST | `/api/v1/webhook/event` | Receive webhook from simulator | Internal |
| POST | `/api/v1/query` | Process natural language query | Session |
| GET | `/api/v1/health` | System health status | None |
| GET | `/api/v1/atl` | Retrieve ATL entries (paginated) | Session |
| GET | `/api/v1/atl/{id}` | Get specific ATL entry | Session |
| POST | `/api/v1/approval/{id}` | Approve/Reject pending action | Session |
| GET | `/api/v1/metrics` | Dashboard health metrics | Session |
| GET | `/api/v1/risks/active` | List active detected risks | Session |

### 6.2 Inter-Service Communication

```
  Dashboard ──HTTP──> Athena Core ──> LLMProvider:
                           │              ├── Dev:  HTTPS ──> Gemini API (external)
                           │              └── Demo: HTTP  ──> Ollama (internal)
                           │
                           ├──bolt://──> Neo4j (Cypher queries)
                           │
                           ├──HTTP──> ChromaDB (Vector search)
                           │
                           └──HTTP──> Simulator API (optional, for God Mode)

  Simulator ──HTTP POST webhook──> Athena Core
```

---

## 7. Security Architecture

### 7.1 Threat Model

| Threat | Severity | Mitigation |
|--------|----------|-----------|
| Data leakage to external APIs | HIGH | Demo mode: fully air-gapped (Ollama). Dev mode: only LLM prompts sent to Gemini API; no project data in prompts |
| LLM hallucination in alerts | HIGH | Citation enforcement: all claims must reference Neo4j/ChromaDB data |
| Unauthorized chaos injection | MEDIUM | God Mode behind authentication; chaos API internal-only |
| ATL tampering | MEDIUM | Append-only log design; no UPDATE/DELETE on ATL table |
| Container escape | LOW | Minimal container privileges; no root in containers |
| Prompt injection via ticket text | MEDIUM | Input sanitization; system prompts with strict boundary instructions |
| API key exposure | MEDIUM | Gemini API key in `.env` only (gitignored); never committed to VCS |

### 7.2 Privacy Model

```
DATA FLOW PRIVACY ANALYSIS
════════════════════════════

  DEV MODE (Cloud LLM — Gemini 1.5 Flash):
  ┌─────────────────────────────────────────────┐
  │           DOCKER HOST (localhost)            │
  │                                             │
  │  Synthetic Data ──> SQLite ──> Neo4j        │
  │       │                         │           │
  │       │              ChromaDB <─┘           │
  │       │                 │                   │
  │       └──> LLMProvider (GeminiProvider)     │
  │                │                            │
  │                │ HTTPS (prompts only)        │
  │                └──────────────┐              │
  │                               │              │
  │  ✓ Project data stays local   │              │
  │  ✓ Only LLM prompts external  │              │
  │  ╳ NO telemetry or analytics  │              │
  └───────────────────────────────│──────────────┘
                                  ▼
                     ┌───────────────────────┐
                     │ Google AI Studio API  │
                     │ (Gemini 1.5 Flash)    │
                     │ Free tier: 15 RPM     │
                     └───────────────────────┘

  DEMO MODE (Local LLM — Ollama + Llama 3 8B Q4):
  ┌─────────────────────────────────────────────┐
  │           DOCKER HOST (localhost)            │
  │                                             │
  │  Synthetic Data ──> SQLite ──> Neo4j        │
  │       │                         │           │
  │       │              ChromaDB <─┘           │
  │       │                 │                   │
  │       └──> LLMProvider (OllamaProvider)     │
  │                │                            │
  │                └──> Ollama (LOCAL) ──> Resp  │
  │                                             │
  │  ╳ NO external API calls                    │
  │  ╳ NO telemetry or analytics                │
  │  ╳ NO cloud storage                         │
  │  ✓ ALL processing on localhost              │
  │  ✓ Works with network cable unplugged       │
  └─────────────────────────────────────────────┘
```

---

## 8. Technology Stack Summary

| Layer | Component | Technology | Version | License |
|-------|-----------|-----------|---------|---------|
| Simulator | REST API | FastAPI | 0.109+ | MIT |
| Simulator | Scheduler | APScheduler | 3.10+ | MIT |
| Simulator | HTTP Client | httpx | 0.27+ | BSD |
| Simulator | Database | SQLite | 3.x | Public Domain |
| Agent | Orchestrator | LangGraph | 0.1+ | MIT |
| Agent | Graph Client | py2neo | 2021.2+ | Apache 2.0 |
| Agent | Vector Client | chromadb | 0.4+ | Apache 2.0 |
| Agent | LLM Abstraction | LLMProvider (custom) | — | Project code |
| Inference (Dev) | LLM API | Google Gemini 1.5 Flash | latest | Google ToS (free tier) |
| Inference (Dev) | Python SDK | google-generativeai | 0.5+ | Apache 2.0 |
| Inference (Demo) | LLM Server | Ollama | 0.1+ | MIT |
| Inference (Demo) | Model | Llama 3 8B Q4 | 3.0 | Meta Community |
| Data | Graph DB | Neo4j CE | 5.x | GPL v3 |
| Data | Vector DB | ChromaDB | 0.4+ | Apache 2.0 |
| Frontend | Framework | Next.js | 14.x | MIT |
| Frontend | Language | TypeScript | 5.x | Apache 2.0 |
| DevOps | Containers | Docker | 24.0+ | Apache 2.0 |
| DevOps | Orchestration | Docker Compose | 2.x | Apache 2.0 |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-02-05 | Team Athena | Initial architecture definition |
| 0.2.0 | 2026-02-19 | Team Athena | Comprehensive architecture with C4 diagrams, API contracts, sequence diagrams, agent state machine, deployment topology, security model, technology stack |
| 0.2.1 | 2026-02-20 | Team Athena | Updated for hybrid dual-mode LLM architecture: LLMProvider abstraction, Gemini (dev) + Ollama (demo), deployment profiles, updated threat/privacy model, tech stack expanded |
