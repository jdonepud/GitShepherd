"""Test runner for verification."""
import os
import subprocess
from typing import Dict

class TestRunner:
    @staticmethod
    def run_tests(workspace_path: str, test_command: str) -> Dict:
        """Run tests and return results."""
        if not test_command:
            return {"success": True, "logs": "No test command provided", "exit_code": 0}
        
        try:
            # Parse command
            cmd_parts = test_command.split()
            if not cmd_parts:
                return {"success": False, "logs": "Invalid test command", "exit_code": 1}
            
            result = subprocess.run(
                cmd_parts,
                cwd=workspace_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            return {
                "success": result.returncode == 0,
                "logs": result.stdout + result.stderr,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "logs": "Test execution timed out after 5 minutes", "exit_code": -1}
        except Exception as e:
            return {"success": False, "logs": f"Error running tests: {str(e)}", "exit_code": -1}
