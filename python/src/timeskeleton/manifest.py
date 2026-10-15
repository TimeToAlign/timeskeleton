"""The canonical order of a TimeSkeleton manifest and its standard writer.

The standard writer sorts the keys of every object by Unicode code point, so
equal objects are equal text whatever order their keys were given in. Every
array of a manifest whose order carries no meaning has one canonical order:

* ``timelines`` by id;
* in every timeline, ``children`` by offset, then id; ``conversion_maps`` by
  id; ``regions`` by start, then end, then id; flow-control ``breaks`` and
  ``markers`` by coordinate, then id; ``jumps`` by from coordinate, then to
  coordinate, then id;
* ``groups`` by id and every group's ``members`` by code point.

Own-axis values compare by their exact numeric value, never by their JSON
spelling; strings compare by Unicode code point. Nothing else is reordered;
in particular a ``graphical.order`` array is a display order and stays as it
is. Readers accept any order; writers emit the canonical one.

The standard writer emits UTF-8 text with every character unescaped except
``"``, ``\\`` and the control characters, two-space indentation and a final
newline. A float is always written as a float (``2.0``, ``1e-07``), spelled as
Python's ``repr``; an integer never carries a decimal point or an exponent.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Callable, Mapping
from fractions import Fraction
from typing import Any

__all__ = ["canonical_json", "canonical_order", "dumps"]


def canonical_json(value: Any) -> str:
    """Return the canonical JSON text of a value: keys sorted, no whitespace.

    Raises:
        ValueError: If the value holds a NaN or an infinity, or a string with a
            lone surrogate (which UTF-8 cannot encode).
    """
    return _utf8(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    )


def _utf8(text: str) -> str:
    """Return ``text``, refused if it holds a lone surrogate."""
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as error:
        raise ValueError(f"a string holds a lone surrogate: {error}") from error
    return text


def _exact(value: Any) -> Fraction:
    """Return the exact value of a bare Number: a JSON number or a pair.

    An integral float in a Fraction pair counts as the integer it equals, as a
    JavaScript reader cannot tell ``1.0`` from ``1``.
    """
    if isinstance(value, list) and len(value) == 2:
        numerator, denominator = (_integer(item) for item in value)
        if denominator > 0:
            return Fraction(numerator, denominator)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"not a Number: {value!r}")
    return Fraction(value)


def spell(value: Any) -> str:
    """Spell a value as a message quotes it.

    A number is spelled as the standard writer spells it, an array as its
    items separated by ``, `` within brackets (``[32, 1]``), anything else as
    compact JSON. The JavaScript package spells numbers and arrays the same way.
    """
    if isinstance(value, list):
        return "[" + ", ".join(spell(item) for item in value) + "]"
    if isinstance(value, bool) or not isinstance(value, int | float):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return repr(value)


def _integer(value: Any) -> int:
    if type(value) is int:
        return value
    if type(value) is float and value.is_integer():
        return int(value)
    raise TypeError(f"not an integer: {value!r}")


def _sorted(entries: list[Any], key: Callable[[Any], Any], where: str) -> list[Any]:
    try:
        return sorted(entries, key=key)
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as error:
        raise ValueError(f"cannot put {where} in canonical order: {error!r}") from error


def _identifier(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError(f"not an id: {value!r}")
    return value


def _by_id(entry: Any) -> str:
    return _identifier(entry["id"])


def _order_timeline(timeline: dict[str, Any]) -> None:
    """Put the arrays of one timeline and its descendants in order, in place."""
    children = timeline.get("children")
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                _order_timeline(child)
        timeline["children"] = _sorted(
            children,
            lambda entry: (_exact(entry["offset"]), _by_id(entry)),
            "children",
        )
    if isinstance(timeline.get("conversion_maps"), list):
        timeline["conversion_maps"] = _sorted(
            timeline["conversion_maps"], _by_id, "conversion_maps"
        )
    if isinstance(timeline.get("regions"), list):
        timeline["regions"] = _sorted(
            timeline["regions"],
            lambda entry: (_exact(entry["start"]), _exact(entry["end"]), _by_id(entry)),
            "regions",
        )
    flow = timeline.get("flow_control")
    if not isinstance(flow, dict):
        return
    if isinstance(flow.get("breaks"), list):
        flow["breaks"] = _sorted(
            flow["breaks"],
            lambda entry: (_exact(entry["coordinate"]), _by_id(entry)),
            "breaks",
        )
    if isinstance(flow.get("jumps"), list):
        flow["jumps"] = _sorted(
            flow["jumps"],
            lambda entry: (
                _exact(entry["from_coordinate"]),
                _exact(entry["to_coordinate"]),
                _by_id(entry),
            ),
            "jumps",
        )
    if isinstance(flow.get("markers"), list):
        flow["markers"] = _sorted(
            flow["markers"],
            lambda entry: (_exact(entry["coordinate"]), _by_id(entry)),
            "markers",
        )


def canonical_order(value: Any) -> Any:
    """Return a deep copy of ``value`` with the arrays of its manifest ordered.

    A value with a top-level ``timelines`` array is a manifest: every timeline
    in it is ordered at every depth and the array itself by id, and its
    ``groups`` are ordered by id, each with its ``members`` by code point.
    Only the arrays listed in the module docstring move; object keys are left
    as they are (``dumps`` sorts them), and any other JSON value is copied
    unchanged.

    Raises:
        ValueError: If a collection holds an entry whose ordering members are
            missing or of the wrong type.
    """
    result = copy.deepcopy(value)
    if not isinstance(result, Mapping) or not isinstance(result.get("timelines"), list):
        return result
    timelines = result["timelines"]
    for timeline in timelines:
        if isinstance(timeline, dict):
            _order_timeline(timeline)
    result["timelines"] = _sorted(timelines, _by_id, "timelines")
    groups = result.get("groups")
    if isinstance(groups, list):
        for group in groups:
            if isinstance(group, dict) and isinstance(group.get("members"), list):
                group["members"] = _sorted(group["members"], _identifier, "members")
        result["groups"] = _sorted(groups, _by_id, "groups")
    return result


def dumps(value: Any) -> str:
    """Return the standard text of a TimeSkeleton manifest, or of any JSON value.

    The value is put in :func:`canonical_order`, then written as UTF-8 text
    with the keys of every object sorted by code point, two-space indentation
    and a final newline, characters unescaped
    (``ensure_ascii=False``) and every float spelled as ``repr`` spells it.

    Raises:
        ValueError: If the value holds a NaN or an infinity, a string with a
            lone surrogate (which UTF-8 cannot encode), or a collection that
            cannot be put in canonical order.
    """
    ordered = canonical_order(value)
    return _utf8(
        json.dumps(
            ordered, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
        + "\n"
    )
