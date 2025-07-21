"""CSV tool for reading, writing, and manipulating CSV files."""
import csv
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .base import BaseTool
from .registry import tool

logger = logging.getLogger(__name__)


@tool
class CSV(BaseTool):
    """Read, write, and manipulate CSV files with various operations."""

    def __init__(self):
        super().__init__(
            name="csv",
            description="Read, write, filter, and analyze CSV files with full data manipulation support",
            emoji="📊"
        )
        # Beautiful dispatch pattern - extensible operations
        self._operations = {
            "read": self._read_csv,
            "write": self._write_csv,
            "filter": self._filter_csv,
            "analyze": self._analyze_csv,
            "transform": self._transform_csv,
            "append": self._append_csv,
        }

    async def run(self, operation: str, file_path: str, data: Optional[List[Dict]] = None,
                  delimiter: str = ",", headers: Optional[List[str]] = None,
                  filter_condition: Optional[str] = None, limit: Optional[int] = None,
                  **kwargs) -> Dict[str, Any]:
        """Execute CSV operation using dispatch pattern.
        
        Args:
            operation: CSV operation (read, write, filter, analyze, transform, append)
            file_path: Path to CSV file
            data: Data for write/append operations (list of dicts)
            delimiter: CSV delimiter (default: comma)
            headers: Column headers for write operations
            filter_condition: Python expression for filtering (e.g., "row['age'] > 25")
            limit: Maximum number of rows to process
            
        Returns:
            Operation results including data, metadata, and statistics
        """
        operation = operation.lower()
        if operation not in self._operations:
            available = ", ".join(self._operations.keys())
            return {"error": f"Invalid operation. Use: {available}"}
        
        if not file_path:
            return {"error": "File path is required"}
        
        # Dispatch to appropriate operation handler
        handler = self._operations[operation]
        return await handler(file_path, data, delimiter, headers, filter_condition, limit, **kwargs)

    async def _read_csv(self, file_path: str, data: Optional[List[Dict]], delimiter: str,
                       headers: Optional[List[str]], filter_condition: Optional[str], 
                       limit: Optional[int], **kwargs) -> Dict[str, Any]:
        """Read CSV file and return data."""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"error": f"File not found: {file_path}"}
            
            rows = []
            with open(path, 'r', newline='', encoding='utf-8') as csvfile:
                # Detect dialect if possible
                try:
                    sample = csvfile.read(1024)
                    csvfile.seek(0)
                    sniffer = csv.Sniffer()
                    dialect = sniffer.sniff(sample, delimiters=delimiter)
                    reader = csv.DictReader(csvfile, delimiter=dialect.delimiter)
                except:
                    reader = csv.DictReader(csvfile, delimiter=delimiter)
                
                for i, row in enumerate(reader):
                    # Apply limit
                    if limit and i >= limit:
                        break
                    
                    # Apply filter condition
                    if filter_condition:
                        try:
                            # Safe evaluation of filter condition with basic functions
                            safe_globals = {
                                "__builtins__": {},
                                "int": int,
                                "float": float,
                                "str": str,
                                "len": len,
                                "abs": abs,
                                "min": min,
                                "max": max
                            }
                            if not eval(filter_condition, safe_globals, {"row": row}):
                                continue
                        except Exception as e:
                            return {"error": f"Filter condition error: {str(e)}"}
                    
                    rows.append(dict(row))
            
            return {
                "success": True,
                "data": rows,
                "row_count": len(rows),
                "columns": list(rows[0].keys()) if rows else [],
                "file_path": file_path
            }
            
        except Exception as e:
            return {"error": f"Failed to read CSV: {str(e)}"}

    async def _write_csv(self, file_path: str, data: Optional[List[Dict]], delimiter: str,
                        headers: Optional[List[str]], filter_condition: Optional[str], 
                        limit: Optional[int], **kwargs) -> Dict[str, Any]:
        """Write data to CSV file."""
        try:
            if not data:
                return {"error": "Data is required for write operation"}
            
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Determine fieldnames
            if headers:
                fieldnames = headers
            elif data:
                fieldnames = list(data[0].keys()) if data else []
            else:
                return {"error": "No headers or data provided"}
            
            with open(path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
                
                rows_written = 0
                for row in data:
                    if limit and rows_written >= limit:
                        break
                    writer.writerow(row)
                    rows_written += 1
            
            return {
                "success": True,
                "rows_written": rows_written,
                "file_path": file_path,
                "columns": fieldnames
            }
            
        except Exception as e:
            return {"error": f"Failed to write CSV: {str(e)}"}

    async def _append_csv(self, file_path: str, data: Optional[List[Dict]], delimiter: str,
                         headers: Optional[List[str]], filter_condition: Optional[str], 
                         limit: Optional[int], **kwargs) -> Dict[str, Any]:
        """Append data to existing CSV file."""
        try:
            if not data:
                return {"error": "Data is required for append operation"}
            
            path = Path(file_path)
            
            # Check if file exists to determine if we need headers
            file_exists = path.exists()
            
            if not file_exists:
                # File doesn't exist, create it with headers
                return await self._write_csv(file_path, data, delimiter, headers, filter_condition, limit)
            
            # File exists, append without headers
            with open(path, 'a', newline='', encoding='utf-8') as csvfile:
                # Read existing headers to maintain consistency
                with open(path, 'r', newline='', encoding='utf-8') as read_file:
                    reader = csv.DictReader(read_file, delimiter=delimiter)
                    existing_headers = reader.fieldnames or []
                
                writer = csv.DictWriter(csvfile, fieldnames=existing_headers, delimiter=delimiter)
                
                rows_appended = 0
                for row in data:
                    if limit and rows_appended >= limit:
                        break
                    writer.writerow(row)
                    rows_appended += 1
            
            return {
                "success": True,
                "rows_appended": rows_appended,
                "file_path": file_path
            }
            
        except Exception as e:
            return {"error": f"Failed to append to CSV: {str(e)}"}

    async def _filter_csv(self, file_path: str, data: Optional[List[Dict]], delimiter: str,
                         headers: Optional[List[str]], filter_condition: Optional[str], 
                         limit: Optional[int], **kwargs) -> Dict[str, Any]:
        """Filter CSV data and optionally save to new file."""
        try:
            # First read the data
            read_result = await self._read_csv(file_path, data, delimiter, headers, filter_condition, limit)
            if not read_result.get("success"):
                return read_result
            
            filtered_data = read_result["data"]
            
            # Optionally write to output file
            output_path = kwargs.get("output_path")
            if output_path:
                write_result = await self._write_csv(output_path, filtered_data, delimiter, headers, None, None)
                if not write_result.get("success"):
                    return write_result
                
                return {
                    "success": True,
                    "filtered_data": filtered_data,
                    "row_count": len(filtered_data),
                    "output_path": output_path
                }
            
            return {
                "success": True,
                "filtered_data": filtered_data,
                "row_count": len(filtered_data)
            }
            
        except Exception as e:
            return {"error": f"Failed to filter CSV: {str(e)}"}

    async def _analyze_csv(self, file_path: str, data: Optional[List[Dict]], delimiter: str,
                          headers: Optional[List[str]], filter_condition: Optional[str], 
                          limit: Optional[int], **kwargs) -> Dict[str, Any]:
        """Analyze CSV file and return statistics."""
        try:
            # Read the data
            read_result = await self._read_csv(file_path, data, delimiter, headers, filter_condition, limit)
            if not read_result.get("success"):
                return read_result
            
            data = read_result["data"]
            if not data:
                return {"error": "No data to analyze"}
            
            # Basic statistics
            total_rows = len(data)
            columns = list(data[0].keys())
            
            # Column analysis
            column_stats = {}
            for col in columns:
                values = [row.get(col, '') for row in data]
                non_empty = [v for v in values if v and str(v).strip()]
                
                column_stats[col] = {
                    "total_values": len(values),
                    "non_empty_values": len(non_empty),
                    "empty_values": len(values) - len(non_empty),
                    "unique_values": len(set(non_empty)),
                    "sample_values": list(set(non_empty))[:5]  # First 5 unique values
                }
                
                # Try to detect numeric columns
                try:
                    numeric_values = [float(v) for v in non_empty if str(v).replace('.', '').replace('-', '').isdigit()]
                    if numeric_values:
                        column_stats[col].update({
                            "numeric": True,
                            "min": min(numeric_values),
                            "max": max(numeric_values),
                            "avg": sum(numeric_values) / len(numeric_values)
                        })
                except:
                    column_stats[col]["numeric"] = False
            
            return {
                "success": True,
                "file_path": file_path,
                "total_rows": total_rows,
                "total_columns": len(columns),
                "columns": columns,
                "column_statistics": column_stats
            }
            
        except Exception as e:
            return {"error": f"Failed to analyze CSV: {str(e)}"}

    async def _transform_csv(self, file_path: str, data: Optional[List[Dict]], delimiter: str,
                           headers: Optional[List[str]], filter_condition: Optional[str], 
                           limit: Optional[int], **kwargs) -> Dict[str, Any]:
        """Transform CSV data with column operations."""
        try:
            # Read the data
            read_result = await self._read_csv(file_path, data, delimiter, headers, filter_condition, limit)
            if not read_result.get("success"):
                return read_result
            
            data = read_result["data"]
            if not data:
                return {"error": "No data to transform"}
            
            # Apply transformations
            transformations = kwargs.get("transformations", {})
            transformed_data = []
            
            for row in data:
                new_row = row.copy()
                
                # Apply column transformations
                for col, transform_expr in transformations.items():
                    try:
                        # Safe evaluation of transformation with basic functions
                        safe_globals = {
                            "__builtins__": {},
                            "int": int,
                            "float": float,
                            "str": str,
                            "len": len,
                            "abs": abs,
                            "min": min,
                            "max": max
                        }
                        new_row[col] = eval(transform_expr, safe_globals, {"row": row, "value": row.get(col)})
                    except Exception as e:
                        return {"error": f"Transformation error for column '{col}': {str(e)}"}
                
                transformed_data.append(new_row)
            
            # Optionally write to output file
            output_path = kwargs.get("output_path")
            if output_path:
                write_result = await self._write_csv(output_path, transformed_data, delimiter, headers, None, None)
                if not write_result.get("success"):
                    return write_result
                
                return {
                    "success": True,
                    "transformed_data": transformed_data,
                    "row_count": len(transformed_data),
                    "output_path": output_path
                }
            
            return {
                "success": True,
                "transformed_data": transformed_data,
                "row_count": len(transformed_data)
            }
            
        except Exception as e:
            return {"error": f"Failed to transform CSV: {str(e)}"}

    def get_schema(self) -> str:
        """Return the tool call schema."""
        return "csv(operation='read|write|filter|analyze|transform|append', file_path='string', data=list, delimiter=',', headers=list, filter_condition='string', limit=int)"

    def get_usage_examples(self) -> List[str]:
        """Return example usage patterns."""
        return [
            "csv(operation='read', file_path='data.csv')",
            "csv(operation='write', file_path='output.csv', data=[{'name': 'John', 'age': 30}])",
            "csv(operation='filter', file_path='data.csv', filter_condition=\"row['age'] > 25\")",
            "csv(operation='analyze', file_path='sales.csv')",
            "csv(operation='append', file_path='logs.csv', data=[{'timestamp': '2024-01-01', 'event': 'login'}])"
        ]
    
    def format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for display."""
        from cogency.utils.formatting import truncate
        operation = params.get("operation", "")
        file_path = params.get("file_path", "")
        return f"({operation}: {truncate(file_path, 25)})" if operation and file_path else ""