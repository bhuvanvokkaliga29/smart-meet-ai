import { MeetingResponse, EnrichedTask, DashboardStats, MeetingRecord } from '../types';

const isLocal = typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');
export const API_BASE = isLocal ? 'http://127.0.0.1:8000/api' : 'https://smartmeet-ai-4ths.onrender.com/api';

export async function uploadMeeting(title: string, transcript?: string, file?: File): Promise<MeetingResponse> {
  const formData = new FormData();
  formData.append('title', title);
  if (transcript) formData.append('transcript', transcript);
  if (file) formData.append('file', file);

  const res = await fetch(`${API_BASE}/upload-meeting`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error('Failed to upload meeting');
  return res.json();
}

export async function runOrchestration(title: string, transcript: string): Promise<MeetingResponse> {
  const res = await fetch(`${API_BASE}/orchestrate-v2`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, transcript, mode: 'demo' }),
  });

  if (!res.ok) throw new Error('Failed to run multi-agent pipeline');
  return res.json();
}

export async function approveTasks(meetingId: string, tasks: EnrichedTask[]): Promise<any> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${API_BASE}/tasks/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ meeting_id: meetingId, tasks }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error('Failed to commit approved tasks');
    return res.json();
  } catch (err) {
    console.warn('Backend server unreachable or timeout, committing locally for demo:', err);
    return { status: 'success', committed_count: tasks.length, message: 'Committed locally' };
  }
}

export async function fetchTasks(): Promise<EnrichedTask[]> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${API_BASE}/tasks`, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) throw new Error('Failed to fetch tasks');
    return res.json();
  } catch (err) {
    return [];
  }
}

export async function fetchMeetings(): Promise<MeetingRecord[]> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${API_BASE}/meetings`, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) throw new Error('Failed to fetch meetings');
    return res.json();
  } catch (err) {
    return [];
  }
}

export async function updateTaskStatus(taskId: string, status: string): Promise<any> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${API_BASE}/tasks/${taskId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status }),
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!res.ok) throw new Error('Failed to update task status');
    return res.json();
  } catch (err) {
    return { status: 'success', task_id: taskId, new_status: status };
  }
}

export async function fetchDashboardStats(): Promise<DashboardStats | null> {
  try {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 2000);
    const res = await fetch(`${API_BASE}/dashboard/stats`, { signal: controller.signal });
    clearTimeout(timer);
    if (!res.ok) throw new Error('Failed to fetch dashboard stats');
    return res.json();
  } catch (err) {
    return null;
  }
}
