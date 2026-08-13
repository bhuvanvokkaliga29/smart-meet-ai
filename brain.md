# SmartMeet AI — Brain Documentation (Single Source of Truth)

## Project Purpose
SmartMeet AI is an enterprise multi-agent meeting intelligence and execution platform. It transforms raw meeting audio—captured via browser extension, audio/video upload, or platform APIs—into structured, verified, and trackable action plans. Unlike passive meeting summarizers, SmartMeet AI enforces human-in-the-loop validation, monitors cross-meeting task continuity, detects altered decisions, and automates task follow-ups until completion.

---

## High-Level Architecture
The system consists of three main sub-systems:
1. **Capture Interface**:
   - **Chrome Extension (Manifest V3)**: Captures tab audio streams (Google Meet / Zoom) directly via Web Audio API.
   - **Live Microphone Voice Recorder Engine**: Direct browser Web Speech API capturing microphone speech real-time with speaker labeling.
   - **Live Transcription Stream Engine**: Real-time line-by-line speaker transcription & diarization streaming in the web dashboard UI.
   - **Frontend Web Dashboard**: Supports manual audio/video uploads and pre-loaded mock meeting triggers.
2. **Multi-Agent Backend Pipeline (FastAPI / Python)**:
   - **Speech Agent**: Speech-to-text conversion & diarization.
   - **Summary Agent**: Executive meeting summary & decision extraction.
   - **Action-Item Agent**: Scans transcript for actionable tasks.
   - **Owner Agent**: Assigns task responsibility based on speaker tags & organizational context.
   - **Deadline Agent**: Resolves relative dates ("by Friday") into strict ISO date formats.
   - **Priority Agent**: Assesses task urgency (High / Medium / Low).
   - **Validation Agent**: Computes AI confidence scores and flags tasks for Human-in-the-Loop review (`VALID` vs `REVIEW`).
   - **Cross-Meeting Agent**: Reconciles new tasks against historical meeting memory to update existing task statuses (`Completed`, `Blocked`, `Pending`) and prevent duplicates.
   - **SQLite Database Engine (`backend/database.py`)**: Real relational SQL database (`smartmeet.db`) storing `meetings`, `tasks`, and `reminders` with foreign keys and ACID transactions.
3. **Task Management & Execution Dashboard (React + TypeScript)**:
   - **Human Approval Portal**: Interface for users to Approve, Edit, or Reject AI-extracted tasks before database commit.
   - **Kanban Board**: Real-time status tracking (`Pending`, `In Progress`, `Blocked`, `Completed`).
   - **Cross-Meeting Intelligence Hub**: Displays pre-meeting status recaps and decision evolution.
   - **Reminder Scheduler Log**: Automated follow-up notifications.

---

## Folder Responsibilities
```
c:\Users\DHANUSH A G\Documents\innovative/
├── brain.md                 # Single source of truth documentation
├── README.md                # Quickstart and setup guide
├── backend/                 # FastAPI Python backend & multi-agent pipeline
│   ├── main.py              # Application entry point & REST API router
│   ├── database.py          # SQLite DB connection & seed data initializer
│   ├── models.py            # Pydantic schemas for inter-agent communication
│   ├── agents/              # Multi-agent worker modules
│   │   ├── orchestrator.py  # Manager Agent sequencing agent pipeline
│   │   ├── speech_agent.py  # Speech recognition & speaker diarization
│   │   ├── summary_agent.py # Executive summary & key decisions generator
│   │   ├── action_agent.py  # Action item extractor
│   │   ├── owner_agent.py   # Task owner assignment agent
│   │   ├── deadline_agent.py# Due date resolution agent
│   │   ├── priority_agent.py# Urgency classification agent
│   │   ├── validation_agent.py # Schema validation & confidence scorer
│   │   └── cross_meeting_agent.py # Cross-meeting memory & status reconciler
│   └── requirements.txt     # Python dependencies
├── extension/               # Chrome Browser Extension (Manifest V3)
│   ├── manifest.json        # Extension metadata & permission manifest
│   ├── background.js        # Service worker for tab audio capture
│   └── popup/               # Extension popup UI
│       ├── popup.html
│       ├── popup.js
│       └── popup.css
└── frontend/                # React + Vite TypeScript Dashboard
    ├── package.json
    ├── index.html
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx          # Main application layout & state orchestrator
    │   ├── components/      # UI components
    │   │   ├── Header.tsx   # Header bar & stat counters
    │   │   ├── MeetingUpload.tsx # Capture & audio upload panel
    │   │   ├── HumanApprovalModal.tsx # Human-in-the-Loop review modal
    │   │   ├── TaskBoard.tsx # Kanban task management board
    │   │   ├── CrossMeetingIntelligence.tsx # Meeting memory & recap view
    │   │   └── AnalyticsPanel.tsx # Productivity charts & reminder logs
    │   └── services/        # API client services
    │       └── api.ts
```

---

## Technology Stack
- **Design System Aesthetic**: Memorisely Typographer Workspace — Warm Parchment canvas (`#faf9f6`), Paper White cards (`#ffffff`), Warm Linen borders (`#f2f0e9`), Ink Black typography (`#171717`), Inter font with tight display tracking (`-3.36px`), and floating pill navigation.
- **Frontend Framework**: React 18 (TypeScript, Vite)
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic v2 (Deployed on **Google Cloud Run**)
- **Database Engine**: Relational PostgreSQL + pgvector (with **BigQuery** for long-term analytics)
- **AI Models**: **Gemini 1.5 Pro** for reasoning, **Gemini 1.5 Flash** for high-speed classification, and **Gemma 2 (9B/27B) via vLLM** for local inference fallback (Managed via **Vertex AI Model Garden** and **Google AI Studio**).
- **Browser Extension**: Chrome Extension Manifest V3 (`chrome.tabCapture` API)
- **Agent Framework**: **Agent Development Kit (ADK)** with **Antigravity** for state management and orchestration.
- **Agent Communication**: **Agent-to-Agent (A2A)** protocol for inter-agent communication, and **Model Context Protocol (MCP)** for external system integrations (Jira/Slack).
- **Enterprise Utilities**: CSV & JSON Report Exporters, RAG Memory Search Modal (⌘K), Celery Scheduler Logs, Slack Webhooks.

---

## Execution Flow
1. **Ingestion**:
   - Audio is captured live via Chrome Extension or uploaded via Web UI.
2. **Transcription**:
   - `SpeechAgent` converts audio into JSON transcript with speaker labels (`Rahul`, `Priya`, etc.) and diarization confidence.
3. **Parallel Agent Extraction**:
   - `SummaryAgent` processes transcript -> extracts executive summary and key decisions.
   - `ActionAgent` processes transcript -> extracts raw task phrases.
4. **Task Enrichment**:
   - `OwnerAgent` assigns owners to raw tasks.
   - `DeadlineAgent` resolves explicit & relative dates.
   - `PriorityAgent` sets urgency scores.
5. **Validation**:
   - `ValidationAgent` computes overall confidence (0-100%) and sets status (`VALID` or `REVIEW`).
6. **Cross-Meeting Reconciliation**:
   - `CrossMeetingAgent` compares extracted tasks against past database tasks to update existing task states (`Completed`, `Blocked`, `Pending`) or mark duplicates.
7. **Human-in-the-Loop Review**:
   - Tasks are held in pending approval stage in the UI. User can Approve, Edit fields, or Reject tasks.
8. **Commit & Action**:
   - Approved tasks commit to the database, trigger status updates on the Task Board, and schedule automated reminders.

---

## API Contracts

### 1. Ingest Meeting
- `POST /api/upload-meeting`
- **Request**: Multipart Form Data (`file: audio/wav`, `title: string`) or JSON (`transcript: string`, `title: string`)
- **Response**: `{ "meeting_id": "m-101", "status": "processing" }`

### 2. Run Multi-Agent Pipeline
- `POST /api/orchestrate`
- **Request**: `{ "meeting_id": "m-101" }`
- **Response**:
  ```json
  {
    "meeting_id": "m-101",
    "summary": "Team agreed to finalize UI design...",
    "decisions": ["Finalize UI by Friday", "Testing starts Monday"],
    "tasks": [
      {
        "id": "t-1",
        "task": "Finish Login UI",
        "owner": "Rahul",
        "deadline": "2026-07-29",
        "priority": "High",
        "confidence": 95,
        "status": "REVIEW",
        "cross_meeting_note": "Updates open action item from July 20 meeting"
      }
    ]
  }
  ```

### 3. Approve Tasks (Human-in-the-Loop)
- `POST /api/tasks/approve`
- **Request**: `{ "meeting_id": "m-101", "approved_tasks": [...] }`
- **Response**: `{ "status": "success", "committed_count": 2 }`

### 4. Fetch Dashboard Tasks
- `GET /api/tasks`
- **Response**: List of tasks grouped by status (`Pending`, `In Progress`, `Blocked`, `Completed`).

### 5. Fetch Cross-Meeting Memory
- `GET /api/cross-meeting/recap`
- **Response**: Recap JSON summarizing status of tasks across prior meetings.

---

## Security Practices
- HTTPS / TLS for API communications.
- Tab capture consent check in Browser Extension.
- PII redaction capabilities prior to LLM submission.
- Immutable audit log for task status updates.

---

## Maintenance Guidelines
- To add a new agent, create a module under `backend/agents/`, define input/output Pydantic schemas in `models.py`, and register the agent in `orchestrator.py`.
- To update the Chrome extension, modify `extension/manifest.json` or `background.js` and reload in `chrome://extensions`.
