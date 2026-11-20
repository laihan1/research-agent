# AI Research Agent

輸入一個研究主題，自動進行多輪聯網搜尋並輸出帶來源引用的結構化研究報告。

## 核心設計

- **手寫 ReAct 循環**：不依賴 LangChain / LangGraph，清晰實作 `plan -> search -> judge -> generate` 流程，硬上限最多 3 輪、每輪最多 5 個查詢。
- **LLM 三級降級鏈**：依序嘗試 `Groq (openai/gpt-oss-120b)` → `Google Gemini Flash` → `OpenRouter 免費模型`，避免綁定單一供應商。
- **單一免費搜尋源**：透過 DuckDuckGo 聯網搜尋，具備超時保護與失敗降級（回傳空列表、不崩潰）。
- **固定四段結構化報告**：背景、關鍵發現（每條附來源 URL）、分歧點、參考連結，並於介面提供思考與搜尋軌跡檢視。
- **輕量持久化**：每次運行結果追加記錄於 `data/runs.jsonl`，人工評估結果保存於 `data/eval.csv`。

## Non-goals（刻意不做）

- 不做多搜索源聚合。
- 不做自動評分（評估靠人工判斷引用支持度與整體可用性）。
- 不做用戶系統、不做歷史記錄管理。
- 不綁定任何單一 LLM 供應商。

## 本地運行

1. 安裝依賴（Python 3.11+）：
   ```bash
   pip install -r requirements.txt