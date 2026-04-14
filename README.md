<div align="center">

# 🏛️ Project Athena

### Autonomous Multi-Agent Framework for Real-Time Program Management & Proactive Risk Mitigation

[![Status](https://img.shields.io/badge/Status-In%20Development-yellow)]()
[![License](https://img.shields.io/badge/License-Academic-blue)]()
[![LLM](https://img.shields.io/badge/LLM-Dual%20Mode-purple)]()

*An AI-powered Program Management Office (PMO) assistant that autonomously ingests enterprise data, synthesizes knowledge, and proactively detects risks — before they become blockers.*

</div>

---

## 🎯 Problem

Program Managers spend **10–15 hours/week** manually aggregating data across Jira, Azure DevOps, Confluence, and Slack. By the time status reports are compiled, they're already outdated. Existing AI tools automate narrow tasks but fail to provide holistic, real-time program intelligence.

## 💡 Solution

Athena deploys a team of **autonomous AI agents** (orchestrated via LangGraph) that continuously ingest project data, build a living knowledge graph, and surface risks proactively — all through natural language interaction.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Next.js 14 Dashboard                 │
│              (Chat Interface + God Mode Console)        │
└──────────────────────────┬──────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │   FastAPI   │
                    │  Orchestrator│
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────┴─────┐   ┌─────┴─────┐   ┌─────┴─────┐
    │ LangGraph │   │   Neo4j   │   │ ChromaDB  │
    │  Agents   │   │  (Graph)  │   │ (Vectors) │
    └─────┬─────┘   └───────────┘   └───────────┘
          │
    ┌─────┴─────┐
    │LLMProvider│
    ├───────────┤
    │ Gemini    │  ← Dev Mode (cloud, free tier)
    │ Ollama    │  ← Demo Mode (local, air-gapped)
    └───────────┘
```

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Agent Orchestration | LangGraph | Multi-agent workflow (Ingestion → Synthesis → Risk → Communication) |
| Knowledge Graph | Neo4j CE | Structured entity relationships & multi-hop reasoning |
| Vector Store | ChromaDB | Semantic search over unstructured text |
| LLM (Dev) | Google Gemini 1.5 Flash | Cloud inference via free tier API |
| LLM (Demo) | Ollama + Llama 3 8B Q4 | Local air-gapped inference |
| Simulator | Project Universe | Enterprise simulator with Chaos Engine (5 fault types) |
| Frontend | Next.js 14 | Real-time dashboard with chat interface |
| API Layer | FastAPI | REST API + WebSocket orchestration |

### Dual-Mode LLM Architecture

Athena uses a pluggable **`LLMProvider`** abstraction that decouples agent logic from any specific LLM backend:

| Mode | Backend | RAM | Network | Use Case |
|------|---------|-----|---------|----------|
| `LLM_BACKEND=gemini` | Gemini 1.5 Flash | ~7 GB | Internet | Day-to-day development |
| `LLM_BACKEND=ollama` | Ollama + Llama 3 8B | ~12 GB | Localhost only | Air-gapped demos |

---

## 🤖 Agent Pipeline

```
Webhook Event → Ingestion Agent → Knowledge Store (Neo4j + ChromaDB)
                                         ↓
                                  Synthesis Agent → Unified Context
                                         ↓
                                     Risk Agent → Anomaly Detection
                                         ↓
                                Communication Agent → Draft Alert
                                         ↓
                                  Human Approval → Stakeholder Notification
```

**Four Specialized Agents:**
1. **Ingestion Agent** — Normalizes data from Jira/Azure DevOps webhooks into the knowledge graph
2. **Synthesis Agent** — Queries Neo4j (Cypher) + ChromaDB (semantic search) for unified context
3. **Risk Agent** — Detects blockers, overdue milestones, and anomalies via graph traversal
4. **Communication Agent** — Drafts stakeholder alerts with citations, pending human approval

---

## 🧪 Project Universe (Enterprise Simulator)

Since real enterprise access isn't available in an academic setting, Athena includes **Project Universe** — a high-fidelity simulator:

- **Jira-Sim API** — Simulates Jira Cloud REST API with realistic project data
- **Chaos Engine** — Injects 5 fault types (blocked tickets, milestone slippage, team reassignment, priority escalation, dependency failures)
- **Webhook Dispatcher** — Pushes real-time events to Athena's ingestion pipeline

---

## 🖥️ Hardware Requirements

| Component | Dev Mode | Demo Mode (Air-Gapped) |
|-----------|----------|----------------------|
| RAM | 8 GB+ | 16 GB |
| GPU | Not required | RTX 3050+ (6 GB VRAM) |
| Storage | 30 GB | 50 GB |
| Network | Internet | Localhost only |

**Developed on:** Lenovo LOQ — i5-13450HX, 16 GB DDR5, RTX 3050 6 GB

---

## 📂 Documentation

All project documents are in the [`docs/`](docs/) directory:

| Document | Description |
|----------|-------------|
| [Synopsis](docs/Athena_Synopsis_Zeroeth-Review_v0.2.0.md) | Project overview, objectives, and expected outcomes |
| [SRS](docs/Athena_SRS_Functional-Requirements_v0.2.0.md) | Functional & non-functional requirements, use cases |
| [HLD](docs/Athena_HLD_System-Architecture_v0.2.0.md) | C4 architecture, deployment topology, security model |
| [DDD](docs/Athena_DDD_Database-Schema_v0.1.0.md) | Database schemas (SQLite, Neo4j, ChromaDB) |
| [Literature Survey](docs/Athena_Literature-Survey_Research-Review_v0.1.0.md) | Review of 15 research papers |
| [Feasibility Study](docs/Athena_Feasibility-Study_Technical-Analysis_v0.1.0.md) | Technical, economic, and operational analysis |
| [Project Plan](docs/Athena_Project-Plan_Detailed-Schedule_v0.1.0.md) | SDLC phases and Gantt chart |
| [Project Report](docs/Athena_Project-Report_Initial-Phase_v0.1.0.md) | Initial phase report |
| [Research Domain](docs/Athena_Research_Domain-Analysis_v0.1.0.md) | Domain analysis and technology selection |

---

## 🛠️ Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Languages** | Python 3.11, TypeScript |
| **Agent Framework** | LangGraph |
| **LLM (Dev)** | Google Gemini 1.5 Flash (free tier) |
| **LLM (Demo)** | Ollama + Llama 3 8B Q4 |
| **Databases** | SQLite, Neo4j CE, ChromaDB |
| **Backend** | FastAPI |
| **Frontend** | Next.js 14 |
| **DevOps** | Docker, Docker Compose |

---

## 📊 Performance Targets

| Metric | Target |
|--------|--------|
| Query Response | < 5 seconds |
| Risk Detection | < 60 seconds |
| Blocker Identification | ≥ 95% detection |
| Offline Capability | 100% (demo mode) |
| Hallucination Rate | 0% (citation-backed) |

---

## 📄 License

This is an academic project developed as part of the 8th semester curriculum. All third-party components use open-source licenses (MIT, Apache 2.0, GPL v3, Llama 3 License).

---

---

## 🚀 Getting Started — How to Run Athena Locally

This section covers the complete local setup from scratch. You will run **3 services** simultaneously.

---

### Prerequisites

Make sure you have the following installed:

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | Any | `git --version` |

You also need **cloud service accounts** (all free tiers):

| Service | Purpose | Sign Up |
|---------|---------|---------|
| [Groq](https://console.groq.com) | LLM inference (Llama 3.3 70B) | Free |
| [Neo4j Aura](https://console.neo4j.io) | Knowledge graph | Free tier |
| [Pinecone](https://app.pinecone.io) | Vector store | Free tier |
| [Neon](https://console.neon.tech) | Serverless Postgres | Free tier |

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/chandanhk304/Athena.git
cd Athena
```

---

### Step 2 — Create and Activate the Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS:**
```bash
python -m venv venv
source venv/bin/activate
```

You should see `(venv)` at the start of your terminal prompt.

---

### Step 3 — Install Python Dependencies

```powershell
pip install -e .
```

> This installs all packages defined in `pyproject.toml`, including LangGraph, FastAPI, Neo4j driver, Pinecone, langchain-groq, SQLAlchemy, and more.

---

### Step 4 — Configure Environment Variables

Create a `.env` file in the project root (copy from the example):

```powershell
copy .env.example .env
```

Open `.env` and fill in your credentials:

```env
# ── LLM ──────────────────────────────────────────────
GROQ_API_KEY=gsk_...              # From console.groq.com → API Keys

# ── Neo4j Aura (Knowledge Graph) ─────────────────────
NEO4J_URI=neo4j+s://xxxxxxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here

# ── Pinecone (Vector Store) ───────────────────────────
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX=athena-pmo         # Index name you created

# ── Neon Postgres (Simulator Database) ───────────────
DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

# ── Service URLs (defaults — do not change unless ports conflict) ──
SIMULATOR_API_URL=http://localhost:8000/api/v1
ATHENA_CORE_URL=http://localhost:8001/api/v1
```

> ⚠️ **Never commit your `.env` file.** It is already excluded by `.gitignore`.

---

### Step 5 — Verify Neo4j Instance is Active

Athena uses Neo4j Aura Free. **Free instances pause after 3 days of inactivity.**

1. Go to [console.neo4j.io](https://console.neo4j.io)
2. Click **Resume** on your instance if it shows "Paused"
3. Wait ~60 seconds for it to start

---

### Step 6 — Seed the Simulator Database

> **Skip this step if the database is already seeded** (i.e., you've run it before on the same Neon instance).

```powershell
python -m simulator.timeline_sim
```

This generates:
- 20 AI-invented employees
- 1 enterprise software project with epics and sprints
- 12 months of sprint history with tickets, comments, and blockers

To wipe and regenerate all data from scratch:
```powershell
python -m simulator.timeline_sim --reset
```

---

### Step 7 — Backfill Knowledge Stores (Neo4j + Pinecone)

> **Skip this step if you've already backfilled** (Neo4j has 1300+ nodes, Pinecone has 1200+ vectors).

```powershell
python -m athena_core.backfill
```

This pulls all stories from the simulator and indexes them into:
- **Neo4j** — as a knowledge graph (Tasks, Users, Epics, Sprints, Risks)
- **Pinecone** — as semantic vector embeddings for AI search

---

### Step 8 — Run All 3 Services

Open **3 separate terminal windows** (all with venv activated for terminals 1 & 2):

**Terminal 1 — Jira Simulator API (port 8000)**
```powershell
cd Athena
venv\Scripts\activate
uvicorn simulator.api:app --port 8000 --reload
```
> ✅ Ready when you see: `Application startup complete.`

**Terminal 2 — Athena Core / Agent Brain API (port 8001)**
```powershell
cd Athena
venv\Scripts\activate
uvicorn athena_core.api:app --port 8001 --reload
```
> ✅ Ready when you see: `Neo4j schema initialized` and `Application startup complete.`

**Terminal 3 — Frontend Dashboard (port 3000)**
```powershell
cd Athena/frontend
npm install          # Only needed first time
npm run dev
```
> ✅ Ready when you see: `✓ Ready in XXXms`

---

### Step 9 — Open the Dashboard

Navigate to **[http://localhost:3000](http://localhost:3000)** in your browser.

You should see:
- 🟢 **Agent Brain** — Online (top nav)
- 🟢 **Simulator** — Online (top nav)
- 📊 **Metrics panel** — showing ~1,300 Neo4j nodes and ~1,247 Pinecone vectors
- 💬 **Chat panel** — ready to accept queries
- ⚠️ **Risk Feed** — showing blocked tickets auto-detected from the simulator

---

### Step 10 — Verify Everything Works (Optional)

Run the full 22-point verification script:

```powershell
# From the project root, with venv active and both APIs running:
python agent_brain\verify_agent.py
```

Expected output: **22/22 checks passed ✅**

---

### 💬 Example Queries to Try

Once the dashboard is open, type these into the AI Chat:

```
What are the blocked tickets?
```
```
Show me the current sprint status.
```
```
Which epics have the most risk?
```
```
Summarize the project health.
```

---

### 🩺 Troubleshooting

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| `NEO4J_URI` DNS error | Neo4j Aura instance is paused | Resume it at [console.neo4j.io](https://console.neo4j.io) |
| `ModuleNotFoundError` | venv not activated | Run `venv\Scripts\activate` |
| Port 3000 in use | Another process running | Run `npx kill-port 3000` then retry |
| `404` on `/api/v1/issues/search` | Old simulator API version | Pull latest + restart simulator |
| Pinecone returns 0 vectors | Index not seeded | Run `python -m athena_core.backfill` |
| Chat returns "not available" | Simulator not running | Start Terminal 1 (port 8000) |
| `langchain_groq` import error | Dependency missing | Run `pip install langchain-groq` |

---

### 📁 Project Structure

```
Athena/
├── agent_brain/          # Phase 4: LangGraph multi-agent system
│   ├── graph.py          # StateGraph with MemorySaver checkpointer
│   ├── nodes.py          # 7 agent nodes (Router → Planner → ... → Executor)
│   ├── tools.py          # 15 tools (Jira read/write, Neo4j, Pinecone, ATL)
│   ├── state.py          # AgentState TypedDict + ATL Pydantic schemas
│   └── verify_agent.py   # 22-point end-to-end verification script
│
├── athena_core/          # Phase 2-3: Ingestion pipeline + Core API
│   ├── api.py            # FastAPI app (webhook, query, ATL, approval endpoints)
│   ├── graph_syncer.py   # Neo4j sync (Cypher graph builder)
│   ├── vector_indexer.py # Pinecone vector embeddings
│   ├── risk_detector.py  # Risk event detection
│   └── backfill.py       # One-time historical data seeder
│
├── simulator/            # Phase 1: Enterprise project simulator
│   ├── api.py            # Jira-compatible FastAPI (15 endpoints)
│   ├── timeline_sim.py   # AI-generated 12-month project history
│   ├── database.py       # SQLAlchemy models (Neon Postgres)
│   └── webhook.py        # Webhook dispatcher for live events
│
├── frontend/             # Phase 5: Next.js 16 dashboard
│   └── src/
│       ├── app/          # Next.js App Router (page, layout, globals.css)
│       ├── components/   # ChatPanel, MetricsPanel, ATLPanel, RiskFeed, TopNav
│       └── lib/          # api.ts (fetch client) + types.ts
│
├── docs/                 # Academic documentation (SRS, HLD, DDD, etc.)
├── .env.example          # Environment variable template
├── pyproject.toml        # Python dependencies
└── README.md             # This file
```

---

<div align="center">
<i>Built with ❤️ by Team Athena</i>
</div>
