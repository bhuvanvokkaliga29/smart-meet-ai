import React, { useEffect, useState } from 'react';
import { API_BASE } from '../services/api';

interface JudgeTraceModalProps {
  commitmentId: string;
  isOpen: boolean;
  onClose: () => void;
}

export const JudgeTraceModal: React.FC<JudgeTraceModalProps> = ({ commitmentId, isOpen, onClose }) => {
  const [trace, setTrace] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen && commitmentId) {
      setLoading(true);
      fetch(`${API_BASE}/supervisor/trace/${commitmentId}`)
        .then(res => res.json())
        .then(data => {
          setTrace(data.trace || []);
          setLoading(false);
        })
        .catch(err => {
          console.error("Failed to fetch trace", err);
          setLoading(false);
        });
    }
  }, [isOpen, commitmentId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-75 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-4xl flex flex-col h-[80vh] overflow-hidden">
        
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50">
          <div>
            <h2 className="text-lg font-bold text-gray-900 flex items-center">
              <svg className="w-5 h-5 mr-2 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"></path></svg>
              System Trace (Judge Mode)
            </h2>
            <p className="text-sm text-gray-500 mt-1 font-mono">{commitmentId}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 focus:outline-none">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-900 text-gray-300 font-mono text-sm">
          {loading ? (
            <div className="animate-pulse">Fetching execution trace...</div>
          ) : trace.length === 0 ? (
            <div className="text-gray-500">No events found for this commitment. (Only new commitments track state via DB)</div>
          ) : (
            <div className="space-y-4">
              {trace.map((event, idx) => (
                <div key={idx} className="border-l-2 border-indigo-500 pl-4 py-2">
                  <div className="text-xs text-gray-500 mb-1">[{event.timestamp}]</div>
                  <div className="font-bold text-white mb-1">
                    <span className="text-indigo-400">{event.component}</span> :: {event.actor}
                  </div>
                  <div className="text-green-400 mb-1">
                    State Transition: <span className="line-through text-gray-600">{event.from_state || 'NONE'}</span> -&gt; <span className="font-bold">{event.to_state}</span>
                  </div>
                  <div className="text-gray-400">
                    {event.detail}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
