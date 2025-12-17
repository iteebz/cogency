import json
import time
from pathlib import Path

from .uuid7 import uuid7


def log_response(conversation_id: str, model: str, response: str):
    if not response:
        return

    debug_path = Path(".cogency/debug") / f"{conversation_id}.jsonl"
    debug_path.parent.mkdir(parents=True, exist_ok=True)

    entry = {
        "request_id": uuid7(),
        "timestamp": time.time(),
        "model": model,
        "response": response,
    }

    with debug_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")
