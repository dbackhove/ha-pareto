"""A translation file that drifts from strings.json shows raw keys in the UI."""

import json
import pathlib

BASE = pathlib.Path("custom_components/pareto")


def load(name: str) -> dict:
    return json.loads((BASE / name).read_text(encoding="utf-8"))


def keys(node, prefix=""):
    found = set()
    for key, value in node.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            found |= keys(value, path)
        else:
            found.add(path)
    return found


def test_english_translation_matches_strings():
    assert keys(load("strings.json")) == keys(load("translations/en.json"))


def test_german_translation_matches_strings():
    assert keys(load("strings.json")) == keys(load("translations/de.json"))


def test_manifest_points_at_the_real_repository():
    manifest = load("manifest.json")
    assert manifest["codeowners"] == ["@dbackhove"]
    assert manifest["documentation"] == "https://github.com/dbackhove/ha-pareto"
    assert manifest["issue_tracker"] == "https://github.com/dbackhove/ha-pareto/issues"
