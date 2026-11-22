# AI Research Agent

English | [中文](README.zh.md)

> **Live Demo**: [https://laihan1-research-agent.streamlit.app/](https://laihan1-research-agent.streamlit.app/)

Enter any research topic to run automated multi-round web searches, sufficiency checks, and source synthesis—producing a structured research report with clickable citations.

---

## Core Design

- **Hand-written ReAct Loop**: Built from scratch without LangChain or LangGraph. Implements a clear `plan -> search -> judge -> generate` loop with hard limits of **max 3 rounds** and **max 5 queries per round**.
- **3-Tier LLM Fallback Chain**: Strictly falls back in order: `Groq (openai/gpt-oss-120b)` → `Google Gemini Flash` → `OpenRouter (free tier)`. Raises a unified `LLMUnavailable` exception only if all providers fail, avoiding single-vendor lock-in.
- **Fault-Tolerant Web Search**: Uses DuckDuckGo as a single free search source with timeout protection and retries. Failures are logged and gracefully degrade to an empty list without crashing the pipeline.
- **Fixed 4-Section Report**: Outputs **Background**, **Key Findings** (every claim backed by a source URL), **Disagreements**, and **References**, plus a full execution trace in the UI.
- **Lightweight Persistence**: Appends structured run logs to `data/runs.jsonl` and stores 10-topic manual evaluation results in `data/eval.csv`.

## Architecture

```text
User Topic (Streamlit UI: app.py)
        │
        ▼
  agent/loop.py :: run(topic) -> Report   (Single entry point; catches all errors as status='failed')
        │
        ├── 1. Plan Queries (agent/llm.py: Groq -> Gemini -> OpenRouter)
        │
        ├── 2. Web Search (agent/search.py: DuckDuckGo; returns [] on timeout/error)
        │        └─ Hard limits: max 3 rounds, max 5 queries/round
        │
        ├── 3. Judge Sufficiency
        │        ├─ Enough info / consecutive unproductive rounds / max rounds reached ──▶ Generate
        │        └─ Gaps remain ──▶ Propose new queries & loop back to Search
        │
        └── 4. Generate 4-Section Report (marks status='degraded' if no sources or parse fallback)
                 │
                 ▼
         Append log to data/runs.jsonl & return Report
```

## Non-goals

- No multi-search-engine aggregation.
- No automated LLM-as-a-judge scoring (evaluation relies on manual verification of citation support and usability).
- No user accounts or chat/history management.
- No lock-in to any single LLM provider.

## Evaluation Summary

Evaluated end-to-end across 10 diverse technical and industry topics. Full results are recorded in [`data/eval.csv`](data/eval.csv):

| Metric | Result | Notes |
| :--- | :--- | :--- |
| **Task Completion** | **9 / 10 (`status=ok`)** | 1 topic gracefully degraded (`status=degraded`) due to consecutive empty DuckDuckGo results (zero crashes) |
| **Citation Support** | **100% (60 / 60)** | All 60 key findings across the 9 valid reports include clickable source URLs |
| **Overall Usability** | **7 High / 2 Medium / 1 Low** | All 9 completed reports serve as solid research starting points |

**Known Limitations**: Free DuckDuckGo search occasionally rate-limits with empty results, and rare queries may surface search-engine ad redirect links (e.g., `bing.com/aclick`). Both behaviors are transparently documented in `data/eval.csv`.

## Local Setup & Testing

1. **Install dependencies (Python 3.11+)**
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux:
   # source .venv/bin/activate

   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Add at least one valid API key in `.env` (`GROQ_API_KEY` recommended). All keys are loaded via environment variables and never hardcoded.

3. **Run the app**
   ```bash
   streamlit run app.py
   ```

4. **Run unit tests** (covers search timeout/empty fallback, LLM 3-tier fallback, max-round termination, and top-level error handling)
   ```bash
   pytest tests/ -v
   ```
