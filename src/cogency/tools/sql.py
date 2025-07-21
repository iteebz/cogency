"""SQL database tool for executing queries across multiple database types."""
import asyncio
import logging
import sqlite3
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from .base import BaseTool
from .registry import tool

logger = logging.getLogger(__name__)


@tool
class SQL(BaseTool):
    """Execute SQL queries across multiple database types with connection management."""

    def __init__(self):
        super().__init__(
            name="sql",
            description="Execute SQL queries on SQLite, PostgreSQL, MySQL databases with connection string support",
            emoji="🗄️"
        )
        # Beautiful dispatch pattern - extensible database support
        self._drivers = {
            "sqlite": self._execute_sqlite,
            "postgresql": self._execute_postgresql,
            "postgres": self._execute_postgresql,  # Alias
            "mysql": self._execute_mysql,
        }

    async def run(self, query: str, connection: str, timeout: int = 30, 
                  params: Optional[List] = None, **kwargs) -> Dict[str, Any]:
        """Execute SQL query using dispatch pattern.
        
        Args:
            query: SQL query to execute
            connection: Database connection string (sqlite:///path, postgresql://..., mysql://...)
            timeout: Query timeout in seconds (default: 30)
            params: Optional query parameters for prepared statements
            
        Returns:
            Query results including rows, columns, and metadata
        """
        if not query or not query.strip():
            return {"error": "SQL query cannot be empty"}
        
        if not connection:
            return {"error": "Database connection string required"}
        
        # Parse connection string to determine driver
        try:
            parsed = urlparse(connection)
            driver = parsed.scheme.lower()
        except Exception:
            return {"error": "Invalid connection string format"}
        
        if driver not in self._drivers:
            available = ", ".join(set(self._drivers.keys()))
            return {"error": f"Unsupported database driver. Use: {available}"}
        
        # Limit timeout
        timeout = min(max(timeout, 1), 300)  # 1-300 seconds for DB queries
        
        # Dispatch to appropriate database handler
        executor = self._drivers[driver]
        return await executor(query, connection, timeout, params or [])

    async def _execute_sqlite(self, query: str, connection: str, timeout: int, 
                            params: List) -> Dict[str, Any]:
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
                    if query.strip().upper().startswith(('SELECT', 'WITH', 'PRAGMA')):
                        # Query returns results
                        rows = cursor.fetchall()
                        columns = [desc[0] for desc in cursor.description] if cursor.description else []
                        return {
                            "success": True,
                            "rows": [dict(row) for row in rows],
                            "columns": columns,
                            "row_count": len(rows),
                            "query_type": "select"
                        }
                    else:
                        # Query modifies data
                        conn.commit()
                        return {
                            "success": True,
                            "rows_affected": cursor.rowcount,
                            "query_type": "modify"
                        }
                        
                finally:
                    conn.close()
            
            # Run with timeout
            result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(None, _sync_execute),
                timeout=timeout
            )
            return result
            
        except asyncio.TimeoutError:
            return {"error": f"Query timed out after {timeout} seconds"}
        except sqlite3.Error as e:
            return {"error": f"SQLite error: {str(e)}"}
        except Exception as e:
            return {"error": f"Database error: {str(e)}"}

    async def _execute_postgresql(self, query: str, connection: str, timeout: int, 
                                params: List) -> Dict[str, Any]:
        """Execute PostgreSQL query."""
        try:
            # Try to import asyncpg
            import asyncpg
        except ImportError:
            return {
                "error": "PostgreSQL support requires 'asyncpg' package. Install with: pip install asyncpg"
            }
        
        try:
            # Connect to PostgreSQL
            conn = await asyncio.wait_for(
                asyncpg.connect(connection), 
                timeout=10
            )
            
            try:
                # Execute query with timeout
                if query.strip().upper().startswith(('SELECT', 'WITH')):
                    # Query returns results
                    rows = await asyncio.wait_for(
                        conn.fetch(query, *params),
                        timeout=timeout
                    )
                    columns = list(rows[0].keys()) if rows else []
                    return {
                        "success": True,
                        "rows": [dict(row) for row in rows],
                        "columns": columns,
                        "row_count": len(rows),
                        "query_type": "select"
                    }
                else:
                    # Query modifies data
                    result = await asyncio.wait_for(
                        conn.execute(query, *params),
                        timeout=timeout
                    )
                    # Parse affected rows from result string
                    rows_affected = 0
                    if result.startswith(('INSERT', 'UPDATE', 'DELETE')):
                        parts = result.split()
                        if len(parts) > 1 and parts[-1].isdigit():
                            rows_affected = int(parts[-1])
                    
                    return {
                        "success": True,
                        "rows_affected": rows_affected,
                        "query_type": "modify"
                    }
                    
            finally:
                await conn.close()
                
        except asyncio.TimeoutError:
            return {"error": f"Query timed out after {timeout} seconds"}
        except Exception as e:
            return {"error": f"PostgreSQL error: {str(e)}"}

    async def _execute_mysql(self, query: str, connection: str, timeout: int, 
                           params: List) -> Dict[str, Any]:
        """Execute MySQL query."""
        try:
            # Try to import aiomysql
            import aiomysql
        except ImportError:
            return {
                "error": "MySQL support requires 'aiomysql' package. Install with: pip install aiomysql"
            }
        
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
            conn = await asyncio.wait_for(
                aiomysql.connect(**conn_kwargs),
                timeout=10
            )
            
            try:
                cursor = await conn.cursor(aiomysql.DictCursor)
                
                # Execute query with timeout
                await asyncio.wait_for(
                    cursor.execute(query, params),
                    timeout=timeout
                )
                
                if query.strip().upper().startswith(('SELECT', 'WITH', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
                    # Query returns results
                    rows = await cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description] if cursor.description else []
                    return {
                        "success": True,
                        "rows": rows,
                        "columns": columns,
                        "row_count": len(rows),
                        "query_type": "select"
                    }
                else:
                    # Query modifies data
                    await conn.commit()
                    return {
                        "success": True,
                        "rows_affected": cursor.rowcount,
                        "query_type": "modify"
                    }
                    
            finally:
                await cursor.close()
                conn.close()
                
        except asyncio.TimeoutError:
            return {"error": f"Query timed out after {timeout} seconds"}
        except Exception as e:
            return {"error": f"MySQL error: {str(e)}"}

    def schema(self) -> str:
        """Return the tool call schema."""
        return "sql(query='string', connection='string', timeout=30, params=list)"

    def examples(self) -> List[str]:
        """Return example usage patterns."""
        return [
            "sql(query='SELECT * FROM users LIMIT 5', connection='sqlite:///app.db')",
            "sql(query='INSERT INTO logs (message) VALUES (?)', connection='sqlite:///app.db', params=['Hello'])",
            "sql(query='CREATE TABLE logs (id INTEGER PRIMARY KEY, message TEXT)', connection='sqlite:///app.db')",
            "sql(query='SELECT COUNT(*) as total FROM orders', connection='postgresql://user:pass@localhost/shop')",
            "sql(query='INSERT INTO users (name, email) VALUES (?, ?)', connection='sqlite:///app.db', params=['John', 'john@example.com'])"
        ]
    
    def format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for display."""
        from cogency.utils.formatting import truncate
        query = params.get("query", "")
        connection = params.get("connection", "")
        # Show database type and truncated query
        db_type = connection.split("://")[0] if "://" in connection else "unknown"
        return f"({db_type}: {truncate(query, 25)})" if query else ""