"""Global paths configuration - ONE canonical instance."""

import os
from pathlib import Path


class _Paths:
    """Global paths singleton - no ceremony, just works."""

    def __init__(self):
        # Allow .env override of base directory
        env_base_dir = os.getenv("COGENCY_BASE_DIR")
        base = Path(env_base_dir if env_base_dir else ".cogency").expanduser()

        self.base_dir = str(base)
        self.sandbox = str(base / "sandbox")
        self.state = str(base / "state")
        self.memory = str(base / "memory")
        self.logs = str(base / "logs")
        self.reports = str(base / "reports")
        self.evals = str(base / "evals")


# ONE global instance - import and use everywhere
paths = _Paths()
