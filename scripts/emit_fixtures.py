#!/usr/bin/env python
"""Emit the golden fixtures of the current schema version through timetoalign.

This script is the only writer of ``fixtures/<version>/*.json``. Every
document is built with timetoalign's public API, serialized with
``Timeline.to_dict()`` (the eventless payload) and, after writing, read back
and round-tripped through ``Timeline.from_dict`` to prove that the library
reproduces each timeline manifest byte for byte.

Run it with an interpreter that has the timetoalign revision the schema
describes::

    python scripts/emit_fixtures.py --timetoalign-commit "$(git -C <timetoalign checkout> rev-parse --short HEAD)"

The commit is recorded in every document's ``meta.generator`` next to the
installed timetoalign version, and ``fixtures/README.md`` repeats both.
"""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from typing import Any

from timetoalign import (
    ContinuousGraphicalTimeline,
    ContinuousLogicalTimeline,
    ContinuousPhysicalTimeline,
    DiscreteGraphicalTimeline,
    DiscreteLogicalTimeline,
    DiscretePhysicalTimeline,
    Timeline,
)

SCHEMA_VERSION = "0.1.0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPOSITORY_ROOT / "fixtures" / SCHEMA_VERSION


def with_children(
    cls: type[Timeline],
    unit: str,
    length: Any,
    children: list[tuple[Any, Any]],
) -> Timeline:
    """Build a timeline of ``cls`` with one child per ``(length, offset)`` pair."""
    parent = cls(length=length, unit=unit)
    for child_length, offset in children:
        parent.add_child(cls(length=child_length, unit=unit), offset)
    return parent


def build_documents() -> dict[str, list[Timeline]]:
    """Return the fixture name to top-level timelines, in emission order.

    Timeline ids are assigned by the library in construction order, so the
    order below is part of the fixture contract.
    """
    documents: dict[str, list[Timeline]] = {}
    documents["continuous_logical"] = [
        with_children(
            ContinuousLogicalTimeline, "quarters", 12, [(4, Fraction(1, 3)), (3, 2)]
        )
    ]
    documents["discrete_logical"] = [
        with_children(
            DiscreteLogicalTimeline,
            "ticks",
            Fraction(480),
            [(Fraction(120), Fraction(3)), (Fraction(96), Fraction(7))],
        )
    ]
    documents["continuous_physical"] = [
        with_children(
            ContinuousPhysicalTimeline, "seconds", 12.5, [(4.25, 0.5), (3.0, 6.0)]
        )
    ]
    documents["discrete_physical"] = [
        with_children(
            DiscretePhysicalTimeline,
            "samples",
            Fraction(44100),
            [(Fraction(11025), Fraction(100)), (Fraction(2205), Fraction(20000))],
        )
    ]
    documents["continuous_graphical"] = [
        with_children(
            ContinuousGraphicalTimeline, "points", 600.0, [(200.0, 10.0), (150.0, 300.0)]
        )
    ]
    documents["discrete_graphical"] = [
        with_children(
            DiscreteGraphicalTimeline,
            "pixels",
            Fraction(1920),
            [(Fraction(640), Fraction(16)), (Fraction(480), Fraction(1000))],
        )
    ]
    with_region = with_children(
        ContinuousLogicalTimeline, "quarters", 12, [(4, Fraction(1, 3)), (3, 2)]
    )
    with_region.create_region("theme", 2, 6)
    documents["with_region"] = [with_region]
    documents["empty"] = []
    grandchild = ContinuousLogicalTimeline(length=2, unit="quarters")
    child = ContinuousLogicalTimeline(length=8, unit="quarters")
    child.add_child(grandchild, Fraction(3, 2))
    nested = ContinuousLogicalTimeline(length=16, unit="quarters")
    nested.add_child(child, 4)
    documents["nested"] = [nested]
    return documents


def document(timelines: list[Timeline], generator: str) -> dict[str, Any]:
    """Wrap top-level timelines in the document envelope."""
    return {
        "meta": {"schema_version": SCHEMA_VERSION, "generator": generator},
        "manifest": {"timelines": {tl.id: tl.to_dict() for tl in timelines}},
    }


def write(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=False)
        handle.write("\n")


def check_round_trip(path: Path) -> int:
    """Return the number of manifests in ``path`` that survive from_dict/to_dict."""
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    count = 0
    for timeline_id, manifest in data["manifest"]["timelines"].items():
        rebuilt = Timeline.from_dict(manifest).to_dict()
        if rebuilt != manifest:
            raise SystemExit(
                f"{path.name}: timeline {timeline_id!r} does not round-trip through "
                f"timetoalign.\nexpected: {json.dumps(manifest, indent=2)}\n"
                f"got:      {json.dumps(rebuilt, indent=2)}"
            )
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--timetoalign-commit",
        required=True,
        help="short commit of the timetoalign checkout the interpreter runs",
    )
    args = parser.parse_args(argv)
    generator = f"timetoalign {version('timetoalign')} ({args.timetoalign_commit})"

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for stale in FIXTURE_DIR.glob("*.json"):
        stale.unlink()
    written: list[Path] = []
    for name, timelines in build_documents().items():
        path = FIXTURE_DIR / f"{name}.json"
        data = document(timelines, generator)
        write(path, data)
        written.append(path)

    for path in written:
        manifests = check_round_trip(path)
        print(f"{path.relative_to(REPOSITORY_ROOT)}: {manifests} manifest(s) round-trip")
    print(f"generator: {generator}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
