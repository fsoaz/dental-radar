import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"


def _imports_under(root: Path) -> list[tuple[Path, str]]:
    imports: list[tuple[Path, str]] = []
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                imports.append((path, node.module))
            elif isinstance(node, ast.Import):
                imports.extend((path, alias.name) for alias in node.names)
    return imports


def test_application_does_not_import_infrastructure() -> None:
    violations = [
        f"{path.relative_to(APP_ROOT)} imports {module}"
        for path, module in _imports_under(APP_ROOT / "application")
        if module == "app.infrastructure" or module.startswith("app.infrastructure.")
    ]
    assert violations == []


def test_domain_does_not_import_outer_layers() -> None:
    forbidden = ("app.application", "app.infrastructure")
    violations = [
        f"{path.relative_to(APP_ROOT)} imports {module}"
        for path, module in _imports_under(APP_ROOT / "domain")
        if any(module == prefix or module.startswith(f"{prefix}.") for prefix in forbidden)
    ]
    assert violations == []
