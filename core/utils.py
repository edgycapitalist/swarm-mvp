"""
Utility functions for SWARM
"""
import hashlib
import json


def compute_hash(data: dict) -> str:
    """Compute a stable hash for a dictionary"""
    json_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_str.encode()).hexdigest()[:16]


def safe_json_loads(text: str, default=None):
    """Safely parse JSON with a default fallback"""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else {}