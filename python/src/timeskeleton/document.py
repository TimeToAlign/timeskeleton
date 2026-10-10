"""The canonical order of a TimeSkeleton document and its standard writer.

Every collection of a document whose order carries no meaning has one
canonical order, so that equal documents are equal text:

* ``manifest.timelines`` by id;
* at every depth, ``children`` by offset, then id;
* ``conversion_maps`` by id;
* ``regions`` by start, then end, then name;
* flow-control ``breaks`` by coordinate, then canonical JSON text;
* ``jumps`` by from coordinate, then to coordinate, then canonical JSON text;
* ``markers`` by name.

Coordinates compare by their exact numeric value, never by their JSON
spelling; strings compare by Unicode code point. The canonical JSON text of an
entry has its object keys sorted by code point and no whitespace. Nothing else
is reordered. Readers accept any order; writers emit the canonical one.

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


def _exact(coordinate: Any) -> Fraction:
    """Return the exact value of a coordinate dict: an int, a float or a pair.

    An integral float in a Fraction pair counts as the integer it equals, as a
    JavaScript reader cannot tell ``1.0`` from ``1``.
    """
    value = coordinate["value"]
    if isinstance(value, list):
        numerator, denominator = (_integer(item) for item in value)
        return Fraction(numerator, denominator)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"not a coordinate value: {value!r}")
    return Fraction(value)


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


def _order_timeline(manifest: dict[str, Any]) -> None:
    """Put one timeline manifest and its children in canonical order, in place."""
    children = manifest.get("children")
    if isinstance(children, dict):
        for child in children.values():
            if isinstance(child, dict) and isinstance(child.get("timeline"), dict):
                _order_timeline(child["timeline"])
        manifest["children"] = dict(
            _sorted(
                list(children.items()),
                lambda item: (_exact(item[1]["offset"]), item[0]),
                "children",
            )
        )
    if isinstance(manifest.get("conversion_maps"), list):
        manifest["conversion_maps"] = _sorted(
            manifest["conversion_maps"], lambda entry: entry["id"], "conversion_maps"
        )
    if isinstance(manifest.get("regions"), list):
        manifest["regions"] = _sorted(
            manifest["regions"],
            lambda entry: (_exact(entry["start"]), _exact(entry["end"]), entry["name"]),
            "regions",
        )
    flow = manifest.get("flow_control")
    if not isinstance(flow, dict):
        return
    if isinstance(flow.get("breaks"), list):
        flow["breaks"] = _sorted(
            flow["breaks"],
            lambda entry: (_exact(entry["coordinate"]), canonical_json(entry)),
            "breaks",
        )
    if isinstance(flow.get("jumps"), list):
        flow["jumps"] = _sorted(
            flow["jumps"],
            lambda entry: (
                _exact(entry["from_coordinate"]),
                _exact(entry["to_coordinate"]),
                canonical_json(entry),
            ),
            "jumps",
        )
    if isinstance(flow.get("markers"), dict):
        flow["markers"] = dict(
            sorted(flow["markers"].items(), key=lambda item: item[0])
        )


def canonical_order(value: Any) -> Any:
    """Return a deep copy of ``value`` with its document in canonical order.

    ``value`` is a TimeSkeleton document, or any JSON value: only the
    collections found where a document holds them (``manifest.timelines`` and,
    in each timeline manifest at every depth, the members listed in the module
    docstring) are reordered, so a value that is no document is copied
    unchanged. The order does not depend on the schema version.

    Raises:
        ValueError: If a collection holds an entry whose ordering members are
            missing or of the wrong type.
    """
    result = copy.deepcopy(value)
    manifest = result.get("manifest") if isinstance(result, Mapping) else None
    timelines = manifest.get("timelines") if isinstance(manifest, Mapping) else None
    if isinstance(timelines, dict):
        for timeline in timelines.values():
            if isinstance(timeline, dict):
                _order_timeline(timeline)
        manifest["timelines"] = dict(
            sorted(timelines.items(), key=lambda item: item[0])
        )
    return result


def dumps(value: Any) -> str:
    """Return the standard text of a document, or of any JSON value.

    The value is put in :func:`canonical_order`, then written as UTF-8 text
    with two-space indentation and a final newline, characters unescaped
    (``ensure_ascii=False``) and every float spelled as ``repr`` spells it.

    Raises:
        ValueError: If the value holds a NaN or an infinity, a string with a
            lone surrogate (which UTF-8 cannot encode), or a collection that
            cannot be put in canonical order.
    """
    ordered = canonical_order(value)
    return _utf8(
        json.dumps(ordered, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    )
