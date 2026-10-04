import React from 'react';
import { DashboardStats } from '../types';

interface HeaderProps {
  stats: DashboardStats | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingCount: number;
  onOpenSearch: () => void;
  onOpenCopilot?: () => void;
}

export const Header: React.FC<HeaderProps> = ({ stats, activeTab, setActiveTab, pendingCount, onOpenSearch, onOpenCopilot }) => {
  return (
    <nav className="floating-nav-pill">
      {/* Brand Logo */}
      <div 
        style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', minWidth: '180px' }} 
        onClick={() => setActiveTab('capture')}
      >
        <span style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-ink-black)', letterSpacing: '-0.5px' }}>
          SmartMeet AI
        </span>
        <span style={{ fontSize: '11px', background: 'var(--color-ink-black)', color: '#ffffff', padding: '3px 8px', borderRadius: '100px', fontWeight: 600 }}>
          v2.0
        </span>
      </div>

      {/* Navigation Pills with Progress Flow */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        {[
          { id: 'capture', label: '1. Ingest & Capture' },
          { id: 'approval', label: `2. Human Approval ${pendingCount > 0 ? `(${pendingCount})` : ''}` },
          { id: 'board', label: '3. Execution Board' },
          { id: 'intelligence', label: '4. Cross-Meeting Memory' },
          { id: 'analytics', label: '5. Analytics' },
        ].map((tab, idx) => {
          const isActive = activeTab === tab.id;
          const isDone = (activeTab === 'approval' && idx === 0) || 
                         (activeTab === 'board' && idx <= 1) || 
                         (activeTab === 'intelligence' && idx <= 2) || 
                         (activeTab === 'analytics' && idx <= 3);

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '8px 16px',
                borderRadius: '100px',
                fontSize: '14px',
                fontWeight: isActive ? 700 : 500,
                color: isActive ? '#ffffff' : isDone ? '#059669' : 'var(--color-ink-black)',
                background: isActive ? 'var(--color-ink-black)' : isDone ? '#ecfdf5' : 'transparent',
                border: isDone && !isActive ? '1px solid #a7f3d0' : 'none',
                whiteSpace: 'nowrap',
                transition: 'all 0.15s ease'
              }}
            >
              {isDone && !isActive ? ` ${tab.label.split('. ')[1]}` : tab.label}
            </button>
          );
        })}
      </div>

      {/* Action Controls & AI Copilot Launcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', minWidth: '220px', justifyContent: 'flex-end' }}>
        {onOpenCopilot && (
          <button
            onClick={onOpenCopilot}
            className="btn-primary-dark"
            style={{ padding: '7px 16px', borderRadius: '100px', fontSize: '13px', fontWeight: 700, background: '#0f172a', color: '#ffffff', border: '1px solid #38bdf8' }}
          >
             AI Copilot
          </button>
        )}

        <button
          onClick={onOpenSearch}
          className="btn-outline-linen"
          style={{ padding: '7px 14px', borderRadius: '100px', fontSize: '13px' }}
        >
           Search ⌘K
        </button>
      </div>
    </nav>
  );
};
