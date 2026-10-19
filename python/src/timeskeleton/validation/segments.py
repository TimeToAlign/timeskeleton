"""Segment-line rules."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from fractions import Fraction
from typing import Any

from ..manifest import _exact
from .containment import offset_order
from .diagnostics import SchemaValidationError, _entries, _Path


def timeline_segment_problems(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[SchemaValidationError]:
    """Yield segment-line violations for one timeline tree."""
    children = _entries(timeline, "children")
    if timeline.get("is_segment_line") is True:
        order = offset_order(children)
        end: Fraction | None = Fraction(0)
        flag = False
        first_id = ""
        for position, index in enumerate(order):
            segment = children[index]
            at = (*path, "children", index)
            name = f"segment {segment['id']!r} of segment line {timeline['id']!r}"
            segment_flag = segment.get("is_segment_line") is True
            if position == 0:
                flag, first_id = segment_flag, segment["id"]
            elif segment_flag != flag:
                yield SchemaValidationError(
                    "segment_line",
                    (*at, "is_segment_line") if "is_segment_line" in segment else at,
                    f"{name} differs from segment {first_id!r} in is_segment_line",
                )
            offset = _exact(segment["offset"])
            if end is not None and offset != end:
                yield SchemaValidationError(
                    "segment_line",
                    (*at, "offset"),
                    f"{name} does not "
                    + (
                        "start at 0"
                        if position == 0
                        else "start where the one before it ends"
                    ),
                )
            length = segment.get("length")
            end = None if length is None else offset + _exact(length)
        length = timeline.get("length")
        if end is not None and length is not None and end != _exact(length):
            yield SchemaValidationError(
                "segment_line",
                (*path, "length"),
                f"the segments of segment line {timeline['id']!r} do not end at its "
                "length",
            )
    for index, child in enumerate(children):
        yield from timeline_segment_problems(child, (*path, "children", index))
