import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { MeetingUpload } from './components/MeetingUpload';
import { HumanApprovalModal } from './components/HumanApprovalModal';
import { TaskBoard } from './components/TaskBoard';
import { CrossMeetingIntelligence } from './components/CrossMeetingIntelligence';
import { AnalyticsPanel } from './components/AnalyticsPanel';
import { MeetingSearchModal } from './components/MeetingSearchModal';
import { AiExecutionCopilot } from './components/AiExecutionCopilot';
import { ExecutionBriefing } from './components/ExecutionBriefing';

import { fetchTasks, fetchMeetings, fetchDashboardStats } from './services/api';
import { MeetingResponse, EnrichedTask, MeetingRecord, DashboardStats } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('capture');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const initialTasks: EnrichedTask[] = [];

  const [tasks, setTasks] = useState<EnrichedTask[]>(initialTasks);
  const [meetings, setMeetings] = useState<MeetingRecord[]>([]);
  const [isSearchOpen, setIsSearchOpen] = useState<boolean>(false);
  const [isCopilotOpen, setIsCopilotOpen] = useState<boolean>(false);
  
  // Current meeting pipeline result waiting for human approval
  const [pendingMeeting, setPendingMeeting] = useState<MeetingResponse | null>(null);

  const loadData = async () => {
    try {
      const [tData, mData, sData] = await Promise.all([
        fetchTasks(),
        fetchMeetings(),
        fetchDashboardStats(),
      ]);
      if (tData && tData.length > 0) {
        setTasks(tData);
      }
      if (mData && mData.length > 0) {
        setMeetings(mData);
      }
      if (sData) {
        setStats(sData);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Keyboard shortcut ⌘K or Ctrl+K for search modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsSearchOpen(prev => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const handlePipelineComplete = async (data: MeetingResponse) => {
    setPendingMeeting(data);
    if (data.pipeline_result.tasks) {
      const pendingTasks = data.pipeline_result.tasks;
      setTasks(prev => [...pendingTasks, ...prev.filter(pt => !pendingTasks.some(p => p.id === pt.id))]);
    }
    await loadData();
    setActiveTab('approval');
  };

  const handleApproved = async (approvedTasks?: EnrichedTask[]) => {
    setPendingMeeting(null);
    if (approvedTasks && approvedTasks.length > 0) {
      const activeApproved = approvedTasks.map(t => ({ ...t, status: t.status === 'Pending Approval' ? 'Pending' : t.status }));
      setTasks(prev => {
        const remaining = prev.filter(pt => !activeApproved.some(a => a.id === pt.id));
        return [...activeApproved, ...remaining];
      });
    }
    await loadData();
    setActiveTab('board');
  };

  return (
    <div style={{ minHeight: '100vh', paddingBottom: '64px' }}>
      <Header
        stats={stats}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        pendingCount={pendingMeeting ? pendingMeeting.pipeline_result.tasks.length : 0}
        onOpenSearch={() => setIsSearchOpen(true)}
        onOpenCopilot={() => setIsCopilotOpen(true)}
      />

      <main style={{ width: '100%', padding: '0 32px' }}>
        {activeTab === 'capture' && (
          <MeetingUpload onPipelineComplete={handlePipelineComplete} />
        )}

        {activeTab === 'approval' && (
          pendingMeeting ? (
            <HumanApprovalModal
              meetingId={pendingMeeting.meeting_id}
              pipelineResult={pendingMeeting.pipeline_result}
              onApproved={handleApproved}
            />
          ) : (
            <div className="paper-card" style={{ padding: '48px 32px', textAlign: 'center', width: '100%', maxWidth: '800px', margin: '40px auto' }}>
              <div className="announcement-pill" style={{ marginBottom: '12px' }}>
                <span className="tag">Stage 5</span> Human Approval Portal
              </div>
              <h3 className="heading-md" style={{ marginBottom: '8px' }}>No Pending Approvals</h3>
              <p className="body-subtext" style={{ fontSize: '15px', marginBottom: '24px' }}>
                Run a live voice capture, microphone stream, or click below to load a sample meeting for instant review.
              </p>
              <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
                <button className="btn-outline-linen" onClick={() => setActiveTab('capture')}>
                  ️ Go to Meeting Capture Studio
                </button>
              </div>
            </div>
          )
        )}

        {activeTab === 'board' && (
          <div className="space-y-6">
            <ExecutionBriefing />
            <TaskBoard tasks={tasks} onTaskUpdated={loadData} />
          </div>
        )}

        {activeTab === 'intelligence' && (
          <CrossMeetingIntelligence
            recap={stats?.cross_meeting_recap || null}
            meetings={meetings}
          />
        )}

        {activeTab === 'analytics' && (
          <AnalyticsPanel stats={stats} tasks={tasks} />
        )}
      </main>

      {/* RAG Memory Search Modal */}
      <MeetingSearchModal
        isOpen={isSearchOpen}
        onClose={() => setIsSearchOpen(false)}
        meetings={meetings}
      />

      {/* AI Execution Copilot Side Panel */}
      <AiExecutionCopilot
        isOpen={isCopilotOpen}
        onClose={() => setIsCopilotOpen(false)}
        tasks={tasks}
      />

      {/* Floating Prototype Demo Button */}
      <div style={{ position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999 }}>
        <button
          onClick={() => {
            setActiveTab('capture');
            setTimeout(() => {
              window.dispatchEvent(new CustomEvent('START_JUDGE_DEMO'));
            }, 100);
          }}
          style={{
            background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            color: '#fff',
            padding: '12px 24px',
            borderRadius: '100px',
            fontWeight: 800,
            fontSize: '15px',
            boxShadow: '0 8px 32px rgba(15,23,42,0.4)',
            border: '2px solid #38bdf8',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            transition: 'transform 0.2s ease, box-shadow 0.2s ease'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.05)';
            e.currentTarget.style.boxShadow = '0 12px 40px rgba(56, 189, 248, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.boxShadow = '0 8px 32px rgba(15,23,42,0.4)';
          }}
        >
          <span style={{ fontSize: '18px' }}></span>
          <span>Prototype Demo</span>
        </button>
      </div>
    </div>
  );
}
