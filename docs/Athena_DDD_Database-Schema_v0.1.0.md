# Database Design Document (DDD)
**Document ID:** Athena_DDD_Database-Schema_v0.1.0  
**Date:** 2026-02-05  
**Version:** 0.1.0 (Minor - Schema Defined)

---

## 1. Introduction

### 1.1 Purpose
This document specifies the database schemas for Project Athena, covering both the simulation layer (Mock Jira) and the knowledge layer (GraphRAG).

### 1.2 Database Strategy

| Layer | Database | Type | Purpose |
|-------|----------|------|---------|
| Simulation | SQLite | Relational | Mock Jira data storage |
| Knowledge | Neo4j | Graph | Relationship mapping |
| Semantic | ChromaDB | Vector | Text embeddings |

---

## 2. Mock Jira Schema (SQLite)

### 2.1 Entity-Relationship Diagram

```
+------------------+       +------------------+       +------------------+
|      USERS       |       |      EPICS       |       |    MILESTONES    |
+------------------+       +------------------+       +------------------+
| PK: id (UUID)    |       | PK: id (VARCHAR) |       | PK: id (UUID)    |
| email (VARCHAR)  |       | title (TEXT)     |       | name (VARCHAR)   |
| name (VARCHAR)   |       | status (ENUM)    |       | deadline (DATE)  |
| role (ENUM)      |       | rag_status (ENUM)|       | status (ENUM)    |
| perf_score (INT) |       | created_at (TS)  |       +--------+---------+
+--------+---------+       +--------+---------+                |
         |                          |                          |
         |                          |                          |
         |    +---------------------+                          |
         |    |                                                |
         v    v                                                |
+------------------+                                           |
|     STORIES      |                                           |
+------------------+                                           |
| PK: id (VARCHAR) |<------------------------------------------+
| FK: epic_id      |                 (Stories belong to Milestones)
| FK: assignee_id  |
| title (TEXT)     |
| description(TEXT)|
| status (ENUM)    |
| priority (ENUM)  |
| points (INT)     |
| blocked_by (JSON)|  <-- Array of Story IDs
| chaos_flag (BOOL)|
| created_at (TS)  |
| updated_at (TS)  |
+--------+---------+
         |
         |
         v
+------------------+       +------------------+
|      RISKS       |       |    AUDIT_LOG     |
+------------------+       +------------------+
| PK: id (UUID)    |       | PK: id (UUID)    |
| FK: story_id     |       | entity_type(ENUM)|
| severity (ENUM)  |       | entity_id (VAR)  |
| description(TEXT)|       | change_type(ENUM)|
| status (ENUM)    |       | payload (JSON)   |
| reported_by (FK) |       | timestamp (TS)   |
+------------------+       +------------------+
```

### 2.2 Table Definitions

#### 2.2.1 Users Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Corporate email |
| name | VARCHAR(100) | NOT NULL | Display name |
| role | ENUM | NOT NULL | DEV, PM, QA, VP |
| perf_score | INTEGER | DEFAULT 50 | Hidden metric (0-100) |
| created_at | TIMESTAMP | DEFAULT NOW | Creation timestamp |

#### 2.2.2 Epics Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(20) | PRIMARY KEY | EPIC-{number} format |
| title | TEXT | NOT NULL | Epic title |
| description | TEXT | | Detailed description |
| status | ENUM | NOT NULL | OPEN, IN_PROGRESS, DONE |
| rag_status | ENUM | COMPUTED | RED, AMBER, GREEN |
| created_at | TIMESTAMP | DEFAULT NOW | Creation timestamp |

#### 2.2.3 Stories Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | VARCHAR(20) | PRIMARY KEY | STORY-{number} format |
| epic_id | VARCHAR(20) | FOREIGN KEY | References epics.id |
| assignee_id | UUID | FOREIGN KEY | References users.id |
| title | TEXT | NOT NULL | Story title |
| description | TEXT | | Detailed description |
| status | ENUM | NOT NULL | TODO, IN_PROGRESS, REVIEW, DONE |
| priority | ENUM | NOT NULL | LOW, MEDIUM, HIGH, CRITICAL |
| points | INTEGER | | Story points (Fibonacci) |
| blocked_by | JSON | | Array of blocking story IDs |
| chaos_flag | BOOLEAN | DEFAULT FALSE | Target for chaos injection |
| created_at | TIMESTAMP | DEFAULT NOW | Creation timestamp |
| updated_at | TIMESTAMP | ON UPDATE NOW | Last modification |

#### 2.2.4 Risks Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| story_id | VARCHAR(20) | FOREIGN KEY | References stories.id |
| severity | ENUM | NOT NULL | CRITICAL, HIGH, MEDIUM, LOW |
| description | TEXT | NOT NULL | Risk description |
| status | ENUM | NOT NULL | OPEN, MITIGATING, CLOSED |
| reported_by | UUID | FOREIGN KEY | References users.id |
| created_at | TIMESTAMP | DEFAULT NOW | Creation timestamp |

#### 2.2.5 Audit Log Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| entity_type | ENUM | NOT NULL | STORY, EPIC, RISK, USER |
| entity_id | VARCHAR(50) | NOT NULL | ID of modified entity |
| change_type | ENUM | NOT NULL | CREATE, UPDATE, DELETE |
| payload | JSON | NOT NULL | Before/after state |
| timestamp | TIMESTAMP | DEFAULT NOW | Event timestamp |

---

## 3. Knowledge Graph Schema (Neo4j)

### 3.1 Graph Model Diagram

```
                                +---------------+
                                |   MILESTONE   |
                                | - name        |
                                | - deadline    |
                                | - status      |
                                +-------+-------+
                                        ^
                                        |
                                   [:PART_OF]
                                        |
+---------------+              +--------+--------+              +---------------+
|     USER      |              |      TASK       |              |     RISK      |
| - email       |<--[:OWNS]--- | - id            |---[:HAS]--->| - id          |
| - name        |              | - title         |              | - severity    |
| - role        |              | - status        |              | - description |
+---------------+              | - priority      |              +-------+-------+
       |                       | - points        |                      |
       |                       +--------+--------+                      |
       |                                |                               |
       |                           [:BLOCKS]                            |
       |                                |                               |
       |                                v                               |
       |                       +--------+--------+                      |
       |                       |      TASK       |                      |
       +---[:ASSIGNED_TO]----->| (Blocked Task)  |                      |
                               +-----------------+                      |
                                                                        |
                                                                        |
                               +----------------+                       |
                               |    FEATURE     |<-----[:IMPACTS]-------+
                               | - name         |
                               | - rag_status   |
                               +----------------+
```

### 3.2 Node Definitions

#### 3.2.1 User Node

| Property | Type | Description |
|----------|------|-------------|
| email | String | Unique identifier (from SQLite) |
| name | String | Display name |
| role | String | DEV, PM, QA, VP |
| workload | Integer | Computed: number of active tasks |

#### 3.2.2 Task Node

| Property | Type | Description |
|----------|------|-------------|
| id | String | STORY-{number} (from SQLite) |
| title | String | Task title |
| status | String | Current workflow state |
| priority | String | Priority level |
| points | Integer | Effort estimation |
| due_date | Date | Deadline (if set) |

#### 3.2.3 Risk Node

| Property | Type | Description |
|----------|------|-------------|
| id | String | RISK-{number} |
| severity | String | CRITICAL, HIGH, MEDIUM, LOW |
| description | String | Risk details |
| status | String | OPEN, MITIGATING, CLOSED |

#### 3.2.4 Milestone Node

| Property | Type | Description |
|----------|------|-------------|
| name | String | Milestone identifier |
| deadline | Date | Target completion date |
| status | String | ON_TRACK, AT_RISK, DELAYED |

#### 3.2.5 Feature Node

| Property | Type | Description |
|----------|------|-------------|
| name | String | Feature/Epic name |
| rag_status | String | RED, AMBER, GREEN |

### 3.3 Relationship Definitions

| Relationship | From | To | Properties |
|--------------|------|-----|------------|
| ASSIGNED_TO | User | Task | assigned_date |
| OWNS | User | Task | (none) |
| BLOCKS | Task | Task | reason |
| PART_OF | Task | Milestone | (none) |
| HAS | Task | Risk | (none) |
| IMPACTS | Risk | Feature | impact_level |

### 3.4 Example Cypher Queries

**Find all blocked critical tasks:**
```cypher
MATCH (t:Task {priority: 'CRITICAL'})-[:BLOCKS]->(blocked:Task)
RETURN t.id, t.title, blocked.id, blocked.title
```

**Find overloaded users (> 5 active tasks):**
```cypher
MATCH (u:User)-[:ASSIGNED_TO]->(t:Task)
WHERE t.status <> 'DONE'
WITH u, count(t) as taskCount
WHERE taskCount > 5
RETURN u.email, u.name, taskCount
```

**Find risks impacting delayed milestones:**
```cypher
MATCH (r:Risk)-[:IMPACTS]->(f:Feature)<-[:PART_OF]-(m:Milestone)
WHERE m.status = 'DELAYED' AND r.severity IN ['CRITICAL', 'HIGH']
RETURN r.id, r.description, m.name, m.deadline
```

---

## 4. Vector Store Schema (ChromaDB)

### 4.1 Collection: ticket_context

| Field | Type | Description |
|-------|------|-------------|
| id | String | ticket_id (e.g., STORY-101) |
| document | String | Concatenated title + description + comments |
| metadata.type | String | STORY, EPIC, RISK |
| metadata.priority | String | Priority level |
| metadata.status | String | Current status |
| embedding | Vector[768] | LLMProvider embedding (Gemini or Llama 3, depending on active mode) |

### 4.2 Collection: meeting_notes

| Field | Type | Description |
|-------|------|-------------|
| id | String | UUID |
| document | String | Full meeting transcript |
| metadata.date | Date | Meeting date |
| metadata.attendees | Array[String] | List of participant emails |
| embedding | Vector[768] | LLMProvider embedding (Gemini or Llama 3, depending on active mode) |

---

## 5. Data Synchronization

### 5.1 Sync Flow Diagram

```
+------------------+                    +------------------+
|     SQLite       |                    |      Neo4j       |
| (Source of Truth)|                    | (Knowledge Copy) |
+--------+---------+                    +--------+---------+
         |                                       ^
         |                                       |
         | 1. State change triggers              |
         |    audit_log INSERT                   |
         |                                       |
         v                                       |
+------------------+                             |
|   Audit Log      |----- 2. Read new entries --+
|   (Change Feed)  |
+------------------+
         |
         | 3. Fire webhook to Athena
         |
         v
+------------------+
|  Athena Ingest   |
| - Parse payload  |
| - Upsert Neo4j   |---- 4. Update graph ----->
| - Update Chroma  |
+------------------+
```

---

**Document Version History:**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1.0 | 2026-02-05 | Team Athena | Initial database schema definition |
| 0.1.1 | 2026-02-20 | Team Athena | Updated embedding references for dual-mode LLMProvider (Gemini/Ollama) |
