import json
import os
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitStats(BaseModel):
    error_count: int = 0
    consecutive_errors: int = 0
    total_loops: int = 0
    state: CircuitState = CircuitState.CLOSED
    last_error_time: Optional[datetime] = None

class CircuitBreaker:
    def __init__(self, 
                 state_file: str = ".circuit_breaker_state.json",
                 error_threshold: int = 5, 
                 reset_timeout_seconds: int = 300):
        self.state_file = state_file
        self.error_threshold = error_threshold
        self.reset_timeout = reset_timeout_seconds
        self.stats = self._load_state()

    def _load_state(self) -> CircuitStats:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Handle datetime deserialization if needed, mostly redundant with Pydantic mode='json'
                    if data.get('last_error_time'):
                        data['last_error_time'] = datetime.fromisoformat(data['last_error_time'])
                    return CircuitStats(**data)
            except Exception:
                pass
        return CircuitStats()

    def _save_state(self):
        with open(self.state_file, 'w') as f:
            # Dump with datetime serialization
            data = self.stats.model_dump(mode='json')
            json.dump(data, f, indent=2)

    def record_error(self, error_msg: str):
        self.stats.error_count += 1
        self.stats.consecutive_errors += 1
        self.stats.last_error_time = datetime.now()
        
        if self.stats.consecutive_errors >= self.error_threshold:
            self.stats.state = CircuitState.OPEN
            print(f"⛔ Circuit Breaker TRIPPED! Too many errors ({self.stats.consecutive_errors})")
        
        self._save_state()

    def record_success(self):
        if self.stats.state == CircuitState.HALF_OPEN:
            self.stats.state = CircuitState.CLOSED
            self.stats.consecutive_errors = 0
            print("✅ Circuit Breaker RECOVERED.")
        elif self.stats.state == CircuitState.CLOSED:
            # Only reset consecutive errors on success in CLOSED state
            self.stats.consecutive_errors = 0
        
        self.stats.total_loops += 1
        self._save_state()

    def allow_request(self) -> bool:
        if self.stats.state == CircuitState.CLOSED:
            return True
        
        if self.stats.state == CircuitState.OPEN:
            if not self.stats.last_error_time:
                return True # Should not happen if OPEN, but safe fallback
            
            elapsed = (datetime.now() - self.stats.last_error_time).total_seconds()
            if elapsed > self.reset_timeout:
                self.stats.state = CircuitState.HALF_OPEN
                print("⚠️ Circuit Breaker HALF-OPEN: Testing recovery...")
                self._save_state()
                return True
            
            return False
            
        if self.stats.state == CircuitState.HALF_OPEN:
            # Allow 1 request to test (simplified logic usually handled by allowing 1 and then checking result)
            return True
            
        return True

    def get_state_summary(self) -> str:
        return f"State: {self.stats.state.value}, Consecutive Errors: {self.stats.consecutive_errors}"
