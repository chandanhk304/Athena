# Implementation Report: Project Universe Simulator
**Document ID:** Athena_Implementation-Report_Project-Universe-Simulator_v0.1.0  
**Project:** Athena: An Autonomous Multi-Agent Framework for Real-Time Program Management and Proactive Risk Mitigation  
**Date:** 2026-04-03  
**Version:** 0.1.0 (Minor — First complete implementation of Phase 3.2)

> **Scope:** This document covers the implementation of the **Project Universe Simulator** — the Data Acquisition Layer described in HLD v0.4.0 Section 2.3.1. It includes the Mock Jira API, AI Data Generator, Timeline Simulator, Chaos Engine, Webhook Dispatcher, and all supporting infrastructure (cloud services, database models, connectivity tooling).

---

## 1. Executive Summary

The Project Universe Simulator is the first fully implemented subsystem of Project Athena. It generates a complete, high-fidelity enterprise project environment — users, teams, projects, sprints, epics, stories, comments, and audit logs — entirely using LLM-driven data generation (Groq API). The simulator exposes a Jira-compatible REST API with 10 query endpoints identical to a production Jira integration's `TOOL_CONFIG`, ensuring that Athena's agent tools work identically against both the simulator and a real Jira instance.

**Key Outcomes:**
- 279 AI-generated stories across 26 sprints spanning 12 months of simulated history
- 965 contextual engineer comments averaging 325 characters each
- 1,778 audit log entries covering all entity lifecycle events
- Zero hardcoded/placeholder data — every entity is LLM-generated
- Zero data integrity violations — all FK, uniqueness, and referential checks pass
- 9 MB database footprint against a 512 MB free tier limit

---

## 2. HLD Requirements Traceability

This section maps every HLD v0.4.0 requirement for the simulator to its implementation status.

### 2.1 Jira-Compatible Query Endpoints (HLD Section 2.3.1)

| # | TOOL_CONFIG Function | API Route | Status | Notes |
|---|---------------------|-----------|--------|-------|
| 1 | `get_jira_issue` | `GET /api/v1/issues/{issue_key}` | ✅ Implemented | Returns full story with comments, reporter, assignee |
| 2 | `search_jira_issues` | `GET /api/v1/issues/search` | ✅ Implemented | JQL parser supports status, priority, assignee, project filters + component breakdown |
| 3 | `get_project_issues` | `GET /api/v1/projects/{project_key}/issues` | ✅ Implemented | Optional status filter |
| 4 | `get_user_issues` | `GET /api/v1/users/{username}/issues` | ✅ Implemented | Matches by email or name (case-insensitive) |
| 5 | `get_sprint_issues` | `GET /api/v1/sprints/issues` | ✅ Implemented | Defaults to ACTIVE sprint if no name provided |
| 6 | `get_issue_comments` | `GET /api/v1/issues/{issue_key}/comments` | ✅ Implemented | Ordered chronologically |
| 7 | `get_issue_transitions` | `GET /api/v1/issues/{issue_key}/transitions` | ✅ Implemented | State machine: OPEN→IN_PROGRESS→BLOCKED/CLOSED |
| 8 | `get_issue_attachments` | `GET /api/v1/issues/{issue_key}/attachments` | ✅ Implemented | Returns empty array (simulator does not store files) |
| 9 | `get_project_summary` | `GET /api/v1/projects/{project_key}/summary` | ✅ Implemented | Returns issue counts by status (OPEN/IN_PROGRESS/BLOCKED/CLOSED) |
| 10 | `download_issue_logs` | `GET /api/v1/issues/{issue_key}/logs` | ✅ Implemented | Returns audit trail with CREATE/UPDATE transitions |

### 2.2 Database Models (HLD Section 3.4)

| # | Model | Table | Status | Key Fields |
|---|-------|-------|--------|------------|
| 1 | User | `users` | ✅ | id, email (unique+indexed), name, role, department, timezone |
| 2 | Team | `teams` | ✅ | id, name, lead_id (FK→users, `use_alter=True` for circular dep) |
| 3 | Project | `projects` | ✅ | id, key (unique+indexed), name, description, lead_id |
| 4 | Sprint | `sprints` | ✅ | id, project_id, name, state (PLANNED/ACTIVE/CLOSED), dates |
| 5 | Epic | `epics` | ✅ | id, key (unique+indexed), project_id, title, status, priority |
| 6 | Story | `stories` | ✅ | id, key (unique+indexed), epic_id, sprint_id, status (OPEN/IN_PROGRESS/BLOCKED/CLOSED), priority (LOW/MEDIUM/HIGH/CRITICAL), story_points, reporter_id, assignee_id |
| 7 | Comment | `comments` | ✅ | id, story_id, author_id, body, created_at |
| 8 | AuditLog | `audit_log` | ✅ | id, entity_type, entity_id, action (CREATE/UPDATE/DELETE), details (JSON), timestamp |

All models include `to_dict()` serialization methods.

### 2.3 Simulator Components (HLD Section 2.3.1)

| Component | File | Status | Description |
|-----------|------|--------|-------------|
| Mock Jira API | `api.py` | ✅ | FastAPI app with 10 TOOL_CONFIG + CRUD + God Mode endpoints |
| AI Data Generator | `data_gen.py` | ✅ | Groq-only with dual-model rotation (70B structural, 8B batch) |
| Timeline Simulator | `timeline_sim.py` | ✅ | 12-month history generator with multi-project support |
| Chaos Engine | `chaos_engine.py` | ✅ | 3 fault patterns with APScheduler + LLM-generated comments |
| Webhook Dispatcher | `webhook.py` | ✅ | Real-time + historical replay, graceful offline handling |
| Database Schema | `database.py` | ✅ | 8 SQLAlchemy ORM models, Neon Postgres connection |
| Connectivity Test | `test_connections.py` | ✅ | Validates all 5 cloud services before simulation |
| Data Quality Audit | `audit_data.py` | ✅ | 10-section analysis of data realism, integrity, and coverage |

### 2.4 Status Enum Compliance (HLD v0.4.0)

| Entity | Valid Statuses | Implemented |
|--------|---------------|-------------|
| Story | OPEN, IN_PROGRESS, BLOCKED, CLOSED | ✅ |
| Sprint | PLANNED, ACTIVE, CLOSED | ✅ |
| Epic | OPEN, IN_PROGRESS, CLOSED | ✅ |
| AuditLog Actions | CREATE, UPDATE, DELETE | ✅ |
| Priority | LOW, MEDIUM, HIGH, CRITICAL | ✅ |

---

## 3. Architecture and Data Flow

### 3.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     PROJECT UNIVERSE SIMULATOR                   │
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ Timeline Sim  │    │  Chaos Engine │    │  Groq API    │       │
│  │ (timeline_    │    │  (chaos_     │    │  (data_gen   │       │
│  │  sim.py)      │    │   engine.py) │    │   .py)       │       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                    │                │
│         ▼                   ▼                    │                │
│  ┌──────────────────────────────────────┐        │                │
│  │         Mock Jira API (api.py)       │◄───────┘                │
│  │         FastAPI — Port 8000          │                         │
│  │  10 TOOL_CONFIG + CRUD + God Mode    │                         │
│  └──────┬──────────────┬────────────────┘                         │
│         │              │                                          │
│         ▼              ▼                                          │
│  ┌────────────┐  ┌─────────────┐                                 │
│  │  Neon PG   │  │  Webhook    │──────▶ Athena Core (:8001)      │
│  │ (database  │  │ (webhook.py)│        (future phase)            │
│  │  .py)      │  └─────────────┘                                 │
│  └────────────┘                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Generation Pipeline

```
1. BOOTSTRAP (create_bootstrap_data)
   ├── Groq 70B → Generate 20 diverse users (names, emails, roles)
   ├── Groq 70B → Generate project structure (name, key, description)
   ├── Groq 70B → Generate 3 epic initiatives
   └── Commit: Users → Team → Project → Epics (FK-ordered commits)

2. SIMULATE (simulate_timeline)
   ├── For each of 26 sprints (12 months ÷ 14 days):
   │   ├── Create Sprint entity (ACTIVE for last, CLOSED for history)
   │   ├── Groq 8B → Batch generate 8-15 stories per sprint
   │   ├── Assign weighted statuses:
   │   │   ├── Historical: 93% CLOSED, 3% OPEN, 2% IN_PROGRESS, 2% BLOCKED
   │   │   └── Recent:     40% CLOSED, 35% IN_PROGRESS, 15% OPEN, 10% BLOCKED
   │   ├── Groq 8B → Batch generate 1-3 comments per story
   │   ├── Write AuditLog entries (CREATE + status transitions)
   │   └── Fire historical webhooks (silent replay)
   └── Commit per sprint for safety (with rollback on failure)

3. CHAOS (ongoing, after API starts)
   ├── APScheduler fires every 3-8 minutes:
   │   ├── TICKET_BLOCKER:       Block HIGH/CRITICAL tickets
   │   ├── DEVELOPER_OVERLOAD:   Assign 6+ CRITICAL tasks to one dev
   │   └── PRIORITY_ESCALATION:  Escalate LOW → CRITICAL with LLM comment
   └── All mutations fire real-time webhooks to Athena Core
```

---

## 4. Cloud Service Integration

### 4.1 Services Used

| Service | Purpose | Tier | Configuration |
|---------|---------|------|---------------|
| **Neon Postgres** | Relational DB for all simulator entities | Free (512 MB) | PostgreSQL 17.8, SSL required |
| **Groq API** | LLM inference for AI data generation | Free | llama-3.3-70b-versatile + llama-3.1-8b-instant |
| **Neo4j Aura** | Knowledge graph (used by Athena Core) | Free (50K nodes) | Instance `a9afe1f2`, user `neo4j` |
| **Pinecone** | Vector store (used by Athena Core) | Free (100K vectors) | Index `athena-vectors`, 768-dim, cosine |
| **Gemini API** | Optional fallback (used by Athena Core) | Free (1500 RPD) | `gemini-2.0-flash` — not used by simulator |

### 4.2 Groq Model Strategy

The simulator uses a **dual-model rotation** to maximize throughput within free tier limits:

| Model | Use Case | Why | Rate Limits |
|-------|----------|-----|-------------|
| `llama-3.3-70b-versatile` | Users, projects, epics (structural) | Higher quality output for foundational entities | 30 RPM, 1K RPD, 12K TPM |
| `llama-3.1-8b-instant` | Stories, comments (high-volume batch) | 14x higher daily limit for bulk generation | 30 RPM, 14.4K RPD, 6K TPM |

**Rate limit handling:** Automatic retry with exponential backoff (2^attempt + jitter) on HTTP 429 responses, up to 3 retries.

### 4.3 Resource Consumption (Post-Generation)

| Service | Used | Free Limit | Utilization | Headroom |
|---------|------|-----------|-------------|----------|
| Neon Postgres | 9 MB | 512 MB | 1.8% | ~56x more projects |
| Groq 70B | ~10 RPD | 1,000 RPD | 1% | ~99 more projects |
| Groq 8B | ~100 RPD | 14,400 RPD | 0.7% | ~143 more projects |
| Neo4j Aura | 0 nodes | 50,000 | 0% | Full capacity |
| Pinecone | 0 vectors | 100,000 | 0% | Full capacity |

---

## 5. Data Quality Audit Results

The following audit was performed against live data in Neon Postgres after a single-project simulation run.

### 5.1 Entity Counts

| Table | Rows | Per-Sprint Avg |
|-------|------|---------------|
| Users | 20 | — |
| Teams | 1 | — |
| Projects | 1 | — |
| Epics | 3 | — |
| Sprints | 26 | — |
| Stories | 279 | ~10.7 per sprint |
| Comments | 965 | ~3.5 per story |
| Audit Log | 1,778 | ~6.4 per story |
| **Total** | **3,073** | |

### 5.2 Status Distribution

| Status | Count | Percentage | Distribution Pattern |
|--------|-------|------------|---------------------|
| CLOSED | 242 | 86.7% | Historical sprints (majority) |
| IN_PROGRESS | 19 | 6.8% | Active/recent sprints |
| BLOCKED | 12 | 4.3% | Realistic blockers across timeline |
| OPEN | 6 | 2.2% | Active sprint backlog |

### 5.3 Priority Distribution

| Priority | Count | Percentage |
|----------|-------|------------|
| MEDIUM | 94 | 33.7% |
| HIGH | 69 | 24.7% |
| CRITICAL | 64 | 22.9% |
| LOW | 52 | 18.6% |

### 5.4 Data Realism Verification

| Check | Result |
|-------|--------|
| Unique emails | ✅ All 20 emails unique |
| Realistic names | ✅ Diverse ethnicities (Patel, Chen, Morales, etc.) |
| Valid roles | ✅ DEV, QA, TECH_LEAD, PM, DESIGN, VP distribution |
| Story title quality | ✅ Zero generic/placeholder titles |
| Comment substance | ✅ Avg 325 chars, mentions PRs, deployments, bugs |
| Assignee coverage | ✅ 100% of stories assigned |

### 5.5 Referential Integrity

| Check | Result |
|-------|--------|
| Stories without sprint | 0 ✅ |
| Stories without epic | 0 ✅ |
| Unassigned stories | 0 ✅ |
| Orphan comments | 0 ✅ |
| Duplicate story keys | 0 ✅ |

---

## 6. File-Level Implementation Details

### 6.1 `simulator/database.py` — ORM Models (185 lines)

Defines all 8 SQLAlchemy ORM models mapped to Neon Postgres tables. Key design decisions:

- **Circular FK resolution:** `User.team_id → teams.id` and `Team.lead_id → users.id` create a circular dependency. Resolved using `ForeignKey("users.id", name="fk_team_lead", use_alter=True)` — SQLAlchemy handles this via `ALTER TABLE` instead of inline FK definition.
- **Serialization:** Every model has a `to_dict()` method that converts DateTime fields to ISO 8601 strings and safely handles nullable fields.
- **Indexing:** `email` (User), `key` (Project, Epic, Story) have unique indexes for fast lookups by the API layer.

### 6.2 `simulator/api.py` — Mock Jira API (355 lines)

FastAPI application implementing 10 Jira-compatible TOOL_CONFIG endpoints + 9 CRUD endpoints + 1 God Mode endpoint.

- **JQL Parser (Endpoint #2):** Parses simple JQL-like filter strings supporting `status=`, `priority=`, `assignee=`, `project=` with case-insensitive matching.
- **Component Breakdown:** When `analyze_by_component=true`, groups stories by their parent Epic and returns status counts per component.
- **Transition State Machine (Endpoint #7):** Implements valid transitions: `OPEN→[IN_PROGRESS]`, `IN_PROGRESS→[BLOCKED, CLOSED]`, `BLOCKED→[OPEN, IN_PROGRESS]`, `CLOSED→[OPEN]`.
- **Audit Integration:** All CRUD mutations write to the `audit_log` table with change details (old/new values).
- **Webhook Integration:** All mutations fire background webhooks via FastAPI's `BackgroundTasks`.

### 6.3 `simulator/data_gen.py` — AI Data Generator (138 lines)

Groq-only LLM data generation engine with dual-model rotation.

- **JSON Extraction:** Strips markdown code fences (`\`\`\`json ... \`\`\``) from LLM output before parsing.
- **Rate Limit Handling:** Retries 3 times with exponential backoff on HTTP 429.
- **Prompt Engineering:** System prompt instructs the LLM to use "corporate jargon, mention microservices down to the module level, reference real tech debt, and include realistic human frustration."

### 6.4 `simulator/timeline_sim.py` — Timeline Simulator (302 lines)

Generates 12 months of project history with the following protections:

- **FK-Ordered Commits:** Commits Team+Project before Epics, Sprint before Stories — preventing foreign key violations.
- **Empty LLM Fallback:** If the LLM returns 0 stories for a sprint (rate limit), the sprint is skipped gracefully.
- **Email Uniqueness:** Deduplicates LLM-generated emails by prepending a UUID fragment.
- **Per-Sprint Rollback:** Each sprint commits independently; a DB failure in one sprint doesn't lose previous work.
- **Multi-Project Support:** `--projects N` flag generates N independent projects sharing the same user pool.
- **Reset Mode:** `--reset` drops all tables via `DROP SCHEMA public CASCADE` (bypasses circular FK ordering).

### 6.5 `simulator/chaos_engine.py` — Chaos Engine (142 lines)

Three fault injection patterns triggered by APScheduler:

| Pattern | Interval | Action | LLM Integration |
|---------|----------|--------|-----------------|
| TICKET_BLOCKER | 3 min ± 60s jitter | Marks HIGH/CRITICAL ticket as BLOCKED | Generates contextual blocker comment |
| DEVELOPER_OVERLOAD | 8 min ± 120s jitter | Assigns 6 CRITICAL tasks to one dev | — |
| PRIORITY_ESCALATION | 5 min ± 60s jitter | Escalates LOW → CRITICAL | Generates frantic escalation comment |

All mutations fire webhooks and are API-driven (calls the Mock Jira API, doesn't directly write to DB).

### 6.6 `simulator/webhook.py` — Webhook Dispatcher (79 lines)

Fires Jira-compatible HTTP POST payloads with the structure:

```json
{
  "event_id": "evt_<uuid>",
  "event_type": "jira:issue_created",
  "timestamp": "2026-03-25T12:00:00Z",
  "webhookEvent": "story",
  "issue": { "id": "STR-abc123", "fields": { ... } }
}
```

- **Silent Mode:** Historical replay suppresses per-event logging (thousands of events during timeline simulation).
- **Graceful Offline:** `ConnectionError` and `Timeout` are caught and counted — simulator never crashes if Athena Core is not running.
- **Stats Tracking:** `get_webhook_stats()` returns dispatched/dropped counts for the simulation summary.

---

## 7. CLI Usage

### 7.1 Connectivity Test

```bash
python simulator/test_connections.py
```

Validates all 5 cloud services (Neon Postgres, Groq 8B, Groq 70B, Neo4j Aura, Pinecone). Returns exit code 0 if all required services pass.

### 7.2 Data Generation

```bash
# Single project, 12 months of history
python -m simulator.timeline_sim

# 3 projects, 6 months of history
python -m simulator.timeline_sim --projects 3 --months 6

# Reset everything and regenerate
python -m simulator.timeline_sim --reset
```

### 7.3 Start Simulator API

```bash
uvicorn simulator.api:app --host 0.0.0.0 --port 8000 --reload
```

### 7.4 Start Chaos Engine (requires API to be running)

```bash
python -m simulator.chaos_engine
```

### 7.5 Data Quality Audit

```bash
python simulator/audit_data.py
```

---

## 8. Known Limitations and Future Improvements

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| JQL parser supports only simple `key=value` filters | Complex JQL (OR, AND, ORDER BY) not supported | Sufficient for Athena's agent tools which use simple queries |
| Attachments endpoint returns empty array | No binary file storage in simulator | Documented as stub; real Jira integration will provide actual files |
| Chaos Engine requires API to be running | Cannot inject chaos during data generation phase | By design — chaos is a runtime feature, not a generation feature |
| Groq free tier rate limits | May throttle during large multi-project generation | Dual-model rotation + exponential backoff mitigate this |

---

## 9. Verification Results

| Test | Method | Result |
|------|--------|--------|
| Cloud Connectivity | `test_connections.py` | 5/5 services connected ✅ |
| Data Generation | `timeline_sim.py` | 279 stories, 965 comments generated ✅ |
| Data Integrity | `audit_data.py` | All 5 referential checks passed ✅ |
| Data Realism | `audit_data.py` | Zero placeholders, avg comment 325 chars ✅ |
| API Endpoints | Manual verification via FastAPI `/docs` | All 10 TOOL_CONFIG endpoints functional ✅ |
| Status Enums | Code inspection | OPEN/IN_PROGRESS/BLOCKED/CLOSED throughout ✅ |

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-04-03 | Team Athena | Initial implementation report covering complete Project Universe Simulator phase |
