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

SCHEMA_ID = "https://timetoalign.github.io/timeskeleton/0.5.0/timeskeleton.schema.json"

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
ID_PATTERN = r"^[^/\u0000-\u001f]+$"

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
    assert SCHEMA_VERSION == "0.5.0"
    assert SUPPORTED_VERSIONS == ("0.5.0",)
    assert SUPPORTED_VERSIONS[-1] == SCHEMA_VERSION


def test_schema_path_names_the_bundled_file() -> None:
    path = schema_path()
    assert path.is_file()
    assert path.name == "timeskeleton-0.5.0.schema.json"
    assert schema_path("0.5.0") == path


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


def test_ids_are_nonempty_without_slashes_or_control_characters() -> None:
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
    assert len(definitions_with_id) == 26
    assert all(
        definition["properties"]["id"]["pattern"] == ID_PATTERN
        for definition in definitions_with_id
    )


def test_regions_and_flow_control_carry_ids() -> None:
    defs = load_schema()["$defs"]
    assert defs["Region"]["required"] == ["id", "name", "start", "end", "meta"]
    assert defs["Region"]["properties"]["name"]["type"] == ["string", "null"]
    assert defs["Break"]["required"] == [
        "id",
        "coordinate",
        "control_type",
        "condition",
        "repeat_count",
        "label",
        "name",
        "meta",
    ]
    assert defs["Jump"]["required"] == [
        "id",
        "from_coordinate",
        "to_coordinate",
        "control_type",
        "condition",
        "repeat_count",
        "target",
        "label",
        "meta",
    ]
    assert defs["Jump"]["properties"]["target"]["type"] == ["string", "null"]
    marker = defs["Marker"]
    assert marker["required"] == ["id", "name", "coordinate"]
    assert list(marker["properties"]) == ["id", "name", "coordinate"]
    assert marker["properties"]["name"]["type"] == ["string", "null"]
    assert marker["properties"]["coordinate"] == {"$ref": "#/$defs/Coordinate"}
    assert defs["FlowControl"]["properties"]["markers"] == {
        "type": "array",
        "items": {"$ref": "#/$defs/Marker"},
    }
    for name in ["Region", "Break", "Jump", "Marker"]:
        assert defs[name]["additionalProperties"] is False


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


def test_fixture_set_contains_exactly_the_0_5_0_manifests() -> None:
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
        "corpus_parangonar_parangonada__score_dlt_1.json",
        "corpus_score_ms3.json",
        "corpus_supra_iiif.json",
        "discrete_graphical.json",
        "discrete_logical.json",
        "discrete_physical.json",
        "flow_control.json",
        "map.json",
        "nested.json",
        "styled__performance.json",
        "styled__score.json",
        "with_region.json",
    ]


def _timeline_structure(timeline: dict) -> tuple:
    flow_control = timeline["flow_control"]
    return (
        timeline["class"],
        timeline["locked"],
        tuple(entry["type"] for entry in timeline["conversion_maps"]),
        len(timeline["regions"]),
        len(flow_control["breaks"]),
        len(flow_control["jumps"]),
        len(flow_control["markers"]),
        tuple(
            _timeline_structure(child["timeline"])
            for child in timeline["children"].values()
        ),
    )


def test_no_two_fixtures_share_a_structure() -> None:
    first_of: dict[tuple, str] = {}
    for path in fixture_paths():
        manifest = json.loads(path.read_text(encoding="utf-8"))
        graphical = manifest.get("graphical")
        structure = (
            _timeline_structure(manifest["timeline"]),
            None if graphical is None else json.dumps(graphical, sort_keys=True),
        )
        assert structure not in first_of, (path.name, first_of.get(structure))
        first_of[structure] = path.name
    assert len(first_of) == 23


def test_the_remaining_parangonar_fixture_is_the_discrete_score() -> None:
    (path,) = [p for p in fixture_paths() if "parangonar" in p.name]
    timeline = json.loads(path.read_text(encoding="utf-8"))["timeline"]
    assert path.name == "corpus_parangonar_parangonada__score_dlt_1.json"
    assert timeline["class"] == "DiscreteLogicalTimeline"
    assert [entry["type"] for entry in timeline["conversion_maps"]] == ["LinearMap"]


_GREY = {"stroke": "#404040", "fill": "#404040"}
_SHARED = [
    {"select": {"element": "label"}, "set": _GREY},
    {"select": {"element": "name"}, "set": _GREY},
    {"select": {"element": "map"}, "set": {"side": "below"}},
    {"select": {"ids": ["a"]}, "set": {"display": "none"}},
]
_STYLED_SCORE = {
    "styles": {
        "accent": {
            "stroke": "#1D4ED8",
            "fill": "#1D4ED8",
            "stroke-width": 4,
            "opacity": 0.8,
        }
    },
    "statements": [
        *_SHARED,
        {"select": {"element": "block"}, "set": {"rx": 4}},
        {
            "select": {"class": "ContinuousLogicalTimeline", "element": "timeline"},
            "set": "accent",
        },
        {
            "select": {"class": "QuartersToTicks"},
            "set": {"stroke": "#7C3AED", "stroke-width": 1.5},
        },
        {
            "select": {"element": "map", "modality": "discrete"},
            "set": {"stroke-dasharray": "4 2"},
        },
        {"select": {"element": "region"}, "set": {"stroke": "#800000"}},
        {"select": {"element": "region"}, "set": {"stroke": "#0F766E"}},
        {
            "select": {"element": "jump", "domain": "logical"},
            "set": {"stroke": "#DB2777", "fill": "#DB2777", "stroke-width": 2},
        },
        {
            "select": {"element": "wedge", "within": "score"},
            "set": {"side": "above", "stroke": "#65A30D", "fill": "#65A30D"},
        },
        {
            "select": {"ids": ["score/end"]},
            "set": {"stroke": "#B45309", "fill": "#B45309"},
        },
        {
            "select": {"element": "child", "within": "score"},
            "set": {"display": "inline"},
        },
        {
            "select": {"element": "child", "within": "b"},
            "set": {"stroke": "#EA580C", "fill": "#EA580C"},
        },
        {
            "select": {"element": "label", "within": "score"},
            "set": {"fill": "#4D7C0F", "font-size": 10},
        },
        {"select": {"ids": ["score/end/label"]}, "set": {"fill": "#A16207"}},
        {"select": {"ids": ["intro/label"]}, "set": {"fill": "#0E7490"}},
        {"select": {"ids": ["da-capo/label"]}, "set": {"fill": "#9D174D"}},
        {
            "select": {"ids": ["score/name"]},
            "set": {
                "fill": "#111827",
                "font-size": 12,
                "content": "Styled score",
                "max-width": 120,
            },
        },
        {"select": {"element": "name", "within": "b"}, "set": {"fill": "#0369A1"}},
    ],
}


def _styled(name: str) -> dict:
    (path,) = [p for p in fixture_paths() if p.name == name]
    return json.loads(path.read_text(encoding="utf-8"))["graphical"]


def test_the_styled_manifests_carry_their_statements() -> None:
    expected = {
        "styled__score.json": _STYLED_SCORE,
        "styled__performance.json": {
            "statements": [
                *_SHARED,
                {
                    "select": {
                        "element": "wedge",
                        "domain": "physical",
                        "within": "performance",
                    },
                    "set": {"stroke": "#7F00FF", "fill": "#7F00FF"},
                },
            ],
        },
    }
    styled = {}
    for path in fixture_paths():
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if "graphical" in manifest:
            assert list(manifest) == ["graphical", "meta", "timeline"]
            styled[path.name] = manifest["graphical"]
    assert styled == expected
    assert [len(value["statements"]) for value in expected.values()] == [21, 5]


# The drawn elements and texts of styled__score: (type, address, timeline it
# belongs to, class, domain, modality, parent address). The map's domain and
# modality are those of its target unit, ticks.
_LOGICAL = ("ContinuousLogicalTimeline", "logical", "continuous")
_SCORE_ELEMENTS = [
    ("timeline", "score", "score", *_LOGICAL, None),
    ("child", "b", "b", *_LOGICAL, "score"),
    ("map", "ticks", "score", "QuartersToTicks", "logical", "discrete", "score"),
    ("region", "intro", "score", *_LOGICAL, "score"),
    ("jump", "da-capo", "score", *_LOGICAL, "score"),
    ("wedge", "score/start", "score", *_LOGICAL, "score"),
    ("wedge", "score/end", "score", *_LOGICAL, "score"),
    ("name", "score/name", "score", *_LOGICAL, "score"),
    ("name", "b/name", "b", *_LOGICAL, "b"),
    ("label", "score/start/label", "score", *_LOGICAL, "score/start"),
    ("label", "score/end/label", "score", *_LOGICAL, "score/end"),
    ("label", "intro/label", "score", *_LOGICAL, "intro"),
    ("label", "da-capo/label", "score", *_LOGICAL, "da-capo"),
]
_ANCESTRY = {"score": ["score"], "b": ["b", "score"]}
_DEPTH = {"score": 1, "b": 2}


def _resolve(graphical: dict, element: tuple, prop: str) -> str:
    """Return the value the manifest's own statements give ``prop``.

    Ranks follow docs/drawing.md section 2.5 within one layer: ids, depth of
    within, class, element, the count of domain and modality, position. An
    inherited property no statement sets is taken from the parent.
    """
    kind, address, owner, cls, domain, modality, parent = element
    ranked = []
    for position, statement in enumerate(graphical["statements"]):
        select = statement["select"]
        declaration = statement["set"]
        if isinstance(declaration, str):
            declaration = graphical["styles"][declaration]
        if prop not in declaration:
            continue
        if any(
            (key == "element" and value != kind)
            or (key == "ids" and address not in value)
            or (key == "class" and value != cls)
            or (key == "domain" and value != domain)
            or (key == "modality" and value != modality)
            or (key == "within" and value not in _ANCESTRY[owner])
            for key, value in select.items()
        ):
            continue
        rank = (
            "ids" in select,
            _DEPTH[select["within"]] if "within" in select else 0,
            "class" in select,
            "element" in select,
            ("domain" in select) + ("modality" in select),
            position,
        )
        ranked.append((rank, declaration[prop]))
    if ranked:
        return max(ranked)[1]
    assert parent is not None, (address, prop)
    (parent_element,) = [e for e in _SCORE_ELEMENTS if e[1] == parent]
    return _resolve(graphical, parent_element, prop)


def test_every_styled_score_item_has_its_own_colour() -> None:
    graphical = _styled("styled__score.json")
    painted = {"name": "fill", "label": "fill", "wedge": "fill"}
    colours = {
        element[1]: _resolve(graphical, element, painted.get(element[0], "stroke"))
        for element in _SCORE_ELEMENTS
    }
    assert colours == {
        "score": "#1D4ED8",
        "b": "#EA580C",
        "ticks": "#7C3AED",
        "intro": "#0F766E",
        "da-capo": "#DB2777",
        "score/start": "#65A30D",
        "score/end": "#B45309",
        "score/name": "#111827",
        "b/name": "#0369A1",
        "score/start/label": "#4D7C0F",
        "score/end/label": "#A16207",
        "intro/label": "#0E7490",
        "da-capo/label": "#9D174D",
    }
    assert len(set(colours.values())) == 13
    for element in _SCORE_ELEMENTS:
        if element[0] in {"timeline", "child", "jump", "wedge"}:
            assert _resolve(graphical, element, "fill") == colours[element[1]]


def test_every_styled_score_item_is_visible() -> None:
    graphical = _styled("styled__score.json")
    declarations = [
        (statement["select"], statement["set"])
        for statement in graphical["statements"]
        if isinstance(statement["set"], dict)
    ] + [(None, style) for style in graphical["styles"].values()]
    for select, declaration in declarations:
        assert declaration.get("stroke-width", 1) > 0
        assert declaration.get("opacity", 1) >= 0.5
        if declaration.get("display") == "none":
            assert select == {"ids": ["a"]}
    content = [
        select for select, declaration in declarations if "content" in declaration
    ]
    assert content == [{"ids": ["score/name"]}]


@pytest.mark.parametrize("accessor", [schema_path, load_schema, fixture_paths])
def test_unknown_version_is_refused(accessor) -> None:
    with pytest.raises(UnsupportedVersionError) as caught:
        accessor("9.9.9")
    assert caught.value.version == "9.9.9"
