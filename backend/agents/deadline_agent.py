import re
import datetime
from typing import List
from models import EnrichedTask, SpeechOutput

class DeadlineAgent:
    """Deadline Agent: Resolves explicit dates, relative days (today, tomorrow, Friday, next week),
    and assigns intelligent ISO deadlines without static hardcoded dates.
    """

    def process(self, tasks: List[EnrichedTask], speech_data: SpeechOutput) -> List[EnrichedTask]:
        today = datetime.date.today()

        day_offsets = {
            'today': 0,
            'tonight': 0,
            'tomorrow': 1,
            'monday': (0 - today.weekday()) % 7 or 7,
            'tuesday': (1 - today.weekday()) % 7 or 7,
            'wednesday': (2 - today.weekday()) % 7 or 7,
            'thursday': (3 - today.weekday()) % 7 or 7,
            'friday': (4 - today.weekday()) % 7 or 7,
            'saturday': (5 - today.weekday()) % 7 or 7,
            'sunday': (6 - today.weekday()) % 7 or 7,
            'next week': 7,
            'in 2 days': 2,
            'in 3 days': 3,
            'in a week': 7,
        }

        for t in tasks:
            search_text = f"{t.task} {t.context or ''}".lower()
            
            # Check for explicit ISO or DD-MM-YYYY dates in text (e.g. 31-07-2026 or 2026-07-31)
            date_match = re.search(r'\b(\d{2,4}[-/\.]\d{1,2}[-/\.]\d{2,4})\b', search_text)
            if date_match:
                d_str = date_match.group(1)
                t.deadline = d_str
                continue

            # Check relative day keywords
            matched_offset = None
            for kw, offset in day_offsets.items():
                if kw in search_text:
                    matched_offset = offset
                    break

            if matched_offset is not None:
                target_date = today + datetime.timedelta(days=matched_offset)
                t.deadline = target_date.strftime("%Y-%m-%d")
            else:
                # Default business deadline: 5 days from today
                target_date = today + datetime.timedelta(days=5)
                t.deadline = target_date.strftime("%Y-%m-%d")

        return tasks
