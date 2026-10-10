from __future__ import annotations

import copy

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

SCHEMA_ID = "https://timetoalign.github.io/timeskeleton/0.2.1/timeskeleton.schema.json"

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
    assert SCHEMA_VERSION == "0.2.1"
    assert SUPPORTED_VERSIONS == ("0.1.0", "0.2.0", "0.2.1")
    assert SUPPORTED_VERSIONS[-1] == SCHEMA_VERSION


def test_schema_path_names_the_bundled_file() -> None:
    path = schema_path()
    assert path.is_file()
    assert path.name == "timeskeleton-0.2.1.schema.json"
    assert schema_path("0.2.1") == path


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
    expected["$id"] = SCHEMA_ID
    expected["description"] = load_schema("0.2.1")["description"]
    assert expected["description"].startswith(load_schema("0.2.0")["description"][:40])
    expected["properties"]["meta"]["properties"]["schema_version"]["const"] = "0.2.1"
    assert load_schema("0.2.1") == expected


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
    assert len(names) == 16
    assert {f"{name}.json" for name in FIXTURE_NAMES}.issubset(names)
    assert "conversion_maps.json" in names
    assert "flow_control.json" in names


@pytest.mark.parametrize("accessor", [schema_path, load_schema, fixture_paths])
def test_unknown_version_is_refused(accessor) -> None:
    with pytest.raises(UnsupportedVersionError) as caught:
        accessor("9.9.9")
    assert caught.value.version == "9.9.9"
