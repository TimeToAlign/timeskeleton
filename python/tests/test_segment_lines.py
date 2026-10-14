from __future__ import annotations

import copy
from typing import Any

import pytest

from timeskeleton import SchemaValidationError, identity_problems, load_schema, validate


def _at(value: Any, unit: str = "quarters", number_type: str = "fraction") -> dict:
    if number_type == "fraction":
        value = [value, 1]
    return {"unit": unit, "number_type": number_type, "value": value}


def _segment_line(load_fixture, segments: dict[str, tuple[int, int]]) -> dict:
    """``bare`` (8 quarters) as a segment line with the given offset and length."""
    manifest = load_fixture("bare")
    line = manifest["timeline"]
    line["is_segment_line"] = True
    for key, (offset, length) in segments.items():
        segment = copy.deepcopy(line)
        segment.update(id=key, name=None, is_segment_line=False, children={})
        segment["length"] = _at(length)
        line["children"][key] = {"offset": _at(offset), "timeline": segment}
    return manifest


def _problems(manifest: dict) -> list[tuple[tuple, str]]:
    return [(problem.path, problem.message) for problem in identity_problems(manifest)]


def _child(*keys: str) -> tuple:
    path: tuple = ("timeline",)
    for key in keys:
        path = (*path, "children", key, "timeline")
    return path


def test_the_flag_is_required_after_locked() -> None:
    manifest = load_schema("0.7.0", "timeline")["$defs"]["TimelineManifest"]
    keys = list(manifest["properties"])
    assert keys[keys.index("locked") + 1] == "is_segment_line"
    assert manifest["properties"]["is_segment_line"]["type"] == "boolean"
    assert len(manifest["required"]) == 15
    assert manifest["required"][manifest["required"].index("locked") + 1] == (
        "is_segment_line"
    )


def test_valid_segment_lines(load_fixture) -> None:
    flat = _segment_line(load_fixture, {"a": (0, 3), "b": (3, 5)})
    validate(flat)
    nested = _segment_line(load_fixture, {"a": (0, 4), "b": (4, 4)})
    for key in ("a", "b"):
        segment = nested["timeline"]["children"][key]["timeline"]
        segment["is_segment_line"] = True
        for inner, offset in (("x", 0), ("y", 2)):
            leaf = copy.deepcopy(segment)
            leaf.update(id=f"{key}{inner}", is_segment_line=False, children={})
            leaf["length"] = _at(2)
            segment["children"][f"{key}{inner}"] = {
                "offset": _at(offset),
                "timeline": leaf,
            }
    validate(nested)
    empty = _segment_line(load_fixture, {})
    empty["timeline"]["length"] = _at(0)
    validate(empty)


def test_a_segment_of_another_class(load_fixture) -> None:
    manifest = _segment_line(load_fixture, {"a": (0, 3), "b": (3, 5)})
    segment = manifest["timeline"]["children"]["b"]["timeline"]
    segment["class"] = "DiscreteLogicalTimeline"
    assert _problems(manifest) == [
        (
            (*_child("b"), "class"),
            "segment 'b' of segment line 'bare' is no ContinuousLogicalTimeline",
        )
    ]


def test_a_segment_with_another_flag(load_fixture) -> None:
    manifest = _segment_line(load_fixture, {"a": (0, 3), "b": (3, 5)})
    manifest["timeline"]["children"]["b"]["timeline"]["is_segment_line"] = True
    manifest["timeline"]["children"]["b"]["timeline"]["length"] = _at(0)
    manifest["timeline"]["children"]["b"]["offset"] = _at(3)
    manifest["timeline"]["length"] = _at(3)
    assert _problems(manifest) == [
        (
            (*_child("b"), "is_segment_line"),
            "segment 'b' of segment line 'bare' differs from segment 'a' in "
            "is_segment_line",
        )
    ]


@pytest.mark.parametrize(
    ("segments", "key", "message"),
    [
        ({"a": (1, 2), "b": (3, 5)}, "a", "does not start at 0"),
        (
            {"a": (0, 3), "b": (4, 4)},
            "b",
            "does not start where the one before it ends",
        ),
        (
            {"a": (0, 3), "b": (2, 6)},
            "b",
            "does not start where the one before it ends",
        ),
    ],
    ids=["not from zero", "gap", "overlap"],
)
def test_segments_are_contiguous_from_zero(
    load_fixture, segments, key, message
) -> None:
    manifest = _segment_line(load_fixture, segments)
    assert _problems(manifest) == [
        (
            ("timeline", "children", key, "offset"),
            f"segment {key!r} of segment line 'bare' {message}",
        )
    ]


@pytest.mark.parametrize("segments", [{"a": (0, 3), "b": (3, 4)}, {}])
def test_the_segments_end_at_the_length(load_fixture, segments) -> None:
    assert _problems(_segment_line(load_fixture, segments)) == [
        (
            ("timeline", "length"),
            "the segments of segment line 'bare' do not end at its length",
        )
    ]


def test_segments_are_visited_in_offset_order(load_fixture) -> None:
    assert _problems(_segment_line(load_fixture, {"z": (0, 3), "a": (3, 5)})) == []
    manifest = _segment_line(load_fixture, {"z": (0, 3), "a": (4, 4)})
    assert [path for path, _ in _problems(manifest)] == [
        ("timeline", "children", "a", "offset")
    ]


def test_values_compare_exactly(load_fixture) -> None:
    def seconds(segments: list[tuple[str, float, float]], length: float) -> dict:
        manifest = _segment_line(load_fixture, {})
        line = manifest["timeline"]
        line.update(
            {"class": "ContinuousPhysicalTimeline", "unit": "seconds"},
            number_type="float",
            measure_map=None,
        )
        line["length"] = _at(length, "seconds", "float")
        for key, offset, size in segments:
            segment = copy.deepcopy(line)
            segment.update(id=key, is_segment_line=False, children={})
            segment["length"] = _at(size, "seconds", "float")
            line["children"][key] = {
                "offset": _at(offset, "seconds", "float"),
                "timeline": segment,
            }
        return manifest

    validate(seconds([("a", 0.0, 0.5), ("b", 0.5, 0.25), ("c", 0.75, 0.25)], 1.0))
    inexact = seconds([("a", 0.0, 0.1), ("b", 0.1, 0.2), ("c", 0.3, 0.7)], 1.0)
    assert [path for path, _ in _problems(inexact)] == [
        ("timeline", "children", "c", "offset"),
        ("timeline", "length"),
    ]


def test_the_problems_come_in_the_stated_order(load_fixture) -> None:
    manifest = _segment_line(load_fixture, {"a": (0, 3), "b": (4, 3)})
    children = manifest["timeline"]["children"]
    children["b"]["timeline"]["class"] = "DiscreteLogicalTimeline"
    children["b"]["timeline"]["is_segment_line"] = True
    assert [path for path, _ in _problems(manifest)] == [
        (*_child("b"), "class"),
        (*_child("b"), "is_segment_line"),
        ("timeline", "children", "b", "offset"),
        ("timeline", "length"),
        (*_child("b"), "length"),
    ]
    with pytest.raises(SchemaValidationError) as caught:
        validate(manifest)
    assert caught.value.path == (*_child("b"), "class")


def test_a_descendant_segment_line_is_checked_at_its_path(load_fixture) -> None:
    manifest = _segment_line(load_fixture, {"a": (0, 8)})
    manifest["timeline"]["is_segment_line"] = False
    child = manifest["timeline"]["children"]["a"]["timeline"]
    child["is_segment_line"] = True
    assert _problems(manifest) == [
        (
            (*_child("a"), "length"),
            "the segments of segment line 'a' do not end at its length",
        )
    ]


def test_a_timeline_that_is_no_segment_line_is_never_checked(load_fixture) -> None:
    manifest = _segment_line(load_fixture, {"a": (1, 2), "b": (5, 1)})
    manifest["timeline"]["is_segment_line"] = False
    assert identity_problems(manifest) == []


SEGMENT_LINE = [
    # (id, name, is_segment_line, locked, absolute start, length)
    ("form", "Form", True, False, 0, 32),
    ("a", "A", True, True, 0, 8),
    ("a1", None, False, True, 0, 8),
    ("b", "B", True, True, 8, 12),
    ("b1", "b1", False, True, 8, 6),
    ("b2", "b2", False, True, 14, 6),
    ("c", "C", True, True, 20, 12),
    ("c1", None, False, True, 20, 12),
]


def test_the_segment_line_fixture(load_fixture) -> None:
    manifest = load_fixture("segment_line")
    found = []

    def visit(timeline: dict, start: int) -> None:
        assert timeline["class"] == "ContinuousLogicalTimeline"
        assert timeline["number_type"] == "fraction"
        assert timeline["length"] == _at(timeline["length"]["value"][0])
        found.append(
            (
                timeline["id"],
                timeline["name"],
                timeline["is_segment_line"],
                timeline["locked"],
                start,
                timeline["length"]["value"][0],
            )
        )
        for child in timeline["children"].values():
            offset = child["offset"]
            assert offset == _at(offset["value"][0])
            visit(child["timeline"], start + offset["value"][0])

    visit(manifest["timeline"], 0)
    assert found == SEGMENT_LINE
    assert identity_problems(manifest) == []
    validate(manifest)
