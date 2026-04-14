# Project Plan & Gantt Chart
**Document ID:** Athena_Project-Plan_Detailed-Schedule_v0.2.0  
**Project:** Athena — Autonomous Multi-Agent Framework for Real-Time Program Management  
**Date:** 2026-02-20 | **Version:** 0.2.0

---

## 1. Project Overview

**Goal:** Develop an autonomous multi-agent system that ingests enterprise project data, synthesizes knowledge via GraphRAG (Neo4j + ChromaDB), and proactively detects risks — powered by a dual-mode `LLMProvider` (Gemini for development, Ollama for air-gapped demos).

**SDLC Model:** Agile-Incremental (15 weeks, 5 phases)  
**Team Size:** 4 members  
**Budget:** $0 (open-source + free-tier APIs)

---

## 2. SDLC Phases

### Phase 1 — Requirements & Research (Weeks 1–3)
| Activity | Deliverable |
|----------|-------------|
| Stakeholder analysis & problem definition | Synopsis |
| Literature survey (15 papers) | Literature Survey Report |
| Functional & non-functional requirements | SRS Document |
| Use case modeling & actor identification | Use Case Diagrams |
| Feasibility analysis (technical, economic) | Feasibility Study |

### Phase 2 — System Design (Weeks 3–5)
| Activity | Deliverable |
|----------|-------------|
| C4 architecture (L1 Context, L2 Container) | HLD Document |
| Database schema design (SQLite, Neo4j, ChromaDB) | DDD Document |
| API contract specification | OpenAPI Specs |
| Agent state machine design | Agent FSM Spec |
| UI/UX wireframes | Wireframe Mockups |
| Docker Compose topology | Deployment Spec |

### Phase 3 — Implementation (Weeks 5–9)
| Activity | Deliverable |
|----------|-------------|
| Project Universe simulator (Jira-Sim API) | Simulator Service |
| Chaos Engine (5 fault types + webhooks) | Chaos Service |
| `LLMProvider` abstraction (Gemini + Ollama) | LLM Module |
| LangGraph agent workflow (4 agents) | Agent Core |
| GraphRAG pipeline (ingestion → Neo4j/ChromaDB) | Knowledge Pipeline |
| Next.js 14 dashboard + chat interface | Frontend App |
| Synthetic dataset generation | Test Data |
| Docker environment & CI setup | Dev Environment |

### Phase 4 — Testing & Validation (Weeks 9–11)
| Activity | Deliverable |
|----------|-------------|
| Unit testing (pytest, Jest) | Test Reports |
| Integration testing (inter-service) | Integration Report |
| E2E Chaos Engine scenarios | E2E Demo Scripts |
| Performance benchmarking | Benchmark Report |
| Acceptance criteria validation | Acceptance Report |

**Acceptance Criteria:**

| Metric | Target |
|--------|--------|
| Query response time | < 5 seconds |
| Risk detection latency | < 60 seconds |
| Blocker identification | ≥ 95% detection |
| Offline capability | 100% (demo mode) |
| Hallucination rate | 0% (citation-backed) |

### Phase 5 — Documentation & Deployment (Weeks 11–15)
| Activity | Deliverable |
|----------|-------------|
| IEEE-format technical paper | Research Paper |
| Final project report | Project Report |
| User manual | User Guide |
| Demo preparation (dev + air-gapped) | Demo Package |
| Hard-bound report & exhibition | Final Submission |

---

## 3. Risk Summary

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM hallucination | HIGH | Citation-grounded responses + human-in-the-loop |
| RAM pressure (16 GB, demo mode) | MED | `--profile demo` selective startup; dev mode skips Ollama |
| Gemini API rate limits | LOW | 15 RPM free tier sufficient; fallback to Ollama |
| Scope creep | MED | Phase gates + university milestone deadlines |

---

## 4. Gantt Chart

```
PROJECT ATHENA — SDLC GANTT CHART (15 Weeks: 14-Feb to 28-May 2026)
══════════════════════════════════════════════════════════════════════════════════════

                              FEB        MARCH           APRIL            MAY
  PHASE / ACTIVITY           W1  W2  W3  W4  W5  W6  W7  W8  W9  W10 W11 W12 W13 W14 W15
  ──────────────────────────  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──

  PHASE 1: REQUIREMENTS
  Problem Definition          ██  ██
  Literature Survey               ██  ██
  SRS & Use Cases                 ██  ██
  Feasibility Study           ██  ██  ██
                                          ▲R1

  PHASE 2: DESIGN
  HLD (C4 Architecture)                  ██  ██
  DDD (Database Schema)                      ██  ██
  API Contracts & Agent FSM                  ██  ██
  UI/UX Wireframes                           ██  ██
                                                  ▲R2

  PHASE 3: IMPLEMENTATION
  Project Universe Simulator                      ██  ██  ██
  Chaos Engine & Webhooks                         ██  ██
  LLMProvider (Gemini/Ollama)                     ██  ██
  LangGraph Agent Workflow                            ██  ██  ██
  GraphRAG Pipeline                                   ██  ██  ██
  Next.js Dashboard                                   ██  ██  ██
  Synthetic Data & Docker                         ██  ██
                                                              ▲R3

  PHASE 4: TESTING
  Unit & Integration Tests                                    ██  ██
  E2E Chaos Scenarios                                         ██  ██
  Performance Benchmarks                                          ██
  Acceptance Validation                                           ██
                                                                  ▲R4

  PHASE 5: DOCUMENTATION
  Technical Paper (IEEE)                                              ██  ██
  Final Report & User Manual                                          ██  ██  ██
  Demo Preparation                                                        ██  ██
  Hard Bound & Exhibition                                                     ██
                                                                              ▲R5
  ──────────────────────────  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──  ──

  LEGEND:  ██ = Active work    ▲Rn = Phase review/milestone
```

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-02-19 | Team Athena | Initial schedule-only document |
| 0.2.0 | 2026-02-20 | Team Athena | Rewritten as standard SDLC project plan with 5 phases, risk summary, and phase-aligned Gantt chart |
