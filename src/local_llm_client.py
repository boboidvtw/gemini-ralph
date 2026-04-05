import os
import json
from openai import AsyncOpenAI
from typing import List, Dict, Any

class LocalLLMClient:
    def __init__(self, model_name: str = "qwen2.5-coder-32b", base_url: str = None, system_instruction: str = None):
        self.system_instruction = system_instruction
        self.model_name = os.getenv("OPENCODE_MODEL_ID", model_name)
        
        if not base_url:
            # Default to LM Studio (1234) or Ollama (11434). Assuming Ollama here, configurable via .env
            base_url = os.getenv("LOCAL_BASE_URL", "http://localhost:11434/v1")
            
        self.client = AsyncOpenAI(api_key="ollama", base_url=base_url)
        
        # OpenAI Compatible Tool Format
        self.tools_def = [
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file. Creates directories if needed.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "content": {"type": "string", "description": "Content to write"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read content from a file.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"}
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "run_command",
                    "description": "Run a shell command.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Command to execute"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                 "type": "function",
                 "function": {
                     "name": "list_dir",
                     "description": "List files in a directory.",
                     "parameters": {
                         "type": "object",
                         "properties": {
                             "path": {"type": "string", "description": "Directory path"}
                         },
                         "required": ["path"]
                     }
                 }
            },
            {
                "type": "function",
                "function": {
                    "name": "task_completed",
                    "description": "Signal that the current task or project is complete.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "summary": {"type": "string", "description": "Summary of work done"}
                        },
                        "required": ["summary"]
                    }
                }
            }
        ]
        
        self.history = []
        if self.system_instruction:
            self.history.append({"role": "system", "content": self.system_instruction})

    def load_history(self, db_history: List[Dict[str, Any]]):
        """Restore chat history from database simple format."""
        self.history = []
        if self.system_instruction:
            self.history.append({"role": "system", "content": self.system_instruction})
            
        for msg in db_history:
            role = msg["role"]
            if role == "tool":
                continue # Simple restoration skips tools for now to avoid ID mismatches
            self.history.append({"role": role, "content": msg["content"]})

    async def send_message_async(self, message: str) -> Any:
        self.history.append({"role": "user", "content": message})
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=self.history,
                tools=self.tools_def,
                tool_choice="auto"
            )
            return response
        except Exception as e:
            print(f"Local LLM API Error: {e}")
            raise

    def get_tool_calls(self, response) -> List[Dict[str, Any]]:
        """Extract tool calls from OpenAI's response format"""
        calls = []
        message = response.choices[0].message
        
        # Crucial for OpenAI: We must append the model's message that requested the tool call
        self.history.append(message)
        
        if message.tool_calls:
            for tool_call in message.tool_calls:
                # Try parsing arguments safely
                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    print(f"Warning: Failed to parse JSON for {tool_call.function.name}")
                    args = {}
                    
                calls.append({
                    "id": tool_call.id,
                    "name": tool_call.function.name,
                    "args": args
                })
        else:
            # If no tools, it's a regular text response, save it
            pass
            
        # Give API response pseudo-property to match gemini style access in main loop
        response.text = message.content or ""
        return calls
    
    async def send_tool_results_async(self, results: List[Dict[str, Any]]):
        """Append tool results to history for Local LLMs."""
        for res in results:
            self.history.append({
                "role": "tool",
                "tool_call_id": res.get("id", ""),
                "name": res["name"],
                "content": str(res["result"])
            })
        
        # Local model doesn't auto-resolve upon adding tool result like Gemini does.
        # It relies on the next main loop sending a generic 'Continuing execution' message
        # or we could force a completion generation here.
        # For compatibility with `agent_loop.py`, we just store it. 
        # The main loop continues and prints Loop #.
