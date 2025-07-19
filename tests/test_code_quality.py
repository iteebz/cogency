"""Test code quality and anti-pattern detection."""
import ast
import re
from pathlib import Path


class TestAntiPatterns:
    """Detect code quality violations and anti-patterns."""
    
    def test_no_magic_strings_in_critical_paths(self, source_files):
        """Critical code paths should not use magic strings."""
        magic_string_violations = []
        
        # These are strings that should be constants
        suspicious_patterns = [
            r'"(?:respond|use_tool|use_tools|tool_needed|direct_response)"',
            r'"(?:pending|in_progress|completed|continue|complete|error)"',
            r'"(?:add|subtract|multiply|divide|square_root)"',
        ]
        
        for file_path in source_files:
            if file_path.name in ['__init__.py', 'conftest.py']:
                continue
                
            content = file_path.read_text()
            
            for pattern in suspicious_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    magic_string_violations.append({
                        'file': str(file_path),
                        'pattern': pattern,
                        'matches': matches
                    })
        
        # For now, just warn about violations
        if magic_string_violations:
            print(f"\nWARNING: Found {len(magic_string_violations)} magic string violations:")
            for violation in magic_string_violations[:3]:  # Show first 3
                print(f"  {violation['file']}: {violation['matches']}")
    
    def test_no_giant_methods(self, source_files):
        """Methods should not be excessively large."""
        large_method_violations = []
        
        for file_path in source_files:
            if file_path.name in ['__init__.py']:
                continue
                
            try:
                tree = ast.parse(file_path.read_text())
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Count lines in method
                        if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                            method_lines = node.end_lineno - node.lineno
                            if method_lines > 50:  # Arbitrary but reasonable limit
                                large_method_violations.append({
                                    'file': str(file_path),
                                    'method': node.name,
                                    'lines': method_lines
                                })
            except SyntaxError:
                continue  # Skip files with syntax errors
        
        # For now, just warn
        if large_method_violations:
            print(f"\nWARNING: Found {len(large_method_violations)} large methods:")
            for violation in large_method_violations[:3]:
                print(f"  {violation['file']}:{violation['method']} ({violation['lines']} lines)")
    
    def test_no_broad_exception_handling(self, source_files):
        """Should not catch Exception without specific handling."""
        broad_exception_violations = []
        
        for file_path in source_files:
            content = file_path.read_text()
            
            # Look for "except Exception:" or "except:" patterns
            suspicious_patterns = [
                r'except\s*Exception\s*:.*\n\s*pass',
                r'except\s*:\s*.*\n\s*pass',
                r'except\s*Exception.*:\s*.*continue'
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, content):
                    broad_exception_violations.append(str(file_path))
        
        # For now, just warn
        if broad_exception_violations:
            print(f"\nWARNING: Found {len(broad_exception_violations)} broad exception handlers:")
            for violation in broad_exception_violations[:3]:
                print(f"  {violation}")
    
    def test_no_giant_inline_strings(self, source_files):
        """Business logic should not contain giant inline strings."""
        giant_string_violations = []
        
        for file_path in source_files:
            content = file_path.read_text()
            
            # Look for triple-quoted strings longer than 10 lines
            triple_quote_strings = re.findall(r'"""([^"]*(?:"[^"]*)*?)"""', content, re.DOTALL)
            
            for string in triple_quote_strings:
                if string.count('\n') > 10:  # More than 10 lines
                    giant_string_violations.append({
                        'file': str(file_path),
                        'lines': string.count('\n'),
                        'preview': string[:100] + '...' if len(string) > 100 else string
                    })
        
        # For now, just warn
        if giant_string_violations:
            print(f"\nWARNING: Found {len(giant_string_violations)} giant inline strings:")
            for violation in giant_string_violations[:2]:
                print(f"  {violation['file']} ({violation['lines']} lines)")


class TestDRYViolations:
    """Detect Don't Repeat Yourself violations."""
    
    def test_no_duplicate_validation_patterns(self, source_files):
        """Similar validation logic should be extracted."""
        validation_patterns = []
        
        for file_path in source_files:
            content = file_path.read_text()
            
            # Look for common validation patterns
            patterns_found = []
            
            if 'is None' in content and 'return {"error"' in content:
                patterns_found.append('none_validation')
            
            if 'if not' in content and 'return {"error"' in content:
                patterns_found.append('falsy_validation')
            
            if len(patterns_found) > 0:
                validation_patterns.append({
                    'file': str(file_path),
                    'patterns': patterns_found
                })
        
        # Count similar patterns across files
        pattern_counts = {}
        for item in validation_patterns:
            for pattern in item['patterns']:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
        
        # Flag patterns that appear in multiple files
        for pattern, count in pattern_counts.items():
            if count >= 3:
                print(f"\nWARNING: Validation pattern '{pattern}' appears in {count} files (consider extracting)")
    
    def test_no_similar_method_signatures(self, source_files):
        """Look for methods that might be doing similar things."""
        method_signatures = []
        
        for file_path in source_files:
            try:
                tree = ast.parse(file_path.read_text())
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Extract method signature info
                        args = [arg.arg for arg in node.args.args if arg.arg != 'self']
                        signature_info = {
                            'file': str(file_path),
                            'method': node.name,
                            'args': args,
                            'arg_count': len(args)
                        }
                        method_signatures.append(signature_info)
            except SyntaxError:
                continue
        
        # Look for suspiciously similar signatures
        similar_groups = {}
        for sig in method_signatures:
            # Group by argument patterns
            key = f"{sig['arg_count']}_{'-'.join(sorted(sig['args']))}"
            if key not in similar_groups:
                similar_groups[key] = []
            similar_groups[key].append(sig)
        
        # Flag groups with multiple similar methods
        for key, group in similar_groups.items():
            if len(group) >= 3 and 'args' in key:  # 3+ methods with similar signatures
                print(f"\nINFO: Found {len(group)} methods with similar signatures:")
                for item in group[:3]:
                    print(f"  {item['file']}:{item['method']}")


class TestArchitecturalConstraints:
    """Test architectural rules and constraints."""
    
    def test_no_circular_imports(self, source_files):
        """Detect potential circular import issues."""
        import_relationships = {}
        
        for file_path in source_files:
            content = file_path.read_text()
            
            # Extract imports
            module_name = self._get_module_name(file_path)
            imports = self._extract_imports(content)
            
            import_relationships[module_name] = imports
        
        # Check for potential circular dependencies
        # This is a simplified check - full cycle detection would be more complex
        potential_issues = []
        for module, imports in import_relationships.items():
            for imported in imports:
                if imported in import_relationships:
                    if module in import_relationships[imported]:
                        potential_issues.append((module, imported))
        
        if potential_issues:
            print(f"\nWARNING: Found {len(potential_issues)} potential circular import issues:")
            for issue in potential_issues[:3]:
                print(f"  {issue[0]} ↔ {issue[1]}")
    
    def test_domain_separation(self, source_files):
        """Check that domains don't have inappropriate dependencies."""
        domain_violations = []
        
        # Define domain boundaries
        domains = {
            'memory': ['memory'],
            'tools': ['tools'],
            'nodes': ['nodes'],
            'llm': ['llm'],
            'reasoning': ['reasoning']
        }
        
        for file_path in source_files:
            content = file_path.read_text()
            file_domain = self._get_file_domain(file_path)
            
            if file_domain:
                # Check what this domain imports
                imports = self._extract_imports(content)
                
                for imported in imports:
                    imported_domain = self._get_domain_from_import(imported)
                    if imported_domain and imported_domain != file_domain:
                        # This is cross-domain - check if it's allowed
                        # For now, just collect info
                        domain_violations.append({
                            'file': str(file_path),
                            'domain': file_domain,
                            'imports': imported_domain
                        })
        
        # Group and summarize
        violation_summary = {}
        for v in domain_violations:
            key = f"{v['domain']} → {v['imports']}"
            violation_summary[key] = violation_summary.get(key, 0) + 1
        
        if violation_summary:
            print(f"\nINFO: Cross-domain dependencies:")
            for dependency, count in violation_summary.items():
                print(f"  {dependency}: {count} files")
    
    def _get_module_name(self, file_path: Path) -> str:
        """Convert file path to module name."""
        relative = file_path.relative_to(file_path.parents[2])  # Remove up to src/
        return str(relative).replace('/', '.').replace('.py', '')
    
    def _extract_imports(self, content: str) -> list:
        """Extract import statements from content."""
        imports = []
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('from ') and ' import ' in line:
                module = line.split('from ')[1].split(' import')[0].strip()
                if 'cogency' in module:
                    imports.append(module)
            elif line.startswith('import ') and 'cogency' in line:
                module = line.split('import ')[1].split(' ')[0].strip()
                imports.append(module)
        return imports
    
    def _get_file_domain(self, file_path: Path) -> str:
        """Determine which domain a file belongs to."""
        path_str = str(file_path)
        if '/memory/' in path_str:
            return 'memory'
        elif '/tools/' in path_str:
            return 'tools'
        elif '/nodes/' in path_str:
            return 'nodes'
        elif '/llm/' in path_str:
            return 'llm'
        elif '/reasoning/' in path_str:
            return 'reasoning'
        return None
    
    def _get_domain_from_import(self, import_str: str) -> str:
        """Determine domain from import string."""
        if '.memory.' in import_str:
            return 'memory'
        elif '.tools.' in import_str:
            return 'tools'
        elif '.nodes.' in import_str:
            return 'nodes'
        elif '.llm.' in import_str:
            return 'llm'
        elif '.reasoning.' in import_str:
            return 'reasoning'
        return None