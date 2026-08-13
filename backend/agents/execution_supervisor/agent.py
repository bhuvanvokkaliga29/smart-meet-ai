"""
Execution Supervisor Agent
==========================
Analyzes the state of all commitments in the database.
Identifies blockers, at-risk deadlines, and generates the Next-Meeting Briefing.
"""

import time
import datetime
from typing import List, Dict, Any
from schemas import NextMeetingBrief, SupervisorAssessment, RiskLevel, CommitmentState
import database
from llm_provider import gemini

class ExecutionSupervisorAgent:
    def __init__(self):
        self.system_prompt = """
        You are the SmartMeet Execution Supervisor.
        Your job is to analyze the state of all active commitments and identify risks.
        Look at deadlines, dependencies, and external Jira/Slack status.
        Generate a briefing for the upcoming meeting to ensure accountability.
        """

    def generate_briefing(self) -> NextMeetingBrief:
        """Analyzes DB state and uses Gemini to synthesize a human-readable brief."""
        tasks = database.get_all_tasks()
        
        # 1. Filter active tasks
        active_tasks = [t for t in tasks if t["status"] not in ["Completed", "Cancelled", "Pending Approval"]]
        completed_since_last = [t for t in tasks if t["status"] == "Completed" and self._was_completed_recently(t)]
        
        # 2. Local heuristic risk assessment
        at_risk = []
        blocked = []
        unresolved = []
        
        today = datetime.date.today()
        for t in active_tasks:
            days_until = self._days_until_deadline(t.get("deadline", ""), today)
            
            assessment = SupervisorAssessment(
                commitment_id=t["id"],
                current_state=CommitmentState(t.get("status", "IN_PROGRESS").upper().replace(" ", "_")),
                days_until_deadline=days_until,
                external_status=t.get("cross_meeting_note", "")
            )
            
            if t["status"] == "Blocked":
                assessment.risk_level = RiskLevel.CRITICAL
                assessment.risk_reasons.append("Marked as explicitly blocked")
                blocked.append(assessment)
                unresolved.append(t)
            elif days_until is not None and days_until < 0:
                assessment.risk_level = RiskLevel.HIGH
                assessment.risk_reasons.append("Deadline has passed")
                at_risk.append(assessment)
                unresolved.append(t)
            elif days_until is not None and days_until <= 2:
                assessment.risk_level = RiskLevel.MEDIUM
                assessment.risk_reasons.append("Deadline is approaching within 48 hours")
                at_risk.append(assessment)

        # 3. LLM Synthesis for Discussion Points
        prompt = f"""
        {self.system_prompt}
        
        CURRENT STATE:
        At Risk: {len(at_risk)} items
        Blocked: {len(blocked)} items
        Completed recently: {len(completed_since_last)} items
        
        Identify 3 key discussion points to open the next meeting with to unblock the team.
        Return ONLY a JSON array of 3 strings.
        """
        
        from pydantic import BaseModel
        class DiscussionList(BaseModel):
            points: List[str]
        
        try:
            res, _, _ = gemini.generate_structured(prompt, DiscussionList)
            discussion_points = res.points
        except Exception:
            discussion_points = ["Review blocked items", "Review at-risk items", "Plan next steps"]

        return NextMeetingBrief(
            at_risk_commitments=at_risk,
            blocked_commitments=blocked,
            completed_since_last=completed_since_last,
            unresolved_from_previous=unresolved,
            recommended_discussion_points=discussion_points
        )

    def _days_until_deadline(self, deadline_str: str, today: datetime.date) -> int | None:
        if not deadline_str or "No Deadline" in deadline_str:
            return None
        try:
            # Assumes YYYY-MM-DD
            target = datetime.datetime.strptime(deadline_str[:10], "%Y-%m-%d").date()
            return (target - today).days
        except Exception:
            return None

    def _was_completed_recently(self, task: Dict[str, Any]) -> bool:
        # Simplistic heuristic for demo
        return "Completed" in task.get("status", "")
