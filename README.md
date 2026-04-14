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

<div align="center">
<i>Built with ❤️ by Team Athena</i>
</div>
