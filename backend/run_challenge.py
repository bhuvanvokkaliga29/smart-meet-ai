import sys
import json
import os

# Ensure we can import from the backend directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.meeting_intelligence.agent import MeetingIntelligenceAgent
from config import settings

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_challenge.py <path_to_transcript>")
        print("Example: python run_challenge.py ../challenge_assets/transcript_1_planning.txt")
        sys.exit(1)
        
    transcript_path = sys.argv[1]
    if not os.path.exists(transcript_path):
        print(f"Error: File not found at {transcript_path}")
        sys.exit(1)
        
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript_text = f.read()
        
    print(f"\n[INFO] Starting Agent: Meeting Notes to Action Items")
    print(f"[INFO] Reading transcript: {os.path.basename(transcript_path)}")
    print("[INFO] Processing with Gemini 2.5 Flash... (This may take a few seconds)\n")
    
    # Initialize the agent
    agent = MeetingIntelligenceAgent()
    
    # Process the transcript
    try:
        result = agent.process(transcript_text, meeting_id="challenge_demo")
        
        # Serialize to dictionary
        result_dict = result.dict() if hasattr(result, 'dict') else result.model_dump()
        
        # Print cleanly
        print("-" * 50)
        print(" AGENT OUTPUT ".center(50, "-"))
        print("-" * 50)
        print(json.dumps(result_dict, indent=2))
        print("-" * 50)
        
        print(f"\n[SUCCESS] Processed {result.total_segments_processed} segments in {result.total_latency_ms:.2f}ms using {result.model_provider}")
        
    except Exception as e:
        print(f"[ERROR] Agent processing failed: {str(e)}")

if __name__ == "__main__":
    main()
