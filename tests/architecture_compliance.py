"""Architecture compliance testing for Beauty Doctrine validation."""

import ast
from pathlib import Path


class ArchitectureValidator:
    """Validates canonical architecture against Beauty Doctrine principles."""

    def __init__(self, source_dir: str = "src/cogency"):
        self.source_dir = Path(source_dir)
        self.violations = []
        self.metrics = {}

    def validate_beauty_doctrine(self) -> dict:
        """Validate all Beauty Doctrine principles."""
        print("🎯 VALIDATING BEAUTY DOCTRINE COMPLIANCE")
        print("=" * 50)

        return {
            "line_counts": self._validate_line_counts(),
            "naming": self._validate_naming(),
            "simplicity": self._validate_simplicity(),
            "duplication": self._detect_duplication(),
            "dependencies": self._analyze_dependencies(),
        }

    def _validate_line_counts(self) -> dict:
        """Validate files follow <150 line Beauty Doctrine."""
        print("\n📏 VALIDATING LINE COUNTS (<150 lines)")
        print("-" * 40)

        violations = []
        compliant = []

        for py_file in self.source_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            with open(py_file) as f:
                line_count = sum(1 for line in f if line.strip())

            relative_path = py_file.relative_to(self.source_dir)

            if line_count > 150:
                violations.append((str(relative_path), line_count))
                print(f"❌ {relative_path}: {line_count} lines")
            else:
                compliant.append((str(relative_path), line_count))
                print(f"✅ {relative_path}: {line_count} lines")

        print(f"\n📊 SUMMARY: {len(compliant)} compliant, {len(violations)} violations")

        return {
            "violations": violations,
            "compliant": compliant,
            "total_files": len(compliant) + len(violations),
        }

    def _validate_naming(self) -> dict:
        """Validate naming follows 'reads like English' principle."""
        print("\n📝 VALIDATING NAMING CONVENTIONS")
        print("-" * 40)

        violations = []
        patterns = []

        for py_file in self.source_dir.rglob("*.py"):
            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        name = node.name
                        if name.startswith("_"):
                            continue  # Private functions OK

                        # Check for Beauty Doctrine violations
                        if len(name) > 20:
                            violations.append(
                                f"{py_file.relative_to(self.source_dir)}:{name} (too long)"
                            )
                        elif "get_" in name and "_data" in name:
                            violations.append(
                                f"{py_file.relative_to(self.source_dir)}:{name} (verbose)"
                            )
                        else:
                            patterns.append(name)

            except Exception:
                continue

        # Show naming patterns
        for violation in violations[:5]:  # Show first 5
            print(f"❌ {violation}")

        for pattern in patterns[:10]:  # Show first 10 good examples
            print(f"✅ {pattern}")

        return {
            "violations": violations,
            "good_patterns": patterns,
            "violation_count": len(violations),
        }

    def _validate_simplicity(self) -> dict:
        """Validate code follows simplicity principles."""
        print("\n🎯 VALIDATING SIMPLICITY PRINCIPLES")
        print("-" * 40)

        complexity_violations = []
        import_violations = []

        for py_file in self.source_dir.rglob("*.py"):
            try:
                with open(py_file) as f:
                    content = f.read()
                    tree = ast.parse(content)

                # Check for local imports (should be at module level)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        # Check if import is inside function
                        for parent in ast.walk(tree):
                            if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                                child == node for child in ast.walk(parent)
                            ):
                                import_violations.append(
                                    f"{py_file.relative_to(self.source_dir)}:{parent.name}"
                                )

                # Check for excessive nesting
                max_nesting = self._calculate_max_nesting(tree)
                if max_nesting > 4:
                    complexity_violations.append(
                        f"{py_file.relative_to(self.source_dir)}: nesting {max_nesting}"
                    )

            except Exception:
                continue

        for violation in complexity_violations:
            print(f"❌ Complex: {violation}")

        for violation in import_violations[:5]:
            print(f"❌ Local import: {violation}")

        return {
            "complexity_violations": complexity_violations,
            "import_violations": import_violations,
            "total_violations": len(complexity_violations) + len(import_violations),
        }

    def _detect_duplication(self) -> dict:
        """Detect code duplication violations."""
        print("\n🔍 DETECTING CODE DUPLICATION")
        print("-" * 40)

        # Simple duplication detection - check for repeated function signatures
        function_signatures = {}
        duplicates = []

        for py_file in self.source_dir.rglob("*.py"):
            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        sig = f"{node.name}({len(node.args.args)})"
                        if sig in function_signatures:
                            duplicates.append(
                                (
                                    sig,
                                    function_signatures[sig],
                                    str(py_file.relative_to(self.source_dir)),
                                )
                            )
                        else:
                            function_signatures[sig] = str(py_file.relative_to(self.source_dir))

            except Exception:
                continue

        for sig, file1, file2 in duplicates:
            print(f"⚠️  Duplicate signature: {sig} in {file1} and {file2}")

        return {"duplicates": duplicates, "duplicate_count": len(duplicates)}

    def _analyze_dependencies(self) -> dict:
        """Analyze import dependencies for circular imports."""
        print("\n🔗 ANALYZING DEPENDENCIES")
        print("-" * 40)

        imports = {}
        circular_risks = []

        for py_file in self.source_dir.rglob("*.py"):
            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                module_name = (
                    str(py_file.relative_to(self.source_dir)).replace("/", ".").replace(".py", "")
                )
                imports[module_name] = []

                for node in ast.walk(tree):
                    if (
                        isinstance(node, ast.ImportFrom)
                        and node.module
                        and node.module.startswith("cogency")
                    ):
                        imports[module_name].append(node.module)

            except Exception:
                continue

        # Simple circular dependency detection
        for module, deps in imports.items():
            for dep in deps:
                if dep in imports and module in imports[dep]:
                    circular_risks.append((module, dep))

        for module, dep in circular_risks:
            print(f"⚠️  Circular risk: {module} ↔ {dep}")

        return {"imports": imports, "circular_risks": circular_risks, "module_count": len(imports)}

    def _calculate_max_nesting(self, tree) -> int:
        """Calculate maximum nesting depth."""

        def get_depth(node, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                    child_depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, child_depth)
                else:
                    child_depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, child_depth)
            return max_depth

        return get_depth(tree)


def run_architecture_validation():
    """Run complete architecture validation suite."""
    validator = ArchitectureValidator()
    results = validator.validate_beauty_doctrine()

    print("\n" + "=" * 50)
    print("🎯 ARCHITECTURE COMPLIANCE SUMMARY")
    print("=" * 50)

    # Line count compliance
    line_results = results["line_counts"]
    total_files = line_results["total_files"]
    violations = len(line_results["violations"])
    compliance_rate = ((total_files - violations) / total_files * 100) if total_files > 0 else 0

    print(
        f"📏 Line Count Compliance: {compliance_rate:.1f}% ({total_files - violations}/{total_files} files)"
    )

    # Naming compliance
    naming_results = results["naming"]
    print(f"📝 Naming Violations: {naming_results['violation_count']}")

    # Simplicity compliance
    simplicity_results = results["simplicity"]
    print(f"🎯 Simplicity Violations: {simplicity_results['total_violations']}")

    # Duplication detection
    duplication_results = results["duplication"]
    print(f"🔍 Code Duplication: {duplication_results['duplicate_count']} cases")

    # Dependency analysis
    dependency_results = results["dependencies"]
    print(f"🔗 Circular Dependencies: {len(dependency_results['circular_risks'])} risks")

    # Overall grade
    total_violations = (
        violations
        + naming_results["violation_count"]
        + simplicity_results["total_violations"]
        + duplication_results["duplicate_count"]
        + len(dependency_results["circular_risks"])
    )

    if total_violations == 0:
        grade = "A+ (Perfect Beauty Doctrine Compliance)"
    elif total_violations <= 5:
        grade = "A (Excellent Architecture)"
    elif total_violations <= 10:
        grade = "B+ (Good Architecture)"
    else:
        grade = "B (Needs Improvement)"

    print(f"\n🏆 OVERALL ARCHITECTURE GRADE: {grade}")
    print(f"📊 Total Violations: {total_violations}")

    return results


if __name__ == "__main__":
    run_architecture_validation()
