from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from timeskeleton import DEFAULTS, SCHEMA_VERSION, load_schema, schema_path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
UNKNOWN = {"x-unknown-key": True}

TIMELINE_CLASSES = [
    "ContinuousLogicalTimeline",
    "ContinuousPhysicalTimeline",
    "ContinuousGraphicalTimeline",
    "DiscreteLogicalTimeline",
    "DiscretePhysicalTimeline",
    "DiscreteGraphicalTimeline",
]
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
PUBLIC = [
    "TimeSkeleton",
    "Timeline",
    "Group",
    "Graphical",
    "ConversionMap",
    "Coordinate",
    "Number",
    "Fraction",
    "TimeUnit",
    "NumberType",
    "Id",
    "MeasureMapRow",
]


def _defs() -> dict[str, Any]:
    return load_schema()["$defs"]


def _nodes(node: Any, inside: bool = False) -> Iterator[tuple[dict, bool]]:
    """Yield every schema node and whether it lies in a branch or an arm."""
    if isinstance(node, list):
        for item in node:
            yield from _nodes(item, inside)
    elif isinstance(node, dict):
        yield node, inside
        for key, value in node.items():
            if key in ("oneOf", "anyOf", "if", "then", "else"):
                yield from _nodes(value, True)
            elif key in ("properties", "$defs"):
                for child in value.values():
                    yield from _nodes(child, False)
            elif key not in ("default", "const", "enum"):
                yield from _nodes(value, inside)


def test_one_document_with_one_root() -> None:
    schema = load_schema()
    assert SCHEMA_VERSION == "0.7.0"
    assert (
        schema_path()
        == REPOSITORY_ROOT / "schema" / "0.7.0" / "timeskeleton.schema.json"
    )
    assert sorted(p.name for p in (REPOSITORY_ROOT / "schema").iterdir()) == ["0.7.0"]
    assert sorted(p.name for p in (REPOSITORY_ROOT / "schema" / "0.7.0").iterdir()) == [
        "timeskeleton.schema.json"
    ]
    assert schema["$id"] == (
        "https://timetoalign.github.io/timeskeleton/0.7.0/timeskeleton.schema.json"
    )
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$ref"] == "#/$defs/TimeSkeleton"


def test_references_are_local_and_resolve_without_anchors() -> None:
    defs = _defs()
    references = [node["$ref"] for node, _ in _nodes(load_schema()) if "$ref" in node]
    assert references
    for reference in references:
        assert reference.startswith("#/$defs/")
        assert reference.removeprefix("#/$defs/") in defs
    assert not [node for node, _ in _nodes(load_schema()) if "$anchor" in node]


def test_the_public_definitions() -> None:
    defs = _defs()
    assert set(PUBLIC) <= set(defs)
    for gone in (
        "Meta",
        "TimelineClass",
        "TimelineManifest",
        "Bundle",
        "GroupGraphical",
        "BundleGraphical",
        "CoordinateNonnegative",
    ):
        assert gone not in defs


def test_the_manifest() -> None:
    manifest = _defs()["TimeSkeleton"]
    assert list(manifest["properties"]) == [
        "$schema",
        "timeskeleton",
        "id",
        "name",
        "meta",
        "timelines",
        "groups",
        "graphical",
    ]
    assert manifest["required"] == ["timeskeleton", "timelines"]
    assert manifest["properties"]["timeskeleton"]["const"] == "0.7.0"
    assert manifest["properties"]["$schema"]["type"] == "string"
    assert manifest["properties"]["timelines"]["items"] == {"$ref": "#/$defs/Timeline"}


def test_the_timeline() -> None:
    timeline = _defs()["Timeline"]
    properties = timeline["properties"]
    assert list(properties) == [
        "id",
        "name",
        "unit",
        "number_type",
        "length",
        "offset",
        "locked",
        "is_segment_line",
        "meta",
        "children",
        "conversion_maps",
        "regions",
        "flow_control",
        "measure_map",
        "metric_hierarchy",
    ]
    assert timeline["required"] == ["id", "unit", "length"]
    assert properties["length"]["anyOf"] == [
        {"$ref": "#/$defs/NumberNonnegative"},
        {"type": "null"},
    ]
    assert properties["offset"]["$ref"] == "#/$defs/Number"
    assert properties["children"]["items"] == {
        "$ref": "#/$defs/Timeline",
        "required": ["offset"],
    }
    assert (
        properties["locked"]["description"] == "Whether the timeline's length is fixed."
    )
    defs = _defs()
    for definition, keys in (
        ("Region", ["start", "end"]),
        ("Break", ["coordinate"]),
        ("Jump", ["from_coordinate", "to_coordinate"]),
        ("Marker", ["coordinate"]),
    ):
        for key in keys:
            assert defs[definition]["properties"][key] == {"$ref": "#/$defs/Number"}


def test_groups_and_the_graphical_block() -> None:
    defs = _defs()
    assert list(defs["Group"]["properties"]) == ["id", "name", "meta", "members"]
    assert defs["Group"]["required"] == ["id", "members"]
    graphical = defs["Graphical"]
    assert list(graphical["properties"]) == ["styles", "statements", "order"]
    assert "required" not in graphical
    order = graphical["properties"]["order"]
    assert order["propertyNames"] == {"$ref": "#/$defs/Id"}
    assert order["additionalProperties"] == {"$ref": "#/$defs/MemberOrder"}
    assert not [node for node, _ in _nodes(load_schema()) if "support_policy" in node]
    for name in CONVERSION_MAP_TYPES:
        definition = defs[name]
        assert definition["properties"]["type"]["const"] == name
        assert "name" in definition["properties"]
        assert "name" not in definition["required"]
        assert set(definition["required"]) == set(definition["properties"]) - {"name"}


def test_objects_are_open_and_mark_their_unknown_keys() -> None:
    nodes = list(_nodes(load_schema()))
    assert not [node for node, _ in nodes if node.get("additionalProperties") is False]
    marked = 0
    for node, inside in nodes:
        is_object = node.get("type") == "object" and "properties" in node
        if inside:
            assert "unevaluatedProperties" not in node
        elif is_object:
            assert node["unevaluatedProperties"] == UNKNOWN
            marked += 1
        else:
            assert "unevaluatedProperties" not in node
    assert marked == len(CONVERSION_MAP_TYPES) + 14


def test_free_objects_say_so() -> None:
    defs = _defs()
    free = [
        defs["TimeSkeleton"]["properties"]["meta"],
        defs["Timeline"]["properties"]["meta"],
        defs["Timeline"]["properties"]["metric_hierarchy"],
        defs["Region"]["properties"]["meta"],
        defs["Break"]["properties"]["meta"],
        defs["Jump"]["properties"]["meta"],
        defs["Group"]["properties"]["meta"],
    ]
    for node in free:
        assert node["additionalProperties"] is True
        assert "properties" not in node


def test_every_marked_object_declares_what_its_branches_declare() -> None:
    for node, inside in _nodes(load_schema()):
        if inside or "unevaluatedProperties" not in node:
            continue
        declared = set(node["properties"])
        assert "patternProperties" not in node
        for key in ("oneOf", "anyOf"):
            for branch in node.get(key, []):
                assert set(branch.get("properties", {})) <= declared
        for key in ("if", "then", "else"):
            assert set(node.get(key, {}).get("properties", {})) <= declared


def test_the_defaults_are_the_table() -> None:
    defs = _defs()
    kinds = {
        "manifest": ["TimeSkeleton"],
        "timeline": ["Timeline"],
        "flow_control": ["FlowControl"],
        "region": ["Region"],
        "break": ["Break"],
        "jump": ["Jump"],
        "marker": ["Marker"],
        "conversion_map": CONVERSION_MAP_TYPES,
        "group": ["Group"],
        "graphical": ["Graphical"],
    }
    assert sorted(kinds) == sorted(DEFAULTS)
    covered = set()
    for kind, names in kinds.items():
        for name in names:
            covered.add(name)
            declared = {
                key: member["default"]
                for key, member in defs[name]["properties"].items()
                if "default" in member
            }
            assert declared == DEFAULTS[kind], name
    for name, definition in defs.items():
        if name not in covered:
            assert not any(
                "default" in m for m in definition.get("properties", {}).values()
            )
    assert "default" not in defs["Timeline"]["properties"]["number_type"]


def test_the_vocabulary() -> None:
    defs = _defs()
    assert defs["TimeUnit"]["enum"] == TIME_UNITS
    assert defs["NumberType"]["enum"] == ["int", "float", "fraction"]
    assert defs["Id"]["pattern"] == r"^[^/\u0000-\u001f]+$"
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
        "boundary",
        "ancestor",
        "group",
        "card",
    ]
    selector = defs["Selector"]["properties"]
    assert list(selector) == [
        "element",
        "ids",
        "domain",
        "modality",
        "class",
        "within",
        "inside",
    ]
    assert selector["class"]["enum"] == TIMELINE_CLASSES + CONVERSION_MAP_TYPES
    assert selector["ids"]["minItems"] == 1
    assert selector["ids"]["uniqueItems"] is True
    assert selector["domain"]["enum"] == ["graphical", "logical", "physical"]
    assert selector["modality"]["enum"] == ["continuous", "discrete"]
    assert defs["Paint"]["pattern"] == "^(#[0-9A-F]{6}|none)$"
    members = defs["Declaration"]["properties"]
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
        "shadow": {"$ref": "#/$defs/Paint"},
    }
