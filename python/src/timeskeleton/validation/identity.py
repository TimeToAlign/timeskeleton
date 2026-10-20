"""Identity, target, reserved-id, group-member and orchestration rules."""

from __future__ import annotations

import re
from collections.abc import Iterator, Mapping
from itertools import chain
from typing import Any

from .containment import timeline_containment_problems
from .diagnostics import (
    SchemaValidationError,
    ValidationCode,
    _entries,
    _Path,
    json_pointer,
)
from .maps import MEASURE_VIEWS, timeline_map_problems, timeline_maps
from .order import order_problems
from .segments import timeline_segment_problems


def _element_ids(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[tuple[str, _Path]]:
    yield timeline["id"], (*path, "id")
    for member in ("conversion_maps", "regions"):
        for index, entry in enumerate(_entries(timeline, member)):
            yield entry["id"], (*path, member, index, "id")
    for index, entry in enumerate(_entries(timeline, "flow_control")):
        yield entry["id"], (*path, "flow_control", index, "id")
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _element_ids(child, (*path, "children", index))


def _nested_map_ids(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[tuple[Any, _Path]]:
    for conversion_map, at in timeline_maps(timeline, path):
        if at[-2] == "maps":
            yield conversion_map["id"], (*at, "id")
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _nested_map_ids(child, (*path, "children", index))


def _timeline_ids(
    timeline: Mapping[str, Any], path: _Path
) -> Iterator[tuple[str, _Path]]:
    yield timeline["id"], (*path, "id")
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _timeline_ids(child, (*path, "children", index))


def _dangling_targets(
    timeline: Mapping[str, Any], path: _Path, measure_maps: set[str]
) -> Iterator[SchemaValidationError]:
    flow = _entries(timeline, "flow_control")
    targets = {entry["id"] for entry in flow if entry["type"] == "jump_to"}
    for index, entry in enumerate(flow):
        if "target" in entry and entry["target"] not in targets:
            yield SchemaValidationError(
                "dangling_target",
                (*path, "flow_control", index, "target"),
                f"{entry['target']!r} names no jump_to of this timeline",
            )
    for conversion_map, at in timeline_maps(timeline, path):
        reference = conversion_map.get("measure_map")
        if conversion_map["type"] in MEASURE_VIEWS and reference not in measure_maps:
            yield SchemaValidationError(
                "dangling_target",
                (*at, "measure_map"),
                f"{reference!r} names no measure map of this manifest",
            )
    for index, child in enumerate(_entries(timeline, "children")):
        yield from _dangling_targets(child, (*path, "children", index), measure_maps)


def _duplicate(
    identifier: str,
    path: _Path,
    first: _Path,
    code: ValidationCode = "duplicate_id",
) -> SchemaValidationError:
    return SchemaValidationError(
        code, path, f"duplicate id {identifier!r}, first at {json_pointer(first)}"
    )


def _root_problems(
    root: Mapping[str, Any], path: _Path, measure_maps: set[str]
) -> Iterator[SchemaValidationError]:
    first: dict[str, _Path] = {}
    for identifier, at in chain(_element_ids(root, path), _nested_map_ids(root, path)):
        if identifier in first:
            yield _duplicate(identifier, at, first[identifier])
        else:
            first[identifier] = at
    yield from _dangling_targets(root, path, measure_maps)
    yield from timeline_map_problems(root, path)
    yield from timeline_containment_problems(root, path)
    yield from timeline_segment_problems(root, path)


_PART_WORDS = ("start", "end", "name", "label", "card")
_BAND_ID = re.compile(
    r"(markers|conversion_maps|children|regions|flow_control)_[1-9][0-9]*"
)


def _reserved(identifier: Any, path: _Path) -> Iterator[SchemaValidationError]:
    if identifier in _PART_WORDS:
        yield SchemaValidationError(
            "reserved_id",
            path,
            f"id {identifier!r} is reserved for the parts of an address",
        )
    elif isinstance(identifier, str) and _BAND_ID.fullmatch(identifier):
        yield SchemaValidationError(
            "reserved_id",
            path,
            f"id {identifier!r} is reserved for the bands of a timeline",
        )


def _parents(roots: list[Mapping[str, Any]]) -> dict[str, str | None]:
    found: dict[str, str | None] = {}

    def visit(timeline: Mapping[str, Any], parent: str | None) -> None:
        found.setdefault(timeline["id"], parent)
        for child in _entries(timeline, "children"):
            visit(child, timeline["id"])

    for root in roots:
        visit(root, None)
    return found


def _ancestors(identifier: str, parents: Mapping[str, str | None]) -> list[str]:
    found: list[str] = []
    parent = parents.get(identifier)
    while parent is not None:
        found.append(parent)
        parent = parents.get(parent)
    return found


def _member_problems(
    group: Mapping[str, Any],
    path: _Path,
    parents: Mapping[str, str | None],
) -> Iterator[SchemaValidationError]:
    selected: dict[str, int] = {}
    earliest_descendant: dict[str, tuple[int, str]] = {}
    for index, member in enumerate(group["members"]):
        at = (*path, index)
        if member not in parents:
            yield SchemaValidationError(
                "group_member", at, f"{member!r} names no timeline of this manifest"
            )
            continue
        ancestors = _ancestors(member, parents)
        relation: tuple[int, str, str] | None = None
        for ancestor in ancestors:
            if ancestor in selected and (
                relation is None or selected[ancestor] < relation[0]
            ):
                relation = (selected[ancestor], ancestor, "lies inside")
        descendant = earliest_descendant.get(member)
        if descendant is not None and (relation is None or descendant[0] < relation[0]):
            relation = (*descendant, "contains")
        if relation is not None:
            _, other, word = relation
            yield SchemaValidationError(
                "group_member",
                at,
                f"member {member!r} {word} member {other!r} of the same group",
            )

        selected.setdefault(member, index)
        for ancestor in ancestors:
            earliest_descendant.setdefault(ancestor, (index, member))


def identity_problems(
    value: Mapping[str, Any],
) -> Iterator[SchemaValidationError]:
    """Yield semantic violations in the established identity order."""
    roots = _entries(value, "timelines")
    groups = _entries(value, "groups")
    measure_maps = _entries(value, "measure_maps")
    measure_map_ids = {measure_map["id"] for measure_map in measure_maps}
    for index, root in enumerate(roots):
        yield from _root_problems(root, ("timelines", index), measure_map_ids)

    manifest_id = value.get("id")
    yield from _reserved(manifest_id, ("id",))
    for index, root in enumerate(roots):
        for identifier, at in _element_ids(root, ("timelines", index)):
            yield from _reserved(identifier, at)
        for identifier, at in _nested_map_ids(root, ("timelines", index)):
            yield from _reserved(identifier, at)
    for index, group in enumerate(groups):
        yield from _reserved(group["id"], ("groups", index, "id"))
    for index, measure_map in enumerate(measure_maps):
        yield from _reserved(measure_map["id"], ("measure_maps", index, "id"))

    timelines: dict[str, _Path] = {}
    for index, root in enumerate(roots):
        seen: dict[str, _Path] = {}
        for identifier, path in _timeline_ids(root, ("timelines", index)):
            if identifier in seen:
                continue
            seen[identifier] = path
            if identifier in timelines:
                yield _duplicate(identifier, path, timelines[identifier])
        for identifier, path in seen.items():
            timelines.setdefault(identifier, path)

    first_group: dict[str, int] = {}
    for index, group in enumerate(groups):
        identifier = group["id"]
        path = ("groups", index, "id")
        if identifier in timelines:
            yield _duplicate(identifier, path, timelines[identifier])
        elif identifier in first_group:
            yield _duplicate(
                identifier, path, ("groups", first_group[identifier], "id")
            )
        first_group.setdefault(identifier, index)

    first_measure_map: dict[str, int] = {}
    for index, measure_map in enumerate(measure_maps):
        identifier = measure_map["id"]
        path = ("measure_maps", index, "id")
        if identifier in timelines:
            yield _duplicate(identifier, path, timelines[identifier])
        elif identifier in first_group:
            yield _duplicate(
                identifier, path, ("groups", first_group[identifier], "id")
            )
        elif identifier in first_measure_map:
            yield _duplicate(
                identifier,
                path,
                ("measure_maps", first_measure_map[identifier], "id"),
            )
        first_measure_map.setdefault(identifier, index)

    if manifest_id is not None:
        if manifest_id in timelines:
            yield _duplicate(
                manifest_id, ("id",), timelines[manifest_id], "manifest_id"
            )
        elif manifest_id in first_group:
            yield _duplicate(
                manifest_id,
                ("id",),
                ("groups", first_group[manifest_id], "id"),
                "manifest_id",
            )
        elif manifest_id in first_measure_map:
            yield _duplicate(
                manifest_id,
                ("id",),
                ("measure_maps", first_measure_map[manifest_id], "id"),
                "manifest_id",
            )

    parents = _parents(roots)
    for index, group in enumerate(groups):
        yield from _member_problems(group, ("groups", index, "members"), parents)
    yield from order_problems(value, timelines, first_group)
