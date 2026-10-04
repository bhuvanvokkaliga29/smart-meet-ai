from typing import List
from models import SummaryOutput, SpeechOutput
from llm_provider import gemini
import structlog

logger = structlog.get_logger(__name__)

class SummaryAgent:
    """Stage 2 Categorized Analyst & Abstractive Summarizer Agent (LLM-Powered):
    Synthesizes high-level executive prose summary, decisions, risks, and completed work
    directly from the transcript using Gemini.
    """

    def process(self, speech_data: SpeechOutput) -> SummaryOutput:
        transcript = speech_data.transcript
        
        if not transcript.strip() or transcript == "No transcript recorded.":
            return SummaryOutput(summary="No summary available.", confidence=0.0)

        prompt = f"""
        You are a highly capable Executive Analyst AI.
        Analyze the following meeting transcript and generate a structured summary.
        
        Rules:
        1. Extract the top decisions made in the meeting (up to 5).
        2. Extract key risks or blockers mentioned (up to 5).
        3. Extract completed work or achievements (up to 5).
        4. Synthesize a professional, high-level abstractive executive summary paragraph that incorporates the key highlights. Do not use conversational meta-dialogue, just output a clean prose summary.
        
        Meeting Speakers: {', '.join(speech_data.speakers)}
        
        Transcript:
        {transcript}
        """
        
        try:
            output, _, _ = gemini.generate_structured(prompt, SummaryOutput)
            return output
        except Exception as e:
            logger.error("summary_agent_llm_error", error=str(e))
            return SummaryOutput(
                summary="Failed to generate AI summary due to an error.",
                confidence=0.5
            )
