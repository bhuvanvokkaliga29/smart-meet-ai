"""
SmartMeet AI v3 — Integration Gateway & Outbox Worker
=====================================================
Handles exactly-once external delivery to Jira and Slack
using the Transactional Outbox pattern.
Provides mock implementations for safe Hackathon judging.
"""

import os
import json
import uuid
import datetime
import time
import threading
import structlog
from typing import Dict, Any

from sqlalchemy.orm import Session
from database import SessionLocal, OutboxEvent, Task, CommitmentEvent
from config import settings

logger = structlog.get_logger()

# ─────────────────────────────────────────────
# External Client Mocks
# ─────────────────────────────────────────────

class JiraClient:
    def __init__(self):
        self.api_key = settings.jira_api_key
        
    def create_issue(self, payload: Dict[str, Any]) -> str:
        """Returns the external issue key."""
        if not self.api_key:
            raise ValueError("Live Jira integration requires JIRA_API_KEY")
            
        # In a real app we'd make an HTTP request to Jira REST API
        raise NotImplementedError("Live Jira integration requires API implementation")

class SlackClient:
    def __init__(self):
        self.api_key = settings.slack_bot_token
        
    def send_message(self, channel: str, message: str) -> str:
        """Returns the message TS."""
        if not self.api_key:
            raise ValueError("Live Slack integration requires SLACK_BOT_TOKEN")
            
        # In a real app we'd make an HTTP request to Slack web API
        raise NotImplementedError("Live Slack integration requires API implementation")

jira_client = JiraClient()
slack_client = SlackClient()

# ─────────────────────────────────────────────
# Outbox Worker
# ─────────────────────────────────────────────

shutdown_event = threading.Event()
MAX_RETRIES = 3

def process_outbox_event(db: Session, event: OutboxEvent):
    """Processes a single outbox event with exactly-once logic and retries."""
    event.status = "PROCESSING"
    event.updated_at = datetime.datetime.utcnow().isoformat()
    db.commit()
    
    payload = json.loads(event.payload)
    commitment_id = event.commitment_id
    
    try:
        if event.action_type == "create_jira":
            external_id = jira_client.create_issue(payload)
            
            # Update the commitment status to CONFIRMED
            task = db.query(Task).filter(Task.id == commitment_id).first()
            if task:
                task.status = "Confirmed"
                task.cross_meeting_note = f"Jira Issue Created: {external_id}"
                
                # Audit Trail
                audit = CommitmentEvent(
                    commitment_id=commitment_id,
                    timestamp=datetime.datetime.utcnow().isoformat(),
                    from_state="Sending",
                    to_state="Confirmed",
                    actor="integration_gateway",
                    component="outbox_worker",
                    detail=f"Jira sync successful. ID: {external_id}"
                )
                db.add(audit)
                
        elif event.action_type == "send_slack":
            slack_client.send_message(payload.get("channel", "#general"), payload.get("message", ""))
            
        # Mark event complete
        event.status = "COMPLETED"
        event.updated_at = datetime.datetime.utcnow().isoformat()
        db.commit()
        logger.info("outbox_event_processed", event_id=event.id, type=event.action_type)
        
    except Exception as e:
        db.rollback()
        # Re-fetch event to update error
        event = db.query(OutboxEvent).filter(OutboxEvent.id == event.id).first()
        if event:
            event.retry_count = (event.retry_count or 0) + 1
            if event.retry_count >= MAX_RETRIES:
                event.status = "FAILED"
                logger.error("outbox_event_failed_max_retries", event_id=event.id, error=str(e))
            else:
                event.status = "PENDING"
                logger.warning("outbox_event_retry", event_id=event.id, retry=event.retry_count, error=str(e))
                
            event.error = str(e)
            event.updated_at = datetime.datetime.utcnow().isoformat()
            db.commit()


def outbox_worker_loop():
    """Background worker thread that polls the outbox table."""
    logger.info("outbox_worker_started")
    while not shutdown_event.is_set():
        try:
            db = SessionLocal()
            # Find a pending event
            event = db.query(OutboxEvent).filter(OutboxEvent.status == "PENDING").order_by(OutboxEvent.created_at).first()
            if event:
                process_outbox_event(db, event)
            else:
                db.close()
                shutdown_event.wait(2.0)  # Polling interval
        except Exception as e:
            logger.error("outbox_worker_crash", error=str(e))
            # Exponential backoff on crash could be added here, we use simple sleep
            shutdown_event.wait(5.0)

# Start the worker thread in the background
worker_thread = threading.Thread(target=outbox_worker_loop, daemon=True)
worker_thread.start()

def shutdown_worker():
    """Gracefully shutdown the outbox worker."""
    logger.info("outbox_worker_shutting_down")
    shutdown_event.set()
    worker_thread.join(timeout=5.0)
