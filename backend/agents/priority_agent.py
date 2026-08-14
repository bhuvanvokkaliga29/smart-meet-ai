from typing import List
from models import EnrichedTask, EnrichedTaskList, SpeechOutput
from llm_provider import gemini
import structlog

logger = structlog.get_logger(__name__)

class PriorityAgent:
    """Priority Agent (LLM-Powered):
    Evaluates task urgency and assigns Priority levels (High, Medium, Low) using Gemini.
    """

    def process(self, tasks: List[EnrichedTask], speech_data: SpeechOutput) -> List[EnrichedTask]:
        if not tasks:
            return []

        tasks_json = [t.model_dump() for t in tasks]

        prompt = f"""
        You are a smart Priority Assessment AI.
        Below is a list of action items extracted from a meeting.
        
        Rules:
        1. Assess the urgency and importance of each task based on its text and context.
        2. Assign a 'priority' level of strictly: "High", "Medium", or "Low".
        3. Consider explicit statements ("highest priority", "blocker", "ASAP") as High.
        4. You must return EXACTLY the same number of tasks as provided, enriched with the 'priority'. Preserve all other task data.
        
        Tasks to Enrich:
        {tasks_json}
        """
        
        try:
            output, _, _ = gemini.generate_structured(prompt, EnrichedTaskList)
            return output.tasks
        except Exception as e:
            logger.error("priority_agent_llm_error", error=str(e))
            return tasks
