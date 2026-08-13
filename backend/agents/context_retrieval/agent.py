"""
Context & Retrieval Agent
=========================
Receives CommitmentCandidate from MeetingIntelligence.
Performs:
1. Owner disambiguation (resolving "Sarah" to an actual identity if possible)
2. Historical memory lookup (detects duplicates and dependencies)
3. Deadline normalization
Outputs: EnrichedCommitment
"""

import time
import uuid
import datetime
from typing import List, Optional
from schemas import (
    CommitmentCandidate, 
    EnrichedCommitment, 
    ResolvedOwner, 
    HistoricalContext,
    CommitmentState,
    CommitmentType
)
import database

class ContextRetrievalAgent:
    def __init__(self):
        # In a real enterprise system this would hook into an Identity Vault or Directory Service
        self.known_identities = {
            "sarah": [
                {"name": "Sarah Jenkins", "role": "Backend Lead", "email": "sjenkins@smartmeet.ai"},
                {"name": "Sarah Rao", "role": "Product Manager", "email": "srao@smartmeet.ai"}
            ],
            "alex": [{"name": "Alex Chen", "role": "Engineering Manager", "email": "achen@smartmeet.ai"}],
            "priya": [{"name": "Priya Sharma", "role": "Database Architect", "email": "psharma@smartmeet.ai"}],
            "rahul": [{"name": "Rahul Verma", "role": "Frontend Developer", "email": "rverma@smartmeet.ai"}],
            "kevin": [{"name": "Kevin Lee", "role": "QA Engineer", "email": "klee@smartmeet.ai"}]
        }

    def process(self, candidates: List[CommitmentCandidate]) -> List[EnrichedCommitment]:
        enriched = []
        for c in candidates:
            start_time = time.time()
            
            # 1. Resolve Owner
            resolved_owner = self._resolve_owner(c.owner_candidate, c.action, c.evidence_transcript)
            
            # 2. Historical Context (Mocked semantic retrieval for demo)
            historical = self._retrieve_history(c.action, resolved_owner.name)
            
            # 3. Deadline Normalization
            normalized_date, reason = self._normalize_deadline(c.deadline_phrase)
            
            # Build EnrichedCommitment
            ec = EnrichedCommitment(
                id=f"c-{uuid.uuid4().hex[:8]}",
                action=c.action,
                resolved_owner=resolved_owner,
                delegator=c.delegator,
                deadline_phrase=c.deadline_phrase,
                normalized_deadline=normalized_date,
                normalization_reason=reason,
                condition=c.condition,
                commitment_type=c.commitment_type,
                priority="High" if any(w in c.action.lower() for w in ['deploy', 'production', 'blocker', 'critical', 'urgent', 'immediately']) else "Medium",
                evidence_transcript=c.evidence_transcript,
                state=CommitmentState.PROPOSED,
                confidence=min(c.confidence, resolved_owner.confidence),
                historical_context=historical,
                model_provider=c.model_provider,
                model_name=c.model_name,
                processing_latency_ms=(time.time() - start_time) * 1000 + (c.processing_latency_ms or 0)
            )
            
            enriched.append(ec)
            
        return enriched

    def _resolve_owner(self, candidate: Optional[str], action: str, evidence: str) -> ResolvedOwner:
        if not candidate or candidate.lower() == "unassigned":
            return ResolvedOwner(name="Unassigned", confidence=0.0, needs_confirmation=True)
            
        cand_lower = candidate.lower().strip()
        matches = self.known_identities.get(cand_lower, [])
        
        if not matches:
            return ResolvedOwner(name=candidate.capitalize(), confidence=0.7, needs_confirmation=True, disambiguation_reason="Not in directory")
            
        if len(matches) == 1:
            return ResolvedOwner(
                name=matches[0]["name"],
                email=matches[0]["email"],
                role=matches[0]["role"],
                confidence=0.95
            )
            
        # Ambiguous case (e.g. "Sarah")
        # In a real app we'd ask Gemini to use context, here we use a deterministic heuristic
        if "backend" in action.lower() or "api" in action.lower() or "server" in action.lower() or "migration" in action.lower():
            target = next(m for m in matches if m["name"] == "Sarah Jenkins")
            return ResolvedOwner(
                name=target["name"],
                email=target["email"],
                role=target["role"],
                confidence=0.85,
                disambiguation_reason="Resolved based on engineering context"
            )
            
        if "product" in action.lower() or "design" in action.lower() or "review" in action.lower():
            target = next(m for m in matches if m["name"] == "Sarah Rao")
            return ResolvedOwner(
                name=target["name"],
                email=target["email"],
                role=target["role"],
                confidence=0.85,
                disambiguation_reason="Resolved based on product context"
            )
            
        # Complete ambiguity
        return ResolvedOwner(
            name=candidate.capitalize(),
            confidence=0.4,
            needs_confirmation=True,
            disambiguation_reason="Multiple matches found. Needs human confirmation.",
            alternative_candidates=[m["name"] for m in matches]
        )

    def _retrieve_history(self, action: str, owner: str) -> HistoricalContext:
        """Looks up existing commitments in the DB to find duplicates/blockers."""
        tasks = database.get_all_tasks()
        
        hist = HistoricalContext()
        action_lower = action.lower()
        
        for t in tasks:
            t_action = t.get("task", "").lower()
            
            # Check for possible duplicate (similar name, same owner, not completed)
            if t.get("owner") == owner and t.get("status") not in ["Completed", "Cancelled"]:
                words_match = sum(1 for w in action_lower.split() if len(w) > 3 and w in t_action)
                if words_match > 1 or action_lower in t_action or t_action in action_lower:
                    hist.possible_duplicate = True
                    hist.duplicate_of = t.get("id")
                    hist.related_commitments.append({
                        "id": t.get("id"),
                        "action": t.get("task"),
                        "status": t.get("status"),
                        "similarity": "high"
                    })
            
            # Check for unresolved blockers globally across previous meetings
            if t.get("status") == "Blocked" and t_action:
                # Basic context match (e.g. migration blocked by server access)
                if any(w in t_action for w in action_lower.split() if len(w) > 4):
                    hist.unresolved_blockers.append(t.get("task"))

        return hist

    def _normalize_deadline(self, phrase: Optional[str]) -> tuple[Optional[str], Optional[str]]:
        if not phrase:
            return None, None
            
        p_lower = phrase.lower().strip()
        today = datetime.date.today()
        
        day_offsets = {
            'today': 0, 'tonight': 0, 'tomorrow': 1,
            'monday': (0 - today.weekday()) % 7 or 7,
            'tuesday': (1 - today.weekday()) % 7 or 7,
            'wednesday': (2 - today.weekday()) % 7 or 7,
            'thursday': (3 - today.weekday()) % 7 or 7,
            'friday': (4 - today.weekday()) % 7 or 7,
            'saturday': (5 - today.weekday()) % 7 or 7,
            'sunday': (6 - today.weekday()) % 7 or 7,
            'next week': 7,
        }
        
        for kw, offset in day_offsets.items():
            if kw in p_lower:
                target_date = today + datetime.timedelta(days=offset)
                return target_date.strftime("%Y-%m-%d"), f"Matched relative day keyword: {kw}"
                
        # Default fallback
        target_date = today + datetime.timedelta(days=3)
        return target_date.strftime("%Y-%m-%d"), "Defaulted to +3 days (no specific date detected)"
