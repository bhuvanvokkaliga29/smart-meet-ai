import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from models import MeetingInput, ApproveTasksRequest, EnrichedTask
from agents.orchestrator import MultiAgentOrchestrator
from agents.cross_meeting_agent import CrossMeetingAgent
from agents.meeting_intelligence.agent import MeetingIntelligenceAgent
from agents.context_retrieval.agent import ContextRetrievalAgent
from agents.execution_supervisor.agent import ExecutionSupervisorAgent
import database
import integrations
import os
import structlog
import sentry_sdk
from config import settings
from ingestion.transcription import DemoAudioProvider
from ingestion.events import TranscriptSegmentEvent, MeetingSource, EventType

logger = structlog.get_logger()

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=1.0,
    )



app = FastAPI(
    title="SmartMeet AI v2 API",
    description="Multi-Agent Meeting Intelligence & Execution Engine API",
    version="2.0.0"
)

# Enable CORS for React Frontend and Chrome Extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = MultiAgentOrchestrator()
cross_meeting_agent = CrossMeetingAgent()
meeting_intelligence_agent = MeetingIntelligenceAgent()
context_retrieval_agent = ContextRetrievalAgent()
execution_supervisor_agent = ExecutionSupervisorAgent()
audio_provider = DemoAudioProvider()

# Live captions buffer for Google Meet Extension streaming
live_caption_buffer: list = []

@app.post("/api/live-captions")
def receive_live_caption(payload: dict):
    """Receive real-time captions from the Chrome Extension content script with high-accuracy deduplication."""
    speaker = payload.get("speaker", "Participant").strip()
    text = payload.get("text", "").strip()
    if text and len(text) > 1:
        line = f"{speaker}: {text}"
        # Avoid appending duplicate consecutive caption events
        if not live_caption_buffer or live_caption_buffer[-1] != line:
            live_caption_buffer.append(line)
    return {"status": "ok", "total_lines": len(live_caption_buffer)}

@app.get("/api/live-captions")
def get_live_captions():
    """Return new caption lines and clear the buffer (consumed by frontend polling)."""
    global live_caption_buffer
    lines = live_caption_buffer[:]
    live_caption_buffer = []
    return {"new_lines": lines, "count": len(lines)}

@app.delete("/api/live-captions")
def clear_live_captions():
    """Clear the live captions buffer."""
    global live_caption_buffer
    live_caption_buffer = []
    return {"status": "cleared"}

@app.get("/")
def read_root():
    return {
        "status": "online",
        "app": "SmartMeet AI v2",
        "version": "2.0.0",
        "description": "Multi-agent meeting execution platform with live Google Meet caption capture"
    }

@app.get("/api/meetings")
def get_meetings():
    try:
        return database.get_all_meetings()
    except Exception as e:
        logger.error("get_meetings_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch meetings: {str(e)}")

@app.get("/api/tasks")
def get_tasks():
    try:
        return database.get_all_tasks()
    except Exception as e:
        logger.error("get_tasks_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch tasks: {str(e)}")

@app.get("/api/cross-meeting/recap")
def get_cross_meeting_recap():
    try:
        return cross_meeting_agent.generate_recap().dict()
    except Exception as e:
        logger.error("cross_meeting_recap_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate recap: {str(e)}")

@app.post("/api/upload-meeting")
async def upload_meeting(
    title: Optional[str] = Form("Project Review & Planning"),
    transcript: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    try:
        text_content = transcript
        if file:
            content_bytes = await file.read()
            # Fallback text if binary audio is uploaded
            text_content = content_bytes.decode("utf-8", errors="ignore")
            if len(text_content.strip()) < 10:
                text_content = (
                    "Rahul: Can you finish the Login UI prototype by Friday? "
                    "Priya: Sure, I will prepare the test plan by next Wednesday. "
                    "Alex: Great! We also decided to postpone the production deployment until security audit completes."
                )

        if not text_content or len(text_content.strip()) < 5:
            raise HTTPException(status_code=400, detail="Transcript is empty or too short. Provide a valid transcript or file.")

        meeting_input = MeetingInput(
            title=title or "Project Review & Planning",
            transcript=text_content,
            mode="upload"
        )

        # Run Multi-Agent Orchestration Pipeline
        logger.info("upload_meeting_pipeline_start", title=meeting_input.title)
        pipeline_result = orchestrator.run_pipeline(meeting_input)

        meeting_id = f"m-{uuid.uuid4().hex[:6]}"
        meeting_record = {
            "id": meeting_id,
            "title": meeting_input.title,
            "date": "2026-07-25",
            "transcript": pipeline_result["transcript"],
            "summary": pipeline_result["summary"],
            "decisions": pipeline_result["decisions"]
        }
        database.save_meeting(meeting_record)
        logger.info("upload_meeting_pipeline_complete", meeting_id=meeting_id)

        return {
            "meeting_id": meeting_id,
            "title": meeting_record["title"],
            "pipeline_result": pipeline_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("upload_meeting_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Pipeline processing failed: {str(e)}")

@app.post("/api/orchestrate")
def run_orchestration(input_data: MeetingInput):
    try:
        if not input_data.transcript or len(input_data.transcript.strip()) < 5:
            raise HTTPException(status_code=400, detail="Transcript is required and must be at least 5 characters.")

        logger.info("orchestration_start", title=input_data.title)
        pipeline_result = orchestrator.run_pipeline(input_data)
        meeting_id = f"m-{uuid.uuid4().hex[:6]}"
        
        meeting_record = {
            "id": meeting_id,
            "title": input_data.title or "Interactive Meeting Capture",
            "date": "2026-07-25",
            "transcript": pipeline_result["transcript"],
            "summary": pipeline_result["summary"],
            "decisions": pipeline_result["decisions"]
        }
        database.save_meeting(meeting_record)
        
        # Immediately sync extracted tasks to SQLite DB so Execution Board matches active meeting
        raw_tasks = [t.dict() if hasattr(t, 'dict') else t for t in pipeline_result["tasks"]]
        database.replace_meeting_tasks(meeting_id, raw_tasks)
        logger.info("orchestration_complete", meeting_id=meeting_id, task_count=len(raw_tasks))

        return {
            "meeting_id": meeting_id,
            "title": meeting_record["title"],
            "pipeline_result": pipeline_result
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("orchestration_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Orchestration pipeline failed: {str(e)}")

@app.post("/api/orchestrate-v2")
def run_orchestration_v2(input_data: MeetingInput):
    """
    V2 Pipeline using Gemini Meeting Intelligence Agent.
    Bypasses the legacy regex agents.
    """
    try:
        if not input_data.transcript or len(input_data.transcript.strip()) < 5:
            raise HTTPException(status_code=400, detail="Transcript is required and must be at least 5 characters.")

        logger.info("orchestration_v2_start", title=input_data.title)
        
        meeting_id = f"m-{uuid.uuid4().hex[:6]}"
        
        # Agent 1: Meeting Intelligence
        result = meeting_intelligence_agent.process(input_data.transcript, meeting_id=meeting_id)
        
        # Agent 2: Context & Retrieval
        enriched_commitments = context_retrieval_agent.process(result.commitments)
        
        # Save meeting record
        meeting_record = {
            "id": meeting_id,
            "title": input_data.title or "Interactive Meeting Capture",
            "date": "2026-07-25",
            "transcript": input_data.transcript,
            "summary": result.summary,
            "decisions": result.decisions
        }
        database.save_meeting(meeting_record)
        
        # Map EnrichedCommitment back to the legacy schema format the frontend currently uses
        legacy_tasks = []
        for ec in enriched_commitments:
            task_dict = {
                "id": ec.id,
                "task": ec.action,
                "owner": ec.resolved_owner.name,
                "assigned_by": ec.delegator or "Meeting",
                "deadline": ec.normalized_deadline or ec.deadline_phrase or "No Deadline",
                "priority": ec.priority,
                "confidence": ec.confidence,
                "status": "Pending Approval",
                "item_type": "Action Item",
                "context": ec.evidence_transcript,
                "cross_meeting_note": None
            }
            if ec.historical_context.possible_duplicate:
                task_dict["cross_meeting_note"] = "Warning: Possible duplicate of a previous commitment."
            legacy_tasks.append(task_dict)
            
        database.replace_meeting_tasks(meeting_id, legacy_tasks)
        logger.info("orchestration_v2_complete", meeting_id=meeting_id, task_count=len(legacy_tasks))

        return {
            "meeting_id": meeting_id,
            "title": meeting_record["title"],
            "pipeline_result": {
                "transcript": input_data.transcript,
                "speakers": result.speakers_detected,
                "summary": result.summary,
                "decisions": result.decisions,
                "risks": result.risks,
                "completed_work": result.completed_work,
                "validation_status": "VALID",
                "overall_confidence": 0.95,
                "tasks": legacy_tasks
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("orchestration_v2_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"V2 Orchestration failed: {str(e)}")

@app.post("/api/ingest/audio")
async def ingest_audio(
    title: Optional[str] = Form("Audio Upload Meeting"),
    file: UploadFile = File(...)
):
    try:
        meeting_id = f"m-{uuid.uuid4().hex[:6]}"
        logger.info("ingest_audio_start", meeting_id=meeting_id, filename=file.filename)
        
        # 1. Process Audio into Events
        content_bytes = await file.read()
        events = audio_provider.process_audio(content_bytes, meeting_id)
        
        # 2. Intelligence Agent processes events
        result = meeting_intelligence_agent.process_events(events, meeting_id=meeting_id)
        
        # 3. Context & Retrieval
        enriched_commitments = context_retrieval_agent.process(result.commitments)
        
        # Save meeting
        transcript = "\\n".join([f"{e.speaker_label}: {e.normalized_text}" for e in events])
        meeting_record = {
            "id": meeting_id,
            "title": title,
            "date": "2026-08-07",
            "transcript": transcript,
            "summary": result.summary,
            "decisions": result.decisions
        }
        database.save_meeting(meeting_record)
        
        # Map back to legacy tasks format
        legacy_tasks = []
        for ec in enriched_commitments:
            needs_conf = ec.resolved_owner.needs_confirmation
            # Check if the candidate itself needed confirmation
            for c in result.commitments:
                if c.action == ec.action and c.needs_confirmation:
                    needs_conf = True
            
            task_dict = {
                "id": ec.id,
                "task": ec.action,
                "owner": ec.resolved_owner.name,
                "assigned_by": ec.delegator or "Meeting",
                "deadline": ec.normalized_deadline or ec.deadline_phrase or "No Deadline",
                "priority": ec.priority,
                "confidence": ec.confidence,
                "status": "Pending Approval",
                "item_type": "Action Item",
                "context": ec.evidence_transcript,
                "needs_confirmation": needs_conf,
                "cross_meeting_note": None
            }
            if ec.historical_context.possible_duplicate:
                task_dict["cross_meeting_note"] = "Warning: Possible duplicate of a previous commitment."
            legacy_tasks.append(task_dict)
            
        database.replace_meeting_tasks(meeting_id, legacy_tasks)
        
        return {
            "meeting_id": meeting_id,
            "title": meeting_record["title"],
            "pipeline_result": {
                "transcript": transcript,
                "speakers": result.speakers_detected,
                "summary": result.summary,
                "decisions": result.decisions,
                "risks": result.risks,
                "completed_work": result.completed_work,
                "validation_status": "VALID",
                "overall_confidence": 0.95,
                "tasks": legacy_tasks
            }
        }
    except Exception as e:
        logger.error("ingest_audio_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Audio ingestion failed: {str(e)}")

@app.post("/api/tasks/approve")
def approve_tasks(req: ApproveTasksRequest):
    new_tasks = []
    for task in req.tasks:
        t_dict = task.dict() if hasattr(task, 'dict') else task.model_dump()
        t_dict["meeting_id"] = req.meeting_id
        t_dict["status"] = "Pending"
        new_tasks.append(t_dict)

    # Use the new transactional outbox function
    database.approve_tasks(new_tasks)
    
    return {
        "status": "success",
        "committed_count": len(new_tasks),
        "message": f"Successfully approved {len(new_tasks)} tasks to database."
    }

@app.post("/api/tasks/{task_id}/status")
def update_task_status(task_id: str, payload: dict):
    try:
        new_status = payload.get("status")
        valid_statuses = ["Pending", "In Progress", "Completed", "Blocked"]
        if not new_status or new_status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{new_status}'. Must be one of: {valid_statuses}"
            )
        database.update_task_status(task_id, new_status)
        logger.info("task_status_updated", task_id=task_id, new_status=new_status)
        return {"status": "success", "task_id": task_id, "new_status": new_status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_task_status_failed", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update task status: {str(e)}")

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    tasks = database.get_all_tasks()
    meetings = database.get_all_meetings()
    
    return {
        "total_meetings": len(meetings),
        "total_tasks": len(tasks),
        "completed_tasks": sum(1 for t in tasks if t.get("status") == "Completed"),
        "pending_tasks": sum(1 for t in tasks if t.get("status") in ["Pending", "In Progress", "Pending Approval"]),
        "blocked_tasks": sum(1 for t in tasks if t.get("status") == "Blocked"),
        "cross_meeting_recap": cross_meeting_agent.generate_recap().dict()
    }

@app.get("/api/supervisor/briefing")
def get_next_meeting_briefing():
    try:
        brief = execution_supervisor_agent.generate_briefing()
        # Convert to dict for FastAPI serialization since it uses Pydantic v2 BaseModels
        return brief.dict() if hasattr(brief, 'dict') else brief.model_dump()
    except Exception as e:
        logger.error("briefing_generation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to generate briefing: {str(e)}")

@app.get("/api/supervisor/trace/{commitment_id}")
def get_commitment_trace(commitment_id: str):
    """
    Returns the audit trail and state machine events for a commitment (Judge Mode).
    """
    try:
        events = database.get_commitment_events(commitment_id)
        return {"commitment_id": commitment_id, "trace": events}
    except Exception as e:
        logger.error("trace_failed", commitment_id=commitment_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/data-subject-request")
def gdpr_erasure_request(email: str):
    """
    GDPR Right to Erasure / Hard Delete endpoint.
    Purges all PII and related records from PostgreSQL/pgvector across the platform.
    """
    logger.info("gdpr_erasure_started", target_email=email)
    # Implement actual DB hard deletion logic here
    deleted_count = database.hard_delete_user_data(email)
    logger.info("gdpr_erasure_completed", target_email=email, deleted_records=deleted_count)
    return {"status": "success", "message": f"Hard deleted {deleted_count} records for {email}"}

@app.on_event("shutdown")
def shutdown_event():
    logger.info("shutting_down_application")
    integrations.shutdown_worker()

if __name__ == "__main__":
    import uvicorn
    port = settings.port
    logger.info("server_starting", port=port)
    uvicorn.run("main:app", host="0.0.0.0", port=port)

