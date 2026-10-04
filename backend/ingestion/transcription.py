import abc
import time
from typing import List
from .events import TranscriptSegmentEvent, MeetingSource, EventType

class TranscriptionProvider(abc.ABC):
    @abc.abstractmethod
    def process_audio(self, audio_bytes: bytes, meeting_id: str) -> List[TranscriptSegmentEvent]:
        pass

class DemoAudioProvider(TranscriptionProvider):
    """
    Robust mock implementation for demoing platform-independence without direct Google Cloud STT keys.
    Simulates speech processing, diarization, and multilingual normalization.
    """
    def process_audio(self, audio_bytes: bytes, meeting_id: str) -> List[TranscriptSegmentEvent]:
        time.sleep(2) # simulate processing latency
        
        # We simulate a code-switched Kannada/English meeting that produces action items
        # to prove the new schema and downstream agents can handle multilingual normalized text.
        events = [
            TranscriptSegmentEvent(
                meeting_id=meeting_id,
                source=MeetingSource.UPLOADED_AUDIO,
                speaker_label="Speaker A",
                speaker_confidence=0.92,
                language="kn-IN",
                original_text="Namaskara team. Namma project progress review madona.",
                normalized_text="Hello team. Let's review our project progress.",
                timestamp_start=time.time() - 60,
                timestamp_end=time.time() - 55
            ),
            TranscriptSegmentEvent(
                meeting_id=meeting_id,
                source=MeetingSource.UPLOADED_AUDIO,
                speaker_label="Speaker B",
                speaker_confidence=0.88,
                language="en",
                original_text="I will prepare the final API architecture by Wednesday.",
                normalized_text="I will prepare the final API architecture by Wednesday.",
                timestamp_start=time.time() - 50,
                timestamp_end=time.time() - 45
            ),
            TranscriptSegmentEvent(
                meeting_id=meeting_id,
                source=MeetingSource.UPLOADED_AUDIO,
                speaker_label="Speaker A",
                speaker_confidence=0.94,
                language="en",
                original_text="Excellent. Bhuvan, please deploy the staging environment after that.",
                normalized_text="Excellent. Bhuvan, please deploy the staging environment after that.",
                timestamp_start=time.time() - 40,
                timestamp_end=time.time() - 35
            ),
            TranscriptSegmentEvent(
                meeting_id=meeting_id,
                source=MeetingSource.UPLOADED_AUDIO,
                speaker_label="Speaker C",
                speaker_confidence=0.65, # Low confidence to trigger Needs Confirmation UI
                language="en",
                original_text="I'll write the documentation if QA passes.",
                normalized_text="I'll write the documentation if QA passes.",
                timestamp_start=time.time() - 30,
                timestamp_end=time.time() - 25
            )
        ]
        return events
