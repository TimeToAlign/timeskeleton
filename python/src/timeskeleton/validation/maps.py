"""Conversion-map rules: the source units and the members of a map that must agree."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from ..manifest import _exact, spell
from .diagnostics import SchemaValidationError, _entries, _Path

MEASURE_VIEWS = frozenset(
    {"MeasureRecordMap", "MeasureNumberMap", "FloatingMeasureMap", "MeasureBeatMap"}
)
"""The conversion map types that read a measure map."""


_Reader = tuple[str, str] | None
"""What a map converts from: the unit its source unit must be and who demands it."""


def _held(
    conversion_map: Mapping[str, Any], path: _Path, reader: _Reader
) -> Iterator[tuple[Any, _Path, _Reader]]:
    yield conversion_map, path, reader
    source = conversion_map.get("source_unit")
    holder = (
        None
        if source is None
        else (source, f"its {conversion_map['type']} {conversion_map['id']!r}")
    )
    maps = conversion_map.get("maps")
    if isinstance(maps, list):
        chain = conversion_map["type"] == "ChainMap"
        for index, entry in enumerate(maps):
            first = not chain or index == 0
            yield from _held(entry, (*path, "maps", index), holder if first else None)
    elif isinstance(maps, Mapping):
        for name in sorted(maps):
            yield from _held(maps[name], (*path, "maps", name), holder)


def _timeline_held(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[tuple[Mapping[str, Any], _Path, _Reader]]:
    reader = (timeline["unit"], f"its timeline {timeline['id']!r}")
    for index, entry in enumerate(_entries(timeline, "conversion_maps")):
        yield from _held(entry, (*path, "conversion_maps", index), reader)


def timeline_maps(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[tuple[Mapping[str, Any], _Path]]:
    """Yield a timeline's conversion maps with their paths, each before those it holds.

    A ``CombinationMap``'s outputs carry no order; they are visited by name, in
    code-point order.
    """
    for conversion_map, at, _ in _timeline_held(timeline, path):
        yield conversion_map, at


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def _increasing(
    conversion_map: Mapping[str, Any], key: str, noun: str, path: _Path
) -> Iterator[SchemaValidationError]:
    values = conversion_map[key]
    for index in range(1, len(values)):
        if _exact(values[index]) <= _exact(values[index - 1]):
            yield SchemaValidationError(
                "conversion_map",
                (*path, key, index),
                f"{noun} {spell(values[index])} of {conversion_map['type']} "
                f"{conversion_map['id']!r} does not exceed the one before it",
            )


def _map_problems(
    conversion_map: Mapping[str, Any], path: _Path, reader: _Reader
) -> Iterator[SchemaValidationError]:
    identifier = conversion_map["id"]
    source = conversion_map.get("source_unit")
    if reader is not None and source is not None and source != reader[0]:
        yield SchemaValidationError(
            "conversion_map",
            (*path, "source_unit"),
            f"{conversion_map['type']} {identifier!r} has source unit {source!r}, "
            f"{reader[1]} has {reader[0]!r}",
        )
    if conversion_map["type"] == "TableMap":
        x_values, y_values = conversion_map["x_values"], conversion_map["y_values"]
        if len(x_values) != len(y_values):
            yield SchemaValidationError(
                "conversion_map",
                (*path, "y_values"),
                f"TableMap {identifier!r} has {len(x_values)} x values and "
                f"{len(y_values)} y values",
            )
        yield from _increasing(conversion_map, "x_values", "x value", path)
    elif conversion_map["type"] == "PiecewiseMap":
        breaks, maps = conversion_map["breaks"], conversion_map["maps"]
        if len(maps) != len(breaks) - 1:
            yield SchemaValidationError(
                "conversion_map",
                (*path, "maps"),
                f"PiecewiseMap {identifier!r} has {_count(len(maps), 'map')} for "
                f"{len(breaks)} breaks; it needs {_count(len(breaks) - 1, 'map')}",
            )
        yield from _increasing(conversion_map, "breaks", "break", path)


def timeline_map_problems(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[SchemaValidationError]:
    """Yield the map rules a timeline tree breaks: source units, arrays that agree.

    A map attached to a timeline converts from the timeline's unit; a map a
    ``PiecewiseMap`` or ``CombinationMap`` holds, and a ``ChainMap``'s first
    map, from its holder's source unit. A null source unit on either side
    checks nothing.
    """
    for conversion_map, at, reader in _timeline_held(timeline, path):
        yield from _map_problems(conversion_map, at, reader)
    for index, child in enumerate(_entries(timeline, "children")):
        yield from timeline_map_problems(child, (*path, "children", index))
