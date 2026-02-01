"""Patch application engine."""
import os
import re
import subprocess
from typing import Dict, Tuple

class PatchEngine:
    @staticmethod
    def apply_unified_diff(workspace_path: str, diff: str) -> Dict:
        """Apply a unified diff to files in workspace."""
        if not diff or not diff.strip():
            return {"success": False, "error": "Empty diff"}
        
        # Clean up diff - remove markdown code blocks
        diff_clean = diff.strip()
        if diff_clean.startswith("```"):
            parts = diff_clean.split("```")
            if len(parts) > 1:
                diff_clean = parts[1]
                if diff_clean.startswith("diff") or diff_clean.startswith("python"):
                    diff_clean = diff_clean.split("\n", 1)[1] if "\n" in diff_clean else ""
        
        # Try git apply first (if git is available)
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False, encoding='utf-8') as f:
                f.write(diff_clean)
                temp_diff = f.name
            
            # Check if patch applies
            result = subprocess.run(
                ['git', 'apply', '--check', temp_diff],
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                # Apply the patch
                result = subprocess.run(
                    ['git', 'apply', temp_diff],
                    cwd=workspace_path,
                    capture_output=True,
                    text=True
                )
                os.unlink(temp_diff)
                if result.returncode == 0:
                    return {"success": True, "message": "Patch applied successfully"}
                else:
                    # Fallback to manual
                    os.unlink(temp_diff)
                    return PatchEngine._apply_manually(workspace_path, diff_clean)
            else:
                os.unlink(temp_diff)
                # Fallback to manual application
                return PatchEngine._apply_manually(workspace_path, diff_clean)
        except FileNotFoundError:
            # Git not available, use manual
            return PatchEngine._apply_manually(workspace_path, diff_clean)
        except Exception as e:
            return {"success": False, "error": f"Error applying patch: {str(e)}"}
    
    @staticmethod
    def _apply_manually(workspace_path: str, diff: str) -> Dict:
        """Manually parse and apply unified diff."""
        try:
            lines = diff.split('\n')
            current_file = None
            current_hunk = []
            old_start = 0
            old_count = 0
            
            i = 0
            while i < len(lines):
                line = lines[i]
                
                # File header
                if line.startswith('---'):
                    # Apply previous file if any
                    if current_file and current_hunk:
                        PatchEngine._apply_hunk(workspace_path, current_file, current_hunk, old_start, old_count)
                    
                    # Extract filename
                    match = re.match(r'^--- a/(.+)$', line)
                    if match:
                        current_file = match.group(1)
                    else:
                        match = re.match(r'^--- (.+)$', line)
                        if match:
                            current_file = match.group(1).split('\t')[0]
                    
                    current_hunk = []
                
                elif line.startswith('+++'):
                    # New file marker, ignore
                    pass
                
                elif line.startswith('@@'):
                    # Hunk header
                    if current_file and current_hunk:
                        PatchEngine._apply_hunk(workspace_path, current_file, current_hunk, old_start, old_count)
                    
                    match = re.match(r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                    if match:
                        old_start = int(match.group(1))
                        old_count = int(match.group(2) or 1)
                        current_hunk = []
                
                elif current_file:
                    current_hunk.append(line)
                
                i += 1
            
            # Apply last hunk
            if current_file and current_hunk:
                PatchEngine._apply_hunk(workspace_path, current_file, current_hunk, old_start, old_count)
            
            return {"success": True, "message": "Patch applied manually"}
        except Exception as e:
            return {"success": False, "error": f"Manual application failed: {str(e)}"}
    
    @staticmethod
    def _apply_hunk(workspace_path: str, file_path: str, hunk_lines: list, old_start: int, old_count: int):
        """Apply a single hunk to a file."""
        full_path = os.path.join(workspace_path, file_path)
        
        if not os.path.exists(full_path):
            # Create new file
            content_lines = []
        else:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content_lines = f.readlines()
        
        result_lines = content_lines.copy()
        old_line = old_start - 1  # Convert to 0-based
        
        for hunk_line in hunk_lines:
            if hunk_line.startswith(' '):
                # Context line - advance
                if old_line < len(result_lines):
                    old_line += 1
            elif hunk_line.startswith('-'):
                # Delete line
                if old_line < len(result_lines):
                    result_lines.pop(old_line)
            elif hunk_line.startswith('+'):
                # Add line
                new_content = hunk_line[1:]  # Remove '+'
                if not new_content.endswith('\n'):
                    new_content += '\n'
                result_lines.insert(old_line, new_content)
                old_line += 1
        
        # Write back
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.writelines(result_lines)
