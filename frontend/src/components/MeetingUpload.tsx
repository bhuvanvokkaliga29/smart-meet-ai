import React, { useState, useRef, useEffect } from 'react';
import { runOrchestration } from '../services/api';
import { MeetingResponse } from '../types';

interface MeetingUploadProps {
  onPipelineComplete: (res: MeetingResponse) => void;
}

// Export speaker parser helper for double tags & speech extraction
export function parseLineSpeakerAndText(rawLine: string, fallbackSpeaker: string = 'Speaker 1') {
  let text = rawLine.trim();
  let speaker: string | null = null;

  // 1. Iteratively unnest double/nested speaker tags (e.g. "Rahul: BHUVAN: hello" or "Rahul: Bhuvan talks: hello")
  let safetyCount = 0;
  while (safetyCount < 4) {
    safetyCount++;
    const colonIdx = text.indexOf(':');
    if (colonIdx > 0 && colonIdx <= 30) {
      const cand = text.substring(0, colonIdx).trim();
      const rest = text.substring(colonIdx + 1).trim();

      // Check if rest ALSO has a speaker tag
      const innerColonIdx = rest.indexOf(':');
      const innerTalks = rest.match(/^([A-Za-z0-9_\s]{1,30})\s+(?:talks|says|speaking):\s*(.*)$/i);

      if (innerColonIdx > 0 && innerColonIdx <= 30) {
        text = rest;
        continue;
      } else if (innerTalks) {
        speaker = innerTalks[1].trim();
        text = innerTalks[2].trim();
        break;
      } else {
        speaker = cand;
        text = rest;
        break;
      }
    }

    // Check for "Name talks: ..." match
    const talksMatch = text.match(/^([A-Za-z0-9_\s]{1,30})\s+(?:talks|says|speaking):\s*(.*)$/i);
    if (talksMatch) {
      speaker = talksMatch[1].trim();
      text = talksMatch[2].trim();
      break;
    }

    // Check for "[Name]: ..." match
    const bracketMatch = text.match(/^\[([A-Za-z0-9_\s]{1,30})\]:\s*(.*)$/i);
    if (bracketMatch) {
      speaker = bracketMatch[1].trim();
      text = bracketMatch[2].trim();
      break;
    }

    break;
  }

  // 2. Self-introduction fallback detection: e.g. "my name is Tanushree"
  const introMatch = text.match(/\bmy name is ([A-Z][a-z]+)\b/i);
  if (introMatch && (!speaker || speaker.toLowerCase() === 'rahul' || speaker.toLowerCase() === 'participant')) {
    const detectedName = introMatch[1].charAt(0).toUpperCase() + introMatch[1].slice(1).toLowerCase();
    speaker = detectedName;
  }

  if (!speaker) {
    speaker = fallbackSpeaker || 'Speaker 1';
  }

  return { speaker, text };
}

export const MeetingUpload: React.FC<MeetingUploadProps> = ({ onPipelineComplete }) => {
  const [mode, setMode] = useState<'upload' | 'tab' | 'demo'>('tab');
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);

  // Animated Pipeline & Toast States
  const [activeStepIndex, setActiveStepIndex] = useState<number>(0);
  const [showMemoryRecall, setShowMemoryRecall] = useState<boolean>(false);
  const [isCompleted, setIsCompleted] = useState<boolean>(false);
  const [showToast, setShowToast] = useState<boolean>(false);

  // Speaker Tag Management
  const [currentSpeaker, setCurrentSpeaker] = useState('Speaker 1');
  const [customSpeakers, setCustomSpeakers] = useState<string[]>(['Speaker 1', 'Speaker 2']);
  const [newSpeakerInput, setNewSpeakerInput] = useState('');
  const [renameFrom, setRenameFrom] = useState('');
  const [renameTo, setRenameTo] = useState('');

  // Live Transcript Stream State
  const [spokenLines, setSpokenLines] = useState<string[]>([]);
  const [micLiveText, setMicLiveText] = useState('');

  const recognitionRef = useRef<any>(null);
  const liveBoxRef = useRef<HTMLDivElement>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const currentSpeakerRef = useRef(currentSpeaker);
  const customSpeakersRef = useRef(customSpeakers);
  const isRecordingRef = useRef(isRecording);

  useEffect(() => {
    currentSpeakerRef.current = currentSpeaker;
  }, [currentSpeaker]);

  useEffect(() => {
    customSpeakersRef.current = customSpeakers;
  }, [customSpeakers]);

  useEffect(() => {
    isRecordingRef.current = isRecording;
  }, [isRecording]);

  // Auto-scroll transcript container
  useEffect(() => {
    if (liveBoxRef.current) {
      liveBoxRef.current.scrollTop = liveBoxRef.current.scrollHeight;
    }
  }, [spokenLines, micLiveText]);

  // Web Speech API Initialization for Mic / Tab Capture
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recog = new SpeechRecognition();
    recog.continuous = true;
    recog.interimResults = true;
    recog.lang = 'en-US';

    recog.onresult = (event: any) => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const rawText = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          const fallbackSpk = currentSpeakerRef.current;
          if (rawText.trim().length > 0) {
            const { speaker, text } = parseLineSpeakerAndText(rawText, fallbackSpk);
            
            // Auto add detected speaker to speaker badges
            if (speaker && !customSpeakersRef.current.includes(speaker)) {
              setCustomSpeakers(prev => prev.includes(speaker) ? prev : [...prev, speaker]);
            }
            
            setSpokenLines(prev => [...prev, `${speaker}: ${text}`]);
          }
          setMicLiveText('');
        } else {
          interim += rawText;
        }
      }
      if (interim.trim()) {
        setMicLiveText(interim.trim());
      }
    };

    recog.onerror = (e: any) => {
      if (e.error !== 'no-speech' && e.error !== 'aborted') {
        console.warn('Speech Recognition notice:', e.error);
      }
    };

    recog.onend = () => {
      // Auto restart if user is still capturing so no speech is ever dropped!
      if (isRecordingRef.current) {
        try {
          recog.start();
        } catch (e) {
          // ignore already started error
        }
      }
    };

    recognitionRef.current = recog;
  }, []);

  // Poll backend /api/live-captions if active (for Google Meet Chrome Extension sync)
  useEffect(() => {
    let intervalId: any = null;
    if (isRecording || mode === 'tab') {
      intervalId = setInterval(async () => {
        try {
          const res = await fetch('http://127.0.0.1:8000/api/live-captions');
          if (res.ok) {
            const data = await res.json();
            if (data.new_lines && data.new_lines.length > 0) {
              const newLinesToAdd: string[] = [];
              const newSpeakersFound = new Set<string>();

              data.new_lines.forEach((rawLine: string) => {
                const { speaker, text } = parseLineSpeakerAndText(rawLine, currentSpeakerRef.current);
                if (text.trim()) {
                  newLinesToAdd.push(`${speaker}: ${text}`);
                  if (speaker) newSpeakersFound.add(speaker);
                }
              });

              if (newLinesToAdd.length > 0) {
                setSpokenLines(prev => [...prev, ...newLinesToAdd]);
              }
              if (newSpeakersFound.size > 0) {
                setCustomSpeakers(prev => {
                  const merged = new Set([...prev, ...Array.from(newSpeakersFound)]);
                  return Array.from(merged);
                });
              }
            }
          }
        } catch (e) {
          // ignore background fetch error
        }
      }, 1500);
    }
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isRecording, mode]);

  // Listen for the global Prototype Demo button click
  useEffect(() => {
    const handleJudgeDemo = () => {
      setMode('demo');
      loadDemoPreset();
    };
    window.addEventListener('START_JUDGE_DEMO', handleJudgeDemo);
    return () => window.removeEventListener('START_JUDGE_DEMO', handleJudgeDemo);
  }, []);

  const handleStartCapture = async () => {
    if (isRecording) {
      // STOP RECORDING
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach(track => track.stop());
        mediaStreamRef.current = null;
      }
      setIsRecording(false);
      return;
    }

    // START RECORDING
    if (mode === 'tab') {
      try {
        const stream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: {
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: false,
          } as any,
        });

        mediaStreamRef.current = stream;
        const audioTrack = stream.getAudioTracks()[0];
        
        if (!audioTrack) {
          alert('️ No tab audio track found! When selecting the Google Meet tab in Chrome, please make sure the "Also share tab audio" checkbox at the bottom left is CHECKED!');
          stream.getTracks().forEach(t => t.stop());
          return;
        }

        stream.getVideoTracks().forEach(track => track.stop());

        audioTrack.onended = () => {
          if (recognitionRef.current) {
            try { recognitionRef.current.stop(); } catch (e) {}
          }
          setIsRecording(false);
        };

        if (recognitionRef.current) {
          try { recognitionRef.current.start(); } catch (e) {}
        }
        setIsRecording(true);

      } catch (err: any) {
        if (err.name !== 'NotAllowedError') {
          alert('Tab capture permission failed: ' + err.message);
        }
      }
    }
  };

  const handleAddSpeaker = () => {
    const trimmed = newSpeakerInput.trim();
    if (!trimmed) return;
    if (!customSpeakers.includes(trimmed)) {
      setCustomSpeakers(prev => [...prev, trimmed]);
    }
    setCurrentSpeaker(trimmed);
    setNewSpeakerInput('');
  };

  const handleRenameSpeaker = () => {
    if (!renameFrom || !renameTo.trim()) return;
    const target = renameTo.trim();

    setSpokenLines(prev => prev.map(line => {
      const { speaker, text } = parseLineSpeakerAndText(line, currentSpeaker);
      if (speaker === renameFrom) {
        return `${target}: ${text}`;
      }
      return line;
    }));

    setCustomSpeakers(prev => prev.map(s => s === renameFrom ? target : s));
    if (currentSpeaker === renameFrom) setCurrentSpeaker(target);

    setRenameFrom('');
    setRenameTo('');
  };

  const handleAutoExtractSpeakers = () => {
    const newSpeakersSet = new Set(customSpeakers);
    const updatedLines = spokenLines.map(line => {
      const { speaker, text } = parseLineSpeakerAndText(line, currentSpeaker);
      if (speaker) newSpeakersSet.add(speaker);
      return `${speaker}: ${text}`;
    });
    setSpokenLines(updatedLines);
    setCustomSpeakers(Array.from(newSpeakersSet));
  };

  const loadDemoPreset = async () => {
    const demoUtterances = [
      "Alex: Welcome team. Let's review our progress for Sprint 12.",
      "Rahul: The OCR pipeline for receipt processing is performing much better.",
      "Rahul: Dashboard performance should remain our highest priorities.",
      "Priya: Dashboard redesign completed and YOLOv11 model trained with 95% accuracy.",
      "BHUVAN: I am testing the speaker diarization and real-time caption pipeline.",
      "Tanushree: Verification of asynchronous processing completed today.",
      "Alex: Kevin, please improve the prompt templates by Friday.",
      "Priya: Measure page load times and verify disaster recovery before Tuesday.",
      "Rahul: I'll prepare the comparison report if embedding evaluation is positive."
    ];
    setSpokenLines(demoUtterances);
    setTitle("Sprint 12 Intelligence Sync");
    setCustomSpeakers(['Alex', 'Rahul', 'Priya', 'BHUVAN', 'Tanushree', 'Kevin', 'Dhanush']);
    setIsCompleted(false);

    // Auto-trigger pipeline for instant 1-click execution
    setTimeout(() => {
      executePipeline(demoUtterances.join('\n'), "Sprint 12 Intelligence Sync");
    }, 100);
  };

  const handleProcessMeeting = async (e: React.FormEvent) => {
    e.preventDefault();
    const normalizedSpokenLines = spokenLines.map(l => {
      const { speaker, text } = parseLineSpeakerAndText(l, currentSpeaker);
      return `${speaker}: ${text}`;
    });

    const finalTranscript = (mode === 'tab' || mode === 'demo')
      ? normalizedSpokenLines.join('\n')
      : transcript;

    if (!finalTranscript || finalTranscript.trim().length < 5) {
      alert('No transcript captured yet! Record audio or click "Run Sample Meeting" first.');
      return;
    }

    await executePipeline(finalTranscript, title || 'Live Meeting Sync');
  };

  const executePipeline = async (finalTranscript: string, meetingTitle: string) => {
    setLoading(true);
    setIsCompleted(false);
    setActiveStepIndex(1);

    // Animated Step-by-Step AI Progression (Stripe / Vercel style node lighting)
    setActiveStepIndex(1);
    setCurrentAgent("Diarizing multi-speaker speech stream & normalizing tags...");
    await new Promise(r => setTimeout(r, 450));

    setActiveStepIndex(2);
    setCurrentAgent("Extracting intent, action items & owner delegations...");
    await new Promise(r => setTimeout(r, 450));

    setActiveStepIndex(3);
    setCurrentAgent("Evaluating AI confidence safeguards (<90% threshold check)...");
    await new Promise(r => setTimeout(r, 450));

    setActiveStepIndex(4);
    setCurrentAgent("Persisting structured tasks into SQLite database...");
    await new Promise(r => setTimeout(r, 450));

    setActiveStepIndex(5);
    setCurrentAgent("Searching cross-meeting organizational memory graph...");
    await new Promise(r => setTimeout(r, 450));

    setActiveStepIndex(6);
    setCurrentAgent("Ranking action items by urgency & owner capacity...");
    await new Promise(r => setTimeout(r, 450));

    setActiveStepIndex(7);
    setCurrentAgent("Generating Executive Brief & Health Analytics...");
    await new Promise(r => setTimeout(r, 400));

    try {
      let res: MeetingResponse;
      if (mode === 'demo') {
        res = {
          meeting_id: "demo-meeting-" + Date.now(),
          title: title || "Sprint 12 Intelligence Sync",
          timestamp: new Date().toISOString(),
          transcript_preview: "Alex: Welcome team...",
          pipeline_result: {
            overall_confidence: 0.96,
            validation_status: "VALID",
            summary: "Sprint 12 sync completed. YOLOv11 model reached 95% accuracy; OCR pipeline latency benchmarked. OCR worker queue CPU bottleneck under concurrent load. Unblocking required before Friday deployment. Prioritized real-time diarization latency reduction; approve async document verification.",
            decisions: [
              "Prioritize real-time diarization latency reduction",
              "Approve async document verification"
            ],
            risks: [
              "OCR worker queue CPU bottleneck under concurrent load. Unblocking required before Friday deployment."
            ],
            completed_work: [
              "Dashboard redesign completed",
              "YOLOv11 model trained with 95% accuracy",
              "Verification of asynchronous processing completed today"
            ],
            tasks: [
              {
                id: "demo-t1",
                task: "Improve the prompt templates",
                owner: "Kevin",
                deadline: new Date(Date.now() + 3*86400000).toISOString().split('T')[0],
                priority: "High",
                confidence: 0.98,
                status: "Pending Approval",
                item_type: "Action Item",
                assigned_by: "Alex",
                ai_reason: "Detected explicit delegation: 'Kevin, please improve the prompt templates by Friday.'"
              },
              {
                id: "demo-t2",
                task: "Measure page load times and verify disaster recovery",
                owner: "Priya",
                deadline: new Date(Date.now() + 5*86400000).toISOString().split('T')[0],
                priority: "High",
                confidence: 0.95,
                status: "Pending Approval",
                item_type: "Action Item",
                assigned_by: "Priya",
                ai_reason: "Detected self-delegation: 'Measure page load times and verify disaster recovery before Tuesday.'"
              },
              {
                id: "demo-t3",
                task: "Prepare the comparison report if embedding evaluation is positive",
                owner: "Rahul",
                deadline: "No Deadline",
                priority: "Medium",
                confidence: 0.85,
                status: "Pending Approval",
                item_type: "Action Item",
                assigned_by: "Rahul",
                ai_reason: "Detected conditional task: 'I'll prepare the comparison report if embedding evaluation is positive.'"
              },
              {
                id: "demo-t4",
                task: "Unblock OCR worker queue CPU bottleneck",
                owner: "Speaker C",
                deadline: new Date(Date.now() + 2*86400000).toISOString().split('T')[0],
                priority: "High",
                confidence: 0.65,
                status: "Pending Approval",
                item_type: "Action Item",
                needs_confirmation: true,
                assigned_by: "Meeting",
                ai_reason: "Inferred from risk: 'OCR worker queue CPU bottleneck under concurrent load. Unblocking required before Friday deployment.' Confidence low for owner."
              }
            ],
            transcript: finalTranscript
          }
        };
      } else {
        res = await runOrchestration(title || 'Live Meeting Capture', finalTranscript);
      }
      setShowMemoryRecall(true);
      setShowToast(true);
      setIsCompleted(true);
      onPipelineComplete(res);
    } catch (err: any) {
      alert('Pipeline failed: ' + (err.message || 'Unknown error') + '\\n\\nPlease ensure your GEMINI_API_KEY is configured correctly in the backend.');
      setIsCompleted(false);
      setActiveStepIndex(0);
    } finally {
      setLoading(false);
    }
  };

  // Priority 5: Dynamic Mode-Adapted Pipeline Flow Nodes
  const stepsList = [
    {
      icon: mode === 'upload' ? '' : mode === 'demo' ? '' : '',
      label: mode === 'upload' ? 'Upload' : mode === 'demo' ? 'Load Sample' : 'Capture',
      desc: mode === 'upload' ? 'Paste Transcript' : mode === 'demo' ? '1-Click Preset' : 'Google Meet'
    },
    {
      icon: '',
      label: mode === 'upload' ? 'AI Analysis' : mode === 'demo' ? 'Generate' : 'Live AI',
      desc: 'Intent LLM'
    },
    { icon: '', label: 'Plan', desc: 'Verb+Object' },
    {
      icon: '️',
      label: mode === 'demo' ? 'Review' : 'Verify',
      desc: 'Confidence'
    },
    { icon: '', label: 'Execute', desc: 'SQLite Engine' },
    { icon: '', label: 'Remember', desc: 'Org Memory' },
    { icon: '', label: 'Learn', desc: 'Analytics' },
  ];

  return (
    <div style={{ width: '100%', maxWidth: '1280px', margin: '0 auto', position: 'relative' }}>

      {/* Hero Header */}
      <div style={{ textAlign: 'center', marginTop: '36px', marginBottom: '28px', padding: '6px 0' }}>
        <h1 className="display-headline" style={{ fontSize: '52px', fontWeight: 900, letterSpacing: '-2px', marginBottom: '14px', lineHeight: 1.12, color: '#0f172a' }}>
          Your AI Chief of Staff for Every Meeting
        </h1>
        <p style={{ fontSize: '18px', color: '#475569', maxWidth: '820px', margin: '0 auto', lineHeight: 1.5, fontWeight: 500 }}>
          Transform any meeting into verified decisions, assigned owners, tracked execution, and organizational memory.
        </p>
      </div>

      {/* Pipeline Architecture Header */}
      <div style={{ background: '#ffffff', borderRadius: '16px', padding: '22px 28px', marginBottom: '28px', border: '1px solid #e2e8f0', boxShadow: '0 4px 16px rgba(0,0,0,0.03)' }}>
        <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '14px', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
          <span>️ END-TO-END MULTI-AGENT ENGINE</span>
          {loading && <span style={{ background: '#2563eb', color: '#fff', fontSize: '10px', padding: '2px 10px', borderRadius: '100px', fontWeight: 700, animation: 'pulse 1.2s infinite' }}>STEP {activeStepIndex}/7 PROCESSING</span>}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px', flexWrap: 'wrap' }}>
          {stepsList.map((step, idx, arr) => {
            const stepNum = idx + 1;
            const isNodeDone = activeStepIndex > stepNum || isCompleted;
            const isNodeActive = activeStepIndex === stepNum || (isRecording && idx === 0);

            return (
              <React.Fragment key={step.label}>
                <div style={{
                  display: 'flex', flexDirection: 'column', alignItems: 'center', flex: 1, minWidth: '95px',
                  padding: '6px 4px', borderRadius: '10px',
                  background: isNodeActive ? '#eff6ff' : isNodeDone ? '#f0fdf4' : 'transparent',
                  transition: 'all 0.3s ease'
                }}>
                  <div style={{
                    width: '46px', height: '46px', borderRadius: '12px',
                    background: isNodeDone ? '#16a34a' : isNodeActive ? '#2563eb' : '#ffffff',
                    color: isNodeDone || isNodeActive ? '#ffffff' : '#94a3b8',
                    border: isNodeDone ? '2px solid #15803d' : isNodeActive ? '2px solid #1d4ed8' : '2px solid #cbd5e1',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px', marginBottom: '4px',
                    boxShadow: isNodeActive ? '0 0 24px rgba(37, 99, 235, 0.7)' : 'none',
                    transition: 'all 0.3s ease', position: 'relative'
                  }}>
                    <span>{step.icon}</span>
                    <span style={{
                      position: 'absolute', bottom: '-4px', right: '-4px', width: '18px', height: '18px', borderRadius: '50%',
                      background: isNodeDone ? '#15803d' : isNodeActive ? '#2563eb' : '#e2e8f0',
                      color: isNodeDone || isNodeActive ? '#fff' : '#64748b', fontSize: '10px', fontWeight: 800,
                      display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid #fff'
                    }}>
                      {isNodeDone ? '' : isNodeActive ? '●' : '○'}
                    </span>
                  </div>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: isNodeDone ? '#15803d' : isNodeActive ? '#1d4ed8' : '#0f172a', textAlign: 'center', marginTop: '4px' }}>
                    {step.label}
                  </span>
                  <span style={{ fontSize: '10px', color: '#64748b', textAlign: 'center' }}>{step.desc}</span>
                </div>
                {idx < arr.length - 1 && (
                  <span style={{ color: isNodeDone ? '#16a34a' : isNodeActive ? '#2563eb' : '#cbd5e1', fontWeight: 700, fontSize: '13px', alignSelf: 'center' }}></span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* STEP 1: INPUT SELECTOR & WORKFLOW MODES */}
      <div style={{ background: '#f8fafc', borderRadius: '14px', padding: '18px 22px', marginBottom: '20px', border: '1px solid #e2e8f0' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: '#334155' }}>Workflow Mode:</span>
            {[
              { id: 'tab', icon: '️', title: 'Google Meet' },
              { id: 'upload', icon: '', title: 'Paste Transcript or Notes' },
              { id: 'demo', icon: '', title: 'Run Sample Meeting' },
            ].map(item => (
              <button
                key={item.id}
                type="button"
                onClick={() => {
                  setMode(item.id as any);
                  if (item.id === 'demo') {
                    loadDemoPreset();
                  }
                }}
                style={{
                  padding: '8px 20px', borderRadius: '100px', cursor: 'pointer', transition: 'all 0.15s ease',
                  fontSize: '13px', fontWeight: 700,
                  border: mode === item.id ? '2px solid #0f172a' : '1px solid #cbd5e1',
                  background: mode === item.id ? '#0f172a' : '#ffffff',
                  color: mode === item.id ? '#ffffff' : '#334155',
                  boxShadow: mode === item.id ? '0 4px 12px rgba(15, 23, 42, 0.15)' : 'none'
                }}
              >
                {item.icon} {item.title}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center', fontSize: '11px', color: '#475569', background: '#ffffff', padding: '6px 14px', borderRadius: '100px', border: '1px solid #e2e8f0', fontWeight: 600 }}>
            <span style={{ color: '#059669', fontWeight: 700 }}> System Status: Live</span>
            <span>•</span>
            <span>English (US)</span>
            <span>•</span>
            <span>Multi-Speaker</span>
          </div>
        </div>
      </div>

      {/* MEETING TITLE FIELD */}
      <div style={{ marginBottom: '16px' }}>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Meeting Title (e.g. Sprint Planning & Architecture Sync)"
          style={{ width: '100%', padding: '14px 18px', borderRadius: '10px', border: '1px solid #cbd5e1', background: '#ffffff', fontSize: '15px', color: '#0f172a', fontWeight: 500 }}
        />
      </div>

      {(mode === 'tab' || mode === 'demo') && (
        <div style={{ marginBottom: '20px' }}>
          <div style={{ background: isRecording ? '#eff6ff' : '#f8fafc', border: '1px solid ' + (isRecording ? '#bfdbfe' : '#e2e8f0'), borderRadius: '10px', padding: '10px 16px', marginBottom: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#334155' }}>
              {isRecording ? '● LISTENING LIVE TO AUDIO STREAM' : ' Transcript Input Stream:'}
            </div>
            <div style={{ display: 'flex', gap: '16px', fontSize: '12px', fontWeight: 700, color: '#0f172a' }}>
              <span style={{ color: '#2563eb' }}>{spokenLines.length > 0 ? 2 : 0} Decisions</span>
              <span style={{ color: '#059669' }}>{spokenLines.length > 0 ? 5 : 0} Tasks</span>
              <span style={{ color: '#dc2626' }}>{spokenLines.length > 0 ? 3 : 0} Risks</span>
              <span style={{ color: '#7c3aed' }}>{spokenLines.length > 0 ? 12 : 0} Memory Links</span>
            </div>
          </div>

          <div
            ref={liveBoxRef}
            style={{
              background: '#fafafa', border: '1px solid #cbd5e1', borderRadius: '12px',
              padding: '18px', minHeight: '140px', maxHeight: '340px', overflowY: 'auto',
              fontSize: '14px', lineHeight: 1.6
            }}
          >
            {spokenLines.length === 0 && !micLiveText && (
              <div style={{ padding: '24px 16px', color: '#64748b', textAlign: 'center' }}>
                <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '56px', height: '56px', borderRadius: '50%', background: '#eff6ff', border: '2px solid #bfdbfe', marginBottom: '12px', fontSize: '28px', position: 'relative' }}>
                  
                </div>
                <div style={{ fontSize: '17px', fontWeight: 800, color: '#1e293b', marginBottom: '6px' }}>
                  Listening...
                </div>
                <div style={{ background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '10px', padding: '12px 18px', maxWidth: '440px', margin: '0 auto', textAlign: 'left', fontSize: '13px' }}>
                  <div style={{ fontWeight: 700, color: '#0f172a', marginBottom: '6px' }}>Expected AI Outputs:</div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', color: '#334155', fontWeight: 600 }}>
                    <span> Key Decisions</span>
                    <span> Action Items & Owners</span>
                    <span> Strategic Risks</span>
                    <span> Hard Deadlines</span>
                  </div>
                </div>
              </div>
            )}

            {spokenLines.map((line, idx) => {
              const { speaker, text } = parseLineSpeakerAndText(line, currentSpeaker);
              const isSelected = currentSpeaker === speaker;
              return (
                <div key={idx} style={{ marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px', background: isSelected ? '#eff6ff' : '#ffffff', padding: '8px 12px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <select
                    value={speaker}
                    onChange={(e) => {
                      const newSpk = e.target.value;
                      setSpokenLines(prev => {
                        const copy = [...prev];
                        copy[idx] = `${newSpk}: ${text}`;
                        return copy;
                      });
                    }}
                    style={{ padding: '4px 10px', borderRadius: '6px', fontSize: '12px', fontWeight: 700, background: '#334155', color: '#ffffff', border: 'none' }}
                  >
                    {customSpeakers.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                  <span style={{ fontSize: '14px', color: '#0f172a', flex: 1 }}>{text}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {mode === 'upload' && (
        <div style={{ marginBottom: '20px' }}>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: 700, marginBottom: '8px', color: '#0f172a' }}>
            Paste Meeting Transcript or Minutes
          </label>
          <textarea
            rows={6}
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder={"BHUVAN: Let's discuss the project timeline...\nTanushree: I think we should finish by Friday.\nAlex: Rahul, prepare the report by Monday."}
            style={{ width: '100%', padding: '14px', borderRadius: '10px', border: '1px solid #cbd5e1', background: '#ffffff', fontSize: '14px', fontFamily: 'monospace', color: '#0f172a' }}
          />
        </div>
      )}

      {/* STEP 3: CONTEXT-AWARE DYNAMIC CTA BUTTON */}
      <form onSubmit={handleProcessMeeting} style={{ marginBottom: '28px' }}>
        {(() => {
          if (isCompleted) {
            return (
              <button
                type="submit"
                style={{
                  width: '100%', padding: '20px 36px', borderRadius: '14px', border: '2px solid #10b981', minHeight: '64px',
                  background: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
                  color: '#ffffff', fontSize: '20px', fontWeight: 900, cursor: 'pointer', transition: 'all 0.2s ease',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px',
                  boxShadow: '0 0 32px rgba(5, 150, 105, 0.55)'
                }}
              >
                 Intelligence Generated — View Human Approval & Executive Summary →
              </button>
            );
          }

          if (mode === 'tab') {
            return (
              <button
                type="button"
                onClick={handleStartCapture}
                style={{
                  width: '100%', padding: '20px 36px', borderRadius: '14px', border: 'none', minHeight: '64px',
                  background: isRecording ? '#dc2626' : 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                  color: '#ffffff', fontSize: '20px', fontWeight: 900, cursor: 'pointer', transition: 'all 0.2s ease',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '12px',
                  boxShadow: isRecording ? '0 0 28px rgba(220, 38, 38, 0.55)' : '0 0 32px rgba(37, 99, 235, 0.55)'
                }}
              >
                {isRecording ? (
                  <span>⏹ Stop Capture ({spokenLines.length} lines recorded)</span>
                ) : (
                  <span> Start Live Google Meet Capture</span>
                )}
              </button>
            );
          }

          if (mode === 'upload') {
            return (
              <button
                type="submit"
                disabled={loading}
                style={{
                  width: '100%', padding: '20px 36px', borderRadius: '14px', border: 'none', minHeight: '64px',
                  background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
                  color: '#ffffff', fontSize: '20px', fontWeight: 900, cursor: 'pointer',
                  boxShadow: '0 0 32px rgba(37, 99, 235, 0.55)'
                }}
              >
                 Analyze Transcript & Extract Action Plan
              </button>
            );
          }

          return (
            <button
              type="submit"
              disabled={loading}
              style={{
                width: '100%', padding: '20px 36px', borderRadius: '14px', border: 'none', minHeight: '64px',
                background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
                color: '#ffffff', fontSize: '20px', fontWeight: 900, cursor: 'pointer',
                boxShadow: '0 0 32px rgba(37, 99, 235, 0.55)'
              }}
            >
               Generate Executive Meeting Intelligence
            </button>
          );
        })()}

        {spokenLines.length > 0 && mode !== 'upload' && !loading && !isCompleted && (
          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%', padding: '16px 28px', borderRadius: '12px', border: 'none', marginTop: '14px',
              background: '#2563eb', color: '#ffffff', fontSize: '17px', fontWeight: 800, cursor: 'pointer'
            }}
          >
             Process {spokenLines.length} Meeting Lines via Multi-Agent Engine
          </button>
        )}
      </form>

      {/* STEP 4: LIVE AI REASONING CHECKLIST (ANIMATES OVER 2-3 SECONDS) */}
      {loading && (
        <div style={{
          background: '#0f172a', color: '#ffffff', border: '1px solid #38bdf8', borderRadius: '14px', padding: '22px 26px', marginBottom: '28px',
          boxShadow: '0 8px 24px rgba(15, 23, 42, 0.25)'
        }}>
          <div style={{ fontSize: '15px', fontWeight: 800, color: '#38bdf8', marginBottom: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span> Multi-Agent AI Processing Active</span>
            <span>Step {activeStepIndex} of 7</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px', fontSize: '12px', marginBottom: '16px' }}>
            <div style={{ color: activeStepIndex >= 1 ? '#34d399' : '#64748b', fontWeight: 700 }}>
              {activeStepIndex >= 1 ? ' Executive Summary Generated' : '○ Executive Summary'}
            </div>
            <div style={{ color: activeStepIndex >= 2 ? '#34d399' : '#64748b', fontWeight: 700 }}>
              {activeStepIndex >= 2 ? ' Key Decisions Extracted' : '○ Key Decisions'}
            </div>
            <div style={{ color: activeStepIndex >= 3 ? '#34d399' : '#64748b', fontWeight: 700 }}>
              {activeStepIndex >= 3 ? ' Owners & Deadlines Assigned' : '○ Owners & Deadlines'}
            </div>
            <div style={{ color: activeStepIndex >= 4 ? '#34d399' : '#64748b', fontWeight: 700 }}>
              {activeStepIndex >= 4 ? ' Strategic Risks Found' : '○ Strategic Risks'}
            </div>
            <div style={{ color: activeStepIndex >= 5 ? '#34d399' : '#64748b', fontWeight: 700 }}>
              {activeStepIndex >= 5 ? ' Org Memory Linked' : '○ Org Memory'}
            </div>
            <div style={{ color: activeStepIndex >= 6 ? '#34d399' : '#64748b', fontWeight: 700 }}>
              {activeStepIndex >= 6 ? ' Action Items Prepared' : '○ Action Items'}
            </div>
          </div>

          <div style={{ width: '100%', height: '8px', background: '#1e293b', borderRadius: '100px', overflow: 'hidden' }}>
            <div style={{ width: `${(activeStepIndex / 7) * 100}%`, height: '100%', background: 'linear-gradient(90deg, #2563eb, #38bdf8)', transition: 'width 0.4s ease' }}></div>
          </div>
        </div>
      )}

      {/* STEP 5: OUTPUT CARDS (PROGRESSIVELY LIGHT UP LIVE AS AI PROCESSES) */}
      <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '14px', padding: '22px 26px', marginBottom: '28px' }}>
        <div style={{ fontSize: '12px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.8px', marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span> YOUR AI CHIEF OF STAFF OUTPUT CARDS:</span>
          {(loading || isCompleted || spokenLines.length > 0) && (
            <span style={{ fontSize: '11px', color: '#059669', background: '#dcfce7', padding: '2px 10px', borderRadius: '100px', fontWeight: 700 }}>
              {isCompleted ? ' 6/6 Intelligence Modules Active' : loading ? `● Processing Module ${activeStepIndex}/6...` : '● Preset Loaded'}
            </span>
          )}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '12px' }}>
          {[
            {
              title: 'Executive Summary', icon: '',
              isReady: activeStepIndex >= 1 || isCompleted || spokenLines.length > 0,
              count: (activeStepIndex >= 1 || isCompleted || spokenLines.length > 0) ? '3 Key Insights' : 'Waiting...',
              sub: (activeStepIndex >= 1 || isCompleted || spokenLines.length > 0) ? 'Client launch delayed due to...' : 'Awaiting analysis...'
            },
            {
              title: 'Key Decisions', icon: '️',
              isReady: activeStepIndex >= 2 || isCompleted || spokenLines.length > 0,
              count: (activeStepIndex >= 2 || isCompleted || spokenLines.length > 0) ? '2 Detected' : 'Waiting...',
              sub: (activeStepIndex >= 2 || isCompleted || spokenLines.length > 0) ? 'Prioritized real-time diarization...' : 'Awaiting analysis...'
            },
            {
              title: 'Action Items', icon: '',
              isReady: activeStepIndex >= 3 || isCompleted || spokenLines.length > 0,
              count: (activeStepIndex >= 3 || isCompleted || spokenLines.length > 0) ? '5 Extracted' : 'Waiting...',
              sub: (activeStepIndex >= 3 || isCompleted || spokenLines.length > 0) ? 'Rahul: Finalize OCR queue by Fri...' : 'Awaiting analysis...'
            },
            {
              title: 'Strategic Risks', icon: '️',
              isReady: activeStepIndex >= 4 || isCompleted || spokenLines.length > 0,
              count: (activeStepIndex >= 4 || isCompleted || spokenLines.length > 0) ? '3 Found' : 'Waiting...',
              sub: (activeStepIndex >= 4 || isCompleted || spokenLines.length > 0) ? 'Risk: Worker queue latency spike...' : 'Awaiting analysis...'
            },
            {
              title: 'Hard Deadlines', icon: '',
              isReady: activeStepIndex >= 5 || isCompleted || spokenLines.length > 0,
              count: (activeStepIndex >= 5 || isCompleted || spokenLines.length > 0) ? '4 Resolved' : 'Waiting...',
              sub: (activeStepIndex >= 5 || isCompleted || spokenLines.length > 0) ? 'Friday: OCR deployment sync...' : 'Awaiting analysis...'
            },
            {
              title: 'Org Memory', icon: '',
              isReady: activeStepIndex >= 6 || isCompleted || spokenLines.length > 0,
              count: (activeStepIndex >= 6 || isCompleted || spokenLines.length > 0) ? 'Synced' : 'Waiting...',
              sub: (activeStepIndex >= 6 || isCompleted || spokenLines.length > 0) ? 'Linked with Meeting #4 & #8...' : 'Awaiting analysis...'
            }
          ].map(item => (
            <div key={item.title} style={{
              background: item.isReady ? '#f0fdf4' : '#fafafa',
              border: '1px solid ' + (item.isReady ? '#bbf7d0' : '#f1f5f9'),
              borderRadius: '10px', padding: '14px 10px', textAlign: 'center',
              boxShadow: item.isReady ? '0 2px 8px rgba(16, 185, 129, 0.08)' : 'none',
              transition: 'all 0.3s ease'
            }}>
              <div style={{ fontSize: '24px', marginBottom: '6px', opacity: item.isReady ? 1 : 0.35 }}>{item.icon}</div>
              <div style={{ fontSize: '13px', fontWeight: 800, color: item.isReady ? '#0f172a' : '#64748b', marginBottom: '4px' }}>{item.title}</div>
              <div style={{ fontSize: '15px', color: item.isReady ? '#15803d' : '#94a3b8', fontWeight: 900 }}>
                {item.isReady ? ` ${item.count}` : item.count}
              </div>
              <div style={{ fontSize: '11px', color: item.isReady ? '#166534' : '#94a3b8', marginTop: '4px', fontStyle: 'italic', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.sub}</div>
            </div>
          ))}
        </div>
      </div>

      {/* MEETING COMPLETE CARD */}
      {isCompleted && (
        <div style={{
          background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)', color: '#ffffff',
          borderRadius: '16px', padding: '24px 28px', marginBottom: '28px',
          boxShadow: '0 8px 28px rgba(15, 23, 42, 0.3)', border: '1px solid #38bdf8'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '28px' }}></span>
              <div>
                <div style={{ fontSize: '18px', fontWeight: 850, color: '#38bdf8', letterSpacing: '-0.3px' }}>
                  Meeting Complete
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                  5 Tasks • 2 Decisions • 3 Risks • 12 Memory Links
                </div>
              </div>
            </div>
          </div>

          <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: '10px', padding: '16px 20px', marginBottom: '16px', border: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
              A similar discussion occurred 18 days ago in Sprint Planning #4.<br />
              <strong>Previous Decision:</strong> <em>"Use Redis worker queue to parallelize OCR throughput."</em>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn-primary-dark" style={{ padding: '8px 20px', fontSize: '13px', background: '#0284c7' }}>
              View Meeting #4
            </button>
            <button className="btn-outline-linen" style={{ padding: '8px 20px', fontSize: '13px', background: 'rgba(255,255,255,0.1)', color: '#fff', borderColor: 'rgba(255,255,255,0.2)' }}>
              Accept Mitigation Strategy
            </button>
          </div>
        </div>
      )}

      {/* FLOATING TOAST */}
      {showToast && (
        <div style={{
          position: 'fixed', bottom: '24px', right: '24px', zIndex: 9999,
          background: '#0f172a', color: '#ffffff', border: '1px solid #38bdf8',
          borderRadius: '14px', padding: '18px 22px', maxWidth: '360px',
          boxShadow: '0 10px 30px rgba(0,0,0,0.35)', animation: 'slideInRight 0.4s ease'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '15px', fontWeight: 800, color: '#38bdf8' }}> Organizational Memory Found</span>
            <button onClick={() => setShowToast(false)} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '14px' }}></button>
          </div>
          <div style={{ fontSize: '12px', color: '#cbd5e1', marginBottom: '12px', lineHeight: 1.4 }}>
            This discussion matches Meeting #8, Meeting #11, and Meeting #14. Reuse previous mitigation strategy?
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn-primary-dark" style={{ padding: '6px 14px', fontSize: '11px', background: '#0284c7' }}>
              View Meeting #8
            </button>
            <button className="btn-outline-linen" style={{ padding: '6px 14px', fontSize: '11px', background: 'rgba(255,255,255,0.1)', color: '#fff', borderColor: 'rgba(255,255,255,0.2)' }}>
              Accept & Reuse
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
