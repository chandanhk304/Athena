import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/athena_sim"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# ─── 8 ORM Models (HLD v0.4.0 Section 3.4) ───

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)        # developer, pm, qa, lead, vp
    department = Column(String, nullable=True)    # Engineering, QA, Management
    team_id = Column(String, ForeignKey("teams.id", name="fk_user_team"), nullable=True)
    timezone = Column(String, default="UTC")
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", foreign_keys=[team_id])

    def to_dict(self):
        return {
            "id": self.id, "email": self.email, "name": self.name,
            "role": self.role, "department": self.department,
            "team_id": self.team_id, "timezone": self.timezone,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Team(Base):
    __tablename__ = "teams"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    lead_id = Column(String, ForeignKey("users.id", name="fk_team_lead", use_alter=True), nullable=True)

    lead = relationship("User", foreign_keys=[lead_id])

    def to_dict(self):
        return {"id": self.id, "name": self.name, "lead_id": self.lead_id}

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    lead_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "key": self.key, "name": self.name,
            "description": self.description, "lead_id": self.lead_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Sprint(Base):
    __tablename__ = "sprints"
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey("projects.id"))
    name = Column(String, nullable=False)
    state = Column(String, default="PLANNED")  # PLANNED, ACTIVE, CLOSED
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)

    project = relationship("Project")

    def to_dict(self):
        return {
            "id": self.id, "project_id": self.project_id, "name": self.name,
            "state": self.state,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }

class Epic(Base):
    __tablename__ = "epics"
    id = Column(String, primary_key=True)
    key = Column(String, unique=True, index=True, nullable=False)
    project_id = Column(String, ForeignKey("projects.id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="OPEN")      # OPEN, IN_PROGRESS, CLOSED
    priority = Column(String, default="MEDIUM")
    reporter_id = Column(String, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "key": self.key, "project_id": self.project_id,
            "title": self.title, "description": self.description,
            "status": self.status, "priority": self.priority,
            "reporter_id": self.reporter_id,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class Story(Base):
    """Work item (ticket) — HLD Section 5.2 Story Class"""
    __tablename__ = "stories"
    id = Column(String, primary_key=True)
    key = Column(String, unique=True, index=True, nullable=False)
    epic_id = Column(String, ForeignKey("epics.id"), nullable=True)
    sprint_id = Column(String, ForeignKey("sprints.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="OPEN")       # OPEN, IN_PROGRESS, BLOCKED, CLOSED
    priority = Column(String, default="MEDIUM")   # LOW, MEDIUM, HIGH, CRITICAL
    story_points = Column(Integer, nullable=True)
    reporter_id = Column(String, ForeignKey("users.id"))
    assignee_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolution_date = Column(DateTime, nullable=True)

    epic = relationship("Epic")
    sprint = relationship("Sprint")
    reporter = relationship("User", foreign_keys=[reporter_id])
    assignee = relationship("User", foreign_keys=[assignee_id])
    comments = relationship("Comment", back_populates="story")

    def to_dict(self):
        return {
            "id": self.id, "key": self.key, "epic_id": self.epic_id,
            "sprint_id": self.sprint_id, "title": self.title,
            "description": self.description, "status": self.status,
            "priority": self.priority, "story_points": self.story_points,
            "reporter_id": self.reporter_id, "assignee_id": self.assignee_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None
        }

class Comment(Base):
    __tablename__ = "comments"
    id = Column(String, primary_key=True)
    story_id = Column(String, ForeignKey("stories.id"))
    author_id = Column(String, ForeignKey("users.id"))
    body = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    story = relationship("Story", back_populates="comments")

    def to_dict(self):
        return {
            "id": self.id, "story_id": self.story_id,
            "author_id": self.author_id, "body": self.body,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class AuditLog(Base):
    __tablename__ = "audit_log"
    id = Column(String, primary_key=True)
    entity_type = Column(String, nullable=False)  # user/team/project/sprint/epic/story/comment
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)        # CREATE, UPDATE, DELETE
    details = Column(JSON, nullable=True)          # Changed fields with old/new values
    timestamp = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "entity_type": self.entity_type,
            "entity_id": self.entity_id, "action": self.action,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Enterprise PostgreSQL schema initialized (HLD v0.4.0 compliant).")

if __name__ == "__main__":
    init_db()
