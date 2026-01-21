# Gemini-Ralph

A Python-native port of the Ralph autonomous development loop, powered by Google Gemini.

## Features
- **Autonomous Loop**: Continuously iterates on tasks until completion.
- **Safety First**: Integrated Circuit Breaker to prevent infinite loops and API overuse.
- **Gemini Powered**: Uses Gemini 1.5 Pro for high-reasoning capabilities.
- **Tool Sandbox**: Controlled environment for file system and terminal operations.

## Usage
1. Set `GOOGLE_API_KEY` in your environment.
2. Create a `@fix_plan.md` file with your tasks.
3. Run `python src/main.py`.
