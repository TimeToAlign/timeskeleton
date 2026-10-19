#!/usr/bin/env python
"""Emit the fixtures of the current schema version through timetoalign: build
the catalogue of ``scripts/fixtures``, replace the manifests of
``fixtures/<version>/`` (or of ``--output``) with each fixture and its minimal
twin, and check every pair; the fixtures of a released version, whose tag
``v<version>`` exists, are never overwritten.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

from fixtures.plan import CATALOGUE, plan
from fixtures.verify import check, twin_path

from timeskeleton import SCHEMA_VERSION, dumps

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPOSITORY_ROOT / "fixtures" / SCHEMA_VERSION


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, emit the fixtures and their twins, and check them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timetoalign-commit",
        required=True,
        help="short commit of the timetoalign checkout the interpreter runs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=FIXTURE_DIR,
        help=f"destination directory (default: fixtures/{SCHEMA_VERSION}/)",
    )
    args = parser.parse_args(argv)
    generator = f"timetoalign {version('timetoalign')} ({args.timetoalign_commit})"
    tag = f"v{SCHEMA_VERSION}"
    tagged = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), "tag", "--list", tag],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    if tag in tagged and args.output.resolve() == FIXTURE_DIR.resolve():
        raise SystemExit(
            f"{tag} is released; its fixtures in {FIXTURE_DIR} are frozen. "
            "Emit into another directory with --output."
        )

    planned = plan(args.output, generator)
    for directory in dict.fromkeys(case.directory for case in CATALOGUE):
        destination = args.output / directory
        destination.mkdir(parents=True, exist_ok=True)
        for stale in destination.glob("*.json"):
            stale.unlink()
    for fixture in planned:
        fixture.path.write_text(dumps(fixture.item.to_dict()), encoding="utf-8")
        twin_path(fixture.path).write_text(
            dumps(fixture.item.to_dict(minimal=True)), encoding="utf-8"
        )

    for fixture in planned:
        problems = check(
            fixture.path.read_text(encoding="utf-8"),
            twin_path(fixture.path).read_text(encoding="utf-8"),
            fixture.reader,
            fixture.source,
        )
        if problems:
            raise SystemExit(f"{fixture.path.name}: " + "; ".join(problems))
        display = (
            fixture.path.relative_to(REPOSITORY_ROOT)
            if fixture.path.is_relative_to(REPOSITORY_ROOT)
            else fixture.path
        )
        print(f"{display}: the fixture and its minimal twin hold")
    print(f"generator: {generator}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
