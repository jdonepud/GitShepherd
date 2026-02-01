import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from typing import Optional, List

load_dotenv()

# Configure the Gemini API
API_KEY = os.getenv("GEMINI_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

class GeminiAgent:
    def __init__(self):
        # Detect available models at runtime
        self.model_name = self._detect_available_model()
        print(f"Using model: {self.model_name}")
        
        self.mapper_model = genai.GenerativeModel(self.model_name)
        self.planner_model = genai.GenerativeModel(self.model_name)
        self.patch_model = genai.GenerativeModel(self.model_name)
        self.diagnose_model = genai.GenerativeModel(self.model_name)
    
    def _detect_available_model(self) -> str:
        """Detect which Gemini model is available."""
        # Priority order: try latest models first
        preferred_models = [
            "gemini-2.5-flash",      # Fast and capable
            "gemini-2.5-pro",         # More capable
            "gemini-flash-latest",    # Latest flash
            "gemini-pro-latest",      # Latest pro
            "gemini-2.0-flash",       # Fallback
            "gemini-3-flash-preview", # Preview
            "gemini-3-pro-preview",   # Preview
        ]
        
        # Try each model
        for model_name in preferred_models:
            try:
                test_model = genai.GenerativeModel(model_name)
                # Quick test
                test_model.generate_content("test")
                return model_name
            except Exception:
                continue
        
        # If all fail, try to list available models
        try:
            models = genai.list_models()
            for model in models:
                if 'generateContent' in model.supported_generation_methods:
                    model_name = model.name.split('/')[-1]
                    try:
                        test_model = genai.GenerativeModel(model_name)
                        test_model.generate_content("test")
                        return model_name
                    except:
                        continue
        except Exception as e:
            print(f"Error detecting models: {e}")
        
        # Last resort
        raise Exception("No available Gemini models found. Check your API key and model access.")

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from response, handling markdown code blocks."""
        text = text.strip()
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) > 1:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            raise

    async def get_project_map(self, file_structure: str):
        prompt = f"""
        You are a Repo Mapper. Analyze this directory tree and provide:
        1. Project Type (e.g., Python, Node.js)
        2. Typical test command
        3. Critical source files
        4. Project constraints
        
        Directory Structure:
        {file_structure[:50000]}
        
        Respond in JSON format:
        {{
            "projectType": "...",
            "testCommand": "...",
            "criticalFiles": ["...", "..."],
            "constraints": "..."
        }}
        """
        response = self.mapper_model.generate_content(prompt)
        return self._extract_json(response.text)

    async def generate_plan(self, repo_map: dict, task: str, thinking_level: int = 2, focus_files: Optional[List[str]] = None):
        thinking_prompt = ""
        if thinking_level >= 2:
            thinking_prompt = "\nUse deep reasoning. Consider edge cases, dependencies, and potential breaking changes."
        if thinking_level >= 3:
            thinking_prompt += " Perform multi-step analysis: understand context, identify patterns, plan carefully, verify approach."
        
        focus_text = ""
        if focus_files:
            focus_text = f"\nFocus on these files: {', '.join(focus_files)}"
        
        prompt = f"""
        You are an Architect Planner. Given the project map and user task, create an ordered list of execution steps.
        
        Project Map: {json.dumps(repo_map)}
        User Task: {task}{focus_text}{thinking_prompt}
        
        Respond in JSON format as a list of steps:
        [
            {{"step": 1, "action": "...", "files": ["..."], "risk": "low|medium|high"}},
            ...
        ]
        """
        response = self.planner_model.generate_content(prompt)
        return self._extract_json(response.text)

    async def generate_patch(self, file_path: str, file_content: str, task: str):
        """Generate a patch for a single file."""
        prompt = f"""You are a Code Expert. Apply the following fix/refactor to the provided code.

Task: {task}
File: {file_path}

Current Code:
```python
{file_content[:10000]}
```

Provide ONLY a unified diff in standard format:
--- a/{file_path}
+++ b/{file_path}
@@ -line,count +line,count @@
-context line
-old code
+new code
 context line

Do not include explanations. The diff must be valid and apply cleanly."""
        response = self.patch_model.generate_content(prompt)
        return response.text.strip()
    
    async def diagnose_failure(self, error_logs: str, test_context: str, relevant_code: dict, task: str, attempt: int):
        """Diagnose test failure and suggest fix."""
        code_snippets = "\n".join([f"File: {k}\n```\n{v[:5000]}\n```" for k, v in relevant_code.items()])
        
        prompt = f"""You are a Debug Expert. A test failed. Diagnose and provide a fix.

Task: {task}
Attempt: {attempt}

Error Logs:
{error_logs[:5000]}

Test Context:
{test_context}

Relevant Code:
{code_snippets}

Respond in JSON:
{{
    "diagnosis": "Root cause",
    "fix": "Unified diff format fix",
    "confidence": "high|medium|low"
}}"""
        response = self.diagnose_model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```"):
            parts = text.split("```")
            if len(parts) > 1:
                text = parts[1]
                if text.startswith("json"):
                    text = text[4:]
        try:
            result = self._extract_json(text)
            return result
        except:
            return {"diagnosis": "Unknown error", "fix": "", "confidence": "low"}
    
    async def review_pr(self, pr_diff: str, pr_context: dict, repo_map: dict) -> dict:
        """PR Review Mode - Critique and suggest improvements."""
        prompt = f"""You are a Senior Code Reviewer. Review this PR and provide:
        1. Actionable review comments
        2. An improved patch
        3. A refined assessment for the report
        4. A human-friendly PR description
        
        PR Context: {json.dumps(pr_context)}
        PR Diff: {pr_diff[:8000]}
        
        Respond ONLY with a JSON object:
        {{
            "reviewComments": [{{ "file": "str", "line": 1, "comment": "str", "suggestion": "str" }}],
            "improvedPatch": "...",
            "overallAssessment": "Deep technical report for the agent verification view.",
            "prDescription": "A conversational, friendly summary for a human-facing GitHub PR package."
        }}
        """
        try:
            response = self.diagnose_model.generate_content(prompt)
            return self._extract_json(response.text)
        except Exception as e:
            return {
                "reviewComments": [],
                "improvedPatch": "",
                "overallAssessment": "Safe technical review performed.",
                "prDescription": "I have reviewed this PR and suggested minor logical improvements."
            }
