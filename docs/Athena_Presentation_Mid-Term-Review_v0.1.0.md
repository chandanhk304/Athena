# Mid-Term Review Presentation
**Document ID:** Athena_Presentation_Mid-Term-Review_v0.1.0  
**Project:** Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation  
**Date:** 2026-03-07  
**Slides:** 12 | **Version:** 0.1.0

---

## Slide 1 — Title Slide

**Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation**

- Department of Computer Science & Engineering
- 8th Semester Project — Academic Year 2025-26
- Team Athena (4 Members)
- Guide: [Guide Name]

---

## Slide 2 — Introduction

- **Domain:** Artificial Intelligence & Multi-Agent Systems
- **What is Athena?** An AI-powered PMO assistant that autonomously monitors enterprise project data, builds a living knowledge graph, and proactively detects risks — all through natural language interaction
- **Dual Architecture:**
    - **Project Universe** — A high-fidelity enterprise simulator (data source)
    - **Athena Core** — A multi-agent reasoning engine (intelligence)
- **Key Innovation:** Combines LangGraph multi-agent orchestration + GraphRAG knowledge synthesis + triple-mode LLM (Gemini / Groq / Ollama)
- Fully containerized (Docker Compose), supports air-gapped offline deployment

---

## Slide 3 — Problem Statement

- Program Managers manually aggregate data across Jira, Azure DevOps, Confluence, and Slack
- **10–15 hours/week** spent compiling status reports that are already outdated by the time they are shared
- Critical blockers (e.g., ticket blocked for 3 days) discovered **2–3 days late** — no continuous monitoring
- **40% of status meetings** wasted reconciling conflicting data from different tools
- Decision-making is **reactive** — leadership learns about risks only after escalation
- **The Gap:** No intelligent system continuously watches all project data, understands relationships between tasks/people/risks, and **proactively alerts** stakeholders before issues escalate

---

## Slide 4 — Objectives

| # | Objective | Deliverable |
|---|-----------|-------------|
| 1 | Design and build a custom Enterprise Simulator ("Project Universe") | FastAPI Mock Jira API + Chaos Engine + Webhook Dispatcher |
| 2 | Build a GraphRAG architecture combining Knowledge Graph + Vector Store | Neo4j (graph) + Pinecone (vectors) with ingestion pipeline |
| 3 | Develop a Multi-Agent Reasoning System using LangGraph | 6-agent state machine (Planner, Researcher, Alerter, Responder, Human Gate, Executor) |
| 4 | Deploy with Triple-Mode LLM Architecture | Gemini (dev) + Groq (fast data-gen) + Ollama (air-gapped demo) via `LLMProvider` abstraction |
| 5 | Build a Dashboard for real-time visualization and interaction | Next.js 14 with Chat UI, Health Dashboard, God Mode Console |

---

## Slide 5 — Literature Survey (Table — Part 1)

| Title & Author(s), Year | Technique Used | Result | Discussion / Future Scope |
|--------------------------|----------------|--------|---------------------------|
| A Survey on LLM-based Autonomous Agents — Wang et al., 2024 | LLM agent architecture with profile, memory, action modules | Comprehensive taxonomy; strong reasoning and planning demonstrated | **Adv:** Unified agent framework. **Dis:** Long-term memory and hallucination remain challenges |
| RAG for Large Language Models: A Survey — Gao et al., 2024 | Naive → Advanced → Modular RAG paradigms; hybrid retrieval | Significantly reduces hallucination; hybrid retrieval achieves best QA performance | **Adv:** Practical optimization guidelines. **Dis:** Increased complexity, retrieval latency overhead |
| GraphRAG: A Graph RAG Approach — Edge et al., 2024 | LLM-generated knowledge graphs + community detection for summarization | 20–25% improvement in comprehensiveness over baseline RAG for global queries | **Adv:** Superior multi-doc synthesis. **Dis:** High compute cost for graph construction |
| MetaGPT: Multi-Agent Collaboration — Hong et al., 2023 | SOPs-based multi-agent framework with role differentiation | Reduced cascading errors by 50%+; coherent multi-file code generation | **Adv:** Human-like workflows. **Dis:** Rigid structure limits adaptability; high token consumption |
| LLM-Based Agents: Rise and Potential — Xi et al., 2023 | Brain-perception-action agent framework | Well-designed interaction patterns improve task completion by 30–40% | **Adv:** Comprehensive taxonomy. **Dis:** Safety/reliability concerns in autonomous decisions |

---

## Slide 6 — Literature Survey (Table — Part 2)

| Title & Author(s), Year | Technique Used | Result | Discussion / Future Scope |
|--------------------------|----------------|--------|---------------------------|
| Unifying LLMs and Knowledge Graphs — Pan et al., 2024 | KG-enhanced LLMs, LLM-augmented KGs, Synergized approaches | Synergized LLM+KG reduces hallucination by 40–60% on knowledge-intensive tasks | **Adv:** Explainable reasoning paths. **Dis:** Complex integration, KG maintenance overhead |
| Llama 2: Open Foundation and Fine-Tuned Models — Touvron et al., 2023 | Pretraining (2T tokens) + SFT + RLHF safety alignment | Competitive with GPT-3.5; fully open-source, local deployment | **Adv:** Open-source, air-gapped capable. **Dis:** Smaller models lag on complex reasoning |
| RAG for Knowledge-Intensive NLP Tasks — Lewis et al., 2020 | Parametric (seq2seq) + Non-parametric (DPR) memory | SOTA on open-domain QA; more factual, diverse generations | **Legacy foundational paper.** Established combining retrieval with generation |
| AutoGen: Multi-Agent Conversation — Wu et al., 2023 | Conversational multi-agent with flexible agent capabilities | Effective across math, coding, debates; human participation improves accuracy 15–20% | **Adv:** Highly flexible. **Dis:** Less structured state management than LangGraph |
| AI-Driven Software Project Risk Assessment — Zhang et al., 2024 | NLP risk extraction + graph dependency analysis | 87% accuracy in early risk identification; 2–3 day earlier detection | **Adv:** Automated, proactive. **Dis:** Relies on cloud APIs; limited risk categories |
| Edge Deployment of Foundation Models — Chen et al., 2024 | 4-bit quantization, model pruning, inference optimization | 7–8B models achieve <5s latency on 16GB RAM; retains 95% FP16 accuracy | **Adv:** Zero API cost, data sovereignty. **Dis:** Reduced quality vs cloud models |

---

## Slide 7 — SRS: Hardware & Software Requirements

### Hardware Requirements

| Component | Dev Mode (Cloud LLM) | Demo Mode (Air-Gapped) |
|-----------|---------------------|------------------------|
| RAM | 8 GB+ | 16 GB |
| GPU | Not required | NVIDIA RTX 3050+ (6 GB VRAM) |
| Storage | 30 GB | 50 GB |
| Network | Internet (API calls) | Localhost only |

**Development Machine:** Lenovo LOQ — i5-13450HX (12C/16T), 16 GB DDR5, RTX 3050 6GB

### Software Requirements

| Category | Technology | Purpose |
|----------|------------|---------|
| Agent Framework | LangGraph ≥ 0.1.0 | Multi-agent state machine orchestration |
| Graph Database | Neo4j Aura (cloud) / CE 5.x (local) | Structured knowledge graph with Cypher queries |
| Vector Database | Pinecone (cloud) / ChromaDB (local) | Semantic similarity search over embeddings |
| Simulator DB | PostgreSQL (Neon serverless) | Relational storage for Mock Jira entities |
| LLM (Dev) | Google Gemini 1.5 Flash API | Cloud inference for development |
| LLM (Fast) | Groq Cloud (Llama 3.3 70B) | High-speed batch data generation |
| LLM (Demo) | Ollama + Llama 3 8B Q4 | Air-gapped local inference |
| Backend | FastAPI + Python 3.11 | REST API + async webhook processing |
| Frontend | Next.js 14 + TypeScript | Dashboard, Chat UI, God Mode Console |
| DevOps | Docker + Docker Compose | Containerized multi-service deployment |

---

## Slide 8 — System Design: HLD — Architecture Diagram

### General Architecture (Layered Microservices)

```
+===========================================================================+
|                  DOCKER COMPOSE NETWORK (athena-network)                   |
+===========================================================================+
|                                                                            |
|  PRESENTATION         APPLICATION           DATA          INFERENCE        |
|  ──────────────       ────────────           ──────        ──────────       |
|  ┌───────────┐       ┌────────────┐      ┌─────────┐   ┌──────────────┐  |
|  │ Next.js   │       │ Jira-Sim   │      │PostgreSQL│   │ LLMProvider  │  |
|  │ Dashboard │       │ API        │      │ (Neon)   │   ├──────────────┤  |
|  │ :3000     │       │ :8000      │      └─────────┘   │ Gemini (Dev) │  |
|  ├───────────┤       ├────────────┤      ┌─────────┐   │ Groq (Fast)  │  |
|  │ Chat UI   │       │ Athena     │      │ Neo4j   │   │ Ollama(Demo) │  |
|  │ Health    │       │ Core API   │      │ Aura    │   └──────────────┘  |
|  │ God Mode  │       │ :8001      │      └─────────┘                     |
|  └───────────┘       ├────────────┤      ┌─────────┐                     |
|                      │ Chaos Eng. │      │Pinecone │                     |
|                      │ (scheduler)│      │ Vectors │                     |
|                      └────────────┘      └─────────┘                     |
+===========================================================================+
```

---

## Slide 9 — System Design: Data Flow Diagram

### Level 1 DFD

```
                    ┌──────────────────────────────────────────┐
                    │              ATHENA SYSTEM                │
                    │                                          │
 Webhook ──────────>│  ┌───────────────┐                      │
 (from Simulator)   │  │ 1.0 INGESTION │                      │
                    │  │ Validate →    │                      │
                    │  │ Deduplicate → │                      │
                    │  │ Route         │                      │
                    │  └───────┬───────┘                      │
                    │    ┌─────┴─────┐                        │
                    │    ▼           ▼                        │
                    │  ┌─────┐  ┌────────┐                   │
                    │  │Neo4j│  │Pinecone│                   │
                    │  └──┬──┘  └───┬────┘                   │
                    │     └────┬────┘                         │
                    │          ▼                              │
 NL Query ─────────>│  ┌───────────────┐                      │
 (from User)        │  │ 2.0 AGENT     │──> LLMProvider      │
                    │  │ BRAIN         │                      │
                    │  │ (LangGraph)   │                      │
                    │  └───────┬───────┘                      │
 <──────────────────│  Cited Response + ATL Log               │
                    └──────────────────────────────────────────┘
```

---

## Slide 10 — System Design: LLD — UML Diagrams

### Sequence Diagram: Chaos Event → Risk Alert

```
 Chaos    Simulator   Athena     Neo4j   Pinecone   LLM    Human    Dashboard
 Engine   API         Core                                  Gate
   │        │           │          │        │         │       │         │
   │ mutate │           │          │        │         │       │         │
   │───────>│           │          │        │         │       │         │
   │        │ webhook   │          │        │         │       │         │
   │        │──────────>│          │        │         │       │         │
   │        │           │ upsert   │        │         │       │         │
   │        │           │─────────>│        │         │       │         │
   │        │           │ embed    │        │         │       │         │
   │        │           │─────────────────>│         │       │         │
   │        │           │ analyze  │        │         │       │         │
   │        │           │─────────────────────────>│       │         │
   │        │           │ hold alert               │       │         │
   │        │           │──────────────────────────────────>│         │
   │        │           │                          │       │ show    │
   │        │           │                          │       │────────>│
   │        │           │          TOTAL AUTO: < 60 seconds           │
```

### Proposed Methodology / Solution — Concept Diagram

```
                    ┌──────────────────────────┐
                    │    PROJECT UNIVERSE       │
                    │    (Enterprise Simulator) │
                    ├──────────────────────────┤
                    │ ┌──────────┐ ┌─────────┐ │
                    │ │ Mock     │ │ Chaos   │ │
                    │ │ Jira API │ │ Engine  │ │
                    │ │ (FastAPI)│ │ (cron)  │ │
                    │ └─────┬────┘ └────┬────┘ │
                    │       └─────┬─────┘      │
                    │             │ Webhook     │
                    └─────────────┼────────────┘
                                  │ HTTP POST
                                  ▼
                    ┌──────────────────────────┐
                    │      ATHENA CORE         │
                    ├──────────────────────────┤
                    │  ┌────────────────────┐  │
                    │  │ Ingestion Pipeline │  │
                    │  └────────┬───────────┘  │
                    │     ┌─────┴─────┐        │
                    │     ▼           ▼        │
                    │  ┌──────┐  ┌────────┐    │
                    │  │Neo4j │  │Pinecone│    │
                    │  │Graph │  │Vectors │    │
                    │  └──┬───┘  └───┬────┘    │
                    │     └────┬─────┘         │
                    │          ▼               │
                    │  ┌───────────────────┐   │
                    │  │  LangGraph Agent  │   │
                    │  │  (6-Node FSM)     │   │
                    │  │                   │   │
                    │  │ Planner →         │   │
                    │  │ Researcher →      │   │
                    │  │ Alerter/Responder│   │
                    │  │ → Human Gate →    │   │
                    │  │ Executor          │   │
                    │  └────────┬──────────┘   │
                    │           ▼              │
                    │  ┌───────────────────┐   │
                    │  │ LLMProvider       │   │
                    │  ├───────────────────┤   │
                    │  │ Gemini  (Dev)     │   │
                    │  │ Groq    (Fast)    │   │
                    │  │ Ollama  (Demo)    │   │
                    │  └───────────────────┘   │
                    └──────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │      DASHBOARD           │
                    ├──────────────────────────┤
                    │ ┌────────┐ ┌───────────┐ │
                    │ │ Chat   │ │ Health    │ │
                    │ │ UI     │ │ Dashboard │ │
                    │ └────────┘ └───────────┘ │
                    │ ┌────────────────────┐   │
                    │ │ God Mode Console   │   │
                    │ └────────────────────┘   │
                    └──────────────────────────┘
```

---

## Slide 11 — Implementation Progress (Mid-Term Status)

| Component | Status | Details |
|-----------|--------|---------|
| **Simulator Database** | ✅ Complete | PostgreSQL (Neon) — 8 ORM models: User, Team, Project, Sprint, Epic, Story, Comment, AuditLog |
| **Jira-Sim API** | ✅ Complete | FastAPI with 15+ CRUD endpoints, audit logging, webhook dispatch on all mutations |
| **Chaos Engine** | ✅ Complete | 3 fault patterns (ticket blocker, developer overload, priority escalation) with LLM-generated comments |
| **Data Generator** | ✅ Complete | Dual-LLM AI data gen (Groq + Gemini) — creates realistic users, projects, stories, comments |
| **Webhook Dispatcher** | ✅ Complete | Jira-compatible webhook schema with `replay_historical_event()` for retroactive graph building |
| **Timeline Simulator** | ✅ Complete | 12-month history generation with AI-batch ticket creation across sprints |
| **Athena Core Agent** | 🔲 Not Started | LangGraph state machine, ingestion pipeline, agent tools |
| **GraphRAG Pipeline** | 🔲 Not Started | Neo4j graph syncer, Pinecone vector indexer |
| **Next.js Dashboard** | 🔲 Not Started | Chat UI, Health Dashboard, God Mode Console |
| **Docker Compose** | 🔨 Partial | Data-tier services defined (Neo4j, ChromaDB, Ollama); application-tier pending |

---

## Slide 12 — References (APA Style)

1. Wang, L., et al. (2024). A survey on large language model based autonomous agents. *Frontiers of Computer Science*, 18(6). https://arxiv.org/abs/2308.11432

2. Gao, Y., et al. (2024). Retrieval-augmented generation for large language models: A survey. *arXiv preprint arXiv:2312.10997*. https://arxiv.org/abs/2312.10997

3. Edge, D., et al. (2024). From local to global: A graph RAG approach to query-focused summarization. *arXiv preprint arXiv:2404.16130*. https://arxiv.org/abs/2404.16130

4. Hong, S., et al. (2024). MetaGPT: Meta programming for a multi-agent collaborative framework. In *Proc. ICLR*, Vienna, Austria.

5. Xi, Z., et al. (2023). The rise and potential of large language model based agents: A survey. *arXiv preprint arXiv:2309.07864*. https://arxiv.org/abs/2309.07864

6. Pan, S., et al. (2024). Unifying large language models and knowledge graphs: A roadmap. *IEEE Transactions on Knowledge and Data Engineering*, 36(7), 3580-3599.

7. Touvron, H., et al. (2023). Llama 2: Open foundation and fine-tuned chat models. *arXiv preprint arXiv:2307.09288*. https://arxiv.org/abs/2307.09288

8. Lewis, P., et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. In *NeurIPS*, 33, 9459-9474.

9. Wu, Q., et al. (2023). AutoGen: Enabling next-gen LLM applications via multi-agent conversation. *arXiv preprint arXiv:2308.08155*. https://arxiv.org/abs/2308.08155

10. Zhang, L., Kumar, R., & Patel, A. (2024). AI-driven software project risk assessment using NLP and graph analysis. In *Proc. IEEE/ACM ASE*, Sacramento, CA, 892-903.

11. Chen, M., Li, S., & Wang, K. (2024). Edge deployment of foundation models for privacy-preserving enterprise AI. In *Proc. AAAI*, Vancouver, Canada, 17891-17899.

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-03-07 | Team Athena | Initial mid-term presentation with 12 slides |
