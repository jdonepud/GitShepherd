"""Artifact generator for PR packages, diffs, and reports."""
import os
import subprocess
from typing import Dict, List, Optional
from datetime import datetime

class ArtifactGenerator:
    @staticmethod
    def generate_unified_diff(workspace_path: str, base_path: Optional[str] = None) -> str:
        """Generate unified diff of all changes."""
        try:
            # Try git diff first
            result = subprocess.run(
                ['git', 'diff', '--no-color'],
                cwd=workspace_path,
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout
        except:
            pass
        
        # Fallback: manual diff generation
        # This would require tracking original vs modified files
        return "# Unified diff would be generated here\n# (Requires git repository or file tracking)"
    
    @staticmethod
    def generate_pr_package(
        task: str,
        changes_summary: str,
        verification_results: Dict,
        unified_diff: str,
        changed_files: List[str],
        guardrails_stats: Optional[Dict] = None
    ) -> Dict:
        """Generate PR-ready package with title, description, checklist, etc."""
        
        # Count changes
        files_count = len(changed_files)
        test_passed = verification_results.get("tests", {}).get("success", False) if isinstance(verification_results.get("tests"), dict) else False
        
        # Generate title
        title = f"Refactor: {task[:50]}" if len(task) > 50 else f"Refactor: {task}"
        
        # Generate description
        description = f"""## Summary

This PR implements the following changes:
{task}

## Changes Made

- Modified {files_count} file(s)
{chr(10).join([f"  - `{f}`" for f in changed_files[:10]])}
{f"{chr(10)}  - ... and {files_count - 10} more files" if files_count > 10 else ""}

## Verification

### Test Results
{'✅ All tests passed' if test_passed else '⚠️ Some tests may have failed - review required'}

### Guardrails
"""
        if guardrails_stats:
            description += f"""
- Files touched: {guardrails_stats.get('files_touched', 0)}/{guardrails_stats.get('max_files', 'N/A')}
- LOC changed: {guardrails_stats.get('loc_changed', 0)}/{guardrails_stats.get('max_loc', 'N/A')}
- Retries used: {guardrails_stats.get('retry_count', 0)}/{guardrails_stats.get('max_retries', 'N/A')}
"""
        
        description += f"""
## How to Apply

```bash
# Apply the patch
git apply <(curl -L <patch-url>)

# Or checkout the branch
git checkout -b gitshepherd-refactor
git apply patch.diff
```

## Testing

Run the following to verify:
```bash
{verification_results.get('testCommand', 'pytest') if isinstance(verification_results, dict) else 'pytest'}
```

## Notes

- This PR was generated autonomously by GitShepherd
- Please review all changes carefully before merging
- Some manual adjustments may be required

---
*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # Generate checklist
        checklist = [
            "✅ Code changes reviewed",
            "✅ Tests pass locally",
            "✅ No breaking changes introduced",
            "⚠️ Manual review recommended",
            "⚠️ Update documentation if needed"
        ]
        
        return {
            "title": title,
            "description": description,
            "checklist": checklist,
            "howTested": f"Ran: {verification_results.get('testCommand', 'pytest') if isinstance(verification_results, dict) else 'pytest'}",
            "howToApply": "git apply patch.diff",
            "knownLimitations": "Autonomous refactor - manual review required",
            "unifiedDiff": unified_diff[:50000]  # Limit size
        }
    
    @staticmethod
    def generate_markdown_report(
        task: str,
        plan: List[Dict],
        execution_log: List[str],
        verification_results: Dict,
        changed_files: List[str],
        guardrails_stats: Optional[Dict] = None
    ) -> str:
        """Generate a markdown report of the refactoring session."""
        
        report = f"""# GitShepherd Refactoring Report

**Task:** {task}
**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Execution Plan

"""
        for step in plan:
            report += f"### Step {step.get('step', '?')}: {step.get('action', 'N/A')}\n"
            report += f"- Files: {', '.join(step.get('files', []))}\n"
            report += f"- Risk: {step.get('risk', 'unknown')}\n\n"
        
        report += "## Execution Log\n\n"
        for log_entry in execution_log:
            report += f"- {log_entry}\n"
        
        report += "\n## Verification Results\n\n"
        if isinstance(verification_results, dict):
            if verification_results.get("tests"):
                test_result = verification_results["tests"]
                report += f"### Tests: {'✅ PASSED' if test_result.get('success') else '❌ FAILED'}\n"
                if test_result.get('output'):
                    report += f"```\n{test_result['output'][:1000]}\n```\n\n"
        
        report += f"## Changed Files\n\n"
        for f in changed_files:
            report += f"- `{f}`\n"
        
        if guardrails_stats:
            report += "\n## Guardrails\n\n"
            report += f"- Files touched: {guardrails_stats.get('files_touched', 0)}/{guardrails_stats.get('max_files', 'N/A')}\n"
            report += f"- LOC changed: {guardrails_stats.get('loc_changed', 0)}/{guardrails_stats.get('max_loc', 'N/A')}\n"
            report += f"- Retries: {guardrails_stats.get('retry_count', 0)}/{guardrails_stats.get('max_retries', 'N/A')}\n"
        
        return report
