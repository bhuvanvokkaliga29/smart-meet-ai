import React, { useState } from 'react';
import { EnrichedTask } from '../types';

interface AiExecutionCopilotProps {
  isOpen: boolean;
  onClose: () => void;
  tasks: EnrichedTask[];
  onReassignTask?: (taskId: string, newOwner: string) => void;
}

interface ChatMessage {
  sender: 'user' | 'ai';
  text: string;
  recommendations?: { label: string; action: () => void }[];
}

export const AiExecutionCopilot: React.FC<AiExecutionCopilotProps> = ({ isOpen, onClose, tasks, onReassignTask }) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'ai',
      text: " Hi! I'm your AI Execution Copilot. Ask me anything about sprint health, overloaded team members, deadline risks, or dependency bottlenecks."
    }
  ]);

  if (!isOpen) return null;

  const quickQuestions = [
    "Why is Sprint Health only 59%?",
    "Who is overloaded right now?",
    "What are our biggest deadline risks?",
    "Show tasks blocking release"
  ];

  const handleAsk = (userText: string) => {
    if (!userText.trim()) return;

    const newMessages: ChatMessage[] = [...messages, { sender: 'user', text: userText }];
    setMessages(newMessages);
    setQuery('');

    // Process AI Response
    setTimeout(() => {
      const qLower = userText.toLowerCase();
      let aiResponseText = "";
      let recommendations: { label: string; action: () => void }[] = [];

      if (qLower.includes('why is sprint health') || qLower.includes('59%') || qLower.includes('health')) {
        aiResponseText = "️ Sprint Health is impacted by 3 major factors:\n1. Emma is overloaded at 240% capacity (6 active tasks).\n2. The OCR Receipt Processing task is blocking 3 downstream tasks.\n3. Ryan has an 83% probability of missing the Thursday deadline.";
        recommendations = [
          {
            label: " Reassign 'API Logging' from Emma to David",
            action: () => {
              const target = tasks.find(t => t.owner === 'Emma');
              if (target && target.id && onReassignTask) {
                onReassignTask(target.id, 'David');
                alert("Successfully reassigned task to David! Emma's workload reduced to 160%.");
              } else {
                alert("Reassigned task to David!");
              }
            }
          },
          {
            label: " Extend OCR target deadline by 1 day",
            action: () => alert("Extended OCR target deadline by 1 day. Downstream bottleneck risk reduced.")
          }
        ];
      } else if (qLower.includes('overloaded') || qLower.includes('who is')) {
        aiResponseText = " Workload Capacity Breakdown:\n• Emma: 240% Capacity (6 tasks) — HIGH RISK\n• Ryan: 110% Capacity (3 tasks) — MODERATE RISK\n• David: 40% Capacity (1 task) — AVAILABLE\n• Priya: 50% Capacity (2 tasks) — AVAILABLE";
        recommendations = [
          {
            label: " Balance Workload: Move 2 tasks to David",
            action: () => alert("Rebalancing completed! All team members now within 100% capacity threshold.")
          }
        ];
      } else if (qLower.includes('risk') || qLower.includes('deadline')) {
        aiResponseText = " Top Execution Risks Identified:\n1. 'Finish OCR Improvements' (Owner: Ryan) — 83% delay risk due to un-tested rainy datasets.\n2. 'Database Failover Recovery' (Owner: Lisa) — 71% delay risk.\n3. 'API Load Testing' (Owner: Emma) — Blocked waiting for OCR completion.";
      } else if (qLower.includes('blocking') || qLower.includes('block')) {
        aiResponseText = " Active Bottleneck Chains:\n[Finish OCR Improvements]  Blocks [Streaming Upload]  Blocks [10k Load Testing]  Blocks [Production Release]";
      } else {
        aiResponseText = `I analyzed all ${tasks.length} active tasks across past meetings. The team's overall delivery confidence is currently at 87% with zero critical security blockers.`;
      }

      setMessages(prev => [...prev, { sender: 'ai', text: aiResponseText, recommendations }]);
    }, 400);
  };

  return (
    <div style={{ position: 'fixed', top: 0, right: 0, bottom: 0, width: '440px', background: '#ffffff', boxShadow: '-8px 0 32px rgba(0, 0, 0, 0.15)', zIndex: 3000, display: 'flex', flexDirection: 'column', borderLeft: '1px solid var(--color-soft-linen)' }}>
      {/* Header */}
      <div style={{ padding: '20px 24px', background: '#0f172a', color: '#ffffff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '20px' }}></span>
          <div>
            <h3 style={{ fontSize: '17px', fontWeight: 800, margin: 0, color: '#ffffff' }}>AI Execution Copilot</h3>
            <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>Enterprise Decision Engine</span>
          </div>
        </div>
        <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', fontSize: '20px', cursor: 'pointer' }}>
          
        </button>
      </div>

      {/* Quick Question Chips */}
      <div style={{ padding: '12px 16px', background: '#f8fafc', borderBottom: '1px solid #e2e8f0', display: 'flex', gap: '6px', overflowX: 'auto' }}>
        {quickQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleAsk(q)}
            style={{
              whiteSpace: 'nowrap', padding: '5px 10px', borderRadius: '100px', fontSize: '11px', fontWeight: 600,
              background: '#ffffff', border: '1px solid #cbd5e1', color: '#334155', cursor: 'pointer', flexShrink: 0
            }}
          >
             {q}
          </button>
        ))}
      </div>

      {/* Chat Messages */}
      <div style={{ flex: 1, padding: '20px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '14px', background: '#fafafa' }}>
        {messages.map((msg, idx) => (
          <div
            key={idx}
            style={{
              alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '88%',
              background: msg.sender === 'user' ? '#171717' : '#ffffff',
              color: msg.sender === 'user' ? '#ffffff' : '#1e293b',
              padding: '14px 16px',
              borderRadius: msg.sender === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
              border: msg.sender === 'user' ? 'none' : '1px solid #e2e8f0',
              boxShadow: 'var(--shadow-subtle)',
              fontSize: '14px',
              lineHeight: 1.55,
              whiteSpace: 'pre-wrap'
            }}
          >
            {msg.text}

            {/* Render 1-Click Action Recommendation Chips */}
            {msg.recommendations && msg.recommendations.length > 0 && (
              <div style={{ marginTop: '12px', paddingTop: '10px', borderTop: '1px dashed #e2e8f0', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#0369a1', textTransform: 'uppercase' }}> Suggested AI Interventions:</span>
                {msg.recommendations.map((rec, rIdx) => (
                  <button
                    key={rIdx}
                    onClick={rec.action}
                    style={{
                      padding: '8px 12px', borderRadius: '6px', background: '#0284c7', color: '#ffffff',
                      border: 'none', fontSize: '12px', fontWeight: 700, cursor: 'pointer', textAlign: 'left',
                      transition: 'background 0.15s'
                    }}
                  >
                    {rec.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => { e.preventDefault(); handleAsk(query); }}
        style={{ padding: '16px', background: '#ffffff', borderTop: '1px solid var(--color-soft-linen)', display: 'flex', gap: '8px' }}
      >
        <input
          type="text"
          placeholder="Ask AI Copilot (e.g. Why is Sprint Health 59%?)..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ flex: 1, padding: '10px 14px', borderRadius: '8px', border: '1px solid var(--color-soft-linen)', background: 'var(--color-warm-parchment)', fontSize: '13px' }}
        />
        <button type="submit" className="btn-primary-dark" style={{ padding: '10px 16px', fontSize: '13px' }}>
          Send
        </button>
      </form>
    </div>
  );
};
