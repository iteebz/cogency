"""SQL database tool for executing queries across multiple database types."""

import asyncio
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class SQLArgs:
    query: str
    connection: str
    timeout: int = 30
    params: Optional[List] = None


@tool
class SQL(Tool):
    """Execute SQL queries across multiple database types with connection management."""

    def __init__(self):
        super().__init__(
            name="sql",
            description="Execute SQL queries on SQLite, PostgreSQL, MySQL databases with connection string support",
            schema="sql(query=str, connection=str, timeout=int, params=list)",
            emoji="🗄️",
            params=SQLArgs,
            examples=[
                "sql(query='SELECT * FROM users', connection='sqlite:///database.db')",
                "sql(query='CREATE TABLE logs (id INTEGER PRIMARY KEY, message TEXT)', connection='sqlite:///app.db')",
                "sql(query='SELECT COUNT(*) as total FROM orders', connection='postgresql://user:pass@localhost/shop')",
                "sql(query='INSERT INTO users (name, email) VALUES (?, ?)', connection='sqlite:///app.db', params=['John', 'john@example.com'])",
            ],
            rules=[
                "Use parameterized queries with 'params' parameter to prevent SQL injection.",
                "SQLite uses ? placeholders, PostgreSQL uses $1, $2, etc.",
                "Always specify connection string with proper database URL format (e.g., 'sqlite:///path/to/db.db', 'postgresql://user:pass@host:port/db').",
                "Queries are auto-committed for modification operations.",
                "Ensure the database type (e.g., 'sqlite', 'postgresql', 'mysql') is correctly specified in the connection string scheme.",
            ],
        )
        # Beautiful dispatch pattern - extensible database support
        self._drivers = {
            "sqlite": self._execute_sqlite,
            "postgresql": self._execute_postgresql,
            "postgres": self._execute_postgresql,  # Alias
            "mysql": self._execute_mysql,
        }

    async def run(
        self,
        query: str,
        connection: str,
        timeout: int = 30,
        params: Optional[List] = None,
        **kwargs,
    ) -> Result:
        """Execute SQL query using dispatch pattern.
        Args:
            query: SQL query to execute
            connection: Database connection string (sqlite:///path, postgresql://..., mysql://...)
            timeout: Query timeout in seconds (default: 30)
            params: Optional query parameters for prepared statements
        Returns:
            Query results including rows, columns, and metadata
        """
        # Schema validation handles required params
        # Parse connection string to determine driver
        try:
            parsed = urlparse(connection)
            driver = parsed.scheme.lower()
        except Exception as e:
            logger.error(f"Context: {e}")
            return Result.fail("Invalid connection string format")
        if driver not in self._drivers:
            available = ", ".join(set(self._drivers.keys()))
            return Result.fail(f"Unsupported database driver. Use: {available}")
        # Limit timeout
        timeout = min(max(timeout, 1), 300)  # 1-300 seconds for DB queries
        # Dispatch to appropriate database handler
        executor = self._drivers[driver]
        return await executor(query, connection, timeout, params or [])

    async def _execute_sqlite(
        self, query: str, connection: str, timeout: int, params: List
    ) -> Result:
        """Execute SQLite query."""
        try:
            # Parse SQLite path from connection string
            parsed = urlparse(connection)
            db_path = parsed.path
            # Handle in-memory databases
            if db_path == ":memory:" or not db_path:
                db_path = ":memory:"
            else:
                # Ensure directory exists for file databases
                Path(db_path).parent.mkdir(parents=True, exist_ok=True)

            # Execute in thread pool to avoid blocking
            def _sync_execute():
                conn = sqlite3.connect(db_path, timeout=timeout)
                conn.row_factory = sqlite3.Row  # Enable column access by name
                try:
                    cursor = conn.execute(query, params)
                    # Handle different query types
                    if query.strip().upper().startswith(("SELECT", "WITH", "PRAGMA")):
                        # Query returns results
                        rows = cursor.fetchall()
                        columns = (
                            [desc[0] for desc in cursor.description] if cursor.description else []
                        )
                        return Result.ok(
                            {
                                "rows": [dict(row) for row in rows],
                                "columns": columns,
                                "row_count": len(rows),
                                "query_type": "select",
                            }
                        )
                    else:
                        # Query modifies data
                        conn.commit()
                        return Result.ok(
                            {
                                "rows_affected": cursor.rowcount,
                                "query_type": "modify",
                            }
                        )
                finally:
                    conn.close()

            # Run with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _sync_execute),
                timeout=timeout,
            )
            return result
        except asyncio.TimeoutError:
            return Result.fail(f"Query timed out after {timeout} seconds")
        except sqlite3.Error as e:
            return Result.fail(f"SQLite error: {str(e)}")
        except Exception as e:
            return Result.fail(f"Database error: {str(e)}")

    async def _execute_postgresql(
        self, query: str, connection: str, timeout: int, params: List
    ) -> Result:
        """Execute PostgreSQL query."""
        try:
            # Try to import asyncpg
            import asyncpg
        except ImportError:
            return Result.ok(
                error="PostgreSQL support requires 'asyncpg' package. Install with: pip install asyncpg"
            )
        try:
            # Connect to PostgreSQL
            conn = await asyncio.wait_for(asyncpg.connect(connection), timeout=10)
            try:
                # Execute query with timeout
                if query.strip().upper().startswith(("SELECT", "WITH")):
                    # Query returns results
                    rows = await asyncio.wait_for(conn.fetch(query, *params), timeout=timeout)
                    columns = list(rows[0].keys()) if rows else []
                    return Result.ok(
                        {
                            "rows": [dict(row) for row in rows],
                            "columns": columns,
                            "row_count": len(rows),
                            "query_type": "select",
                        }
                    )
                else:
                    # Query modifies data
                    result = await asyncio.wait_for(conn.execute(query, *params), timeout=timeout)
                    # Parse affected rows from result string
                    rows_affected = 0
                    if result.startswith(("INSERT", "UPDATE", "DELETE")):
                        parts = result.split()
                        if len(parts) > 1 and parts[-1].isdigit():
                            rows_affected = int(parts[-1])
                    return Result.ok(
                        {
                            "rows_affected": rows_affected,
                            "query_type": "modify",
                        }
                    )
            finally:
                await conn.close()
        except asyncio.TimeoutError:
            return Result.fail(f"Query timed out after {timeout} seconds")
        except Exception as e:
            return Result.fail(f"PostgreSQL error: {str(e)}")

    async def _execute_mysql(
        self, query: str, connection: str, timeout: int, params: List
    ) -> Result:
        """Execute MySQL query."""
        try:
            # Try to import aiomysql
            import aiomysql
        except ImportError:
            return Result.ok(
                error="MySQL support requires 'aiomysql' package. Install with: pip install aiomysql"
            )
        try:
            # Parse MySQL connection string
            parsed = urlparse(connection)
            conn_kwargs = {
                "host": parsed.hostname or "localhost",
                "port": parsed.port or 3306,
                "user": parsed.username,
                "password": parsed.password,
                "db": parsed.path.lstrip("/") if parsed.path else None,
                "connect_timeout": 10,
            }
            # Connect to MySQL
            conn = await asyncio.wait_for(aiomysql.connect(**conn_kwargs), timeout=10)
            try:
                cursor = await conn.cursor(aiomysql.DictCursor)
                # Execute query with timeout
                await asyncio.wait_for(cursor.execute(query, params), timeout=timeout)
                if (
                    query.strip()
                    .upper()
                    .startswith(("SELECT", "WITH", "SHOW", "DESCRIBE", "EXPLAIN"))
                ):
                    # Query returns results
                    rows = await cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    return Result.ok(
                        {
                            "rows": rows,
                            "columns": columns,
                            "row_count": len(rows),
                            "query_type": "select",
                        }
                    )
                else:
                    # Query modifies data
                    await conn.commit()
                    return Result.ok(
                        {
                            "rows_affected": cursor.rowcount,
                            "query_type": "modify",
                        }
                    )
            finally:
                await cursor.close()
                conn.close()
        except asyncio.TimeoutError:
            logger.error(f"MySQL query timed out after {timeout} seconds: {query}")
            return Result.fail(f"Query timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"MySQL error executing query '{query}': {e}")
            return Result.fail(f"MySQL error: {str(e)}")

    def format_human(
        self, params: Dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format SQL execution for display."""
        from cogency.utils import truncate

        query = params.get("query", "")
        connection = params.get("connection", "")
        # Show database type and truncated query
        db_type = connection.split("://")[0] if "://" in connection else "unknown"
        param_str = f"({db_type}: {truncate(query, 25)})" if query else ""
        if results is None:
            return param_str, ""
        # Format results
        if not results.success:
            result_str = f"Error: {results.error}"
        else:
            data = results.data
            query_type = data.get("query_type", "")
            if query_type == "select":
                count = data.get("row_count", 0)
                result_str = f"Selected {count} rows"
            elif query_type == "modify":
                affected = data.get("rows_affected", 0)
                result_str = f"Affected {affected} rows"
            else:
                result_str = "Query executed"
        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format SQL results for agent action history."""
        if not result_data:
            return "No result"

        query_type = result_data.get("query_type", "")
        formatters = {
            "select": lambda data: f"Selected {data.get('row_count', 0)} rows",
            "modify": lambda data: f"Affected {data.get('rows_affected', 0)} rows",
        }
        return formatters.get(query_type, lambda data: "SQL query executed")(result_data)
