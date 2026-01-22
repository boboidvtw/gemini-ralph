import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

class StateManager:
    def __init__(self, db_path: str = "ralph_state.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table for chat history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        ''')

        # Table for key-value state (Circuit Breaker, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kv_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()

    def save_message(self, session_id: str, role: str, content: str):
        """Save a message to history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO history (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
            (session_id, role, content, time.time())
        )
        conn.commit()
        conn.close()

    def get_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent chat history."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            'SELECT role, content FROM history WHERE session_id = ? ORDER BY id DESC LIMIT ?',
            (session_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        # Return reversed to be in chronological order
        return [{"role": row["role"], "content": row["content"]} for row in rows][::-1]

    def save_state(self, key: str, value: Any):
        """Save an arbitrary JSON-serializable value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        serialized = json.dumps(value)
        cursor.execute(
            'INSERT OR REPLACE INTO kv_state (key, value, updated_at) VALUES (?, ?, ?)',
            (key, serialized, time.time())
        )
        conn.commit()
        conn.close()

    def get_state(self, key: str, default: Any = None) -> Any:
        """Retrieve a stored value."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT value FROM kv_state WHERE key = ?', (key,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return default
        return default
