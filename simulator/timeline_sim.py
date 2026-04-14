"""
Enterprise Timeline Simulator — Populates Neon Postgres with 12 months of AI-generated data.
Supports multiple projects via CLI: python -m simulator.timeline_sim --projects 3
"""
import os
import sys
import random
import argparse
from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session
from .database import SessionLocal, User, Team, Project, Sprint, Epic, Story, Comment, AuditLog, init_db
from .data_gen import (
    generate_realistic_users, generate_core_project,
    generate_realistic_stories_batch, generate_realistic_comments_batch
)
from .webhook import replay_historical_event, get_webhook_stats

HISTORY_MONTHS = 12
SPRINT_LENGTH_DAYS = 14

# Valid statuses per HLD v0.4.0
STATUSES = ["OPEN", "IN_PROGRESS", "BLOCKED", "CLOSED"]
PRIORITIES = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
DEPARTMENTS = ["Engineering", "QA", "Product", "Design", "Infrastructure", "Security"]

def log_audit(db: Session, entity_type: str, entity_id: str, action: str, details: dict = None):
    """Write an AuditLog entry — ensures endpoint #10 (download_issue_logs) has data."""
    db.add(AuditLog(
        id=f"AUD-{uuid.uuid4().hex[:8]}", entity_type=entity_type,
        entity_id=entity_id, action=action, details=details
    ))


def create_bootstrap_data(db: Session, project_index: int = 1):
    """Generate users, team, project, and epics entirely via LLM. No hardcoded data."""
    print(f"\n{'='*60}")
    print(f"  BOOTSTRAPPING PROJECT {project_index}")
    print(f"{'='*60}")

    # 1. Generate Users (only for the first project; reuse across projects)
    if project_index == 1:
        # ── Guard: skip user creation if users already exist in DB ───
        existing_users = db.query(User).all()
        if existing_users:
            print(f"  ℹ️  Found {len(existing_users)} existing users in DB — skipping user generation.")
            print(f"     (Run with --reset to wipe and regenerate all data)")
            users = existing_users
        else:
            print("  -> Asking AI to invent 20 corporate employees...")
            ai_users = generate_realistic_users(count=20)
            if not ai_users:
                print("  ❌ LLM returned no users! Check your GROQ_API_KEY.")
                sys.exit(1)
            users = []
            seen_emails = set()
            for ud in ai_users:
                email = ud.get("email", f"dev{random.randint(100,999)}@corp.com")
                # Ensure email uniqueness (LLM sometimes generates duplicates)
                if email in seen_emails:
                    email = f"{uuid.uuid4().hex[:4]}.{email}"
                seen_emails.add(email)
                u = User(
                    id=f"USR-{uuid.uuid4().hex[:8]}",
                    name=ud.get("name", "Fallback Name"),
                    email=email,
                    role=ud.get("role", "DEV"),
                    department=random.choice(DEPARTMENTS),
                    timezone=random.choice(["UTC", "US/Eastern", "US/Pacific", "Europe/London", "Asia/Kolkata"])
                )
                db.add(u)
                users.append(u)
                log_audit(db, "user", u.id, "CREATE", {"name": u.name, "role": u.role})
            db.commit()
            print(f"  ✅ Created {len(users)} AI-generated users")
    else:
        users = db.query(User).all()
        print(f"  -> Reusing {len(users)} existing users across projects")

    # 2. Generate Project and Epics via LLM
    print("  -> Asking AI to invent an enterprise software project...")
    ai_proj = generate_core_project()
    p_name = ai_proj.get("project_name", f"Enterprise Platform {project_index}")
    p_key = ai_proj.get("project_key", f"PRJ{project_index}")

    # Ensure unique project key
    existing = db.query(Project).filter(Project.key == p_key).first()
    if existing:
        p_key = f"{p_key}{project_index}"

    team = Team(id=f"TEM-{uuid.uuid4().hex[:8]}", name=f"{p_name} Core Team", lead_id=users[0].id)
    db.add(team)

    proj = Project(
        id=f"PRJ-{uuid.uuid4().hex[:8]}", key=p_key, name=p_name,
        description=ai_proj.get("description", ""), lead_id=users[0].id
    )
    db.add(proj)
    log_audit(db, "project", proj.id, "CREATE", {"name": p_name, "key": p_key})
    db.commit()  # Flush Team + Project BEFORE adding Epics (FK dependency)

    epics = []
    epic_data = ai_proj.get("epics", [])
    if not epic_data:
        epic_data = [{"title": "Core Infrastructure", "description": "Backend services"}]

    for i, ep in enumerate(epic_data):
        e = Epic(
            id=f"EPC-{uuid.uuid4().hex[:8]}", key=f"{p_key}-E{i+1}",
            project_id=proj.id, title=ep.get("title", "Unknown Epic"),
            description=ep.get("description", ""), reporter_id=users[0].id
        )
        db.add(e)
        epics.append(e)
        log_audit(db, "epic", e.id, "CREATE", {"title": e.title})

    db.commit()
    print(f"  ✅ Created project '{p_name}' ({p_key}) with {len(epics)} epics")
    return users, team, proj, epics


def simulate_timeline(db: Session, users, proj, epics):
    """
    Generate 12 months of sprints with AI-written stories in mixed statuses.
    The most recent sprint is ACTIVE with OPEN/IN_PROGRESS/BLOCKED tickets.
    All older sprints are CLOSED with mostly CLOSED tickets.
    """
    print(f"\n  Simulating {HISTORY_MONTHS} months of history for '{proj.name}'...")
    start_date = datetime.utcnow() - timedelta(days=HISTORY_MONTHS * 30)
    current_date = start_date

    sprint_num = 1
    story_counter = 1
    total_comments = 0

    # Calculate total sprints to know which is the last one
    total_sprints = int((HISTORY_MONTHS * 30) / SPRINT_LENGTH_DAYS)

    while current_date < datetime.utcnow():
        sprint_end = current_date + timedelta(days=SPRINT_LENGTH_DAYS)
        is_last_sprint = sprint_num >= total_sprints
        is_recent = sprint_num >= total_sprints - 1  # Last 2 sprints have mixed statuses

        sprint_state = "ACTIVE" if is_last_sprint else "CLOSED"
        print(f"\n  --- Sprint {sprint_num}/{total_sprints} ({current_date.date()} to {sprint_end.date()}) [{sprint_state}] ---")

        sprint = Sprint(
            id=f"SPR-{uuid.uuid4().hex[:8]}", project_id=proj.id,
            name=f"{proj.name} Sprint {sprint_num}", state=sprint_state,
            start_date=current_date, end_date=sprint_end
        )
        db.add(sprint)
        log_audit(db, "sprint", sprint.id, "CREATE", {"name": sprint.name, "state": sprint_state})
        db.commit()  # Flush Sprint BEFORE adding Stories (FK: story.sprint_id -> sprint.id)

        # Generate stories — batch for speed
        num_stories = random.randint(8, 15)
        epic = random.choice(epics)
        print(f"  -> Generating {num_stories} AI stories under '{epic.title}'...")

        ai_stories = generate_realistic_stories_batch(epic.title, count=num_stories)
        if not ai_stories:
            print(f"  ⚠️  LLM returned 0 stories (rate limit?). Continuing to next sprint...")
            sprint_num += 1
            current_date = sprint_end
            continue

        for sd in ai_stories:
            # Assign realistic mixed statuses
            if is_recent:
                # Recent sprints: distribute across all statuses
                status = random.choices(
                    STATUSES, weights=[15, 35, 10, 40], k=1
                )[0]
            else:
                # Historical sprints: mostly closed with a few lingering open
                status = random.choices(
                    STATUSES, weights=[3, 2, 2, 93], k=1
                )[0]

            # Filter users by role for assignment
            dev_users = [u for u in users if u.role in ("DEV", "QA", "TECH_LEAD")]
            pm_users = [u for u in users if u.role in ("PM", "TECH_LEAD", "VP")]
            assignee = random.choice(dev_users) if dev_users else random.choice(users)
            reporter = random.choice(pm_users) if pm_users else random.choice(users)

            story_created = current_date + timedelta(days=random.randint(0, 3))
            story_resolved = story_created + timedelta(days=random.randint(1, 12)) if status == "CLOSED" else None

            story = Story(
                id=f"STR-{uuid.uuid4().hex[:8]}", key=f"{proj.key}-{story_counter}",
                epic_id=epic.id, sprint_id=sprint.id,
                title=sd.get("title", "Implementation Task"),
                description=sd.get("description", ""),
                status=status,
                priority=sd.get("priority", random.choice(PRIORITIES)),
                story_points=sd.get("story_points", random.choice([1, 2, 3, 5, 8, 13])),
                reporter_id=reporter.id, assignee_id=assignee.id,
                created_at=story_created, updated_at=story_resolved or story_created,
                resolution_date=story_resolved
            )
            db.add(story)

            # AuditLog: CREATE
            log_audit(db, "story", story.id, "CREATE", {
                "title": story.title, "status": story.status, "priority": story.priority,
                "assignee": assignee.email
            })

            # AuditLog: simulate status transitions for CLOSED tickets
            if status == "CLOSED":
                log_audit(db, "story", story.id, "UPDATE", {
                    "status": {"from": "OPEN", "to": "IN_PROGRESS"}
                })
                log_audit(db, "story", story.id, "UPDATE", {
                    "status": {"from": "IN_PROGRESS", "to": "CLOSED"}
                })

            story_counter += 1

            # Fire historical webhook
            replay_historical_event("jira:issue_created", "story", story.id, story.to_dict(), story_created)

            # Generate threaded comments
            num_comments = random.randint(1, 3)
            ai_comments = generate_realistic_comments_batch(story.title, count=num_comments)

            for cd in (ai_comments or []):
                body_text = cd.get("body", "") if isinstance(cd, dict) else str(cd)
                if not body_text:
                    continue
                cmt_created = story_created + timedelta(days=random.randint(1, 8))
                c = Comment(
                    id=f"CMT-{uuid.uuid4().hex[:8]}", story_id=story.id,
                    author_id=random.choice(users).id,
                    body=body_text, created_at=cmt_created
                )
                db.add(c)
                log_audit(db, "comment", c.id, "CREATE", {"story_id": story.id})
                replay_historical_event("jira:comment_created", "comment", c.id,
                                        {"story_id": story.id, "body": c.body}, cmt_created)
                total_comments += 1

        try:
            db.commit()  # Commit per sprint for safety
        except Exception as e:
            print(f"  ❌ DB commit failed for Sprint {sprint_num}: {e}")
            db.rollback()
        sprint_num += 1
        current_date = sprint_end

    print(f"\n  ✅ Project '{proj.name}' complete: {story_counter-1} stories, {total_comments} comments, {sprint_num-1} sprints")
    return story_counter - 1, total_comments


def main():
    parser = argparse.ArgumentParser(description="Athena Enterprise Timeline Simulator")
    parser.add_argument("--projects", type=int, default=1, help="Number of projects to generate (default: 1)")
    parser.add_argument("--months", type=int, default=12, help="Months of history to simulate (default: 12)")
    parser.add_argument("--reset", action="store_true", help="Drop all tables and start fresh (cleans up failed runs)")
    args = parser.parse_args()

    global HISTORY_MONTHS
    HISTORY_MONTHS = args.months

    print("=" * 60)
    print("  ATHENA — ENTERPRISE TIMELINE SIMULATOR")
    print(f"  Projects: {args.projects} | History: {args.months} months")
    print("=" * 60)

    db = SessionLocal()

    if args.reset:
        from .database import engine
        from sqlalchemy import text
        print("\n  ⚠️  Dropping all tables (--reset)...")
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
            conn.commit()
        print("  ✅ Tables dropped. Recreating...")

    init_db()

    grand_total_stories = 0
    grand_total_comments = 0

    for i in range(1, args.projects + 1):
        users, team, proj, epics = create_bootstrap_data(db, project_index=i)
        stories, comments = simulate_timeline(db, users, proj, epics)
        grand_total_stories += stories
        grand_total_comments += comments

    db.close()

    stats = get_webhook_stats()
    print("\n" + "=" * 60)
    print("  SIMULATION COMPLETE")
    print(f"  Total Projects:  {args.projects}")
    print(f"  Total Stories:   {grand_total_stories}")
    print(f"  Total Comments:  {grand_total_comments}")
    print(f"  Webhooks Sent:   {stats['dispatched']}")
    print(f"  Webhooks Dropped:{stats['dropped']} (Athena Core offline — expected)")
    print("=" * 60)


if __name__ == "__main__":
    main()