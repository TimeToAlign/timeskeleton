#!/usr/bin/env python3
"""Check that every version declaration in the repository agrees.

A timeskeleton release is one version carried by:

* ``python/pyproject.toml`` (``project.version``),
* ``js/package.json`` (``version``),
* ``SCHEMA_VERSION`` in ``python/src/timeskeleton/validate.py`` and in
  ``js/src/validate.ts``,
* the schema document ``schema/<version>/timeskeleton.schema.json``, whose
  ``$id`` names the version and whose version marker ``timeskeleton`` is the
  constant of the version; it is the only version under ``schema/``,
* a non-empty fixture directory ``fixtures/<version>/``.

Usage::

    python scripts/check_versions.py            # the declarations agree with each other
    python scripts/check_versions.py --tag v0.5.0   # ... and with the release tag

Exit status 0 prints the agreed version; 1 lists every disagreement.
Standard library only, so the release workflow can run it before any
environment is set up.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CONSTANT = re.compile(r'^(?:export const |)SCHEMA_VERSION(?:: str)? = "([^"]+)";?$', re.M)


def declarations() -> dict[str, str | None]:
    """Collect every version declaration, ``None`` where one is missing."""
    found: dict[str, str | None] = {}

    pyproject = REPOSITORY_ROOT / "python" / "pyproject.toml"
    with pyproject.open("rb") as handle:
        found["python/pyproject.toml"] = tomllib.load(handle)["project"].get("version")

    package_json = REPOSITORY_ROOT / "js" / "package.json"
    with package_json.open(encoding="utf-8") as handle:
        found["js/package.json"] = json.load(handle).get("version")

    for source in ("python/src/timeskeleton/validate.py", "js/src/validate.ts"):
        text = (REPOSITORY_ROOT / source).read_text(encoding="utf-8")
        match = CONSTANT.search(text)
        found[source] = match.group(1) if match else None

    return found


def _read(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def schema_declarations(version: str) -> dict[str, str | None]:
    """Collect the declarations that depend on the agreed version."""
    found: dict[str, str | None] = {}
    path = REPOSITORY_ROOT / "schema" / version / "timeskeleton.schema.json"
    if path.is_file():
        schema = _read(path)
        schema_id = schema.get("$id", "")
        found["schema $id"] = (
            version if schema_id.endswith(f"/{version}/timeskeleton.schema.json") else schema_id
        )
        root = schema.get("$defs", {}).get("TimeSkeleton", {})
        marker = root.get("properties", {}).get("timeskeleton", {})
        found["schema timeskeleton const"] = marker.get("const")
    else:
        found["schema document"] = None
    others = sorted(p.name for p in (REPOSITORY_ROOT / "schema").iterdir() if p.name != version)
    found["schema versions"] = version if not others else ", ".join([version, *others])
    fixtures = REPOSITORY_ROOT / "fixtures" / version
    found["fixtures directory"] = version if any(fixtures.glob("*.json")) else None
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--tag", help="release tag that must carry the version, e.g. v0.5.0")
    args = parser.parse_args(argv)

    found = declarations()
    if args.tag is not None:
        found["tag"] = args.tag[1:] if args.tag.startswith("v") else None

    versions = {value for value in found.values() if value is not None}
    version = next(iter(versions)) if len(versions) == 1 else None
    if version is not None:
        found.update(schema_declarations(version))

    disagreements = {
        name: value for name, value in found.items() if value is None or value != version
    }
    if disagreements:
        print("version declarations disagree:", file=sys.stderr)
        for name, value in found.items():
            marker = "  " if name not in disagreements else "! "
            print(f"{marker}{name}: {value if value is not None else '(missing)'}", file=sys.stderr)
        return 1
    print(version)
    return 0


if __name__ == "__main__":
    sys.exit(main())
