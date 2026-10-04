from models import RawTaskList, SpeechOutput
from llm_provider import gemini
import structlog

logger = structlog.get_logger(__name__)

class ActionAgent:
    """Stage 2 Action Extractor Agent (LLM-Powered):
    Extracts high-recall technical action items and separates conditional triggers
    directly from the transcript using Gemini.
    """

    def process(self, speech_data: SpeechOutput) -> RawTaskList:
        transcript = speech_data.transcript
        
        if not transcript.strip() or transcript == "No transcript recorded.":
            return RawTaskList(tasks=[])

        prompt = f"""
        You are an expert AI Action Item Extractor.
        Analyze the following meeting transcript and extract all Action Items.
        
        Rules:
        1. Extract clear, actionable tasks or directives.
        2. Ignore status updates, completed work, or generic decisions.
        3. If the task has a conditional trigger ("if X, then do Y"), extract "If X" into the condition field.
        4. Include the exact context/quote where this task was mentioned.
        5. Provide a confidence score for each extracted task (0.0 to 1.0).
        6. Set the item_type strictly to "Action Item".
        7. Identify the speaker who mentioned the task if possible, otherwise use "Meeting".
        
        Transcript:
        {transcript}
        """
        
        try:
            output, _, _ = gemini.generate_structured(prompt, RawTaskList)
            return output
        except Exception as e:
            logger.error("action_agent_llm_error", error=str(e))
            return RawTaskList(tasks=[])
