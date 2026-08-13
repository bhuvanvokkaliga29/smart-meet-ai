import re
from typing import List, Tuple, Optional
from models import SpeechOutput, MeetingInput

class SpeechAgent:
    """Speech Recognition & Diarization Cleaning Agent.
    Normalizes transcript text, fixes concatenated speaker tags, extracts actual speaker names,
    and removes raw speech artifacts.
    """

    def process(self, input_data: MeetingInput) -> SpeechOutput:
        raw_text = input_data.transcript or ""
        
        if not raw_text.strip():
            return SpeechOutput(
                transcript="No transcript recorded.",
                speakers=[],
                confidence=0.5
            )

        # 1. Separate concatenated speaker labels (e.g., "CollegeSpeaker 1: so" -> "College\nSpeaker 1: so")
        # Match patterns like word/char immediately followed by a Speaker label
        cleaned_text = re.sub(r'([^\n])((?:Speaker\s+\d+|[A-Z][a-zA-B0-9\s_]{2,20}):)', r'\1\n\2', raw_text)

        # 2. Extract actual unique speakers from lines
        extracted_speakers = []
        lines = [l.strip() for l in cleaned_text.split('\n') if l.strip()]
        
        normalized_lines = []
        for line in lines:
            speaker_name, content = self._parse_speaker_and_content(line)
            content_cleaned = self._clean_speech_artifacts(content)
            
            if speaker_name:
                if speaker_name not in extracted_speakers:
                    extracted_speakers.append(speaker_name)
                if content_cleaned:
                    normalized_lines.append(f"{speaker_name}: {content_cleaned}")
            else:
                if content_cleaned:
                    normalized_lines.append(content_cleaned)

        final_transcript = "\n".join(normalized_lines) if normalized_lines else raw_text
        final_speakers = extracted_speakers if extracted_speakers else (input_data.speakers or ["Speaker 1"])

        return SpeechOutput(
            transcript=final_transcript,
            speakers=final_speakers,
            confidence=0.92 if len(normalized_lines) > 0 else 0.70
        )

    def _parse_speaker_and_content(self, line: str) -> Tuple[Optional[str], str]:
        """Parse speaker and content from a line, handling double prefixes (e.g. Rahul: BHUVAN: words)."""
        text = line.strip()
        speaker = None
        
        # Iteratively unnest double/triple speaker prefixes (e.g. Rahul: BHUVAN: hello -> BHUVAN: hello)
        safety_count = 0
        while safety_count < 3:
            safety_count += 1
            # Check for Colon match: "Name:"
            m_colon = re.match(r'^([A-Z0-9_\s]{1,30}|[A-Z][a-zA-B0-9\s_]{1,30}):\s*(.*)$', text, re.IGNORECASE)
            if m_colon:
                cand_spk = m_colon.group(1).strip()
                rest = m_colon.group(2).strip()
                # If rest ALSO starts with a speaker tag (e.g., BHUVAN: hello or Bhuvan talks: hello)
                m_inner_colon = re.match(r'^([A-Z0-9_\s]{1,30}|[A-Z][a-zA-B0-9\s_]{1,30}):\s*(.*)$', rest, re.IGNORECASE)
                m_inner_talks = re.match(r'^([A-Z0-9_\s]{1,30}|[A-Z][a-zA-B0-9\s_]{1,30})\s+(?:talks|says|speaking):\s*(.*)$', rest, re.IGNORECASE)
                if m_inner_colon or m_inner_talks:
                    text = rest
                    continue
                else:
                    speaker = cand_spk
                    text = rest
                    break
            
            # Check for Talks match: "Name talks: ..."
            m_talks = re.match(r'^([A-Z0-9_\s]{1,30}|[A-Z][a-zA-B0-9\s_]{1,30})\s+(?:talks|says|speaking):\s*(.*)$', text, re.IGNORECASE)
            if m_talks:
                speaker = m_talks.group(1).strip()
                text = m_talks.group(2).strip()
                break

            # Check for Bracket match: "[Name]: ..."
            m_bracket = re.match(r'^\[([A-Z0-9_\s]{1,30}|[A-Z][a-zA-B0-9\s_]{1,30})\]:\s*(.*)$', text, re.IGNORECASE)
            if m_bracket:
                speaker = m_bracket.group(1).strip()
                text = m_bracket.group(2).strip()
                break

            break

        # Check self-introduction pattern if speaker is generic/default
        m_intro = re.search(r'\bmy name is ([A-Z][a-z]+)\b', text, re.IGNORECASE)
        if m_intro and (not speaker or speaker.lower() in ['rahul', 'participant', 'unknown', 'speaker 1']):
            speaker = m_intro.group(1).capitalize()

        return speaker, text

    def _clean_speech_artifacts(self, text: str) -> str:
        """Clean speech stuttering, repeated words, and informal filler tokens."""
        if not text:
            return ""
        
        # Remove repeated identical words (e.g. "hello hello hello" -> "hello")
        words = text.split()
        dedup_words = []
        for w in words:
            clean_w = re.sub(r'[^\w]', '', w.lower())
            if len(dedup_words) > 0:
                prev_clean = re.sub(r'[^\w]', '', dedup_words[-1].lower())
                if clean_w and clean_w == prev_clean and len(clean_w) > 2:
                    continue
            dedup_words.append(w)
        
        cleaned = " ".join(dedup_words)
        # Clean double spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
