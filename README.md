# Gemini-Ralph
> **Version: 2.1.0**

> **A lightweight, fully autonomous "AI Software Engineer" (Autonomous Coding Agent)**  
> Simply write down your goal (in `@fix_plan.md`), and it will automatically: **Read code ➡️ Modify code ➡️ Run terminal commands to test ➡️ Fix its own bugs ➡️ Loop until the task is complete.** Think of it as a lightweight, local version of tools like Devin or Claude Code.

A Python-native autonomous coding agent powered by Google Gemini (Flash 2.5/2.0/1.5).

## Features
- **Autonomous Loop**: Continuously iterates on tasks until completion using `@fix_plan.md`.
- **Double Validation Protocol**: Agent strictly enforces automated core logic tests AND visual/E2E UI tests before considering a task completed.
- **Local Model Support**: Natively switch between Gemini API and OpenAI-compatible local endpoints (like Ollama or LM Studio).
- **Advanced Safety**: 
    - **Circuit Breaker**: Prevents API abuse by tracking consecutive errors.
    - **Vector Semantic Stuck Detection**: Uses Gemini Embeddings (`text-embedding-004`) to detect if the agent is semantically repeating itself.
- **Gemini Powered**: Exploits the high-speed and reasoning capabilities of Gemini Flash models.
- **Tool Sandbox**: Controlled environment for file system and terminal operations.
- **Async Core**: Fully asynchronous architecture using `asyncio` for improved concurrency.
- **State Persistence**: Uses SQLite to automatically save chat history and session state.

## Architecture

- `src/agent_loop.py`: The brain. Manages context injection and tool execution.
- `src/gemini_client.py`: Wrapper for `google-generativeai` with Function Calling definitions.
- `src/stuck_detector.py`: Vector-based similarity engine for infinite loop detection.
- `src/tools.py`: Safe implementation of internal tools.
- `src/circuit_breaker.py`: State machine for error tracking.
- `src/persistence.py`: SQLite-based state management and history retrieval.

## Generated Examples
The following files were written **entirely by the autonomous agent** during verification tests. They are **NOT** part of the core agent logic:
- `fib_gen.py`: A script generating Fibonacci numbers (Test Case #1).
- `todo_cli.py`: A command-line Todo App (Test Case #2).
- `results/`: Directory containing output from these test scripts.

## Usage
1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Set API Key**:
   Set `GOOGLE_API_KEY` in your environment or `.env` file.
3. **Execute**:
   ```bash
   python src/main.py
   ```
   *Ensure a `@fix_plan.md` exists in the working directory.*

### Running with Local Models (Ollama / LM Studio)
You can seamlessly switch Gemini-Ralph to use local LLMs (e.g., Qwen2.5-Coder, Llama-3.3) by modifying your environment variables:
```bash
PROVIDER=LOCAL
LOCAL_BASE_URL=http://localhost:11434/v1 # For Ollama (use 1234 for LM Studio)
OPENCODE_MODEL_ID=qwen2.5-coder:32b # The model name in your local instance
```
*(Note: Function calling requires strong reasoning. Models below 14B parameters may fail to format tool JSONs correctly.)*

## Rate Limits & Configuration

### Why is the loop slow?
By default, the agent waits **30 seconds** between API error retries. This is specifically tuned for the **Gemini API Free Tier**, which has a strict rate limit (approx. 15 requests per minute).

### How to speed it up?
If you have a **Paid (Pay-as-you-go)** Gemini API Key, you can reduce this delay for much faster execution.

To change the delay, edit `src/agent_loop.py`:
```python
# src/agent_loop.py
await asyncio.sleep(30) # Change 30 to 1 or 0 for paid plans
```
