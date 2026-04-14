"""
Graph Syncer — Neo4j Aura Integration
Upserts entity nodes and relationships into the knowledge graph using Cypher MERGE.

Node Types (7): Project, Epic, Task, User, Sprint, Comment, Risk
Relationship Types (8): ASSIGNED_TO, REPORTED_BY, BELONGS_TO, PART_OF, IN_SPRINT, AUTHORED, HAS_RISK, BLOCKS
"""
from neo4j import GraphDatabase
from . import config

_driver = None


def get_driver():
    """Lazy-init Neo4j driver (reused across calls)."""
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            config.NEO4J_URI,
            auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
        )
    return _driver


def close():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


# ═══════════════════════════════════════════════════════════════
#  SCHEMA INITIALIZATION — Run once to create indexes
# ═══════════════════════════════════════════════════════════════

def init_schema():
    """Create property indexes for fast lookups. Idempotent (IF NOT EXISTS)."""
    index_statements = [
        "CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.id)",
        "CREATE INDEX IF NOT EXISTS FOR (u:User) ON (u.email)",
        "CREATE INDEX IF NOT EXISTS FOR (p:Project) ON (p.id)",
        "CREATE INDEX IF NOT EXISTS FOR (p:Project) ON (p.key)",
        "CREATE INDEX IF NOT EXISTS FOR (e:Epic) ON (e.id)",
        "CREATE INDEX IF NOT EXISTS FOR (e:Epic) ON (e.key)",
        "CREATE INDEX IF NOT EXISTS FOR (t:Task) ON (t.id)",
        "CREATE INDEX IF NOT EXISTS FOR (t:Task) ON (t.key)",
        "CREATE INDEX IF NOT EXISTS FOR (s:Sprint) ON (s.id)",
        "CREATE INDEX IF NOT EXISTS FOR (c:Comment) ON (c.id)",
        "CREATE INDEX IF NOT EXISTS FOR (r:Risk) ON (r.id)",
    ]
    driver = get_driver()
    with driver.session() as session:
        for stmt in index_statements:
            session.run(stmt)
    print("[GraphSyncer] Neo4j schema indexes initialized.")


# ═══════════════════════════════════════════════════════════════
#  SYNC HANDLERS — One per entity type
# ═══════════════════════════════════════════════════════════════

def _sync_user(tx, fields: dict):
    """MERGE a User node."""
    tx.run("""
        MERGE (u:User {id: $id})
        SET u.name = $name,
            u.email = $email,
            u.role = $role,
            u.department = $department,
            u.timezone = $timezone
    """, id=fields.get("id"), name=fields.get("name"), email=fields.get("email"),
         role=fields.get("role"), department=fields.get("department"),
         timezone=fields.get("timezone"))


def _sync_project(tx, fields: dict):
    """MERGE a Project node + OWNS relationship from lead."""
    tx.run("""
        MERGE (p:Project {id: $id})
        SET p.key = $key,
            p.name = $name,
            p.description = $description
    """, id=fields.get("id"), key=fields.get("key"),
         name=fields.get("name"), description=fields.get("description"))

    # Lead → OWNS → Project
    if fields.get("lead_id"):
        tx.run("""
            MATCH (u:User {id: $lead_id})
            MATCH (p:Project {id: $project_id})
            MERGE (u)-[:OWNS]->(p)
        """, lead_id=fields["lead_id"], project_id=fields["id"])


def _sync_epic(tx, fields: dict):
    """MERGE an Epic node + PART_OF relationship to Project."""
    tx.run("""
        MERGE (e:Epic {id: $id})
        SET e.key = $key,
            e.title = $title,
            e.description = $description,
            e.status = $status,
            e.priority = $priority
    """, id=fields.get("id"), key=fields.get("key"),
         title=fields.get("title"), description=fields.get("description"),
         status=fields.get("status"), priority=fields.get("priority"))

    # Epic → PART_OF → Project
    if fields.get("project_id"):
        tx.run("""
            MATCH (e:Epic {id: $epic_id})
            MATCH (p:Project {id: $project_id})
            MERGE (e)-[:PART_OF]->(p)
        """, epic_id=fields["id"], project_id=fields["project_id"])

    # Reporter → REPORTED_BY (reversed for readability)
    if fields.get("reporter_id"):
        tx.run("""
            MATCH (e:Epic {id: $epic_id})
            MATCH (u:User {id: $reporter_id})
            MERGE (u)-[:REPORTED_BY]->(e)
        """, epic_id=fields["id"], reporter_id=fields["reporter_id"])


def _sync_sprint(tx, fields: dict):
    """MERGE a Sprint node + relationship to Project."""
    tx.run("""
        MERGE (s:Sprint {id: $id})
        SET s.name = $name,
            s.state = $state,
            s.start_date = $start_date,
            s.end_date = $end_date
    """, id=fields.get("id"), name=fields.get("name"),
         state=fields.get("state"), start_date=fields.get("start_date"),
         end_date=fields.get("end_date"))

    # Sprint → PART_OF → Project
    if fields.get("project_id"):
        tx.run("""
            MATCH (s:Sprint {id: $sprint_id})
            MATCH (p:Project {id: $project_id})
            MERGE (s)-[:PART_OF]->(p)
        """, sprint_id=fields["id"], project_id=fields["project_id"])


def _sync_story(tx, fields: dict):
    """MERGE a Task (Story) node + all relationships."""
    tx.run("""
        MERGE (t:Task {id: $id})
        SET t.key = $key,
            t.title = $title,
            t.description = $description,
            t.status = $status,
            t.priority = $priority,
            t.story_points = $story_points,
            t.created_at = $created_at,
            t.updated_at = $updated_at,
            t.resolution_date = $resolution_date
    """, id=fields.get("id"), key=fields.get("key"),
         title=fields.get("title"), description=fields.get("description"),
         status=fields.get("status"), priority=fields.get("priority"),
         story_points=fields.get("story_points"),
         created_at=fields.get("created_at"), updated_at=fields.get("updated_at"),
         resolution_date=fields.get("resolution_date"))

    # Task → BELONGS_TO → Epic
    if fields.get("epic_id"):
        tx.run("""
            MATCH (t:Task {id: $task_id})
            MATCH (e:Epic {id: $epic_id})
            MERGE (t)-[:BELONGS_TO]->(e)
        """, task_id=fields["id"], epic_id=fields["epic_id"])

    # Task → IN_SPRINT → Sprint
    if fields.get("sprint_id"):
        tx.run("""
            MATCH (t:Task {id: $task_id})
            MATCH (s:Sprint {id: $sprint_id})
            MERGE (t)-[:IN_SPRINT]->(s)
        """, task_id=fields["id"], sprint_id=fields["sprint_id"])

    # User → ASSIGNED_TO → Task
    if fields.get("assignee_id"):
        tx.run("""
            MATCH (u:User {id: $user_id})
            MATCH (t:Task {id: $task_id})
            MERGE (u)-[:ASSIGNED_TO]->(t)
        """, user_id=fields["assignee_id"], task_id=fields["id"])

    # User → REPORTED_BY → Task
    if fields.get("reporter_id"):
        tx.run("""
            MATCH (u:User {id: $user_id})
            MATCH (t:Task {id: $task_id})
            MERGE (u)-[:REPORTED_BY]->(t)
        """, user_id=fields["reporter_id"], task_id=fields["id"])

    # If BLOCKED → create Risk node + HAS_RISK relationship
    if fields.get("status") == "BLOCKED":
        tx.run("""
            MERGE (r:Risk {id: 'RISK-' + $task_id})
            SET r.type = 'BLOCKED_TICKET',
                r.severity = $priority,
                r.description = 'Ticket ' + $key + ' is BLOCKED',
                r.detected_at = $updated_at
            WITH r
            MATCH (t:Task {id: $task_id})
            MERGE (t)-[:HAS_RISK]->(r)
        """, task_id=fields["id"], key=fields.get("key", ""),
             priority=fields.get("priority", "HIGH"),
             updated_at=fields.get("updated_at", ""))


def _sync_comment(tx, fields: dict):
    """MERGE a Comment node + AUTHORED relationship."""
    tx.run("""
        MERGE (c:Comment {id: $id})
        SET c.body = $body,
            c.created_at = $created_at
    """, id=fields.get("id"), body=fields.get("body"),
         created_at=fields.get("created_at"))

    # Comment is ON a Task (story)
    if fields.get("story_id"):
        tx.run("""
            MATCH (c:Comment {id: $comment_id})
            MATCH (t:Task {id: $story_id})
            MERGE (c)-[:ON]->(t)
        """, comment_id=fields["id"], story_id=fields["story_id"])

    # User → AUTHORED → Comment
    if fields.get("author_id"):
        tx.run("""
            MATCH (u:User {id: $author_id})
            MATCH (c:Comment {id: $comment_id})
            MERGE (u)-[:AUTHORED]->(c)
        """, author_id=fields["author_id"], comment_id=fields["id"])


# ═══════════════════════════════════════════════════════════════
#  PUBLIC API
# ═══════════════════════════════════════════════════════════════

# Route table: entity_type → handler function
_HANDLERS = {
    "user": _sync_user,
    "team": None,  # Teams are lightweight; users have team_id
    "project": _sync_project,
    "epic": _sync_epic,
    "sprint": _sync_sprint,
    "story": _sync_story,
    "comment": _sync_comment,
}


def sync_event(event: dict) -> bool:
    """
    Sync a webhook event to Neo4j.
    Returns True if synced, False if entity type is not handled.
    """
    entity_type = event.get("webhookEvent", "").lower()
    fields = event.get("issue", {}).get("fields", {})

    # For story events, also include the issue id
    issue_id = event.get("issue", {}).get("id")
    if issue_id and "id" not in fields:
        fields["id"] = issue_id

    handler = _HANDLERS.get(entity_type)
    if handler is None:
        return False

    driver = get_driver()
    with driver.session() as session:
        session.execute_write(handler, fields)

    return True


def search_graph(cypher_query: str, params: dict = None) -> list:
    """
    Agent Tool #11: Execute a Cypher query on the knowledge graph.
    Returns list of record dictionaries.
    """
    driver = get_driver()
    with driver.session() as session:
        result = session.run(cypher_query, params or {})
        return [dict(record) for record in result]


def get_node_counts() -> dict:
    """Get count of each node type for metrics endpoint."""
    driver = get_driver()
    with driver.session() as session:
        result = session.run("""
            CALL db.labels() YIELD label
            CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as cnt', {}) YIELD value
            RETURN label, value.cnt as count
        """)
        # Fallback if APOC is not available (Aura free tier)
        try:
            return {r["label"]: r["count"] for r in result}
        except Exception:
            pass

    # Simple fallback without APOC
    counts = {}
    labels = ["User", "Project", "Epic", "Task", "Sprint", "Comment", "Risk"]
    with driver.session() as session:
        for label in labels:
            result = session.run(f"MATCH (n:{label}) RETURN count(n) as cnt")
            record = result.single()
            counts[label] = record["cnt"] if record else 0
    return counts
