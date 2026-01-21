# Gemini-Ralph

A Python-native port of the Ralph autonomous development loop, powered by Google Gemini (1.5 Pro).

## Features
- **Autonomous Loop**: Continuously iterates on tasks until completion using `@fix_plan.md`.
- **Advanced Safety**: 
    - **Circuit Breaker**: Prevents API abuse by tracking consecutive errors.
    - **Vector Semantic Stuck Detection**: Uses Gemini Embeddings (`text-embedding-004`) to detect if the agent is semantically repeating itself (Cosine Similarity > 0.95), effectively halting infinite loops even if the output text varies slightly.
- **Gemini Powered**: Exploits the high-reasoning capabilities of Gemini 1.5 Pro.
- **Tool Sandbox**: Controlled environment for file system and terminal operations.

## Architecture

- `src/agent_loop.py`: The brain. Manages context injection and tool execution.
- `src/gemini_client.py`: Wrapper for `google-generativeai` with Function Calling definitions.
- `src/stuck_detector.py`: **[NEW]** Vector-based similarity engine for infinite loop detection.
- `src/tools.py`: Safe implementation of file/terminal internal tools.
- `src/circuit_breaker.py`: State machine for error tracking (CLOSED/OPEN/HALF_OPEN).

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
