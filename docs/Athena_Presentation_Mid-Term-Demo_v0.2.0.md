# Mid-Term Evaluation Presentation

**Project:** Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation  
**Team:** 1MS22CS012 (Aditya G S), 1MS22CS039 (Deepak B P), 1MS22CS045 (Chandan H K), 1MS22CS054 (Gaurav Kumar)  
**Guide:** [Guide Name]  
**Date:** April 2026

---

## Slide 1 — Title Slide

**Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation**

Department of Computer Science & Engineering  
RNS Institute of Technology, Bengaluru

Team Members:
- Aditya G S (1MS22CS012)
- Deepak B P (1MS22CS039)
- Chandan H K (1MS22CS045)
- Gaurav Kumar (1MS22CS054)

Guide: [Guide Name]  
Academic Year: 2025–2026

---

## Slide 2 — Introduction

**What is Athena?**

An AI-powered autonomous Program Management Office (PMO) assistant that:
- **Ingests** enterprise project data in real-time via webhooks
- **Synthesizes** data into a Knowledge Graph (Neo4j) + Vector Store (Pinecone)
- **Reasons** using a multi-agent LangGraph state machine
- **Detects** risks proactively — sub-60-second detection vs. 2–3 day manual lag
- **Alerts** stakeholders with human-in-the-loop approval

**Dual-Architecture Design:**
- **Project Universe** — High-fidelity enterprise simulator (data source)
- **Athena Core** — Multi-agent reasoning engine (intelligence)
- **Dashboard** — Real-time Next.js 14 UI (presentation)

---

## Slide 3 — Problem Statement

**The Problem:**
- Program Managers spend **10–15 hours/week** manually aggregating data across Jira, Azure DevOps, Confluence
- Risks discovered **2–3 days after** they escalate — by then, damage is done
- No existing tool combines real-time monitoring + autonomous reasoning + human governance

**Why Current Tools Fail:**

| Limitation | Impact |
|-----------|--------|
| Jira/Azure DevOps are passive data stores | No proactive risk detection |
| Dashboards show data, don't reason | No root-cause analysis |
| AI tools use cloud-only LLMs | No data sovereignty / offline mode |
| No human-in-the-loop governance | Trust gap for enterprise adoption |

---

## Slide 4 — Objectives

| # | Objective | Status |
|---|-----------|--------|
| 1 | Build a live enterprise simulator with Mock Jira API, Chaos Engine, and Webhook Dispatcher | ✅ Complete |
| 2 | Ingest webhook events into a dual-store GraphRAG architecture (Neo4j + Pinecone) | ✅ Complete |
| 3 | Implement a 6-node LangGraph multi-agent state machine with 15 tools | 🔲 Pending |
| 4 | Support triple-mode LLM (Gemini, Groq, Ollama) via pluggable `LLMProvider` | ✅ Partial (Groq + Pinecone Inference done) |
| 5 | Build a real-time Next.js 14 dashboard with Chat UI, Health Panel, God Mode | 🔲 Pending |

**Mid-Term Progress: 2 of 4 major subsystems fully implemented and verified.**

---

## Slide 5 — Literature Survey

**15 papers reviewed (2020–2025) across 5 domains:**

| # | Key Paper | Year | Relevance to Athena |
|---|-----------|------|---------------------|
| 1 | Wang et al. — LLM-based Autonomous Agents Survey | 2024 | Validates agent architecture; highlights memory/hallucination challenges |
| 2 | Gao et al. — RAG Survey | 2024 | Informs dual-store approach (graph + vector) |
| 3 | Edge et al. — GraphRAG | 2024 | Foundational to Neo4j + Pinecone knowledge architecture |
| 4 | Hong et al. — MetaGPT | 2023 | Influenced role-based agent specialization |
| 5 | Zhang et al. — AI-Driven Risk Assessment | 2024 | Directly influenced risk detection pipeline |

**5 Research Gaps Identified:**
1. No integrated Multi-Agent + GraphRAG for PM
2. No privacy-first dual-mode AI agent deployments
3. Limited real-time proactive risk detection in AI-driven PM
4. No high-fidelity enterprise simulation for agent testing
5. Insufficient human-in-the-loop governance

---

## Slide 6 — Software Requirement Specifications

**Functional Requirements (9 groups, 40+ sub-requirements):**

| FR | Capability | Priority |
|----|-----------|----------|
| FR-01 | Enterprise Simulation — Mock Jira API + Chaos Engine + Webhooks | HIGH |
| FR-02 | Data Ingestion — Webhook pipeline with validation and deduplication | HIGH |
| FR-03 | Knowledge Graph — 7 node types, 8 relationships in Neo4j | HIGH |
| FR-04 | Vector Store — Semantic search in Pinecone (1024-dim) | HIGH |
| FR-05 | Multi-Agent Reasoning — 6-node LangGraph state machine, 15 tools | HIGH |
| FR-06 | Risk Detection — BLOCKED/overload/cycle detection within 60s | HIGH |
| FR-07 | Dashboard — RAG indicators, Chat UI, God Mode | HIGH |

**Non-Functional Requirements:**

| NFR | Target |
|-----|--------|
| Query response | < 5s (P95) |
| Risk detection | < 60s end-to-end |
| Hallucination rate | 0% (citation-backed) |
| Air-gapped mode | 100% local processing |

**H/W:** Intel i5-13450HX, 16 GB DDR5, RTX 3050 6GB  
**S/W:** Python 3.11, FastAPI, LangGraph, Neo4j, Pinecone, Next.js 14, Docker

---

## Slide 7 — System Design

**Architecture:** Layered Microservices (4 tiers) — Presentation, Application, Data, Inference

*(Refer to: Layered Architecture Diagram — Athena_HLD_v0.3.0, Section 2.1)*

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| Dual-Architecture (Simulator + Agent) | Production portability — agent works on real Jira without code changes |
| Event-Driven (Webhooks) | Mirrors real enterprise integrations; no polling |
| GraphRAG (Neo4j + Pinecone) | Relationship-aware reasoning + semantic search = zero hallucination |
| Triple-Mode LLM | Dev (Gemini), Fast (Groq), Offline (Ollama) — one abstraction |
| Human-in-the-Loop | Human Gate node ensures no autonomous action without approval |

**Agent Tools:** 10 Jira Integration Tools (from production TOOL_CONFIG) + 5 Internal Knowledge Tools

*(Refer to: Data Flow Diagrams — Athena_HLD_v0.3.0, Sections 3.1–3.3)*  
*(Refer to: Class Diagrams — Athena_HLD_v0.3.0, Sections 5.1–5.2)*  
*(Refer to: Sequence Diagrams — Athena_HLD_v0.3.0, Sections 6.1–6.3)*

---

## Slide 8 — Implementation (Simulator)

**Phase 3.2 — Project Universe Simulator** ✅

| Module | File | Lines | Key Feature |
|--------|------|-------|-------------|
| Mock Jira API | `api.py` | 355 | 10 TOOL_CONFIG endpoints + CRUD + God Mode |
| AI Data Generator | `data_gen.py` | 138 | Groq dual-model (70B structural, 8B batch) |
| Timeline Simulator | `timeline_sim.py` | 302 | 12 months, 26 sprints, FK-ordered commits |
| Chaos Engine | `chaos_engine.py` | 142 | 3 fault patterns with LLM-generated comments |
| Webhook Dispatcher | `webhook.py` | 79 | Real-time + historical replay |
| Database ORM | `database.py` | 185 | 8 SQLAlchemy models, Neon Postgres |

**Data Generated:**
- 20 AI-generated users, 1 project, 3 epics, 26 sprints
- **279 stories** — zero placeholder titles
- **965 comments** — avg 325 chars, realistic engineer commentary
- **1,778 audit logs** — full entity lifecycle tracking
- **Zero data integrity violations** — all FK and uniqueness checks pass

---

## Slide 9 — Implementation (GraphRAG Pipeline)

**Phase 3.3 — Data Ingestion & GraphRAG Pipeline** ✅

| Module | File | Lines | Key Feature |
|--------|------|-------|-------------|
| Ingestion Pipeline | `ingestion.py` | 198 | 4-step: Validate → Dedup → Route → Risk Detect |
| Graph Syncer | `graph_syncer.py` | 230 | MERGE handlers for 7 node types in Neo4j |
| Vector Indexer | `vector_indexer.py` | 225 | Pinecone Inference (multilingual-e5-large, 1024-dim) |
| Historical Backfill | `backfill.py` | 183 | Fetch-then-close for Neon SSL resilience |
| Athena Core API | `api.py` | 153 | 6 endpoints (webhook, health, metrics, risks, graph, vector) |

**Knowledge Stores Populated:**
- **Neo4j Aura:** 1,305 nodes (20 Users + 1 Project + 3 Epics + 26 Sprints + 279 Tasks + 964 Comments + 12 Risks)
- **Pinecone:** 1,247 vectors (279 stories + 965 comments + 3 epics)
- **12 risk events** auto-detected for BLOCKED tickets during backfill
- All operations idempotent (MERGE + upsert) — safe to replay

---

## Slide 10 — Challenges and Solutions

| Challenge | Solution |
|-----------|----------|
| Circular FK (Team↔User) | `use_alter=True` — SQLAlchemy generates `ALTER TABLE` |
| Neon SSL timeout during backfill | Fetch-then-close: fetch all rows → close DB → process cloud services |
| Groq rate limits (30 RPM) | Dual-model rotation (70B + 8B) + exponential backoff |
| LLM generating invalid JSON | Markdown fence stripping + retry with fallback prompts |
| Neo4j Aura free tier auto-pause | Driver automatic retry handles 60s cold-start |
| No embedding model in Groq | Used Pinecone's built-in Inference API (zero external deps) |

**Cloud Service Utilization (all within free tier):**

| Service | Used | Limit | Utilization |
|---------|------|-------|-------------|
| Neon Postgres | 9 MB | 512 MB | 1.8% |
| Neo4j Aura | 1,305 nodes | 50,000 | 2.6% |
| Pinecone | 1,247 vectors | 100,000 | 1.2% |

---

## Slide 11 — Conclusion and Future Work

**Accomplished (Mid-Term):**
- ✅ Literature survey — 15 papers, 5 research gaps identified
- ✅ SRS — 9 FR groups, 8 NFRs, 5 use cases, traceability matrix
- ✅ System Design — 5-layer architecture, 14 UML classes, 3 sequence diagrams
- ✅ **Simulator** — 279 stories, 965 comments, 1,778 audit logs, zero placeholders
- ✅ **GraphRAG Pipeline** — 1,305 graph nodes, 1,247 vectors, 12 auto-detected risks

**Remaining (Final Submission):**
- 🔲 Agent Brain — 6-node LangGraph state machine with 15 tools
- 🔲 Dashboard — Next.js 14 with Chat UI, Health Panel, God Mode Console
- 🔲 Integration Testing — End-to-end chaos→detection→alert under 60 seconds
- 🔲 Air-gapped demo mode — Ollama + Llama 3 8B Q4

---

## Slide 12 — References

[1] Wang et al., "LLM-based Autonomous Agents Survey," *Frontiers of CS*, 2024.  
[2] Gao et al., "RAG for LLMs: A Survey," arXiv, 2024.  
[3] Edge et al., "GraphRAG: Query-Focused Summarization," arXiv, 2024.  
[4] Hong et al., "MetaGPT: Multi-Agent Framework," *ICLR*, 2024.  
[5] Xi et al., "Rise and Potential of LLM-Based Agents," arXiv, 2023.  
[6] Pan et al., "Unifying LLMs and Knowledge Graphs," *IEEE TKDE*, 2024.  
[7] Touvron et al., "Llama 2: Open Foundation Models," arXiv, 2023.  
[8] Lewis et al., "RAG for Knowledge-Intensive NLP," *NeurIPS*, 2020.  
[9] Qian et al., "ChatDev: Communicative Agents," *ACL*, 2024.  
[10] Wu et al., "AutoGen: Multi-Agent Conversation," arXiv, 2023.  
[11–15] Additional papers on KG-GNN, LLM Reasoning, Knowledge Distillation, AI Risk Assessment, Edge Deployment.

---

**Thank You**

*Demo available: Simulator API running on localhost:8000 with live data*  
*Neo4j Aura and Pinecone populated with 1,305 nodes and 1,247 vectors*

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-03-17 | Team Athena | Initial mid-term presentation (12 slides) |
| 0.2.0 | 2026-04-03 | Team Athena | Updated for mid-term demo with implementation results |
