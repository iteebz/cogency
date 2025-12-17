import re
import sqlite3
from pathlib import Path

from cogency.lib.sqlite import DB


def test_no_phantom_table_references():
    """Verify SQL table references in code match schema."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(DB._schema_sql())

    schema_tables = {
        row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    conn.close()

    assert schema_tables == {"messages", "events", "profiles"}

    repo_root = Path(__file__).parent.parent.parent.parent

    sql_files = [
        repo_root / "src" / "cogency" / "lib" / "sqlite.py",
        repo_root / "tests" / "unit" / "lib" / "test_sqlite.py",
    ]

    violations = []

    for py_file in sql_files:
        if not py_file.exists():
            continue

        content = py_file.read_text()

        for line_num, line in enumerate(content.splitlines(), 1):
            if not any(kw in line.upper() for kw in ["SELECT", "INSERT", "DELETE", "UPDATE"]):
                continue

            for keyword in ["FROM", "INTO", "UPDATE"]:
                pattern = rf"{keyword}\s+(\w+)"
                for match in re.finditer(pattern, line, re.IGNORECASE):
                    table = match.group(1).lower()

                    if table not in schema_tables and table not in {
                        "sqlite_master",
                        "where",
                        "order",
                        "limit",
                        "group",
                        "values",
                    }:
                        violations.append(
                            f"{py_file.relative_to(repo_root)}:{line_num} - '{table}'"
                        )

    assert not violations, "Phantom tables:\n" + "\n".join(violations)
