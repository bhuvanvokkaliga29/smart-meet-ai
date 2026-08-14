from models import SpeechOutput, MeetingInput
from llm_provider import gemini
import structlog

logger = structlog.get_logger(__name__)

class SpeechAgent:
    """Speech Recognition & Diarization Cleaning Agent (LLM-Powered).
    Normalizes transcript text, fixes concatenated speaker tags, extracts actual speaker names,
    and removes raw speech artifacts using Gemini.
    """

    def process(self, input_data: MeetingInput) -> SpeechOutput:
        raw_text = input_data.transcript or ""
        
        if not raw_text.strip():
            return SpeechOutput(
                transcript="No transcript recorded.",
                speakers=[],
                confidence=0.5
            )

        prompt = f"""
        You are an expert Speech Diarization and Transcription Cleanup AI.
        Clean the following raw meeting transcript.
        
        Rules:
        1. Separate concatenated speaker labels (e.g., if a line says "Bhuvan talks: Rahul: hello", untangle it appropriately).
        2. Clean up speech artifacts like stuttering, repeated words, and filler words ("um", "uh", "you know").
        3. Extract all actual, unique speaker names from the dialogue.
        4. Do NOT summarize or change the meaning of the sentences, just clean the text and format it properly as 'Speaker: Content'.

        Raw Transcript:
        {raw_text}
        """
        
        try:
            output, model, latency = gemini.generate_structured(prompt, SpeechOutput)
            
            # Fallback to input speakers if none detected
            if not output.speakers and input_data.speakers:
                output.speakers = input_data.speakers
                
            return output
        except Exception as e:
            logger.error("speech_agent_llm_error", error=str(e))
            return SpeechOutput(
                transcript=raw_text,
                speakers=input_data.speakers or ["Participant"],
                confidence=0.5
            )
