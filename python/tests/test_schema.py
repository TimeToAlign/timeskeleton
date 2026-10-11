from __future__ import annotations

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

SCHEMA_ID = "https://timetoalign.github.io/timeskeleton/0.4.0/timeskeleton.schema.json"

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
ID_PATTERN = r"^[^\u0000-\u001f]*$"

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
    assert SCHEMA_VERSION == "0.4.0"
    assert SUPPORTED_VERSIONS == ("0.4.0",)
    assert SUPPORTED_VERSIONS[-1] == SCHEMA_VERSION


def test_schema_path_names_the_bundled_file() -> None:
    path = schema_path()
    assert path.is_file()
    assert path.name == "timeskeleton-0.4.0.schema.json"
    assert schema_path("0.4.0") == path


def test_schema_identity() -> None:
    schema = load_schema()
    assert schema["$id"] == SCHEMA_ID
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    version = schema["properties"]["meta"]["properties"]["schema_version"]
    assert version == {
        "const": SCHEMA_VERSION,
        "description": "The timeskeleton release this manifest conforms to.",
    }


def test_the_manifest_holds_exactly_one_timeline() -> None:
    schema = load_schema()
    assert list(schema["properties"]) == ["meta", "timeline", "graphical"]
    assert schema["properties"]["timeline"] == {"$ref": "#/$defs/TimelineManifest"}
    assert schema["properties"]["graphical"] == {"$ref": "#/$defs/Graphical"}
    assert schema["required"] == ["meta", "timeline"]
    assert schema["additionalProperties"] is False


CONVERSION_MAP_TYPES = [
    "BeatInMeasureMap",
    "ChainMap",
    "CombinationMap",
    "ConstantMap",
    "FloorMap",
    "InterpolationMap",
    "IntervalToConstantMap",
    "LinearMap",
    "MetricMap",
    "MetricalPositionMap",
    "PiecewiseMap",
    "QuartersToFloatingMeasures",
    "QuartersToMeasureNumber",
    "QuartersToTicks",
    "RotationMap",
    "SamplesToSeconds",
    "ScalarMap",
    "SecondsToSamples",
    "ShiftMap",
    "TableMap",
    "TicksToQuarters",
]


def test_the_graphical_block_vocabulary() -> None:
    defs = load_schema()["$defs"]
    graphical = defs["Graphical"]
    assert graphical["properties"] == {
        "styles": {
            "type": "object",
            "description": graphical["properties"]["styles"]["description"],
            "additionalProperties": {"$ref": "#/$defs/Declaration"},
        },
        "statements": {
            "type": "array",
            "description": graphical["properties"]["statements"]["description"],
            "items": {"$ref": "#/$defs/Statement"},
        },
    }
    assert "required" not in graphical
    assert graphical["additionalProperties"] is False
    statement = defs["Statement"]
    assert statement["required"] == ["select", "set"]
    assert statement["additionalProperties"] is False
    assert statement["properties"]["select"] == {"$ref": "#/$defs/Selector"}
    assert [
        {key: value for key, value in branch.items() if key != "description"}
        for branch in statement["properties"]["set"]["oneOf"]
    ] == [{"$ref": "#/$defs/Declaration"}, {"type": "string"}]
    assert defs["ElementType"]["enum"] == [
        "block",
        "timeline",
        "child",
        "map",
        "region",
        "break",
        "jump",
        "wedge",
        "name",
        "label",
    ]
    map_types = [
        name
        for name, definition in defs.items()
        if definition.get("properties", {}).get("type", {}).get("const") == name
    ]
    assert map_types == CONVERSION_MAP_TYPES
    selector = defs["Selector"]
    properties = selector["properties"]
    assert list(properties) == [
        "element",
        "ids",
        "domain",
        "modality",
        "class",
        "within",
    ]
    assert properties["element"] == {"$ref": "#/$defs/ElementType"}
    assert properties["ids"]["items"] == {"type": "string"}
    assert properties["ids"]["minItems"] == 1
    assert properties["ids"]["uniqueItems"] is True
    assert properties["domain"]["enum"] == ["graphical", "logical", "physical"]
    assert properties["modality"]["enum"] == ["continuous", "discrete"]
    assert properties["class"]["enum"] == TIMELINE_CLASSES + CONVERSION_MAP_TYPES
    assert properties["within"]["type"] == "string"
    assert selector["additionalProperties"] is False
    assert defs["Paint"]["pattern"] == "^(#[0-9A-F]{6}|none)$"
    declaration = defs["Declaration"]
    assert declaration["additionalProperties"] is False
    assert "minProperties" not in declaration
    members = declaration["properties"]
    assert members == {
        "stroke": {"$ref": "#/$defs/Paint"},
        "stroke-width": {"type": "number", "minimum": 0},
        "stroke-dasharray": {
            "type": "string",
            "description": members["stroke-dasharray"]["description"],
            "pattern": (
                "^(none|(0|[1-9][0-9]*)(\\.[0-9]+)?( (0|[1-9][0-9]*)(\\.[0-9]+)?)*)$"
            ),
        },
        "fill": {"$ref": "#/$defs/Paint"},
        "opacity": {"type": "number", "minimum": 0, "maximum": 1},
        "font-size": {"type": "number", "exclusiveMinimum": 0},
        "rx": {"type": "number", "minimum": 0},
        "display": {"type": "string", "enum": ["inline", "none"]},
        "side": {"type": "string", "enum": ["above", "below"]},
        "content": {"type": "string"},
        "max-width": {
            "oneOf": [
                {"type": "number", "exclusiveMinimum": 0},
                {"const": "none"},
            ]
        },
    }


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
    assert manifest["properties"]["metric_hierarchy"]["description"] == (
        "The metric hierarchy, or null; an object without further constraints."
    )


def test_ids_exclude_control_characters() -> None:
    defs = load_schema()["$defs"]
    assert defs["TimelineManifest"]["properties"]["id"]["pattern"] == ID_PATTERN
    assert defs["TimelineManifest"]["properties"]["children"]["propertyNames"] == {
        "pattern": ID_PATTERN
    }
    definitions_with_id = [
        definition
        for definition in defs.values()
        if "id" in definition.get("properties", {})
    ]
    assert len(definitions_with_id) == 22
    assert all(
        definition["properties"]["id"]["pattern"] == ID_PATTERN
        for definition in definitions_with_id
    )


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


def test_fixture_set_contains_exactly_the_0_4_0_manifests() -> None:
    names = [path.name for path in fixture_paths()]
    assert names == [
        "bare.json",
        "contiguous.json",
        "continuous_graphical.json",
        "continuous_logical.json",
        "continuous_physical.json",
        "conversion_maps__maps_quarters.json",
        "conversion_maps__maps_samples.json",
        "conversion_maps__maps_seconds.json",
        "conversion_maps__maps_ticks.json",
        "corpus_audio_audio.json",
        "corpus_midi_score_midi.json",
        "corpus_parangonar_parangonada__perf_1966_Szegedi_cpt1.json",
        "corpus_parangonar_parangonada__perf_1966_Szegedi_dpt1.json",
        "corpus_parangonar_parangonada__perf_1970_Gould_cpt1.json",
        "corpus_parangonar_parangonada__perf_1970_Gould_dpt1.json",
        "corpus_parangonar_parangonada__perf_1971_Curzon_cpt1.json",
        "corpus_parangonar_parangonada__perf_1971_Curzon_dpt1.json",
        "corpus_parangonar_parangonada__perf_1985_Brendel_cpt1.json",
        "corpus_parangonar_parangonada__perf_1985_Brendel_dpt1.json",
        "corpus_parangonar_parangonada__perf_2023_Hewitt_cpt1.json",
        "corpus_parangonar_parangonada__perf_2023_Hewitt_dpt1.json",
        "corpus_parangonar_parangonada__score_clt1.json",
        "corpus_parangonar_parangonada__score_dlt1.json",
        "corpus_score_ms3.json",
        "corpus_supra_iiif.json",
        "discrete_graphical.json",
        "discrete_logical.json",
        "discrete_physical.json",
        "flow_control.json",
        "map.json",
        "nested.json",
        "styled__perf.json",
        "styled__score.json",
        "with_region.json",
    ]


def test_the_styled_manifests_carry_their_statements() -> None:
    grey = {"stroke": "#404040", "fill": "#404040"}
    shared = [
        {"select": {"element": "label"}, "set": grey},
        {"select": {"element": "name"}, "set": grey},
        {"select": {"element": "map"}, "set": {"side": "below"}},
        {"select": {"ids": ["a"]}, "set": {"display": "none"}},
    ]
    green = {"side": "above", "stroke": "#006600", "fill": "#006600"}
    violet = {"stroke": "#7F00FF", "fill": "#7F00FF"}
    accent = {
        "stroke": "#7F00FF",
        "stroke-width": 0,
        "stroke-dasharray": "3 3",
        "fill": "#7F00FF",
        "opacity": 0.5,
        "font-size": 10,
        "rx": 0,
        "display": "inline",
        "side": "above",
        "content": "Styled score",
        "max-width": 160,
    }
    expected = {
        "styled__score.json": {
            "styles": {"accent": accent},
            "statements": [
                *shared,
                {"select": {"element": "wedge", "within": "score"}, "set": green},
                {
                    "select": {"class": "ContinuousLogicalTimeline"},
                    "set": "accent",
                },
                {
                    "select": {"domain": "logical", "within": "score"},
                    "set": {"stroke": "#000080", "fill": "#000080"},
                },
                {
                    "select": {"element": "region", "within": "score"},
                    "set": {"stroke": "#800000", "fill": "#800000"},
                },
                {
                    "select": {"element": "region", "within": "score"},
                    "set": {"stroke": "#008080", "fill": "#008080"},
                },
                {
                    "select": {"element": "child", "within": "score"},
                    "set": {"display": "inline"},
                },
                {
                    "select": {"within": "b"},
                    "set": {"stroke": "#FF8000", "fill": "#FF8000"},
                },
            ],
        },
        "styled__perf.json": {
            "statements": [
                *shared,
                {
                    "select": {
                        "element": "wedge",
                        "domain": "physical",
                        "within": "perf",
                    },
                    "set": violet,
                },
            ],
        },
    }
    styled = {}
    for path in fixture_paths():
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if "graphical" in manifest:
            assert list(manifest) == ["meta", "timeline", "graphical"]
            styled[path.name] = manifest["graphical"]
    assert styled == expected
    assert [len(value["statements"]) for value in expected.values()] == [11, 5]


@pytest.mark.parametrize("accessor", [schema_path, load_schema, fixture_paths])
def test_unknown_version_is_refused(accessor) -> None:
    with pytest.raises(UnsupportedVersionError) as caught:
        accessor("9.9.9")
    assert caught.value.version == "9.9.9"
