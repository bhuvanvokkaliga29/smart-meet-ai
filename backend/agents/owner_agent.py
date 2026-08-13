import re
from typing import List
from models import RawTaskList, EnrichedTask, SpeechOutput

class OwnerAgent:
    """Owner & Delegator Resolution Agent:
    Distinguishes the speaker (assigned_by) from the person being addressed (owner).
    Handles direct assignments ("Kevin, please..."), group tasks ("Everyone / Let's..."),
    and self-commitments ("I will...").
    """

    def process(self, task_list: RawTaskList, speech_data: SpeechOutput) -> List[EnrichedTask]:
        enriched = []
        known_speakers = speech_data.speakers or []

        for raw_task in task_list.tasks:
            context = raw_task.context or ""
            t_text = raw_task.task
            
            # Extract speaker (assigned_by) from context prefix ("Sarah: Kevin, please...")
            assigned_by = getattr(raw_task, 'speaker', 'Meeting') or 'Meeting'
            raw_statement = context
            
            if ":" in context:
                parts = context.split(":", 1)
                assigned_by = parts[0].strip()
                raw_statement = parts[1].strip()

            owner = "Unassigned"

            # RULE 1: Direct Assignment to Addressed Person
            # Match: "Kevin, please...", "Emily, finish...", "Priya, improve..."
            addressed_match = re.search(
                r'^\s*([A-Z][a-zA-B0-9]{2,20})\s*,\s*(?:please|can you|could you|make sure|finish|improve|prioritise|prioritize|attend|prepare|conduct|run|add|update|notify)\b',
                raw_statement,
                flags=re.IGNORECASE
            )
            
            if addressed_match:
                candidate_name = addressed_match.group(1).capitalize()
                invalid_words = {'Today', 'Please', 'Meeting', 'Action', 'Review', 'Finish', 'Prepare', 'Complete', 'Decide', 'High', 'Medium', 'Low', 'Task', 'Sprint'}
                if candidate_name not in invalid_words:
                    owner = candidate_name

            # RULE 2: Group Directive ("Everyone...", "Let's...", "We need to...")
            if owner == "Unassigned":
                if re.search(r'\b(?:everyone|all of us|team)\b', raw_statement, flags=re.IGNORECASE) or \
                   re.search(r'^\s*(?:let\'s|we should|we need to|we will|our team)\b', raw_statement, flags=re.IGNORECASE):
                    owner = "Team"

            # RULE 3: Self-Commitment ("I will...", "I'll...", "I'm going to...")
            if owner == "Unassigned":
                if re.search(r'\b(?:i will|i\'ll|i am going to|i\'m gonna|i can|i have|myself)\b', raw_statement, flags=re.IGNORECASE):
                    owner = assigned_by if assigned_by not in ['Meeting', 'Participant'] else "Unassigned"

            # RULE 4: Mention of person in statement ("assigned to Kevin", "ask Emily", "Priya will handle")
            if owner == "Unassigned":
                name_match = re.search(r'\b(?:assigned to|ask|check with|notify)\s+([A-Z][a-zA-B0-9]{2,20})\b', raw_statement, flags=re.IGNORECASE)
                if name_match:
                    owner = name_match.group(1).capitalize()

            # RULE 5: Fallback to speaker if line is a clear single-person statement
            if owner == "Unassigned" and assigned_by not in ['Meeting', 'Participant']:
                owner = assigned_by

            enriched.append(EnrichedTask(
                task=raw_task.task,
                context=raw_task.context,
                owner=owner,
                assigned_by=assigned_by,
                condition=getattr(raw_task, 'condition', None),
                item_type=getattr(raw_task, 'item_type', 'Action Item'),
                confidence=raw_task.confidence
            ))

        return enriched
