from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class SpeakerUtterance(BaseModel):
    speaker: str
    text: str

class MeetingInput(BaseModel):
    title: Optional[str] = "Project Update & Review Meeting"
    transcript: Optional[str] = None
    speakers: Optional[List[str]] = Field(default_factory=lambda: ["Rahul", "Priya", "Alex"])
    mode: Optional[str] = "upload" # upload, extension, demo

class SpeechOutput(BaseModel):
    transcript: str
    speakers: List[str]
    confidence: float

class SummaryOutput(BaseModel):
    summary: str
    decisions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    completed_work: List[str] = Field(default_factory=list)
    confidence: float = 0.95

class RawTask(BaseModel):
    task: str
    context: Optional[str] = None
    speaker: Optional[str] = "Meeting"
    condition: Optional[str] = None
    item_type: str = "Action Item" # Action Item, Decision, Risk, Completed Work, Follow-up
    confidence: float = 0.90

class RawTaskList(BaseModel):
    tasks: List[RawTask]

class EnrichedTask(BaseModel):
    id: Optional[str] = None
    task: str
    context: Optional[str] = None
    owner: Optional[str] = "Unassigned"
    assigned_by: Optional[str] = "Meeting"
    deadline: Optional[str] = "No Deadline"
    priority: Optional[str] = "Medium"
    condition: Optional[str] = None
    depends_on: Optional[str] = None
    progress_percent: int = 0
    subtasks: List[Dict[str, Any]] = Field(default_factory=list)
    origin_meeting: Optional[str] = "Meeting #18"
    origin_timestamp: Optional[str] = "14:32"
    origin_transcript_quote: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.90
    status: str = "Pending Approval"
    item_type: str = "Action Item" # Action Item, Decision, Risk, Completed Work, Follow-up
    cross_meeting_note: Optional[str] = None

class ValidatedTaskList(BaseModel):
    status: str # VALID, REVIEW
    overall_confidence: float
    tasks: List[EnrichedTask]

class ApproveTasksRequest(BaseModel):
    meeting_id: str
    tasks: List[EnrichedTask]

class CrossMeetingRecap(BaseModel):
    total_previous_tasks: int
    completed_count: int
    pending_count: int
    blocked_count: int
    execution_rate: float = 92.0
    topics_needing_followup: List[str] = Field(default_factory=list)
    repeated_blockers: List[Dict[str, Any]] = Field(default_factory=list)
    overdue_by_owner: List[Dict[str, Any]] = Field(default_factory=list)
    weekly_trends: List[Dict[str, Any]] = Field(default_factory=list)
    ai_insights: List[str] = Field(default_factory=list)
    status_recap_text: str
