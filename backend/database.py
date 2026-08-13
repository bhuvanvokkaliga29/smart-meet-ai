"""
SmartMeet AI v3 — Dual-Mode Database Engine
===========================================
Uses SQLAlchemy to support both the legacy SQLite development mode
and the National Finale PostgreSQL production mode.

Tables:
- meetings
- tasks (legacy + new commitments)
- commitment_events (audit trail for the state machine)
- reminders
"""

import os
import json
from typing import Dict, List, Any
from sqlalchemy import create_engine, text, Column, String, Float, Integer, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings

DATABASE_URL = settings.database_url
if not DATABASE_URL:
    DB_FILE = os.path.join(os.path.dirname(__file__), "smartmeet.db")
    DATABASE_URL = f"sqlite:///{DB_FILE}"

# Using echo=False to avoid massive logging
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ─────────────────────────────────────────────
# Models
# ─────────────────────────────────────────────

class Meeting(Base):
    __tablename__ = "meetings"
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    date = Column(String, nullable=False)
    transcript = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    decisions = Column(String, nullable=False) # JSON string

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True)
    meeting_id = Column(String)
    task = Column(String, nullable=False)
    context = Column(String)
    owner = Column(String, nullable=False)
    deadline = Column(String, nullable=False)
    priority = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    cross_meeting_note = Column(String)

class CommitmentEvent(Base):
    __tablename__ = "commitment_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    commitment_id = Column(String, nullable=False)
    timestamp = Column(String, nullable=False)
    from_state = Column(String)
    to_state = Column(String, nullable=False)
    actor = Column(String, nullable=False)
    component = Column(String, nullable=False)
    detail = Column(String)

class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(String, primary_key=True)
    task_id = Column(String)
    recipient = Column(String, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False)
    sent_at = Column(String)

class OutboxEvent(Base):
    __tablename__ = "outbox"
    id = Column(Integer, primary_key=True, autoincrement=True)
    commitment_id = Column(String, nullable=False)
    action_type = Column(String, nullable=False) # e.g. "create_jira", "send_slack"
    payload = Column(String, nullable=False) # JSON payload
    status = Column(String, default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    error = Column(String)
    retry_count = Column(Integer, default=0)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Seed data if empty
    db = SessionLocal()
    count = db.query(Meeting).count()
    if count == 0:
        seed_db(db)
    db.close()

def seed_db(db):
    m = Meeting(
        id="m-prev-001",
        title="Sprint Planning & Architecture Sync (July 20)",
        date="2026-07-20",
        transcript="Alex: Welcome team. Rahul, please start working on the Auth module by July 25. Priya, we need the initial Database Schema by July 24.",
        summary="Team aligned on Sprint 12 deliverables. Auth module assigned to Rahul, DB Schema to Priya.",
        decisions=json.dumps(["Use FastAPI for backend services", "Adopt Chrome Extension for live tab audio capture"])
    )
    db.add(m)
    
    tasks_seed = [
        Task(id="t-101", meeting_id="m-prev-001", task="Develop Authentication & JWT Module", context="Auth Module", owner="Rahul", deadline="2026-07-25", priority="High", confidence=0.95, status="Completed", cross_meeting_note="Completed during previous sprint."),
        Task(id="t-102", meeting_id="m-prev-001", task="Design Initial PostgreSQL Database Schema", context="DB Architecture", owner="Priya", deadline="2026-07-24", priority="High", confidence=0.92, status="Completed", cross_meeting_note="Completed and committed to repo."),
        Task(id="t-103", meeting_id="m-prev-001", task="Draft OpenAPI Swagger Specification", context="API Specs", owner="Alex", deadline="2026-07-28", priority="Medium", confidence=0.89, status="Pending", cross_meeting_note="Carried over to current meeting."),
        Task(id="t-104", meeting_id="m-prev-001", task="Configure Redis Celery Worker Pipeline", context="Scheduler", owner="Alex", deadline="2026-07-26", priority="High", confidence=0.85, status="Blocked", cross_meeting_note="Blocked waiting for infrastructure setup.")
    ]
    db.add_all(tasks_seed)
    db.commit()

# ─────────────────────────────────────────────
# CRUD Operations
# ─────────────────────────────────────────────

def get_all_meetings() -> List[Dict[str, Any]]:
    db = SessionLocal()
    meetings = db.query(Meeting).all()
    result = []
    for m in meetings:
        d = m.__dict__.copy()
        d.pop("_sa_instance_state", None)
        d["decisions"] = json.loads(d["decisions"])
        result.append(d)
    db.close()
    return result

def save_meeting(meeting: Dict[str, Any]):
    db = SessionLocal()
    # Replace existing or insert new
    existing = db.query(Meeting).filter(Meeting.id == meeting["id"]).first()
    if existing:
        for k, v in meeting.items():
            if k == "decisions" and isinstance(v, list):
                setattr(existing, k, json.dumps(v))
            else:
                setattr(existing, k, v)
    else:
        m = Meeting(
            id=meeting["id"],
            title=meeting["title"],
            date=meeting["date"],
            transcript=meeting["transcript"],
            summary=meeting["summary"],
            decisions=json.dumps(meeting["decisions"])
        )
        db.add(m)
    db.commit()
    db.close()

def get_all_tasks() -> List[Dict[str, Any]]:
    db = SessionLocal()
    tasks = db.query(Task).all()
    result = []
    for t in tasks:
        d = t.__dict__.copy()
        d.pop("_sa_instance_state", None)
        result.append(d)
    db.close()
    return result

def replace_meeting_tasks(meeting_id: str, new_tasks: List[Dict[str, Any]]):
    db = SessionLocal()
    # Remove existing non-completed tasks for this meeting
    # We clear the active board for this meeting to sync it
    db.query(Task).filter(Task.status != 'Completed').delete()
    
    for t in new_tasks:
        existing = db.query(Task).filter(Task.id == t["id"]).first()
        if existing:
            for k, v in t.items():
                setattr(existing, k, v)
        else:
            new_task = Task(
                id=t["id"],
                meeting_id=meeting_id,
                task=t["task"],
                context=t.get("context"),
                owner=t["owner"],
                deadline=t["deadline"],
                priority=t["priority"],
                confidence=t["confidence"],
                status=t.get("status", "Pending"),
                cross_meeting_note=t.get("cross_meeting_note", "Extracted from active meeting pipeline.")
            )
            db.add(new_task)
    db.commit()
    db.close()

def approve_tasks(new_tasks: List[Dict[str, Any]]):
    """
    Transactional boundary: updates task and inserts Outbox event in ONE commit.
    """
    import datetime
    import json
    db = SessionLocal()
    try:
        for t in new_tasks:
            # Upsert task
            existing = db.query(Task).filter(Task.id == t["id"]).first()
            if existing:
                for k, v in t.items():
                    setattr(existing, k, v)
                existing.status = "Sending" # Moving to Sending state for Jira
            else:
                new_task = Task(
                    id=t["id"],
                    meeting_id=t.get("meeting_id"),
                    task=t["task"],
                    context=t.get("context"),
                    owner=t["owner"],
                    deadline=t["deadline"],
                    priority=t["priority"],
                    confidence=t["confidence"],
                    status="Sending",
                    cross_meeting_note=t.get("cross_meeting_note")
                )
                db.add(new_task)
            
            # Create Outbox Event
            payload = {
                "summary": t["task"],
                "assignee": t["owner"],
                "duedate": t["deadline"]
            }
            outbox = OutboxEvent(
                commitment_id=t["id"],
                action_type="create_jira",
                payload=json.dumps(payload),
                status="PENDING",
                created_at=datetime.datetime.utcnow().isoformat(),
                updated_at=datetime.datetime.utcnow().isoformat()
            )
            db.add(outbox)
            
            # Create Audit Event
            audit = CommitmentEvent(
                commitment_id=t["id"],
                timestamp=datetime.datetime.utcnow().isoformat(),
                from_state="Pending Approval",
                to_state="Sending",
                actor="human_approver",
                component="hitl_dashboard",
                detail="Approved by human. Outbox event queued."
            )
            db.add(audit)
            
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def update_task_status(task_id: str, new_status: str):
    db = SessionLocal()
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        old_status = task.status
        task.status = new_status
        
        # Log to audit trail
        import datetime
        evt = CommitmentEvent(
            commitment_id=task_id,
            timestamp=datetime.datetime.utcnow().isoformat(),
            from_state=old_status,
            to_state=new_status,
            actor="human_or_webhook",
            component="state_machine",
            detail=f"Status transitioned from {old_status} to {new_status}"
        )
        db.add(evt)
        
    db.commit()
    db.close()

def get_reminders() -> List[Dict[str, Any]]:
    db = SessionLocal()
    reminders = db.query(Reminder).all()
    result = []
    for r in reminders:
        d = r.__dict__.copy()
        d.pop("_sa_instance_state", None)
        result.append(d)
    db.close()
    return result

def get_commitment_events(commitment_id: str) -> List[Dict[str, Any]]:
    db = SessionLocal()
    events = db.query(CommitmentEvent).filter(CommitmentEvent.commitment_id == commitment_id).order_by(CommitmentEvent.id).all()
    result = []
    for e in events:
        d = e.__dict__.copy()
        d.pop("_sa_instance_state", None)
        result.append(d)
    db.close()
    return result

def hard_delete_user_data(email: str) -> int:
    db = SessionLocal()
    owner_name = email.split('@')[0].capitalize()
    
    r_deleted = db.query(Reminder).filter(Reminder.recipient == email).delete()
    t_deleted = db.query(Task).filter(Task.owner == owner_name).delete()
    
    db.commit()
    db.close()
    return r_deleted + t_deleted

# Initialize tables on load
init_db()
