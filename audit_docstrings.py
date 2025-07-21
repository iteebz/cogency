#!/usr/bin/env python3
"""
Docstring audit script for v1.0.0 release
Checks for multiline formatting, profanity, unclear descriptions, and inconsistencies
"""

import json
import re
from pathlib import Path
from typing import Dict


class DocstringAuditor:
    def __init__(self, docs_path: str):
        with open(docs_path) as f:
            self.docs = json.load(f)
        self.issues = []

    def audit_all(self):
        """Run all audits and return issues"""
        print("🔍 Auditing docstrings for v1.0.0 release...\n")

        # Audit package docstring
        pkg = self.docs.get("package", {})
        self._audit_docstring(pkg.get("docstring", ""), "package", pkg.get("name", "cogency"))

        # Audit modules
        for module_name, module_data in self.docs.get("modules", {}).items():
            self._audit_module(module_name, module_data)

        return self.issues

    def _audit_module(self, module_name: str, module_data: Dict):
        """Audit a single module"""
        # Module docstring
        self._audit_docstring(module_data.get("docstring", ""), "module", module_name)

        # Classes
        for class_data in module_data.get("classes", []):
            class_name = class_data.get("name", "")
            self._audit_docstring(
                class_data.get("docstring", ""), "class", f"{module_name}.{class_name}"
            )

            # Methods
            for method in class_data.get("methods", []):
                method_name = method.get("name", "")
                self._audit_docstring(
                    method.get("docstring", ""),
                    "method",
                    f"{module_name}.{class_name}.{method_name}",
                )

        # Functions
        for func_data in module_data.get("functions", []):
            func_name = func_data.get("name", "")
            self._audit_docstring(
                func_data.get("docstring", ""), "function", f"{module_name}.{func_name}"
            )

    def _audit_docstring(self, docstring: str, item_type: str, item_name: str):
        """Audit individual docstring for issues"""
        if not docstring:
            if item_type != "module":  # Modules can have empty docstrings
                self._add_issue("missing", item_type, item_name, "Missing docstring")
            return

        # Check for profanity (word boundary check to avoid false positives)
        profanity_words = ["damn", "hell", "shit", "fuck", "stupid", "dumb"]
        for word in profanity_words:
            pattern = r"\b" + re.escape(word) + r"\b"
            if re.search(pattern, docstring.lower()):
                self._add_issue("profanity", item_type, item_name, f"Contains profanity: '{word}'")

        # Check for multiline formatting issues
        if "\n" in docstring:
            lines = docstring.split("\n")
            if len(lines) > 1:
                # Check for inconsistent indentation
                non_empty_lines = [line for line in lines[1:] if line.strip()]
                if non_empty_lines:
                    indents = [len(line) - len(line.lstrip()) for line in non_empty_lines]
                    if len(set(indents)) > 2:  # More than 2 different indentations
                        self._add_issue(
                            "formatting",
                            item_type,
                            item_name,
                            "Inconsistent indentation in multiline docstring",
                        )

        # Check for unclear/vague docstrings
        vague_patterns = [
            r"^(Base class|Abstract|Simple|Basic|Main|Default)\.?\s*$",
            r"^(Execute|Run|Process)\.?\s*$",
            r"^(Get|Set)\.?\s*$",
            r"^\w+\.?\s*$",  # Single word docstrings
        ]

        for pattern in vague_patterns:
            if re.match(pattern, docstring.strip(), re.IGNORECASE):
                self._add_issue(
                    "vague", item_type, item_name, f"Vague/unclear docstring: '{docstring.strip()}'"
                )

        # Check for inconsistent punctuation
        if not docstring.strip().endswith(".") and len(docstring.strip()) > 10:
            self._add_issue(
                "punctuation", item_type, item_name, "Missing period at end of docstring"
            )

        # Check for inconsistent capitalization
        first_char = docstring.strip()[0] if docstring.strip() else ""
        if first_char and not first_char.isupper():
            self._add_issue(
                "capitalization", item_type, item_name, "Docstring should start with capital letter"
            )

    def _add_issue(self, issue_type: str, item_type: str, item_name: str, description: str):
        """Add issue to list"""
        self.issues.append(
            {
                "type": issue_type,
                "item_type": item_type,
                "item_name": item_name,
                "description": description,
            }
        )

    def print_report(self):
        """Print formatted audit report"""
        if not self.issues:
            print("✅ No docstring issues found! Codebase is v1.0.0 ready.")
            return

        print(f"❌ Found {len(self.issues)} docstring issues:\n")

        # Group by issue type
        by_type = {}
        for issue in self.issues:
            issue_type = issue["type"]
            if issue_type not in by_type:
                by_type[issue_type] = []
            by_type[issue_type].append(issue)

        # Print by category
        icons = {
            "missing": "📝",
            "profanity": "🤬",
            "formatting": "📐",
            "vague": "❓",
            "punctuation": "📃",
            "capitalization": "🔤",
        }

        for issue_type, issues in by_type.items():
            icon = icons.get(issue_type, "⚠️")
            print(f"{icon} {issue_type.upper()} ({len(issues)} issues):")
            for issue in issues:
                print(f"  • {issue['item_type']}: {issue['item_name']}")
                print(f"    {issue['description']}")
            print()

        print(f"📊 Summary: {len(self.issues)} total issues across {len(by_type)} categories")
        print("\n🔧 Run with --fix flag to automatically fix simple issues")


def main():
    docs_path = "website/scripts/src/data/api/docs.json"

    if not Path(docs_path).exists():
        print(f"❌ Documentation file not found: {docs_path}")
        print("Run the docs generation script first")
        return

    auditor = DocstringAuditor(docs_path)
    auditor.audit_all()
    auditor.print_report()


if __name__ == "__main__":
    main()
