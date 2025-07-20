"""Test SQL tool business logic."""
import pytest
import tempfile
from pathlib import Path

from cogency.tools.sql import SQL


class TestSQL:
    """Test SQL tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """SQL tool implements required interface."""
        sql = SQL()
        
        # Required attributes
        assert sql.name == "sql"
        assert sql.description
        assert hasattr(sql, 'run')
        
        # Schema and examples
        schema = sql.get_schema()
        examples = sql.get_usage_examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_empty_query_error(self):
        """SQL tool handles empty queries."""
        sql = SQL()
        
        result = await sql.run(query="", connection="sqlite:///test.db")
        assert "error" in result
        assert "SQL query cannot be empty" in result["error"]
        
        result = await sql.run(query="   ", connection="sqlite:///test.db")
        assert "error" in result
        assert "SQL query cannot be empty" in result["error"]
    
    @pytest.mark.asyncio
    async def test_missing_connection_error(self):
        """SQL tool handles missing connection string."""
        sql = SQL()
        
        result = await sql.run(query="SELECT 1", connection="")
        assert "error" in result
        assert "Database connection string required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_invalid_connection_format(self):
        """SQL tool handles invalid connection strings."""
        sql = SQL()
        
        result = await sql.run(query="SELECT 1", connection="invalid-connection")
        assert "error" in result
        # Connection without scheme will be treated as unsupported driver
        assert "Unsupported database driver" in result["error"]
    
    @pytest.mark.asyncio
    async def test_unsupported_driver(self):
        """SQL tool handles unsupported database drivers."""
        sql = SQL()
        
        result = await sql.run(query="SELECT 1", connection="oracle://user:pass@host/db")
        assert "error" in result
        assert "Unsupported database driver" in result["error"]
        assert "sqlite" in result["error"] and "postgresql" in result["error"] and "mysql" in result["error"]
    
    @pytest.mark.asyncio
    async def test_sqlite_create_table(self):
        """Test SQLite table creation."""
        sql = SQL()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            connection = f"sqlite:///{db_path}"
            
            # Create table
            result = await sql.run(
                query="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)",
                connection=connection
            )
            
            assert result["success"] is True
            assert result["query_type"] == "modify"
            assert "rows_affected" in result
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_sqlite_insert_and_select(self):
        """Test SQLite insert and select operations."""
        sql = SQL()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            connection = f"sqlite:///{db_path}"
            
            # Create table
            await sql.run(
                query="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)",
                connection=connection
            )
            
            # Insert data
            result = await sql.run(
                query="INSERT INTO users (name, age) VALUES (?, ?)",
                connection=connection,
                params=["Alice", 30]
            )
            
            assert result["success"] is True
            assert result["query_type"] == "modify"
            assert result["rows_affected"] == 1
            
            # Insert more data
            await sql.run(
                query="INSERT INTO users (name, age) VALUES (?, ?)",
                connection=connection,
                params=["Bob", 25]
            )
            
            # Select data
            result = await sql.run(
                query="SELECT * FROM users ORDER BY name",
                connection=connection
            )
            
            assert result["success"] is True
            assert result["query_type"] == "select"
            assert result["row_count"] == 2
            assert result["columns"] == ["id", "name", "age"]
            assert len(result["rows"]) == 2
            assert result["rows"][0]["name"] == "Alice"
            assert result["rows"][0]["age"] == 30
            assert result["rows"][1]["name"] == "Bob"
            assert result["rows"][1]["age"] == 25
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_sqlite_update_and_delete(self):
        """Test SQLite update and delete operations."""
        sql = SQL()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            connection = f"sqlite:///{db_path}"
            
            # Setup test data
            await sql.run(
                query="CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)",
                connection=connection
            )
            await sql.run(
                query="INSERT INTO users (name, age) VALUES (?, ?), (?, ?)",
                connection=connection,
                params=["Alice", 30, "Bob", 25]
            )
            
            # Update data
            result = await sql.run(
                query="UPDATE users SET age = ? WHERE name = ?",
                connection=connection,
                params=[31, "Alice"]
            )
            
            assert result["success"] is True
            assert result["query_type"] == "modify"
            assert result["rows_affected"] == 1
            
            # Verify update
            result = await sql.run(
                query="SELECT age FROM users WHERE name = ?",
                connection=connection,
                params=["Alice"]
            )
            assert result["rows"][0]["age"] == 31
            
            # Delete data
            result = await sql.run(
                query="DELETE FROM users WHERE name = ?",
                connection=connection,
                params=["Bob"]
            )
            
            assert result["success"] is True
            assert result["query_type"] == "modify"
            assert result["rows_affected"] == 1
            
            # Verify deletion
            result = await sql.run(
                query="SELECT COUNT(*) as count FROM users",
                connection=connection
            )
            assert result["rows"][0]["count"] == 1
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_sqlite_pragma_queries(self):
        """Test SQLite PRAGMA queries (should be treated as select)."""
        sql = SQL()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            connection = f"sqlite:///{db_path}"
            
            # PRAGMA query
            result = await sql.run(
                query="PRAGMA table_info(sqlite_master)",
                connection=connection
            )
            
            assert result["success"] is True
            assert result["query_type"] == "select"
            assert "rows" in result
            assert "columns" in result
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_sqlite_syntax_error(self):
        """Test SQLite syntax error handling."""
        sql = SQL()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            connection = f"sqlite:///{db_path}"
            
            # Invalid SQL syntax
            result = await sql.run(
                query="INVALID SQL SYNTAX",
                connection=connection
            )
            
            assert "error" in result
            assert "SQLite error" in result["error"]
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_sqlite_timeout_parameter(self):
        """Test timeout parameter validation."""
        sql = SQL()
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        try:
            connection = f"sqlite:///{db_path}"
            
            # Test with custom timeout
            result = await sql.run(
                query="SELECT 1 as test",
                connection=connection,
                timeout=5
            )
            
            assert result["success"] is True
            
            # Test timeout bounds (should be clamped to 1-300)
            result = await sql.run(
                query="SELECT 1 as test",
                connection=connection,
                timeout=0  # Should be clamped to 1
            )
            
            assert result["success"] is True
            
        finally:
            Path(db_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_postgresql_not_installed(self):
        """Test PostgreSQL error when asyncpg not installed."""
        sql = SQL()
        
        # Mock the import error by testing with postgresql connection
        # This will fail gracefully if asyncpg is not installed
        result = await sql.run(
            query="SELECT 1",
            connection="postgresql://user:pass@localhost/test"
        )
        
        # Should either work (if asyncpg installed) or show helpful error
        if "error" in result:
            assert "asyncpg" in result["error"] or "PostgreSQL" in result["error"]
        else:
            # If it doesn't error, asyncpg is installed and connection failed for other reasons
            assert "error" in result  # Connection should fail since we're using fake credentials
    
    @pytest.mark.asyncio
    async def test_mysql_not_installed(self):
        """Test MySQL error when aiomysql not installed."""
        sql = SQL()
        
        # Mock the import error by testing with mysql connection
        result = await sql.run(
            query="SELECT 1",
            connection="mysql://user:pass@localhost/test"
        )
        
        # Should either work (if aiomysql installed) or show helpful error
        if "error" in result:
            assert "aiomysql" in result["error"] or "MySQL" in result["error"]
        else:
            # If it doesn't error, aiomysql is installed and connection failed for other reasons
            assert "error" in result  # Connection should fail since we're using fake credentials
    
    @pytest.mark.asyncio
    async def test_format_params(self):
        """Test parameter formatting for display."""
        sql = SQL()
        
        # Test with query and connection
        params = {
            "query": "SELECT * FROM users WHERE age > 25",
            "connection": "sqlite:///test.db"
        }
        formatted = sql.format_params(params)
        assert "sqlite" in formatted
        assert "SELECT * FROM users" in formatted or "SELECT * FROM user" in formatted  # Truncated
        
        # Test with empty params
        formatted = sql.format_params({})
        assert formatted == ""
    
    @pytest.mark.asyncio
    async def test_sqlite_memory_database(self):
        """Test SQLite in-memory database."""
        sql = SQL()
        
        connection = "sqlite://:memory:"
        
        # Create and use in-memory database
        result = await sql.run(
            query="CREATE TABLE temp (id INTEGER, value TEXT)",
            connection=connection
        )
        assert result["success"] is True
        
        # Note: In-memory databases don't persist between connections
        # so this is mainly testing that the connection string is parsed correctly