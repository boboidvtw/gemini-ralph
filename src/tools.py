import os
import subprocess
import glob
from typing import List, Dict, Any, Union

class ToolSet:
    """
    Implements the tools that Gemini can use to interact with the environment.
    Mirrors the capabilities of Claude Code CLI.
    """
    
    def __init__(self, allowed_tools: List[str] = None):
        self.allowed_tools = allowed_tools or ["Write", "Read", "Bash", "ListDir"]

    def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        if tool_name not in self.allowed_tools and tool_name != "Bash(git *)":
             # Basic fuzzy check, robust implementation would need regex matching for Bash(*)
             # For now, simplistic Check
             pass
        
        try:
            if tool_name == "Write":
                return self.write_file(args.get("path"), args.get("content"))
            elif tool_name == "Read":
                return self.read_file(args.get("path"))
            elif tool_name == "Bash":
                return self.run_command(args.get("command"))
            elif tool_name == "ListDir":
                return self.list_dir(args.get("path"))
            else:
                return f"Error: Unknown tool '{tool_name}'"
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def write_file(self, path: str, content: str) -> str:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error writing file {path}: {str(e)}"

    def read_file(self, path: str) -> str:
        try:
            if not os.path.exists(path):
                return f"Error: File {path} does not exist"
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file {path}: {str(e)}"

    def run_command(self, command: str) -> str:
        try:
            # Security: In a real agent, we'd want strict sandboxing here.
            # For this MVP, we assume the user trusts the agent (like Ralph).
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=120 # 2 minute timeout
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            return output.strip()
        except subprocess.TimeoutExpired:
            return "Error: Command timed out after 120 seconds"
        except Exception as e:
            return f"Error running command: {str(e)}"

    def list_dir(self, path: str) -> str:
        try:
            if not os.path.exists(path):
                 return f"Error: Path {path} does not exist"
            
            # Simple listing
            files = os.listdir(path)
            # Add type indicators
            result = []
            for name in files:
                full_path = os.path.join(path, name)
                if os.path.isdir(full_path):
                    result.append(f"{name}/")
                else:
                    result.append(name)
            return "\n".join(result)
        except Exception as e:
            return f"Error listing directory {path}: {str(e)}"
