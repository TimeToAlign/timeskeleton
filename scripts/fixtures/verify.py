"""Pure checks for the fixture/twin laws and library round trips."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from timeskeleton import canonical_order, complete, dumps, minimal, unknown_keys


def twin_path(path: Path) -> Path:
    """Return the path of a fixture's ``<name>.minimal.json`` twin."""
    return path.with_name(f"{path.stem}.minimal.json")


def _library_order(value: dict[str, Any]) -> str:
    """Return a manifest's JSON text with sorted keys and arrays as they stand."""
    return json.dumps(value, sort_keys=True)


def check(
    fixture_text: str,
    twin_text: str,
    reader: type[Any],
    source: dict[str, Any],
) -> tuple[str, ...]:
    """Return the laws a fixture and its minimal twin break, empty if none.

    Both validate without unknown keys (a manifest that does not validate
    raises); ``minimal`` of the fixture is the twin and ``complete`` of the
    twin the fixture; the library, through ``reader``, reads both to objects
    that write the fixture and the twin byte for byte, each already in
    canonical order; and ``complete`` of the composed ``source`` is the
    fixture, so the library wrote back what the catalogue composed.
    """
    fixture, twin = json.loads(fixture_text), json.loads(twin_text)
    problems: list[str] = []
    for label, value in (("fixture", fixture), ("twin", twin)):
        keys = unknown_keys(value)
        if keys:
            problems.append(f"the {label} has unknown keys {keys}")
    if dumps(minimal(fixture)) != twin_text:
        problems.append("minimal(fixture) is not the twin")
    if dumps(complete(twin)) != fixture_text:
        problems.append("complete(twin) is not the fixture")
    for label, value in (("fixture", fixture), ("twin", twin)):
        read = reader.from_dict(value)
        written = read.to_dict()
        written_minimal = read.to_dict(minimal=True)
        if dumps(written) != fixture_text:
            problems.append(f"the {label} read and written is not byte-equal")
        if dumps(written_minimal) != twin_text:
            problems.append(f"the {label} read and written minimal is not byte-equal")
        if _library_order(canonical_order(written)) != _library_order(written):
            problems.append(f"the {label} read is written out of canonical order")
    if dumps(complete(source)) != fixture_text:
        problems.append("the library did not write back its manifest")
    return tuple(problems)
