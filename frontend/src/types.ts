export interface SubTask {
  id: string;
  title: string;
  completed: boolean;
}

export interface TaskHistoryItem {
  timestamp: string;
  action: string;
  author: string;
}

export interface EnrichedTask {
  id?: string;
  task: string;
  context?: string;
  owner: string;
  assigned_by?: string;
  deadline: string;
  priority: 'High' | 'Medium' | 'Low';
  condition?: string;
  depends_on?: string;
  progress_percent?: number;
  subtasks?: SubTask[];
  origin_meeting?: string;
  origin_timestamp?: string;
  origin_transcript_quote?: string;
  history?: TaskHistoryItem[];
  confidence: number;
  confidence_level?: string;
  ai_reason?: string;
  status: string;
  item_type?: 'Action Item' | 'Decision' | 'Risk' | 'Completed Work' | 'Follow-up';
  cross_meeting_note?: string;
  needs_confirmation?: boolean;
}

export interface PipelineResult {
  transcript: string;
  speakers: string[];
  summary: string;
  decisions: string[];
  risks?: string[];
  completed_work?: string[];
  validation_status: 'VALID' | 'REVIEW';
  overall_confidence: number;
  tasks: EnrichedTask[];
}

export interface MeetingResponse {
  meeting_id: string;
  title: string;
  pipeline_result: PipelineResult;
}

export interface MeetingRecord {
  id: string;
  title: string;
  date: string;
  transcript: string;
  summary: string;
  decisions: string[];
}

export interface CrossMeetingRecap {
  total_previous_tasks: number;
  completed_count: number;
  pending_count: number;
  blocked_count: number;
  execution_rate?: number;
  topics_needing_followup: string[];
  repeated_blockers?: { topic: string; count: number; severity?: string }[];
  overdue_by_owner?: { owner: string; overdue: number; total?: number }[];
  weekly_trends?: { week: string; tasks: number; completion_rate?: number }[];
  ai_insights?: string[];
  status_recap_text: string;
}

export interface DashboardStats {
  total_meetings: number;
  total_tasks: number;
  completed_tasks: number;
  pending_tasks: number;
  blocked_tasks: number;
  cross_meeting_recap: CrossMeetingRecap;
}
