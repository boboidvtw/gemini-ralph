# Gemini-Ralph

A Python-native autonomous coding agent powered by Google Gemini (Flash 2.5/2.0/1.5).

## Features
- **Autonomous Loop**: Continuously iterates on tasks until completion using `@fix_plan.md`.
- **Advanced Safety**: 
    - **Circuit Breaker**: Prevents API abuse by tracking consecutive errors.
    - **Vector Semantic Stuck Detection**: Uses Gemini Embeddings (`text-embedding-004`) to detect if the agent is semantically repeating itself.
- **Gemini Powered**: Exploits the high-speed and reasoning capabilities of Gemini Flash models.
- **Tool Sandbox**: Controlled environment for file system and terminal operations.

## Architecture

- `src/agent_loop.py`: The brain. Manages context injection and tool execution.
- `src/gemini_client.py`: Wrapper for `google-generativeai` with Function Calling definitions.
- `src/stuck_detector.py`: Vector-based similarity engine for infinite loop detection.
- `src/tools.py`: Safe implementation of internal tools.
- `src/circuit_breaker.py`: State machine for error tracking.

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

## Rate Limits & Configuration

### Why is the loop slow?
By default, the agent waits **30 seconds** between API error retries. This is specifically tuned for the **Gemini API Free Tier**, which has a strict rate limit (approx. 15 requests per minute).

### How to speed it up?
If you have a **Paid (Pay-as-you-go)** Gemini API Key, you can reduce this delay for much faster execution.

To change the delay, edit `src/agent_loop.py`:
```python
# src/agent_loop.py
time.sleep(30) # Change 30 to 1 or 0 for paid plans
```
