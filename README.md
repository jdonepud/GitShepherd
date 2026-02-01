# GitShepherd 🐑

**Autonomous AI refactoring agent that transforms natural language tasks into PR-ready code changes—powered by Gemini AI.**

GitShepherd is a smart, self-improving agent that helps open-source contributors and maintainers save massive amounts of time on routine code improvement tasks. Powered by Gemini 3's 1M+ token context window.

## Features

- **Repo Fetcher:** Pulls public repositories via tarball/API for fast analysis.
- **Autonomous Planner:** Creates multi-level refactoring plans based on natural language tasks.
- **Verification Loop:** Runs tests (pytest, etc.) in a loop to ensure correctness.
- **PR Packager:** Generates ready-to-use PR descriptions and unified patches.

## Tech Stack

- **Frontend:** Vanilla HTML/JS with Glassmorphism CSS.
- **Backend:** Python / FastAPI.
- **Intelligence:** Gemini 2.5/3 (Auto-detects available models).
- **Test Runner:** Docker (optional) or local execution.

## Getting Started

1.  **Install dependencies:**
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

2.  **Set up environment:**
    ```bash
    # Create .env file with:
    GEMINI_API_KEY=your_api_key_here
    ```

3.  **Start the backend:**
    ```bash
    python main.py
    ```

3.  **Open the frontend:**
    Open `frontend/index.html` in your browser.

## How it Works

1.  **Call 0 - Repo Mapper:** Analyzes the directory tree to understand project type and test commands.
2.  **Call 1 - Planner:** Generates an ordered execution plan.
3.  **Loop - Execution & Correction:** The agent edits code and runs tests until the task is complete or max retries are reached.
4.  **Final - PR Package:** Summarizes changes into a patch and a description.
