import pytest
import datetime
from agents.execution_supervisor.agent import ExecutionSupervisorAgent
from schemas import NextMeetingBrief

def test_supervisor_initialization():
    agent = ExecutionSupervisorAgent()
    assert agent.system_prompt is not None

def test_supervisor_generate_briefing():
    agent = ExecutionSupervisorAgent()
    
    from unittest.mock import patch, MagicMock
    with patch("agents.execution_supervisor.agent.database.get_all_tasks") as mock_get_tasks, \
         patch("agents.execution_supervisor.agent.gemini.generate_structured") as mock_generate:
         
        mock_get_tasks.return_value = [
            {
                "id": "t-1",
                "status": "In Progress",
                "deadline": (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            },
            {
                "id": "t-2",
                "status": "Blocked",
                "deadline": (datetime.date.today() + datetime.timedelta(days=5)).strftime("%Y-%m-%d"),
            },
            {
                "id": "t-3",
                "status": "Completed",
                "deadline": (datetime.date.today() - datetime.timedelta(days=2)).strftime("%Y-%m-%d"),
            }
        ]
        
        mock_list = MagicMock()
        mock_list.points = ["Test discussion point 1"]
        mock_generate.return_value = (mock_list, "gemini", 100.0)
        
        brief = agent.generate_briefing()
        
        assert isinstance(brief, NextMeetingBrief)
        assert len(brief.at_risk_commitments) == 1
        assert len(brief.blocked_commitments) == 1
        assert len(brief.completed_since_last) == 1
        assert len(brief.recommended_discussion_points) == 1

def test_days_until_deadline():
    agent = ExecutionSupervisorAgent()
    today = datetime.date(2026, 8, 7)
    
    assert agent._days_until_deadline("2026-08-08", today) == 1
    assert agent._days_until_deadline("2026-08-06", today) == -1
    assert agent._days_until_deadline("No Deadline", today) is None
    assert agent._days_until_deadline(None, today) is None
