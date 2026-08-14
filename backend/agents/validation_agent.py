import uuid
from typing import List
from models import EnrichedTask, ValidatedTaskList
from llm_provider import gemini
import structlog

logger = structlog.get_logger(__name__)

class ValidationAgent:
    """Validation Agent (LLM-Powered):
    Merges near-duplicate tasks, checks completeness, assigns IDs, computes confidence,
    and determines review status using Gemini.
    """

    def process(self, tasks: List[EnrichedTask]) -> ValidatedTaskList:
        if not tasks:
            return ValidatedTaskList(
                status="VALID",
                overall_confidence=0.85,
                tasks=[]
            )

        # Assign UUIDs to tasks that don't have one
        for t in tasks:
            if not t.id:
                t.id = f"t-{uuid.uuid4().hex[:6]}"

        tasks_json = [t.model_dump() for t in tasks]

        prompt = f"""
        You are a highly analytical Task Validation and Deduplication AI.
        Below is a list of enriched action items.
        
        Rules:
        1. Identify any duplicate or near-duplicate tasks. Merge them into a single canonical task (keeping the most specific details like deadlines or owners).
        2. Assign a 'status' to each task: "Pending Approval" for good tasks, or "Pending Approval (Review Needed)" for tasks missing critical info (e.g., Unassigned owner, missing deadline, low confidence).
        3. Evaluate the 'overall_confidence' of the final task list (0.0 to 1.0).
        4. If the overall_confidence is < 0.85 or any task needs review, set the list 'status' to "REVIEW". Otherwise set it to "VALID".
        5. Return the finalized 'tasks' array along with the list 'status' and 'overall_confidence'. DO NOT lose the task 'id' fields.
        
        Tasks to Validate:
        {tasks_json}
        """
        
        try:
            output, _, _ = gemini.generate_structured(prompt, ValidatedTaskList)
            return output
        except Exception as e:
            logger.error("validation_agent_llm_error", error=str(e))
            # Fallback
            for t in tasks:
                t.status = "Pending Approval (Review Needed)"
            return ValidatedTaskList(status="REVIEW", overall_confidence=0.5, tasks=tasks)
