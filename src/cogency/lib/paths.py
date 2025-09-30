from pathlib import Path


def get_cogency_dir(base_dir: str = None) -> Path:
    if base_dir:
        cogency_dir = Path(base_dir)
    else:
        cogency_dir = Path(".cogency")
    cogency_dir.mkdir(exist_ok=True)
    return cogency_dir


class Paths:
    @staticmethod
    def db(subpath: str = None, base_dir: str = None) -> Path:
        base = get_cogency_dir(base_dir) / "store.db"
        return base / subpath if subpath else base

    @staticmethod
    def sandbox(subpath: str = None, base_dir: str = None) -> Path:
        base = get_cogency_dir(base_dir) / "sandbox"
        base.mkdir(exist_ok=True)
        return base / subpath if subpath else base

    @staticmethod
    def evals(subpath: str = None, base_dir: str = None) -> Path:
        base = get_cogency_dir(base_dir) / "evals"
        base.mkdir(exist_ok=True)
        return base / subpath if subpath else base
