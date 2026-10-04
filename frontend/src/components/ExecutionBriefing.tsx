import React, { useEffect, useState } from 'react';
import { API_BASE } from '../services/api';

export const ExecutionBriefing: React.FC = () => {
  const [briefing, setBriefing] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/supervisor/briefing`)
      .then(res => res.json())
      .then(data => {
        setBriefing(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch briefing", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-4 border rounded shadow-sm bg-white animate-pulse h-32">Loading Supervisor Briefing...</div>;
  }

  if (!briefing) return null;

  return (
    <div style={{ padding: '20px', border: '1px solid #e2e8f0', borderRadius: '8px', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)', background: 'linear-gradient(to bottom right, #eff6ff, #ffffff)', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
        <svg style={{ width: '24px', height: '24px', color: '#4f46e5', marginRight: '8px' }} fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
        <h2 style={{ fontSize: '20px', fontWeight: 'bold', color: '#1f2937', margin: 0 }}>Next-Meeting Briefing</h2>
      </div>
      
      <p style={{ fontSize: '14px', color: '#4b5563', marginBottom: '16px', margin: '0 0 16px 0' }}>
        Synthesized by the Execution Supervisor Agent. Use these points to start the next meeting.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: '#374151', textTransform: 'uppercase', letterSpacing: '0.025em', margin: '0 0 8px 0' }}>Recommended Discussion Points</h3>
          <ul style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '8px', padding: 0, margin: 0, listStyle: 'none' }}>
            {briefing.recommended_discussion_points?.map((point: string, idx: number) => (
              <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', fontSize: '14px' }}>
                <span style={{ color: '#6366f1', marginRight: '8px' }}>•</span>
                <span style={{ color: '#1f2937' }}>{point}</span>
              </li>
            ))}
          </ul>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginTop: '16px' }}>
          <div style={{ padding: '12px', backgroundColor: '#fef2f2', border: '1px solid #fee2e2', borderRadius: '6px' }}>
            <h4 style={{ fontSize: '12px', fontWeight: 'bold', color: '#991b1b', textTransform: 'uppercase', margin: '0 0 4px 0' }}>Blocked Commitments</h4>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#dc2626' }}>{briefing.blocked_commitments?.length || 0}</div>
          </div>
          <div style={{ padding: '12px', backgroundColor: '#fffbeb', border: '1px solid #fef3c7', borderRadius: '6px' }}>
            <h4 style={{ fontSize: '12px', fontWeight: 'bold', color: '#92400e', textTransform: 'uppercase', margin: '0 0 4px 0' }}>At-Risk Deadlines</h4>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#d97706' }}>{briefing.at_risk_commitments?.length || 0}</div>
          </div>
        </div>
      </div>
    </div>
  );
};
