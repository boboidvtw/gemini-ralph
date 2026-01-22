import os
import time
import sys
import asyncio
import uuid
from typing import Optional
from .gemini_client import GeminiClient
from .tools import ToolSet
from .circuit_breaker import CircuitBreaker, CircuitState
from .stuck_detector import StuckDetector
from .persistence import StateManager

class AgentLoop:
    def __init__(self, task_file: str = "@fix_plan.md"):
        self.task_file = task_file
        self.client = GeminiClient()
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
            print(f"📜 Loaded {len(history)} past messages from DB.")
            # Note: In a real scenario, we might want to re-inject these into self.client.chat.history
            # For this MVP, we assume the Context Prompt is enough to ground the agent, 
            # or we rely on the fact that 'history' variable is just for us to see, 
            # but we actually need to repopulate the chat object if we wanted true conversational continuity.
            # However, since we rebuild context every loop via _build_context(), explicit chat history 
            # is less critical than the prompt itself. 
            pass

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

            for tool in tool_calls:
                name = tool['name']
                args = tool['args']
                print(f"🔧 Executing Tool: {name}({args})")
                
                if name == "task_completed":
                    print(f"✅ Project Complete. Summary: {args.get('summary')}")
                    return 0

                # Execute Tool Logic (Synchronous tools wrapped in executor if needed, 
                # but for simplicity we run them directly as file IO is fast enough)
                tool_result = ""
                try:
                    # Sync tool execution
                    if name == "write_file":
                        tool_result = self.tools.write_file(args['path'], args['content'])
                    elif name == "read_file":
                        tool_result = self.tools.read_file(args['path'])
                    elif name == "run_command":
                        # run_command might block, strictly better to await loop.run_in_executor
                        # tool_result = self.tools.run_command(args['command'])
                        loop = asyncio.get_running_loop()
                        tool_result = await loop.run_in_executor(None, self.tools.run_command, args['command'])
                    elif name == "list_dir":
                        tool_result = self.tools.list_dir(args['path'])
                        
                    print(f"   -> Result: {tool_result[:100]}...") 
                    
                    # Save Tool Result to DB (represented as User role providing info)
                    self.state_manager.save_message(self.session_id, "tool", f"Tool {name} result: {tool_result}")

                    # Send result back
                    try:
                        await self.client.send_tool_result_async(name, tool_result)
                    except Exception as e:
                        print(f"⚠️ API Error (Tool Result): {e}")
                        self.breaker.record_error(str(e))
                        await asyncio.sleep(30)
                    
                except Exception as e:
                    error_msg = f"Tool Execution Error: {str(e)}"
                    print(f"   -> {error_msg}")
                    self.breaker.record_error(error_msg)
                    try:
                        await self.client.send_tool_result_async(name, error_msg)
                    except:
                        pass

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
