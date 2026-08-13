import uuid
import time
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum

class MeetingSource(str, Enum):
    LIVE_AUDIO = "live_audio"
    MEET_CAPTION = "meet_caption"
    UPLOADED_AUDIO = "upload_audio"
    UPLOADED_TRANSCRIPT = "upload_transcript"
    PASTED_TRANSCRIPT = "pasted_transcript"

class EventType(str, Enum):
    TRANSCRIPT_SEGMENT = "TRANSCRIPT_SEGMENT"
    SPEAKER_IDENTIFIED = "SPEAKER_IDENTIFIED"
    VISUAL_CONTEXT = "VISUAL_CONTEXT"
    MEETING_STARTED = "MEETING_STARTED"
    MEETING_ENDED = "MEETING_ENDED"

class NormalizedMeetingEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"evt-{uuid.uuid4().hex[:8]}")
    meeting_id: str
    event_type: EventType
    timestamp_start: float = Field(default_factory=time.time)
    source: MeetingSource

class TranscriptSegmentEvent(NormalizedMeetingEvent):
    event_type: EventType = EventType.TRANSCRIPT_SEGMENT
    timestamp_end: Optional[float] = None
    speaker_id: Optional[str] = None
    speaker_label: Optional[str] = None
    speaker_confidence: float = 0.0
    language: str = "en"
    original_text: str
    normalized_text: str
    confidence: float = 1.0

class VisualContextEvent(NormalizedMeetingEvent):
    event_type: EventType = EventType.VISUAL_CONTEXT
    image_url: Optional[str] = None
    description: str
