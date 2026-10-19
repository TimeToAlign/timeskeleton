from __future__ import annotations

import copy
import json
import math
from typing import Any

import pytest

from timeskeleton import (
    canonical_json,
    canonical_order,
    complete,
    dumps,
    fixture_paths,
    minimal,
    rejection_paths,
    validate,
    warning_paths,
)

from .conftest import bundle, manifest, respellable, respelled, timeline

# Shared with the JavaScript suite, character for character.
NUMBER_CORPUS = (
    "[0.1, 2.0, 1e-07, 1e+16, 123456789012345678, -0.0, 5e-324, "
    "1.7976931348623157e+308, 1E5, 1.50, -0, 100, 0.0001, 1e-05, "
    '1000000000000000.0, "\\u00e9", "\\ud83d\\ude00", "\\ufb00", '
    '"a\\"b\\\\c\\n\\u0001\\u001f"]'
)
NUMBER_CORPUS_TEXT = (
    "[\n"
    "  0.1,\n"
    "  2.0,\n"
    "  1e-07,\n"
    "  1e+16,\n"
    "  123456789012345678,\n"
    "  -0.0,\n"
    "  5e-324,\n"
    "  1.7976931348623157e+308,\n"
    "  100000.0,\n"
    "  1.5,\n"
    "  0,\n"
    "  100,\n"
    "  0.0001,\n"
    "  1e-05,\n"
    "  1000000000000000.0,\n"
    '  "é",\n'
    '  "\U0001f600",\n'
    '  "ﬀ",\n'
    '  "a\\"b\\\\c\\n\\u0001\\u001f"\n'
    "]\n"
)


def _standard_files() -> list:
    return [*fixture_paths(), *rejection_paths(), *warning_paths()]


@pytest.mark.parametrize(
    "path", _standard_files(), ids=lambda path: f"{path.parent.name}/{path.name}"
)
def test_standard_files_round_trip_byte_for_byte(path) -> None:
    text = path.read_text(encoding="utf-8")
    assert dumps(json.loads(text)) == text


def test_number_corpus() -> None:
    assert dumps(json.loads(NUMBER_CORPUS)) == NUMBER_CORPUS_TEXT


def test_canonical_order_copies_and_reorders_manifests_only() -> None:
    value = manifest(timeline("b"), timeline("a"))
    text = json.dumps(value)
    assert [root["id"] for root in canonical_order(value)["timelines"]] == ["a", "b"]
    assert json.dumps(value) == text
    other = {"b": [3, 1], "timeline": {"regions": [{"id": "z"}, {"id": "a"}]}}
    assert json.dumps(canonical_order(other)) == json.dumps(other)


def test_the_writer_sorts_every_object_by_key() -> None:
    value = {"b": 1, "\U0001f600": 2, "\ufb00": 3, "A": {"z": 0, "10": 1, "2": 2}}
    assert dumps(value) == (
        "{\n"
        '  "A": {\n'
        '    "10": 1,\n'
        '    "2": 2,\n'
        '    "z": 0\n'
        "  },\n"
        '  "b": 1,\n'
        '  "\ufb00": 3,\n'
        '  "\U0001f600": 2\n'
        "}\n"
    )


def _tied_manifest() -> dict[str, Any]:
    """A manifest with ties at every key level, own-axis values in mixed forms."""
    regions = [
        ("rb", [2, 1], [6, 1]),
        ("ra", [2, 1], [6, 1]),
        ("rc", [2, 1], [4, 1]),
        ("rd", [5, 8], [2, 3]),
    ]
    root = timeline(
        "piece",
        length=(16, 1),
        number_type="fraction",
        children=[
            timeline(
                "z",
                offset=(1, 1),
                children=[
                    timeline("y", length=(2, 1), offset=(1, 1)),
                    timeline("x", length=(2, 1), offset=(0, 1)),
                ],
            ),
            timeline("m", offset=(1, 1)),
            timeline("b", offset=(5, 8)),
            timeline("a", offset=(2, 3)),
        ],
        conversion_maps=[
            {
                "type": "ShiftMap",
                "id": map_id,
                "source_unit": "quarters",
                "target_unit": None,
                "offset": [1, 2],
            }
            for map_id in ["\U0001f600", "\ufb00", "B2", "a2", "B"]
        ],
        regions=[{"id": i, "start": s, "end": e} for i, s, e in regions],
        flow_control={
            "breaks": [
                {"id": "kb", "coordinate": [12, 1]},
                {"id": "ka", "coordinate": [12, 1]},
                {"id": "kz", "coordinate": [5, 8]},
            ],
            "jumps": [
                {
                    "id": "jj",
                    "from_coordinate": [8, 1],
                    "to_coordinate": [2, 1],
                    "target": "Coda",
                },
                {"id": "jd", "from_coordinate": [8, 1], "to_coordinate": [2, 1]},
                {"id": "js", "from_coordinate": [8, 1], "to_coordinate": [2, 3]},
                {"id": "je", "from_coordinate": [5, 8], "to_coordinate": [2, 1]},
            ],
            "markers": [
                {"id": marker_id, "coordinate": coordinate}
                for marker_id, coordinate in [
                    ("\U0001f600!", [2, 1]),
                    ("\ufb00!", [2, 1]),
                    ("\u00e9", [2, 1]),
                    ("Coda", [2, 1]),
                    ("starting", [5, 8]),
                ]
            ],
        },
    )
    return manifest(root)


def test_every_tie_resolves_to_the_canonical_order() -> None:
    result = canonical_order(_tied_manifest())
    validate(result)
    root = result["timelines"][0]
    assert [child["id"] for child in root["children"]] == ["b", "a", "m", "z"]
    assert [child["id"] for child in root["children"][3]["children"]] == ["x", "y"]
    assert [entry["id"] for entry in root["conversion_maps"]] == [
        "B",
        "B2",
        "a2",
        "\ufb00",
        "\U0001f600",
    ]
    assert [entry["id"] for entry in root["regions"]] == ["rd", "rc", "ra", "rb"]
    flow = root["flow_control"]
    assert [entry["id"] for entry in flow["breaks"]] == ["kz", "ka", "kb"]
    assert [entry["id"] for entry in flow["jumps"]] == ["je", "js", "jd", "jj"]
    assert [entry["id"] for entry in flow["markers"]] == [
        "starting",
        "Coda",
        "\u00e9",
        "\ufb00!",
        "\U0001f600!",
    ]


def test_bare_values_compare_by_exact_value() -> None:
    root = timeline(
        "take",
        "seconds",
        10.0,
        children=[
            timeline("late", "seconds", 1.0, offset=2),
            timeline("tie-b", "seconds", 1.0, offset=0.625),
            timeline("tie-a", "seconds", 1.0, offset=0.625),
            timeline("early", "seconds", 1.0, offset=0.5),
        ],
        regions=[
            {"id": "r2", "start": 1, "end": 2.5},
            {"id": "r1", "start": 1.0, "end": 2},
        ],
    )
    result = canonical_order(manifest(root))["timelines"][0]
    assert [child["id"] for child in result["children"]] == [
        "early",
        "tie-a",
        "tie-b",
        "late",
    ]
    assert [region["id"] for region in result["regions"]] == ["r1", "r2"]
    mixed = canonical_order(
        {
            "timelines": [
                {
                    "id": "q",
                    "children": [
                        {"id": "c", "offset": [5, 8]},
                        {"id": "b", "offset": 0.625},
                        {"id": "a", "offset": [2, 1]},
                    ],
                }
            ]
        }
    )
    assert [child["id"] for child in mixed["timelines"][0]["children"]] == [
        "b",
        "c",
        "a",
    ]


def test_roots_groups_and_members_are_ordered_and_display_orders_kept() -> None:
    value = bundle()
    value["timelines"].reverse()
    value["groups"].reverse()
    for group in value["groups"]:
        group["members"].reverse()
    value["graphical"]["order"] = {
        "group_2": ["excerpt", "page"],
        "group_1": ["performance", "score"],
    }
    given = copy.deepcopy(value)
    result = canonical_order(value)
    assert value == given
    assert [root["id"] for root in result["timelines"]] == [
        "annotations",
        "page",
        "performance",
        "recording",
        "score",
    ]
    assert [group["id"] for group in result["groups"]] == ["group_1", "group_2"]
    assert [group["members"] for group in result["groups"]] == [
        ["performance", "score"],
        ["excerpt", "page"],
    ]
    assert result["graphical"]["order"] == {
        "group_2": ["excerpt", "page"],
        "group_1": ["performance", "score"],
    }
    validate(result)


def test_members_are_ordered_by_code_point() -> None:
    value = {
        "timelines": [],
        "groups": [{"id": "g", "members": ["\U0001f600", "\ufb00", "b"]}],
    }
    assert canonical_order(value)["groups"][0]["members"] == [
        "b",
        "\ufb00",
        "\U0001f600",
    ]


def test_a_member_that_is_no_string_is_refused() -> None:
    value = {"timelines": [], "groups": [{"id": "g", "members": ["a", 5]}]}
    with pytest.raises(ValueError, match="cannot put members in canonical order"):
        canonical_order(value)


def test_readers_coerce_and_writers_spell_canonically() -> None:
    value, twin = respellable(), respelled()
    written = canonical_json(value)
    assert written != canonical_json(twin)
    assert canonical_json(canonical_order(twin)) == canonical_json(twin)
    for convert in (complete, minimal, canonical_order):
        assert canonical_json(convert(value)) == canonical_json(convert(twin)), convert
    assert dumps(value) == dumps(twin)
    assert canonical_json(value) == written


def test_a_value_without_an_exact_respelling_is_left_as_written() -> None:
    value = manifest(timeline("take", "seconds", 9007199254740993))
    (root,) = canonical_order(value)["timelines"]
    assert type(root["length"]) is int
    assert root["length"] == 9007199254740993


def test_canonical_json_text() -> None:
    value = {
        "\U0001f600": {"b": True, "a": [1, 2.5, None]},
        "\ufb00": "\u00fc",
        "\u00e9": 1,
        "z": "\n",
        "a": [],
    }
    assert canonical_json(value) == (
        '{"a":[],"z":"\\n","\u00e9":1,"\ufb00":"\u00fc",'
        '"\U0001f600":{"a":[1,2.5,null],"b":true}}'
    )


@pytest.mark.parametrize(
    "value", ["\ud800", {"\udfff": 1}, math.nan, math.inf], ids=repr
)
def test_values_the_writer_refuses(value) -> None:
    with pytest.raises(ValueError):
        dumps([value])
    with pytest.raises(ValueError):
        canonical_json([value])


def test_an_unorderable_collection_is_refused() -> None:
    value = {"timelines": [{"id": "t", "regions": [{"id": "r"}] * 2}]}
    with pytest.raises(ValueError, match="cannot put regions in canonical order"):
        dumps(value)
