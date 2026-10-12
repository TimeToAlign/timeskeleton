#!/usr/bin/env python3
"""Check that every version declaration in the repository agrees.

A timeskeleton release is one version carried by:

* ``python/pyproject.toml`` (``project.version``),
* ``js/package.json`` (``version``),
* ``SCHEMA_VERSION`` in ``python/src/timeskeleton/validate.py`` and in
  ``js/src/validate.ts``,
* the schema of the version, whose ``$id`` and ``meta.schema_version``
  constant carry the version: the one file
  ``schema/timeskeleton-<version>.schema.json`` up to 0.6.0, or from 0.7.0 on
  the directory ``schema/<version>/`` with the documents ``core``,
  ``timeline``, ``group`` and ``bundle`` (each ``<name>.schema.json``, each
  ``$id`` naming the version, the constant in ``core``'s ``Meta``); the schemas
  of older versions remain beside it,
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


DOCUMENTS = ("core", "timeline", "group", "bundle")


def _read(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _const(meta: dict) -> str | None:
    return meta.get("properties", {}).get("schema_version", {}).get("const")


def schema_declarations(version: str) -> dict[str, str | None]:
    """Collect the declarations that depend on the agreed version."""
    found: dict[str, str | None] = {}
    single = REPOSITORY_ROOT / "schema" / f"timeskeleton-{version}.schema.json"
    directory = REPOSITORY_ROOT / "schema" / version
    if single.is_file():
        schema = _read(single)
        schema_id = schema.get("$id", "")
        found["schema file"] = version
        found["schema $id"] = version if f"/{version}/" in schema_id else schema_id
        meta = schema.get("properties", {}).get("meta", {})
        found["schema meta.schema_version const"] = _const(meta)
    elif directory.is_dir():
        for name in DOCUMENTS:
            path = directory / f"{name}.schema.json"
            if not path.is_file():
                found[f"schema document {name}"] = None
                continue
            schema_id = _read(path).get("$id", "")
            found[f"schema document {name} $id"] = (
                version if schema_id.endswith(f"/{version}/{name}.schema.json") else schema_id
            )
        core = directory / "core.schema.json"
        meta = _read(core).get("$defs", {}).get("Meta", {}) if core.is_file() else {}
        found["schema meta.schema_version const"] = _const(meta)
    else:
        found["schema file"] = None
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
