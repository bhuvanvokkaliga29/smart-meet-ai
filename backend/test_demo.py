from models import MeetingInput
from agents.orchestrator import MultiAgentOrchestrator
import database
import json

def run_demo_simulation():
    print("=" * 70)
    print("⚡ SMARTMEET AI v2 — MULTI-AGENT EXECUTION DEMO SIMULATION ⚡")
    print("=" * 70)

    # Step 1: Input Meeting Speech
    input_data = MeetingInput(
        title="Project Kickoff & Release Sync",
        transcript=(
            "Rahul: Can you finish the Login UI prototype by Friday? "
            "Priya: Sure, I will prepare the test plan by next Wednesday. "
            "Alex: Great! We also decided to postpone the production deployment until security audit completes."
        ),
        speakers=["Rahul", "Priya", "Alex"],
        mode="demo"
    )

    print(f"\n🎙️  STEP 1: INGESTING MEETING CAPTURE")
    print(f"Title: {input_data.title}")
    print(f"Transcript Input:\n\"{input_data.transcript}\"")

    # Step 2: Run Multi-Agent Orchestrator Pipeline
    print(f"\n🤖 STEP 2: RUNNING MULTI-AGENT ORCHESTRATOR PIPELINE...")
    orchestrator = MultiAgentOrchestrator()
    result = orchestrator.run_pipeline(input_data)

    print("\n--- 📝 SUMMARY AGENT OUTPUT ---")
    print(f"Summary: {result['summary']}")
    print("Key Decisions:")
    for d in result["decisions"]:
        print(f"  ✓ {d}")

    print("\n--- 🔍 VALIDATION AGENT OUTPUT ---")
    print(f"Validation Status: {result['validation_status']}")
    print(f"Overall Confidence Rating: {int(result['overall_confidence'] * 100)}%")

    print("\n--- 🛠️  EXTRACTED ENRICHED ACTION ITEMS ---")
    for i, t in enumerate(result["tasks"], 1):
        print(f"Task #{i}: {t['task']}")
        print(f"   👤 Owner: {t['owner']}")
        print(f"   📅 Target Deadline: {t['deadline']}")
        print(f"   🔥 Priority Level: {t['priority']}")
        print(f"   🎯 Confidence Score: {int(t['confidence'] * 100)}%")
        print(f"   🧠 Cross-Meeting Memory Note: {t['cross_meeting_note']}\n")

    # Step 3: Human-in-the-Loop Approval & SQL Commit
    print("✨ STEP 3: HUMAN-IN-THE-LOOP APPROVAL PORTAL")
    print("Simulating User Verification & Approval...")
    approved_tasks = []
    for t in result["tasks"]:
        t["meeting_id"] = "m-demo-2026"
        t["status"] = "Pending"
        approved_tasks.append(t)

    database.add_tasks(approved_tasks)
    print(f"✅ Committed {len(approved_tasks)} verified tasks into SQLite database (smartmeet.db)!")

    # Step 4: Check Cross-Meeting Memory & Status Recap
    print("\n🧠 STEP 4: CROSS-MEETING INTELLIGENCE RECAP")
    recap = orchestrator.cross_meeting_agent.generate_recap()
    print(f"Status Recap: {recap.status_recap_text}")
    print(f"Total Tracked Tasks: {recap.total_previous_tasks}")
    print(f"  - Completed: {recap.completed_count}")
    print(f"  - Active/Pending: {recap.pending_count}")
    print(f"  - Blocked: {recap.blocked_count}")

    print("\n=" * 70)
    print("🎉 DEMO SIMULATION COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_demo_simulation()
