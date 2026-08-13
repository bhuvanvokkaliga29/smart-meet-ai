import pytest
from unittest.mock import patch
from agents.meeting_intelligence.agent import MeetingIntelligenceAgent
from schemas import MeetingIntelligenceOutput, CommitmentCandidate

def test_meeting_intelligence_agent_initialization():
    agent = MeetingIntelligenceAgent()
    assert "SmartMeet AI Meeting Intelligence Agent" in agent.system_prompt

@patch("agents.meeting_intelligence.agent.gemini.generate_structured")
def test_meeting_intelligence_agent_process(mock_generate):
    agent = MeetingIntelligenceAgent()
    transcript = "Sarah: I will prepare the migration plan by Friday.\nAlex: I will deploy the production server immediately."
    
    mock_commitments = [
        CommitmentCandidate(
            action="Deploy", owner_candidate="Alex", deadline_phrase="immediately",
            commitment_type="delegated_commitment", evidence_transcript="Deploy production", confidence=0.9
        )
    ]
    mock_output = MeetingIntelligenceOutput(meeting_id="m-test-123", summary="Test summary", commitments=mock_commitments)
    mock_generate.return_value = (mock_output, "gemini-2.5-flash", 120.0)
    
    result = agent.process(transcript, meeting_id="m-test-123")
    
    assert isinstance(result, MeetingIntelligenceOutput)
    assert result.meeting_id == "m-test-123"
    assert "gemini" in result.model_provider
    
    # Check trace metrics are set
    assert result.total_latency_ms >= 0
    assert result.total_segments_processed > 0
    
    # Check that individual candidate objects also received trace values
    if result.commitments:
        assert result.commitments[0].model_provider == result.model_provider
        assert result.commitments[0].processing_latency_ms >= 0
