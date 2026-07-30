"""ranking.py must stay free of Home Assistant imports so it tests without fixtures."""

import ast
import pathlib


def test_ranking_module_has_no_homeassistant_imports():
    source = pathlib.Path("custom_components/pareto/ranking.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)

    offenders = [name for name in imported if name.split(".")[0] == "homeassistant"]
    assert offenders == [], f"ranking.py must stay HA-free, found: {offenders}"
