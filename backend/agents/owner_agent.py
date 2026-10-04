from typing import List
from models import RawTaskList, EnrichedTask, EnrichedTaskList, SpeechOutput
from llm_provider import gemini
import structlog

logger = structlog.get_logger(__name__)

class OwnerAgent:
    """Owner & Delegator Resolution Agent (LLM-Powered):
    Distinguishes the speaker (assigned_by) from the person being addressed (owner).
    Handles direct assignments, group tasks, and self-commitments using Gemini.
    """

    def process(self, task_list: RawTaskList, speech_data: SpeechOutput) -> List[EnrichedTask]:
        if not task_list.tasks:
            return []

        tasks_json = [t.model_dump() for t in task_list.tasks]

        prompt = f"""
        You are an intelligent Task Ownership Assignment AI.
        Below is a list of action items extracted from a meeting.
        Your goal is to accurately assign the 'owner' (the person who must do the task) and the 'assigned_by' (the person who delegated the task or the meeting itself).
        
        Rules:
        1. Contextual Directives: If Speaker A says "Speaker B, please do X", then owner=Speaker B, assigned_by=Speaker A.
        2. Self-commitments: If Speaker A says "I will do X", then owner=Speaker A.
        3. Group Tasks: If Speaker A says "We need to do X" or "Everyone", then owner="Team".
        4. Mentions: "Let's check with Emily" -> owner=Emily.
        5. Default: If no owner is clear, set owner="Unassigned".
        6. You must return EXACTLY the same number of tasks as provided, fully enriched with 'owner' and 'assigned_by'. Preserve all existing task data.
        
        Known Speakers: {', '.join(speech_data.speakers)}
        
        Tasks to Enrich:
        {tasks_json}
        """
        
        try:
            output, _, _ = gemini.generate_structured(prompt, EnrichedTaskList)
            return output.tasks
        except Exception as e:
            logger.error("owner_agent_llm_error", error=str(e))
            # Fallback
            enriched = []
            for t in task_list.tasks:
                enriched.append(EnrichedTask(
                    task=t.task,
                    context=t.context,
                    owner="Unassigned",
                    assigned_by=t.speaker or "Meeting",
                    condition=t.condition,
                    item_type=t.item_type,
                    confidence=t.confidence
                ))
            return enriched
