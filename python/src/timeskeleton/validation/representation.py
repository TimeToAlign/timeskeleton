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


def _representation_problem(
    key: str, owner: Mapping[str, Any], path: _Path, number_type: str
) -> Iterator[SchemaValidationError]:
    value = owner.get(key)
    if value is None or _represents(value, number_type):
        return
    fix = rewritten(value, number_type) or _ARTICLES[number_type]
    yield SchemaValidationError(
        "representation",
        (*path, key),
        f"{key} {spell(value)} of '{owner['id']}' is {_ARTICLES[_written_as(value)]} "
        f"on {_ARTICLES[number_type]} axis: write {fix}",
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
    for index, entry in enumerate(_entries(timeline, "flow_control")):
        yield from _representation_problem(
            "coordinate", entry, (*path, "flow_control", index), own
        )
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _timeline_representation(child, (*path, "children", index), own)


def representation_problems(
    manifest: Mapping[str, Any],
) -> Iterator[SchemaValidationError]:
    """Yield own-axis representation violations in manifest order."""
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
