# Gemini-Ralph
> **版本: 2.1.0**

> **一個輕量級、全自動的「AI 開發助理工程師」 (Autonomous Coding Agent)**  
> 只要寫下你的目標 (在 `@fix_plan.md` 中)，它就會自動：**自己讀 Code ➡️ 自己改 Code ➡️ 自己下指令跑測試 ➡️ 發現報錯自己修 ➡️ 循環到任務完成為止。** 它的運作理念類似於輕量本機版的 Devin 或 Claude Code。

一個由 Google Gemini (Flash 2.5/2.0/1.5) 驅動的 Python 原生自主編碼 AI Agent。

## 功能特色
- **自主循環 (Autonomous Loop)**: 依據 `@fix_plan.md` 持續執行任務直到完成。
- **雙重驗收機制 (Double Validation)**: Agent 在回報任務完成前，強制執行「做法一 (核心邏輯自動化腳本)」與「做法二 (E2E 終端機/Web 模擬測試)」的兩階段防護機制。
- **支援本機大模型 (Ollama / LM Studio)**: 可自由切換使用 Gemini API 或是純本機的 OpenAI 相容伺服器。
- **進階安全性**: 
    - **熔斷機制 (Circuit Breaker)**: 追蹤連續錯誤，防止 API 濫用。
    - **向量語意卡死偵測 (Vector Semantic Stuck Detection)**: 使用 Gemini Embeddings (`text-embedding-004`) 偵測 Agent 是否在語意上重複鬼打牆。
- **Gemini 強力驅動**: 利用 Gemini Flash 模型的高速與推理能力。
- **工具沙盒 (Tool Sandbox)**: 受控的檔案系統與終端機操作環境。
- **異步核心 (Async Core)**: 全面升級為 `asyncio` 架構，提升並發處理能力。
- **狀態持久化 (State Persistence)**: 使用 SQLite 自動儲存對話記錄與 Session 狀態。

## 架構說明

- `src/agent_loop.py`: 大腦。負責管理 Context 注入與工具執行。
- `src/gemini_client.py`: `google-generativeai` 的封裝，定義了 Function Calling 介面。
- `src/stuck_detector.py`: 基於向量相似度的無限迴圈偵測引擎。
- `src/tools.py`: 內部工具的安全實作。
- `src/circuit_breaker.py`: 錯誤追蹤的狀態機。
- `src/persistence.py`: 基於 SQLite 的狀態管理與歷史檢索。

## 自動生成範例 (Generated Examples)
以下檔案是由 Agent 在驗證測試過程中 **完全自主撰寫** 的範例，皆 **不屬於** 本專案的核心邏輯：
- `fib_gen.py`: 產生費波那契數列的腳本 (測試案例 #1)。
- `todo_cli.py`: 命令列 Todo 清單應用程式 (測試案例 #2)。
- `results/`: 存放這些測試腳本產出的執行結果。

## 使用方法
1. **安裝依賴**:
   ```bash
   pip install -r requirements.txt
   ```
2. **設定 API Key**:
   在環境變數或 `.env` 檔案中設定 `GOOGLE_API_KEY`。
3. **執行**:
   ```bash
   python src/main.py
   ```
   *請確保工作目錄下有 `@fix_plan.md` 檔案。*

### 切換為使用本機模型 (Ollama / LM Studio)
若要讓 Gemini-Ralph 切換為使用本機伺服器的 LLM (例如 Qwen2.5-Coder 或是 Llama-3.3)，請在環境變數或 `.env` 進行以下設定：
```bash
PROVIDER=LOCAL
LOCAL_BASE_URL=http://localhost:11434/v1 # 若使用 LM Studio 請改為 http://localhost:1234/v1
OPENCODE_MODEL_ID=qwen2.5-coder:32b # 您本機模型對應的名稱
```
*(請注意：自動化 Agent 依賴極強的 Function Calling 能力，若本機模型參數低於 14B，可能會經常發生工具呼叫格式錯誤問題而卡死。)*

## 速率限制 (Rate Limits) 與設定

### 為什麼執行速度較慢？
預設情況下，Agent 在發生 API 錯誤重試前會等待 **30 秒**。這是專門為 **Gemini API 免費版 (Free Tier)** 調整的設定，因為該方案有嚴格的速率限制 (約每分鐘 15 次請求)。

### 如何加速？
如果您擁有 **付費 (Pay-as-you-go)** 的 Gemini API Key，您可以縮短此延遲以獲得更快的執行速度。

修改 `src/agent_loop.py`:
```python
# src/agent_loop.py
await asyncio.sleep(30) # 付費方案可將 30 改為 1 或 0
```
