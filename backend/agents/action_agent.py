import re
from typing import List, Tuple, Optional
from models import RawTaskList, RawTask, SpeechOutput
from agents.intent_classifier import IntentClassifier

class ActionAgent:
    """Stage 2 Action Extractor Agent:
    Uses Stage 1 IntentClassifier to filter out non-action clauses (Decisions, Completed, Risks, Information, Questions).
    Extracts high-recall technical action items and separates conditional triggers.
    """

    def process(self, speech_data: SpeechOutput) -> RawTaskList:
        transcript = speech_data.transcript
        lines = [l.strip() for l in transcript.split('\n') if l.strip()]
        tasks: List[RawTask] = []
        seen_tasks = set()

        for line in lines:
            speaker = "Participant"
            text = line
            if ":" in line:
                parts = line.split(":", 1)
                speaker = parts[0].strip()
                text = parts[1].strip()

            # Split utterance into sentences/clauses
            clauses = re.split(r'[\.\!\?\;\n]|\b(?:then|and|also|furthermore)\b', text, flags=re.IGNORECASE)

            for clause in clauses:
                c_clean = clause.strip()
                if len(c_clean) < 5:
                    continue

                # Stage 1: Intent Classification
                intent, confidence = IntentClassifier.classify(c_clean)

                # ONLY process Stage 2 if Stage 1 intent is 'Action'
                if intent == "Action":
                    task_title, condition_str = self._extract_action_details(c_clean)

                    if task_title:
                        norm_key = task_title.lower()
                        if norm_key not in seen_tasks:
                            seen_tasks.add(norm_key)
                            tasks.append(RawTask(
                                task=task_title,
                                context=f"{speaker}: {c_clean}",
                                speaker=speaker,
                                condition=condition_str,
                                item_type="Action Item",
                                confidence=confidence
                            ))

        return RawTaskList(tasks=tasks[:12])

    def _extract_action_details(self, clause: str) -> Tuple[str, Optional[str]]:
        """Stage 2: Formats task title and extracts conditional clause ('If [condition], [action]')."""
        condition_str = None
        
        # 1. Condition extraction
        cond_match = re.search(r'^\s*if\s+(.*?),\s*(.*)$', clause, flags=re.IGNORECASE)
        if cond_match:
            raw_cond = cond_match.group(1).strip()
            raw_action = cond_match.group(2).strip()
            condition_str = f"If {raw_cond}"
            clause = raw_action

        # 2. Clean task title formatting
        cleaned = re.sub(r'^\s*[A-Z][a-zA-B0-9]{2,20}\s*,\s*(?:please|can you|could you|make sure|finish|improve)?\s*', '', clause, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'^(?:we need to|i think we should|make sure to|please|i will|i\'ll|you should|we have to|our task is to)\s*', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'\b(?:fucking|bitch|shit|crap|damn)\b', '', cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        if len(cleaned) < 4:
            return "", None

        task_title = cleaned[0].upper() + cleaned[1:]

        if len(task_title) > 90:
            task_title = task_title[:87] + "..."

        return task_title, condition_str
