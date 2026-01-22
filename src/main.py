import os
import sys
import asyncio

# Add project root to python path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent_loop import AgentLoop
from dotenv import load_dotenv

async def main_async():
    load_dotenv() # Load .env if present
    
    # Simple CLI args
    task_file = "@fix_plan.md"
    if len(sys.argv) > 1:
        task_file = sys.argv[1]
        
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found. Please set it in .env or environment variables.")
        return

    agent = AgentLoop(task_file=task_file)
    try:
        await agent.run()
    except asyncio.CancelledError:
        print("\n🛑 Agent stopped (Cancelled).")
    except Exception as e:
         print(f"\n❌ Agent Logic Error: {e}")

def main():
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user.")

if __name__ == "__main__":
    main()
