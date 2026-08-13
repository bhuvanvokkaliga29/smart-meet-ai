import uuid
import re
from typing import List
from models import EnrichedTask, ValidatedTaskList

class ValidationAgent:
    """Validation Agent: Merges near-duplicate tasks into single canonical tasks,
    checks completeness, computes confidence scores, and determines review status.
    """

    def process(self, tasks: List[EnrichedTask]) -> ValidatedTaskList:
        if not tasks:
            return ValidatedTaskList(
                status="VALID",
                overall_confidence=0.85,
                tasks=[]
            )

        unique_tasks: List[EnrichedTask] = []
        total_conf = 0.0
        needs_review = False

        for t in tasks:
            clean_title = t.task.strip().lower()
            if len(clean_title) < 4:
                continue

            # Check for near-duplicate or semantic match in unique_tasks list
            duplicate_found = False
            for idx, existing in enumerate(unique_tasks):
                ex_title = existing.task.lower()

                # Calculate word overlap ratio
                t_words = set(re.findall(r'\w{4,}', clean_title))
                ex_words = set(re.findall(r'\w{4,}', ex_title))

                if t_words and ex_words:
                    intersection = t_words.intersection(ex_words)
                    overlap = len(intersection) / max(min(len(t_words), len(ex_words)), 1)

                    if overlap >= 0.65 or (clean_title in ex_title or ex_title in clean_title):
                        duplicate_found = True

                        # Prefer task with explicit deadline or clearer directive
                        if (t.deadline and t.deadline != "No Deadline" and existing.deadline == "No Deadline") or \
                           (len(t.task) > len(existing.task) and "by" in t.task.lower()):
                            unique_tasks[idx] = t # Replace with more specific canonical task
                        break

            if not duplicate_found:
                if not t.id:
                    t.id = f"t-{uuid.uuid4().hex[:6]}"

                if t.owner in ["Unassigned", "Unknown"] or not t.deadline or t.confidence < 0.85:
                    t.status = "Pending Approval (Review Needed)"
                    needs_review = True
                else:
                    t.status = "Pending Approval"

                unique_tasks.append(t)

        total_conf = sum(t.confidence for t in unique_tasks)
        overall_conf = (total_conf / len(unique_tasks)) if unique_tasks else 0.88
        status_flag = "REVIEW" if (needs_review or overall_conf < 0.85) else "VALID"

        return ValidatedTaskList(
            status=status_flag,
            overall_confidence=round(overall_conf, 2),
            tasks=unique_tasks
        )
