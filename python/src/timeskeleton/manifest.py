"""The canonical order of a TimeSkeleton manifest and its standard writer.

The standard writer sorts the keys of every object by Unicode code point, so
equal objects are equal text whatever order their keys were given in. Every
array of a manifest whose order carries no meaning has one canonical order:

* ``conversion_maps`` by id;
* ``regions`` by start, then end, then id;
* flow-control ``breaks`` and ``markers`` by coordinate, then id;
* ``jumps`` by from coordinate, then to coordinate, then id.

Coordinates compare by their exact numeric value, never by their JSON
spelling; strings compare by Unicode code point. Ids are unique within a
manifest, so no two entries tie. Nothing else is reordered. Readers accept
any order; writers emit the canonical one.

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
    """Put the arrays of one timeline manifest and its children in order, in place."""
    children = manifest.get("children")
    if isinstance(children, dict):
        for child in children.values():
            if isinstance(child, dict) and isinstance(child.get("timeline"), dict):
                _order_timeline(child["timeline"])
    if isinstance(manifest.get("conversion_maps"), list):
        manifest["conversion_maps"] = _sorted(
            manifest["conversion_maps"], lambda entry: entry["id"], "conversion_maps"
        )
    if isinstance(manifest.get("regions"), list):
        manifest["regions"] = _sorted(
            manifest["regions"],
            lambda entry: (_exact(entry["start"]), _exact(entry["end"]), entry["id"]),
            "regions",
        )
    flow = manifest.get("flow_control")
    if not isinstance(flow, dict):
        return
    if isinstance(flow.get("breaks"), list):
        flow["breaks"] = _sorted(
            flow["breaks"],
            lambda entry: (_exact(entry["coordinate"]), entry["id"]),
            "breaks",
        )
    if isinstance(flow.get("jumps"), list):
        flow["jumps"] = _sorted(
            flow["jumps"],
            lambda entry: (
                _exact(entry["from_coordinate"]),
                _exact(entry["to_coordinate"]),
                entry["id"],
            ),
            "jumps",
        )
    if isinstance(flow.get("markers"), list):
        flow["markers"] = _sorted(
            flow["markers"],
            lambda entry: (_exact(entry["coordinate"]), entry["id"]),
            "markers",
        )


def canonical_order(value: Any) -> Any:
    """Return a deep copy of ``value`` with the arrays of its manifest ordered.

    A value with a top-level ``timeline`` member orders the arrays of that
    timeline manifest and of its children at every depth. Only the arrays
    listed in the module docstring move; object keys are left as they are
    (``dumps`` sorts them), and any other JSON value is copied unchanged.

    Raises:
        ValueError: If a collection holds an entry whose ordering members are
            missing or of the wrong type.
    """
    result = copy.deepcopy(value)
    timeline = result.get("timeline") if isinstance(result, Mapping) else None
    if isinstance(timeline, dict):
        _order_timeline(timeline)
    return result


def dumps(value: Any) -> str:
    """Return the standard text of a manifest, or of any JSON value.

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
