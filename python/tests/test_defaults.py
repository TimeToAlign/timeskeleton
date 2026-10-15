from __future__ import annotations

import json
from typing import Any

import pytest

from timeskeleton import complete, dumps, minimal, validate

from .conftest import bundle, manifest, timeline

SMALLEST = {
    "timeskeleton": "0.7.0",
    "timelines": [{"id": "piece", "unit": "quarters", "length": [32, 1]}],
}
EMPTY_FLOW = {"breaks": [], "jumps": [], "markers": []}


def test_the_smallest_file_completes_to_the_literal_complete_form() -> None:
    assert complete(SMALLEST) == {
        "timeskeleton": "0.7.0",
        "name": None,
        "meta": {},
        "groups": [],
        "timelines": [
            {
                "id": "piece",
                "unit": "quarters",
                "length": [32, 1],
                "name": None,
                "number_type": "fraction",
                "locked": False,
                "is_segment_line": False,
                "meta": {},
                "children": [],
                "conversion_maps": [],
                "regions": [],
                "flow_control": EMPTY_FLOW,
                "measure_map": None,
                "metric_hierarchy": None,
            }
        ],
    }
    assert minimal(complete(SMALLEST)) == SMALLEST


def test_every_object_gains_exactly_its_defaults() -> None:
    shift = {
        "type": "ShiftMap",
        "id": "s",
        "source_unit": None,
        "target_unit": None,
        "offset": 1,
    }
    metric = {
        "type": "MetricMap",
        "id": "mm",
        "source_unit": None,
        "target_unit": None,
        "starts": [],
        "mcs": [],
        "mns": [],
        "lengths": [],
    }
    root = timeline(
        "score",
        regions=[{"id": "r", "start": [0, 1], "end": [1, 1]}],
        flow_control={
            "breaks": [{"id": "b", "coordinate": [1, 1]}],
            "jumps": [{"id": "j", "from_coordinate": [1, 1], "to_coordinate": [0, 1]}],
            "markers": [{"id": "m", "coordinate": [0, 1]}],
        },
        conversion_maps=[
            {
                "type": "ChainMap",
                "id": "chain",
                "source_unit": None,
                "target_unit": None,
                "maps": [shift],
            },
            {
                "type": "CombinationMap",
                "id": "combo",
                "source_unit": None,
                "target_unit": None,
                "maps": {"x": {**shift, "id": "x"}},
                "names": ["x"],
            },
            {
                "type": "BeatInMeasureMap",
                "id": "bim",
                "source_unit": None,
                "target_unit": None,
                "meter_map": metric,
            },
        ],
    )
    value = complete(
        manifest(root, groups=[{"id": "g", "members": ["score"]}], graphical={})
    )
    done = value["timelines"][0]
    assert done["regions"][0] == {
        "id": "r",
        "start": [0, 1],
        "end": [1, 1],
        "name": None,
        "meta": {},
    }
    flow = done["flow_control"]
    assert flow["breaks"][0] == {
        "id": "b",
        "coordinate": [1, 1],
        "control_type": "section_break",
        "condition": "always",
        "repeat_count": 1,
        "label": None,
        "name": None,
        "meta": {},
    }
    assert flow["jumps"][0] == {
        "id": "j",
        "from_coordinate": [1, 1],
        "to_coordinate": [0, 1],
        "control_type": "repeat_end",
        "condition": "first_n",
        "repeat_count": 1,
        "target": None,
        "label": None,
        "meta": {},
    }
    assert flow["markers"][0] == {"id": "m", "coordinate": [0, 1], "name": None}
    chain, combo, bim = done["conversion_maps"]
    assert chain["name"] is None and chain["maps"][0]["name"] is None
    assert combo["name"] is None and combo["maps"]["x"]["name"] is None
    assert bim["name"] is None and bim["meter_map"]["name"] is None
    assert value["groups"] == [
        {"id": "g", "members": ["score"], "name": None, "meta": {}}
    ]
    assert value["graphical"] == {"styles": {}, "statements": [], "order": {}}
    validate(value)


@pytest.mark.parametrize(
    ("unit", "number_type"),
    [
        ("ticks", "int"),
        ("seconds", "float"),
        ("whole_note", "fraction"),
        ("pixels", "int"),
    ],
)
def test_the_unit_decides_the_default_number_type(unit: str, number_type: str) -> None:
    value = complete(manifest(timeline("t", unit, None)))
    assert value["timelines"][0]["number_type"] == number_type
    assert "number_type" not in minimal(value)["timelines"][0]


def test_absent_defaults_are_never_added_or_removed() -> None:
    value = complete(SMALLEST)
    assert "id" not in value and "graphical" not in value
    assert "offset" not in value["timelines"][0]
    styled = manifest(timeline("score"), graphical={})
    assert minimal(styled)["graphical"] == {}
    assert complete(styled)["graphical"] == {
        "styles": {},
        "statements": [],
        "order": {},
    }
    child = manifest(timeline("score", children=[timeline("c", offset=(0, 1))]))
    assert minimal(child)["timelines"][0]["children"][0]["offset"] == [0, 1]


def test_values_other_than_the_default_stay() -> None:
    value = manifest(
        timeline(
            "score",
            locked=True,
            number_type="float",
            length=8.0,
            flow_control={
                "breaks": [{"id": "b", "coordinate": 1.0, "repeat_count": 2}],
                "jumps": [],
            },
        )
    )
    assert minimal(value) == manifest(
        timeline(
            "score",
            locked=True,
            number_type="float",
            length=8.0,
            flow_control={
                "breaks": [{"id": "b", "coordinate": 1.0, "repeat_count": 2}]
            },
        )
    )


def test_a_value_of_another_type_is_not_the_default() -> None:
    value = manifest(
        timeline(
            "score",
            flow_control={
                "breaks": [{"id": "b", "coordinate": [1, 1], "repeat_count": 1.0}]
            },
        )
    )
    assert dumps(minimal(value)) == dumps(value)
    assert dumps(complete(minimal(value))) == dumps(complete(value))


def test_unknown_keys_pass_through() -> None:
    value = manifest(
        timeline("score", lenght=1, flow_control={"codas": [], "breaks": []}),
        extra={"meta": {}},
    )
    assert minimal(value) == manifest(
        timeline("score", lenght=1, flow_control={"codas": []}),
        extra={"meta": {}},
    )
    assert complete(value)["extra"] == {"meta": {}}
    assert complete(value)["timelines"][0]["flow_control"]["codas"] == []


def test_length_survives_both_forms() -> None:
    for length in (None, [8, 1]):
        value = manifest(timeline("score", length=length))
        assert complete(value)["timelines"][0]["length"] == length
        assert minimal(value)["timelines"][0]["length"] == length


def _documents() -> list[dict[str, Any]]:
    return [
        SMALLEST,
        complete(SMALLEST),
        bundle(),
        manifest(timeline("score", lenght=1, flow_control={"codas": [], "breaks": []})),
        manifest(
            timeline("score", locked=True, children=[timeline("c", offset=(0, 1))]),
            graphical={},
        ),
        manifest(
            timeline(
                "score",
                flow_control={
                    "jumps": [
                        {
                            "id": "j",
                            "from_coordinate": [4, 1],
                            "to_coordinate": [0, 1],
                            "repeat_count": 1.0,
                        }
                    ]
                },
            )
        ),
    ]


@pytest.mark.parametrize("value", _documents())
def test_the_round_trips(value: dict) -> None:
    given = json.dumps(value)
    assert dumps(minimal(complete(value))) == dumps(minimal(value))
    assert dumps(complete(minimal(value))) == dumps(complete(value))
    assert complete(value) is not value and minimal(value) is not value
    assert json.dumps(value) == given
    validate(complete(value))
    validate(minimal(value))
