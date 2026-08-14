import datetime
from typing import List
from models import EnrichedTask, EnrichedTaskList, SpeechOutput
from llm_provider import gemini
import structlog

logger = structlog.get_logger(__name__)

class DeadlineAgent:
    """Deadline Agent (LLM-Powered):
    Resolves explicit dates and relative days intelligently using Gemini.
    """

    def process(self, tasks: List[EnrichedTask], speech_data: SpeechOutput) -> List[EnrichedTask]:
        if not tasks:
            return []

        today_str = datetime.date.today().strftime("%Y-%m-%d")
        tasks_json = [t.model_dump() for t in tasks]

        prompt = f"""
        You are a smart Deadline Inference AI.
        Below is a list of action items extracted from a meeting.
        Today's date is {today_str}.
        
        Rules:
        1. Look at the 'task' and 'context' fields to identify any mention of dates or deadlines.
        2. Resolve relative dates (e.g. "by tomorrow", "next Friday", "end of week") into exact YYYY-MM-DD format based on today's date ({today_str}).
        3. If no deadline is mentioned or implied, set it to "No Deadline" or a standard business date (e.g., 5 days from now).
        4. You must return EXACTLY the same number of tasks as provided, fully enriched with the calculated 'deadline'. Preserve all other task data.
        
        Tasks to Enrich:
        {tasks_json}
        """
        
        try:
            output, _, _ = gemini.generate_structured(prompt, EnrichedTaskList)
            return output.tasks
        except Exception as e:
            logger.error("deadline_agent_llm_error", error=str(e))
            return tasks
