from __future__ import annotations

import ast
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements.txt"

IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    "assets",
    "logs",
}

PACKAGE_NAMES = {
    "colorama": "colorama>=0.4.6",
    "psutil": "psutil>=6.1.0",
    "rich": "rich>=13.9.0",
}


def main() -> None:
    local_modules = discover_local_modules()
    required_packages = discover_required_packages(local_modules)
    existing_lines = read_requirements()

    merged = list(existing_lines)
    normalized = {line.split("==")[0].split(">=")[0].lower() for line in merged}

    for package in sorted(required_packages):
        package_name = package.split("==")[0].split(">=")[0].lower()
        if package_name not in normalized:
            merged.append(package)
            normalized.add(package_name)

    REQUIREMENTS_PATH.write_text("\n".join(merged).strip() + "\n", encoding="utf-8")


def discover_local_modules() -> set[str]:
    modules = set()
    for path in PROJECT_ROOT.iterdir():
        if path.name in IGNORED_DIRECTORIES:
            continue
        if path.is_file() and path.suffix == ".py":
            modules.add(path.stem)
        elif path.is_dir() and (path / "__init__.py").exists():
            modules.add(path.name)
    return modules


def discover_required_packages(local_modules: set[str]) -> set[str]:
    packages: set[str] = set()
    for path in iter_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            for module_name in imported_module_names(node):
                if is_third_party(module_name, local_modules):
                    packages.add(PACKAGE_NAMES.get(module_name, module_name))
    return packages


def iter_python_files() -> list[Path]:
    files = []
    for path in PROJECT_ROOT.rglob("*.py"):
        if any(part in IGNORED_DIRECTORIES for part in path.relative_to(PROJECT_ROOT).parts):
            continue
        files.append(path)
    return files


def imported_module_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name.split(".")[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        return [node.module.split(".")[0]]
    return []


def is_third_party(module_name: str, local_modules: set[str]) -> bool:
    if module_name in local_modules:
        return False
    if module_name in sys.stdlib_module_names:
        return False
    return module_name not in {"tkinter"}


def read_requirements() -> list[str]:
    if not REQUIREMENTS_PATH.exists():
        return []
    lines = REQUIREMENTS_PATH.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


if __name__ == "__main__":
    main()
