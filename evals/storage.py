"""Run persistence - full trace retention."""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import CONFIG


def save_run(results: dict, run_id: str = None) -> Path:
    """Save evaluation run."""
    run_id = run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir = CONFIG.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    with open(run_dir / "evaluation.json", "w") as f:
        json.dump(results, f, indent=2)

    for category in results.get("categories", []):
        with open(run_dir / f"{category['category']}.json", "w") as f:
            json.dump(category, f, indent=2)

    return run_dir
