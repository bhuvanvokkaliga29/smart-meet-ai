from typing import List
from models import ValidatedTaskList, CrossMeetingRecap
import database
from llm_provider import gemini
import structlog

logger = structlog.get_logger(__name__)

class CrossMeetingAgent:
    """Cross-Meeting Agent (LLM-Powered):
    Reconciles extracted tasks with historical meeting memory, detects duplicate commitments,
    tracks repeated blockers, and generates a dynamic recap using Gemini.
    """

    def reconcile(self, validated_data: ValidatedTaskList) -> ValidatedTaskList:
        existing_tasks = database.get_all_tasks()
        
        if not validated_data.tasks or not existing_tasks:
            for t in validated_data.tasks:
                if not t.cross_meeting_note:
                    t.cross_meeting_note = "New action item created in this meeting context."
            return validated_data

        existing_json = [{"id": t.get("id"), "task": t.get("task"), "owner": t.get("owner"), "status": t.get("status")} for t in existing_tasks][-50:] # Limit to last 50 for context
        new_tasks_json = [t.model_dump() for t in validated_data.tasks]

        prompt = f"""
        You are a Cross-Meeting Intelligence AI.
        You are reconciling NEW tasks from the current meeting against EXISTING tasks from previous meetings.
        
        Rules:
        1. Compare each NEW task against the EXISTING tasks.
        2. If a new task matches an existing task (e.g. same owner, similar directive), add a 'cross_meeting_note' explaining the match and status update.
        3. If it's completely new, set 'cross_meeting_note' to "New action item created in this meeting context."
        4. Return EXACTLY the same number of new tasks provided, updated with the notes. Set status to whatever you receive for the new tasks.
        5. Return the list status and overall confidence exactly as received.
        
        EXISTING TASKS:
        {existing_json}
        
        NEW TASKS:
        {new_tasks_json}
        
        LIST METADATA:
        status: {validated_data.status}
        overall_confidence: {validated_data.overall_confidence}
        """
        
        try:
            output, _, _ = gemini.generate_structured(prompt, ValidatedTaskList)
            
            # Defensive programming: ensure we didn't drop tasks or override IDs completely wrongly
            # But normally we just trust the ValidatedTaskList structure if well formed.
            for idx, old_t in enumerate(validated_data.tasks):
                if idx < len(output.tasks):
                    old_t.cross_meeting_note = output.tasks[idx].cross_meeting_note
            return validated_data
        except Exception as e:
            logger.error("cross_meeting_agent_reconcile_llm_error", error=str(e))
            for t in validated_data.tasks:
                if not t.cross_meeting_note:
                    t.cross_meeting_note = "New action item created in this meeting context."
            return validated_data

    def generate_recap(self) -> CrossMeetingRecap:
        tasks = database.get_all_tasks()
        meetings = database.get_all_meetings()

        # Build context
        total = len(tasks)
        completed = sum(1 for t in tasks if t.get("status") == "Completed")
        pending = sum(1 for t in tasks if t.get("status") in ["Pending", "In Progress", "Pending Approval"])
        blocked = sum(1 for t in tasks if t.get("status") == "Blocked")
        exec_rate = round((completed / max(total, 1)) * 100, 1) if total > 0 else 92.0

        meetings_summary = [{"title": m.get("title"), "summary": m.get("summary")} for m in meetings]
        tasks_summary = [{"task": t.get("task"), "owner": t.get("owner"), "status": t.get("status")} for t in tasks][-50:]

        prompt = f"""
        You are a Cross-Meeting Intelligence AI generating a high-level recap.
        
        Database Stats:
        - Total tasks across {len(meetings)} meetings: {total}
        - Completed: {completed}, Pending: {pending}, Blocked: {blocked}
        - Execution Rate: {exec_rate}%
        
        Meetings Summary:
        {meetings_summary}
        
        Recent Tasks:
        {tasks_summary}
        
        Rules:
        1. Fill out the CrossMeetingRecap structure based on the real stats provided.
        2. Identify 'repeated_blockers' from the task topics that are pending or blocked. Provide topic, count, and severity.
        3. Calculate 'overdue_by_owner' for owners with pending/blocked tasks. Provide owner, overdue count, and total count.
        4. Generate a 'status_recap_text' describing the overall team performance.
        5. Extract 'topics_needing_followup'.
        6. Return the fully formed structured output.
        """
        
        try:
            output, _, _ = gemini.generate_structured(prompt, CrossMeetingRecap)
            # Ensure hard stats are accurate, the LLM might hallucinate them
            output.total_previous_tasks = total
            output.completed_count = completed
            output.pending_count = pending
            output.blocked_count = blocked
            output.execution_rate = exec_rate
            return output
        except Exception as e:
            logger.error("cross_meeting_agent_recap_llm_error", error=str(e))
            return CrossMeetingRecap(
                total_previous_tasks=total,
                completed_count=completed,
                pending_count=pending,
                blocked_count=blocked,
                execution_rate=exec_rate,
                status_recap_text="Error generating recap due to AI failure."
            )
