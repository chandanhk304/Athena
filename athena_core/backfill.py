"""
Historical Backfill — Populates Neo4j + Pinecone from existing Neon Postgres data.
Reads all entities from the simulator database and feeds them through the ingestion pipeline.

Run: python -m athena_core.backfill
"""
import sys
import time
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import config
from .graph_syncer import init_schema, get_node_counts
from .vector_indexer import get_vector_count
from .ingestion import process_event, get_metrics

# Import simulator ORM models
sys.path.insert(0, ".")
from simulator.database import User, Team, Project, Sprint, Epic, Story, Comment


def _make_event(event_type: str, entity_type: str, entity_id: str, fields: dict) -> dict:
    """Construct a synthetic webhook event for the ingestion pipeline."""
    return {
        "event_id": f"backfill_{uuid.uuid4().hex[:12]}",
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "webhookEvent": entity_type,
        "is_historical_replay": True,
        "issue": {
            "id": entity_id,
            "fields": fields
        }
    }


def _fresh_session(engine):
    """Create a fresh DB session — prevents SSL timeout on Neon serverless."""
    Session = sessionmaker(bind=engine)
    return Session()


def backfill():
    """Main backfill procedure — reads Postgres, feeds into ingestion pipeline."""
    print("=" * 60)
    print("  ATHENA — HISTORICAL BACKFILL")
    print("  Populating Neo4j + Pinecone from Neon Postgres")
    print("=" * 60)

    # Neon serverless aggressively closes idle SSL connections.
    # We create a fresh session before each phase to avoid stale connections.
    engine = create_engine(
        config.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=120,        # Recycle connections after 2 min
        connect_args={"connect_timeout": 10}
    )

    # Initialize Neo4j schema
    print("\n  [1/7] Initializing Neo4j schema indexes...")
    try:
        init_schema()
    except Exception as e:
        print(f"  ❌ Neo4j schema init failed: {e}")
        print("  Check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env")
        sys.exit(1)

    # ─── Phase 1: Users ─────────────────────────────────────
    print("\n  [2/7] Backfilling Users...")
    db = _fresh_session(engine)
    users = db.query(User).all()
    user_count = 0
    for u in users:
        event = _make_event("jira:user_created", "user", u.id, u.to_dict())
        result = process_event(event)
        if result.get("graph_synced"):
            user_count += 1
    db.close()
    print(f"  ✅ {user_count}/{len(users)} users synced to Neo4j")

    # ─── Phase 2: Projects ──────────────────────────────────
    print("\n  [3/7] Backfilling Projects...")
    db = _fresh_session(engine)
    projects = db.query(Project).all()
    for p in projects:
        event = _make_event("jira:project_created", "project", p.id, p.to_dict())
        process_event(event)
    db.close()
    print(f"  ✅ {len(projects)} projects synced")

    # ─── Phase 3: Epics ─────────────────────────────────────
    print("\n  [4/7] Backfilling Epics...")
    db = _fresh_session(engine)
    epics = db.query(Epic).all()
    for e in epics:
        event = _make_event("jira:epic_created", "epic", e.id, e.to_dict())
        process_event(event)
    db.close()
    print(f"  ✅ {len(epics)} epics synced (graph + vector)")

    # ─── Phase 4: Sprints ───────────────────────────────────
    print("\n  [5/7] Backfilling Sprints...")
    db = _fresh_session(engine)
    sprints = db.query(Sprint).all()
    for s in sprints:
        event = _make_event("jira:sprint_created", "sprint", s.id, s.to_dict())
        process_event(event)
    db.close()
    print(f"  ✅ {len(sprints)} sprints synced")

    # ─── Phase 5: Stories (batch for efficiency) ────────────
    print("\n  [6/7] Backfilling Stories...")
    db = _fresh_session(engine)
    stories = db.query(Story).all()
    db.close()  # Close immediately — we have the data in memory

    story_graph = 0
    story_vector = 0
    batch_size = 10

    for i in range(0, len(stories), batch_size):
        batch = stories[i:i + batch_size]
        for s in batch:
            event = _make_event("jira:issue_created", "story", s.id, s.to_dict())
            result = process_event(event)
            if result.get("graph_synced"):
                story_graph += 1
            if result.get("vector_indexed"):
                story_vector += 1

        processed = min(i + batch_size, len(stories))
        print(f"    Progress: {processed}/{len(stories)} stories...", end="\r")

        if i + batch_size < len(stories):
            time.sleep(0.3)

    print(f"\n  ✅ {story_graph} stories → Neo4j, {story_vector} stories → Pinecone")

    # ─── Phase 6: Comments (batch for efficiency) ───────────
    print("\n  [7/7] Backfilling Comments...")
    db = _fresh_session(engine)
    comments = db.query(Comment).all()
    db.close()  # Close immediately — we have the data in memory

    comment_graph = 0
    comment_vector = 0

    for i in range(0, len(comments), batch_size):
        batch = comments[i:i + batch_size]
        for c in batch:
            event = _make_event("jira:comment_created", "comment", c.id, c.to_dict())
            result = process_event(event)
            if result.get("graph_synced"):
                comment_graph += 1
            if result.get("vector_indexed"):
                comment_vector += 1

        processed = min(i + batch_size, len(comments))
        print(f"    Progress: {processed}/{len(comments)} comments...", end="\r")

        if i + batch_size < len(comments):
            time.sleep(0.3)

    print(f"\n  ✅ {comment_graph} comments → Neo4j, {comment_vector} comments → Pinecone")

    # ─── Summary ────────────────────────────────────────────
    metrics = get_metrics()
    print("\n" + "=" * 60)
    print("  BACKFILL COMPLETE")
    print("=" * 60)
    print(f"  Events processed:   {metrics['events_processed']}")
    print(f"  Graph nodes synced: {metrics['graph_synced']}")
    print(f"  Vectors indexed:    {metrics['vectors_indexed']}")
    print(f"  Risks detected:     {metrics['risks_detected']}")

    # Verify counts
    print("\n  --- Verification ---")
    try:
        node_counts = get_node_counts()
        total_nodes = sum(node_counts.values())
        print(f"  Neo4j total nodes: {total_nodes}")
        for label, count in sorted(node_counts.items()):
            print(f"    {label:10s} → {count}")
    except Exception as e:
        print(f"  Neo4j verification failed: {e}")

    try:
        vec_count = get_vector_count()
        print(f"  Pinecone vectors:  {vec_count}")
    except Exception as e:
        print(f"  Pinecone verification failed: {e}")

    print("=" * 60)


if __name__ == "__main__":
    backfill()
