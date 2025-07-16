#!/usr/bin/env python3
"""
Generate API documentation from cogency OSS project.
Extracts docs via Python inspection and outputs JSON for Astro.

Run from website: python scripts/generate_docs.py
Or with poetry: cd ../../ && poetry run python website/scripts/generate_docs.py
"""

import json
import sys
import inspect
import subprocess
from pathlib import Path
from typing import Dict, Any, List
import importlib.util


def load_cogency_module(cogency_python_path: str):
    """Load the cogency package from the OSS repo."""
    cogency_src = Path(cogency_python_path) / "src"
    sys.path.insert(0, str(cogency_src))
    
    try:
        import cogency
        return cogency
    except ImportError as e:
        print(f"Failed to import cogency: {e}")
        return None


def extract_class_info(cls) -> Dict[str, Any]:
    """Extract documentation info from a class."""
    info = {
        "name": cls.__name__,
        "docstring": inspect.getdoc(cls) or "",
        "module": cls.__module__,
        "methods": []
    }
    
    # Get constructor signature
    try:
        init_sig = inspect.signature(cls.__init__)
        info["init_signature"] = str(init_sig)
    except (ValueError, TypeError):
        info["init_signature"] = ""
    
    # Extract public methods
    for name, method in inspect.getmembers(cls, inspect.isfunction):
        if not name.startswith("_"):
            method_info = {
                "name": name,
                "docstring": inspect.getdoc(method) or "",
                "signature": str(inspect.signature(method)) if hasattr(method, "__call__") else ""
            }
            info["methods"].append(method_info)
    
    return info


def extract_function_info(func) -> Dict[str, Any]:
    """Extract documentation info from a function."""
    try:
        signature = str(inspect.signature(func))
    except (ValueError, TypeError):
        signature = ""
    
    return {
        "name": func.__name__,
        "docstring": inspect.getdoc(func) or "",
        "module": func.__module__,
        "signature": signature
    }


def generate_api_docs(cogency_python_path: str) -> Dict[str, Any]:
    """Generate comprehensive API documentation."""
    cogency = load_cogency_module(cogency_python_path)
    if not cogency:
        return {}
    
    docs = {
        "package": {
            "name": "cogency",
            "version": getattr(cogency, "__version__", "unknown"),
            "docstring": inspect.getdoc(cogency) or ""
        },
        "modules": {}
    }
    
    # Core modules to document
    module_names = [
        "agent", "llm", "tools", "nodes", "memory", 
        "context", "config", "types", "trace"
    ]
    
    for module_name in module_names:
        try:
            module = getattr(cogency, module_name, None)
            if module is None:
                # Try importing submodule
                full_name = f"cogency.{module_name}"
                module = importlib.import_module(full_name)
            
            if module:
                module_info = {
                    "name": module_name,
                    "docstring": inspect.getdoc(module) or "",
                    "classes": [],
                    "functions": []
                }
                
                # Extract classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if obj.__module__.startswith("cogency"):
                        module_info["classes"].append(extract_class_info(obj))
                
                # Extract functions
                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    if obj.__module__.startswith("cogency"):
                        module_info["functions"].append(extract_function_info(obj))
                
                docs["modules"][module_name] = module_info
                
        except ImportError as e:
            print(f"Warning: Could not import cogency.{module_name}: {e}")
    
    return docs


def main():
    """Main entry point."""
    # Default to cogency src directory (restructured)
    cogency_path = "../.."
    output_dir = "src/data/autodocs"
    
    if len(sys.argv) > 1:
        cogency_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    
    print(f"Generating docs from: {cogency_path}")
    print(f"Output directory: {output_dir}")
    
    # Generate documentation
    docs = generate_api_docs(cogency_path)
    
    if not docs or not docs.get("modules"):
        print("❌ No documentation generated")
        sys.exit(1)
    
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Write to JSON file
    output_file = output_path / "api_docs.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Generated documentation for {len(docs['modules'])} modules")
    print(f"Output written to: {output_file}")
    print(f"Modules: {list(docs['modules'].keys())}")


if __name__ == "__main__":
    main()