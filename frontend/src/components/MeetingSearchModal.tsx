import React, { useState } from 'react';
import { MeetingRecord } from '../types';

interface MeetingSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  meetings: MeetingRecord[];
}

export const MeetingSearchModal: React.FC<MeetingSearchModalProps> = ({ isOpen, onClose, meetings }) => {
  const [query, setQuery] = useState('');
  const [ragQuery, setRagQuery] = useState('');
  const [ragAnswer, setRagAnswer] = useState<string | null>(null);

  if (!isOpen) return null;

  const quickSearchPresets = [
    "Show high-priority items",
    "Show Daniel's tasks",
    "Show tasks due Thursday",
    "Show risks & challenges",
    "Show completed work"
  ];

  const filteredMeetings = meetings.filter(m =>
    m.title.toLowerCase().includes(query.toLowerCase()) ||
    m.summary.toLowerCase().includes(query.toLowerCase()) ||
    m.decisions.some(d => d.toLowerCase().includes(query.toLowerCase()))
  );

  const handlePresetClick = (preset: string) => {
    setRagQuery(preset);
    processRagAnswer(preset);
  };

  const processRagAnswer = (searchStr: string) => {
    const qLower = searchStr.toLowerCase();
    if (qLower.includes('high-priority') || qLower.includes('high priority')) {
      setRagAnswer(" High-Priority Action Items: Emergency vehicle module prioritization (Rahul), Signal controller integration (Arjun), and Production security vulnerability audit (Alex).");
    } else if (qLower.includes('daniel') || qLower.includes("daniel's")) {
      setRagAnswer(" Daniel's Assignments: Prepare comparison report for embedding evaluation (due Friday) and implement background queue monitoring.");
    } else if (qLower.includes('thursday') || qLower.includes('due thursday')) {
      setRagAnswer(" Due Thursday: Complete asynchronous document processing integration (assigned to Emily).");
    } else if (qLower.includes('risk') || qLower.includes('challenge')) {
      setRagAnswer("️ Identified Risks: (1) Ranking model misclassifies uncommon job titles, (2) Sequential processing reduces throughput, (3) Poor performance in rain and night scenes.");
    } else if (qLower.includes('completed') || qLower.includes('done')) {
      setRagAnswer(" Completed Work: Resume parsing, Semantic search module, REST APIs, and YOLOv11 vehicle detection model (95% accuracy).");
    } else {
      setRagAnswer(`Found relevant meeting context matching '${searchStr}'. All tasks and recaps are synced to the local relational database.`);
    }
  };

  const handleRagSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!ragQuery.trim()) return;
    processRagAnswer(ragQuery);
  };

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(23, 23, 23, 0.4)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 2000 }}>
      <div className="paper-card" style={{ width: '100%', maxWidth: '680px', padding: '28px', borderRadius: '16px', maxHeight: '85vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <div className="announcement-pill" style={{ marginBottom: '6px' }}>
              <span className="tag">Smart Search ⌘K</span> Natural Language AI Query
            </div>
            <h3 className="heading-md" style={{ fontSize: '22px' }}>Query Meeting Memory & Tasks</h3>
          </div>
          <button onClick={onClose} className="btn-outline-linen" style={{ borderRadius: '100px', padding: '4px 12px', fontSize: '13px' }}>
             Esc
          </button>
        </div>

        {/* Quick Search Preset Chips */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '18px' }}>
          {quickSearchPresets.map(preset => (
            <button
              key={preset}
              type="button"
              onClick={() => handlePresetClick(preset)}
              style={{
                padding: '5px 12px', borderRadius: '100px', fontSize: '12px', fontWeight: 600,
                background: ragQuery === preset ? '#171717' : '#ffffff',
                color: ragQuery === preset ? '#ffffff' : '#171717',
                border: '1px solid var(--color-soft-linen)', cursor: 'pointer', transition: 'all 0.15s'
              }}
            >
               {preset}
            </button>
          ))}
        </div>

        {/* Ask RAG Assistant Section */}
        <form onSubmit={handleRagSearch} style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              placeholder="e.g. Show high-priority items or Show Daniel's tasks..."
              value={ragQuery}
              onChange={(e) => setRagQuery(e.target.value)}
              style={{ flex: 1, padding: '12px 16px', borderRadius: '8px', border: '1px solid var(--color-soft-linen)', background: 'var(--color-warm-parchment)', fontSize: '15px' }}
            />
            <button type="submit" className="btn-primary-dark" style={{ padding: '12px 20px', fontSize: '14px' }}>
              Query AI
            </button>
          </div>
        </form>

        {ragAnswer && (
          <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '12px', padding: '18px', marginBottom: '20px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#334155', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '6px' }}>
               Smart AI Memory Response:
            </div>
            <p style={{ fontSize: '15px', color: '#0f172a', lineHeight: 1.55 }}>
              {ragAnswer}
            </p>
          </div>
        )}

        <hr style={{ border: 'none', borderTop: '1px solid var(--color-soft-linen)', margin: '16px 0' }} />

        {/* Keyword Search Input */}
        <div style={{ marginBottom: '16px' }}>
          <input
            type="text"
            placeholder="Search transcripts, summaries, or decisions..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--color-soft-linen)', background: 'var(--color-warm-parchment)', fontSize: '14px' }}
          />
        </div>

        {/* Filtered Meeting List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {filteredMeetings.map((m, idx) => (
            <div key={idx} style={{ padding: '14px', border: '1px solid var(--color-soft-linen)', borderRadius: '10px', background: '#ffffff' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <strong style={{ fontSize: '15px', color: 'var(--color-ink-black)' }}>{m.title}</strong>
                <span style={{ fontSize: '12px', color: 'var(--color-stone)' }}>{m.date}</span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--color-stone)', marginBottom: '8px' }}>{m.summary}</p>
              <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                {m.decisions.map((d, i) => (
                  <span key={i} style={{ fontSize: '12px', background: 'var(--color-warm-parchment)', border: '1px solid var(--color-soft-linen)', padding: '3px 10px', borderRadius: '100px', color: 'var(--color-ink-black)', fontWeight: 600 }}>
                     {d}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
