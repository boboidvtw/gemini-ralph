# Gemini-Ralph

一個由 Google Gemini (Flash 2.5/2.0/1.5) 驅動的 Python 原生自主編碼 AI Agent。

## 功能特色
- **自主循環 (Autonomous Loop)**: 依據 `@fix_plan.md` 持續執行任務直到完成。
- **進階安全性**: 
    - **熔斷機制 (Circuit Breaker)**: 追蹤連續錯誤，防止 API 濫用。
    - **向量語意卡死偵測 (Vector Semantic Stuck Detection)**: 使用 Gemini Embeddings (`text-embedding-004`) 偵測 Agent 是否在語意上重複鬼打牆。
- **Gemini 強力驅動**: 利用 Gemini Flash 模型的高速與推理能力。
- **工具沙盒 (Tool Sandbox)**: 受控的檔案系統與終端機操作環境。

## 架構說明

- `src/agent_loop.py`: 大腦。負責管理 Context 注入與工具執行。
- `src/gemini_client.py`: `google-generativeai` 的封裝，定義了 Function Calling 介面。
- `src/stuck_detector.py`: 基於向量相似度的無限迴圈偵測引擎。
- `src/tools.py`: 內部工具的安全實作。
- `src/circuit_breaker.py`: 錯誤追蹤的狀態機。

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

## 速率限制 (Rate Limits) 與設定

### 為什麼執行速度較慢？
預設情況下，Agent 在發生 API 錯誤重試前會等待 **30 秒**。這是專門為 **Gemini API 免費版 (Free Tier)** 調整的設定，因為該方案有嚴格的速率限制 (約每分鐘 15 次請求)。

### 如何加速？
如果您擁有 **付費 (Pay-as-you-go)** 的 Gemini API Key，您可以縮短此延遲以獲得更快的執行速度。

修改 `src/agent_loop.py`:
```python
# src/agent_loop.py
time.sleep(30) # 付費方案可將 30 改為 1 或 0
```
