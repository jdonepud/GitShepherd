"""Analyze tasks to determine if code changes are needed."""
import re
from typing import Tuple

class TaskAnalyzer:
    """Analyze user tasks to determine intent."""
    
    # Keywords that indicate code changes are needed
    CODE_CHANGE_KEYWORDS = [
        'refactor', 'fix', 'add', 'modify', 'update', 'change', 'improve',
        'implement', 'create', 'write', 'remove', 'delete', 'replace',
        'convert', 'migrate', 'rewrite', 'optimize', 'enhance', 'edit',
        'patch', 'apply', 'make', 'do', 'transform'
    ]
    
    # Keywords that indicate analysis-only (no code changes)
    ANALYSIS_KEYWORDS = [
        'explain', 'analyze', 'describe', 'review', 'examine', 'understand',
        'document', 'summarize', 'list', 'show', 'display', 'tell', 'what',
        'how does', 'what is', 'explore', 'inspect', 'look at', 'check'
    ]
    
    @staticmethod
    def requires_code_changes(task: str) -> Tuple[bool, str]:
        """
        Determine if task requires code changes.
        Returns (requires_changes, reason)
        """
        task_lower = task.lower()
        
        # Check for explicit PR/change requests
        if any(keyword in task_lower for keyword in ['create pr', 'generate pr', 'make pr', 'pull request']):
            return True, "Explicit PR request detected"
        
        # Check for code change keywords
        change_matches = sum(1 for keyword in TaskAnalyzer.CODE_CHANGE_KEYWORDS if keyword in task_lower)
        analysis_matches = sum(1 for keyword in TaskAnalyzer.ANALYSIS_KEYWORDS if keyword in task_lower)
        
        # If analysis keywords dominate, it's likely analysis-only
        if analysis_matches > change_matches and analysis_matches > 0:
            return False, "Task appears to be analysis-only"
        
        # If change keywords are present, likely needs changes
        if change_matches > 0:
            return True, f"Code change keywords detected ({change_matches} matches)"
        
        # Default: if unclear, assume analysis-only to be safe
        return False, "No clear code change intent detected"
    
    @staticmethod
    def should_generate_pr(task: str, files_changed: int) -> bool:
        """
        Determine if PR should be generated.
        Only generate if:
        1. Task requires code changes AND
        2. Files were actually changed
        """
        requires_changes, _ = TaskAnalyzer.requires_code_changes(task)
        return requires_changes and files_changed > 0
