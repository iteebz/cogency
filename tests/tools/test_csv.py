"""Test CSV tool business logic."""
import pytest
import tempfile
from pathlib import Path

from cogency.tools.csv import CSV


class TestCSV:
    """Test CSV tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_interface(self):
        """CSV tool implements required interface."""
        csv_tool = CSV()
        
        # Required attributes
        assert csv_tool.name == "csv"
        assert csv_tool.description
        assert hasattr(csv_tool, 'run')
        
        # Schema and examples
        schema = csv_tool.schema()
        examples = csv_tool.examples()
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """CSV tool handles invalid operations."""
        csv_tool = CSV()
        
        result = await csv_tool.run(operation="invalid", file_path="test.csv")
        assert "error" in result
        assert "Invalid operation" in result["error"]
        assert "read, write, filter, analyze, transform, append" in result["error"]
    
    @pytest.mark.asyncio
    async def test_missing_file_path(self):
        """CSV tool handles missing file path."""
        csv_tool = CSV()
        
        result = await csv_tool.run(operation="read", file_path="")
        assert "error" in result
        assert "File path is required" in result["error"]
    
    @pytest.mark.asyncio
    async def test_write_csv(self):
        """Test writing CSV data to file."""
        csv_tool = CSV()
        
        test_data = [
            {"name": "Alice", "age": "30", "city": "New York"},
            {"name": "Bob", "age": "25", "city": "San Francisco"},
            {"name": "Charlie", "age": "35", "city": "Chicago"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            result = await csv_tool.run(
                operation="write",
                file_path=csv_path,
                data=test_data
            )
            
            assert result["success"] is True
            assert result["rows_written"] == 3
            assert result["file_path"] == csv_path
            assert result["columns"] == ["name", "age", "city"]
            
            # Verify file was created and has content
            assert Path(csv_path).exists()
            with open(csv_path, 'r') as f:
                content = f.read()
                assert "Alice" in content
                assert "Bob" in content
                assert "Charlie" in content
                
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_write_csv_with_custom_headers(self):
        """Test writing CSV with custom headers."""
        csv_tool = CSV()
        
        test_data = [
            {"full_name": "Alice Smith", "years": "30"},
            {"full_name": "Bob Jones", "years": "25"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            result = await csv_tool.run(
                operation="write",
                file_path=csv_path,
                data=test_data,
                headers=["full_name", "years"]
            )
            
            assert result["success"] is True
            assert result["columns"] == ["full_name", "years"]
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_write_csv_no_data_error(self):
        """Test write operation without data."""
        csv_tool = CSV()
        
        result = await csv_tool.run(
            operation="write",
            file_path="test.csv",
            data=None
        )
        
        assert "error" in result
        assert "Data is required for write operation" in result["error"]
    
    @pytest.mark.asyncio
    async def test_read_csv(self):
        """Test reading CSV data from file."""
        csv_tool = CSV()
        
        # First create a test file
        test_data = [
            {"name": "Alice", "age": "30", "city": "New York"},
            {"name": "Bob", "age": "25", "city": "San Francisco"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            # Write test data
            await csv_tool.run(
                operation="write",
                file_path=csv_path,
                data=test_data
            )
            
            # Read it back
            result = await csv_tool.run(
                operation="read",
                file_path=csv_path
            )
            
            assert result["success"] is True
            assert result["row_count"] == 2
            assert result["columns"] == ["name", "age", "city"]
            assert len(result["data"]) == 2
            assert result["data"][0]["name"] == "Alice"
            assert result["data"][1]["name"] == "Bob"
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_read_csv_with_limit(self):
        """Test reading CSV with row limit."""
        csv_tool = CSV()
        
        # Create test file with more data
        test_data = [
            {"name": f"Person{i}", "age": str(20 + i)} 
            for i in range(10)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            await csv_tool.run(operation="write", file_path=csv_path, data=test_data)
            
            # Read with limit
            result = await csv_tool.run(
                operation="read",
                file_path=csv_path,
                limit=3
            )
            
            assert result["success"] is True
            assert result["row_count"] == 3
            assert len(result["data"]) == 3
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """Test reading non-existent file."""
        csv_tool = CSV()
        
        result = await csv_tool.run(
            operation="read",
            file_path="/nonexistent/file.csv"
        )
        
        assert "error" in result
        assert "File not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_filter_csv(self):
        """Test filtering CSV data."""
        csv_tool = CSV()
        
        test_data = [
            {"name": "Alice", "age": "30", "city": "New York"},
            {"name": "Bob", "age": "25", "city": "San Francisco"},
            {"name": "Charlie", "age": "35", "city": "Chicago"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            await csv_tool.run(operation="write", file_path=csv_path, data=test_data)
            
            # Filter for people over 28
            result = await csv_tool.run(
                operation="filter",
                file_path=csv_path,
                filter_condition="int(row['age']) > 28"
            )
            
            assert result["success"] is True
            assert result["row_count"] == 2
            filtered_names = [row["name"] for row in result["filtered_data"]]
            assert "Alice" in filtered_names
            assert "Charlie" in filtered_names
            assert "Bob" not in filtered_names
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_filter_csv_with_output(self):
        """Test filtering CSV and saving to output file."""
        csv_tool = CSV()
        
        test_data = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            input_path = f.name
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            output_path = f.name
        
        try:
            await csv_tool.run(operation="write", file_path=input_path, data=test_data)
            
            result = await csv_tool.run(
                operation="filter",
                file_path=input_path,
                filter_condition="int(row['age']) >= 30",
                output_path=output_path
            )
            
            assert result["success"] is True
            assert result["output_path"] == output_path
            
            # Verify output file was created
            assert Path(output_path).exists()
            
        finally:
            Path(input_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_filter_invalid_condition(self):
        """Test filter with invalid condition."""
        csv_tool = CSV()
        
        test_data = [{"name": "Alice", "age": "30"}]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            await csv_tool.run(operation="write", file_path=csv_path, data=test_data)
            
            result = await csv_tool.run(
                operation="filter",
                file_path=csv_path,
                filter_condition="invalid_function(row['age'])"
            )
            
            assert "error" in result
            assert "Filter condition error" in result["error"]
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_analyze_csv(self):
        """Test CSV analysis functionality."""
        csv_tool = CSV()
        
        test_data = [
            {"name": "Alice", "age": "30", "score": "85.5"},
            {"name": "Bob", "age": "25", "score": "92.0"},
            {"name": "Charlie", "age": "", "score": "78.5"},  # Empty age
            {"name": "", "age": "35", "score": "invalid"}  # Empty name, invalid score
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            await csv_tool.run(operation="write", file_path=csv_path, data=test_data)
            
            result = await csv_tool.run(
                operation="analyze",
                file_path=csv_path
            )
            
            assert result["success"] is True
            assert result["total_rows"] == 4
            assert result["total_columns"] == 3
            assert result["columns"] == ["name", "age", "score"]
            
            # Check column statistics
            stats = result["column_statistics"]
            
            # Name column stats
            assert stats["name"]["total_values"] == 4
            assert stats["name"]["non_empty_values"] == 3  # One empty
            assert stats["name"]["empty_values"] == 1
            assert stats["name"]["unique_values"] == 3
            
            # Age column stats (should detect as numeric)
            assert stats["age"]["non_empty_values"] == 3
            assert stats["age"]["numeric"] is True
            assert stats["age"]["min"] == 25.0
            assert stats["age"]["max"] == 35.0
            assert stats["age"]["avg"] == 30.0  # (30+25+35)/3
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_analyze_empty_csv(self):
        """Test analyzing empty CSV file."""
        csv_tool = CSV()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            # Create empty CSV
            await csv_tool.run(operation="write", file_path=csv_path, data=[])
            
            result = await csv_tool.run(
                operation="analyze",
                file_path=csv_path
            )
            
            assert "error" in result
            assert "No data to analyze" in result["error"]
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_append_csv(self):
        """Test appending data to existing CSV."""
        csv_tool = CSV()
        
        initial_data = [
            {"name": "Alice", "age": "30"}
        ]
        
        append_data = [
            {"name": "Bob", "age": "25"},
            {"name": "Charlie", "age": "35"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            # Create initial file
            await csv_tool.run(operation="write", file_path=csv_path, data=initial_data)
            
            # Append data
            result = await csv_tool.run(
                operation="append",
                file_path=csv_path,
                data=append_data
            )
            
            assert result["success"] is True
            assert result["rows_appended"] == 2
            
            # Verify total data
            read_result = await csv_tool.run(operation="read", file_path=csv_path)
            assert read_result["row_count"] == 3
            names = [row["name"] for row in read_result["data"]]
            assert "Alice" in names
            assert "Bob" in names
            assert "Charlie" in names
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_append_to_nonexistent_file(self):
        """Test appending to non-existent file (should create it)."""
        csv_tool = CSV()
        
        append_data = [{"name": "Alice", "age": "30"}]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        # Remove the file so it doesn't exist
        Path(csv_path).unlink()
        
        try:
            result = await csv_tool.run(
                operation="append",
                file_path=csv_path,
                data=append_data
            )
            
            assert result["success"] is True
            assert result["rows_written"] == 1  # Should use write operation
            
            # Verify file was created
            assert Path(csv_path).exists()
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_transform_csv(self):
        """Test CSV data transformation."""
        csv_tool = CSV()
        
        test_data = [
            {"name": "alice", "age": "30", "score": "85"},
            {"name": "bob", "age": "25", "score": "92"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            await csv_tool.run(operation="write", file_path=csv_path, data=test_data)
            
            # Transform: capitalize names, double scores
            transformations = {
                "name": "value.title()",
                "score": "str(int(value) * 2)"
            }
            
            result = await csv_tool.run(
                operation="transform",
                file_path=csv_path,
                transformations=transformations
            )
            
            assert result["success"] is True
            assert result["row_count"] == 2
            
            # Check transformations
            transformed = result["transformed_data"]
            assert transformed[0]["name"] == "Alice"
            assert transformed[0]["score"] == "170"  # 85 * 2
            assert transformed[1]["name"] == "Bob"
            assert transformed[1]["score"] == "184"  # 92 * 2
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_transform_invalid_expression(self):
        """Test transform with invalid expression."""
        csv_tool = CSV()
        
        test_data = [{"name": "Alice", "age": "30"}]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            await csv_tool.run(operation="write", file_path=csv_path, data=test_data)
            
            result = await csv_tool.run(
                operation="transform",
                file_path=csv_path,
                transformations={"name": "invalid_function(value)"}
            )
            
            assert "error" in result
            assert "Transformation error" in result["error"]
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_custom_delimiter(self):
        """Test CSV operations with custom delimiter."""
        csv_tool = CSV()
        
        test_data = [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            csv_path = f.name
        
        try:
            # Write with semicolon delimiter
            await csv_tool.run(
                operation="write",
                file_path=csv_path,
                data=test_data,
                delimiter=";"
            )
            
            # Read with same delimiter
            result = await csv_tool.run(
                operation="read",
                file_path=csv_path,
                delimiter=";"
            )
            
            assert result["success"] is True
            assert result["row_count"] == 2
            assert result["data"][0]["name"] == "Alice"
            
        finally:
            Path(csv_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_format_params(self):
        """Test parameter formatting for display."""
        csv_tool = CSV()
        
        # Test with operation and file path
        params = {
            "operation": "read",
            "file_path": "/very/long/path/to/some/data/file.csv"
        }
        formatted = csv_tool.format_params(params)
        assert "read" in formatted
        assert "file.csv" in formatted or "/very/long/path" in formatted
        
        # Test with empty params
        formatted = csv_tool.format_params({})
        assert formatted == ""