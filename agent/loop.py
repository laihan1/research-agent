import json
import os
import re
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from agent.models import Report, Step, SearchResult
from agent.llm import complete
from agent.search import search

MAX_ROUNDS = int(os.getenv("MAX_ROUNDS", "3"))
MAX_QUERIES_PER_ROUND = int(os.getenv("MAX_QUERIES_PER_ROUND", "5"))
MAX_RESULTS_PER_QUERY = 5
DEBUG = os.getenv("DEBUG", "0") == "1"


def _log(msg: str):
    if DEBUG:
        print(f"[debug] {msg}")


def _save_run(report: Report) -> None:
    try:
        path = Path("data/runs.jsonl")
        path.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **asdict(report),
        }
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[loop] failed to save run: {e}")


def _parse_json(raw: str):
    cleaned = re.sub(r"```(?:json)?\s*", "", raw).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}|\[.*\]", cleaned, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


def _plan_queries(topic: str) -> list[str]:
    target = min(3, MAX_QUERIES_PER_ROUND)
    prompt = (
        f"You are a research planner. Generate {target} short, simple web search queries "
        f"(3-6 words each, no parentheses or long sentences) to research the topic.\n"
        f"Return ONLY a JSON array of strings. No explanation, no markdown.\n\n"
        f"Topic: {topic}"
    )
    raw = complete(prompt, temperature=0.3)
    _log(f"plan raw: {raw[:300]}")
    data = _parse_json(raw)
    if isinstance(data, list):
        queries = [q.strip() for q in data if isinstance(q, str) and q.strip()]
        return queries[:MAX_QUERIES_PER_ROUND] or [topic]
    return [topic]


def _judge(topic: str, results: list[SearchResult]) -> dict:
    if not results:
        return {"enough": False, "reason": "no results", "new_queries": [topic]}
    target = min(3, MAX_QUERIES_PER_ROUND)
    snippets = "\n".join(f"- {r.title}: {r.snippet[:150]}" for r in results[:10])
    prompt = (
        f"Topic: {topic}\n\n"
        f"Current search results ({len(results)} total):\n{snippets}\n\n"
        f"Decide if these results are sufficient for a clear, concise starter research report "
        f"(background, key findings, and any disagreements). "
        f"If the core topic is already well covered by multiple relevant sources, set enough to true. "
        f"Only if major basic gaps remain, set enough to false and propose up to {target} short keyword queries "
        f"(3-6 words each, no parentheses).\n"
        f"Return ONLY JSON: {{\"enough\": true/false, \"reason\": \"...\", \"new_queries\": [\"...\"]}}"
    )
    raw = complete(prompt, temperature=0.2)
    _log(f"judge raw: {raw[:300]}")
    data = _parse_json(raw)
    if isinstance(data, dict) and "enough" in data:
        enough = data.get("enough")
        if isinstance(enough, str):
            enough = enough.strip().lower() == "true"
        else:
            enough = bool(enough)
        new_queries = [q for q in data.get("new_queries", []) if isinstance(q, str) and q.strip()]
        return {
            "enough": enough,
            "reason": str(data.get("reason", "")),
            "new_queries": new_queries[:MAX_QUERIES_PER_ROUND],
        }
    return {"enough": True, "reason": "judge parse failed", "new_queries": []}


def _generate_report(topic: str, results: list[SearchResult]) -> dict:
    sources = "\n".join(
        f"[{i+1}] {r.title}\nURL: {r.url}\nSnippet: {r.snippet[:300]}"
        for i, r in enumerate(results[:15])
    )
    prompt = (
        f"Write a structured research report on: {topic}\n\n"
        f"Use ONLY these sources:\n{sources}\n\n"
        f"Return ONLY JSON with this schema:\n"
        f"{{\"background\": \"...\", \"findings\": [{{\"claim\": \"...\", \"source\": \"<url>\"}}], \"disagreements\": [\"...\"]}}\n"
        f"Every finding MUST cite a source URL from the list above. Provide 3-8 findings.\n"
        f"IMPORTANT: If the sources are unrelated to the topic, return an EMPTY findings array "
        f"and explain in background. Do NOT turn 'this source is unrelated' into a finding."
    )
    raw = complete(prompt, temperature=0.2)
    _log(f"generate raw (first 800 chars): {raw[:800]}")
    data = _parse_json(raw)
    if isinstance(data, dict) and "findings" in data:
        findings = data.get("findings", [])
        if isinstance(findings, list):
            return {
                "background": data.get("background", ""),
                "findings": findings,
                "disagreements": data.get("disagreements", []),
                "degraded": False,
            }
    _log("generate fallback triggered (parse failure)")
    return {
        "background": f"Research on '{topic}' based on {len(results)} sources.",
        "findings": [{"claim": f"{r.title}: {r.snippet[:200]}", "source": r.url} for r in results[:10]],
        "disagreements": [],
        "degraded": True,
    }


def run(topic: str) -> Report:
    steps: list[Step] = []
    all_results: list[SearchResult] = []
    try:
        queries = None
        last_round = 1
        consecutive_unproductive = 0
        for round_no in range(1, MAX_ROUNDS + 1):
            last_round = round_no
            t0 = time.perf_counter()
            if queries is None:
                queries = _plan_queries(topic)

            t0 = time.perf_counter()
            round_results = []
            for i, q in enumerate(queries):
                if i > 0:
                    time.sleep(1.0)
                for r in search(q, max_results=MAX_RESULTS_PER_QUERY):
                    r.round = round_no
                    round_results.append(r)
            before_urls = {r.url for r in all_results}
            all_results.extend(round_results)
            new_unique = len({r.url for r in all_results} - before_urls)
            steps.append(Step(
                round=round_no, action="search",
                input={"queries": queries},
                output={"num_results": len(round_results), "new_unique": new_unique},
                duration_ms=int((time.perf_counter() - t0) * 1000),
            ))

            t0 = time.perf_counter()
            verdict = _judge(topic, all_results)
            steps.append(Step(
                round=round_no, action="judge",
                input={"num_results": len(all_results)}, output=verdict,
                duration_ms=int((time.perf_counter() - t0) * 1000),
            ))

            if verdict["enough"]:
                break
            if not verdict["new_queries"] or new_unique == 0:
                consecutive_unproductive += 1
                _log(f"round {round_no}: unproductive (new_unique={new_unique}, "
                     f"new_queries={len(verdict['new_queries'])}), streak={consecutive_unproductive}")
                if consecutive_unproductive >= 2:
                    _log("two consecutive unproductive rounds, breaking")
                    break
            else:
                consecutive_unproductive = 0
            queries = verdict["new_queries"] or [topic]

        seen = set()
        unique = []
        for r in all_results:
            if r.url and r.url not in seen:
                seen.add(r.url)
                unique.append(r)

        if not unique:
            report = Report(topic=topic, status="degraded", steps=steps)
        else:
            t0 = time.perf_counter()
            content = _generate_report(topic, unique)
            findings = content.get("findings", [])
            steps.append(Step(
                round=last_round, action="generate",
                input={"num_sources": len(unique)},
                output={"findings": len(findings)},
                duration_ms=int((time.perf_counter() - t0) * 1000),
            ))

            status = "ok" if (findings and not content.get("degraded")) else "degraded"
            report = Report(
                topic=topic,
                background=content.get("background", ""),
                findings=findings,
                disagreements=content.get("disagreements", []),
                references=[r.url for r in unique],
                steps=steps,
                status=status,
            )
    except Exception as e:
        print(f"[loop] run failed: {e}")
        report = Report(topic=topic, status="failed", steps=steps)

    _save_run(report)
    return report