# System Design
**(Project Proposal Review and Detailed Design Finalization)**

**Document ID:** Athena_HLD_System-Architecture_v0.4.0  
**Project:** Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation  
**Date:** 2026-03-17  
**Version:** 0.4.0

> **Design Approach:** Object-Oriented (UML-based), as recommended for Python-based systems. All architectural, structural, and behavioral diagrams use UML notation. The primary structural diagram is the **Class Diagram** and the primary behavioral diagram is the **Sequence Diagram**.

---

## 1. Introduction to the System

Project Athena is an AI-powered, autonomous Program Management Office (PMO) assistant. It continuously ingests enterprise project data via webhooks, synthesizes it into a unified Knowledge Graph and Vector Store (GraphRAG), and proactively detects risks before they escalate — notifying stakeholders via a real-time dashboard with human-in-the-loop approval. The system replaces the 10–15 hours/week that Program Managers spend manually aggregating data from tools like Jira, Azure DevOps, and Confluence, enabling sub-60-second automated risk detection compared to the current 2–3 day manual lag.

### 1.1 Background and Motivation

- **The PMO Pain Point:** In large-scale software enterprises, a Program Management Office oversees multiple parallel projects. Each generates data across disparate tools — tickets, sprints, bugs, pipelines, incidents. Program Managers must manually log into each tool, extract data, cross-reference it, and compile unified status reports. This process is inherently reactive: risks are discovered only after they have already escalated.

- **Role of Agentic AI and Multi-Agent Systems:** The rise of Agentic AI (2024–2026) has created a new category of AI systems that go beyond passive question-answering. AI Agents can autonomously observe data, reason about relationships, detect anomalies, and take actions — making them ideal for the continuous monitoring and proactive alerting that manual PMO workflows cannot achieve. Athena leverages this paradigm by combining LangGraph multi-agent orchestration, GraphRAG knowledge synthesis (Neo4j + Pinecone), and a triple-mode LLM architecture (Gemini, Groq, Ollama) to create an intelligent system that watches, reasons, and acts.

- **Role of Dual-Architecture Design:** Since students cannot access real corporate Jira/Azure DevOps data, Athena introduces a "Project Universe" — a high-fidelity enterprise simulator that generates realistic PM events, complete with a Chaos Engine that injects real-world failures (blocked tickets, overloaded developers, delayed milestones). This simulator-and-agent architecture ensures the agent core is production-portable: it could connect to real enterprise APIs without any code changes.

### 1.2 Objectives of the System

| # | Objective | SRS Trace |
|---|-----------|-----------|
| 1 | **Enterprise Simulation:** Build a live enterprise simulator with Mock Jira API, Chaos Engine, and Webhook Dispatcher to generate realistic project events | FR-01, FR-02 |
| 2 | **GraphRAG Knowledge Synthesis:** Ingest webhook events into a dual-store architecture (Neo4j knowledge graph + Pinecone vector store) for relationship-aware, citation-grounded reasoning | FR-03, FR-04 |
| 3 | **Multi-Agent Reasoning:** Implement a 6-node LangGraph state machine (Planner, Researcher, Alerter, Responder, Human Gate, Executor) for autonomous risk detection and query answering | FR-05, FR-06 |
| 4 | **Triple-Mode LLM:** Support Gemini (dev), Groq (fast data-gen), and Ollama (air-gapped demo) through a pluggable `LLMProvider` abstraction | FR-07, NFR-01 |
| 5 | **Real-Time Dashboard:** Build a Next.js 14 dashboard with Chat UI, Health Dashboard (RAG indicators), and God Mode Console for live demo | FR-08, FR-09 |

### 1.3 Scope of the System

| In Scope | Out of Scope |
|----------|-------------|
| Synthetic enterprise data generation using AI (Groq + Gemini) | Real Jira/Azure DevOps API integration |
| Real-time webhook-driven event processing | Email/SMS/Slack notification delivery |
| Knowledge graph construction and semantic search | Natural language to Jira ticket creation |
| Autonomous risk detection and alert drafting | Automated project scheduling or resource allocation |
| Human-in-the-loop approval for sensitive actions | Autonomous execution without human oversight |
| Air-gapped (offline) deployment mode | Multi-tenant enterprise deployment |

### 1.4 System Overview

The system follows a **Dual-Architecture** design:

1. **Project Universe (Simulator)** generates realistic enterprise PM events via a Mock Jira API, periodically injects failures through a Chaos Engine, and fires Jira-compatible webhooks on every data mutation.

2. **Athena Core (Agent)** receives webhooks, processes them through an Ingestion Pipeline that syncs data to Neo4j (structured graph) and Pinecone (semantic vectors), and routes risk events to a LangGraph Agent Brain that analyzes, drafts alerts, and holds them for human approval.

3. **Dashboard (Presentation)** provides a Next.js 14 frontend with Chat Interface (NL queries with cited responses), Health Dashboard (RAG status indicators), and God Mode Console (chaos injection for live demos).

**Refer to:** *System Context Diagram* (Athena_HLD_v0.3.0, Section 1.3) — shows the three-tier context of Human Users ↔ Athena System ↔ Project Universe.

---

## 2. Architectural Design

### 2.1 System Architecture Overview

Athena employs a **Layered Microservices Architecture** with four distinct tiers orchestrated via Docker Compose.

**Refer to:** *Layered Microservices Architecture Diagram* (Athena_HLD_v0.3.0, Section 2.1) — shows the four layers: Presentation, Application, Data, and Inference.

The four layers are:

| Layer | Services | Responsibility |
|-------|----------|----------------|
| **Presentation** | Next.js Dashboard (:3000) | Chat UI, Health Dashboard, God Mode Console |
| **Application** | Jira-Sim API (:8000), Athena Core (:8001), Chaos Engine | Business logic, webhook processing, agent orchestration |
| **Data** | PostgreSQL (Neon), Neo4j Aura, Pinecone | Persistent storage — relational, graph, and vector |
| **Inference** | LLMProvider → Gemini / Groq / Ollama | Language model inference for reasoning and data generation |

### 2.2 Architectural Pattern Selection

#### 2.2.1 Microservices Architecture

Each major system function is deployed as an independent service communicating over HTTP. The Simulator API, Athena Core API, and Dashboard are separate FastAPI / Next.js applications. This enables independent development, testing, and deployment of each tier. For example, the Simulator can run standalone to generate data without Athena Core being online, and Athena Core can process historical events without the Dashboard.

#### 2.2.2 Event-Driven Architecture

Inter-system communication is achieved through **webhooks** (HTTP POST events) rather than synchronous RPC or polling. When any entity changes state in the Simulator (ticket created, status updated, priority escalated), a Jira-compatible webhook event is immediately dispatched to Athena Core's ingestion endpoint. This mirrors how real enterprise tools (Jira Cloud, GitHub) notify external systems, making the architecture production-portable.

### 2.3 System Layers

#### 2.3.1 Data Acquisition Layer (Project Universe Simulator)

The Data Acquisition Layer is the **Project Universe** — a complete enterprise simulator built from scratch using FastAPI. It consists of:

- **Mock Jira API** (FastAPI, Port 8000): A REST API that replicates Jira's real interface with CRUD operations and **10 Jira-compatible query endpoints** modeled after a production Jira integration. The API surface matches the function signatures used by real enterprise AI agents querying Jira, ensuring production portability. Data is stored in PostgreSQL (Neon serverless) with 8 ORM models managed by SQLAlchemy.

**Jira-Compatible Query Endpoints (from Production TOOL_CONFIG):**

| # | Endpoint | Method | Parameters | Description | Maps to TOOL_CONFIG |
|---|----------|--------|------------|-------------|--------------------|
| 1 | `/api/v1/issues/{issue_key}` | GET | `issue_key` (required) | Get detailed information about a specific issue by its key (e.g., PROJ-123) | `get_jira_issue` |
| 2 | `/api/v1/issues/search` | GET | `jql` (required), `analyze_by_component` (required) | Search issues using JQL query language; optionally returns component breakdown | `search_jira_issues` |
| 3 | `/api/v1/projects/{project_key}/issues` | GET | `project_key` (required), `status` (optional) | Get all issues for a project with optional status filter | `get_project_issues` |
| 4 | `/api/v1/users/{username}/issues` | GET | `username` (optional, defaults to currentUser) | Get issues assigned to a specific user | `get_user_issues` |
| 5 | `/api/v1/sprints/issues` | GET | `sprint_name` (optional, defaults to active sprint) | Get all issues in a sprint | `get_sprint_issues` |
| 6 | `/api/v1/issues/{issue_key}/comments` | GET | `issue_key` (required) | Get all comments for a specific issue | `get_issue_comments` |
| 7 | `/api/v1/issues/{issue_key}/transitions` | GET | `issue_key` (required) | Get available status transitions for an issue (e.g., OPEN→IN_PROGRESS→BLOCKED) | `get_issue_transitions` |
| 8 | `/api/v1/issues/{issue_key}/attachments` | GET | `issue_key` (required) | Get attachments metadata for an issue | `get_issue_attachments` |
| 9 | `/api/v1/projects/{project_key}/summary` | GET | `project_key` (required) | Get project summary with issue counts by status (OPEN, IN_PROGRESS, BLOCKED, CLOSED) | `get_project_summary` |
| 10 | `/api/v1/issues/{issue_key}/logs` | GET | `issue_key` (required) | Download attachments and audit logs from an issue | `download_issue_logs` |

> **Note:** This TOOL_CONFIG is derived from a live production Jira integration used by an enterprise AI agent. By implementing identical function signatures in the Simulator, Athena's agent tools work identically against both the Simulator and a real Jira instance — enabling zero-change production migration.

**Additional Simulator Components:**

- **AI Data Generator** (`data_gen.py`): Uses a dual-LLM approach — **Groq (Llama 3.3 70B)** for fast batch generation and **Gemini 1.5 Flash** as fallback — to create hyper-realistic enterprise data. Generates diverse user profiles, project hierarchies, epic/story structures, and contextual comments that are indistinguishable from real enterprise data.

- **Timeline Simulator** (`timeline_sim.py`): Generates 12 months of historical project data by AI-batch creating 20–50 stories per sprint across multiple projects, then replays historical events via webhooks to build the knowledge graph retroactively.

- **Chaos Engine** (`chaos_engine.py`): A scheduled background process (APScheduler) that periodically injects realistic failures — ticket blockers, developer overloads, and priority escalations — with LLM-generated contextual comments to make the failures indistinguishable from real incidents.

- **Webhook Dispatcher** (`webhook.py`): Fires Jira-compatible HTTP POST webhooks to Athena Core on every data mutation. Supports both real-time dispatch and historical event replay for retroactive knowledge graph construction.

**SRS Trace:** FR-01 (Enterprise Simulation), FR-02 (Chaos Injection)

#### 2.3.2 Data Processing Layer (Ingestion Pipeline)

The Data Processing Layer sits inside Athena Core and is responsible for:

- **Validation:** Incoming webhook events are validated against a JSON schema to ensure required fields (event_id, event_type, entity_type, entity_id, timestamp) are present and correctly typed. Invalid events return HTTP 400 and are logged.

- **Deduplication:** Each event's `event_id` (UUID v4) is checked against a processed-events set. Duplicate events return HTTP 200 and are skipped, ensuring idempotent processing.

- **Routing:** Valid, deduplicated events are routed based on `entity_type` to two parallel processors — the Graph Syncer (Neo4j) and the Vector Indexer (Pinecone).

- **Notification:** If the event is risk-related (status change to BLOCKED, priority escalation to CRITICAL, developer overload), the Agent Brain is notified to trigger autonomous risk analysis.

**SRS Trace:** FR-03 (Data Ingestion)

#### 2.3.3 AI Analytics Layer (Agent Brain)

The AI Analytics Layer is the intelligence core where Athena reasons about project state. It consists of:

- **LangGraph State Machine:** A 6-node directed graph that processes inputs (user queries or risk events) through specialized agents: Planner (classify intent), Researcher (query Neo4j + Pinecone + Jira), Alerter (draft communications), Responder (format cited responses), Human Gate (await approval), and Executor (execute + log).

- **Agent Tools (15 total):** The agent has access to two categories of tools:

  **Jira Integration Tools (10)** — modeled after a production Jira TOOL_CONFIG, these tools call the Simulator's Jira-compatible API:

  | # | Tool Function | Parameters | Description |
  |---|---------------|------------|-------------|
  | 1 | `get_jira_issue(issue_key)` | `issue_key`: str (required) | Get detailed information about a specific issue by its key |
  | 2 | `search_jira_issues(jql, analyze_by_component)` | `jql`: str (required), `analyze_by_component`: bool (required) | Search issues using JQL; optionally with component breakdown |
  | 3 | `get_project_issues(project_key, status)` | `project_key`: str (required), `status`: str (optional) | Get all issues for a project with optional status filter |
  | 4 | `get_user_issues(username)` | `username`: str (optional) | Get issues assigned to a user |
  | 5 | `get_sprint_issues(sprint_name)` | `sprint_name`: str (optional) | Get issues in a sprint |
  | 6 | `get_issue_comments(issue_key)` | `issue_key`: str (required) | Get all comments for an issue |
  | 7 | `get_issue_transitions(issue_key)` | `issue_key`: str (required) | Get available status transitions for an issue |
  | 8 | `get_issue_attachments(issue_key)` | `issue_key`: str (required) | Get attachments for an issue |
  | 9 | `get_project_summary(project_key)` | `project_key`: str (required) | Get project summary with issue counts by status |
  | 10 | `download_issue_logs(issue_key)` | `issue_key`: str (required) | Download attachments and logs from an issue |

  **Internal Knowledge Tools (5)** — direct access to Athena's knowledge stores and internal functions:

  | # | Tool Function | Parameters | Description |
  |---|---------------|------------|-------------|
  | 11 | `search_graph(query)` | `query`: str | Execute Cypher queries on Neo4j knowledge graph |
  | 12 | `search_docs(text, k)` | `text`: str, `k`: int | Semantic similarity search on Pinecone vector store |
  | 13 | `draft_message(ctx, tpl)` | `ctx`: dict, `tpl`: str | LLM-generated alert/communication draft |
  | 14 | `classify_severity(risk)` | `risk`: dict | Classify risk severity (LOW/MEDIUM/HIGH/CRITICAL) |
  | 15 | `log_action(entry)` | `entry`: dict | Append to ATL (Action & Tracking Log) |

- **LLM Inference:** All reasoning and generation is delegated to the `LLMProvider` abstraction, which routes to Gemini (dev), Groq (fast), or Ollama (air-gapped) based on configuration.

**SRS Trace:** FR-05 (Multi-Agent Reasoning), FR-06 (Risk Detection), FR-07 (LLM Abstraction)

#### 2.3.4 Application Layer (Dashboard)

The Application Layer is the **Next.js 14 Dashboard** that serves as the primary user interface:

- **Chat Interface:** Users submit natural language queries ("What is the status of Project Alpha?") and receive grounded, citation-backed responses with confidence scores. Multi-turn conversation history is maintained.

- **Health Dashboard:** Displays real-time RAG (Red/Amber/Green) indicators for program health, milestone progress, blocked ticket counts, and overloaded developer alerts. Updates via REST polling every 5 seconds.

- **God Mode Console:** A demo-specific panel that allows evaluators to manually trigger chaos events (select chaos type → inject → observe Athena detect and respond in real-time). This demonstrates the full event→detection→alert pipeline live.

**SRS Trace:** FR-08 (Dashboard), FR-09 (Chat Interface)

#### 2.3.5 Storage Layer

Athena uses three complementary storage systems, each optimized for a specific query pattern:

| Storage | Technology | Data Type | Query Pattern | SRS Trace |
|---------|------------|-----------|---------------|-----------|
| **Relational DB** | PostgreSQL (Neon serverless) | Simulator entities (users, projects, tickets, sprints, comments) | CRUD operations, joins, audit queries | FR-01 |
| **Knowledge Graph** | Neo4j Aura (cloud free tier) | Entity relationships (ASSIGNED_TO, BLOCKS, DEPENDS_ON, HAS_RISK, IMPACTS) | Cypher graph traversal, multi-hop path queries, pattern matching | FR-04 |
| **Vector Store** | Pinecone (cloud free tier) | Text embeddings of ticket descriptions, comments, risk summaries | Semantic similarity search (top-K approximate nearest neighbors) | FR-04 |

### 2.4 Module Interaction and Communication

**Refer to:** *Inter-Module Communication Diagram* (Athena_HLD_v0.3.0, Section 2.3) — shows data exchange patterns across all modules.

| Communication Path | Protocol | Format | Direction |
|-------------------|----------|--------|-----------|
| Dashboard ↔ Athena Core | HTTP / WebSocket | JSON | Bidirectional |
| Simulator → Athena Core | HTTP POST (webhook) | Jira-compatible JSON | One-way push |
| Athena Core → Simulator API | HTTP REST (Jira tools) | JSON (10 TOOL_CONFIG endpoints) | Request-response |
| Athena Core → Neo4j Aura | Bolt protocol | Cypher queries | Bidirectional |
| Athena Core → Pinecone | HTTPS REST API | JSON (embeddings + metadata) | Bidirectional |
| Athena Core → LLM | HTTPS (cloud) / HTTP (local) | JSON prompt → text response | Request-response |
| Chaos Engine → Simulator API | HTTP REST | JSON CRUD mutations | One-way |

**API Communication Mechanisms:**

- **Webhook Events:** The Simulator fires webhooks using `httpx` async HTTP client. Events follow a Jira-compatible schema with `event_id`, `event_type`, `entity_type`, `changed_fields`, and `timestamp`. Connection failures are gracefully handled (logged and dropped; simulator doesn't crash).

- **REST APIs:** Both Simulator and Athena Core expose OpenAPI-documented REST endpoints via FastAPI. The dashboard communicates with Athena Core via standard REST with JSON payloads.

- **Graph Protocol:** Neo4j Aura is accessed via the Bolt protocol through the `py2neo` library. All graph operations use Cypher queries with parameterized inputs to prevent injection.

---

## 3. Data Flow and Process Modeling

> **Note:** Following the Object-Oriented approach, data flow is modeled using UML Activity Diagrams. Database design is modeled using UML Class Diagrams (see Section 5).

### 3.1 System Context — Activity Diagram (Level 0)

This diagram shows the overall interaction between Athena and its external actors.

**Refer to:** *Level 0 Context DFD* (Athena_HLD_v0.3.0, Section 3.1) — shows the three external entities (Project Universe, Athena System, Users) and data flows between them.

**External Actors and Data Flows:**

| External Actor | Data Into Athena | Data Out of Athena |
|----------------|------------------|--------------------|
| **Project Universe (Simulator)** | Webhook events (ticket created, updated, blocked, escalated) | God Mode commands (chaos injection triggers) |
| **PMO Leader / Program Manager** | Natural language queries via Chat UI | Cited responses, risk alerts, RAG health indicators |
| **Scrum Master** | Workload queries, sprint health checks | Developer load analysis, sprint status |
| **Evaluator (Demo)** | Chaos injection via God Mode Console | Real-time event→detection→alert demonstration |

### 3.2 System Process Flow — Activity Diagram (Level 1)

This diagram shows the internal modules and how data flows between them.

**Refer to:** *Level 1 System Activity Diagram* (Athena_HLD_v0.3.0, Section 3.2) — shows the Ingestion Pipeline (1.0) feeding into Neo4j (D1) and Pinecone (D2), which feed the Agent Brain (2.0) that produces Cited Responses and ATL entries (D3).

**Module Descriptions:**

| Module | Input | Processing | Output |
|--------|-------|------------|--------|
| **Ingestion Pipeline** | Webhook JSON event | Validate schema → Deduplicate by event_id → Route by entity_type | Graph upsert commands, vector embeddings |
| **Graph Syncer** | Entity data from webhook | MERGE (upsert) nodes and relationships in Neo4j using Cypher | Updated knowledge graph |
| **Vector Indexer** | Text fields (title, description, comments) | Generate embeddings via LLM → Upsert to Pinecone with metadata | Updated vector index |
| **Agent Brain** | User query OR risk event notification | Classify → Research (graph + vector) → Alert/Respond → Human Gate → Execute | Cited response, ATL log entry |
| **Dashboard** | Metrics API responses, query responses | Render health indicators, chat messages, alert cards | User-facing UI |

### 3.3 Ingestion Pipeline Detail — Activity Diagram (Level 2)

**Refer to:** *Level 2 Ingestion Pipeline Diagram* (Athena_HLD_v0.3.0, Section 3.3) — shows the 4-step flow: Validate → Deduplicate → Route → (Graph Syncer + Vector Indexer in parallel) → Notify Agent Brain.

### 3.4 Database Design

#### 3.4.1 Relational Database Schema (PostgreSQL — Simulator)

The simulator's relational database stores all enterprise entities using SQLAlchemy ORM. The schema consists of 8 entities:

**Main Entities:**

| Entity | Purpose | Key Attributes | SRS Trace |
|--------|---------|----------------|-----------|
| **User** | Developer, PM, QA, VP profiles | id, email, name, role, department, team_id, timezone | FR-01 |
| **Team** | Organizational units | id, name, lead_id (FK → User) | FR-01 |
| **Project** | Enterprise projects | id, key, name, description, lead_id (FK → User) | FR-01 |
| **Sprint** | Time-boxed iterations | id, project_id, name, state (PLANNED/ACTIVE/CLOSED), start_date, end_date | FR-01 |
| **Epic** | Feature-level grouping | id, key, project_id, title, description, status, priority, reporter_id | FR-01 |
| **Story** | Work items (tickets) | id, key, epic_id, sprint_id, title, status, priority, story_points, assignee_id, reporter_id | FR-01 |
| **Comment** | Discussion on stories | id, story_id, author_id, body, created_at | FR-01 |
| **AuditLog** | Change tracking | id, entity_type, entity_id, action, details (JSON), timestamp | FR-01, FR-06 |

#### 3.4.2 Table Structure

**User Table:**

| Column | Type | Constraints |
|--------|------|-------------|
| id | String (UUID) | PRIMARY KEY |
| email | String | UNIQUE, NOT NULL |
| name | String | NOT NULL |
| role | String | NOT NULL (developer/pm/qa/lead/vp) |
| department | String | — |
| team_id | String (UUID) | FOREIGN KEY → Team.id |
| timezone | String | — |
| created_at | DateTime | DEFAULT NOW() |

**Story Table:**

| Column | Type | Constraints |
|--------|------|-------------|
| id | String (UUID) | PRIMARY KEY |
| key | String | UNIQUE, NOT NULL |
| epic_id | String (UUID) | FOREIGN KEY → Epic.id |
| sprint_id | String (UUID) | FOREIGN KEY → Sprint.id |
| title | String | NOT NULL |
| description | Text | — |
| status | String | NOT NULL (OPEN/IN_PROGRESS/BLOCKED/CLOSED) |
| priority | String | NOT NULL (LOW/MEDIUM/HIGH/CRITICAL) |
| story_points | Integer | — |
| reporter_id | String (UUID) | FOREIGN KEY → User.id |
| assignee_id | String (UUID) | FOREIGN KEY → User.id |
| created_at | DateTime | DEFAULT NOW() |
| updated_at | DateTime | ON UPDATE NOW() |
| resolution | DateTime | NULLABLE |

**AuditLog Table:**

| Column | Type | Constraints |
|--------|------|-------------|
| id | String (UUID) | PRIMARY KEY |
| entity_type | String | NOT NULL (user/team/project/sprint/epic/story/comment) |
| entity_id | String (UUID) | NOT NULL |
| action | String | NOT NULL (CREATE/UPDATE/DELETE) |
| details | JSON | Changed fields with old/new values |
| timestamp | DateTime | DEFAULT NOW() |

#### 3.4.3 Data Model Relationship Diagram

**Refer to:** *ER Diagram* (Athena_HLD_v0.3.0, Section 3.4) — shows the 8-entity relationship diagram with foreign key connections (Team→User, User→Project, Project→Sprint, Project→Epic, Epic→Story, Story→Comment, User→Story assignments).

**Refer to:** *Knowledge Graph Schema Diagram* (Athena_HLD_v0.3.0, Section 3.5) — shows the Neo4j graph schema with 7 node types (Project, Epic, Task, User, Risk, Milestone, Sprint) and 8 relationship types (ASSIGNED_TO, BLOCKS, DEPENDS_ON, PART_OF, BELONGS_TO, HAS_RISK, IMPACTS, OWNS).

---

## 4. User Interface (UI) Design

### 4.1 UI Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Simplicity** | Clean, information-dense layout without visual clutter; RAG indicators use intuitive color coding |
| **Real-Time Feedback** | Health metrics poll every 5 seconds; chat responses stream tokens as they are generated |
| **Actionability** | Every risk alert includes Approve/Reject/Modify buttons — users act directly from the alert card |
| **Citation Transparency** | Every Athena response displays cited ticket/entity IDs so users can verify claims against ground truth |
| **Confidence Display** | Responses show a confidence score (0–100%) so users can gauge reliability |

### 4.2 User Roles

| Role | Access Level | Primary Use | Example Query |
|------|-------------|-------------|---------------|
| **PMO Leader / VP** | Full read, approval authority | Executive summary of all programs | "Give me a health summary of all active projects" |
| **Program Manager** | Full read, approval authority | Monitor project risks and blockers | "Which tickets are blocking the March milestone?" |
| **Scrum Master** | Team-scoped read, approval authority | Track team workload and sprint health | "Is any developer overloaded with critical tasks?" |
| **System Administrator** | Full access + God Mode | System configuration, demo control | Chaos injection, system health monitoring |

### 4.3 UI Wireframes / Mockups

**Refer to:** *Dashboard Wireframe* (Athena_HLD_v0.3.0, Section 4.1) — shows the complete dashboard layout with Health Panel (top), Risk Feed (left 60%), Chat Interface (right 40%), ATL Viewer (bottom-left), and God Mode Console (collapsible bottom).

**Key Screens:**

1. **Main Dashboard** — Health Bar showing overall RAG status, risk counts, blocked counts, sprint progress, and overloaded developer count. Below: Risk Feed with pending alerts on the left, Chat Panel on the right.

2. **Chat Interface** — Multi-turn conversational interface where users type NL queries and receive cited responses with confidence scores. Message history persists per session.

3. **God Mode Console** — Collapsible panel at the bottom with a dropdown to select chaos type (Ticket Blocker, Developer Overload, Priority Escalation) and an "INJECT CHAOS" button. Displays real-time event log of chaos injections and Athena's responses.

### 4.4 User Experience (UX) Considerations

- **Navigation:** Single-page application — Health Bar visible at all times; Risk Feed and Chat Panel side-by-side; God Mode togglable
- **Mobile Compatibility:** Responsive layout; Chat Panel takes full width on mobile; Health Bar stacks vertically
- **Real-Time Alerts:** Browser notification API for critical alerts when dashboard tab is not in focus
- **Loading States:** Skeleton screens during API calls; streaming tokens for AI responses
- **Error Handling:** User-friendly error messages (no raw stack traces); automatic retry for transient failures

### Component Design

### 4.5 Front-End Components

| Component | Type | Description | SRS Trace |
|-----------|------|-------------|-----------|
| `<HealthBar />` | Display | Top-level RAG health indicators with color-coded status badges | FR-08 |
| `<RiskFeed />` | Interactive | Scrollable list of pending risk alerts with Approve/Reject/Modify actions | FR-06, FR-08 |
| `<ChatPanel />` | Interactive | Multi-turn NL chat with streaming responses, citations, and confidence | FR-09 |
| `<ATLViewer />` | Display | Chronological audit trail of all agent decisions with timestamps | FR-06 |
| `<GodModeConsole />` | Interactive | Chaos type selector + injection button + real-time event log | FR-02 |
| `<ApprovalCard />` | Interactive | Individual alert card with full context, severity badge, and action buttons | FR-06 |

### 4.6 Back-End Integration

| Frontend Component | API Endpoint | Method | Polling/Push |
|-------------------|-------------|--------|--------------|
| `<HealthBar />` | `/api/v1/metrics` | GET | Poll (5s interval) |
| `<RiskFeed />` | `/api/v1/risks/active` | GET | Poll (5s interval) |
| `<ChatPanel />` | `/api/v1/query` | POST | One-shot per query |
| `<ATLViewer />` | `/api/v1/atl` | GET | Poll (10s interval) |
| `<ApprovalCard />` | `/api/v1/approval/{id}` | POST | One-shot per action |
| `<GodModeConsole />` | Simulator `/api/v1/chaos/trigger` | POST | One-shot per injection |

### 4.7 Input and Output Definition

| Component | Input | Output |
|-----------|-------|--------|
| **Simulator API** | CRUD request (JSON) | Entity response + webhook event fired |
| **Chaos Engine** | Scheduled trigger OR manual injection | Ticket mutation + LLM-generated comment |
| **Ingestion Pipeline** | Webhook JSON event | Neo4j upsert + Pinecone embedding |
| **Agent Brain** | NL query OR risk notification | Cited response with confidence + ATL entry |
| **Health Dashboard** | Metrics API response | RAG indicators + counts |
| **Chat Interface** | User text query | AI response with citations |

### 4.8 User Feedback and Accessibility

- **Approval Feedback:** After approving/rejecting an alert, the UI shows a confirmation toast with the decision and timestamp
- **Health Alerts:** Critical risks trigger browser notifications with sound; amber risks show banner alerts
- **Confidence Indicator:** Every AI response displays a progress bar (0–100%) so users understand reliability
- **Data Freshness:** Timestamps on all displayed data indicate when it was last updated
- **Accessibility:** All interactive elements have unique IDs for automated testing; RAG colors meet WCAG 2.1 contrast ratios; keyboard navigation supported (Enter to send, Tab to navigate)

---

## 5. Class Diagram and Classes

> **Approach:** Object-Oriented UML Class Diagrams are used to model both the data layer (ORM models) and the agent layer (LLMProvider hierarchy, AgentState, AgentBrain).

### 5.1 Major Classes

| Class | Package | Purpose |
|-------|---------|---------|
| `User` | `simulator.database` | Developer/PM/QA/VP entity with team assignment |
| `Team` | `simulator.database` | Organizational unit with a team lead |
| `Project` | `simulator.database` | Enterprise project with a project lead |
| `Sprint` | `simulator.database` | Time-boxed iteration within a project |
| `Epic` | `simulator.database` | Feature-level grouping within a project |
| `Story` | `simulator.database` | Individual work item (ticket) with assignment |
| `Comment` | `simulator.database` | Discussion on a story |
| `AuditLog` | `simulator.database` | Change tracking with JSON details |
| `LLMProvider` | `athena_core.llm` | Abstract base class for LLM inference |
| `GeminiProvider` | `athena_core.llm` | Gemini 1.5 Flash implementation |
| `GroqProvider` | `athena_core.llm` | Groq (Llama 3.3 70B) implementation |
| `OllamaProvider` | `athena_core.llm` | Ollama (Llama 3 8B local) implementation |
| `AgentState` | `athena_core.agent` | TypedDict holding session state across agent nodes |
| `AgentBrain` | `athena_core.agent` | LangGraph orchestrator with 6 agent nodes and tool functions |

### 5.2 Class Attributes and Methods

**User Class:**

| Attribute | Type | Description |
|-----------|------|-------------|
| id | String (UUID) | Primary key |
| email | String | Unique email |
| name | String | Display name |
| role | String | developer / pm / qa / lead / vp |
| department | String | Engineering / QA / Management |
| team_id | FK → Team | Team membership |
| timezone | String | User timezone |
| created_at | DateTime | Account creation timestamp |

Methods:
- `to_dict()` → dict: Serialize to JSON-compatible dictionary
- Relationship: `team` → Team (Many-to-One)

**Story Class:**

| Attribute | Type | Description |
|-----------|------|-------------|
| id | String (UUID) | Primary key |
| key | String | Human-readable key (e.g., PROJ-123) |
| epic_id | FK → Epic | Parent epic |
| sprint_id | FK → Sprint | Current sprint |
| title | String | Story title |
| description | Text | Full description |
| status | String | OPEN / IN_PROGRESS / BLOCKED / CLOSED |
| priority | String | LOW / MEDIUM / HIGH / CRITICAL |
| story_points | Integer | Effort estimate |
| reporter_id | FK → User | Who created it |
| assignee_id | FK → User | Who is working on it |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last modification |
| resolution | DateTime | When resolved (nullable) |

Methods:
- `to_dict()` → dict: Serialize to JSON-compatible dictionary
- Relationships: `epic` → Epic, `sprint` → Sprint, `reporter` → User, `assignee` → User, `comments` → List[Comment]

**LLMProvider Class (Abstract):**

| Method | Signature | Description |
|--------|-----------|-------------|
| `generate` | `(prompt: str) → str` | Generate text completion from prompt |
| `embed` | `(text: str) → list[float]` | Generate embedding vector for text |

Subclasses: `GeminiProvider(api_key, model)`, `GroqProvider(api_key, model)`, `OllamaProvider(base_url, model)`

**AgentBrain Class:**

| Attribute | Type | Description |
|-----------|------|-------------|
| state | AgentState | Current session state (TypedDict) |
| llm | LLMProvider | Active LLM backend |
| graph_client | Neo4jClient | Neo4j Aura connection |
| vector_client | PineconeClient | Pinecone connection |
| jira_client | JiraSimClient | Simulator API connection (Jira-compatible) |

| Method | Signature | Description |
|--------|-----------|-------------|
| `planner` | `(state) → AgentState` | Classify input type (query/risk/general) |
| `researcher` | `(state) → AgentState` | Query Jira + graph + vector stores |
| `alerter` | `(state) → AgentState` | Draft risk alert with severity |
| `responder` | `(state) → AgentState` | Format cited response |
| `human_gate` | `(state) → AgentState` | Pause for approval if risk/action |
| `executor` | `(state) → AgentState` | Execute approved action + log to ATL |

Jira Integration Tools (10): `get_jira_issue(issue_key)`, `search_jira_issues(jql, analyze_by_component)`, `get_project_issues(project_key, status?)`, `get_user_issues(username?)`, `get_sprint_issues(sprint_name?)`, `get_issue_comments(issue_key)`, `get_issue_transitions(issue_key)`, `get_issue_attachments(issue_key)`, `get_project_summary(project_key)`, `download_issue_logs(issue_key)`

Internal Knowledge Tools (5): `search_graph(query)`, `search_docs(text, k)`, `draft_message(ctx, tpl)`, `classify_severity(risk)`, `log_action(entry)`

### 5.3 UML Class Diagrams

**Refer to:** *ORM Class Diagram* (Athena_HLD_v0.3.0, Section 5.1) — shows the 8 SQLAlchemy model classes with attributes, types, and FK relationships.

**Refer to:** *Agent Architecture Class Diagram* (Athena_HLD_v0.3.0, Section 5.2) — shows the LLMProvider abstract class with 3 concrete implementations (GeminiProvider, GroqProvider, OllamaProvider), the AgentState TypedDict with 13 fields, and the AgentBrain class with 6 agent methods and 6 tool functions.

---

## 6. Sequence Diagram

> **Selected Primary Behavioral Diagram:** Sequence Diagram (models system logic and inter-component interactions).

### 6.1 Chaos Event → Risk Detection → Alert Flow

This sequence demonstrates the core autonomous capability of Athena: detecting a risk injected by the Chaos Engine and alerting stakeholders within 60 seconds.

**Sequence:**
```
Chaos Engine → Simulator API → Webhook Dispatcher → Ingestion Pipeline
→ Graph Syncer (Neo4j) + Vector Indexer (Pinecone) → Agent Brain (Researcher)
→ Agent Brain (Alerter) → Human Gate → Dashboard (pending alert)
```

**Refer to:** *Chaos Event Sequence Diagram* (Athena_HLD_v0.3.0, Section 6.1) — shows the full 9-participant sequence with timing annotations (Total auto: < 60 seconds).

**Walkthrough:**
1. **Chaos Engine** selects a fault pattern (e.g., TICKET_BLOCKER) and mutates a story in the Simulator API
2. **Simulator API** processes the mutation, logs an AuditLog entry, and triggers the Webhook Dispatcher
3. **Webhook Dispatcher** fires an HTTP POST with a Jira-compatible JSON payload to Athena Core
4. **Ingestion Pipeline** validates, deduplicates, and routes the event to Graph Syncer and Vector Indexer
5. **Graph Syncer** creates/updates nodes and [:BLOCKS] relationship in Neo4j via Cypher MERGE
6. **Vector Indexer** generates a text embedding and upserts to Pinecone with metadata
7. **Agent Brain** detects a risk event → Planner classifies as RISK_ALERT → Researcher queries Neo4j for impact analysis (downstream blocked tasks, affected milestones, responsible developer) and Pinecone for similar historical incidents
8. **Alerter** drafts a structured alert with severity, impact analysis, and recommended action
9. **Human Gate** holds the alert for human approval → Dashboard displays pending alert card

### 6.2 User Query Processing Flow

This sequence shows how a Program Manager's natural language query is processed.

**Sequence:**
```
User → Dashboard → Athena Core API → Planner → Researcher
→ Neo4j + Pinecone → LLM → Responder → Dashboard → User
```

**Refer to:** *User Query Sequence Diagram* (Athena_HLD_v0.3.0, Section 6.2) — shows the 7-participant sequence for query processing.

**Walkthrough:**
1. **User** types "Which tickets are blocking the March milestone?" in the Chat Panel
2. **Dashboard** sends POST to `/api/v1/query` with the query text
3. **Planner** classifies input as STATUS_QUERY, determines required tool calls
4. **Researcher** executes `search_graph()` with Cypher: `MATCH (t:Task)-[:BLOCKS]->(m:Milestone {name: "March"}) RETURN t` and `search_docs()` for semantic context
5. **LLM** synthesizes graph + vector results into a natural language response with citations
6. **Responder** formats the response with ticket IDs, confidence score, and source references
7. **Dashboard** renders the response in the Chat Panel with clickable citation links

### 6.3 Agent State Machine Flow

**Refer to:** *LangGraph Agent State Machine Diagram* (Athena_HLD_v0.3.0, Section 6.3) — shows the complete LangGraph graph with Semantic Router → Planner → Researcher → Alerter → Responder → Human Gate → Executor/Log → End, including conditional branching for query/risk/general paths and approved/rejected/auto approval outcomes.

---

## 7. Security & Performance Considerations

### 7.1 Data Security

| Mechanism | Implementation | SRS Trace |
|-----------|----------------|-----------|
| **Transport Encryption** | All cloud API calls (Neo4j Aura, Pinecone, Gemini, Groq) use HTTPS/TLS | NFR-02 |
| **Database Encryption** | Neon PostgreSQL provides encryption at rest; Neo4j Aura uses encrypted storage | NFR-02 |
| **Secure Webhooks** | Internal-only communication (Docker network); production would add HMAC signatures | NFR-02 |
| **Credential Protection** | All API keys in `.env` (gitignored); `.env.example` with placeholders only; no credentials in code or VCS | NFR-02 |

### 7.2 Authentication and Access Control

| Mechanism | Implementation |
|-----------|----------------|
| **Role-Based Access Control (RBAC)** | User roles (PMO, PM, Scrum Master, Admin) determine visible data and action permissions |
| **God Mode Protection** | Chaos injection endpoints restricted to Admin role; not exposed to general users |
| **API Internal-Only** | Simulator API and Athena Core API are Docker-internal; only Dashboard port (3000) is externally exposed |
| **Human Gate** | All risk-triggered actions (alerts, escalations) require explicit human approval before execution |

### 7.3 Privacy Protection

| Concern | Mitigation |
|---------|------------|
| **Data Sovereignty** | Demo mode: fully air-gapped deployment via Ollama — zero external API calls, all processing on localhost |
| **LLM Prompt Leakage** | Dev mode: only LLM prompts sent to Gemini/Groq; no raw project data included in prompts |
| **Synthetic Data** | All enterprise data is AI-generated; no real corporate data is used or stored |
| **No Telemetry** | Zero telemetry, analytics, or external tracking in any deployment mode |
| **Audit Compliance** | Every agent decision is logged in the append-only ATL (Action & Tracking Log) with timestamp and rationale |

**Refer to:** *Privacy Model Diagrams* (Athena_HLD_v0.3.0, Section 7.2) — shows data flow analysis for both Dev Mode (cloud LLMs with prompts-only external) and Demo Mode (fully local, air-gapped).

### 7.4 Performance Optimization

| Technique | Where Applied | Benefit |
|-----------|---------------|---------|
| **Connection Pooling** | SQLAlchemy → PostgreSQL (Neon) | Reuse DB connections, avoid connection overhead |
| **Async HTTP** | FastAPI + httpx (webhooks) | Non-blocking I/O for concurrent event processing |
| **Background Tasks** | Webhook dispatch after API response | Fast API response; webhook fires asynchronously |
| **Cypher Index** | Neo4j node properties (id, key) | Sub-second graph lookups on indexed fields |
| **HNSW Vector Index** | Pinecone | Sub-second approximate nearest neighbor search |
| **LLM Caching** | Repeated identical queries | Cache result for configurable TTL |
| **Batch Data Gen** | Groq (fast inference) for timeline_sim | 10x faster than Gemini for bulk story generation |

**Performance Targets:**

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Chat query (P95) | < 5 seconds | End-to-end from query to rendered response |
| Webhook ingestion | < 30 seconds | HTTP POST receipt to Neo4j + Pinecone upsert |
| Risk detection | < 60 seconds | Chaos event to alert on dashboard |
| System startup | < 3 minutes | `docker compose up` to all services healthy |
| Dashboard refresh | < 2 seconds | Polling cycle for health metrics |

---

## 8. Technology Stack Selection

### 8.1 Programming Languages

| Language | Scope | Justification |
|----------|-------|---------------|
| **Python 3.11** | All backend (Simulator, Athena Core, agents) | Rich AI/ML ecosystem; LangGraph, FastAPI, SQLAlchemy all Python-native |
| **TypeScript 5.x** | Frontend (Dashboard) | Type safety for complex React components; Next.js requires TypeScript |

### 8.2 Front-End Technologies

| Technology | Version | Purpose |
|-----------|---------|---------|
| **Next.js** | 14.x | React meta-framework with SSR, API routes, and App Router |
| **React** | 18.x | Component-based UI rendering |
| **Tailwind CSS** | 3.x | Utility-first CSS for rapid UI development |

### 8.3 Back-End Technologies

| Technology | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | 0.110+ | Async REST API framework with auto-generated OpenAPI docs |
| **LangGraph** | 0.1+ | Stateful multi-agent workflow orchestration with checkpointing |
| **SQLAlchemy** | 2.0+ | Database-agnostic ORM for PostgreSQL |
| **APScheduler** | 3.10+ | Background scheduled task execution (Chaos Engine) |
| **httpx** | 0.27+ | Async HTTP client for webhook dispatch |
| **py2neo** | 2021.2+ | Python client for Neo4j (Cypher queries) |

### 8.4 Databases

| Database | Type | Deployment | Purpose |
|----------|------|-----------|---------|
| **PostgreSQL (Neon)** | Relational | Cloud serverless (free tier) | Simulator entity storage (users, projects, tickets) |
| **Neo4j Aura** | Graph | Cloud managed (free tier) | Knowledge graph for relationship traversal |
| **Pinecone** | Vector | Cloud managed (free tier) | Semantic similarity search over embeddings |

### 8.5 AI / LLM Frameworks

| Technology | Purpose | Deployment Mode |
|-----------|---------|-----------------|
| **Google Gemini 1.5 Flash** | Primary LLM for development and reasoning | Dev mode (cloud API, 15 RPM free tier) |
| **Groq Cloud (Llama 3.3 70B)** | Fast inference for batch data generation | Dev mode (cloud API, fastest inference) |
| **Ollama + Llama 3 8B Q4** | Local LLM for air-gapped demos | Demo mode (local GPU, RTX 3050 6GB VRAM) |
| **LangGraph** | Multi-agent state machine orchestration | Both modes |
| **LangChain** | LLM integration libraries (Google GenAI, Groq) | Both modes |

### 8.6 Cloud and DevOps Platforms

| Technology | Purpose |
|-----------|---------|
| **Docker** | Container runtime for all services |
| **Docker Compose** | Multi-service orchestration with profiles (dev, demo) |
| **Neon** | Serverless PostgreSQL hosting (cloud, free tier) |
| **Neo4j Aura** | Managed graph database (cloud, free tier) |
| **Pinecone** | Managed vector database (cloud, free tier) |

**Refer to:** *Technology Stack Diagram* (Athena_HLD_v0.3.0, Section 8.1) — shows the complete stack organized by layer (Frontend, Backend, Data, LLM Inference, Infra).

---

## 9. Scalability & Reliability Planning

### 9.1 System Scalability

**Current Deployment (Academic):**

**Refer to:** *Deployment Topology Diagram* (Athena_HLD_v0.3.0, Section 9.1) — shows the Docker Compose service topology with ports, profiles, and persistence mapping.

**Scaling Path to Production:**

| Dimension | Academic Deployment | Production Path |
|-----------|-------------------|-----------------|
| Services | Single-instance per service (Docker Compose) | Kubernetes with replica sets + auto-scaling |
| LLM Throughput | 15 RPM (Gemini free tier) | Paid API tier or self-hosted vLLM cluster |
| Relational DB | Neon free tier (0.5 GB) | Neon Pro or self-hosted PostgreSQL with read replicas |
| Graph DB | Neo4j Aura free (50K nodes) | Neo4j AuraDB Professional or Enterprise cluster |
| Vector DB | Pinecone free (100K vectors) | Pinecone Standard or self-hosted Qdrant |
| Frontend | Single Next.js instance | CDN-deployed static export with edge functions |

### 9.2 Load Balancing

| Scenario | Current | Production Path |
|----------|---------|-----------------|
| API Traffic | Single FastAPI instance handles all requests | Nginx / Traefik reverse proxy distributing across replicas |
| LLM Inference | Sequential requests to single provider | Request queue with round-robin across provider pool |
| Database Reads | Direct connection to single DB | Connection pooling with read replicas |
| Webhook Ingestion | Synchronous processing | Message queue (Redis / RabbitMQ) for async processing with backpressure |

### 9.3 Fault Tolerance

| Mechanism | Implementation |
|-----------|----------------|
| **Webhook Retry** | 3 retries with exponential backoff (1s, 2s, 4s); 10-second timeout per request |
| **Graceful Degradation** | If Athena Core is unreachable, webhooks are logged and dropped — Simulator continues operating independently |
| **Event Deduplication** | `event_id` (UUID v4) uniqueness check prevents duplicate processing when events are retried |
| **Idempotent Operations** | Graph Syncer uses MERGE (upsert) in Cypher — safe to replay events without data corruption |
| **LLM Fallback Chain** | Groq → Gemini → Ollama (if primary provider fails, falls to next available) |
| **Container Restart** | `restart: always` policy on all Docker services — auto-recover from crashes |
| **Data Persistence** | Named Docker volumes for Neo4j, ChromaDB, Ollama models; cloud databases (Neon, Aura, Pinecone) are inherently persistent |

### 9.4 Continuous Monitoring

| Tool / Mechanism | Purpose |
|-----------------|---------|
| **`/api/v1/health` endpoints** | Liveness check on Simulator API and Athena Core API |
| **Docker Compose logs** | `docker compose logs -f` for real-time service log streaming |
| **ATL (Action & Tracking Log)** | Audit trail of every agent decision with timestamp, agent ID, input, output, and rationale |
| **Dashboard Health Panel** | Visual indicators for system health — turns RED if any service is unreachable |
| **APScheduler job monitoring** | Chaos Engine logs inject times, types, and affected entities |

---

## 10. Conclusion

The proposed system design provides a scalable, secure, and AI-driven program management platform capable of autonomous risk detection, proactive stakeholder alerting, and real-time decision support through a modular multi-agent architecture. The key contributions of this design are:

1. **Dual-Architecture Separation:** The Project Universe simulator and Athena Core are fully decoupled, communicating only via webhooks. This ensures the agent core is production-portable — it can connect to real Jira, Azure DevOps, or ServiceNow APIs without modifying its core logic, making the architecture both academically rigorous and enterprise-applicable.

2. **GraphRAG Knowledge Synthesis:** By combining Neo4j's structured graph traversal (Cypher queries for multi-hop relationship analysis) with Pinecone's semantic vector search (embedding-based similarity), the system achieves relationship-aware, citation-grounded responses that eliminate LLM hallucination — every claim cites specific ticket IDs from the knowledge graph.

3. **Triple-Mode LLM Architecture:** The `LLMProvider` abstraction supports three backends (Gemini for development, Groq for fast data generation, Ollama for air-gapped demos), enabling deployment across environments from cloud-connected development to fully offline operation — addressing enterprise data sovereignty requirements without code changes.

4. **Human-in-the-Loop Governance:** The Human Gate node in the LangGraph state machine ensures no autonomous action is taken without explicit human approval, while the append-only ATL provides a complete audit trail for compliance — critical requirements for enterprise AI trust.

5. **Event-Driven Reactive Pipeline:** The webhook-driven ingestion pipeline enables end-to-end detection latency under 60 seconds from chaos event injection to alert appearing on the dashboard, compared to the 2–3 day lag of manual monitoring — a 4,000x improvement in detection speed.

The Object-Oriented design approach ensures consistency across all architectural, structural, and behavioral models. Every UI component, API endpoint, and agent tool traces back to specific SRS requirements (FR-01 through FR-09, NFR-01, NFR-02), ensuring the system is engineered through disciplined Software Engineering principles, not just coded.

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-02-05 | Team Athena | Initial architecture definition |
| 0.2.0 | 2026-02-19 | Team Athena | C4 diagrams, API contracts, security model |
| 0.3.0 | 2026-03-03 | Team Athena | 10-section academic format with full UML diagrams |
| 0.4.0 | 2026-03-17 | Team Athena | Restructured to sample template with detailed subsections, OO approach, SRS traceability, expanded layer descriptions |
| 0.4.1 | 2026-03-17 | Team Athena | Integrated production Jira TOOL_CONFIG (10 functions) into Simulator API and Agent Brain tools; expanded agent tooling from 6 to 15 tools |
