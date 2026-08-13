import re
from typing import List
from models import EnrichedTask, SpeechOutput

class PriorityAgent:
    """Priority Agent: Evaluates task urgency, explicit priority statements
    (e.g., 'highest priority', 'imminent deadline'), and assigns Priority levels (High, Medium, Low).
    """

    def process(self, tasks: List[EnrichedTask], speech_data: SpeechOutput) -> List[EnrichedTask]:
        high_keywords = [
            'highest priority', 'high priority', 'prioritise', 'prioritize',
            'critical', 'urgent', 'asap', 'immediately', 'emergency', 'blocker',
            'by monday', 'by thursday', 'by friday', 'by tomorrow', 'today'
        ]

        med_keywords = [
            'medium priority', 'improve', 'prepare', 'complete', 'review', 'verify',
            'update', 'schedule', 'discuss', 'study', 'work on', 'plan', 'integrate',
            'evaluate', 'run'
        ]

        for t in tasks:
            text = f"{t.task} {t.context or ''}".lower()
            
            if any(re.search(r'\b' + re.escape(kw) + r'\b', text) for kw in high_keywords):
                t.priority = "High"
            elif any(re.search(r'\b' + re.escape(kw) + r'\b', text) for kw in med_keywords):
                t.priority = "Medium"
            else:
                t.priority = "Low"

        return tasks
