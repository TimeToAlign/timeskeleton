"""The defaults of a TimeSkeleton manifest: the complete and the minimal form.

Every key with a default may be left out of a manifest, and a reader supplies
the default. The complete form writes every such key, its default included;
the minimal form leaves out exactly the keys whose value is the default.
Either form reads to the same manifest, and each converts to the other. A key
whose default is "absent" (a manifest's ``id`` and ``graphical``, a root's
``offset``) is never added and never removed. Unknown keys pass through
untouched.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from .manifest import UNIT_NUMBER_TYPES, _respell

__all__ = ["DEFAULTS", "complete", "minimal"]

DEFAULTS: dict[str, dict[str, Any]] = {
    "manifest": {"name": None, "meta": {}, "groups": [], "measure_maps": []},
    "timeline": {
        "name": None,
        "locked": False,
        "is_segment_line": False,
        "meta": {},
        "children": [],
        "conversion_maps": [],
        "regions": [],
        "flow_control": [],
    },
    "region": {"name": None, "meta": {}},
    "flow_control_element": {"name": None, "label": None, "meta": {}},
    "repeat_end": {"repeat_count": 1},
    "conversion_map": {"name": None},
    "linear_map": {"scalar": 1, "offset": 0},
    "table_map": {"kind": "linear", "extrapolate": "none"},
    "measure_map": {"name": None, "meta": {}},
    "group": {"name": None, "meta": {}},
    "graphical": {"styles": {}, "statements": [], "order": {}},
}
"""The default of every key that has one, by the kind of object holding it.

A timeline's ``number_type`` defaults to its unit's default number type.
Every conversion map has the keys of ``conversion_map``; a ``LinearMap`` adds
those of ``linear_map`` and a ``TableMap`` those of ``table_map``. Every
flow-control element has the keys of ``flow_control_element``, and one whose
manifestation is ``repeat_end`` adds those of ``repeat_end``, as no other
element carries a repeat count. The
JavaScript package's ``DEFAULTS`` holds the same table, and the schema
declares each value as the key's ``default``.
"""

_MAP_KINDS = {"LinearMap": "linear_map", "TableMap": "table_map"}
"""The kind of the defaults a conversion map type adds to those of every map."""

_Pass = Callable[[dict[str, Any], str], None]


def _objects(owner: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = owner.get(key)
    return (
        [entry for entry in value if isinstance(entry, dict)]
        if isinstance(value, list)
        else []
    )


def _visit_map(conversion_map: dict[str, Any], apply: _Pass) -> None:
    """Apply a pass to a conversion map and to the maps it holds."""
    apply(conversion_map, "conversion_map")
    map_type = conversion_map.get("type")
    if isinstance(map_type, str) and map_type in _MAP_KINDS:
        apply(conversion_map, _MAP_KINDS[map_type])
    maps = conversion_map.get("maps")
    nested = (
        maps
        if isinstance(maps, list)
        else list(maps.values())
        if isinstance(maps, dict)
        else []
    )
    for entry in nested:
        if isinstance(entry, dict):
            _visit_map(entry, apply)


def _visit_timeline(timeline: dict[str, Any], apply: _Pass) -> None:
    """Apply a pass to a timeline and to everything it holds."""
    apply(timeline, "timeline")
    for child in _objects(timeline, "children"):
        _visit_timeline(child, apply)
    for conversion_map in _objects(timeline, "conversion_maps"):
        _visit_map(conversion_map, apply)
    for region in _objects(timeline, "regions"):
        apply(region, "region")
    for entry in _objects(timeline, "flow_control"):
        apply(entry, "flow_control_element")
        if entry.get("manifestation") == "repeat_end":
            apply(entry, "repeat_end")


def _visit_manifest(manifest: Any, apply: _Pass) -> None:
    """Apply a pass to every object of a manifest that has defaults, outermost first."""
    if not isinstance(manifest, dict):
        return
    apply(manifest, "manifest")
    for timeline in _objects(manifest, "timelines"):
        _visit_timeline(timeline, apply)
    for group in _objects(manifest, "groups"):
        apply(group, "group")
    for measure_map in _objects(manifest, "measure_maps"):
        apply(measure_map, "measure_map")
    if isinstance(manifest.get("graphical"), dict):
        apply(manifest["graphical"], "graphical")


def _default_number_type(timeline: dict[str, Any]) -> str | None:
    unit = timeline.get("unit")
    return UNIT_NUMBER_TYPES.get(unit) if isinstance(unit, str) else None


def _complete_one(owner: dict[str, Any], kind: str) -> None:
    for key, value in DEFAULTS[kind].items():
        if key not in owner:
            owner[key] = copy.deepcopy(value)
    if kind == "timeline" and "number_type" not in owner:
        number_type = _default_number_type(owner)
        if number_type is not None:
            owner["number_type"] = number_type


def _same(left: Any, right: Any) -> bool:
    """Whether two JSON values are identical: numbers in type and value.

    An int is never the float of the same value (``1.0`` is not ``1``), and
    a boolean is no number.
    """
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if isinstance(left, int | float) or isinstance(right, int | float):
        return type(left) is type(right) and left == right
    if isinstance(left, list) or isinstance(right, list):
        return (
            isinstance(left, list)
            and isinstance(right, list)
            and len(left) == len(right)
            and all(_same(a, b) for a, b in zip(left, right, strict=True))
        )
    if isinstance(left, dict) or isinstance(right, dict):
        return (
            isinstance(left, dict)
            and isinstance(right, dict)
            and left.keys() == right.keys()
            and all(_same(left[key], right[key]) for key in left)
        )
    return left == right


def _strip_one(owner: dict[str, Any], kind: str) -> None:
    for key, value in DEFAULTS[kind].items():
        if key in owner and _same(owner[key], value):
            del owner[key]
    if kind == "timeline" and "number_type" in owner:
        if owner["number_type"] == _default_number_type(owner):
            del owner["number_type"]


def complete(value: Any) -> Any:
    """Return a copy of a manifest in the complete form.

    Every key with a default that is absent is added with its default, at
    every depth (a timeline's ``number_type`` is its unit's default). Keys
    whose default is "absent" are never added, present keys keep their
    values, spelled as their number type selects (as ``canonical_order``
    spells them), and unknown keys pass through. The JavaScript package's
    ``complete`` gives the same value.
    """
    result = copy.deepcopy(value)
    _respell(result)
    _visit_manifest(result, _complete_one)
    return result


def minimal(value: Any) -> Any:
    """Return a copy of a manifest in the minimal form.

    The complete form without every key whose value is its default in type
    and value (``repeat_count: 1.0`` is not the default ``1`` and stays).
    ``minimal(complete(x))`` equals ``minimal(x)`` and
    ``complete(minimal(x))`` equals ``complete(x)``. The JavaScript package's
    ``minimal`` gives the same value.
    """
    result = complete(value)
    _visit_manifest(result, _strip_one)
    return result
