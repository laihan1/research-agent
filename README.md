# AI Research Agent

> **在线体验（Live Demo）**：[https://laihan1-research-agent.streamlit.app/](https://laihan1-research-agent.streamlit.app/)

输入一个研究主题，自动执行多轮联网搜索、信息充分性判断与来源汇总，输出带可点击引用链接的结构化研究报告。

---

## 核心设计

- **手写 ReAct 循环**：不依赖 LangChain / LangGraph，清晰实现 `plan -> search -> judge -> generate` 主循环，硬上限最多 **3 轮**、每轮最多 **5 个查询**。
- **LLM 三级降级链**：严格按 `Groq (openai/gpt-oss-120b)` → `Google Gemini Flash` → `OpenRouter 免费模型` 顺序自动切换，全部不可用时抛出统一异常 `LLMUnavailable`，避免绑定单一供应商。
- **单一免费搜索源与容错**：基于 DuckDuckGo 联网搜索，带超时控制与重试；失败时记录日志并返回空列表，绝不向上抛异常导致崩溃。
- **固定四段结构化报告**：输出「背景 / 关键发现（每条附来源 URL）/ 分歧点 / 参考链接」，并在 UI 中展示完整执行轨迹。
- **轻量持久化与可追溯**：每次运行追加记录到 `data/runs.jsonl`，10 主题人工评估记录保存在 `data/eval.csv`。

## 架构流程

```text
User Topic (Streamlit UI: app.py)
        │
        ▼
  agent/loop.py :: run(topic) -> Report   (唯一入口，异常兜底转为 status='failed')
        │
        ├── 1. Plan 查询规划 (agent/llm.py: Groq -> Gemini -> OpenRouter)
        │
        ├── 2. Search 联网搜索 (agent/search.py: DuckDuckGo, 超时/失败返回 [])
        │        └─ 硬上限：最多 3 轮，每轮最多 5 个查询
        │
        ├── 3. Judge 信息充分性判断
        │        ├─ 信息足够 / 连续无新增来源 / 达最大轮数 ──▶ 进入生成
        │        └─ 信息不足 ──▶ 生成新关键词，进入下一轮 Search
        │
        └── 4. Generate 生成四段报告 (无来源或解析兜底标记 status='degraded')
                 │
                 ▼
         追加日志至 data/runs.jsonl & 返回 Report
