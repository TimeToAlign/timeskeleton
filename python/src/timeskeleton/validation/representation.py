"""Finite-number and own-axis representation rules."""

from __future__ import annotations

import math
from collections.abc import Iterator, Mapping
from fractions import Fraction
from typing import Any

from ..manifest import _exact, spell
from .diagnostics import (
    SchemaValidationError,
    _entries,
    _Path,
    json_pointer,
    number_type_of,
)

_ARTICLES = {"int": "an int", "float": "a float", "fraction": "a fraction"}

_MAP_NUMBER_MEMBERS = {
    "IntervalToConstantMap": {"arrays": ("boundaries",)},
    "LinearMap": {"values": ("scalar", "offset")},
    "MetricMap": {"arrays": ("starts", "lengths")},
    "PiecewiseMap": {"arrays": ("breaks",)},
    "QuartersToFloatingMeasures": {"arrays": ("x_values", "y_values")},
    "QuartersToMeasureNumber": {"arrays": ("boundaries",)},
    "QuartersToTicks": {"values": ("scalar",)},
    "SamplesToSeconds": {"values": ("scalar",)},
    "ScalarMap": {"values": ("scalar",)},
    "SecondsToSamples": {"values": ("scalar",)},
    "ShiftMap": {"values": ("offset",)},
    "TableMap": {"arrays": ("x_values", "y_values")},
    "TicksToQuarters": {"values": ("scalar",)},
}

_MAP_NESTED_MEMBERS = {
    "BeatInMeasureMap": {"values": ("meter_map",)},
    "ChainMap": {"arrays": ("maps",)},
    "CombinationMap": {"records": ("maps",)},
    "MetricalPositionMap": {"values": ("meter_map",)},
    "PiecewiseMap": {"arrays": ("maps",)},
}


def _written_as(value: Any) -> str:
    if isinstance(value, list):
        return "fraction"
    return "int" if isinstance(value, int) else "float"


def _represents(value: Any, number_type: str) -> bool:
    if number_type == "fraction":
        return isinstance(value, list)
    if isinstance(value, list):
        return False
    if number_type == "float":
        return not isinstance(value, int) or rewritten(value, "float") is not None
    return isinstance(value, int) or value.is_integer()


def rewritten(value: Any, number_type: str) -> str | None:
    """Return an exact rewriting in ``number_type``, or ``None``."""
    exact = _exact(value)
    if number_type == "fraction":
        return spell([exact.numerator, exact.denominator])
    if number_type == "int":
        return spell(exact.numerator) if exact.denominator == 1 else None
    try:
        double = exact.numerator / exact.denominator
    except OverflowError:
        return None
    return spell(double) if Fraction(double) == exact else None


def _fraction_member_problems(
    value: Any, path: _Path
) -> Iterator[SchemaValidationError]:
    if not isinstance(value, list):
        return
    for index, member in enumerate(value):
        if not isinstance(member, float):
            continue
        name = "numerator" if index == 0 else "denominator"
        yield SchemaValidationError(
            "representation",
            (*path, index),
            f"fraction {name} {spell(member)} is a float: write "
            f"{rewritten(member, 'int')}",
        )


def _representation_problem(
    key: str, owner: Mapping[str, Any], path: _Path, number_type: str
) -> Iterator[SchemaValidationError]:
    value = owner.get(key)
    if value is None:
        return
    yield from _fraction_member_problems(value, (*path, key))
    if _represents(value, number_type):
        return
    fix = rewritten(value, number_type) or _ARTICLES[number_type]
    yield SchemaValidationError(
        "representation",
        (*path, key),
        f"{key} {spell(value)} of '{owner['id']}' is {_ARTICLES[_written_as(value)]} "
        f"on {_ARTICLES[number_type]} axis: write {fix}",
    )


def _conversion_map_fraction_problems(
    conversion_map: Mapping[str, Any], path: _Path
) -> Iterator[SchemaValidationError]:
    map_type = conversion_map["type"]
    members = _MAP_NUMBER_MEMBERS.get(map_type, {})
    for key in members.get("values", ()):
        yield from _fraction_member_problems(conversion_map.get(key), (*path, key))
    for key in members.get("arrays", ()):
        for index, value in enumerate(_entries(conversion_map, key)):
            yield from _fraction_member_problems(value, (*path, key, index))

    nested_members = _MAP_NESTED_MEMBERS.get(map_type, {})
    for key in nested_members.get("values", ()):
        nested = conversion_map.get(key)
        if isinstance(nested, Mapping):
            yield from _conversion_map_fraction_problems(nested, (*path, key))
    for key in nested_members.get("arrays", ()):
        for index, nested in enumerate(_entries(conversion_map, key)):
            yield from _conversion_map_fraction_problems(nested, (*path, key, index))
    for key in nested_members.get("records", ()):
        nested_maps = conversion_map.get(key)
        if isinstance(nested_maps, Mapping):
            for name, nested in nested_maps.items():
                if isinstance(nested, Mapping):
                    yield from _conversion_map_fraction_problems(
                        nested, (*path, key, name)
                    )


def _timeline_representation(
    timeline: Mapping[str, Any], path: _Path, offset_type: str | None
) -> Iterator[SchemaValidationError]:
    own = number_type_of(timeline)
    yield from _representation_problem("offset", timeline, path, offset_type or own)
    yield from _representation_problem("length", timeline, path, own)
    for index, region in enumerate(_entries(timeline, "regions")):
        for key in ("start", "end"):
            yield from _representation_problem(
                key, region, (*path, "regions", index), own
            )
    flow = timeline.get("flow_control") or {}
    for member, keys in (
        ("breaks", ("coordinate",)),
        ("jumps", ("from_coordinate", "to_coordinate")),
        ("markers", ("coordinate",)),
    ):
        for index, entry in enumerate(_entries(flow, member)):
            for key in keys:
                yield from _representation_problem(
                    key, entry, (*path, "flow_control", member, index), own
                )
    for index, conversion_map in enumerate(_entries(timeline, "conversion_maps")):
        yield from _conversion_map_fraction_problems(
            conversion_map, (*path, "conversion_maps", index)
        )
    measure_map = timeline.get("measure_map")
    if isinstance(measure_map, list):
        for index, row in enumerate(measure_map):
            if not isinstance(row, Mapping):
                continue
            for key in (
                "qstamp",
                "nominal_length",
                "actual_length",
                "offset_within_measure",
            ):
                yield from _fraction_member_problems(
                    row.get(key), (*path, "measure_map", index, key)
                )
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _timeline_representation(child, (*path, "children", index), own)


def representation_problems(
    manifest: Mapping[str, Any],
) -> Iterator[SchemaValidationError]:
    """Yield fraction-member and own-axis representation violations in order."""
    for index, root in enumerate(_entries(manifest, "timelines")):
        yield from _timeline_representation(root, ("timelines", index), None)


def finite_number_problems(
    value: Any,
    path: _Path = (),
    owner_id: str | None = None,
    owner_key: str | None = None,
) -> Iterator[SchemaValidationError]:
    """Yield non-finite float leaves before schema validation."""
    if isinstance(value, float) and not math.isfinite(value):
        detail = (
            f"{owner_key} of '{owner_id}' is not a finite number"
            if owner_id is not None and owner_key is not None
            else f"{json_pointer(path)} is not a finite number"
        )
        yield SchemaValidationError("finite_number", path, detail)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            yield from finite_number_problems(item, (*path, index), owner_id, owner_key)
        return
    if not isinstance(value, Mapping):
        return
    identifier = value.get("id")
    current_id = identifier if isinstance(identifier, str) else owner_id
    for key, item in value.items():
        yield from finite_number_problems(item, (*path, key), current_id, key)
