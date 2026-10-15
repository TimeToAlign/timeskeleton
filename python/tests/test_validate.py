from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from timeskeleton import (
    SchemaValidationError,
    UnsupportedVersionError,
    dumps,
    json_pointer,
    rejection_paths,
    validate,
)

from .conftest import manifest, timeline

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SMALLEST = {
    "timeskeleton": "0.7.0",
    "timelines": [{"id": "piece", "unit": "quarters", "length": [32, 1]}],
}

REJECTIONS = [
    "break_control_type_unknown",
    "child_end_beyond_parent",
    "child_id_control_character_newline",
    "child_missing_offset",
    "child_offset_beyond_parent",
    "child_offset_fraction_on_float_axis",
    "child_offset_negative",
    "child_unit_differs",
    "conversion_map_unknown_type",
    "float_axis_int_not_exact",
    "group_id_duplicate",
    "group_id_is_descendant_id",
    "group_id_is_timeline_id",
    "group_member_with_slash",
    "group_members_repeated",
    "group_missing_id",
    "group_missing_members",
    "group_order_not_member",
    "group_order_repeated",
    "id_control_character_tab",
    "id_duplicate_across_kinds",
    "id_empty",
    "id_with_slash",
    "jump_condition_unknown",
    "jump_target_dangling",
    "later_root_missing_unit",
    "length_coordinate_dict",
    "length_fraction_on_int_axis",
    "length_int_on_fraction_axis",
    "length_negative",
    "length_string_fraction",
    "length_three_element_fraction",
    "length_zero_denominator",
    "linear_map_missing_scalar",
    "manifest_id_is_descendant_id",
    "manifest_id_is_group_id",
    "marker_coordinate_dict",
    "markers_object",
    "measure_map_empty",
    "measure_map_not_array",
    "measure_map_on_graphical_timeline",
    "measure_map_row_actual_length_negative",
    "measure_map_row_offset_within_measure_zero",
    "measure_map_row_qstamp_negative",
    "measure_map_row_qstamp_string",
    "measure_map_row_without_count_or_id",
    "member_dangling",
    "member_in_two_groups",
    "members_contain_member",
    "members_inside_member",
    "metric_hierarchy_string",
    "order_missing_member",
    "order_not_array",
    "order_unknown_group",
    "part_word_one_root",
    "part_word_region_card",
    "part_word_region_label",
    "part_word_timeline_id",
    "region_start_float_on_fraction_axis",
    "root_missing_marker",
    "root_missing_timelines",
    "segment_line_flag_not_boolean",
    "segment_line_gap",
    "segment_line_gap_in_later_root",
    "segment_line_not_from_zero",
    "segment_line_segment_flag",
    "segment_line_short_of_length",
    "statement_select_empty_ids",
    "statement_select_inside_unknown_element",
    "statement_select_projection",
    "statement_select_unknown_element",
    "statement_set_content_not_string",
    "statement_set_dasharray_malformed",
    "statement_set_max_width_zero",
    "statement_set_neither_object_nor_string",
    "statement_set_opacity_above_one",
    "statement_set_shadow_lower_case",
    "statement_set_stroke_lower_case",
    "timeline_missing_length",
    "timeline_name_not_string",
    "timeline_number_type_unknown",
    "timeline_unit_unknown",
    "timelines_child_id_duplicate_across_roots",
    "timelines_id_duplicate_across_roots",
    "timelines_root_jump_target_dangling",
    "version_unknown",
]


def _problem(value: Any) -> tuple[tuple[str | int, ...], str]:
    with pytest.raises(SchemaValidationError) as caught:
        validate(value)
    return caught.value.path, caught.value.message


# -- the version marker -----------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        {"timelines": []},
        {"meta": {"schema_version": "0.7.0"}, "timelines": []},
        [],
        "0.7.0",
    ],
    ids=["no marker", "former declaration", "list", "string"],
)
def test_a_value_without_the_marker_is_no_manifest(value: Any) -> None:
    assert _problem(value) == ((), "not a TimeSkeleton manifest")


@pytest.mark.parametrize("version", ["9.9.9", "0.6.0", "0.7", 7])
def test_another_version_is_unsupported(version: Any) -> None:
    with pytest.raises(UnsupportedVersionError) as caught:
        validate({"timeskeleton": version})
    assert caught.value.version == version


def test_the_unsupported_version_message() -> None:
    with pytest.raises(UnsupportedVersionError) as caught:
        validate({"timeskeleton": "9.9.9", "timelines": []})
    assert str(caught.value) == (
        "unsupported TimeSkeleton version '9.9.9'; this package reads 0.7.0 only"
    )


def test_the_smallest_and_the_empty_manifest_validate() -> None:
    validate(SMALLEST)
    validate({"timeskeleton": "0.7.0", "timelines": []})


# -- representation ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("root", "message"),
    [
        (
            timeline("score", length=32),
            "length 32 of 'score' is an int on a fraction axis: write [32, 1]",
        ),
        (
            timeline("score", length=0.5),
            "length 0.5 of 'score' is a float on a fraction axis: write [1, 2]",
        ),
        (
            timeline("score", length=0.1),
            "length 0.1 of 'score' is a float on a fraction axis: write "
            "[3602879701896397, 36028797018963968]",
        ),
        (
            timeline("take", "seconds", (3, 4)),
            "length [3, 4] of 'take' is a fraction on a float axis: write 0.75",
        ),
        (
            timeline("take", "seconds", (1, 3)),
            "length [1, 3] of 'take' is a fraction on a float axis: write a float",
        ),
        (
            timeline("midi", "ticks", (480, 1)),
            "length [480, 1] of 'midi' is a fraction on an int axis: write 480",
        ),
        (
            timeline("midi", "ticks", 0.5),
            "length 0.5 of 'midi' is a float on an int axis: write an int",
        ),
        (
            timeline("midi", "ticks", (1, 2)),
            "length [1, 2] of 'midi' is a fraction on an int axis: write an int",
        ),
        (
            timeline("take", "seconds", 9007199254740993),
            "length 9007199254740993 of 'take' is an int on a float axis: "
            "write a float",
        ),
        (
            timeline("take", "seconds", 2.0, number_type="fraction"),
            "length 2.0 of 'take' is a float on a fraction axis: write [2, 1]",
        ),
        (
            timeline("score", length=(2, 1), number_type="float"),
            "length [2, 1] of 'score' is a fraction on a float axis: write 2.0",
        ),
        (
            timeline("score", offset=3),
            "offset 3 of 'score' is an int on a fraction axis: write [3, 1]",
        ),
    ],
)
def test_a_length_or_offset_in_another_representation(root: dict, message: str) -> None:
    key = message.split(" ", 1)[0]
    assert _problem(manifest(root)) == (("timelines", 0, key), message)


@pytest.mark.parametrize("child_unit", ["seconds", "quarters"])
def test_a_child_offset_lies_on_its_parents_axis(child_unit: str) -> None:
    child = timeline("take", child_unit, 4.0 if child_unit == "seconds" else (4, 1))
    child["offset"] = [1, 2]
    value = manifest(timeline("recording", "seconds", 60.0, children=[child]))
    assert _problem(value) == (
        ("timelines", 0, "children", 0, "offset"),
        "offset [1, 2] of 'take' is a fraction on a float axis: write 0.5",
    )


@pytest.mark.parametrize(
    ("member", "entry", "key"),
    [
        ("regions", {"id": "intro", "start": 1, "end": [2, 1]}, "start"),
        ("regions", {"id": "intro", "start": [1, 1], "end": 2}, "end"),
        ("breaks", {"id": "fine", "coordinate": 4}, "coordinate"),
        ("markers", {"id": "segno", "coordinate": 4}, "coordinate"),
        (
            "jumps",
            {"id": "back", "from_coordinate": 4, "to_coordinate": [0, 1]},
            "from_coordinate",
        ),
        (
            "jumps",
            {"id": "back", "from_coordinate": [4, 1], "to_coordinate": 0},
            "to_coordinate",
        ),
    ],
)
def test_every_own_axis_value_is_checked(member: str, entry: dict, key: str) -> None:
    root = timeline("score")
    if member == "regions":
        root["regions"] = [entry]
        path: tuple[str | int, ...] = ("timelines", 0, "regions", 0, key)
    else:
        root["flow_control"] = {member: [entry]}
        path = ("timelines", 0, "flow_control", member, 0, key)
    value = entry[key]
    assert _problem(manifest(root)) == (
        path,
        f"{key} {value} of '{entry['id']}' is an int on a fraction axis: "
        f"write [{value}, 1]",
    )


@pytest.mark.parametrize(
    "root",
    [
        timeline("midi", "ticks", 8),
        timeline("midi", "ticks", 8.0),
        timeline("take", "seconds", 8),
        timeline("take", "seconds", 0.5),
        timeline("take", "seconds", 9007199254740992),
        timeline("take", "seconds", 10**20),
        timeline("score", length=(8, 1)),
        timeline("score", length=None),
        timeline("take", "seconds", 2.5, offset=-1700000000.25),
        timeline("score", offset=[-3, 2]),
    ],
)
def test_values_in_their_axis_representation_validate(root: dict) -> None:
    validate(manifest(root))


def test_the_first_representation_problem_is_raised() -> None:
    root = timeline("score", length=8, regions=[{"id": "r", "start": 0, "end": [1, 1]}])
    assert _problem(manifest(root))[0] == ("timelines", 0, "length")


# -- unknown length ---------------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        manifest(timeline("score", length=None)),
        manifest(timeline("score", length=None, locked=True)),
        manifest(
            timeline("score", children=[timeline("c", length=None, offset=(2, 1))])
        ),
        manifest(
            timeline("score", length=None, children=[timeline("c", offset=(2, 1))])
        ),
        manifest(
            timeline("score"),
            timeline("perf", "seconds", None),
            groups=[{"id": "g", "members": ["perf", "score"]}],
        ),
    ],
    ids=["root", "locked", "child", "known child of unknown parent", "group member"],
)
def test_an_unknown_length_is_no_violation(value: dict) -> None:
    validate(value)


# -- shared rejections -------------------------------------------------------------


def test_the_rejection_cases_are_stated() -> None:
    assert [path.stem for path in rejection_paths()] == REJECTIONS


@pytest.mark.parametrize("path", rejection_paths(), ids=lambda path: path.stem)
def test_shared_rejection_is_rejected_at_its_path(path: Path) -> None:
    case = json.loads(path.read_text(encoding="utf-8"))
    assert dumps(case) == path.read_text(encoding="utf-8")
    if case.get("error") == "UnsupportedVersionError":
        assert case["path"] == ["timeskeleton"]
        with pytest.raises(UnsupportedVersionError):
            validate(case["manifest"])
        return
    assert "error" not in case
    with pytest.raises(SchemaValidationError) as caught:
        validate(case["manifest"])
    assert list(caught.value.path) == case["path"]


# -- errors and paths ---------------------------------------------------------------


def test_error_renders_as_json_pointer() -> None:
    with pytest.raises(SchemaValidationError) as caught:
        validate(manifest(timeline("score", unit="beats")))
    assert caught.value.path == ("timelines", 0, "unit")
    assert str(caught.value).startswith("#/timelines/0/unit: ")


def test_json_pointer_rendering() -> None:
    assert json_pointer(()) == "#"
    assert json_pointer(("a/b", "c~d", 0)) == "#/a~1b/c~0d/0"


@pytest.mark.parametrize("value", [9007199254740993, 9223372036854775807])
def test_integer_boundaries_validate_and_preserve(value: int) -> None:
    document = manifest(timeline("midi", "ticks", value))
    validate(document)
    assert json.loads(dumps(document))["timelines"][0]["length"] == value


def _styled(declaration: dict) -> dict:
    return manifest(
        timeline("score"),
        graphical={
            "statements": [{"select": {"element": "timeline"}, "set": declaration}]
        },
    )


@pytest.mark.parametrize(
    "declaration",
    [
        {"stroke-width": 0, "rx": 0},
        {"opacity": 0},
        {"opacity": 1},
        {"font-size": 0.5, "max-width": 1},
        {"max-width": "none", "content": "Score"},
        {"stroke-dasharray": "none"},
        {"stroke-dasharray": "4 2.5"},
    ],
)
def test_graphical_property_bounds_accept_exact_valid_values(declaration: dict) -> None:
    validate(_styled(declaration))


@pytest.mark.parametrize(
    ("declaration", "member"),
    [
        ({"stroke-width": -1}, "stroke-width"),
        ({"rx": -0.5}, "rx"),
        ({"opacity": -0.1}, "opacity"),
        ({"opacity": 1.1}, "opacity"),
        ({"font-size": 0}, "font-size"),
        ({"max-width": 0}, "max-width"),
        ({"content": 5}, "content"),
        ({"stroke-dasharray": "4,2"}, "stroke-dasharray"),
    ],
)
def test_graphical_property_bounds_reject_at_the_property(
    declaration: dict, member: str
) -> None:
    path = _problem(_styled(declaration))[0]
    assert path == ("graphical", "statements", 0, "set", member)


@pytest.mark.parametrize(
    "statement",
    [
        {"select": {"element": "card"}, "set": {"rx": 5}},
        {"select": {"inside": "ancestor"}, "set": {"opacity": 0.35}},
        {"select": {"element": "card"}, "set": {"shadow": "#B8BEC8"}},
    ],
)
def test_card_inside_and_shadow_validate(statement: dict) -> None:
    validate(manifest(timeline("score"), graphical={"statements": [statement]}))


def _defaults_block() -> dict:
    """The JSON block of section 4 of the drawing specification."""
    text = (REPOSITORY_ROOT / "docs" / "drawing.md").read_text(encoding="utf-8")
    section = text.split("\n## 4. Defaults\n", 1)[1]
    block = section.split("```json\n", 1)[1].split("\n```", 1)[0]
    return json.loads(block)


def test_the_defaults_are_a_valid_graphical_block() -> None:
    defaults = _defaults_block()
    assert len(defaults["styles"]) == 3
    assert len(defaults["statements"]) == 28
    validate({**SMALLEST, "graphical": defaults})


def test_names_remain_unrestricted() -> None:
    validate(manifest(timeline("score", name="tab\there\nnewline")))
