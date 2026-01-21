import os
import time
import sys
from typing import Optional
from .gemini_client import GeminiClient
from .tools import ToolSet
from .circuit_breaker import CircuitBreaker, CircuitState
from .stuck_detector import StuckDetector

class AgentLoop:
    def __init__(self, task_file: str = "@fix_plan.md"):
        self.task_file = task_file
        self.client = GeminiClient()
        self.tools = ToolSet()
        self.breaker = CircuitBreaker()
        self.stuck_detector = StuckDetector()
        self.loop_count = 0

    def run(self):
        print("\n🚀 Starting Gemini-Ralph Autonomous Agent...")
        
        while True:
            self.loop_count += 1
            print(f"\n🔄 Loop #{self.loop_count}")

            # 1. Check Circuit Breaker
            if not self.breaker.allow_request():
                print("⛔ Circuit Breaker is OPEN. Stopping execution.")
                break

            # 2. Build Context
            prompt = self._build_context()
            
            # 3. Call AI
            try:
                print("🤖 Sending request to Gemini...")
                response = self.client.send_message(prompt)
                
                # --- Stuck Detection ---
                # Combine User Prompt + Model Response + Tool Calls (if any) as the "State"
                current_state_text = ""
                try:
                    # Safely extract text if present
                    if response.parts:
                        for part in response.parts:
                            if part.text:
                                current_state_text += part.text
                            elif part.function_call:
                                current_state_text += f"[Tool: {part.function_call.name}]"
                except Exception:
                    pass # Fallback to empty if extraction fails
                
                if current_state_text and self.stuck_detector.check_is_stuck(current_state_text):
                    print("⛔ Loop Detected (Stuck). Halting execution.")
                    self.breaker.record_error("Stuck Loop Detected")
                    break
                # -----------------------

                self.breaker.record_success() # Reset consecutive errors on successful API call
            except Exception as e:
                print(f"⚠️ API Error: {e}")
                self.breaker.record_error(str(e))
                time.sleep(30) # Backoff (Increased to 30s for Free Tier Rate Limits)
                continue

            # 4. Handle Tool Calls
            tool_calls = self.client.get_tool_calls(response)
            
            if not tool_calls:
                # No tools called, just plain text response
                print(f"💬 AI: {response.text}")
                # Analyze for completion heuristics if no explicit parsed signal
                if "TASK_COMPLETE" in response.text: # Simple heuristic override
                     print("✅ Project Complete (Heuristic).")
                     break
                continue

            for tool in tool_calls:
                name = tool['name']
                args = tool['args']
                print(f"🔧 Executing Tool: {name}({args})")
                
                # Special Exit Signal
                if name == "task_completed":
                    print(f"✅ Project Complete. Summary: {args.get('summary')}")
                    return 0

                # Map Gemini tool names to ToolSet methods
                # Note: ToolSet uses capitalized names (legacy), we track mapping here or unify them
                # For this MVP, we map simple lowercase to ToolSet internal logic
                tool_result = ""
                try:
                    if name == "write_file":
                        tool_result = self.tools.write_file(args['path'], args['content'])
                    elif name == "read_file":
                        tool_result = self.tools.read_file(args['path'])
                    elif name == "run_command":
                        tool_result = self.tools.run_command(args['command'])
                    elif name == "list_dir":
                        tool_result = self.tools.list_dir(args['path'])
                        
                    print(f"   -> Result: {tool_result[:100]}...") # Truncate log
                    
                    # Send result back to Gemini (Function Chaining)
                    # Note: In a real loop, we might buffer results or handle multi-turn.
                    # Here we treat tool output as immediate feedback for next step?
                    # Actually, for Gemini, we MUST send the function_response back immediately to close the turn.
                    self.client.send_tool_result(name, tool_result)
                    
                except Exception as e:
                    error_msg = f"Tool Execution Error: {str(e)}"
                    print(f"   -> {error_msg}")
                    self.breaker.record_error(error_msg)
                    self.client.send_tool_result(name, error_msg)

    def _build_context(self) -> str:
        context = f"You are Ralph, an autonomous coding agent. Loop #{self.loop_count}.\n"
        
        # Inject Task Plan
        if os.path.exists(self.task_file):
            with open(self.task_file, 'r') as f:
                context += f"\nCurrent Plan ({self.task_file}):\n{f.read()}\n"
        else:
             context += f"\nNo {self.task_file} found. Please create one or ask me to create it.\n"

        context += "\nGoal: Complete the remaining tasks in the plan. Used tools to explore, editing, and verify.\n"
        context += "When satisfied, call the 'task_completed' tool."
        
        return context
