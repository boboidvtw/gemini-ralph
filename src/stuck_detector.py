import os
from typing import List, Deque
from collections import deque
from termcolor import colored

class StuckDetector:
    """
    Detects if the agent is stuck in an infinite loop using exact matching of consecutive actions.
    This saves API tokens compared to semantic vector embeddings.
    """
    def __init__(self, window_size: int = 4):
        self.history: Deque[str] = deque(maxlen=window_size)
        self.disabled = False
        
    def check_is_stuck(self, content: str) -> bool:
        """
        Check if the current content is identical to the past 'window_size' history entries.
        Returns True if stuck.
        """
        if self.disabled or not content.strip():
            return False

        is_stuck = False
        try:
            # Check if all elements in a full history are exactly the same as the current content
            if len(self.history) == self.history.maxlen:
                if all(past_content == content for past_content in self.history):
                    is_stuck = True
            
            self.history.append(content)
            
            if is_stuck:
                print(colored(f"\n⚠️ STUCK DETECTED! Exact repetition detected over {self.history.maxlen} consecutive turns.", "red"))
                
            return is_stuck

        except Exception as e:
            print(colored(f"Error in StuckDetector: {e}", "yellow"))
            return False

