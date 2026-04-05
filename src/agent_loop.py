import os
import time
import sys
import asyncio
import uuid
from typing import Optional
from .gemini_client import GeminiClient
from .local_llm_client import LocalLLMClient
from .tools import ToolSet
from .circuit_breaker import CircuitBreaker, CircuitState
from .stuck_detector import StuckDetector
from .persistence import StateManager

class AgentLoop:
    def __init__(self, task_file: str = "@fix_plan.md"):
        self.task_file = task_file
        
        # Build strict system instruction with the task plan
        system_instruction = "You are Ralph, an autonomous coding agent.\n"
        if os.path.exists(self.task_file):
            with open(self.task_file, 'r') as f:
                system_instruction += f"\nCurrent Plan ({self.task_file}):\n{f.read()}\n"
        else:
             system_instruction += f"\nNo {self.task_file} found. Please create one or ask me to create it.\n"
        system_instruction += """
Goal: Complete the remaining tasks in the plan. Use your tools to explore, edit, and verify.
CRITICAL RULE (Double Validation Protocol): Before calling 'task_completed', you MUST systematically verify your work in two phases (if applicable to the task):
1. Phase 1 (Core/Logic): Write & run automated scripts (e.g. pytest) via run_command to verify internal logic. If errors exist, fix the code and retest until green.
2. Phase 2 (E2E/UI): Once Phase 1 passes, use UI testing tools (e.g. Playwright) or compiled simulations to verify the final end-user result.
If Phase 2 fails, you must go back, fix the core codebase, and restart verification strictly from Phase 1.
Only call 'task_completed' when all tests consecutively pass perfectly without errors.
"""

        provider = os.getenv("PROVIDER", "GEMINI").upper()
        if provider == "LOCAL":
            print("🔌 Selected Engine: Local LLM Server (Ollama / LM Studio)")
            self.client = LocalLLMClient(system_instruction=system_instruction)
        else:
            print("🔌 Selected Engine: Google Gemini API")
            self.client = GeminiClient(system_instruction=system_instruction)
            
        self.tools = ToolSet()
        self.breaker = CircuitBreaker()
        self.stuck_detector = StuckDetector()
        self.state_manager = StateManager()
        
        # Load or create session
        self.session_id = self.state_manager.get_state("current_session_id")
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
            self.state_manager.save_state("current_session_id", self.session_id)
            print(f"🆕 New Session ID: {self.session_id}")
        else:
            print(f"📂 Resuming Session ID: {self.session_id}")

        self.loop_count = self.state_manager.get_state("loop_count", 0)

    async def run(self):
        print("\n🚀 Starting Gemini-Ralph Autonomous Agent (Async Mode)...")
        
        # Restore History if resuming
        history = self.state_manager.get_history(self.session_id)
        if history:
            print(f"📜 Loaded {len(history)} past messages from DB. Restoring context...")
            self.client.load_history(history)

        while True:
            self.loop_count += 1
            self.state_manager.save_state("loop_count", self.loop_count)
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
                # Save User Prompt to DB
                self.state_manager.save_message(self.session_id, "user", prompt)
                
                response = await self.client.send_message_async(prompt)
                
                # Save Model Response Text (simplified for DB)
                if response.text:
                   self.state_manager.save_message(self.session_id, "model", response.text)

                # --- Stuck Detection ---
                current_state_text = ""
                try:
                    if response.parts:
                        for part in response.parts:
                            if part.text:
                                current_state_text += part.text
                            elif part.function_call:
                                current_state_text += f"[Tool: {part.function_call.name}]"
                except Exception:
                    pass
                
                if current_state_text and self.stuck_detector.check_is_stuck(current_state_text):
                    print("⛔ Loop Detected (Stuck). Halting execution.")
                    self.breaker.record_error("Stuck Loop Detected")
                    break
                # -----------------------

                self.breaker.record_success() 
            except Exception as e:
                print(f"⚠️ API Error: {e}")
                self.breaker.record_error(str(e))
                await asyncio.sleep(30) # Async Sleep
                continue

            # 4. Handle Tool Calls
            tool_calls = self.client.get_tool_calls(response)
            
            if not tool_calls:
                print(f"💬 AI: {response.text}")
                if "TASK_COMPLETE" in response.text:
                     print("✅ Project Complete (Heuristic).")
                     break
                continue

            tool_results_to_send = []
            for tool in tool_calls:
                name = tool['name']
                args = tool['args']
                print(f"🔧 Executing Tool: {name}({args})")
                
                if name == "task_completed":
                    print(f"✅ Project Complete. Summary: {args.get('summary')}")
                    return 0

                # Execute Tool Logic
                tool_result = ""
                try:
                    # Sync tool execution
                    if name == "write_file":
                        tool_result = self.tools.write_file(args['path'], args['content'])
                    elif name == "read_file":
                        tool_result = self.tools.read_file(args['path'])
                    elif name == "run_command":
                        loop = asyncio.get_running_loop()
                        tool_result = await loop.run_in_executor(None, self.tools.run_command, args['command'])
                    elif name == "list_dir":
                        tool_result = self.tools.list_dir(args['path'])
                        
                    print(f"   -> Result: {tool_result[:100]}...") 
                    
                    # Save Tool Result to DB
                    self.state_manager.save_message(self.session_id, "tool", f"Tool {name} result: {tool_result}")

                    tool_results_to_send.append({"id": tool.get("id"), "name": name, "result": str(tool_result)})
                    
                except Exception as e:
                    error_msg = f"Tool Execution Error: {str(e)}"
                    print(f"   -> {error_msg}")
                    self.breaker.record_error(error_msg)
                    tool_results_to_send.append({"id": tool.get("id"), "name": name, "result": error_msg})

            # Send ALL results back at once to comply with Gemini API's conversational rhythm
            if tool_results_to_send:
                try:
                    await self.client.send_tool_results_async(tool_results_to_send)
                except Exception as e:
                    print(f"⚠️ API Error (Tool Result): {e}")
                    self.breaker.record_error(str(e))
                    await asyncio.sleep(30)

    def _build_context(self) -> str:
        # Instead of bloating the history with the full plan every turn,
        # we configure the plan as a system_instruction and just send a short ping to continue.
        if self.loop_count == 1:
            return f"Agent initialized. Loop #{self.loop_count}. Please review the plan in your system instructions and begin."
        else:
            return f"Continuing execution. Loop #{self.loop_count}. Please analyze your previous results and take the next step."
