"""
SmartMeet AI v2 — Backend Test Suite
=====================================
Comprehensive PyTest tests covering API endpoints, agent pipeline,
database operations, and data model validation.
"""

import pytest
import json
import os
import sqlite3
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Create a FastAPI TestClient for endpoint testing."""
    from main import app
    return TestClient(app)

@pytest.fixture(autouse=True)
def mock_gemini():
    from models import SpeechOutput, SummaryOutput, RawTaskList, RawTask, IntentOutput, EnrichedTaskList, EnrichedTask, ValidatedTaskList, CrossMeetingRecap
    with patch("llm_provider.gemini.generate_structured") as mock_gen:
        def side_effect(prompt, schema):
            if schema == SpeechOutput:
                return SpeechOutput(transcript="Mocked transcript", speakers=["Rahul", "Alex"], confidence=0.9), "mock", 100
            elif schema == SummaryOutput:
                return SummaryOutput(summary="Mocked summary", decisions=["dec1"], risks=[], completed_work=[], confidence=0.9), "mock", 100
            elif schema == RawTaskList:
                return RawTaskList(tasks=[RawTask(task="Mock task", speaker="Alex", confidence=0.9)]), "mock", 100
            elif schema == IntentOutput:
                if "Good morning" in prompt or "hello" in prompt.lower():
                    return IntentOutput(intent="Discussion", confidence=0.9), "mock", 100
                return IntentOutput(intent="Action", confidence=0.9), "mock", 100
            elif schema == EnrichedTaskList:
                if "Priority Assessment" in prompt:
                    return EnrichedTaskList(tasks=[EnrichedTask(id="t-mock", task="Deploy production server immediately", owner="Alex", priority="High", confidence=0.9)]), "mock", 100
                elif "Deadline Inference" in prompt:
                    return EnrichedTaskList(tasks=[EnrichedTask(id="t-mock", task="Finish report by Friday", owner="Alex", deadline="2026-08-14", confidence=0.9)]), "mock", 100
                else:
                    return EnrichedTaskList(tasks=[EnrichedTask(id="t-mock", task="Mock task", owner="Rahul", assigned_by="Alex", confidence=0.9)]), "mock", 100
            elif schema == ValidatedTaskList:
                return ValidatedTaskList(status="VALID", overall_confidence=0.9, tasks=[EnrichedTask(id="t-mock", task="Mock task", owner="Rahul", assigned_by="Alex", priority="High", deadline="2026-08-14", confidence=0.9)]), "mock", 100
            elif schema == CrossMeetingRecap:
                return CrossMeetingRecap(total_previous_tasks=1, completed_count=0, pending_count=1, blocked_count=0, execution_rate=0.0, status_recap_text="Mock"), "mock", 100
            return schema(), "mock", 100
        mock_gen.side_effect = side_effect
        yield mock_gen



@pytest.fixture
def sample_transcript():
    """Provide a reusable sample meeting transcript."""
    return (
        "Rahul: Can you finish the Login UI prototype by Friday? "
        "Priya: Sure, I will prepare the test plan by next Wednesday. "
        "Alex: Great! We also decided to postpone the production deployment "
        "until security audit completes."
    )


@pytest.fixture
def sample_meeting_input():
    """Provide a reusable MeetingInput dict."""
    return {
        "title": "Test Sprint Planning",
        "transcript": (
            "Rahul: Can you finish the Login UI prototype by Friday? "
            "Priya: Sure, I will prepare the test plan by next Wednesday. "
            "Alex: Great! We decided to postpone deployment until security audit."
        ),
        "speakers": ["Rahul", "Priya", "Alex"],
        "mode": "demo",
    }


# ---------------------------------------------------------------------------
# 1. Health & Root Endpoint Tests
# ---------------------------------------------------------------------------

class TestHealthEndpoints:
    """Verify that the API is alive and returning correct metadata."""

    def test_root_returns_200(self, client):
        resp = client.get("/")
        assert resp.status_code == 200

    def test_root_contains_app_name(self, client):
        data = client.get("/").json()
        assert data["app"] == "SmartMeet AI v2"
        assert data["version"] == "2.0.0"
        assert data["status"] == "online"


# ---------------------------------------------------------------------------
# 2. Meeting & Task CRUD Endpoint Tests
# ---------------------------------------------------------------------------

class TestMeetingEndpoints:
    """Test meeting listing and task listing endpoints."""

    def test_get_meetings_returns_list(self, client):
        resp = client.get("/api/meetings")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_tasks_returns_list(self, client):
        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_dashboard_stats(self, client):
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_meetings" in data
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "pending_tasks" in data
        assert "blocked_tasks" in data

    def test_get_cross_meeting_recap(self, client):
        resp = client.get("/api/cross-meeting/recap")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_previous_tasks" in data
        assert "status_recap_text" in data


# ---------------------------------------------------------------------------
# 3. Orchestration Pipeline Tests
# ---------------------------------------------------------------------------

class TestOrchestrationPipeline:
    """Test the multi-agent orchestration endpoint end-to-end."""

    def test_orchestrate_returns_pipeline_result(self, client, sample_meeting_input):
        resp = client.post("/api/orchestrate", json=sample_meeting_input)
        assert resp.status_code == 200
        data = resp.json()
        assert "meeting_id" in data
        assert "pipeline_result" in data
        result = data["pipeline_result"]
        assert "summary" in result
        assert "decisions" in result
        assert "tasks" in result
        assert isinstance(result["tasks"], list)

    def test_orchestrate_extracts_tasks(self, client, sample_meeting_input):
        resp = client.post("/api/orchestrate", json=sample_meeting_input)
        tasks = resp.json()["pipeline_result"]["tasks"]
        assert len(tasks) > 0
        for t in tasks:
            assert "task" in t
            assert "owner" in t
            assert "deadline" in t
            assert "priority" in t

    def test_orchestrate_assigns_meeting_id(self, client, sample_meeting_input):
        resp = client.post("/api/orchestrate", json=sample_meeting_input)
        mid = resp.json()["meeting_id"]
        assert mid.startswith("m-")


# ---------------------------------------------------------------------------
# 4. Live Captions Buffer Tests
# ---------------------------------------------------------------------------

class TestLiveCaptions:
    """Test the Chrome Extension live caption streaming buffer."""

    def test_post_caption(self, client):
        client.delete("/api/live-captions")
        resp = client.post(
            "/api/live-captions",
            json={"speaker": "Rahul", "text": "Hello team, let's begin."},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"
        assert resp.json()["total_lines"] >= 1

    def test_get_captions_drains_buffer(self, client):
        client.delete("/api/live-captions")
        client.post(
            "/api/live-captions",
            json={"speaker": "Alex", "text": "Testing drain"},
        )
        resp = client.get("/api/live-captions")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1
        # Buffer should be empty after drain
        resp2 = client.get("/api/live-captions")
        assert resp2.json()["count"] == 0

    def test_clear_captions(self, client):
        client.post(
            "/api/live-captions",
            json={"speaker": "Priya", "text": "Will be cleared"},
        )
        resp = client.delete("/api/live-captions")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cleared"

    def test_duplicate_caption_dedup(self, client):
        client.delete("/api/live-captions")
        payload = {"speaker": "Alex", "text": "Same line"}
        client.post("/api/live-captions", json=payload)
        client.post("/api/live-captions", json=payload)
        resp = client.get("/api/live-captions")
        assert resp.json()["count"] == 1


# ---------------------------------------------------------------------------
# 5. Pydantic Model Validation Tests
# ---------------------------------------------------------------------------

class TestModels:
    """Test Pydantic model schemas and defaults."""

    def test_meeting_input_defaults(self):
        from models import MeetingInput
        m = MeetingInput()
        assert m.title is not None
        assert m.mode == "upload"

    def test_enriched_task_defaults(self):
        from models import EnrichedTask
        t = EnrichedTask(task="Test task")
        assert t.owner == "Unassigned"
        assert t.priority == "Medium"
        assert t.status == "Pending Approval"
        assert t.confidence == 0.90

    def test_summary_output_schema(self):
        from models import SummaryOutput
        s = SummaryOutput(summary="Test summary", decisions=["d1"], risks=["r1"])
        assert s.summary == "Test summary"
        assert s.confidence == 0.95


# ---------------------------------------------------------------------------
# 6. Individual Agent Unit Tests
# ---------------------------------------------------------------------------

class TestAgents:
    """Unit tests for individual agent modules."""

    def test_speech_agent_processes_transcript(self):
        from agents.speech_agent import SpeechAgent
        from models import MeetingInput
        agent = SpeechAgent()
        inp = MeetingInput(transcript="Rahul: Hello Priya: Hi there")
        result = agent.process(inp)
        assert result.transcript is not None
        assert len(result.speakers) > 0

    def test_intent_classifier_detects_action(self):
        from agents.intent_classifier import IntentClassifier
        clf = IntentClassifier()
        intent, conf = clf.classify("Kevin please finish the report by Friday")
        assert intent == "Action"
        assert conf > 0.5

    def test_intent_classifier_filters_greetings(self):
        from agents.intent_classifier import IntentClassifier
        clf = IntentClassifier()
        intent, conf = clf.classify("Good morning everyone")
        assert intent in ("Discussion", "Greeting", "Information")

    def test_action_agent_extracts_tasks(self):
        from agents.action_agent import ActionAgent
        from models import SpeechOutput
        agent = ActionAgent()
        speech = SpeechOutput(
            transcript="Alex: Kevin, please improve the prompt templates by Friday.",
            speakers=["Alex", "Kevin"],
            confidence=0.95,
        )
        raw_list = agent.process(speech)
        assert len(raw_list.tasks) > 0

    def test_priority_agent_assigns_priority(self):
        from agents.priority_agent import PriorityAgent
        from models import EnrichedTask, SpeechOutput
        agent = PriorityAgent()
        tasks = [
            EnrichedTask(task="Deploy production server immediately", owner="Alex"),
            EnrichedTask(task="Update readme documentation", owner="Priya"),
        ]
        speech = SpeechOutput(
            transcript="Deploy production server immediately. Update readme documentation.",
            speakers=["Alex", "Priya"],
            confidence=0.95,
        )
        result = agent.process(tasks, speech)
        assert result[0].priority == "High"

    def test_deadline_agent_resolves_dates(self):
        from agents.deadline_agent import DeadlineAgent
        from models import EnrichedTask, SpeechOutput
        agent = DeadlineAgent()
        tasks = [EnrichedTask(task="Finish report by Friday", owner="Alex")]
        speech = SpeechOutput(
            transcript="Finish report by Friday",
            speakers=["Alex"],
            confidence=0.95,
        )
        result = agent.process(tasks, speech)
        # Should resolve "Friday" to an ISO date
        assert result[0].deadline != "No Deadline"


# ---------------------------------------------------------------------------
# 7. Database CRUD Tests
# ---------------------------------------------------------------------------

class TestDatabase:
    """Test database read/write operations."""

    def test_get_all_meetings_returns_list(self):
        import database
        meetings = database.get_all_meetings()
        assert isinstance(meetings, list)

    def test_get_all_tasks_returns_list(self):
        import database
        tasks = database.get_all_tasks()
        assert isinstance(tasks, list)

    def test_save_and_retrieve_meeting(self):
        import database
        test_meeting = {
            "id": "m-test-pytest",
            "title": "PyTest Meeting",
            "date": "2026-08-06",
            "transcript": "Test transcript",
            "summary": "Test summary",
            "decisions": ["Decision 1"],
        }
        database.save_meeting(test_meeting)
        meetings = database.get_all_meetings()
        found = [m for m in meetings if m["id"] == "m-test-pytest"]
        assert len(found) == 1
        assert found[0]["title"] == "PyTest Meeting"

    def test_update_task_status(self):
        import database
        tasks = database.get_all_tasks()
        if tasks:
            tid = tasks[0]["id"]
            original_status = tasks[0]["status"]
            database.update_task_status(tid, "Completed")
            updated = database.get_all_tasks()
            t = [t for t in updated if t["id"] == tid][0]
            assert t["status"] == "Completed"
            # Restore
            database.update_task_status(tid, original_status)

    def test_get_reminders(self):
        import database
        reminders = database.get_reminders()
        assert isinstance(reminders, list)
