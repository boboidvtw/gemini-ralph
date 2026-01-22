import asyncio
import sys
import os
import sqlite3

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent_loop import AgentLoop
from src.persistence import StateManager
from dotenv import load_dotenv

async def test_smoke():
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️ No API Key found, using dummy for structural test")
        os.environ["GOOGLE_API_KEY"] = "TEST_DUMMY_KEY"
        
    print("🧪 Starting Smoke Test...")
    
    # 1. Initialize StateManager
    db_path = "ralph_state.db"
    if os.path.exists(db_path):
        os.remove(db_path) # Clean start
        print("   - Removed old DB")

    mgr = StateManager(db_path=db_path)
    print("   - StateManager initialized (DB created)")
    
    # 2. Check DB Schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"   - Tables found: {tables}")
    assert "history" in tables
    assert "kv_state" in tables
    conn.close()

    # 3. Initialize AgentLoop (Mocking run to avoid infinite loop or API cost)
    agent = AgentLoop()
    print(f"   - AgentLoop initialized with Session ID: {agent.session_id}")
    
    # Verify Session ID saved
    saved_id = mgr.get_state("current_session_id")
    assert saved_id == agent.session_id
    print("   - Session ID verification passed")

    print("✅ Smoke Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_smoke())
