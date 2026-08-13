import re
from typing import Tuple, Optional

class IntentClassifier:
    """Stage 1: Sentence Intent Classifier Engine.
    Classifies each sentence/clause into exactly ONE intent:
    'Action', 'Decision', 'Risk', 'Completed', 'Discussion', 'Question', or 'Information'.
    """

    @staticmethod
    def classify(clause: str) -> Tuple[str, float]:
        c_lower = clause.lower().strip()

        if not c_lower or len(c_lower) < 5:
            return "Information", 0.50

        # 1. QUESTION INTENT
        if '?' in clause or c_lower.startswith(('what ', 'how ', 'why ', 'can we ', 'could you ', 'is there ', 'are we ')):
            return "Question", 0.95

        # 2. GREETINGS & META-DISCUSSION INTENT (Strictly Filter Out Meta Intros & Agendas)
        greetings = [
            'good morning', 'hello', 'hi ', 'welcome', 'let\'s go around', 'let\'s go through',
            'discuss progress', 'outstanding issues', 'anything that might delay', 'agenda for today',
            'how is everyone', 'like to understand', 'my name is', 'myself'
        ]
        if any(g in c_lower for g in greetings):
            return "Discussion", 0.95

        # 3. STATUS UPDATES & GENERAL STATEMENTS (Filter Out Exploratory & Ongoing Work)
        status_updates = [
            'i\'m investigating', 'investigating a', 'currently working on', 'we are exploring',
            'experimenting with', 'currently testing', 'biggest goals are', 'our goal is',
            'looking into', 'the pilot is a', 'major milestone', 'that\'s encouraging'
        ]
        if any(su in c_lower for su in status_updates):
            return "Information", 0.90

        # 4. DECISION INTENT
        # Scope freezes, strategic alignment, team choices
        decision_patterns = [
            r'\bno new features\b', r'\bfocus on stability\b', r'\bprioritis[e|ing]\b', r'\bprioritiz[e|ing]\b',
            r'\bhighest priorit[y|ies]\b', r'\bwe decided\b', r'\bagreed on\b', r'\bplan is to freeze\b',
            r'\bdecided to\b', r'\bunanimously agreed\b'
        ]
        if any(re.search(pat, c_lower) for pat in decision_patterns):
            # Unless it's a specific personal task assignment like "Kevin, please finish..."
            if not re.search(r'^\s*[a-z][a-z0-9]{2,15}\s*,\s*(?:finish|implement|prepare|attend|run|verify)\b', c_lower):
                return "Decision", 0.94

        # 5. COMPLETED MILESTONES INTENT
        # Past achievements, completed features
        future_aux = ['will ', 'i\'ll', 'gonna', 'going to', 'need to', 'must ', 'should ', 'plan to', 'by monday', 'by tuesday', 'by wednesday', 'by thursday', 'by friday', 'finish ', 'complete ']
        has_future = any(fa in c_lower for fa in future_aux)

        completed_patterns = [
            r'\bcompleted\b', r'\bimplemented\b', r'\bmigrated\b', r'\bimproved from\b', r'\bfinished\b',
            r'\bperforming much better\b', r'\bachieved\b', r'\bapis finished\b', r'\bdashboard finished\b',
            r'\bis complete\b', r'\bis fully integrated\b'
        ]
        if any(re.search(pat, c_lower) for pat in completed_patterns) and not has_future:
            return "Completed", 0.93

        # 6. RISK INTENT
        # Technical blockers, bugs, throughput limits, memory spikes, latency
        risk_patterns = [
            r'\bmisclassifi[es|ed|cation]\b', r'\breduces throughput\b', r'\blimited (?:automated )?test\b',
            r'\bpoor performance\b', r'\black of\b', r'\bbug\b', r'\bblocker\b', r'\bissue we discovered\b',
            r'\bmemory spikes\b', r'\breplication latency\b', r'\bcausing extraction errors\b',
            r'\bconcern\b', r'\bbottleneck\b', r'\bdelay\b'
        ]
        if any(re.search(pat, c_lower) for pat in risk_patterns) and not has_future:
            return "Risk", 0.92

        # 7. ACTION INTENT (Explicit Future Directives & Tasks)
        action_patterns = [
            r'\bmeasure\b', r'\bverify\b', r'\bconfigure\b', r'\bfinish\b', r'\bimprove\b',
            r'\bconduct\b', r'\bprepare\b', r'\battend\b', r'\bimplement\b', r'\bintegrat[e|ion]\b',
            r'\bdeploy\b', r'\btest\b', r'\bresolve\b', r'\bfix\b', r'\bupdate\b', r'\bsubmit\b',
            r'\bevaluate\b', r'\brun\b', r'\badd\b', r'\bnotify\b', r'\breduce\b',
            r'\bwill\b', r'\bgonna\b', r'\bgoing to\b', r'\bneed to\b', r'\bmust\b', r'\bshould\b',
            r'\bby (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next week)\b'
        ]

        if any(re.search(pat, c_lower) for pat in action_patterns):
            return "Action", 0.91

        # 8. DEFAULT INFORMATION / DISCUSSION
        return "Information", 0.60
