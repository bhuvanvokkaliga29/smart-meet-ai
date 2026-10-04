from models import MeetingInput, ValidatedTaskList, SummaryOutput
from agents.speech_agent import SpeechAgent
from agents.summary_agent import SummaryAgent
from agents.action_agent import ActionAgent
from agents.owner_agent import OwnerAgent
from agents.deadline_agent import DeadlineAgent
from agents.priority_agent import PriorityAgent
from agents.validation_agent import ValidationAgent
from agents.cross_meeting_agent import CrossMeetingAgent

class MultiAgentOrchestrator:
    """Manager / Dispatcher Agent orchestrating sequential and parallel agent execution."""

    def __init__(self):
        self.speech_agent = SpeechAgent()
        self.summary_agent = SummaryAgent()
        self.action_agent = ActionAgent()
        self.owner_agent = OwnerAgent()
        self.deadline_agent = DeadlineAgent()
        self.priority_agent = PriorityAgent()
        self.validation_agent = ValidationAgent()
        self.cross_meeting_agent = CrossMeetingAgent()

    def run_pipeline(self, input_data: MeetingInput) -> dict:
        # Step 1: Speech-to-Text & Diarization
        speech_output = self.speech_agent.process(input_data)

        # Step 2: Parallel execution (Summary & Action Extraction)
        summary_output = self.summary_agent.process(speech_output)
        raw_task_list = self.action_agent.process(speech_output)

        # Step 3: Sequential task enrichment
        owner_tasks = self.owner_agent.process(raw_task_list, speech_output)
        deadline_tasks = self.deadline_agent.process(owner_tasks, speech_output)
        enriched_tasks = self.priority_agent.process(deadline_tasks, speech_output)

        # Step 4: Validation & Confidence scoring
        validated_list = self.validation_agent.process(enriched_tasks)

        # Step 5: Cross-Meeting Intelligence reconciliation
        reconciled_list = self.cross_meeting_agent.reconcile(validated_list)

        return {
            "transcript": speech_output.transcript,
            "speakers": speech_output.speakers,
            "summary": summary_output.summary,
            "decisions": summary_output.decisions,
            "risks": summary_output.risks,
            "completed_work": summary_output.completed_work,
            "validation_status": reconciled_list.status,
            "overall_confidence": reconciled_list.overall_confidence,
            "tasks": [t.dict() for t in reconciled_list.tasks]
        }
