"""Guardrails for change budget and safety enforcement."""
from typing import Dict, List, Optional, Tuple

class Guardrails:
    def __init__(
        self, 
        max_files: int = 50, 
        max_loc: int = 5000, 
        max_retries: int = 6, 
        conservative: bool = True,
        max_loc_per_file: int = 500
    ):
        self.max_files = max_files
        self.max_loc = max_loc
        self.max_loc_per_file = max_loc_per_file
        self.max_retries = max_retries
        self.conservative = conservative
        self.files_touched = set()
        self.loc_changed = 0
        self.retry_count = 0
        
        # Allowed/disallowed operations
        self.allowed_operations = [
            "edit", "refactor", "add_test", "fix_bug", "improve", "optimize",
            "update", "modify", "enhance", "cleanup"
        ]
        
        self.disallowed_operations = [
            "delete_critical", "remove_security", "change_api_contract", 
            "break_compatibility", "remove_authentication", "disable_validation"
        ]
    
    def check_budget(self, files: List[str], estimated_loc: int = 0) -> Tuple[bool, str]:
        """Check if operation is within budget."""
        new_files = set(files) - self.files_touched
        
        if len(self.files_touched) + len(new_files) > self.max_files:
            return False, f"Exceeds max files limit ({self.max_files})"
        
        if self.loc_changed + estimated_loc > self.max_loc:
            return False, f"Exceeds max LOC limit ({self.max_loc})"
        
        return True, ""
    
    def check_file_size(self, file_path: str, loc: int) -> Tuple[bool, str]:
        """Check if file is within size limits."""
        if loc > self.max_loc_per_file:
            return False, f"File exceeds max LOC per file ({self.max_loc_per_file})"
        return True, ""
    
    def record_change(self, files: List[str], loc: int):
        """Record a change."""
        self.files_touched.update(files)
        self.loc_changed += loc
    
    def can_retry(self) -> bool:
        """Check if we can retry."""
        return self.retry_count < self.max_retries
    
    def record_retry(self):
        """Record a retry attempt."""
        self.retry_count += 1
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        return {
            "files_touched": len(self.files_touched),
            "max_files": self.max_files,
            "loc_changed": self.loc_changed,
            "max_loc": self.max_loc,
            "max_loc_per_file": self.max_loc_per_file,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "budget_remaining": {
                "files": self.max_files - len(self.files_touched),
                "loc": self.max_loc - self.loc_changed
            }
        }
    
    def validate_operation(self, operation: str) -> Tuple[bool, str]:
        """Validate if operation is allowed."""
        if operation in self.disallowed_operations:
            return False, f"Operation '{operation}' is not allowed"
        
        if self.conservative and operation not in self.allowed_operations:
            return False, f"Operation '{operation}' not in allowed list (conservative mode)"
        
        return True, ""
