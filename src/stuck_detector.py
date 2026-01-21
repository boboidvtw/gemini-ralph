import os
import numpy as np
import google.generativeai as genai
from typing import List, Deque
from collections import deque
from termcolor import colored

class StuckDetector:
    """
    Detects if the agent is stuck in an infinite loop using semantic vector similarity.
    Uses Gemini's embedding model to convert agent actions/thoughts into vectors.
    """
    def __init__(self, 
                 model_name: str = "models/text-embedding-004",
                 window_size: int = 5,
                 similarity_threshold: float = 0.95):
        self.model_name = model_name
        self.history: Deque[str] = deque(maxlen=window_size)
        self.vectors: Deque[np.ndarray] = deque(maxlen=window_size)
        self.similarity_threshold = similarity_threshold
        
        # Ensure API key is configured (should be handled by main/client but good to check)
        if not os.getenv("GOOGLE_API_KEY"):
             print(colored("Warning: GOOGLE_API_KEY not set. StuckDetector disabled.", "yellow"))
             self.disabled = True
        else:
             self.disabled = False

    def check_is_stuck(self, content: str) -> bool:
        """
        Check if the current content is semantically identical to recent history.
        Returns True if stuck.
        """
        if self.disabled or not content.strip():
            return False

        try:
            # 1. Get Embedding for current content
            # Gemini embedding returns a list of floats
            result = genai.embed_content(
                model=self.model_name,
                content=content,
                task_type="semantic_similarity"
            )
            
            if not result or 'embedding' not in result:
                return False
                
            current_vector = np.array(result['embedding'])
            
            # 2. Compare with history
            is_stuck = False
            max_sim = 0.0
            
            for past_vector in self.vectors:
                sim = self._cosine_similarity(current_vector, past_vector)
                max_sim = max(max_sim, sim)
                
                if sim > self.similarity_threshold:
                    is_stuck = True
                    break
            
            # 3. Update history
            self.history.append(content)
            self.vectors.append(current_vector)
            
            if is_stuck:
                print(colored(f"\n⚠️ STUCK DETECTED! Semantic Similarity: {max_sim:.4f} > {self.similarity_threshold}", "red"))
                
            return is_stuck

        except Exception as e:
            print(colored(f"Error in StuckDetector: {e}", "yellow"))
            return False

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
            
        return dot_product / (norm_v1 * norm_v2)
