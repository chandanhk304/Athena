# Zeroeth Review PPT Content
## Project: Athena - Autonomous Multi-Agent Framework for Program Management
**Document ID:** Athena_Presentation_Zeroeth-Review_v0.1.0  
**Date:** 2026-02-12  
**Version:** 0.1.0

---

## Slide 1: Problem Statement

- Manual program status reporting consumes ~10 hours/week per Program Manager
- Critical blockers are discovered 2-3 days late on average
- 40% of status meetings are spent reconciling conflicting data from multiple sources
- No unified "Single Source of Truth" exists across project management tools
- Reactive decision-making causes issues to escalate before PMO awareness

---

## Slide 2: Objective & Scope of the Proposed Project

**Objectives:**
1. Build a Multi-Agent System (LangGraph) for real-time program monitoring
2. Implement GraphRAG architecture (Neo4j + ChromaDB) for unified data synthesis
3. Develop a High-Fidelity Enterprise Simulator ("Project Universe")
4. Create human-in-the-loop approval workflows for risk communication
5. Deploy a dual-mode LLM via `LLMProvider` abstraction (Gemini for dev, Ollama + Llama 3 for air-gapped demo)

**Scope:**
- Simulated enterprise data integration via webhooks
- Autonomous risk detection and severity categorization
- Natural language query interface for program status
- Action & Tracking Log (ATL) for audit compliance
- Dashboard visualization of program health

---

## Slide 3: Proposed Methodology

**Model:** Agile-Incremental (2-week sprints)

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Research & Planning | Weeks 1-2 | Domain research, feasibility, SRS |
| System Design | Weeks 3-4 | HLD, database schema, API contracts |
| Development | Weeks 5-8 | Simulator, agent core, dashboard |
| Testing & Verification | Weeks 9-12 | Integration tests, demo, documentation |

---

## Slide 4: Hardware & Software to be used

**Software (Development):**

| Category | Tools |
|----------|-------|
| Languages | Python 3.11, TypeScript |
| Frameworks | FastAPI, LangGraph, Next.js 14 |
| Databases | SQLite, Neo4j CE, ChromaDB |
| AI Runtime (Dev) | Google Gemini 1.5 Flash (free tier) |
| AI Runtime (Demo) | Ollama, Llama 3 (8B Q4) |
| DevOps | Docker, Docker Compose, Git |

**Hardware (Deployment):**

| Component | Specification |
|-----------|---------------|
| Machine | Lenovo LOQ (actual dev hardware) |
| CPU | Intel Core i5-13450HX |
| RAM | 16 GB DDR5 (~7 GB dev / ~12 GB demo) |
| GPU | NVIDIA RTX 3050 6 GB VRAM |
| Storage | 512 GB NVMe |

---

## Slide 5: Expected Outcome of the Proposed Project

| Metric | Target |
|--------|--------|
| Query Response Time | < 5 seconds |
| Risk Detection Latency | < 60 seconds |
| Data Accuracy | Zero hallucination (citation-based) |
| Offline Capability | 100% functional (demo mode) |
| Blocker Identification | 95% detection rate |
| Audit Trail | Complete decision logging |

---

## Slide 6: What contribution to society would the project make?

- **Efficiency:** Frees 10+ hours/week per PM from manual data aggregation
- **Proactive Safety:** Early risk identification prevents project failures
- **Data-Driven Culture:** Real-time accurate information for all stakeholders
- **Privacy-First AI:** Dual-mode deployment — fully air-gapped for demo; minimal API footprint (Gemini free tier) for dev
- **Open-Source Education:** Architecture patterns for AI agent development
- **Knowledge Democratization:** Reduces information gap between teams and leadership

---

## Slide 7: References

[1] LangChain. (2025). *LangGraph: Building Stateful Agents.* https://langchain-ai.github.io/langgraph/

[2] Neo4j Inc. (2025). *Graph Database Fundamentals.* https://neo4j.com/docs/

[3] Meta Platforms. (2024). *Llama 3 Model Card.* https://llama.meta.com/

[4] Ollama Inc. (2025). *Run Llama 3 Locally.* https://ollama.com/

[5] Chroma. (2025). *The AI-native embedding database.* https://www.trychroma.com/

[6] Lewis, P., et al. (2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. *NeurIPS 2020*, 33, 9459-9474.

[7] Touvron, H., et al. (2023). Llama 2: Open Foundation and Fine-Tuned Chat Models. *arXiv:2307.09288*.

[8] IBM Research. (2025). *GraphRAG: Graph-based Retrieval Augmented Generation.* https://ibm.com/docs/graphrag
