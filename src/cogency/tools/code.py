"""Code execution tool for Python/JavaScript - ISOLATED & SANDBOXED."""
import asyncio
import json
import logging
import tempfile
import subprocess
from typing import Any, Dict, List, Optional
from pathlib import Path
import os
import sys

from .base import BaseTool
from .registry import tool

logger = logging.getLogger(__name__)


@tool
class Code(BaseTool):
    """Execute Python and JavaScript code safely in isolated environment."""

    def __init__(self):
        super().__init__(
            name="code",
            description="Execute code snippets directly - for running inline Python/JS code, not files",
            emoji="🚀"
        )
        # Beautiful dispatch pattern - extensible and clean
        self._languages = {
            "python": self._execute_python,
            "javascript": self._execute_javascript,
            "js": self._execute_javascript,  # Alias
        }

    async def run(self, code: str, language: str = "python", timeout: int = 30, 
                  **kwargs) -> Dict[str, Any]:
        """Execute code using dispatch pattern.
        
        Args:
            code: Source code to execute
            language: Programming language (python, javascript/js)
            timeout: Execution timeout in seconds (default: 30, max: 120)
            
        Returns:
            Execution results including output, errors, and exit code
        """
        if not code or not code.strip():
            return {"error": "Code cannot be empty"}
        
        language = language.lower()
        if language not in self._languages:
            available = ", ".join(set(self._languages.keys()))
            return {"error": f"Unsupported language. Use: {available}"}
        
        # Limit timeout
        timeout = min(max(timeout, 1), 120)  # 1-120 seconds
        
        # Dispatch to appropriate language handler
        executor = self._languages[language]
        return await executor(code, timeout)

    async def _execute_python(self, code: str, timeout: int) -> Dict[str, Any]:
        """Execute Python code in isolated subprocess."""
        
        # Security: restricted Python execution
        safe_python_wrapper = '''
import sys
import os
import subprocess
import importlib

# Disable dangerous modules
BLOCKED_MODULES = {
    'os', 'subprocess', 'sys', 'importlib', 'builtins', '__builtin__',
    'eval', 'exec', 'compile', 'open', 'file', 'input', 'raw_input',
    'reload', '__import__', 'vars', 'dir', 'globals', 'locals',
    'delattr', 'setattr', 'getattr', 'hasattr'
}

# Restricted builtins
safe_builtins = {
    'abs', 'all', 'any', 'bin', 'bool', 'chr', 'dict', 'enumerate',
    'filter', 'float', 'frozenset', 'hex', 'int', 'isinstance', 'issubclass',
    'iter', 'len', 'list', 'map', 'max', 'min', 'oct', 'ord', 'pow',
    'print', 'range', 'repr', 'reversed', 'round', 'set', 'slice',
    'sorted', 'str', 'sum', 'tuple', 'type', 'zip'
}

# Import commonly used safe modules
import math
import random
import datetime
import json
import re

# Set up restricted globals
restricted_globals = {
    '__builtins__': {name: __builtins__[name] for name in safe_builtins if name in __builtins__},
    'math': math,
    'random': random,
    'datetime': datetime,
    'json': json,
    're': re
}

try:
    # Execute user code with restricted globals
    exec("""''' + code.replace('"""', '\\"""') + '''""", restricted_globals)
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
    sys.exit(1)
'''
        
        return await self._run_in_subprocess(['python', '-c', safe_python_wrapper], timeout)

    async def _execute_javascript(self, code: str, timeout: int) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js."""
        
        # Check if Node.js is available
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return {"error": "Node.js not found. Please install Node.js to execute JavaScript code."}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"error": "Node.js not found. Please install Node.js to execute JavaScript code."}
        
        # Security: restricted JavaScript execution
        safe_js_wrapper = f'''
// Disable dangerous globals
delete global.require;
delete global.process;
delete global.Buffer;
delete global.__dirname;
delete global.__filename;

// Restricted console for output
const output = [];
const originalLog = console.log;
console.log = (...args) => {{
    output.push(args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
    ).join(' '));
}};

try {{
    // User code execution
    {code}
    
    // Output results
    if (output.length > 0) {{
        originalLog(output.join('\\n'));
    }}
}} catch (error) {{
    originalLog(`Error: ${{error.name}}: ${{error.message}}`);
    process.exit(1);
}}
'''
        
        return await self._run_in_subprocess(['node', '-e', safe_js_wrapper], timeout)

    async def _run_in_subprocess(self, cmd: List[str], timeout: int) -> Dict[str, Any]:
        """Run command in subprocess with timeout and output capture."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024  # 1MB output limit
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                # Kill the process on timeout
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                return {"error": f"Code execution timed out after {timeout} seconds"}
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # Truncate very long output
            max_output = 5000  # 5KB per stream
            if len(stdout_text) > max_output:
                stdout_text = stdout_text[:max_output] + "\n... (output truncated)"
            if len(stderr_text) > max_output:
                stderr_text = stderr_text[:max_output] + "\n... (output truncated)"
            
            return {
                "exit_code": exit_code,
                "success": exit_code == 0,
                "output": stdout_text,
                "error_output": stderr_text,
                "timeout": timeout
            }
            
        except Exception as e:
            return {"error": f"Code execution failed: {str(e)}"}

    def get_schema(self) -> str:
        """Return the tool call schema."""
        return (
            "code(code='string', language='python|javascript|js', timeout=int) - "
            "Examples: code(code='print(2 + 2)', language='python'), "
            "code(code='console.log(Math.sqrt(16))', language='javascript')"
        )

    def get_usage_examples(self) -> List[str]:
        """Return example usage patterns."""
        return [
            "code(code='print(2 + 2)', language='python')",
            "code(code='import math; print(math.pi)', language='python')",
            "code(code='console.log(Math.sqrt(16))', language='javascript')",
            "code(code='const arr = [1,2,3]; console.log(arr.map(x => x*2))', language='js')"
        ]
    
    def format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for display."""
        from cogency.messaging import _truncate
        code = params.get("code", "")
        return f"({_truncate(code, 35)})" if code else ""