import os
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool
from typing import List, Dict, Any, Optional

class GeminiClient:
    def __init__(self, model_name: str = "gemini-1.5-pro", api_key: str = None):
        if not api_key:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        
        # Define Tools for Gemini Function Calling
        self.tools_def = [
            {
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
            },
            {
                "name": "read_file",
                "description": "Read content from a file.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "run_command",
                "description": "Run a shell command.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Command to execute"}
                    },
                    "required": ["command"]
                }
            },
            {
                 "name": "list_dir",
                 "description": "List files in a directory.",
                 "parameters": {
                     "type": "object",
                     "properties": {
                         "path": {"type": "string", "description": "Directory path"}
                     },
                     "required": ["path"]
                 }
            },
            {
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
        ]
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=[genai.Tool(function_declarations=self.tools_def)]
        )
        self.chat = self.model.start_chat(enable_automatic_function_calling=False) # We handle execution manually for safety

    def send_message(self, message: str) -> Any:
        try:
            response = self.chat.send_message(message)
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
    
    def send_tool_result(self, tool_name: str, result: str):
        """Send tool execution result back to Gemini"""
        # In the new SDK, we send a Part with function_response
        self.chat.send_message(
            genai.protos.Content(
                parts=[genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=tool_name,
                        response={"result": result} 
                    )
                )]
            )
        )
