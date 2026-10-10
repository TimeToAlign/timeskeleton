from __future__ import annotations

import copy
import json

import pytest

from timeskeleton import (
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    UnsupportedVersionError,
    fixture_paths,
    load_schema,
    schema_path,
)

from .conftest import FIXTURE_NAMES

SCHEMA_ID = "https://timetoalign.github.io/timeskeleton/0.3.0/timeskeleton.schema.json"

TIMELINE_CLASSES = [
    "ContinuousLogicalTimeline",
    "ContinuousPhysicalTimeline",
    "ContinuousGraphicalTimeline",
    "DiscreteLogicalTimeline",
    "DiscretePhysicalTimeline",
    "DiscreteGraphicalTimeline",
]

TIME_UNITS = [
    "number",
    "floating_measures",
    "whole_note",
    "quarters",
    "ticks",
    "milliseconds",
    "seconds",
    "minutes",
    "samples",
    "frames",
    "pixels",
    "meters",
    "centimeters",
    "millimeters",
    "inches",
    "points",
]

NUMBER_TYPES = ["int", "float", "fraction"]

MEASURE_MAP_ROW_KEYS = [
    "ID",
    "count",
    "qstamp",
    "number",
    "name",
    "time_signature",
    "nominal_length",
    "actual_length",
    "start_repeat",
    "end_repeat",
    "next",
    "volta",
    "offset_within_measure",
]

MANIFEST_KEYS = [
    "id",
    "name",
    "class",
    "unit",
    "number_type",
    "length",
    "locked",
    "meta",
    "children",
    "conversion_maps",
    "regions",
    "flow_control",
    "measure_map",
    "metric_hierarchy",
]


def test_schema_version_is_the_latest_supported_version() -> None:
    assert SCHEMA_VERSION == "0.3.0"
    assert SUPPORTED_VERSIONS == ("0.1.0", "0.2.0", "0.2.1", "0.3.0")
    assert SUPPORTED_VERSIONS[-1] == SCHEMA_VERSION


def test_schema_path_names_the_bundled_file() -> None:
    path = schema_path()
    assert path.is_file()
    assert path.name == "timeskeleton-0.3.0.schema.json"
    assert schema_path("0.3.0") == path


def test_schema_identity() -> None:
    schema = load_schema()
    assert schema["$id"] == SCHEMA_ID
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    version = schema["properties"]["meta"]["properties"]["schema_version"]
    assert version == {
        "const": SCHEMA_VERSION,
        "description": "The timeskeleton release this document conforms to.",
    }


def test_0_2_1_differs_from_0_2_0_in_its_id_version_and_description_only() -> None:
    expected = copy.deepcopy(load_schema("0.2.0"))
    expected["$id"] = SCHEMA_ID.replace("0.3.0", "0.2.1")
    expected["description"] = load_schema("0.2.1")["description"]
    assert expected["description"].startswith(load_schema("0.2.0")["description"][:40])
    expected["properties"]["meta"]["properties"]["schema_version"]["const"] = "0.2.1"
    assert load_schema("0.2.1") == expected


GRAPHICAL_DEFINITIONS = [
    "Graphical",
    "StyleRules",
    "StyleRule",
    "StyleSelector",
    "ElementType",
    "StyleProperties",
]


def test_0_3_0_is_0_2_1_plus_the_graphical_block() -> None:
    schema = copy.deepcopy(load_schema("0.3.0"))
    assert list(schema["properties"]) == ["meta", "manifest", "graphical"]
    assert schema["properties"].pop("graphical") == {"$ref": "#/$defs/Graphical"}
    assert list(schema["$defs"])[-len(GRAPHICAL_DEFINITIONS) :] == GRAPHICAL_DEFINITIONS
    for name in GRAPHICAL_DEFINITIONS:
        del schema["$defs"][name]
    previous = load_schema("0.2.1")
    assert schema["description"].startswith(previous["description"] + " Version 0.3.0")
    schema["description"] = previous["description"]
    schema["$id"] = previous["$id"]
    schema["properties"]["meta"]["properties"]["schema_version"]["const"] = "0.2.1"
    assert schema == previous
    assert "graphical" not in schema["required"]


def test_the_graphical_block_vocabulary() -> None:
    defs = load_schema()["$defs"]
    graphical = defs["Graphical"]
    assert graphical["properties"] == {
        "styles": {"$ref": "#/$defs/StyleRules"},
        "timelines": {
            "type": "object",
            "description": graphical["properties"]["timelines"]["description"],
            "additionalProperties": {"$ref": "#/$defs/StyleRules"},
        },
    }
    assert "required" not in graphical
    assert graphical["additionalProperties"] is False
    assert defs["StyleRules"]["items"] == {"$ref": "#/$defs/StyleRule"}
    assert defs["StyleRule"]["required"] == ["select", "set"]
    assert defs["ElementType"]["enum"] == [
        "timeline",
        "child",
        "map",
        "region",
        "break",
        "jump",
        "wedge",
        "label",
    ]
    selector = defs["StyleSelector"]
    assert list(selector["properties"]) == ["element", "domain", "modality", "ids"]
    domains = selector["properties"]["domain"]["enum"]
    assert domains == ["graphical", "logical", "physical"]
    assert selector["properties"]["modality"]["enum"] == ["continuous", "discrete"]
    assert selector["properties"]["ids"]["minItems"] == 1
    assert selector["additionalProperties"] is False
    properties = defs["StyleProperties"]
    assert list(properties["properties"]) == [
        "colour",
        "line_pattern",
        "visible",
        "side",
        "show_length",
        "show_projected_coordinates",
    ]
    assert properties["properties"]["colour"]["pattern"] == "^#[0-9A-F]{6}$"
    patterns = properties["properties"]["line_pattern"]["enum"]
    assert patterns == ["solid", "dotted", "dashed"]
    assert properties["properties"]["side"]["enum"] == ["above", "below"]
    assert properties["additionalProperties"] is False
    assert properties["minProperties"] == 1


def test_enumerations_are_the_library_vocabulary() -> None:
    defs = load_schema()["$defs"]
    assert defs["TimelineClass"]["enum"] == TIMELINE_CLASSES
    assert defs["TimeUnit"]["enum"] == TIME_UNITS
    assert defs["NumberType"]["enum"] == NUMBER_TYPES


def test_timeline_manifest_is_closed_over_fourteen_keys() -> None:
    manifest = load_schema()["$defs"]["TimelineManifest"]
    assert manifest["required"] == MANIFEST_KEYS
    assert list(manifest["properties"]) == MANIFEST_KEYS
    assert manifest["additionalProperties"] is False


def test_measure_map_is_a_nonempty_compressed_row_list() -> None:
    measure_map = load_schema()["$defs"]["MeasureMap"]
    row = load_schema()["$defs"]["MeasureMapRow"]
    assert measure_map["type"] == "array"
    assert measure_map["items"] == {"$ref": "#/$defs/MeasureMapRow"}
    assert measure_map["minItems"] == 1
    assert list(row["properties"]) == MEASURE_MAP_ROW_KEYS
    assert row["anyOf"] == [{"required": ["ID"]}, {"required": ["count"]}]
    assert row["additionalProperties"] is False
    properties = row["properties"]
    assert properties["actual_length"]["$ref"] == "#/$defs/NumberPositive"
    assert properties["offset_within_measure"]["$ref"] == "#/$defs/NumberPositive"
    assert properties["qstamp"]["$ref"] == "#/$defs/NumberNonnegative"
    assert properties["nominal_length"]["anyOf"] == [
        {"$ref": "#/$defs/NumberPositive"},
        {"type": "null"},
    ]


def test_measure_map_is_admitted_on_quarters_timelines_only() -> None:
    manifest = load_schema()["$defs"]["TimelineManifest"]
    assert manifest["if"] == {
        "properties": {"unit": {"const": "quarters"}},
        "required": ["unit"],
    }
    assert manifest["else"] == {"properties": {"measure_map": {"type": "null"}}}


def test_metrical_position_map_states_its_meter_map_once() -> None:
    position_map = load_schema()["$defs"]["MetricalPositionMap"]
    assert position_map["required"] == [
        "type",
        "id",
        "name",
        "source_unit",
        "target_unit",
        "meter_map",
        "beat_map_id",
    ]
    assert position_map["additionalProperties"] is False


def test_fixture_set_contains_the_synthetic_and_extended_documents() -> None:
    names = [path.name for path in fixture_paths()]
    assert len(names) == 20
    assert {f"{name}.json" for name in FIXTURE_NAMES}.issubset(names)
    assert "conversion_maps.json" in names
    assert "flow_control.json" in names
    assert {"bare.json", "contiguous.json", "map.json", "styled.json"}.issubset(names)


def test_the_0_3_0_fixtures_are_the_0_2_1_fixtures_and_four_drawings() -> None:
    previous = {path.name: path for path in fixture_paths("0.2.1")}
    current = {path.name: path for path in fixture_paths("0.3.0")}
    assert sorted(set(current) - set(previous)) == [
        "bare.json",
        "contiguous.json",
        "map.json",
        "styled.json",
    ]
    generator = json.loads(current["empty.json"].read_text(encoding="utf-8"))["meta"][
        "generator"
    ]
    for name, path in previous.items():
        old = json.loads(path.read_text(encoding="utf-8"))["meta"]["generator"]
        expected = (
            path.read_text(encoding="utf-8")
            .replace('"schema_version": "0.2.1"', '"schema_version": "0.3.0"')
            .replace(json.dumps(old), json.dumps(generator))
        )
        assert current[name].read_text(encoding="utf-8") == expected, name


def test_only_the_styled_fixture_carries_a_graphical_block() -> None:
    styled = []
    for path in fixture_paths():
        document = json.loads(path.read_text(encoding="utf-8"))
        if "graphical" in document:
            styled.append(path.name)
            assert list(document) == ["meta", "manifest", "graphical"]
            assert document["graphical"] == {
                "styles": [
                    {"select": {}, "set": {"show_length": True}},
                    {"select": {"element": "label"}, "set": {"colour": "#404040"}},
                    {"select": {"element": "map"}, "set": {"side": "below"}},
                    {"select": {"ids": ["a"]}, "set": {"visible": False}},
                ],
                "timelines": {
                    "score": [
                        {
                            "select": {"element": "wedge"},
                            "set": {"side": "above", "colour": "#006600"},
                        },
                        {"select": {"domain": "logical"}, "set": {"colour": "#000080"}},
                        {"select": {"element": "region"}, "set": {"colour": "#800000"}},
                        {"select": {"element": "region"}, "set": {"colour": "#008080"}},
                        {"select": {"element": "child"}, "set": {"visible": True}},
                    ],
                    "b": [
                        {
                            "select": {},
                            "set": {
                                "colour": "#FF8000",
                                "show_projected_coordinates": True,
                            },
                        }
                    ],
                    "perf": [
                        {
                            "select": {"element": "wedge", "domain": "physical"},
                            "set": {"colour": "#7F00FF"},
                        }
                    ],
                },
            }
    assert styled == ["styled.json"]


@pytest.mark.parametrize("accessor", [schema_path, load_schema, fixture_paths])
def test_unknown_version_is_refused(accessor) -> None:
    with pytest.raises(UnsupportedVersionError) as caught:
        accessor("9.9.9")
    assert caught.value.version == "9.9.9"
