import ast
from pathlib import Path


def _imports_in_file(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.add(name.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)

    return imports


def _assert_no_imports(paths: list[Path], *, banned_prefixes: tuple[str, ...]) -> None:
    violations: list[str] = []
    for path in paths:
        for module in sorted(_imports_in_file(path)):
            if module.startswith(banned_prefixes):
                violations.append(f"{path}: imports {module}")
    assert not violations, "Boundary violations:\n" + "\n".join(violations)


def test_core_does_not_import_lib() -> None:
    core = sorted(Path("src/cogency/core").glob("*.py"))
    _assert_no_imports(core, banned_prefixes=("cogency.lib",))


def test_protocols_are_pure() -> None:
    protocols = [Path("src/cogency/core/protocols.py")]
    _assert_no_imports(
        protocols, banned_prefixes=("cogency.lib", "cogency.context", "cogency.tools")
    )


def test_tools_do_not_import_core_agent() -> None:
    tools = sorted(Path("src/cogency/tools").glob("*.py"))
    _assert_no_imports(tools, banned_prefixes=("cogency.core.agent",))
