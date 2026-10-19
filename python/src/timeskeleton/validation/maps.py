"""Conversion-map rules: the members of a map that must agree."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from ..manifest import _exact, spell
from .diagnostics import SchemaValidationError, _entries, _Path

MEASURE_VIEWS = frozenset(
    {"MeasureRecordMap", "MeasureNumberMap", "FloatingMeasureMap", "MeasureBeatMap"}
)
"""The conversion map types that read a measure map."""


def _held(
    conversion_map: Mapping[str, Any], path: _Path
) -> Iterator[tuple[Any, _Path]]:
    yield conversion_map, path
    maps = conversion_map.get("maps")
    if isinstance(maps, list):
        for index, entry in enumerate(maps):
            yield from _held(entry, (*path, "maps", index))
    elif isinstance(maps, Mapping):
        for name in sorted(maps):
            yield from _held(maps[name], (*path, "maps", name))


def timeline_maps(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[tuple[Mapping[str, Any], _Path]]:
    """Yield a timeline's conversion maps with their paths, each before those it holds.

    A ``CombinationMap``'s outputs carry no order; they are visited by name, in
    code-point order.
    """
    for index, entry in enumerate(_entries(timeline, "conversion_maps")):
        yield from _held(entry, (*path, "conversion_maps", index))


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
    conversion_map: Mapping[str, Any], path: _Path
) -> Iterator[SchemaValidationError]:
    identifier = conversion_map["id"]
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
    """Yield the map rules a timeline tree breaks: arrays that must agree."""
    for conversion_map, at in timeline_maps(timeline, path):
        yield from _map_problems(conversion_map, at)
    for index, child in enumerate(_entries(timeline, "children")):
        yield from timeline_map_problems(child, (*path, "children", index))
