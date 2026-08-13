import React, { useState } from 'react';
import { CrossMeetingRecap, MeetingRecord } from '../types';

interface CrossMeetingIntelligenceProps {
  recap: CrossMeetingRecap | null;
  meetings: MeetingRecord[];
}

export const CrossMeetingIntelligence: React.FC<CrossMeetingIntelligenceProps> = ({ recap, meetings }) => {
  const [showChangesSummary, setShowChangesSummary] = useState<boolean>(false);
  const [showAllMeetings, setShowAllMeetings] = useState<boolean>(false);
  const [decisionReused, setDecisionReused] = useState<boolean>(false);
  const [rebalanced, setRebalanced] = useState<boolean>(false);

  const repeatedBlockers = recap?.repeated_blockers || [
    { topic: "Dashboard Performance & Page Load Speed", count: 6, severity: "High", timeline: "Week 1  Week 2  Week 3 (Active)" },
    { topic: "OCR Receipt Accuracy & Unrecognized Fonts", count: 4, severity: "High", timeline: "Week 2  Week 3  Week 4 (Improving)" },
    { topic: "Database Backup & Automated Recovery Failover", count: 5, severity: "Medium", timeline: "Week 1  Week 3 (Active Blocker)" }
  ];

  const overdueByOwner = [
    { owner: "Emma", total: rebalanced ? 4 : 6, overdue: rebalanced ? 1 : 3, status: rebalanced ? "Balanced" : "Overloaded" },
    { owner: "David", total: rebalanced ? 4 : 2, overdue: 0, status: "Available" },
    { owner: "Ryan", total: 3, overdue: 1, status: "Moderate" }
  ];

  const decisionLifeCycle = [
    { title: "Adopt FastAPI for Backend Services", status: "Implemented", date: "July 24", impact: "Response time improved by 31%" },
    { title: "Chrome Extension Live Captions", status: "Verified", date: "July 25", impact: "Zero setup friction for end users" },
    { title: "Deployment Target Date", status: "Decision Changed (2x)", date: "July 26", impact: "Postponed 2 days for security audit" }
  ];

  const executionRate = recap?.execution_rate || 92.0;

  return (
    <div className="paper-card" style={{ padding: '32px 40px', width: '100%' }}>
      
      {/* 1. ULTRA-COMPACT SINGLE-ROW PROJECT DNA (Vercel / Linear Style) */}
      <div style={{ background: '#0f172a', borderRadius: '12px', padding: '12px 20px', color: '#ffffff', marginBottom: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', fontSize: '13px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '14px' }}></span>
          <strong style={{ color: '#38bdf8', textTransform: 'uppercase', fontSize: '12px', letterSpacing: '0.6px' }}>Project DNA:</strong>
        </div>
        <div> <strong>Goal:</strong> OCR Accuracy</div>
        <div> <strong>Phase:</strong> Staging Test</div>
        <div> <strong>Risk:</strong> Deploy Failover</div>
        <div> <strong>Lead:</strong> Emma</div>
        <div>️ <strong>Stable:</strong> Auth JWT</div>
        <div>⏱️ <strong>Issue Age:</strong> 18 Days</div>
        <div style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', padding: '3px 10px', borderRadius: '100px', fontWeight: 700, border: '1px solid #38bdf8' }}>
           Memory Coverage: 15 Meetings Indexed (127 Linked Entities)
        </div>
      </div>

      {/* 2. HIGH-VISIBILITY AI MEMORY RECALL & KNOWLEDGE REUSE (Top Priority Placement) */}
      <div style={{ background: '#f0f9ff', border: '1px solid #7dd3fc', borderRadius: '14px', padding: '20px 24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '18px' }}></span>
            <h4 style={{ fontSize: '15px', fontWeight: 800, color: '#0369a1', margin: 0, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              AI Memory Recall & Knowledge Reuse
            </h4>
          </div>
          <span style={{ fontSize: '11px', background: '#e0f2fe', color: '#0369a1', padding: '3px 10px', borderRadius: '100px', fontWeight: 700 }}>
            Semantic Embedding Match
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
          {/* Recall Card */}
          <div style={{ background: '#ffffff', border: '1px solid #bae6fd', padding: '14px 16px', borderRadius: '10px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#0284c7', marginBottom: '4px' }}>
               Contextual Memory Recall:
            </div>
            <div style={{ fontSize: '13px', color: '#0c4a6e', fontWeight: 600 }}>
              Current Discussion: <strong>OCR Receipt Accuracy</strong>  Linked Meetings: <strong>Meeting #2, #5, #9</strong>
            </div>
          </div>

          {/* Knowledge Reuse Card with Priority 9 Memory Match Scores */}
          <div style={{ background: '#ffffff', border: '1px solid #bae6fd', padding: '14px 16px', borderRadius: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <div style={{ fontSize: '12px', fontWeight: 800, color: '#0284c7', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span> Enterprise Knowledge Reuse Alert:</span>
                <span style={{ background: '#dbeafe', color: '#1e40af', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 800 }}>
                  94% Match (Meeting #4)
                </span>
                <span style={{ background: '#f3e8ff', color: '#6b21a8', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 800 }}>
                  Decision Reused 3 Times
                </span>
              </div>
              <div style={{ fontSize: '13px', color: '#0c4a6e', fontWeight: 600 }}>
                Decision "Migrate Redis Caching Layer" was approved in Meeting #4 (94% match) and reused 3 times!
              </div>
            </div>
            <button
              onClick={() => {
                setDecisionReused(true);
                alert("Reused decision from Meeting #4 (94% confidence match)! Saved 45 minutes of team discussion.");
              }}
              style={{
                padding: '8px 14px', borderRadius: '6px', fontSize: '12px', fontWeight: 800, border: 'none', cursor: 'pointer',
                background: decisionReused ? '#22c55e' : '#0284c7', color: '#ffffff', whiteSpace: 'nowrap', boxShadow: '0 2px 6px rgba(2,132,199,0.3)'
              }}
            >
              {decisionReused ? ' Reused (3x)' : 'Accept Suggestion (94% Match)'}
            </button>
          </div>
        </div>
      </div>

      {/* 3. WHAT CHANGED SINCE LAST MEETING & AI ASSISTANT BUTTON */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h3 className="heading-md" style={{ fontSize: '22px', margin: 0 }}>Cross-Meeting Intelligence & Velocity</h3>
          <p style={{ fontSize: '14px', color: 'var(--color-stone)', margin: '2px 0 0 0' }}>
            Tracks decision lifecycles, recurring blockers, and team capacity across sprint sessions.
          </p>
        </div>

        <button
          onClick={() => setShowChangesSummary(!showChangesSummary)}
          className="btn-outline-linen"
          style={{ padding: '8px 16px', borderRadius: '100px', fontSize: '13px', fontWeight: 700 }}
        >
           {showChangesSummary ? 'Hide Delta Briefing' : 'What Changed Since Last Meeting?'}
        </button>
      </div>

      {showChangesSummary && (
        <div style={{ background: '#f8fafc', border: '1px solid #cbd5e1', borderRadius: '12px', padding: '16px 20px', marginBottom: '24px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#334155', marginBottom: '8px' }}>
             Delta Briefing (Since Meeting July 20):
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', fontSize: '12px', color: '#475569', fontWeight: 600 }}>
            <div style={{ background: '#ffffff', padding: '8px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}> 2 Blockers Resolved (Auth & DB)</div>
            <div style={{ background: '#ffffff', padding: '8px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}>️ 1 New Blocker (OCR PDF Memory)</div>
            <div style={{ background: '#ffffff', padding: '8px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}> OCR Accuracy: 88%  96%</div>
            <div style={{ background: '#ffffff', padding: '8px 12px', borderRadius: '6px', border: '1px solid #e2e8f0' }}> Deploy Postponed 2 Days</div>
          </div>
        </div>
      )}

      {/* 4. EVIDENCE-BASED AI EXECUTIVE INSIGHT CARD */}
      <div style={{ background: '#fefce8', border: '1px solid #fef08a', borderRadius: '14px', padding: '20px 24px', marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
          <span style={{ fontSize: '18px' }}></span>
          <h4 style={{ fontSize: '14px', fontWeight: 800, color: '#854d0e', margin: 0, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            AI Executive Insight
          </h4>
        </div>
        <p style={{ fontSize: '14px', color: '#713f12', lineHeight: 1.6, margin: 0, fontWeight: 600 }}>
          "Database Recovery has appeared in 5 of the last 7 meetings and has delayed deployment three consecutive times. Resolving this issue is likely to unblock 4 downstream tasks. Recommend prioritizing Database Failover recovery before introducing new OCR features."
        </p>
      </div>

      {/* 5. EXECUTIVE MEMORY DASHBOARD (Decision Stability 82% & Execution Rate 92%) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '14px', marginBottom: '28px' }}>
        <div style={{ background: '#ffffff', border: '1px solid var(--color-soft-linen)', padding: '16px 20px', borderRadius: '12px', boxShadow: 'var(--shadow-subtle)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-stone)', fontWeight: 600 }}> Decision Stability</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#0284c7', marginTop: '2px' }}>82%</div>
          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>15 unchanged • 3 modified</div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid var(--color-soft-linen)', padding: '16px 20px', borderRadius: '12px', boxShadow: 'var(--shadow-subtle)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-stone)', fontWeight: 600 }}> Execution Rate</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#166534', marginTop: '2px' }}>{executionRate}%</div>
          <div style={{ fontSize: '11px', color: '#15803d', marginTop: '2px' }}>12 completed / 13 created</div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid var(--color-soft-linen)', padding: '16px 20px', borderRadius: '12px', boxShadow: 'var(--shadow-subtle)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-stone)', fontWeight: 600 }}>️ Recurring Blockers</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#dc2626', marginTop: '2px' }}>3 Active</div>
          <div style={{ fontSize: '11px', color: '#b91c1c', marginTop: '2px' }}>OCR, Caching, DB Failover</div>
        </div>

        <div style={{ background: '#ffffff', border: '1px solid var(--color-soft-linen)', padding: '16px 20px', borderRadius: '12px', boxShadow: 'var(--shadow-subtle)' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-stone)', fontWeight: 600 }}>⏱️ Longest Open Blocker</div>
          <div style={{ fontSize: '24px', fontWeight: 800, color: '#d97706', marginTop: '2px' }}>18 Days</div>
          <div style={{ fontSize: '11px', color: '#b45309', marginTop: '2px' }}>PDF Memory Spikes</div>
        </div>
      </div>

      {/* 6. PROJECT EVOLUTION ROADMAP TIMELINE */}
      <div style={{ marginBottom: '28px', background: 'var(--color-warm-parchment)', border: '1px solid var(--color-soft-linen)', borderRadius: '14px', padding: '20px 24px' }}>
        <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--color-stone)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '14px' }}>
          ️ Project Evolution Timeline Across Meetings
        </h4>
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center', overflowX: 'auto', paddingBottom: '4px' }}>
          {[
            { step: 'Meeting 1', topic: 'Architecture & Stack', status: 'Completed' },
            { step: 'Meeting 2', topic: 'Database & Auth Schema', status: 'Completed' },
            { step: 'Meeting 3', topic: 'OCR Model Fine-Tuning', status: 'In Progress' },
            { step: 'Meeting 4', topic: '10k Load Testing', status: 'Pending' },
            { step: 'Meeting 5', topic: 'Client Demonstration', status: 'Upcoming' }
          ].map((item, idx) => (
            <React.Fragment key={idx}>
              <div style={{ background: '#ffffff', border: '1px solid var(--color-soft-linen)', borderRadius: '8px', padding: '10px 14px', minWidth: '170px' }}>
                <div style={{ fontSize: '11px', fontWeight: 800, color: '#0284c7', textTransform: 'uppercase' }}>{item.step}</div>
                <div style={{ fontSize: '13px', fontWeight: 700, color: '#171717', margin: '2px 0' }}>{item.topic}</div>
                <div style={{ fontSize: '11px', color: item.status === 'Completed' ? '#166534' : item.status === 'In Progress' ? '#92400e' : '#64748b', fontWeight: 600 }}>
                  ● {item.status}
                </div>
              </div>
              {idx < 4 && <div style={{ fontSize: '16px', color: '#94a3b8' }}></div>}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* 7. RECURRING BLOCKERS & OWNER INTELLIGENCE WITH AI RECOMMENDATIONS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '28px' }}>
        
        {/* Recurring Blockers */}
        <div style={{ background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '14px', padding: '20px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#991b1b', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
            ️ Recurring Blockers Lifecycle
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {repeatedBlockers.map((b, idx) => (
              <div key={idx} style={{ background: '#ffffff', border: '1px solid #fee2e2', borderRadius: '8px', padding: '10px 14px' }}>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#7f1d1d' }}>{b.topic}</div>
                <div style={{ fontSize: '12px', color: '#b91c1c', marginTop: '3px', fontWeight: 600 }}>
                  Mentioned: <strong>{b.count} meetings</strong> • Timeline: <span>{b.timeline}</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Owner Intelligence with AI Action */}
        <div style={{ background: '#fffbe8', border: '1px solid #fde68a', borderRadius: '14px', padding: '20px' }}>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#92400e', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '12px' }}>
             Owner Intelligence & Workload AI
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {overdueByOwner.map((o, idx) => (
              <div key={idx} style={{ background: '#ffffff', border: '1px solid #fef08a', borderRadius: '8px', padding: '10px 14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '14px', fontWeight: 700, color: '#78350f' }}>{o.owner} ({o.total} tasks)</div>
                  <div style={{ fontSize: '12px', color: o.overdue > 0 ? '#dc2626' : '#166534', fontWeight: 600 }}>
                    {o.overdue > 0 ? `️ ${o.overdue} overdue (${o.status})` : ' Available Capacity'}
                  </div>
                </div>
                {o.owner === 'Emma' && !rebalanced && (
                  <button
                    onClick={() => {
                      setRebalanced(true);
                      alert("Rebalanced workload! Reassigned 2 tasks from Emma to David.");
                    }}
                    style={{ padding: '6px 10px', borderRadius: '6px', background: '#dc2626', color: '#ffffff', border: 'none', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
                  >
                    Accept Suggestion
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 8. RECENT MEETINGS (TOP 3 DEFAULT + COLLAPSIBLE "VIEW ALL MEETINGS") */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 className="heading-md" style={{ fontSize: '20px', margin: 0 }}>
          Recent Meeting Records ({meetings.length})
        </h3>
        <button
          onClick={() => setShowAllMeetings(!showAllMeetings)}
          className="btn-outline-linen"
          style={{ padding: '6px 14px', borderRadius: '100px', fontSize: '13px', fontWeight: 700, color: '#0284c7' }}
        >
          {showAllMeetings ? '▲ Show Recent 3 Meetings' : `▼ View All Meetings (${meetings.length})`}
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        {(showAllMeetings ? meetings : meetings.slice(0, 3)).map((m, idx) => (
          <div key={m.id || idx} style={{ background: '#ffffff', border: '1px solid var(--color-soft-linen)', borderRadius: '12px', padding: '18px', boxShadow: 'var(--shadow-subtle)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
              <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--color-ink-black)' }}>{m.title}</div>
              <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 600 }}> {m.date}</div>
            </div>

            <div style={{ display: 'flex', gap: '8px', fontSize: '11px', color: '#475569', marginBottom: '10px', fontWeight: 600 }}>
              <span> 6 Participants</span> • <span>⏱️ 48m</span> • <span style={{ color: '#0284c7', fontWeight: 700 }}> Score: 91%</span>
            </div>

            <p style={{ fontSize: '12px', color: '#334155', marginBottom: '12px', lineHeight: 1.45 }}>
              {m.summary.length > 90 ? m.summary.substring(0, 87) + '...' : m.summary}
            </p>

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              <span style={{ background: '#dbeafe', color: '#1e40af', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>
                Tasks: {m.decisions.length * 2 + 1}
              </span>
              <span style={{ background: '#fef3c7', color: '#92400e', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>
                Decisions: {m.decisions.length}
              </span>
              <span style={{ background: '#f3f4f6', color: '#374151', padding: '2px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>
                Topics: OCR, Deploy
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
