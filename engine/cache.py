"""Deterministic Disk Cache for LLM Calls.

Rule R8: All LLM calls cached by input hash. The demo runs from cache.
Full flow works from cache with the network off.
"""

import os
import json
import hashlib
from typing import Optional, Dict, Any

CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cache")


def get_cache_key(prompt: str, model: str = "gemini-2.5-flash", **kwargs) -> str:
    """Generates a stable SHA-256 hash for given prompt and configuration."""
    content = f"{model}::{prompt.strip()}"
    if kwargs:
        content += f"::{json.dumps(kwargs, sort_keys=True)}"
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class DiskCache:
    def __init__(self, cache_dir: str = CACHE_DIR):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        file_path = os.path.join(self.cache_dir, f"{key}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set(self, key: str, value: Dict[str, Any]) -> None:
        file_path = os.path.join(self.cache_dir, f"{key}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(value, f, indent=2)
        except Exception:
            pass

    def clear(self) -> None:
        if os.path.exists(self.cache_dir):
            for fname in os.listdir(self.cache_dir):
                if fname.endswith(".json"):
                    try:
                        os.remove(os.path.join(self.cache_dir, fname))
                    except Exception:
                        pass
