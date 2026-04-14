"""
Enterprise Project Universe — Mock Jira API
Implements the 10 Jira-compatible TOOL_CONFIG endpoints from HLD v0.4.0 Section 2.3.1.
"""
import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from .database import SessionLocal, User, Team, Project, Sprint, Epic, Story, Comment, AuditLog
from .webhook import dispatch_webhook

app = FastAPI(title="Project Universe — Jira-Compatible Mock API (HLD v0.4.0)")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ─── Pydantic Schemas ───

class UserCreate(BaseModel):
    id: str; email: str; name: str; role: str
    department: Optional[str] = None; team_id: Optional[str] = None

class TeamCreate(BaseModel):
    id: str; name: str; lead_id: Optional[str] = None

class ProjectCreate(BaseModel):
    id: str; key: str; name: str; description: Optional[str] = None; lead_id: str

class SprintCreate(BaseModel):
    id: str; project_id: str; name: str; state: str = "PLANNED"
    start_date: Optional[datetime] = None; end_date: Optional[datetime] = None

class EpicCreate(BaseModel):
    id: str; key: str; project_id: str; title: str
    description: Optional[str] = None; status: str = "OPEN"
    priority: str = "MEDIUM"; reporter_id: str

class StoryCreate(BaseModel):
    id: str; key: str; title: str; reporter_id: str
    epic_id: Optional[str] = None; sprint_id: Optional[str] = None
    description: Optional[str] = None; status: str = "OPEN"
    priority: str = "MEDIUM"; story_points: Optional[int] = None
    assignee_id: Optional[str] = None

class StoryUpdate(BaseModel):
    status: Optional[str] = None; priority: Optional[str] = None
    assignee_id: Optional[str] = None; sprint_id: Optional[str] = None
    story_points: Optional[int] = None

class CommentCreate(BaseModel):
    id: str; story_id: str; author_id: str; body: str

class ChaosRequest(BaseModel):
    chaos_type: str  # TICKET_BLOCKER, DEVELOPER_OVERLOAD, PRIORITY_ESCALATION

# ─── Audit Logging ───

def log_audit(db: Session, entity_type: str, entity_id: str, action: str, details: Dict[str, Any] = None):
    db.add(AuditLog(
        id=f"AUD-{os.urandom(4).hex()}", entity_type=entity_type,
        entity_id=entity_id, action=action, details=details
    ))

# ─── Health ───

@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy", "version": "HLD-v0.4.0", "engine": "Neon Serverless Postgres"}

# ═════════════════════════════════════════════════════════════════════════════
# 10 JIRA-COMPATIBLE TOOL_CONFIG ENDPOINTS (HLD v0.4.0 Section 2.3.1)
# ═════════════════════════════════════════════════════════════════════════════

# 2. search_jira_issues — MUST be defined BEFORE /issues/{issue_key} to avoid
#    FastAPI matching "search" as an issue_key value.
@app.get("/api/v1/issues/search")
def search_jira_issues(
    jql: str = Query(..., description="JQL-like query string"),
    analyze_by_component: bool = Query(False),
    db: Session = Depends(get_db)
):
    query = db.query(Story)
    # Parse simple JQL-like filters
    jql_lower = jql.lower()
    if "status=" in jql_lower:
        status = jql.split("status=")[1].split(" ")[0].strip("'\"")
        query = query.filter(Story.status == status.upper())
    if "priority=" in jql_lower:
        priority = jql.split("priority=")[1].split(" ")[0].strip("'\"")
        query = query.filter(Story.priority == priority.upper())
    if "assignee=" in jql_lower:
        assignee = jql.split("assignee=")[1].split(" ")[0].strip("'\"")
        user = db.query(User).filter(User.email.ilike(f"%{assignee}%")).first()
        if user:
            query = query.filter(Story.assignee_id == user.id)
    if "project=" in jql_lower:
        proj_key = jql.split("project=")[1].split(" ")[0].strip("'\"")
        epics = db.query(Epic.id).join(Project).filter(Project.key == proj_key.upper()).all()
        epic_ids = [e[0] for e in epics]
        if epic_ids:
            query = query.filter(Story.epic_id.in_(epic_ids))

    issues = query.limit(200).all()
    result = {"total": len(issues), "issues": [s.to_dict() for s in issues]}

    if analyze_by_component:
        breakdown = {}
        for s in issues:
            epic = db.query(Epic).filter(Epic.id == s.epic_id).first()
            component = epic.title if epic else "Unassigned"
            breakdown.setdefault(component, {"total": 0, "OPEN": 0, "IN_PROGRESS": 0, "BLOCKED": 0, "CLOSED": 0})
            breakdown[component]["total"] += 1
            if s.status in breakdown[component]:
                breakdown[component][s.status] += 1
        result["component_breakdown"] = breakdown
    return result


# 1. get_jira_issue — Get detailed information about a specific issue by key
#    NOTE: This must be defined AFTER /issues/search to prevent route shadowing.
@app.get("/api/v1/issues/{issue_key}")
def get_jira_issue(issue_key: str, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.key == issue_key).first()
    if not story:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
    result = story.to_dict()
    result["comments"] = [c.to_dict() for c in story.comments] if story.comments else []
    result["reporter"] = story.reporter.to_dict() if story.reporter else None
    result["assignee"] = story.assignee.to_dict() if story.assignee else None
    return result



# 3. get_project_issues — Get all issues for a project with optional status filter
@app.get("/api/v1/projects/{project_key}/issues")
def get_project_issues(project_key: str, status: Optional[str] = None, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.key == project_key.upper()).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_key} not found")
    epics = db.query(Epic).filter(Epic.project_id == project.id).all()
    epic_ids = [e.id for e in epics]
    query = db.query(Story).filter(Story.epic_id.in_(epic_ids))
    if status:
        query = query.filter(Story.status == status.upper())
    stories = query.all()
    return {"project": project.to_dict(), "total": len(stories), "issues": [s.to_dict() for s in stories]}

# 4. get_user_issues — Get issues assigned to a specific user
@app.get("/api/v1/users/{username}/issues")
def get_user_issues(username: str = "currentUser", db: Session = Depends(get_db)):
    user = db.query(User).filter((User.email.ilike(f"%{username}%")) | (User.name.ilike(f"%{username}%"))).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {username} not found")
    stories = db.query(Story).filter(Story.assignee_id == user.id).all()
    return {"user": user.to_dict(), "total": len(stories), "issues": [s.to_dict() for s in stories]}

# 5. get_sprint_issues — Get all issues in a sprint
@app.get("/api/v1/sprints/issues")
def get_sprint_issues(sprint_name: Optional[str] = None, db: Session = Depends(get_db)):
    if sprint_name:
        sprint = db.query(Sprint).filter(Sprint.name.ilike(f"%{sprint_name}%")).first()
    else:
        sprint = db.query(Sprint).filter(Sprint.state == "ACTIVE").first()
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint not found")
    stories = db.query(Story).filter(Story.sprint_id == sprint.id).all()
    return {"sprint": sprint.to_dict(), "total": len(stories), "issues": [s.to_dict() for s in stories]}

# 6. get_issue_comments — Get all comments for a specific issue
@app.get("/api/v1/issues/{issue_key}/comments")
def get_issue_comments(issue_key: str, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.key == issue_key).first()
    if not story:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
    comments = db.query(Comment).filter(Comment.story_id == story.id).order_by(Comment.created_at).all()
    return {"issue_key": issue_key, "total": len(comments), "comments": [c.to_dict() for c in comments]}

# 7. get_issue_transitions — Get available status transitions for an issue
@app.get("/api/v1/issues/{issue_key}/transitions")
def get_issue_transitions(issue_key: str, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.key == issue_key).first()
    if not story:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
    transitions_map = {
        "OPEN": ["IN_PROGRESS"],
        "IN_PROGRESS": ["BLOCKED", "CLOSED"],
        "BLOCKED": ["OPEN", "IN_PROGRESS"],
        "CLOSED": ["OPEN"]
    }
    return {
        "issue_key": issue_key,
        "current_status": story.status,
        "available_transitions": transitions_map.get(story.status, [])
    }

# 8. get_issue_attachments — Get attachments metadata for an issue
@app.get("/api/v1/issues/{issue_key}/attachments")
def get_issue_attachments(issue_key: str, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.key == issue_key).first()
    if not story:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
    # Simulator does not store real files; returns metadata stub
    return {"issue_key": issue_key, "attachments": [], "message": "No attachments in simulator mode"}

# 9. get_project_summary — Get project summary with issue counts by status
@app.get("/api/v1/projects/{project_key}/summary")
def get_project_summary(project_key: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.key == project_key.upper()).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_key} not found")
    epics = db.query(Epic).filter(Epic.project_id == project.id).all()
    epic_ids = [e.id for e in epics]
    stories = db.query(Story).filter(Story.epic_id.in_(epic_ids)).all()
    counts = {"OPEN": 0, "IN_PROGRESS": 0, "BLOCKED": 0, "CLOSED": 0}
    for s in stories:
        if s.status in counts:
            counts[s.status] += 1
    return {
        "project": project.to_dict(),
        "total_issues": len(stories),
        "total_epics": len(epics),
        "status_counts": counts
    }

# 10. download_issue_logs — Get audit logs for a specific issue
@app.get("/api/v1/issues/{issue_key}/logs")
def download_issue_logs(issue_key: str, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.key == issue_key).first()
    if not story:
        raise HTTPException(status_code=404, detail=f"Issue {issue_key} not found")
    logs = db.query(AuditLog).filter(
        AuditLog.entity_type == "story", AuditLog.entity_id == story.id
    ).order_by(AuditLog.timestamp).all()
    return {"issue_key": issue_key, "total": len(logs), "logs": [l.to_dict() for l in logs]}

# ═══════════════════════════════════════════════════════════════════════════════
# CRUD ENDPOINTS (used by Timeline Simulator and Chaos Engine internally)
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/users")
def list_users(db: Session = Depends(get_db), limit: int = 200):
    return [u.to_dict() for u in db.query(User).limit(limit).all()]

@app.post("/api/v1/users")
def create_user(user: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_user = User(**user.dict())
    db.add(db_user)
    log_audit(db, "user", db_user.id, "CREATE")
    db.commit(); db.refresh(db_user)
    background_tasks.add_task(dispatch_webhook, "jira:user_created", "user", db_user.id, db_user.to_dict())
    return db_user.to_dict()

@app.post("/api/v1/teams")
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    db_team = Team(**team.dict())
    db.add(db_team)
    log_audit(db, "team", db_team.id, "CREATE")
    db.commit(); db.refresh(db_team)
    return db_team.to_dict()

@app.post("/api/v1/projects")
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_proj = Project(**project.dict())
    db.add(db_proj)
    log_audit(db, "project", db_proj.id, "CREATE")
    db.commit(); db.refresh(db_proj)
    return db_proj.to_dict()

@app.post("/api/v1/sprints")
def create_sprint(sprint: SprintCreate, db: Session = Depends(get_db)):
    db_sprint = Sprint(**sprint.dict())
    db.add(db_sprint)
    log_audit(db, "sprint", db_sprint.id, "CREATE")
    db.commit(); db.refresh(db_sprint)
    return db_sprint.to_dict()

@app.post("/api/v1/epics")
def create_epic(epic: EpicCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_epic = Epic(**epic.dict())
    db.add(db_epic)
    log_audit(db, "epic", db_epic.id, "CREATE")
    db.commit(); db.refresh(db_epic)
    background_tasks.add_task(dispatch_webhook, "jira:epic_created", "epic", db_epic.id, db_epic.to_dict())
    return db_epic.to_dict()

@app.get("/api/v1/stories")
def list_stories(db: Session = Depends(get_db), limit: int = 200, skip: int = 0):
    return [s.to_dict() for s in db.query(Story).offset(skip).limit(limit).all()]

@app.post("/api/v1/stories")
def create_story(story: StoryCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_story = Story(**story.dict())
    db.add(db_story)
    log_audit(db, "story", db_story.id, "CREATE")
    db.commit(); db.refresh(db_story)
    background_tasks.add_task(dispatch_webhook, "jira:issue_created", "story", db_story.id, db_story.to_dict())
    return db_story.to_dict()

@app.patch("/api/v1/stories/{story_id}")
def update_story(story_id: str, updates: StoryUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    changes = {}
    if updates.status is not None:
        changes["status"] = {"from": story.status, "to": updates.status}
        story.status = updates.status
        if updates.status == "CLOSED":
            story.resolution_date = datetime.utcnow()
    if updates.priority is not None:
        changes["priority"] = {"from": story.priority, "to": updates.priority}
        story.priority = updates.priority
    if updates.assignee_id is not None:
        changes["assignee_id"] = {"from": story.assignee_id, "to": updates.assignee_id}
        story.assignee_id = updates.assignee_id
    if updates.sprint_id is not None:
        changes["sprint_id"] = {"from": story.sprint_id, "to": updates.sprint_id}
        story.sprint_id = updates.sprint_id
    if updates.story_points is not None:
        story.story_points = updates.story_points
    log_audit(db, "story", story_id, "UPDATE", changes)
    db.commit(); db.refresh(story)
    background_tasks.add_task(dispatch_webhook, "jira:issue_updated", "story", story_id, story.to_dict())
    return story.to_dict()

@app.post("/api/v1/comments")
def create_comment(comment: CommentCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_comment = Comment(**comment.dict())
    db.add(db_comment)
    log_audit(db, "comment", db_comment.id, "CREATE")
    db.commit(); db.refresh(db_comment)
    background_tasks.add_task(dispatch_webhook, "jira:comment_created", "comment", db_comment.id, db_comment.to_dict())
    return db_comment.to_dict()

@app.get("/api/v1/audit")
def get_audit_logs(db: Session = Depends(get_db), limit: int = 1000):
    return [a.to_dict() for a in db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()]

# ─── God Mode Console endpoint (HLD Section 4.6) ───
@app.post("/api/v1/chaos/trigger")
def trigger_chaos(req: ChaosRequest, background_tasks: BackgroundTasks):
    from .chaos_engine import inject_ticket_blocker, inject_developer_overload, inject_priority_escalation
    handlers = {
        "TICKET_BLOCKER": inject_ticket_blocker,
        "DEVELOPER_OVERLOAD": inject_developer_overload,
        "PRIORITY_ESCALATION": inject_priority_escalation
    }
    handler = handlers.get(req.chaos_type)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown chaos type: {req.chaos_type}")
    background_tasks.add_task(handler)
    return {"status": "injecting", "chaos_type": req.chaos_type}