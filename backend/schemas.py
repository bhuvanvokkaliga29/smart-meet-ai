"""
SmartMeet AI v3 — Commitment Schemas & A2A Contracts
=====================================================
Typed data contracts for inter-agent communication (A2A protocol).
These schemas flow through the 3-agent pipeline:

Meeting Intelligence Agent → CommitmentCandidate
Context & Retrieval Agent  → EnrichedCommitment
Execution Supervisor       → SupervisorAssessment
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


# ─────────────────────────────────────────────
# Commitment State Machine
# ─────────────────────────────────────────────

class CommitmentState(str, Enum):
    DETECTED = "DETECTED"
    PROPOSED = "PROPOSED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    SENDING = "SENDING"
    CONFIRMED = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    AT_RISK = "AT_RISK"
    COMPLETED = "COMPLETED"
    VERIFIED = "VERIFIED"
    CANCELLED = "CANCELLED"
    CANCELLED_BEFORE_APPROVAL = "CANCELLED_BEFORE_APPROVAL"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    FAILED = "FAILED"


# Valid state transitions (deterministic — agents cannot bypass)
VALID_TRANSITIONS: Dict[CommitmentState, List[CommitmentState]] = {
    CommitmentState.DETECTED: [CommitmentState.PROPOSED, CommitmentState.CANCELLED_BEFORE_APPROVAL],
    CommitmentState.PROPOSED: [CommitmentState.AWAITING_APPROVAL, CommitmentState.CANCELLED_BEFORE_APPROVAL],
    CommitmentState.AWAITING_APPROVAL: [CommitmentState.APPROVED, CommitmentState.CANCELLED_BEFORE_APPROVAL],
    CommitmentState.APPROVED: [CommitmentState.SENDING, CommitmentState.CANCELLED],
    CommitmentState.SENDING: [CommitmentState.CONFIRMED, CommitmentState.FAILED, CommitmentState.RECONCILIATION_REQUIRED],
    CommitmentState.CONFIRMED: [CommitmentState.IN_PROGRESS, CommitmentState.BLOCKED, CommitmentState.COMPLETED],
    CommitmentState.IN_PROGRESS: [CommitmentState.BLOCKED, CommitmentState.AT_RISK, CommitmentState.COMPLETED],
    CommitmentState.BLOCKED: [CommitmentState.IN_PROGRESS, CommitmentState.AT_RISK, CommitmentState.CANCELLED],
    CommitmentState.AT_RISK: [CommitmentState.IN_PROGRESS, CommitmentState.BLOCKED, CommitmentState.COMPLETED, CommitmentState.CANCELLED],
    CommitmentState.COMPLETED: [CommitmentState.VERIFIED],
    CommitmentState.VERIFIED: [],
    CommitmentState.CANCELLED: [],
    CommitmentState.CANCELLED_BEFORE_APPROVAL: [],
    CommitmentState.RECONCILIATION_REQUIRED: [CommitmentState.CONFIRMED, CommitmentState.FAILED],
    CommitmentState.FAILED: [CommitmentState.SENDING, CommitmentState.CANCELLED],
}


def validate_transition(current: CommitmentState, target: CommitmentState) -> bool:
    """Deterministic state machine validation. Returns True if transition is valid."""
    return target in VALID_TRANSITIONS.get(current, [])


# ─────────────────────────────────────────────
# A2A Contract: Meeting Intelligence → Context
# ─────────────────────────────────────────────

class CommitmentType(str, Enum):
    SELF_COMMITMENT = "self_commitment"           # "I will finish..."
    DELEGATED_COMMITMENT = "delegated_commitment"  # "Sarah, please finish..."
    GROUP_COMMITMENT = "group_commitment"           # "Let's all review..."
    CONDITIONAL_COMMITMENT = "conditional"          # "If QA passes, deploy..."
    CORRECTION = "correction"                       # "Actually, make that Friday"
    CANCELLATION = "cancellation"                   # "Forget that, we don't need..."


class CommitmentCandidate(BaseModel):
    """Output of Meeting Intelligence Agent. A2A handoff to Context Agent."""
    action: str = Field(description="The commitment action extracted from speech")
    owner_candidate: Optional[str] = Field(None, description="Candidate owner name from transcript")
    delegator: Optional[str] = Field(None, description="Person who delegated the commitment")
    deadline_phrase: Optional[str] = Field(None, description="Raw deadline phrase from transcript")
    condition: Optional[str] = Field(None, description="Conditional clause if any")
    commitment_type: CommitmentType = Field(default=CommitmentType.SELF_COMMITMENT)
    evidence_transcript: str = Field(description="Exact transcript segment as evidence")
    evidence_segment_index: Optional[int] = Field(None, description="Index of transcript segment")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    identity_confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in the owner identity assignment")
    needs_confirmation: bool = Field(default=False, description="True if owner identity must be manually confirmed")
    correction_target: Optional[str] = Field(None, description="If correction, what is being corrected")
    cancellation_target: Optional[str] = Field(None, description="If cancellation, what is being cancelled")
    # Trace metadata
    model_provider: str = Field(default="unknown", description="gemini, gemma, regex-fallback")
    model_name: str = Field(default="unknown")
    processing_latency_ms: Optional[float] = None


class MeetingIntelligenceOutput(BaseModel):
    """Full output of the Meeting Intelligence Agent."""
    meeting_id: str
    commitments: List[CommitmentCandidate] = Field(default_factory=list)
    summary: str = ""
    decisions: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    completed_work: List[str] = Field(default_factory=list)
    speakers_detected: List[str] = Field(default_factory=list)
    total_segments_processed: int = 0
    model_provider: str = "unknown"
    model_name: str = "unknown"
    total_latency_ms: float = 0.0


# ─────────────────────────────────────────────
# A2A Contract: Context Agent → Supervisor
# ─────────────────────────────────────────────

class ResolvedOwner(BaseModel):
    """Owner resolution result from Context Agent."""
    name: str
    email: Optional[str] = None
    role: Optional[str] = None
    confidence: float = 0.0
    needs_confirmation: bool = False
    disambiguation_reason: Optional[str] = None
    alternative_candidates: List[str] = Field(default_factory=list)


class DependencyCandidate(BaseModel):
    """A detected dependency between commitments."""
    blocking_commitment: str
    blocked_commitment: str
    dependency_type: str = "blocks"  # blocks, requires, related_to
    confidence: float = 0.0
    evidence: Optional[str] = None


class HistoricalContext(BaseModel):
    """Historical information retrieved by Context Agent."""
    related_commitments: List[Dict[str, Any]] = Field(default_factory=list)
    possible_duplicate: bool = False
    duplicate_of: Optional[str] = None
    unresolved_blockers: List[str] = Field(default_factory=list)
    relevant_decisions: List[str] = Field(default_factory=list)
    previous_meeting_context: Optional[str] = None


class EnrichedCommitment(BaseModel):
    """Output of Context & Retrieval Agent. A2A handoff to Execution Supervisor."""
    id: str
    action: str
    resolved_owner: ResolvedOwner
    delegator: Optional[str] = None
    deadline_phrase: Optional[str] = None
    normalized_deadline: Optional[str] = None
    deadline_timezone: Optional[str] = None
    normalization_reason: Optional[str] = None
    condition: Optional[str] = None
    commitment_type: CommitmentType = CommitmentType.SELF_COMMITMENT
    priority: str = "Medium"
    evidence_transcript: str = ""
    state: CommitmentState = CommitmentState.PROPOSED
    confidence: float = 0.0
    dependencies: List[DependencyCandidate] = Field(default_factory=list)
    historical_context: HistoricalContext = Field(default_factory=HistoricalContext)
    # Trace
    model_provider: str = "unknown"
    model_name: str = "unknown"
    processing_latency_ms: Optional[float] = None


# ─────────────────────────────────────────────
# A2A Contract: Execution Supervisor Output
# ─────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SupervisorAssessment(BaseModel):
    """Output of Execution Supervisor Agent."""
    commitment_id: str
    current_state: CommitmentState
    risk_level: RiskLevel = RiskLevel.LOW
    risk_reasons: List[str] = Field(default_factory=list)
    recommended_action: Optional[str] = None
    follow_up_message: Optional[str] = None
    escalation_needed: bool = False
    dependency_impact: List[str] = Field(default_factory=list)
    days_until_deadline: Optional[int] = None
    external_status: Optional[str] = None  # Jira/Slack status
    external_url: Optional[str] = None


class NextMeetingBrief(BaseModel):
    """Pre-meeting accountability briefing."""
    meeting_id: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    at_risk_commitments: List[SupervisorAssessment] = Field(default_factory=list)
    blocked_commitments: List[SupervisorAssessment] = Field(default_factory=list)
    completed_since_last: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_from_previous: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_discussion_points: List[str] = Field(default_factory=list)
    repeated_blockers: List[Dict[str, Any]] = Field(default_factory=list)


# ─────────────────────────────────────────────
# Commitment Event (Audit Trail)
# ─────────────────────────────────────────────

class CommitmentEvent(BaseModel):
    """Immutable event in commitment lifecycle."""
    commitment_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    from_state: Optional[CommitmentState] = None
    to_state: CommitmentState
    actor: str = "system"  # system, human, agent, jira-webhook, slack-webhook
    component: str = "unknown"  # meeting_intelligence, context_agent, supervisor, hitl, outbox
    detail: Optional[str] = None
    latency_ms: Optional[float] = None


# ─────────────────────────────────────────────
# System Trace (Judge Mode)
# ─────────────────────────────────────────────

class TraceStep(BaseModel):
    """Single step in the system trace visible in Judge Mode."""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    component: str  # caption_received, gemini_classification, adk_meeting_intelligence, a2a_handoff, context_agent, mcp_memory_lookup, commitment_proposed, human_approved, outbox_created, jira_confirmed, webhook_received, supervisor_analyzed, briefing_generated
    status: str = "success"  # success, failure, pending, skipped
    detail: Optional[str] = None
    latency_ms: Optional[float] = None
    model_used: Optional[str] = None


class CommitmentTrace(BaseModel):
    """Full execution trace for a commitment (Judge Mode)."""
    commitment_id: str
    steps: List[TraceStep] = Field(default_factory=list)
