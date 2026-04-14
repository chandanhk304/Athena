# Software Requirements Specification (SRS)
**Document ID:** Athena_SRS_Functional-Requirements_v0.2.0  
**Project:** Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation  
**Date:** 2026-02-19  
**Version:** 0.2.0 (Minor - Comprehensive Requirements with Use Cases & Analysis)

---

## 1. Introduction

### 1.1 Purpose
This Software Requirements Specification (SRS) document provides a complete description of the functional and non-functional requirements for Project Athena. It serves as the primary reference for the development team during system design, implementation, and testing phases. The document is intended for all stakeholders including the development team, project guide, and evaluation panel.

### 1.2 Scope
Project Athena is an Autonomous Multi-Agent Framework that provides real-time program management and proactive risk mitigation for enterprise environments. The system operates within a self-contained simulation environment (Project Universe) and demonstrates MNC-grade capabilities using a dual-mode LLM architecture (cloud API for development, local LLM for air-gapped deployment). The system:
- **Ingests** real-time project events via webhooks from a simulated enterprise environment
- **Stores** structured relationships in a Knowledge Graph and unstructured context in a Vector Store
- **Reasons** using a multi-agent LangGraph state machine powered by an LLM via a pluggable `LLMProvider` abstraction
- **Alerts** stakeholders proactively when risks are detected, with human-in-the-loop approval
- **Logs** every agent decision in an auditable Action & Tracking Log (ATL)

### 1.3 Intended Audience

| Audience | Relevance |
|----------|-----------|
| Development Team | Implementation reference for all modules |
| Project Guide | Evaluation of requirement completeness and feasibility |
| QA & Testing | Test case design and validation criteria |
| Panel Evaluators | Understanding of system scope, capabilities, and boundaries |
| Future Maintainers | System behavior documentation for extensions |

### 1.4 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| AI Agent | An autonomous software entity that perceives its environment, reasons about it, and takes actions to achieve goals |
| ATL | Action & Tracking Log — a persistent audit trail of all agent decisions and actions |
| Chaos Engine | A scheduled subsystem that injects realistic enterprise failures into the simulator |
| ChromaDB | An open-source vector embedding database for semantic search |
| Cypher | The query language for Neo4j graph databases |
| GraphRAG | Retrieval-Augmented Generation enhanced with Knowledge Graph traversal |
| Human Gate | A checkpoint in the agent workflow requiring human approval before proceeding |
| LangGraph | A Python framework for building stateful, multi-actor applications with LLMs |
| LLM | Large Language Model — a deep learning model trained on large text corpora |
| LLMProvider | An abstraction layer with pluggable backends (Gemini for dev, Ollama for air-gapped demo) |
| Neo4j | A graph database that stores data as nodes and relationships |
| Ollama | An open-source framework for running LLMs locally |
| RAG | Retrieval-Augmented Generation — grounding LLM responses in external knowledge |
| SSOT | Single Source of Truth — a unified authoritative data source |
| Webhook | An HTTP POST callback triggered by a state change in the source system |

### 1.5 References

| Ref # | Document | Version |
|-------|----------|---------|
| R1 | Athena_Synopsis_Zeroeth-Review | v0.2.0 |
| R2 | Athena_HLD_System-Architecture | v0.2.0 |
| R3 | Athena_DDD_Database-Schema | v0.1.0 |
| R4 | Athena_Research_Domain-Analysis | v0.1.0 |
| R5 | Athena_Feasibility-Study_Technical-Analysis | v0.1.0 |
| R6 | IEEE Std 830-1998 (Recommended Practice for SRS) | — |

---

## 2. Overall Description

### 2.1 Product Perspective

Athena is a self-contained system that does NOT integrate with any external production tools. Instead, it creates its own simulated enterprise environment (Project Universe) and then monitors that environment autonomously.

```
 EXTERNAL WORLD                       ATHENA SYSTEM BOUNDARY
+-----------------------------+      +==========================================+
|                             |      ||                                        ||
|  Real Jira       ╳ --------|----->||  Project Universe (Simulator)           ||
|  Real Azure DevOps ╳ ------|----->||    └──> Mock Jira API                   ||
|  Real ServiceNow   ╳ -----|----->||    └──> Chaos Engine                    ||
|                             |      ||    └──> Webhook Dispatcher              ||
|  Cloud LLM APIs             |      ||                                        ||
|  (OpenAI, Claude)  ╳       |      ||  Athena Core (Agent)                   ||
|                             |      ||    └──> Ingestion Pipeline              ||
|  Google Gemini     ✓ ------+----->||    └──> GraphRAG (Neo4j + ChromaDB)     ||
|  (Dev Mode Only)           |      ||    └──> LangGraph Agent Brain           ||
+-----------------------------+      ||    └──> LLMProvider Abstraction         ||
  Real PM tools: Blocked             ||         ├── GeminiProvider (Dev Mode)   ||
  Gemini API: Dev mode only          ||         └── OllamaProvider (Demo Mode)  ||
  Ollama: Demo/air-gapped mode       ||                                        ||
                                     ||  Dashboard (Next.js)                   ||
                                     ||    └──> Chat Interface                  ||
                                     ||    └──> Health Dashboard                ||
                                     ||    └──> God Mode Console                ||
                                     +==========================================+
                                        Services run on localhost (both modes)
```

### 2.2 Product Features (Summary)

| Feature ID | Feature | Description |
|-----------|---------|-------------|
| F1 | Enterprise Simulation | A live simulator that generates realistic project management events |
| F2 | Real-Time Data Ingestion | Webhook-driven pipeline that processes events within 30 seconds |
| F3 | Knowledge Graph Construction | Automated graph building from project events with relationship mapping |
| F4 | Semantic Vector Search | Text-based similarity search across ticket descriptions and notes |
| F5 | Multi-Agent Reasoning | Specialized agents collaborate through a state machine to answer queries |
| F6 | Proactive Risk Detection | Autonomous identification of blockers, overloads, and dependency cycles |
| F7 | Human-in-the-Loop Approval | Mandatory human approval before sensitive actions are executed |
| F8 | Natural Language Interface | Chat-based query system with citation-grounded responses |
| F9 | Audit Trail (ATL) | Complete logging of every agent decision with timestamp and rationale |
| F10 | Dashboard Visualization | Real-time RAG status, health metrics, and chaos injection console |

### 2.3 User Classes and Characteristics

| User Class | Technical Level | Frequency of Use | Key Capabilities Needed |
|-----------|----------------|-------------------|------------------------|
| **PMO Leader / VP** | Low | Daily (morning review) | Executive summary, health overview, milestone tracking |
| **Program Manager** | Medium | Continuous (throughout day) | Risk monitoring, blocker identification, status queries |
| **Scrum Master** | Medium–High | Sprint cycles (planning + standups) | Team workload analysis, sprint health, dependency tracking |
| **Evaluator / Demo User** | Varies | During demonstrations | God Mode console, chaos injection, system observation |

### 2.4 Operating Environment

**Development Machine:** Lenovo LOQ — Intel i5-13450HX (12C/16T), 16 GB DDR5 RAM, NVIDIA RTX 3050 6GB VRAM

| Component | Dev Mode (Cloud LLM) | Demo Mode (Local LLM) |
|-----------|---------------------|----------------------|
| Host OS | Windows 10/11, macOS, or Linux (via Docker) | Same |
| Container Runtime | Docker Engine 24.0+, Docker Compose v2+ | Same |
| Network | Internet (Google Gemini API calls) | Localhost only (air-gapped) |
| RAM Usage | ~7 GB (services only) | ~12-14 GB (services + Ollama) |
| GPU Usage | Not required | RTX 3050 6GB (Llama 3 Q4 inference) |
| Storage | 20 GB | 25 GB (+ Llama 3 model weights) |
| Browser | Chrome, Firefox, or Edge (for Dashboard) | Same |

### 2.5 Design and Implementation Constraints

| Constraint | Rationale |
|-----------|-----------|
| Dual-mode LLM: Cloud (dev) + Local (demo) | 16GB RAM cannot run all services + local LLM + dev tools simultaneously |
| LLM backends limited to Gemini Flash and Llama 3 8B Q4 | Free tier API for dev; Q4 quantization fits in 6GB VRAM for demo |
| LLMProvider abstraction required | Ensures agent logic is decoupled from any specific LLM backend |
| SQLite for simulator DB | Lightweight, zero-configuration, suitable for simulation |
| Docker Compose orchestration | Single-command deployment requirement |
| Python 3.11+ for backend | LangGraph and py2neo compatibility |
| Next.js 14 for frontend | Server-side rendering for dashboard performance |

### 2.6 Assumptions and Dependencies

| # | Assumption / Dependency |
|---|------------------------|
| A1 | Docker and Docker Compose are installed on the deployment machine |
| A2 | **Dev mode:** Google AI Studio API key is configured in `.env` (`GEMINI_API_KEY`) |
| A3 | **Demo mode:** The Llama 3 8B Q4 model has been pulled via Ollama before first use |
| A4 | **Demo mode:** No concurrent resource-intensive applications (IDE, browser closed) |
| A5 | The evaluator uses a modern web browser (Chrome/Firefox/Edge) |
| A6 | `LLM_BACKEND` env variable is set to `gemini` (dev) or `ollama` (demo) |
| D1 | LangGraph library version ≥ 0.1.0 |
| D2 | Neo4j Community Edition 5.x Docker image |
| D3 | ChromaDB version ≥ 0.4.0 |
| D4 | Ollama version ≥ 0.1.0 with Llama 3 8B Q4 model (demo mode only) |
| D5 | Google Generative AI Python SDK (`google-generativeai`) (dev mode only) |

---

## 3. System Context and Actors

### 3.1 System Context Diagram

```
                                    SYSTEM BOUNDARY
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │                                                                              │
 │        ┌─────────────┐         ┌──────────────────────────────────┐          │
 │        │             │         │         ATHENA SYSTEM            │          │
 │        │   ACTORS    │         │                                  │          │
 │        │             │         │  ┌────────────────────────────┐  │          │
 │        │ ┌─────────┐ │  Chat   │  │    Presentation Layer      │  │          │
 │        │ │ PMO     │─┼────────>│  │  (Dashboard + Chat + God)  │  │          │
 │        │ │ Leader  │ │         │  └────────────┬───────────────┘  │          │
 │        │ └─────────┘ │         │               │                 │          │
 │        │             │<────────┤  ┌────────────┴───────────────┐  │          │
 │        │ ┌─────────┐ │  Alert  │  │       Agent Layer          │  │          │
 │        │ │ Program │─┼────────>│  │  (LangGraph State Machine) │  │          │
 │        │ │ Manager │ │         │  └────────────┬───────────────┘  │          │
 │        │ └─────────┘ │         │               │                 │          │
 │        │             │         │  ┌────────────┴───────────────┐  │          │
 │        │ ┌─────────┐ │  Query  │  │       Data Layer           │  │          │
 │        │ │ Scrum   │─┼────────>│  │  (Neo4j + ChromaDB)        │  │          │
 │        │ │ Master  │ │         │  └────────────┬───────────────┘  │          │
 │        │ └─────────┘ │         │               │                 │          │
 │        │             │         │  ┌────────────┴───────────────┐  │          │
 │        │ ┌─────────┐ │  Chaos  │  │     Inference Layer        │  │          │
 │        │ │Evaluator│─┼────────>│  │  (LLMProvider Abstraction)  │  │          │
 │        │ └─────────┘ │         │  └───────────────────────────┘  │          │
 │        │             │         │                                  │          │
 │        └─────────────┘         └──────────────────────────────────┘          │
 │                                                                              │
 │        ┌──────────────────┐     Webhook     ┌───────────────────┐           │
 │        │  Project Universe │───────────────>│   Athena Core     │           │
 │        │  (Simulator)      │               │   (Agent)          │           │
 │        └──────────────────┘                └───────────────────┘           │
 │                                                                              │
 └──────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Actor Descriptions

| Actor | Type | Description | Interactions |
|-------|------|-------------|-------------|
| PMO Leader | Human (Primary) | Executive who needs high-level program health summary | Queries via chat; receives proactive alerts; approves escalations |
| Program Manager | Human (Primary) | Day-to-day manager tracking risks, blockers, and milestones | Queries via chat; monitors dashboard; reviews ATL; approves communications |
| Scrum Master | Human (Secondary) | Team-level manager tracking sprint health and workload | Queries workload; checks sprint status; reviews dependency graphs |
| Evaluator | Human (Special) | Demo observer with access to God Mode for chaos injection | Triggers chaos events; observes system response; validates behavior |
| Project Universe | System (Internal) | Simulated enterprise PM environment generating events | Sends webhooks on state changes; provides REST API for data queries |
| Chaos Engine | System (Internal) | Automated failure injection subsystem | Randomly mutates simulator state; creates blockers and overloads |
| LLMProvider | System (Internal) | Pluggable LLM inference layer | Processes natural language; generates responses via Gemini (dev) or Ollama (demo) |

---

## 4. Functional Requirements

### FR-01: Enterprise Simulation (Project Universe)

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-01.1 | The system SHALL provide a Mock Jira REST API with CRUD operations for Users, Epics, Stories, Risks, and Audit Logs | HIGH | Core data source for the agent to monitor |
| FR-01.2 | The Mock Jira API SHALL support the following endpoints: `GET/POST /api/v1/tickets`, `GET/PUT/DELETE /api/v1/tickets/{id}`, `GET /api/v1/users`, `GET /api/v1/epics`, `GET /api/v1/sprints` | HIGH | Standard REST interface matching real Jira API patterns |
| FR-01.3 | The Chaos Engine SHALL inject realistic enterprise failures on a configurable schedule (default: every 5 minutes) | HIGH | Validates system behavior under enterprise-like stress |
| FR-01.4 | Chaos events SHALL include: ticket blocking (mark as BLOCKED), developer overloading (assign >5 critical tasks), milestone delay (set past_due = true), dependency cycle creation, and priority escalation | HIGH | Covers the critical failure modes seen in real enterprises |
| FR-01.5 | The Webhook Dispatcher SHALL fire HTTP POST requests to a configurable Athena endpoint within 2 seconds of any state change | HIGH | Enables real-time event-driven processing |
| FR-01.6 | Webhook payloads SHALL conform to a defined JSON schema including: event_type, entity_type, entity_id, changed_fields, timestamp, and source | HIGH | Consistent data contract between simulator and agent |
| FR-01.7 | The Synthetic Data Generator SHALL create a realistic enterprise dataset with 20-50 users, 3-5 projects, 4-8 epics per project, and 30-50 stories per project on initialization | MEDIUM | Provides meaningful data volume for demonstration |
| FR-01.8 | The simulator SHALL persist all data in SQLite with proper foreign key constraints and referential integrity | HIGH | Data consistency for downstream processing |

### FR-02: Data Ingestion Pipeline

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-02.1 | The Ingestion Pipeline SHALL receive webhook HTTP POST requests on `/api/v1/webhook/event` | HIGH | Entry point for all real-time data |
| FR-02.2 | The Pipeline SHALL validate incoming webhook payloads against the defined JSON schema and reject malformed payloads with HTTP 400 | HIGH | Data quality assurance |
| FR-02.3 | For each valid event, the Pipeline SHALL invoke the Graph Syncer to create or update nodes and relationships in Neo4j | HIGH | Knowledge Graph must reflect current state |
| FR-02.4 | For each valid event containing text fields (title, description, comments), the Pipeline SHALL invoke the Vector Indexer to create or update embeddings in ChromaDB | HIGH | Semantic search index must stay current |
| FR-02.5 | The Pipeline SHALL process each webhook event within 30 seconds of receipt | HIGH | Near real-time requirement for risk detection |
| FR-02.6 | The Pipeline SHALL handle duplicate events idempotently (processing the same event twice produces the same result) | MEDIUM | Webhook delivery guarantees may cause duplicates |
| FR-02.7 | The Pipeline SHALL log all received events with timestamp and processing status in the Ingestion Log | MEDIUM | Debugging and audit capability |

### FR-03: Knowledge Graph (Neo4j)

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-03.1 | The Graph Syncer SHALL create and maintain the following node types: User, Task, Risk, Milestone, Feature, Epic, Sprint | HIGH | Complete entity model for PM domain |
| FR-03.2 | The Graph Syncer SHALL create and maintain the following relationship types: ASSIGNED_TO, BLOCKS, PART_OF, HAS_RISK, IMPACTS, OWNS, MEMBER_OF, DEPENDS_ON | HIGH | Captures structural dependencies |
| FR-03.3 | The system SHALL support Cypher queries for: finding all blocked critical tasks, identifying overloaded developers (>5 active critical tasks), detecting dependency cycles, and listing risks impacting a specific milestone | HIGH | Core analysis capabilities |
| FR-03.4 | Node properties SHALL include: entity_id, name, status, priority, created_at, updated_at, and entity-specific fields | HIGH | Rich metadata for analysis |
| FR-03.5 | The Graph Syncer SHALL perform UPSERT operations (create if not exists, update if exists) to maintain consistency | HIGH | Prevents duplicate nodes |

### FR-04: Vector Store (ChromaDB)

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-04.1 | The Vector Indexer SHALL maintain two collections: `ticket_context` (ticket titles, descriptions, comments) and `meeting_notes` (generated summaries and risk reports) | HIGH | Separate collections for different content types |
| FR-04.2 | Text SHALL be embedded using the active LLMProvider backend: Gemini Embedding API (dev mode) or Ollama embeddings endpoint (demo mode) | HIGH | Dual-mode support; both backends produce compatible embeddings |
| FR-04.3 | Each vector entry SHALL store metadata: source_entity_id, entity_type, timestamp, and original_text | HIGH | Enables citation tracing |
| FR-04.4 | Semantic search SHALL return top-K (configurable, default K=5) most similar documents with similarity scores | HIGH | Tunable retrieval quality |
| FR-04.5 | The Vector Indexer SHALL update embeddings when the source entity's text fields change | MEDIUM | Keeps semantic index consistent |

### FR-05: Multi-Agent Reasoning (LangGraph)

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-05.1 | The Agent Brain SHALL implement a LangGraph state machine with the following nodes: Planner, Researcher, Alerter, Responder, Human Gate, Executor | HIGH | Core agent architecture |
| FR-05.2 | The Planner node SHALL classify incoming inputs as: STATUS_QUERY, RISK_ALERT, ACTION_REQUEST, or GENERAL_QUESTION | HIGH | Determines processing path |
| FR-05.3 | The Researcher node SHALL invoke `search_graph()` and `search_docs()` tools to gather context from Neo4j and ChromaDB | HIGH | Dual-source retrieval (GraphRAG) |
| FR-05.4 | The Alerter node SHALL be triggered when a risk event exceeds a severity threshold and SHALL draft a stakeholder communication with severity, impact, and recommended action | HIGH | Proactive alerting capability |
| FR-05.5 | The Responder node SHALL format responses with: answer text, confidence level, source citations (ticket IDs), and data freshness timestamp | HIGH | Grounded, traceable responses |
| FR-05.6 | The Human Gate SHALL pause execution for all actions classified as RISK_ALERT or ACTION_REQUEST and require explicit human approval (Approve/Reject/Modify) | HIGH | Governance and safety |
| FR-05.7 | The Executor node SHALL carry out approved actions and log them to the ATL | HIGH | Action completion and audit |
| FR-05.8 | The Agent SHALL NEVER generate responses from its training data alone; all factual claims MUST be backed by data retrieved from Neo4j or ChromaDB | HIGH | Zero hallucination requirement |
| FR-05.9 | If no relevant data is found, the Agent SHALL respond: "I don't have sufficient information to answer this query. No matching data found in [source]." | HIGH | Explicit failure over confabulation |
| FR-05.10 | The agent state SHALL include checkpointing to allow recovery from mid-workflow failures | MEDIUM | Reliability in long-running workflows |

### FR-06: User Chat Interface

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-06.1 | Users SHALL interact with Athena via a natural language chat interface in the Dashboard | HIGH | Primary user interaction mode |
| FR-06.2 | The chat interface SHALL support multi-turn conversations with context retained across messages within a session | MEDIUM | Enables follow-up queries |
| FR-06.3 | Each response SHALL display: answer text, source citations as clickable references, confidence indicator, and response timestamp | HIGH | Transparency and traceability |
| FR-06.4 | The chat interface SHALL display a typing indicator while the agent processes a query | LOW | UX polish |

### FR-07: Autonomous Risk Monitoring

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-07.1 | The system SHALL detect tickets transitioning to BLOCKED status within 60 seconds of the webhook event | HIGH | Core proactive monitoring |
| FR-07.2 | The system SHALL classify detected risks into severity levels: CRITICAL (impacts milestone), HIGH (blocks >2 downstream tasks), MEDIUM (blocks 1-2 tasks), LOW (potential risk) | HIGH | Prioritization for stakeholders |
| FR-07.3 | The system SHALL detect developer overload when a single user has >5 active tasks with priority CRITICAL or HIGH | MEDIUM | Resource bottleneck detection |
| FR-07.4 | The system SHALL detect dependency cycles using Neo4j graph traversal (Cypher pathfinding queries) | MEDIUM | Deadlock prevention |
| FR-07.5 | The system SHALL detect overdue milestones by comparing milestone due dates against current date and task completion percentages | MEDIUM | Schedule risk detection |
| FR-07.6 | For each detected risk, the system SHALL perform multi-hop impact analysis: identify all downstream tasks, affected milestones, and impacted team members | HIGH | Comprehensive risk assessment |

### FR-08: Action & Tracking Log (ATL)

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-08.1 | Every agent action SHALL be recorded in the ATL with: timestamp, action_type, agent_node, input_context, decision_rationale, output, and approval_status | HIGH | Complete audit compliance |
| FR-08.2 | The ATL SHALL be queryable via both the Dashboard UI and API | HIGH | Multiple access methods for review |
| FR-08.3 | The system SHALL generate daily digest summaries of all ATL entries grouped by severity | MEDIUM | Periodic review capability |
| FR-08.4 | ATL entries SHALL be immutable once created (append-only log) | HIGH | Audit integrity |

### FR-09: Dashboard & Visualization

| ID | Requirement | Priority | Rationale |
|----|-------------|----------|-----------|
| FR-09.1 | The Dashboard SHALL display real-time program health using RAG (Red/Amber/Green) indicators for each project | HIGH | At-a-glance status |
| FR-09.2 | The Dashboard SHALL show: active risk count, blocked ticket count, overloaded developer count, and overall health score | HIGH | Key metrics visibility |
| FR-09.3 | The Dashboard SHALL provide a God Mode Console that allows authorized users to: manually trigger chaos events, view system internals, and monitor agent state transitions | MEDIUM | Demo and evaluation capability |
| FR-09.4 | The Dashboard SHALL auto-refresh health metrics at configurable intervals (default: 30 seconds) | MEDIUM | Real-time feel without manual refresh |
| FR-09.5 | The Dashboard SHALL display pending Human Gate approvals with full context for review | HIGH | Governance workflow in UI |

---

## 5. Non-Functional Requirements

### NFR-01: Performance

| ID | Requirement | Target | Measurement Method |
|----|-------------|--------|-------------------|
| NFR-01.1 | Chat query response time | < 5 seconds (P95) | Automated load test with 50 predefined queries |
| NFR-01.2 | Webhook ingestion latency | < 30 seconds per event | Timestamp diff: webhook receipt vs. graph/vector update complete |
| NFR-01.3 | Risk detection latency | < 60 seconds from event | Timestamp diff: chaos injection vs. alert generation |
| NFR-01.4 | Concurrent user support | ≥ 10 simultaneous queries | Load test with 10 parallel requests |
| NFR-01.5 | Dashboard refresh latency | < 2 seconds per refresh cycle | Browser performance profiling |
| NFR-01.6 | System startup time | < 3 minutes from `docker-compose up` | Timed full-stack startup |

### NFR-02: Reliability

| ID | Requirement | Target | Measurement Method |
|----|-------------|--------|-------------------|
| NFR-02.1 | System availability during demo | 99% (< 1 minute downtime per 2-hour demo) | Continuous monitoring |
| NFR-02.2 | Data consistency | Eventual consistency within 60 seconds | Compare Neo4j state with SQLite source |
| NFR-02.3 | Hallucination rate | 0% | Manual audit of 100 responses against knowledge graph ground truth |
| NFR-02.4 | Webhook delivery reliability | > 99% | Compare fired webhooks (simulator log) vs received webhooks (ingestion log) |
| NFR-02.5 | Agent workflow completion | > 95% (state machine reaches terminal node) | LangGraph execution logs |

### NFR-03: Security & Privacy

| ID | Requirement | Target | Measurement Method |
|----|-------------|--------|-------------------|
| NFR-03.1 | Data sovereignty (demo mode) | 100% local processing when `LLM_BACKEND=ollama` | Network traffic analysis (no external calls in demo mode) |
| NFR-03.2 | Data sovereignty (dev mode) | Only LLM prompts sent externally (to Gemini API); project data stays local | Network traffic audit — only `generativelanguage.googleapis.com` calls |
| NFR-03.3 | Audit trail completeness | 100% of agent actions logged | Compare agent state transitions with ATL entries |
| NFR-03.4 | Human approval enforcement | 100% of sensitive actions require approval | Verify no alert or escalation bypasses Human Gate |
| NFR-03.5 | No credential storage | API keys in `.env` only (gitignored); no cleartext in codebase | Static code analysis |
| NFR-03.6 | Container isolation | Each service in its own container with minimal privileges | Docker security audit |

### NFR-04: Portability & Deployment

| ID | Requirement | Target | Measurement Method |
|----|-------------|--------|-------------------|
| NFR-04.1 | Single-command deployment | `docker-compose up -d` starts all services | Manual verification on clean machine |
| NFR-04.2 | OS compatibility | Works on Windows 10+, macOS 12+, Ubuntu 22.04+ | Cross-platform testing |
| NFR-04.3 | Hardware minimum | Functional on 16GB RAM, 50GB storage | Verified on minimum-spec machine |
| NFR-04.4 | Dependency management | All Python dependencies in requirements.txt / pyproject.toml | Reproducible build verification |
| NFR-04.5 | Configuration externalization | All tunable parameters in .env or config files (no hardcoded values) | Code review |

### NFR-05: Usability

| ID | Requirement | Target | Measurement Method |
|----|-------------|--------|-------------------|
| NFR-05.1 | Time to first query | < 5 minutes from startup | Timed walkthrough by new user |
| NFR-05.2 | Natural language support | System understands conversational English queries | Test suite of 30 varied phrasings |
| NFR-05.3 | Error messaging | User-friendly error messages (no raw stack traces) | UI review |

---

## 6. Use Cases

### UC-01: Query Program Status

```
TITLE:    Query Program Status
ACTOR:    PMO Leader / Program Manager
TRIGGER:  User types a natural language query in the Chat Interface

PRECONDITIONS:
  - System is running (all Docker services UP)
  - Simulator has generated baseline project data
  - Knowledge Graph and Vector Store are populated

MAIN SUCCESS SCENARIO:
  ┌─────────┐                                               ┌──────────┐
  │  USER   │                                               │  ATHENA  │
  └────┬────┘                                               └────┬─────┘
       │                                                         │
       │  1. Types: "What is the status of Project Alpha?"       │
       │────────────────────────────────────────────────────────>│
       │                                                         │
       │                    2. Planner classifies as STATUS_QUERY │
       │                    3. Researcher queries Neo4j:          │
       │                       MATCH (p:Project {name:'Alpha'})  │
       │                       -[:HAS_EPIC]->(e)-[:HAS_STORY]->(s│)
       │                       RETURN p, e, s                    │
       │                    4. Researcher queries ChromaDB:       │
       │                       semantic_search("Project Alpha    │
       │                       status progress")                 │
       │                    5. Responder merges graph data +      │
       │                       vector context                    │
       │                    6. LLM generates response with       │
       │                       citations                         │
       │                                                         │
       │  7. Response: "Project Alpha is 72% complete.           │
       │     2 CRITICAL blockers: TICKET-189 (Payment API        │
       │     blocked by TICKET-156), TICKET-234 (DB Migration    │
       │     overdue by 3 days). March milestone at risk.         │
       │     [Sources: EPIC-7, TICKET-189, TICKET-234,           │
       │      MILESTONE-3]"                                      │
       │<────────────────────────────────────────────────────────│
       │                                                         │

POSTCONDITIONS:
  - Response displayed in Chat Interface with clickable citations
  - Query logged in ATL with processing time

ALTERNATIVE FLOWS:
  3a. No matching project found in Knowledge Graph
      → Agent responds: "I don't have information about a project 
        called 'Alpha'. Available projects: [list from Neo4j]"
  6a. LLM cannot synthesize a coherent response
      → Agent responds with raw data: "Here are the relevant 
        tickets for Project Alpha: [structured list]"
```

### UC-02: Proactive Risk Alert (Blocked Ticket)

```
TITLE:    Proactive Risk Alert — Blocked Critical Ticket
ACTOR:    System (Chaos Engine) → Athena → Program Manager
TRIGGER:  Chaos Engine marks a CRITICAL ticket as BLOCKED

PRECONDITIONS:
  - Chaos Engine is running on schedule
  - Athena Ingestion Pipeline is listening for webhooks
  - Knowledge Graph contains the ticket and its relationships

MAIN SUCCESS SCENARIO:
  ┌──────────┐        ┌──────────┐        ┌──────────┐        ┌──────────┐
  │  CHAOS   │        │ PROJECT  │        │  ATHENA  │        │   PMO    │
  │  ENGINE  │        │ UNIVERSE │        │   CORE   │        │  USER    │
  └────┬─────┘        └────┬─────┘        └────┬─────┘        └────┬─────┘
       │                    │                   │                    │
  1. Select random         │                   │                    │
     CRITICAL ticket       │                   │                    │
       │                    │                   │                    │
  2. UPDATE tickets        │                   │                    │
     SET status='BLOCKED'  │                   │                    │
       │───────────────────>│                   │                    │
       │                    │                   │                    │
       │              3. Fire webhook           │                    │
       │                    │───────────────────>│                   │
       │                    │                   │                    │
       │                    │             4. Parse webhook           │
       │                    │             5. Graph Syncer:           │
       │                    │                MERGE [:BLOCKS]         │
       │                    │                relationship            │
       │                    │             6. Vector Indexer:         │
       │                    │                Update embedding        │
       │                    │                   │                    │
       │                    │             7. Planner detects         │
       │                    │                RISK_ALERT              │
       │                    │             8. Researcher runs         │
       │                    │                multi-hop analysis:     │
       │                    │                - Downstream tasks?     │
       │                    │                - Affected milestones?  │
       │                    │                - Blocker owner?        │
       │                    │                   │                    │
       │                    │             9. Alerter drafts          │
       │                    │                communication          │
       │                    │                   │                    │
       │                    │            10. HUMAN GATE:             │
       │                    │                Hold for approval       │
       │                    │                   │───────────────────>│
       │                    │                   │                    │
       │                    │                   │  11. PMO reviews   │
       │                    │                   │      and APPROVES  │
       │                    │                   │<───────────────────│
       │                    │                   │                    │
       │                    │            12. Executor sends alert    │
       │                    │            13. Log to ATL              │
       │                    │                   │                    │

POSTCONDITIONS:
  - Alert delivered to Dashboard with full impact analysis
  - ATL entry created with: event details, analysis steps, approval record
  - Knowledge Graph updated with BLOCKS relationship

TIMING:
  Steps 1-3:  < 2 seconds  (Chaos injection + webhook fire)
  Steps 4-6:  < 30 seconds (Ingestion processing)
  Steps 7-9:  < 30 seconds (Agent reasoning)
  Steps 10-11: Variable    (Awaiting human approval)
  Steps 12-13: < 2 seconds (Execution + logging)
  TOTAL (automated): < 60 seconds
```

### UC-03: God Mode Chaos Injection (Demo)

```
TITLE:    God Mode Chaos Injection
ACTOR:    Evaluator / Demo Observer
TRIGGER:  Evaluator clicks "Inject Chaos" in God Mode Console

PRECONDITIONS:
  - Dashboard is running and Evaluator has accessed God Mode
  - System is in normal operating state

MAIN SUCCESS SCENARIO:
  ┌──────────┐                                              ┌──────────┐
  │EVALUATOR │                                              │  ATHENA  │
  └────┬─────┘                                              └────┬─────┘
       │                                                         │
       │  1. Opens God Mode Console in Dashboard                 │
       │  2. Selects chaos type: "Block Critical Ticket"         │
       │  3. Clicks "Inject Chaos"                               │
       │────────────────────────────────────────────────────────>│
       │                                                         │
       │                    4. Simulator API creates blocker      │
       │                    5. Webhook fires to Athena            │
       │                    6. Ingestion processes event          │
       │                    7. Agent detects + analyzes risk      │
       │                    8. Dashboard updates:                 │
       │                       - Health status turns AMBER/RED    │
       │                       - Risk count increments            │
       │                       - Alert appears in notification    │
       │                                                         │
       │  9. Evaluator observes real-time system response         │
       │     (entire flow visible in Dashboard within 60 sec)    │
       │<────────────────────────────────────────────────────────│
       │                                                         │

POSTCONDITIONS:
  - Evaluator can see the complete event → detection → alert flow
  - System health indicators updated in real-time
  - All steps logged and viewable in ATL
```

### UC-04: Workload Analysis Query

```
TITLE:    Developer Workload Analysis
ACTOR:    Scrum Master
TRIGGER:  Scrum Master queries about team workload during sprint planning

MAIN SUCCESS SCENARIO:
  ┌──────────┐                                              ┌──────────┐
  │  SCRUM   │                                              │  ATHENA  │
  │  MASTER  │                                              │          │
  └────┬─────┘                                              └────┬─────┘
       │                                                         │
       │  1. "Which developers are overloaded right now?"         │
       │────────────────────────────────────────────────────────>│
       │                                                         │
       │                    2. Planner: STATUS_QUERY              │
       │                    3. Researcher: Cypher query:          │
       │                       MATCH (u:User)-[:ASSIGNED_TO]->(t) │
       │                       WHERE t.status IN ['In Progress', │
       │                       'Blocked'] AND t.priority IN      │
       │                       ['CRITICAL','HIGH']               │
       │                       WITH u, count(t) as taskCount     │
       │                       WHERE taskCount > 5               │
       │                       RETURN u.name, taskCount          │
       │                                                         │
       │  4. "2 developers are currently overloaded:              │
       │     • dev_alice@company.com: 7 active critical tasks     │
       │       (3 BLOCKED). Bottleneck on: EPIC-12, EPIC-15     │
       │     • dev_bob@company.com: 6 active critical tasks      │
       │       (1 BLOCKED). Bottleneck on: EPIC-8               │
       │     Recommendation: Redistribute tasks from EPIC-12     │
       │     [Sources: USER-5, USER-8, EPIC-8, EPIC-12, EPIC-15]│
       │     "                                                   │
       │<────────────────────────────────────────────────────────│
       │                                                         │
```

### UC-05: Dependency Cycle Detection

```
TITLE:    Dependency Cycle Detection
ACTOR:    System (Automated) / Program Manager
TRIGGER:  New DEPENDS_ON relationship creates a cycle in the task graph

MAIN SUCCESS SCENARIO:
  1. Chaos Engine creates a circular dependency: TASK-A → TASK-B → TASK-C → TASK-A
  2. Webhook fires with the new dependency relationship
  3. Ingestion Pipeline processes and updates Neo4j
  4. Agent detects cycle via Cypher pathfinding:
     MATCH path = (t:Task)-[:DEPENDS_ON*]->(t) RETURN path
  5. Alerter drafts: "⚠️ DEPENDENCY CYCLE DETECTED: TASK-A → TASK-B → TASK-C → TASK-A. 
     This creates a deadlock. None of these tasks can proceed. 
     Recommended: Remove dependency between TASK-C and TASK-A."
  6. Human Gate holds alert for approval
  7. On approval, alert delivered and logged in ATL
```

---

## 7. Data Flow Diagrams

### 7.1 Level 0: Context Diagram

```
                    ┌─────────────────────┐
     Chaos Events   │                     │   Chat Queries
  ┌────────────────>│                     │<──────────────────┐
  │                 │       ATHENA        │                   │
  │   Webhooks      │      SYSTEM         │   Alerts &        │
  │ ┌──────────────>│                     │──────────────┐   │
  │ │               │                     │   Responses   │   │
  │ │               └─────────────────────┘              │   │
  │ │                                                     │   │
  │ │                                                     │   │
+-+-+------------+                              +---------+--+-+
| PROJECT        |                              |  HUMAN USERS  |
| UNIVERSE       |                              |  (PMO, PM,    |
| (Simulator)    |                              |   SM, Eval)   |
+----------------+                              +---------------+
```

### 7.2 Level 1: Major Subsystem Flows

```
┌──────────────┐     Webhook (JSON)      ┌──────────────────┐
│   PROJECT    │ ──────────────────────> │    INGESTION     │
│   UNIVERSE   │                         │    PIPELINE      │
│              │                         │                  │
│ ┌──────────┐ │                         │  Validates &     │
│ │Mock Jira │ │                         │  normalizes      │
│ │   API    │ │                         │  incoming events │
│ └──────────┘ │                         └───────┬──────────┘
│ ┌──────────┐ │                                 │
│ │  Chaos   │ │                    ┌────────────┼────────────┐
│ │  Engine  │ │                    │            │            │
│ └──────────┘ │                    ▼            ▼            ▼
└──────────────┘           ┌──────────┐  ┌──────────┐  ┌──────────┐
                           │  SQLite  │  │  Neo4j   │  │ ChromaDB │
                           │ (Source  │  │ (Graph)  │  │ (Vector) │
                           │  of Truth│  │          │  │          │
                           └──────────┘  └─────┬────┘  └─────┬────┘
                                               │             │
                                               └──────┬──────┘
                                                      │
                                                      ▼
┌──────────────┐    Query / Response     ┌──────────────────┐
│   DASHBOARD  │ <────────────────────── │   LANGGRAPH      │
│              │                         │   AGENT BRAIN    │
│ ┌──────────┐ │    User Query           │                  │
│ │Chat UI   │ │ ──────────────────────> │  ┌────────────┐  │
│ └──────────┘ │                         │  │ Planner    │  │
│ ┌──────────┐ │    Health Metrics       │  │ Researcher │  │
│ │Health    │ │ <────────────────────── │  │ Alerter    │  │
│ │Dashboard │ │                         │  │ Responder  │  │
│ └──────────┘ │    Chaos Trigger        │  │ Human Gate │  │
│ ┌──────────┐ │ ──────────────────────> │  │ Executor   │  │
│ │God Mode  │ │                         │  └────────────┘  │
│ └──────────┘ │                         │                  │
└──────────────┘                         │  ┌────────────┐  │
                                         │  │ Ollama     │  │
                                         │  │ (Llama 3)  │  │
                                         │  └────────────┘  │
                                         └──────────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │     ATL      │
                                              │ (Audit Log)  │
                                              └──────────────┘
```

### 7.3 Level 2: Agent Processing Detail

```
                  ┌────────────────────────────────────────────────────────┐
                  │                  AGENT BRAIN (LangGraph)               │
                  │                                                        │
  Input           │  ┌──────────┐    ┌──────────────┐                     │
  (Query/Event)──>│  │ SEMANTIC │───>│   PLANNER    │                     │
                  │  │ ROUTER   │    │ (Classify    │                     │
                  │  └──────────┘    │  intent)     │                     │
                  │                  └──────┬───────┘                     │
                  │                         │                              │
                  │            ┌────────────┼────────────┐                │
                  │            │STATUS_QUERY│RISK_ALERT  │GENERAL        │
                  │            ▼            ▼            ▼                │
                  │     ┌────────────┐  ┌─────────┐  ┌─────────┐        │
                  │     │ RESEARCHER │  │ ALERTER │  │RESPONDER│        │
                  │     │            │  │         │  │(Direct) │        │
                  │     │ Tools:     │  │ Tools:  │  └────┬────┘        │
                  │     │ search_    │  │ draft_  │       │              │
                  │     │ graph()    │  │ message │       │              │
                  │     │ search_    │  │ ()      │       │              │
                  │     │ docs()     │  └────┬────┘       │              │
                  │     └─────┬──────┘       │            │              │
                  │           │              │            │              │
                  │           ▼              ▼            │              │
                  │     ┌────────────────────────┐        │              │
                  │     │     RESPONDER          │<───────┘              │
                  │     │ (Format + cite sources)│                       │
                  │     └───────────┬────────────┘                       │
                  │                 │                                     │
                  │                 ▼                                     │
                  │     ┌────────────────────────┐                       │
                  │     │     HUMAN GATE         │                       │
                  │     │ (If RISK_ALERT or      │──> Pending Approval   │
                  │     │  ACTION_REQUEST)       │    (Dashboard UI)     │
                  │     └───────────┬────────────┘                       │
                  │                 │ Approved                           │
                  │                 ▼                                     │
                  │     ┌────────────────────────┐                       │
                  │     │     EXECUTOR           │──> ATL Log Entry      │
  Output          │     │ (Execute + log)        │                       │
  (Response)  <───│     └────────────────────────┘                       │
                  │                                                        │
                  └────────────────────────────────────────────────────────┘
```

---

## 8. Data Dictionary

### 8.1 Webhook Event Schema

| Field | Type | Required | Description | Example |
|-------|------|----------|-------------|---------|
| event_id | UUID | Yes | Unique event identifier | "a1b2c3d4-..." |
| event_type | Enum | Yes | Type of change | "ticket_updated", "ticket_created", "risk_created" |
| entity_type | Enum | Yes | Type of entity changed | "ticket", "epic", "user", "sprint" |
| entity_id | String | Yes | ID of the changed entity | "TICKET-789" |
| changed_fields | Object | Yes | Fields that changed with old/new values | {"status": {"old": "In Progress", "new": "Blocked"}} |
| timestamp | ISO 8601 | Yes | When the change occurred | "2026-03-15T14:00:00Z" |
| source | String | Yes | Origin of the change | "chaos_engine", "user_action", "system" |
| metadata | Object | No | Additional context | {"triggered_by": "chaos_rule_3"} |

### 8.2 Agent State Schema

| Field | Type | Description |
|-------|------|-------------|
| session_id | UUID | Unique session identifier |
| input | String | Original user query or webhook event |
| input_type | Enum | STATUS_QUERY, RISK_ALERT, ACTION_REQUEST, GENERAL |
| graph_results | List | Results from Neo4j Cypher queries |
| vector_results | List | Results from ChromaDB semantic search |
| draft_response | String | Generated response text |
| citations | List | Source entity IDs referenced in response |
| confidence | Float | Confidence score (0.0 – 1.0) |
| requires_approval | Boolean | Whether Human Gate is needed |
| approval_status | Enum | PENDING, APPROVED, REJECTED, NOT_REQUIRED |
| atl_entry_id | UUID | Reference to ATL log entry |
| error | String | Error message if workflow failed |

### 8.3 ATL Entry Schema

| Field | Type | Description |
|-------|------|-------------|
| entry_id | UUID | Unique ATL entry identifier |
| timestamp | ISO 8601 | When the action was taken |
| action_type | Enum | QUERY_RESPONSE, RISK_ALERT, ESCALATION, SYSTEM_EVENT |
| agent_node | String | Which agent node performed the action |
| input_summary | String | Summarized input that triggered this action |
| decision_rationale | String | Why the agent made this decision |
| output_summary | String | What the agent produced |
| approval_status | Enum | APPROVED, REJECTED, AUTO_APPROVED, PENDING |
| approved_by | String | User who approved (if applicable) |
| processing_time_ms | Integer | End-to-end processing time in milliseconds |

---

## 9. Requirements Traceability Matrix

| Requirement ID | Use Case | Test Case ID | Test Description | Priority |
|---------------|----------|-------------|------------------|----------|
| FR-01.1 | UC-02, UC-03 | TC-SIM-001 | Verify Mock Jira API responds to all CRUD operations | HIGH |
| FR-01.3 | UC-02, UC-03 | TC-SIM-002 | Verify Chaos Engine injects events on schedule | HIGH |
| FR-01.5 | UC-02 | TC-SIM-003 | Verify webhook fires within 2 seconds of state change | HIGH |
| FR-02.1 | UC-01, UC-02 | TC-ING-001 | Verify ingestion endpoint accepts valid webhook payloads | HIGH |
| FR-02.5 | UC-02 | TC-ING-002 | Verify processing completes within 30 seconds | HIGH |
| FR-03.1 | UC-01, UC-04 | TC-GRA-001 | Verify all node types created in Neo4j | HIGH |
| FR-03.3 | UC-04, UC-05 | TC-GRA-002 | Verify Cypher queries return correct results | HIGH |
| FR-04.1 | UC-01 | TC-VEC-001 | Verify ChromaDB collections created and populated | HIGH |
| FR-04.4 | UC-01 | TC-VEC-002 | Verify semantic search returns relevant results | HIGH |
| FR-05.1 | UC-01, UC-02 | TC-AGT-001 | Verify LangGraph state machine executes all nodes | HIGH |
| FR-05.2 | UC-01 | TC-AGT-002 | Verify Planner correctly classifies query types | HIGH |
| FR-05.6 | UC-02 | TC-AGT-003 | Verify Human Gate pauses for RISK_ALERT | HIGH |
| FR-05.8 | UC-01 | TC-AGT-004 | Verify no response contains uncited information | HIGH |
| FR-06.1 | UC-01, UC-04 | TC-UI-001 | Verify chat interface accepts and displays queries | HIGH |
| FR-07.1 | UC-02 | TC-RSK-001 | Verify blocked ticket detected within 60 seconds | HIGH |
| FR-07.2 | UC-02 | TC-RSK-002 | Verify risk severity classification accuracy | HIGH |
| FR-07.4 | UC-05 | TC-RSK-003 | Verify dependency cycle detection | MEDIUM |
| FR-08.1 | UC-01, UC-02 | TC-ATL-001 | Verify ATL entries created for all agent actions | HIGH |
| FR-09.1 | UC-01 | TC-DSH-001 | Verify dashboard displays RAG indicators | HIGH |
| FR-09.3 | UC-03 | TC-DSH-002 | Verify God Mode triggers chaos events | MEDIUM |
| NFR-01.1 | UC-01 | TC-PRF-001 | Verify query response < 5 seconds (P95) | HIGH |
| NFR-01.3 | UC-02 | TC-PRF-002 | Verify risk detection < 60 seconds | HIGH |
| NFR-02.3 | UC-01 | TC-PRF-003 | Verify 0% hallucination on 100-response audit | HIGH |
| NFR-03.1 | All | TC-SEC-001 | Verify zero external network calls in demo mode; only Gemini API calls in dev mode | HIGH |
| NFR-04.1 | All | TC-DEP-001 | Verify single docker-compose up deployment | HIGH |

---

## 10. Acceptance Criteria Summary

| # | Criterion | Pass Condition |
|---|-----------|---------------|
| 1 | The system starts with a single `docker-compose up -d` command | All 7 services reach "healthy" status within 3 minutes |
| 2 | The simulator generates realistic enterprise data on startup | SQLite contains ≥ 200 tickets across ≥ 3 projects |
| 3 | Chaos events trigger webhook delivery to Athena | ≥ 99% of chaos events produce a received webhook |
| 4 | User can query program status via chat | System responds with cited, accurate answer in < 5 seconds |
| 5 | System detects blocked critical tickets proactively | Detection occurs within 60 seconds of blocking event |
| 6 | Agent never fabricates data | 100% of factual claims in responses are backed by Neo4j/ChromaDB data |
| 7 | Sensitive actions require human approval | No alert or escalation bypasses the Human Gate |
| 8 | Complete audit trail exists | Every agent action has a corresponding ATL entry |
| 9 | System works in air-gapped mode (demo) | Set `LLM_BACKEND=ollama`, disconnect internet, full demo runs offline |
| 10 | Dashboard displays real-time health | RAG indicators update within 30 seconds of state change |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-02-05 | Team Athena | Initial requirements specification |
| 0.2.0 | 2026-02-19 | Team Athena | Comprehensive SRS with detailed FR/NFR, 5 use cases with sequence diagrams, DFDs, data dictionary, traceability matrix, acceptance criteria |
| 0.2.1 | 2026-02-20 | Team Athena | Updated for hybrid dual-mode LLM architecture: LLMProvider abstraction, Gemini (dev) + Ollama (demo), hardware specs updated to actual development machine |
