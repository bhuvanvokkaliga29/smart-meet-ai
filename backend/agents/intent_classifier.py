from typing import Tuple
from models import IntentOutput
from llm_provider import gemini
import structlog

logger = structlog.get_logger(__name__)

class IntentClassifier:
    """Stage 1: Sentence Intent Classifier Engine (LLM-Powered).
    Classifies each sentence/clause into exactly ONE intent using Gemini.
    """

    @staticmethod
    def classify(clause: str) -> Tuple[str, float]:
        c_lower = clause.lower().strip()
        if not c_lower or len(c_lower) < 5:
            return "Information", 0.50

        prompt = f"""
        You are an Intent Classifier AI for meeting transcripts.
        Classify the following clause into EXACTLY ONE of the following intents:
        'Action', 'Decision', 'Risk', 'Completed', 'Discussion', 'Question', or 'Information'.
        
        Clause: "{clause}"
        
        Respond with the classification and your confidence (0.0 to 1.0).
        """
        
        try:
            output, _, _ = gemini.generate_structured(prompt, IntentOutput)
            return output.intent, output.confidence
        except Exception as e:
            logger.error("intent_classifier_llm_error", error=str(e))
            return "Information", 0.50
