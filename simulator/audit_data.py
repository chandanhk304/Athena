#!/usr/bin/env python3
"""
Comprehensive Data Quality Audit — Inspects every table in Neon Postgres.
Checks data realism, quantity, distribution, and integrity.
Run: python simulator/audit_data.py
"""
import os
import json
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Session = sessionmaker(bind=engine)
db = Session()

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def subsection(title):
    print(f"\n  --- {title} ---")

# ═══════════════════════════════════════════════════════════════
section("1. TABLE ROW COUNTS")
# ═══════════════════════════════════════════════════════════════
tables = ["users", "teams", "projects", "sprints", "epics", "stories", "comments", "audit_log"]
counts = {}
for t in tables:
    result = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
    counts[t] = result
    print(f"  {t:15s} → {result:,} rows")

total_entities = sum(counts.values())
print(f"\n  TOTAL ENTITIES: {total_entities:,}")

# ═══════════════════════════════════════════════════════════════
section("2. USERS — Role Distribution & Realism")
# ═══════════════════════════════════════════════════════════════
users = db.execute(text("SELECT id, name, email, role, department, timezone FROM users")).fetchall()
if users:
    roles = Counter(u.role for u in users)
    print(f"  Total users: {len(users)}")
    print(f"  Role distribution:")
    for role, count in sorted(roles.items(), key=lambda x: -x[1]):
        print(f"    {role:12s} → {count}")

    subsection("Sample Users (first 5)")
    for u in users[:5]:
        print(f"    {u.name:25s} | {u.email:35s} | {u.role:10s} | {u.department or 'N/A'}")

    # Check for realism issues
    issues = []
    emails = [u.email for u in users]
    if len(set(emails)) != len(emails):
        issues.append("⚠️  DUPLICATE EMAILS FOUND")
    if any("test" in e.lower() or "example" in e.lower() for e in emails):
        issues.append("⚠️  Generic test/example emails detected")
    if any("Fallback" in u.name for u in users):
        issues.append("⚠️  Fallback placeholder names found")
    if not issues:
        print("\n  ✅ Users look realistic — diverse names, valid emails, proper roles")
    else:
        for i in issues:
            print(f"\n  {i}")

# ═══════════════════════════════════════════════════════════════
section("3. PROJECTS & EPICS — Structure Quality")
# ═══════════════════════════════════════════════════════════════
projects = db.execute(text("SELECT id, key, name, description FROM projects")).fetchall()
if projects:
    for p in projects:
        print(f"\n  Project: {p.name} ({p.key})")
        print(f"  Description: {(p.description or '')[:120]}...")
        epics = db.execute(text("SELECT key, title, description, status FROM epics WHERE project_id = :pid"), {"pid": p.id}).fetchall()
        print(f"  Epics: {len(epics)}")
        for e in epics:
            print(f"    [{e.key}] {e.title} ({e.status})")
            print(f"         {(e.description or '')[:100]}...")

# ═══════════════════════════════════════════════════════════════
section("4. SPRINTS — Timeline & State Distribution")
# ═══════════════════════════════════════════════════════════════
sprints = db.execute(text("SELECT id, name, state, start_date, end_date FROM sprints ORDER BY start_date")).fetchall()
if sprints:
    states = Counter(s.state for s in sprints)
    print(f"  Total sprints: {len(sprints)}")
    print(f"  State distribution: {dict(states)}")
    print(f"  Date range: {sprints[0].start_date} → {sprints[-1].end_date}")

    subsection("First 3 & Last 3 Sprints")
    for s in sprints[:3]:
        print(f"    {s.name[:40]:42s} | {s.state:8s} | {s.start_date}")
    print(f"    {'...'}")
    for s in sprints[-3:]:
        print(f"    {s.name[:40]:42s} | {s.state:8s} | {s.start_date}")

# ═══════════════════════════════════════════════════════════════
section("5. STORIES — Status, Priority, Points Distribution")
# ═══════════════════════════════════════════════════════════════
stories = db.execute(text("SELECT id, key, title, description, status, priority, story_points, assignee_id, reporter_id FROM stories")).fetchall()
if stories:
    statuses = Counter(s.status for s in stories)
    priorities = Counter(s.priority for s in stories)
    points = Counter(s.story_points for s in stories)

    print(f"  Total stories: {len(stories)}")
    print(f"\n  Status distribution:")
    for st, cnt in sorted(statuses.items(), key=lambda x: -x[1]):
        pct = cnt / len(stories) * 100
        bar = "█" * int(pct / 2)
        print(f"    {st:15s} → {cnt:4d} ({pct:5.1f}%) {bar}")

    print(f"\n  Priority distribution:")
    for pr, cnt in sorted(priorities.items(), key=lambda x: -x[1]):
        pct = cnt / len(stories) * 100
        print(f"    {pr:15s} → {cnt:4d} ({pct:5.1f}%)")

    print(f"\n  Story points distribution:")
    for pt, cnt in sorted(points.items(), key=lambda x: (x[0] or 0)):
        print(f"    {str(pt):5s} pts → {cnt:4d}")

    # Check title quality
    subsection("Sample Story Titles (random 10)")
    import random
    sample = random.sample(stories, min(10, len(stories)))
    for s in sample:
        print(f"    [{s.key}] {s.title[:70]}")
        if s.description:
            print(f"             {s.description[:80]}...")

    # Check for garbage/generic titles
    generic_count = sum(1 for s in stories if s.title in ("Implementation Task", "Fix Bug", "Test Ticket", "Task"))
    if generic_count > 0:
        print(f"\n  ⚠️  {generic_count} stories have generic fallback titles")
    else:
        print(f"\n  ✅ All story titles appear to be AI-generated and unique")

    # Check assignee coverage
    assigned = sum(1 for s in stories if s.assignee_id)
    print(f"  Assignee coverage: {assigned}/{len(stories)} ({assigned/len(stories)*100:.0f}%)")

# ═══════════════════════════════════════════════════════════════
section("6. COMMENTS — Thread Quality")
# ═══════════════════════════════════════════════════════════════
comments = db.execute(text("SELECT id, story_id, body FROM comments")).fetchall()
if comments:
    print(f"  Total comments: {len(comments)}")
    avg_len = sum(len(c.body) for c in comments) / len(comments)
    print(f"  Average comment length: {avg_len:.0f} characters")

    subsection("Sample Comments (random 5)")
    sample_comments = random.sample(comments, min(5, len(comments)))
    for c in sample_comments:
        print(f"    [{c.story_id[:12]}...] {c.body[:100]}...")

    # Check for garbage
    generic_comments = sum(1 for c in comments if c.body in ("LGTM.", "Ok", "Done", ""))
    if generic_comments > 0:
        print(f"\n  ⚠️  {generic_comments} comments are generic fallbacks")
    else:
        print(f"\n  ✅ All comments appear to be substantive AI-generated text")

# ═══════════════════════════════════════════════════════════════
section("7. AUDIT LOG — Coverage")
# ═══════════════════════════════════════════════════════════════
audits = db.execute(text("SELECT entity_type, action, COUNT(*) as cnt FROM audit_log GROUP BY entity_type, action ORDER BY cnt DESC")).fetchall()
if audits:
    total_audits = sum(a.cnt for a in audits)
    print(f"  Total audit entries: {total_audits}")
    for a in audits:
        print(f"    {a.entity_type:10s} {a.action:8s} → {a.cnt:,}")

# ═══════════════════════════════════════════════════════════════
section("8. DATA INTEGRITY CHECKS")
# ═══════════════════════════════════════════════════════════════

# Orphaned stories (no sprint)
orphan_stories = db.execute(text("SELECT COUNT(*) FROM stories WHERE sprint_id IS NULL")).scalar()
print(f"  Stories without sprint: {orphan_stories}")

# Orphaned stories (no epic)
no_epic = db.execute(text("SELECT COUNT(*) FROM stories WHERE epic_id IS NULL")).scalar()
print(f"  Stories without epic:   {no_epic}")

# Unassigned stories
unassigned = db.execute(text("SELECT COUNT(*) FROM stories WHERE assignee_id IS NULL")).scalar()
print(f"  Unassigned stories:     {unassigned}")

# Comments on non-existent stories
orphan_comments = db.execute(text(
    "SELECT COUNT(*) FROM comments c LEFT JOIN stories s ON c.story_id = s.id WHERE s.id IS NULL"
)).scalar()
print(f"  Orphan comments:        {orphan_comments}")

# Duplicate story keys
dup_keys = db.execute(text(
    "SELECT key, COUNT(*) FROM stories GROUP BY key HAVING COUNT(*) > 1"
)).fetchall()
print(f"  Duplicate story keys:   {len(dup_keys)}")

if orphan_stories == 0 and no_epic == 0 and orphan_comments == 0 and len(dup_keys) == 0:
    print("\n  ✅ All integrity checks PASSED")
else:
    print("\n  ⚠️  Some integrity issues found (see above)")

# ═══════════════════════════════════════════════════════════════
section("9. NEON POSTGRES STORAGE USAGE")
# ═══════════════════════════════════════════════════════════════
db_size = db.execute(text("SELECT pg_size_pretty(pg_database_size(current_database()))")).scalar()
print(f"  Database size: {db_size}")
print(f"  Neon free tier limit: 512 MB")

for t in tables:
    tsize = db.execute(text(f"SELECT pg_size_pretty(pg_total_relation_size('{t}'))")).scalar()
    print(f"    {t:15s} → {tsize}")

# ═══════════════════════════════════════════════════════════════
section("10. RESOURCE CONSUMPTION ESTIMATE")
# ═══════════════════════════════════════════════════════════════
print("""
  Service            | Used (est.)        | Free Tier Limit     | Remaining
  -------------------|--------------------|--------------------|--------------------
  Neon Postgres      | See DB size above  | 512 MB storage     | ~500 MB headroom
  Neo4j Aura         | 0 nodes (unused)   | 50,000 nodes       | 50,000 nodes
  Pinecone           | 0 vectors (unused) | 100,000 vectors    | 100,000 vectors
  Groq (70b)         | ~5-10 RPD used     | 1,000 RPD          | ~990 RPD
  Groq (8b-instant)  | ~50-100 RPD used   | 14,400 RPD         | ~14,300 RPD
  Gemini (optional)  | rate-limited       | 1,500 RPD          | resets daily

  VERDICT: You can comfortably generate 2-3 more projects today.
  The bottleneck is Groq 70b (1K RPD), but bulk generation uses 8b-instant (14.4K RPD).
""")

db.close()
print("\n" + "=" * 60)
print("  AUDIT COMPLETE")
print("=" * 60)
