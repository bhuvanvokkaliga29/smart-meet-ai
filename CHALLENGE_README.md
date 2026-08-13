# 24-Hour AI Agent Challenge Submission
## Agent: Meeting Notes to Action Items (Intermediate)

This is a working, end-to-end implementation of the **Meeting Notes to Action Items** agent for the Rooman Technologies Junior AI Research Associate Challenge.

### 🎯 What This Agent Does
> "My agent takes a raw meeting transcript (text) and produces a structured JSON containing a concise summary, key decisions, and assigned action items with deadlines."

---

### 🚀 Setup & Installation (Foolproof Guide)

**1. Clone the repository and navigate to the backend directory:**
```bash
# Ensure you are in the backend directory
cd backend
```

**2. Create a virtual environment and install dependencies:**
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

**3. Configure your API Key:**
This agent uses the `google-genai` SDK. You need a Google Gemini API key.
Create a file named `.env` in the `backend/` directory:
```bash
# backend/.env
GEMINI_API_KEY="your_api_key_here"
```

---

### 🏃 How to Run the Agent (End-to-End Demo)

We have provided three sample meeting transcripts in the `challenge_assets/` folder to demonstrate the agent's capabilities.

Run the evaluation script from the `backend/` directory:
```bash
python run_challenge.py ../challenge_assets/transcript_1_planning.txt
```

**Expected Output:**
The CLI script will feed the raw text to the `MeetingIntelligenceAgent` and print a beautifully structured JSON response containing:
1. `summary`: 1-2 sentence executive summary.
2. `decisions`: A list of explicitly made decisions.
3. `commitments`: (Action Items) With extracted `action`, `owner_candidate`, `deadline_phrase`, and the `evidence_transcript`.
4. `risks` and `completed_work`.

You can also test the other transcripts:
```bash
python run_challenge.py ../challenge_assets/transcript_2_standup.txt
python run_challenge.py ../challenge_assets/transcript_3_postmortem.txt
```

---

### 🧠 Design Choices & Approach

**1. Model Choice: Gemini 2.5 Flash**
We chose `gemini-2.5-flash` primarily for its speed, huge context window (essential for long meeting transcripts), and native support for **Structured Outputs** via Pydantic schemas. 

**2. One-Pass Extraction (Data Extraction vs Map-Reduce)**
Instead of using a multi-agent map-reduce architecture (Agent A summarizes, Agent B finds tasks, Agent C finds owners) which can be slow and expensive, we opted for a single-pass extraction. We pass a strongly typed Pydantic Schema (`MeetingIntelligenceOutput`) to the LLM. The LLM acts as a strict data-extraction engine, pulling out the summary, decisions, and action items in one fast API call.

**3. Evidence-Based Output**
Every extracted action item requires the LLM to output an `evidence_transcript` (the exact segment where the commitment was spoken). This significantly reduces hallucinations and allows users to trust the generated action items.

---

### ⚖️ Tradeoffs & Limitations

1. **Dependency on Speaker Diarization:** 
   This agent currently relies on the input text already having speaker labels (e.g., `Sarah: I will do this`). If a raw audio transcript lacks diarization, the agent will struggle to assign owners accurately. With more time, we would integrate an audio processing layer (like Pyannote or Google Cloud Speech-to-Text) to handle raw audio.
   
2. **Context Window Limits on Massive Meetings:**
   While Gemini has a large context window, feeding a 4-hour raw transcript might dilute attention. A tradeoff was made to process the transcript whole for simplicity. With more time, we would implement a chunking mechanism (RAG or rolling summary) for meetings longer than 2 hours.

3. **String Matching for Deadlines:**
   The agent extracts the `deadline_phrase` as spoken (e.g., "by next Wednesday"). It does not normalize this to an ISO date. This was an intentional tradeoff to prevent the LLM from making incorrect date assumptions without knowing the exact time the meeting occurred. In a production app, a secondary agent (like our `ContextRetrievalAgent`) handles timezone-aware date normalization.
