# Domain Research Report
**Document ID:** Athena_Research_Domain-Analysis_v0.1.0  
**Date:** 2026-02-05  
**Version:** 0.1.0 (Minor - Core Research Complete)

---

## 1. Executive Summary

This document presents the domain research findings for Project Athena, an Autonomous Multi-Agent Framework for Program Management. The research covers three critical domains: Multi-Agent Frameworks, Enterprise Data Integration, and Knowledge Architectures.

---

## 2. Multi-Agent Framework Analysis

### 2.1 Framework Comparison

| Framework | Vendor | Strengths | Weaknesses | Selection |
|-----------|--------|-----------|------------|-----------|
| LangGraph | LangChain | State management, cyclic flows, human-in-loop | Steeper learning curve | **SELECTED** |
| CrewAI | CrewAI | Role-based teams, easy setup | Limited state control | Rejected |
| AutoGen | Microsoft | Conversational, code execution | Less structured workflows | Rejected |

### 2.2 LangGraph Architecture

```
LANGGRAPH EXECUTION MODEL

                    +----------------+
                    |   USER INPUT   |
                    +-------+--------+
                            |
                            v
                    +-------+--------+
                    |     STATE      |
                    | {query, steps, |
                    |  context, ...} |
                    +-------+--------+
                            |
            +---------------+---------------+
            |               |               |
            v               v               v
    +-------+----+  +-------+----+  +-------+----+
    |   NODE A   |  |   NODE B   |  |   NODE C   |
    |  (Planner) |  | (Researcher)|  | (Responder)|
    +-------+----+  +-------+----+  +-------+----+
            |               |               |
            +---------------+---------------+
                            |
                    +-------+--------+
                    | CONDITIONAL    |
                    | EDGE ROUTING   |
                    +-------+--------+
                            |
                    +-------v--------+
                    |  NEXT STATE    |
                    +----------------+
```

### 2.3 Key LangGraph Features

| Feature | Benefit for Athena |
|---------|-------------------|
| Stateful Graphs | Track program context across interactions |
| Cyclic Execution | Retry failed operations, iterative refinement |
| Checkpointing | Resume from failures, audit trail |
| Human-in-Loop | Approval gates for sensitive actions |
| Tool Integration | Connect to Neo4j, ChromaDB, external APIs |

---

## 3. Enterprise Data Integration

### 3.1 PMO Tool Analysis

| Tool | API Type | Webhook Support | Rate Limits |
|------|----------|-----------------|-------------|
| Jira Cloud | REST v3 | Yes (async) | 100 req/sec |
| Azure DevOps | REST + GraphQL | Yes (Service Hooks) | 200x typical user |
| Asana | REST | Yes | 1500 req/min |
| ServiceNow | REST + SOAP | Yes | Varies |

### 3.2 Webhook Event Model

```
ENTERPRISE WEBHOOK FLOW

+-----------+     +-----------+     +-----------+
|   JIRA    |     |   AZURE   |     |   ASANA   |
|   CLOUD   |     |   DEVOPS  |     |           |
+-----+-----+     +-----+-----+     +-----+-----+
      |                 |                 |
      |                 |                 |
      v                 v                 v
+-----+-----+     +-----+-----+     +-----+-----+
| issue:    |     | workitem: |     | task:     |
| updated   |     | updated   |     | changed   |
+-----------+     +-----------+     +-----------+
      |                 |                 |
      +--------+--------+--------+--------+
               |
               v
       +-------+--------+
       |   ADAPTER      |
       |   LAYER        |
       | (Normalization)|
       +-------+--------+
               |
               v
       +-------+--------+
       |   UNIFIED      |
       |   EVENT        |
       |   {type, id,   |
       |    payload}    |
       +----------------+
```

### 3.3 Simulation Strategy

Since real enterprise data is unavailable, the project implements a **High-Fidelity Simulator**:

| Component | Simulates | Realism Level |
|-----------|-----------|---------------|
| Jira-Sim API | Jira REST API | HIGH |
| Chaos Engine | Enterprise failures | HIGH |
| Webhook Dispatcher | Real HTTP webhooks | EXACT |
| Audit Log | Change data capture | HIGH |

---

## 4. Knowledge Architecture: GraphRAG

### 4.1 Traditional RAG vs GraphRAG

```
TRADITIONAL RAG                    GRAPHRAG (Selected)

+---------+                        +---------+
|  Query  |                        |  Query  |
+----+----+                        +----+----+
     |                                  |
     v                                  v
+---------+                        +---------+
| Vector  |                        | Vector  |
| Search  |                        | Search  |
+----+----+                        +----+----+
     |                                  |
     v                                  +--------+
+---------+                                      |
|   LLM   |                             +--------v--------+
| (Answer)|                             |   Knowledge     |
+---------+                             |   Graph Query   |
                                        +--------+--------+
LIMITATIONS:                                     |
- No relationships                      +--------v--------+
- Context loss                          |   Merged        |
- Hallucination risk                    |   Context       |
                                        +--------+--------+
                                                 |
                                        +--------v--------+
                                        |      LLM        |
                                        |   (Grounded)    |
                                        +-----------------+

                                        BENEFITS:
                                        + Relationship-aware
                                        + Multi-hop reasoning
                                        + Reduced hallucination
```

### 4.2 GraphRAG Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| Vector Store | ChromaDB | Semantic search on unstructured text |
| Knowledge Graph | Neo4j | Structured relationships between entities |
| LLM | LLMProvider (Gemini or Ollama) | Reasoning and response generation |
| Embeddings | LLMProvider (Gemini or Llama 3) | Text vectorization |

### 4.3 Knowledge Graph Schema

```
ENTITY RELATIONSHIP MODEL

+------------+                              +------------+
|    USER    |                              |    RISK    |
| - email    |                              | - severity |
| - role     |                              | - status   |
+-----+------+                              +-----+------+
      |                                           |
      | [:ASSIGNED_TO]                   [:HAS]   |
      |                                           |
      v                                           v
+-----+------+        [:BLOCKS]           +------+-----+
|    TASK    |<-------------------------->|    TASK    |
| - id       |                            | (Blocked)  |
| - status   |                            +------------+
| - priority |                                   |
+-----+------+                                   |
      |                                          |
      | [:PART_OF]                               | [:IMPACTS]
      |                                          |
      v                                          v
+-----+------+                            +------+-----+
|  MILESTONE |                            |  FEATURE   |
| - deadline |                            | - rag_stat |
| - status   |                            +------------+
+------------+
```

---

## 5. LLM Strategy Analysis

### 5.1 Dual-Mode Rationale

Running a local LLM (Ollama + Llama 3 8B) alongside Neo4j, ChromaDB, and all Docker services simultaneously requires ~12-14 GB RAM. On the development hardware (Lenovo LOQ, 16 GB DDR5 RAM), this leaves zero headroom for IDEs, browsers, and debugging tools. The dual-mode approach solves this:

| Mode | LLM Backend | RAM Footprint | Network | Use Case |
|------|------------|---------------|---------|----------|
| **Development** | Google Gemini 1.5 Flash (free tier) | ~7 GB | Internet (Gemini API) | Day-to-day coding, testing, iteration |
| **Air-Gapped Demo** | Ollama + Llama 3 8B Q4 | ~12 GB | Localhost only | Final demos, privacy-sensitive deployments |

A pluggable `LLMProvider` abstraction (Python abstract class) with `GeminiProvider` and `OllamaProvider` implementations ensures agent logic is completely decoupled from any specific LLM backend. Switching modes requires only changing `LLM_BACKEND=gemini|ollama` in the `.env` file.

### 5.2 Model Comparison

| Model | Parameters | VRAM Required | Quality | Speed |
|-------|------------|---------------|---------|-------|
| **Gemini 1.5 Flash** | N/A (cloud) | 0 GB (API) | Excellent | Fast |
| **Llama 3 8B Q4** | 8B | 6 GB | Good | Fast |
| Llama 3 70B | 70B | 48 GB | Excellent | Slow |
| Mistral 7B | 7B | 8 GB | Good | Fast |
| Qwen 2.5 7B | 7B | 8 GB | Good | Fast |

### 5.3 Recommendation

**Selected: Dual-mode via LLMProvider abstraction**

| Criterion | Dev Mode (Gemini) | Demo Mode (Ollama + Llama 3 8B Q4) |
|-----------|-------------------|---------------------|
| Hardware Fit | No GPU required | Runs on RTX 3050 6GB |
| Reasoning Quality | Excellent | Sufficient for PM queries |
| Tool Use | Supports function calling | Supports function calling |
| Cost | $0 (free tier) | $0 (local) |
| Privacy | Prompts sent to Google | Fully air-gapped |

---

## 6. Security and Privacy Model

### 6.1 Dual-Mode Deployment Architecture

```
DEV MODE DEPLOYMENT BOUNDARY

+================================================================+
||                    LOCAL DOCKER NETWORK                       ||
||                                                               ||
||  +---------------+  +---------------+                         ||
||  | Neo4j         |  | ChromaDB      |                         ||
||  | (Graph)       |  | (Vectors)     |                         ||
||  +---------------+  +---------------+                         ||
||         ^                   ^                                  ||
||         |                   |                                  ||
||         +-------------------+                                  ||
||                    |                                           ||
||           +--------+--------+                                  ||
||           |   Athena Core   |                                  ||
||           |   (FastAPI)     |                                  ||
||           +--------+--------+                                  ||
||                    |                                           ||
+====================|============================================+
                     | LLMProvider → GeminiProvider
                     | (HTTPS to Gemini API)
                     v
              +-------------+
              | Google AI   |
              | Studio API  |
              | (Free Tier) |
              +-------------+


DEMO MODE (AIR-GAPPED) DEPLOYMENT BOUNDARY

+================================================================+
||                    LOCAL DOCKER NETWORK                       ||
||                                                               ||
||  +---------------+  +---------------+  +---------------+      ||
||  | Neo4j         |  | ChromaDB      |  | Ollama        |      ||
||  | (Graph)       |  | (Vectors)     |  | (Llama 3 8B)  |      ||
||  +---------------+  +---------------+  +---------------+      ||
||         ^                   ^                  ^               ||
||         |                   |                  |               ||
||         +-------------------+------------------+               ||
||                             |                                  ||
||                    +--------+--------+                         ||
||                    |   Athena Core   |                         ||
||                    |   (FastAPI)     |                         ||
||                    +--------+--------+                         ||
||                             |                                  ||
+==============================|==================================+
                               |
                        NO EXTERNAL
                        NETWORK ACCESS
                               |
                               X (Blocked)
                               |
                    +----------+----------+
                    |   External APIs     |
                    |   (OpenAI, Jira)    |
                    +---------------------+
```

### 6.2 Privacy Guarantees

| Guarantee | Implementation |
|-----------|----------------|
| Data Sovereignty | All project data stored locally (both modes) |
| No API Leakage (demo mode) | Ollama for fully air-gapped inference |
| Minimal API footprint (dev mode) | Only LLM prompts sent to Gemini API; no project data in prompts |
| Audit Trail | Complete action logging |
| Synthetic Data | No real PII |

---

## 7. Conclusion

The research concludes that:
1. **LangGraph** provides the best control for program management workflows
2. **GraphRAG** enables relationship-aware reasoning critical for PMO use cases
3. **Dual-Mode LLM** eliminates cost barriers (free-tier Gemini + local Ollama) while offering flexible deployment: cloud for agility, local for privacy
4. **High-Fidelity Simulation** demonstrates enterprise capabilities without corporate access

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-02-05 | Team Athena | Initial domain research |
| 0.1.1 | 2026-02-20 | Team Athena | Updated for hybrid dual-mode LLM architecture: LLMProvider abstraction, Gemini (dev) + Ollama (demo), dual-mode deployment diagrams |
