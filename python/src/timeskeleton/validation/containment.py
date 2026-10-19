"""Timeline containment rules."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from fractions import Fraction
from itertools import pairwise
from typing import Any

from ..manifest import _exact, spell
from .diagnostics import SchemaValidationError, _entries, _Path, number_type_of
from .representation import rewritten


def offset_order(children: list[Any]) -> list[int]:
    """Return child indices in exact offset order, ties by id."""
    return sorted(
        range(len(children)),
        key=lambda index: (_exact(children[index]["offset"]), children[index]["id"]),
    )


def child_ends(timeline: Mapping[str, Any]) -> list[Fraction | None]:
    """Return each child's end, deriving an unknown segment end from its successor."""
    children = _entries(timeline, "children")
    ends: list[Fraction | None] = [
        _exact(child["offset"]) + _exact(child["length"])
        if child.get("length") is not None and child["unit"] == timeline["unit"]
        else None
        for child in children
    ]
    if timeline.get("is_segment_line") is True:
        order = offset_order(children)
        for index, successor in pairwise(order):
            if children[index].get("length") is None:
                ends[index] = _exact(children[successor]["offset"])
    return ends


def timeline_containment_problems(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[SchemaValidationError]:
    """Yield children off their parent's axis or beyond its known end."""
    length = timeline.get("length")
    ends = child_ends(timeline)
    for index, child in enumerate(_entries(timeline, "children")):
        at = (*path, "children", index)
        offset = _exact(child["offset"])
        if child["unit"] != timeline["unit"]:
            yield SchemaValidationError(
                "child_unit",
                (*at, "unit"),
                f"child '{child['id']}' has unit '{child['unit']}', its parent "
                f"'{timeline['id']}' has '{timeline['unit']}'",
            )
        end = ends[index]
        if length is not None and offset > _exact(length):
            yield SchemaValidationError(
                "child_offset",
                (*at, "offset"),
                f"offset {spell(child['offset'])} of '{child['id']}' is beyond the "
                f"length {spell(length)} of its parent '{timeline['id']}'",
            )
        elif length is not None and end is not None and end > _exact(length):
            pair = [end.numerator, end.denominator]
            yield SchemaValidationError(
                "child_end",
                (*at, "length"),
                f"child '{child['id']}' ends at "
                f"{rewritten(pair, number_type_of(timeline)) or spell(pair)}, beyond "
                f"the length {spell(length)} of its parent '{timeline['id']}'",
            )
        yield from timeline_containment_problems(child, at)
