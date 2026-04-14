# System Design Document
**Document ID:** Athena_HLD_System-Architecture_v0.3.0  
**Project:** Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation  
**Date:** 2026-03-03  
**Version:** 0.3.0 (Minor - Restructured to Academic System Design Format)

---

## 1. Introduction to the System

### 1.1 Purpose

Project Athena is an AI-powered Program Management Office (PMO) assistant that autonomously ingests enterprise project data, synthesizes it into a unified Knowledge Graph and Vector Store, and proactively detects risks before they become blockers. It replaces the 10-15 hours/week of manual status aggregation that Program Managers currently spend across Jira, Azure DevOps, and Confluence.

### 1.2 Design Philosophy

The system follows a **Dual-Architecture** approach with strict separation of concerns:

1. **Project Universe** — A high-fidelity enterprise simulator that generates realistic PM events as the data source
2. **Athena Core** — A multi-agent reasoning engine that ingests, synthesizes, and acts on those events

These two systems communicate exclusively via HTTP webhooks and REST APIs, mirroring how a real AI agent would integrate with enterprise tools. This architectural separation ensures Athena Core is production-portable — it could connect to real Jira APIs without code changes.

### 1.3 System Context

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

### 1.4 Design Principles

| Principle | Description | Implementation |
|-----------|-------------|----------------|
| Air-Gapped Capable | Fully offline deployment via Ollama | All services run locally via Docker Compose |
| Dual-Mode LLM | Pluggable LLM backend for dev and demo | `LLMProvider` abstraction with Gemini, Groq, and Ollama |
| Event-Driven | React to state changes, not polling | Webhook-driven ingestion pipeline |
| Dual Knowledge Store | Structured + unstructured knowledge | Neo4j (graph) + Pinecone (vector) |
| Human-in-the-Loop | No autonomous action without approval | Human Gate node in LangGraph |
| Citation-First | Every factual claim backed by data | Mandatory source references in all outputs |
| Stateful Orchestration | Recoverable, inspectable workflows | LangGraph with state checkpointing |

---

## 2. Architectural Design

### 2.1 Overall Architecture — Layered Microservices Model

Athena follows a **layered microservices architecture** with four distinct tiers: Presentation, Application, Data, and Inference.

```
+==============================================================================+
||                       DOCKER COMPOSE NETWORK (athena-network)               ||
+==============================================================================+
|                                                                               |
|  +------------------------------+     +-----------------------------------+   |
|  |    PRESENTATION LAYER        |     |        APPLICATION LAYER          |   |
|  +------------------------------+     +-----------------------------------+   |
|  |                              |     |                                   |   |
|  | ┌──────────┐ ┌───────────┐  |     | ┌───────────────┐ ┌────────────┐ |   |
|  | │ Chat     │ │ Health    │  |     | │ Jira-Sim API  │ │ Athena     │ |   |
|  | │ Interface│ │ Dashboard │  |     | │ (FastAPI)     │ │ Core API   │ |   |
|  | │          │ │ (RAG)     │  |     | │ Port: 8000    │ │ (FastAPI)  │ |   |
|  | └──────────┘ └───────────┘  |     | │               │ │ Port: 8001 │ |   |
|  | ┌──────────────────────┐    |     | ├───────────────┤ ├────────────┤ |   |
|  | │ God Mode Console     │    |     | │ Chaos Engine  │ │ Agent Brain│ |   |
|  | │ (Chaos Injection UI) │    |     | │ (APScheduler) │ │ (LangGraph)│ |   |
|  | └──────────────────────┘    |     | └───────────────┘ └────────────┘ |   |
|  |       Next.js 14 :3000      |     |                                   |   |
|  +------------------------------+     +-----------------------------------+   |
|                                                                               |
|  +------------------------------+     +-----------------------------------+   |
|  |       DATA LAYER             |     |       INFERENCE LAYER             |   |
|  +------------------------------+     +-----------------------------------+   |
|  |                              |     |                                   |   |
|  | ┌──────────┐ ┌───────────┐  |     | ┌───────────────────────────────┐ |   |
|  | │PostgreSQL│ │ Neo4j     │  |     | │       LLMProvider             │ |   |
|  | │ (Neon)   │ │ Aura      │  |     | │       (Abstraction)           │ |   |
|  | │ Sim DB   │ │ Graph DB  │  |     | ├───────────────────────────────┤ |   |
|  | │ (cloud)  │ │ (cloud)   │  |     | │ Dev:  GeminiProvider          │ |   |
|  | └──────────┘ └───────────┘  |     | │       (Gemini 1.5 Flash API)  │ |   |
|  | ┌──────────┐                |     | ├───────────────────────────────┤ |   |
|  | │ Pinecone │                |     | │ Fast: GroqProvider            │ |   |
|  | │ Vector   │                |     | │       (Llama 3.3 70B, cloud)  │ |   |
|  | │ Store    │                |     | ├───────────────────────────────┤ |   |
|  | │ (cloud)  │                |     | │ Demo: OllamaProvider          │ |   |
|  | └──────────┘                |     | │       (Llama 3 8B, local GPU) │ |   |
|  +------------------------------+     +───────────────────────────────────+   |
+===============================================================================+
```

### 2.2 Module Breakdown

| Layer | Module | Technology | Responsibility |
|-------|--------|------------|----------------|
| **Presentation** | Chat Interface | Next.js 14 + WebSocket | NL query input, streaming responses, citation links |
| **Presentation** | Health Dashboard | Next.js 14 + REST | RAG indicators, risk counts, health scores |
| **Presentation** | God Mode Console | Next.js 14 + REST | Chaos injection UI, real-time event log |
| **Application** | Jira-Sim API | FastAPI (Python) | Mock Jira REST API with CRUD for all PM entities |
| **Application** | Chaos Engine | APScheduler (Python) | Scheduled fault injection (3 patterns) |
| **Application** | Webhook Dispatcher | httpx (Python) | Fires Jira-compatible webhooks to Athena |
| **Application** | Ingestion Pipeline | FastAPI (Python) | Validates, deduplicates, and routes webhook events |
| **Application** | Agent Brain | LangGraph (Python) | Multi-agent state machine (6 agent nodes) |
| **Data** | Simulator DB | PostgreSQL (Neon) | Relational storage for simulator entities |
| **Data** | Knowledge Graph | Neo4j Aura | Structured entity relationships and graph traversal |
| **Data** | Vector Store | Pinecone | Semantic similarity search over text embeddings |
| **Inference** | LLMProvider | Custom abstraction | Pluggable interface for Gemini, Groq, Ollama backends |

### 2.3 Inter-Module Communication

```
  Dashboard ──HTTP/WS──> Athena Core API
                              │
                              ├──HTTP REST──> Simulator API (10 Jira TOOL_CONFIG endpoints)
                              │
                              ├──Cypher (bolt://)──> Neo4j Aura (cloud)
                              │
                              ├──HTTP──> Pinecone (cloud)
                              │
                              └──HTTP──> LLMProvider:
                                            ├── Dev:  HTTPS ──> Gemini API
                                            ├── Fast: HTTPS ──> Groq API
                                            └── Demo: HTTP  ──> Ollama (local)

  Simulator API ──HTTP POST webhook──> Athena Core API

  Chaos Engine ──HTTP──> Simulator API (mutates data, triggers webhooks)
```

---

## 3. Data Flow Diagram

### 3.1 Level 0 — Context DFD

```
+──────────────+                                           +──────────────+
│              │    Webhook Events (HTTP POST)              │              │
│   PROJECT    │──────────────────────────────────────────>│   ATHENA     │
│   UNIVERSE   │                                           │   SYSTEM     │
│  (Simulator) │<──────────────────────────────────────────│              │
│              │    God Mode Commands (REST)                │              │
+──────────────+                                           +──────┬───────+
                                                                  │
                                                      Cited Responses,
                                                      Alerts, RAG Health
                                                                  │
                                                                  ▼
                                                           +──────────────+
                                                           │    USERS     │
                                                           │ (PMO, PM,   │
                                                           │  Scrum, Eval)│
                                                           +──────────────+
```

### 3.2 Level 1 — System DFD

```
                    ┌──────────────────────────────────────────────────────┐
                    │                  ATHENA SYSTEM                       │
                    │                                                      │
 Webhook ──────────>│  ┌───────────────┐                                  │
 (from Simulator)   │  │ 1.0 INGESTION │                                  │
                    │  │   PIPELINE    │                                  │
                    │  │               │                                  │
                    │  │ - Validate    │                                  │
                    │  │ - Deduplicate │                                  │
                    │  │ - Route       │                                  │
                    │  └───────┬───────┘                                  │
                    │          │                                          │
                    │    ┌─────┴─────┐                                    │
                    │    ▼           ▼                                    │
                    │  ┌─────┐  ┌────────┐                               │
                    │  │ D1  │  │  D2    │                               │
                    │  │Neo4j│  │Pinecone│                               │
                    │  │Graph│  │Vectors │                               │
                    │  └──┬──┘  └───┬────┘                               │
                    │     │         │                                     │
                    │     └────┬────┘                                     │
                    │          ▼                                          │
                    │  ┌───────────────┐                                  │
                    │  │ 2.0 AGENT     │                                  │
 NL Query ─────────>│  │   BRAIN       │                                  │
 (from User)        │  │               │                                  │
                    │  │ - Planner     │                                  │
                    │  │ - Researcher  │──> LLMProvider ──> LLM Backend  │
                    │  │ - Alerter     │                                  │
                    │  │ - Responder   │                                  │
                    │  │ - Human Gate  │                                  │
                    │  │ - Executor    │                                  │
                    │  └───────┬───────┘                                  │
                    │          │                                          │
                    │          ▼                                          │
                    │  ┌───────────────┐    ┌───────────────┐            │
                    │  │ Cited Response│    │  D3 ATL       │            │
 <──────────────────│  │ (to User)     │    │  (Audit Log)  │            │
 Response / Alert   │  └───────────────┘    └───────────────┘            │
                    │                                                      │
                    └──────────────────────────────────────────────────────┘
```

### 3.3 Level 2 — Ingestion Pipeline Detail

```
  Webhook POST
       │
       ▼
  ┌─────────────────┐
  │  1.1 VALIDATE   │──── Invalid ──> HTTP 400 + log error
  │  (JSON schema)  │
  └────────┬────────┘
           │ Valid
           ▼
  ┌─────────────────┐
  │ 1.2 DEDUPLICATE │──── Duplicate ──> HTTP 200 + skip
  │ (event_id check)│
  └────────┬────────┘
           │ New event
           ▼
  ┌─────────────────┐
  │  1.3 ROUTE      │
  │  (entity_type)  │
  └────────┬────────┘
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
  │ Neo4j │  │Pinecone│
  │ Aura  │  │        │
  └───────┘  └────────┘
           │
           ▼
  ┌─────────────────┐
  │ 1.4 NOTIFY      │
  │ Agent Brain     │──── If risk event, trigger analysis
  └─────────────────┘
```

### 3.4 Database Schema — ER Diagram

```
  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐
  │     TEAM     │         │    USER      │         │   PROJECT    │
  ├──────────────┤    1:N  ├──────────────┤  1:N    ├──────────────┤
  │ PK id        │<────────│ PK id        │────────>│ PK id        │
  │    name      │         │    email     │  leads  │    key       │
  │ FK lead_id   │────────>│    name      │         │    name      │
  └──────────────┘         │    role      │         │    description│
                           │    department│         │ FK lead_id   │
                           │ FK team_id   │         │    created_at│
                           │    timezone  │         └──────┬───────┘
                           │    created_at│                │ 1:N
                           └──────┬───────┘                │
                                  │ 1:N                    │
                           ┌──────┴───────┐         ┌──────┴───────┐
                           │    STORY     │         │    EPIC      │
                           ├──────────────┤         ├──────────────┤
                           │ PK id        │    N:1  │ PK id        │
                           │    key       │────────>│    key       │
                           │ FK epic_id   │         │ FK project_id│
                           │ FK sprint_id │         │    title     │
                           │    title     │         │    description│
                           │    description│        │    status    │
                           │    status    │         │    priority  │
                           │    priority  │         │ FK reporter_id│
                           │    story_pts │         │    created_at│
                           │ FK reporter_id│        └──────────────┘
                           │ FK assignee_id│
                           │    created_at│         ┌──────────────┐
                           │    updated_at│         │   SPRINT     │
                           │    resolution│    N:1  ├──────────────┤
                           │              │────────>│ PK id        │
                           └──────┬───────┘         │ FK project_id│
                                  │ 1:N             │    name      │
                           ┌──────┴───────┐         │    state     │
                           │   COMMENT    │         │  start_date  │
                           ├──────────────┤         │  end_date    │
                           │ PK id        │         └──────────────┘
                           │ FK story_id  │
                           │ FK author_id │         ┌──────────────┐
                           │    body      │         │  AUDIT_LOG   │
                           │    created_at│         ├──────────────┤
                           └──────────────┘         │ PK id        │
                                                    │  entity_type │
                                                    │  entity_id   │
                                                    │  action      │
                                                    │  details(JSON)│
                                                    │  timestamp   │
                                                    └──────────────┘
```

### 3.5 Knowledge Graph Schema (Neo4j)

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
              │          │ HAS_  │          │
              └──┬───┬───┘ RISK  └──────────┘
  ASSIGNED_TO ┌──┘   └──┐ BLOCKS / DEPENDS_ON
              ▼          ▼
         ┌────────┐  ┌────────┐
         │  USER  │  │  TASK  │ (another task)
         └────────┘  └────────┘

  NODE TYPES:
  ┌────────────┬──────────────────────────────────────────────────┐
  │ Node       │ Properties                                       │
  ├────────────┼──────────────────────────────────────────────────┤
  │ Project    │ id, name, status, health, start_date, end_date  │
  │ Epic       │ id, name, project_id, status, progress_pct      │
  │ Task       │ id, title, description, status, priority        │
  │ User       │ id, name, email, role, team                     │
  │ Risk       │ id, type, severity, description, detected_at    │
  │ Milestone  │ id, name, due_date, status, completion_pct      │
  │ Sprint     │ id, name, start_date, end_date, status          │
  └────────────┴──────────────────────────────────────────────────┘

  RELATIONSHIP TYPES:
  ┌────────────────┬──────────────┬──────────────────────────────┐
  │ Relationship   │ From → To    │ Properties                   │
  ├────────────────┼──────────────┼──────────────────────────────┤
  │ ASSIGNED_TO    │ Task → User  │ assigned_at                  │
  │ BLOCKS         │ Task → Task  │ blocked_since                │
  │ DEPENDS_ON     │ Task → Task  │ dependency_type              │
  │ PART_OF        │ Task → Epic  │ —                            │
  │ BELONGS_TO     │ Epic → Proj  │ —                            │
  │ HAS_RISK       │ Task → Risk  │ detected_at                  │
  │ IMPACTS        │ Risk → Mile  │ impact_level                 │
  │ OWNS           │ User → Proj  │ role                         │
  └────────────────┴──────────────┴──────────────────────────────┘
```

---

## 4. User Interface (UI) Design

### 4.1 UI Wireframe — Dashboard Layout

```
+==============================================================================+
|  ATHENA DASHBOARD                                    [User: PM] [Logout]     |
+==============================================================================+
|                                                                               |
|  +---HEALTH PANEL (top bar)----------------------------------------------+   |
|  |                                                                        |   |
|  |  [■ Overall: GREEN]  [■ Risks: 3 AMBER]  [■ Blocked: 2 RED]          |   |
|  |  [■ Sprint: 72% ON-TRACK]  [■ Overloaded Devs: 1]                    |   |
|  |                                                                        |   |
|  +------------------------------------------------------------------------+   |
|                                                                               |
|  +---LEFT PANEL (60%)--------------------+  +---RIGHT PANEL (40%)---------+  |
|  |                                        |  |                             |  |
|  |  RISK FEED                             |  |  CHAT INTERFACE             |  |
|  |  ┌──────────────────────────────────┐  |  |  ┌───────────────────────┐  |  |
|  |  │ ⚠ TICKET-789 BLOCKED (CRITICAL) │  |  |  │ You: What is the     │  |  |
|  |  │   Impacts: March Milestone       │  |  |  │ status of Project    │  |  |
|  |  │   Owner: dev_alice               │  |  |  │ Alpha?               │  |  |
|  |  │   [APPROVE] [REJECT] [MODIFY]    │  |  |  ├───────────────────────┤  |  |
|  |  ├──────────────────────────────────┤  |  |  │ Athena: Project Alpha│  |  |
|  |  │ ⚠ dev_bob OVERLOADED (6 tasks)  │  |  |  │ is 72% complete.     │  |  |
|  |  │   Recommend: Redistribute EPIC-12│  |  |  │ 2 blockers found:    │  |  |
|  |  │   [APPROVE] [REJECT]             │  |  |  │ TICKET-189, 234      │  |  |
|  |  └──────────────────────────────────┘  |  |  │ [Sources: EPIC-7]    │  |  |
|  |                                        |  |  │ Confidence: 94%      │  |  |
|  |  ATL (RECENT ACTIONS)                  |  |  └───────────────────────┘  |  |
|  |  ┌──────────────────────────────────┐  |  |                             |  |
|  |  │ 14:02 ALERT_SENT ticket_blocker  │  |  |  ┌───────────────────────┐  |  |
|  |  │ 14:01 RISK_DETECTED overload     │  |  |  │ [Type your query...] │  |  |
|  |  │ 13:58 QUERY_ANSWERED status      │  |  |  │              [SEND]  │  |  |
|  |  └──────────────────────────────────┘  |  |  └───────────────────────┘  |  |
|  +----------------------------------------+  +-----------------------------+  |
|                                                                               |
|  +---GOD MODE PANEL (collapsible, bottom)--------------------------------+   |
|  |  Chaos Type: [Ticket Blocker ▼]  [INJECT CHAOS]  | Last: 14:00 OK    |   |
|  +------------------------------------------------------------------------+   |
+===============================================================================+
```

### 4.2 Component Design

#### 4.2.1 Frontend Components

| Component | Type | Props/Inputs | Output | Description |
|-----------|------|--------------|--------|-------------|
| `<HealthBar />` | Display | health metrics JSON | RAG status indicators | Top-level program health bar with color-coded indicators |
| `<RiskFeed />` | Interactive | active risks list | Approval actions | List of pending risk alerts with Approve/Reject/Modify buttons |
| `<ChatPanel />` | Interactive | user query (string) | cited response | Multi-turn chat with Athena, displays citations and confidence |
| `<ATLViewer />` | Display | ATL entries list | scrollable log | Chronological audit trail of all agent decisions |
| `<GodModeConsole />` | Interactive | chaos type selection | injection status | Dropdown + button to trigger chaos events for demos |
| `<ApprovalCard />` | Interactive | alert context JSON | approve/reject | Individual pending alert card with full context and action buttons |

#### 4.2.2 Backend Integration

| Frontend Route | Backend Endpoint | Method | Data Flow |
|----------------|-----------------|--------|-----------|
| `/dashboard` | `/api/v1/metrics` | GET (polling 5s) | Real-time health metrics |
| `/chat` | `/api/v1/query` | POST | NL query → cited response |
| `/risks` | `/api/v1/risks/active` | GET | Active risk alerts |
| `/approval/:id` | `/api/v1/approval/{id}` | POST | Approve/Reject decision |
| `/atl` | `/api/v1/atl` | GET | Paginated audit log |
| `/godmode` | Simulator `/api/v1/chaos/trigger` | POST | Chaos event injection |

#### 4.2.3 User Feedback and Accessibility

- Chat responses display **confidence scores** (0–100%) and **data freshness timestamps**
- Error states show user-friendly messages (no raw stack traces or JSON errors)
- All interactive elements have unique IDs for automated testing
- RAG colors meet WCAG 2.1 contrast standards
- Chat input supports keyboard shortcuts (Enter to send, Shift+Enter for newline)
- Loading states with skeleton screens during API calls

---

## 5. Class Diagram and Classes

### 5.1 Simulator — ORM Models (SQLAlchemy)

```
+==================+      +==================+      +==================+
|      User        |      |      Team        |      |    Project       |
+==================+      +==================+      +==================+
| - id: String PK  |      | - id: String PK  |      | - id: String PK  |
| - email: String  |<──── | - name: String   |      | - key: String    |
| - name: String   | lead | - lead_id: FK    |      | - name: String   |
| - role: String   |      +==================+      | - description:Txt|
| - department: Str|                                 | - lead_id: FK    |──>User
| - team_id: FK    |──> Team                        | - created_at: DT |
| - timezone: Str  |                                 +==================+
| - created_at: DT |
+==================+
        ▲ assignee              ▲ reporter
        │                       │
+==================+      +==================+      +==================+
|      Story       |      |      Epic        |      |     Sprint       |
+==================+      +==================+      +==================+
| - id: String PK  |      | - id: String PK  |      | - id: String PK  |
| - key: String    |      | - key: String    |      | - project_id: FK |
| - epic_id: FK    |──>   | - project_id: FK |──>   | - name: String   |
| - sprint_id: FK  |──>   | - title: String  |      | - state: String  |
| - title: String  |      | - description:Txt|      |   (PLANNED/      |
| - description:Txt|      | - status: String |      |    ACTIVE/CLOSED) |
| - status: String |      | - priority: Str  |      | - start_date: DT |
| - priority: Str  |      | - reporter_id: FK|──>   | - end_date: DT   |
| - story_points:Int|     | - created_at: DT |      +==================+
| - reporter_id: FK|──>   +==================+
| - assignee_id: FK|──>                              +==================+
| - created_at: DT |      +==================+      |    AuditLog      |
| - updated_at: DT |      |     Comment      |      +==================+
| - resolution: DT |      +==================+      | - id: String PK  |
+==================+      | - id: String PK  |      | - entity_type:Str|
        │                  | - story_id: FK   |──>   | - entity_id: Str |
        └──────────────────| - author_id: FK  |──>   | - action: String |
                    1:N    | - body: Text     |      | - details: JSON  |
                           | - created_at: DT |      | - timestamp: DT  |
                           +==================+      +==================+
```

### 5.2 Athena Core — Agent Architecture Classes

```
+============================+
|     LLMProvider (ABC)      |
+============================+
| + generate(prompt): str    |
| + embed(text): list[float] |
+============================+
        ▲           ▲           ▲
        │           │           │
+============+ +============+ +============+
| GeminiProv | | GroqProv   | | OllamaProv |
+============+ +============+ +============+
| - api_key  | | - api_key  | | - base_url |
| - model    | | - model    | | - model    |
+============+ +============+ +============+


+==============================================+
|         AgentState (TypedDict)               |
+==============================================+
| + session_id: str                            |
| + input: str                                 |
| + input_type: str                            |
|   (STATUS_QUERY | RISK_ALERT |               |
|    ACTION_REQUEST | GENERAL)                 |
| + messages: list                             |
| + graph_results: list                        |
| + vector_results: list                       |
| + draft_response: str                        |
| + citations: list[str]                       |
| + confidence: float                          |
| + severity: str                              |
| + requires_approval: bool                    |
| + approval_status: str                       |
|   (PENDING | APPROVED | REJECTED | AUTO)     |
| + atl_entry: dict                            |
| + error: str                                 |
+==============================================+


+==============================================+
|         AgentBrain (LangGraph)               |
+==============================================+
| - state: AgentState                          |
| - llm: LLMProvider                           |
| - graph_client: Neo4jClient                  |
| - vector_client: PineconeClient              |
| - jira_client: JiraSimClient                 |
|----------------------------------------------|
| + planner(state): AgentState                 |
| + researcher(state): AgentState              |
| + alerter(state): AgentState                 |
| + responder(state): AgentState               |
| + human_gate(state): AgentState              |
| + executor(state): AgentState                |
|----------------------------------------------|
| JIRA INTEGRATION TOOLS (10):                 |
| + get_jira_issue(issue_key): dict            |
| + search_jira_issues(jql, comp): list        |
| + get_project_issues(proj, status?): list    |
| + get_user_issues(username?): list           |
| + get_sprint_issues(sprint?): list           |
| + get_issue_comments(issue_key): list        |
| + get_issue_transitions(issue_key): list     |
| + get_issue_attachments(issue_key): list     |
| + get_project_summary(proj_key): dict        |
| + download_issue_logs(issue_key): dict       |
|----------------------------------------------|
| INTERNAL KNOWLEDGE TOOLS (5):                |
| + search_graph(query: str): list             |
| + search_docs(text: str, k: int): list       |
| + draft_message(ctx: dict, tpl: str): str    |
| + classify_severity(risk: dict): str         |
| + log_action(entry: dict): dict              |
+==============================================++
```

---

## 6. Sequence Diagrams

### 6.1 End-to-End: Chaos Event → Detection → Alert

```
 Chaos     Jira-Sim   Webhook     Ingestion    Graph     Vector    Agent     Human    Dashboard
 Engine    API        Dispatch    Pipeline     Syncer    Indexer   Brain     Gate
   │         │          │           │            │         │         │         │         │
   │ mutate  │          │           │            │         │         │         │         │
   │ ticket  │          │           │            │         │         │         │         │
   │────────>│          │           │            │         │         │         │         │
   │         │ state    │           │            │         │         │         │         │
   │         │ changed  │           │            │         │         │         │         │
   │         │─────────>│           │            │         │         │         │         │
   │         │          │ HTTP POST │            │         │         │         │         │
   │         │          │──────────>│            │         │         │         │         │
   │         │          │           │ upsert     │         │         │         │         │
   │         │          │           │───────────>│         │         │         │         │
   │         │          │           │ embed      │         │         │         │         │
   │         │          │           │───────────────────>│         │         │         │
   │         │          │           │ notify     │         │         │         │         │
   │         │          │           │───────────────────────────>│         │         │
   │         │          │           │            │  query  │         │         │         │
   │         │          │           │            │<────────────────│         │         │
   │         │          │           │            │  results│         │         │         │
   │         │          │           │            │────────────────>│         │         │
   │         │          │           │            │         │  query  │         │         │
   │         │          │           │            │         │<────────│         │         │
   │         │          │           │            │         │ results │         │         │
   │         │          │           │            │         │────────>│         │         │
   │         │          │           │            │         │         │ hold    │         │
   │         │          │           │            │         │         │ alert   │         │
   │         │          │           │            │         │         │────────>│         │
   │         │          │           │            │         │         │         │ show    │
   │         │          │           │            │         │         │         │ pending │
   │         │          │           │            │         │         │         │────────>│
   │         │          │           │            │         │         │         │         │

  TIMING: Chaos→Webhook: <2s | Ingestion: <30s | Analysis: <30s | Total auto: <60s
```

### 6.2 User Query Processing

```
  User       Dashboard     Athena API     Planner     Researcher    LLM       Responder
    │            │              │             │            │          │           │
    │ NL query   │              │             │            │          │           │
    │───────────>│              │             │            │          │           │
    │            │ POST /query  │             │            │          │           │
    │            │─────────────>│             │            │          │           │
    │            │              │  classify   │            │          │           │
    │            │              │────────────>│            │          │           │
    │            │              │             │ tool calls │          │           │
    │            │              │             │───────────>│          │           │
    │            │              │             │            │ Cypher   │           │
    │            │              │             │            │ + search │           │
    │            │              │             │            │─────────>│           │
    │            │              │             │            │ context  │           │
    │            │              │             │            │<─────────│           │
    │            │              │             │  results   │          │           │
    │            │              │             │<───────────│          │           │
    │            │              │  format     │            │          │           │
    │            │              │─────────────────────────────────>│           │
    │            │              │             │            │          │  cited    │
    │            │              │             │            │          │  response │
    │            │              │<────────────────────────────────────────────── │
    │            │ response     │             │            │          │           │
    │            │<─────────────│             │            │          │           │
    │ display    │              │             │            │          │           │
    │<───────────│              │             │            │          │           │
    │            │              │             │            │          │           │
```

### 6.3 LangGraph Agent State Machine

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
          └──────┬───────┘ └─────┬──────┘       │
                 │               │              │
                 │               ▼              │
                 │         ┌────────────┐       │
                 │         │  ALERTER   │       │
                 │         │            │       │
                 │         │ Tools:     │       │
                 │         │ draft_msg  │       │
                 │         │ classify   │       │
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
                 │  If RISK or  │
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

---

## 7. Security & Performance Considerations

### 7.1 Security Measures

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Data leakage to external APIs | HIGH | Demo mode: fully air-gapped (Ollama). Dev mode: only LLM prompts sent to Gemini/Groq; no project data in prompts |
| LLM hallucination in alerts | HIGH | Citation enforcement — all claims must reference Neo4j/Pinecone data. If no data found: "I don't have this information" |
| Unauthorized chaos injection | MEDIUM | God Mode behind role-based access; chaos API internal-only |
| ATL tampering | MEDIUM | Append-only log design; no UPDATE/DELETE on ATL table |
| Prompt injection via ticket text | MEDIUM | Input sanitization; system prompts with strict boundary instructions |
| API key exposure | MEDIUM | All keys in `.env` (gitignored); `.env.example` with placeholders only |
| Container escape | LOW | Minimal container privileges; no root processes in containers |

### 7.2 Privacy Model

```
  DEV MODE (Cloud LLMs — Gemini + Groq):
  ┌──────────────────────────────────────────────┐
  │           LOCALHOST                           │
  │                                               │
  │  Synthetic Data ──> PostgreSQL ──> Neo4j Aura │
  │       │                              │        │
  │       │              Pinecone <──────┘        │
  │       │                 │                     │
  │       └──> LLMProvider (Gemini / Groq)        │
  │                │                              │
  │                │ HTTPS (prompts only)          │
  │                └──────────────┐               │
  │                               │               │
  │  ✓ Project data stays local   │               │
  │  ✓ Only LLM prompts external  │               │
  │  ✗ NO telemetry or analytics  │               │
  └───────────────────────────────│───────────────┘
                                  ▼
                     ┌──────────────────────┐
                     │ Gemini / Groq Cloud  │
                     └──────────────────────┘

  DEMO MODE (Local LLM — Ollama + Llama 3 8B):
  ┌──────────────────────────────────────────────┐
  │           LOCALHOST                           │
  │                                               │
  │  Synthetic Data ──> PostgreSQL ──> Neo4j      │
  │       │                              │        │
  │       │              ChromaDB <──────┘        │
  │       │                 │                     │
  │       └──> LLMProvider (OllamaProvider)       │
  │                │                              │
  │                └──> Ollama (LOCAL) ──> Resp    │
  │                                               │
  │  ✗ NO external API calls                      │
  │  ✗ NO telemetry or analytics                  │
  │  ✗ NO cloud storage                           │
  │  ✓ ALL processing on localhost                │
  │  ✓ Works with network cable unplugged         │
  └───────────────────────────────────────────────┘
```

### 7.3 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Chat query response (P95) | < 5 seconds | End-to-end from query submission to rendered response |
| Webhook ingestion | < 30 seconds | From HTTP POST receipt to Neo4j + Pinecone upsert |
| Risk detection | < 60 seconds | From chaos event to alert appearing on dashboard |
| System startup | < 3 minutes | `docker-compose up` to all services healthy |
| Dashboard refresh | < 2 seconds | Polling cycle for health metrics |
| Concurrent queries | ≥ 10 | Simultaneous user sessions |

### 7.4 Performance Optimization Techniques

| Technique | Where Applied | Benefit |
|-----------|---------------|---------|
| Connection pooling | PostgreSQL (SQLAlchemy) | Reuse DB connections, avoid overhead |
| FastAPI async handlers | Webhook ingestion | Non-blocking I/O for concurrent events |
| BackgroundTasks | Webhook dispatch after API response | User gets fast response; webhook fire is async |
| Cypher query optimization | Neo4j graph traversal | Indexed lookups on id/key fields |
| Vector index (HNSW) | Pinecone | Sub-second approximate nearest neighbor |
| LLM response caching | Repeated queries | Cache identical query results for TTL |

---

## 8. Technology Stack Selection

### 8.1 Stack Overview

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                    TECHNOLOGY STACK                              │
  ├─────────────────────────────────────────────────────────────────┤
  │                                                                 │
  │  FRONTEND          BACKEND            DATA             INFRA    │
  │  ─────────         ────────            ─────            ─────   │
  │  Next.js 14        FastAPI             Neo4j Aura       Docker  │
  │  React 18          Python 3.11         Pinecone         Compose │
  │  TypeScript        LangGraph           PostgreSQL       Neon    │
  │  Tailwind CSS      APScheduler         (Neon cloud)     (cloud) │
  │                    httpx                                         │
  │                    SQLAlchemy                                    │
  │                    py2neo                                        │
  │                                                                 │
  │  LLM INFERENCE                                                  │
  │  ──────────────                                                 │
  │  Gemini 1.5 Flash (Dev mode — Google AI Studio free tier)       │
  │  Groq Cloud (Fast mode — Llama 3.3 70B for data generation)    │
  │  Ollama + Llama 3 8B Q4 (Demo mode — local GPU, air-gapped)   │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
```

### 8.2 Detailed Stack Table

| Layer | Component | Technology | Version | License | Justification |
|-------|-----------|-----------|---------|---------|---------------|
| Frontend | Framework | Next.js | 14.x | MIT | SSR + API routes, React ecosystem |
| Frontend | Language | TypeScript | 5.x | Apache 2.0 | Type safety for complex UI |
| Backend | REST API | FastAPI | 0.110+ | MIT | Async Python, auto OpenAPI docs |
| Backend | Agent | LangGraph | 0.1+ | MIT | Stateful multi-agent workflows |
| Backend | Scheduler | APScheduler | 3.10+ | MIT | Background chaos event scheduling |
| Backend | HTTP | httpx | 0.27+ | BSD | Async HTTP client for webhooks |
| Backend | ORM | SQLAlchemy | 2.0+ | MIT | Database-agnostic ORM |
| Data | Relational DB | PostgreSQL (Neon) | 16.x | PostgreSQL | Free serverless, zero-ops |
| Data | Graph DB | Neo4j Aura | 5.x | Freemium | Free cloud graph, Cypher queries |
| Data | Vector DB | Pinecone | 3.x | Freemium | Free tier, managed HNSW index |
| Inference | Dev LLM | Gemini 1.5 Flash | latest | Google ToS | 15 RPM free tier, high quality |
| Inference | Fast LLM | Groq Cloud | latest | Groq ToS | Fastest inference for batch data gen |
| Inference | Local LLM | Ollama + Llama 3 8B | 3.0 | Meta License | Air-gapped, privacy-first demos |
| DevOps | Containers | Docker | 24.0+ | Apache 2.0 | Consistent deployment |
| DevOps | Orchestration | Docker Compose | 2.x | Apache 2.0 | Multi-service local orchestration |

### 8.3 Why This Stack (vs. Alternatives)

| Decision | Chosen | Alternative Considered | Reason for Choice |
|----------|--------|----------------------|-------------------|
| Agent framework | LangGraph | AutoGen, CrewAI | LangGraph provides stateful graph-based workflows with checkpointing; others lack fine-grained control |
| Graph DB | Neo4j Aura | Amazon Neptune, ArangoDB | Neo4j Aura has a free tier; Cypher is the most mature graph query language |
| Vector DB | Pinecone | ChromaDB, Weaviate | Pinecone free tier is managed (zero-ops); ChromaDB requires self-hosting |
| Simulator DB | PostgreSQL (Neon) | SQLite | Neon provides cloud persistence, concurrent access, and proper relational features at zero cost |
| LLM (Dev) | Gemini Flash | GPT-4, Claude | Free tier with 15 RPM; sufficient quality for development and testing |
| LLM (Data Gen) | Groq (Llama 3.3 70B) | Gemini only | Groq is 10x faster inference; ideal for batch generating hundreds of tickets |
| Frontend | Next.js 14 | Vite + React, Svelte | SSR, API routes, and mature React ecosystem for complex dashboards |

---

## 9. Scalability & Reliability Planning

### 9.1 Current Deployment Topology

```
+=========================================================================+
|                       docker-compose.yml                                |
+=========================================================================+
|                                                                         |
|  SERVICE           PORT     CLOUD/LOCAL     PROFILE    PERSISTENCE      |
|  ─────────         ─────    ───────────     ────────   ──────────       |
|                                                                         |
|  sim-api           8000     Local           dev,demo   → Neon (cloud)   |
|  sim-chaos         —        Local           dev,demo   —               |
|  athena-core       8001     Local           dev,demo   → Neo4j Aura    |
|                                                        → Pinecone      |
|  neo4j             7474,    Local Docker    demo       neo4j_data/     |
|                    7687     (fallback)                                  |
|  chromadb          8002     Local Docker    demo       chroma_data/    |
|  ollama            11434    Local Docker    demo       ollama_models/  |
|  dashboard         3000     Local           dev,demo   —               |
|                                                                         |
+=========================================================================+

  DEPLOYMENT MODES:
    Dev Mode:   docker compose --profile dev up -d       (cloud DBs + Gemini)
    Demo Mode:  docker compose --profile demo up -d      (local everything)
```

### 9.2 Scalability Strategy

| Dimension | Current (Academic) | Production-Ready Path |
|-----------|-------------------|----------------------|
| **Horizontal Scaling** | Single-instance per service | Kubernetes with replica sets per service |
| **LLM Throughput** | 15 RPM (Gemini free tier) | Upgrade to paid tier or self-hosted vLLM cluster |
| **Database** | Neon free tier (0.5 GB) | Neon Pro or self-hosted PostgreSQL with read replicas |
| **Graph DB** | Neo4j Aura free (50K nodes) | Neo4j AuraDB Professional or self-hosted cluster |
| **Vector DB** | Pinecone free (100K vectors) | Pinecone Standard or self-hosted Qdrant |
| **Caching** | None (direct queries) | Redis layer for repeated queries (TTL-based) |
| **Load Balancing** | N/A (single instance) | Nginx / Traefik reverse proxy with health checks |

### 9.3 Reliability Measures

| Measure | Implementation |
|---------|----------------|
| **Webhook retry** | 3 retries with exponential backoff (1s, 2s, 4s) |
| **Graceful degradation** | If Athena Core is unreachable, webhooks are logged and dropped (simulator doesn't crash) |
| **Event deduplication** | `event_id` uniqueness check prevents duplicate processing |
| **LLM fallback chain** | Groq → Gemini → Ollama (if primary fails, fall to next) |
| **Idempotent operations** | Graph Syncer uses UPSERT (MERGE in Cypher) — safe to replay events |
| **Container restart policy** | `restart: always` on all Docker services |
| **Data persistence** | Named Docker volumes for Neo4j, ChromaDB, Ollama models |
| **Health checks** | `/api/v1/health` endpoint on all API services |

### 9.4 Uptime & Recovery

| Scenario | Recovery Strategy | RTO |
|----------|------------------|-----|
| Service crash | Docker `restart: always` auto-restarts | < 30 seconds |
| Database connection lost | SQLAlchemy `pool_pre_ping=True` auto-reconnects | < 5 seconds |
| LLM API rate limit | Fallback to alternate provider in LLMProvider chain | Immediate |
| Full system restart | `docker-compose up -d` restores all services | < 3 minutes |
| Neo4j Aura outage | Fall back to local Neo4j Docker container (demo profile) | < 2 minutes |

---

## 10. Conclusion

Project Athena demonstrates a production-grade system design for an autonomous multi-agent AI system applied to program management. The key architectural contributions are:

1. **Dual-Architecture Separation** — The Project Universe simulator and Athena Core are completely decoupled, communicating only via webhooks. This design allows Athena Core to connect to real enterprise tools (Jira, Azure DevOps) with zero changes to its core logic.

2. **Triple-Mode LLM Strategy** — The `LLMProvider` abstraction supports three backends (Gemini for development, Groq for fast data generation, Ollama for air-gapped demos), making the system portable across environments from cloud to fully offline.

3. **GraphRAG Knowledge Architecture** — By combining Neo4j's structured graph traversal with Pinecone's semantic vector search, the system achieves relationship-aware, citation-grounded responses that eliminate LLM hallucination.

4. **Human-in-the-Loop Governance** — The Human Gate node in the LangGraph state machine ensures no autonomous action is taken without explicit human approval, addressing a critical enterprise requirement for AI trust and auditability.

5. **Event-Driven Reactive Architecture** — The webhook-driven pipeline enables sub-60-second detection of risks from the moment a chaos event occurs to the alert appearing on the dashboard.

The system is designed for academic demonstration while maintaining architectural patterns that scale to enterprise deployment through the scalability and reliability strategies outlined in Section 9.

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-02-05 | Team Athena | Initial architecture definition |
| 0.2.0 | 2026-02-19 | Team Athena | Comprehensive architecture with C4 diagrams, API contracts, sequence diagrams, agent state machine, deployment topology, security model |
| 0.2.1 | 2026-02-20 | Team Athena | Updated for dual-mode LLM (Gemini + Ollama) |
| 0.3.0 | 2026-03-03 | Team Athena | Restructured to 10-section academic System Design format with ER diagrams, class diagrams, UI wireframes, scalability planning |
