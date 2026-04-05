import os
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from typing import List, Dict, Any, Optional
import asyncio

class GeminiClient:
    def __init__(self, model_name: str = "gemini-flash-latest", api_key: str = None, system_instruction: str = None):
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        self.system_instruction = system_instruction
        
        # Define Tools for Gemini Function Calling
        self.tools_def = [
            {
                "name": "write_file",
                "description": "Write content to a file. Creates directories if needed.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {"type": "STRING", "description": "File path"},
                        "content": {"type": "STRING", "description": "Content to write"}
                    },
                    "required": ["path", "content"]
                }
            },
            {
                "name": "read_file",
                "description": "Read content from a file.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "path": {"type": "STRING", "description": "File path"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "run_command",
                "description": "Run a shell command.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "command": {"type": "STRING", "description": "Command to execute"}
                    },
                    "required": ["command"]
                }
            },
            {
                 "name": "list_dir",
                 "description": "List files in a directory.",
                 "parameters": {
                     "type": "OBJECT",
                     "properties": {
                         "path": {"type": "STRING", "description": "Directory path"}
                     },
                     "required": ["path"]
                 }
            },
            {
                "name": "task_completed",
                "description": "Signal that the current task or project is complete.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "summary": {"type": "STRING", "description": "Summary of work done"}
                    },
                    "required": ["summary"]
                }
            }
        ]
        
        kwargs = {"model_name": model_name, "tools": self.tools_def}
        if self.system_instruction:
            kwargs["system_instruction"] = self.system_instruction
        self.model = genai.GenerativeModel(**kwargs)
        # Note: history=[] means we start fresh, but we can load history if needed manually
        self.chat = self.model.start_chat(enable_automatic_function_calling=False)

    def load_history(self, db_history: List[Dict[str, Any]]):
        """Restore chat history from database simple format."""
        formatted_history = []
        for msg in db_history:
            # Map simplified DB roles to Gemini API roles ("user" or "model")
            role = "user" if msg["role"] in ["user", "tool"] else "model"
            formatted_history.append({"role": role, "parts": [msg["content"]]})
        self.chat = self.model.start_chat(enable_automatic_function_calling=False, history=formatted_history)

    async def send_message_async(self, message: str) -> Any:
        try:
            response = await self.chat.send_message_async(message)
            return response
        except Exception as e:
            print(f"Gemini API Error: {e}")
            raise

    def get_tool_calls(self, response) -> List[Dict[str, Any]]:
        """Extract tool calls from response candidate"""
        calls = []
        if not response.candidates:
            return calls
            
        for part in response.candidates[0].content.parts:
            if part.function_call:
                calls.append({
                    "name": part.function_call.name,
                    "args": dict(part.function_call.args)
                })
        return calls
    
    async def send_tool_results_async(self, results: List[Dict[str, Any]]):
        """Send multiple tool execution results back to Gemini asynchronously in a single turn."""
        parts = []
        for res in results:
            parts.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=res["name"],
                        response={"result": res["result"]} 
                    )
                )
            )
        await self.chat.send_message_async(genai.protos.Content(parts=parts))
