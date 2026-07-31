"""The version lives in three files and they have to agree.

`manifest.json` is the one Home Assistant and HACS read, and it is also where
the card's cache-busting `?v=` comes from. The other two are bookkeeping. All
three get bumped by hand, which is exactly the kind of edit that goes half
done and stays unnoticed until a browser serves a stale card bundle.
"""

import json
import re
import tomllib
from pathlib import Path

REPO = Path(__file__).parent.parent
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def manifest_version() -> str:
    return json.loads((REPO / "custom_components" / "pareto" / "manifest.json").read_text())[
        "version"
    ]


def pyproject_version() -> str:
    return tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["version"]


def package_version() -> str:
    return json.loads((REPO / "frontend" / "package.json").read_text())["version"]


def test_all_three_files_carry_the_same_version():
    assert manifest_version() == pyproject_version() == package_version()


def test_the_version_is_a_plain_semver():
    """The release workflow compares it against a `vX.Y.Z` tag, so anything
    else -- a suffix, a date, a stray space -- breaks tagging."""
    assert SEMVER.match(manifest_version())
