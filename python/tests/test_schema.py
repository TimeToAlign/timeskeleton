from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from timeskeleton import DEFAULTS, SCHEMA_VERSION, load_schema, schema_path
from timeskeleton.validate import UNIT_NUMBER_TYPES

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

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


def _map_types() -> list[str]:
    """The conversion map types: the definitions ``ConversionMap`` chooses between."""
    return [
        branch["$ref"].removeprefix("#/$defs/")
        for branch in _defs()["ConversionMap"]["oneOf"]
    ]


def _target(node: dict) -> dict:
    """The definition a node refers to, else the node."""
    if "$ref" in node:
        return _defs()[node["$ref"].removeprefix("#/$defs/")]
    return node


def _custom_keys(node: Any) -> list[str]:
    """Every key of the document that begins with ``x-``."""
    if isinstance(node, list):
        return [key for item in node for key in _custom_keys(item)]
    if not isinstance(node, dict):
        return []
    found = [key for key in node if key.startswith("x-")]
    return found + [key for value in node.values() for key in _custom_keys(value)]


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
        "TimelineClass",
        "TimelineManifest",
        "Bundle",
        "GroupGraphical",
        "BundleGraphical",
        "CoordinateNonnegative",
        "MemberOrder",
    ):
        assert gone not in defs


def test_the_unit_table_states_the_default_number_types() -> None:
    unit = _defs()["TimeUnit"]
    assert unit["type"] == "string"
    assert "enum" not in unit
    assert [entry["const"] for entry in unit["oneOf"]] == list(UNIT_NUMBER_TYPES)
    pattern = re.compile(
        r"^(Logical|Physical|Graphical), (continuous|discrete); "
        r"default number type (int|float|fraction)\.$"
    )
    for entry in unit["oneOf"]:
        assert sorted(entry) == ["const", "description"]
        match = pattern.match(entry["description"])
        assert match is not None, entry["const"]
        assert match[3] == UNIT_NUMBER_TYPES[entry["const"]], entry["const"]


def test_repeated_shapes_are_shared_definitions() -> None:
    defs = _defs()
    assert defs["Name"] == {
        "type": ["string", "null"],
        "description": "Human-readable name, or null when none was given.",
        "default": None,
    }
    assert defs["Meta"] == {
        "type": "object",
        "additionalProperties": True,
        "description": "Free-form metadata.",
        "default": {},
    }
    names = [
        defs[owner]["properties"]["name"]
        for owner in ("TimeSkeleton", "Timeline", "Group", "Region", "Break", "Marker")
    ] + [defs["MapBase"]["properties"]["name"]]
    metas = [
        defs[owner]["properties"]["meta"]
        for owner in ("TimeSkeleton", "Timeline", "Group", "Region", "Break", "Jump")
    ]
    for node in names:
        assert node["$ref"] == "#/$defs/Name"
    for node in metas:
        assert node["$ref"] == "#/$defs/Meta"
    for node, _ in _nodes(load_schema()):
        properties = node.get("properties", {})
        if "meta" in properties:
            assert properties["meta"]["$ref"] == "#/$defs/Meta"
        if properties.get("name", {}).get("type") == ["string", "null"]:
            raise AssertionError(f"an inline name: {properties['name']}")


def test_every_conversion_map_extends_the_map_base() -> None:
    defs = _defs()
    base = defs["MapBase"]
    assert list(base["properties"]) == [
        "type",
        "id",
        "name",
        "source_unit",
        "target_unit",
    ]
    assert base["required"] == ["type", "id", "source_unit", "target_unit"]
    for name in _map_types():
        definition = defs[name]
        assert definition["type"] == "object"
        assert definition["allOf"] == [{"$ref": "#/$defs/MapBase"}]
        own = set(definition["properties"]) & set(base["properties"])
        assert own == {"type"}, name
        assert definition["properties"]["type"] == {"const": name}
        assert "type" in definition["required"]
        assert not set(definition["required"]) & {"id", "source_unit", "target_unit"}


def test_references_are_ids_and_addresses() -> None:
    defs = _defs()
    selector = defs["Selector"]["properties"]
    assert selector["within"]["$ref"] == "#/$defs/Id"
    assert selector["ids"]["items"] == {"$ref": "#/$defs/Address"}
    assert defs["Jump"]["properties"]["target"]["anyOf"] == [
        {"$ref": "#/$defs/Id"},
        {"type": "null"},
    ]
    for owner, key in (
        ("InterpolationMap", "source_id"),
        ("InterpolationMap", "target_id"),
        ("MetricalPositionMap", "beat_map_id"),
    ):
        assert defs[owner]["properties"][key]["$ref"] == "#/$defs/Id"
    address = Draft202012Validator({"$ref": "#/$defs/Address", "$defs": defs})
    for accepted in ("score", "score/regions_1", "score/region_1/label", "a b/c"):
        assert address.is_valid(accepted), accepted
    for refused in ("", "/score", "score/", "score//label", "score/a\tb"):
        assert not address.is_valid(refused), refused


def test_objects_are_open_without_a_custom_keyword() -> None:
    defs = _defs()
    nodes = list(_nodes(load_schema()))
    assert not [node for node, _ in nodes if node.get("additionalProperties") is False]
    assert not [node for node, _ in nodes if "unevaluatedProperties" in node]
    assert not _custom_keys(load_schema())
    for name in ["Meta"]:
        assert defs[name]["additionalProperties"] is True
        assert "properties" not in defs[name]
    hierarchy = defs["Timeline"]["properties"]["metric_hierarchy"]
    assert hierarchy["additionalProperties"] is True
    assert "properties" not in hierarchy


def test_every_object_declares_what_its_branches_declare() -> None:
    for node, inside in _nodes(load_schema()):
        if inside or node.get("type") != "object" or "properties" not in node:
            continue
        declared = set(node["properties"])
        for entry in node.get("allOf", []):
            declared |= set(_target(entry)["properties"])
        assert "patternProperties" not in node
        for key in ("oneOf", "anyOf"):
            for branch in node.get(key, []):
                assert set(branch.get("properties", {})) <= declared
        for key in ("if", "then", "else"):
            assert set(node.get(key, {}).get("properties", {})) <= declared


def test_every_discriminated_union_tags_each_branch_with_a_distinct_constant() -> None:
    unions = [node for node, _ in _nodes(load_schema()) if "discriminator" in node]
    assert sorted(node["discriminator"]["propertyName"] for node in unions) == [
        "number_type",
        "type",
    ]
    for node in unions:
        key = node["discriminator"]["propertyName"]
        tags = [_target(branch)["properties"][key]["const"] for branch in node["oneOf"]]
        assert all(isinstance(tag, str) for tag in tags)
        assert len(set(tags)) == len(tags)
        for branch in node["oneOf"]:
            assert key in _target(branch).get("required", node.get("required", []))


def _defaults(definition: dict) -> dict[str, Any]:
    """The defaults a definition declares, through references and its base."""
    members = dict(definition.get("properties", {}))
    for entry in definition.get("allOf", []):
        members |= _target(entry)["properties"]
    return {
        key: (member if "default" in member else _target(member))["default"]
        for key, member in members.items()
        if "default" in member or "default" in _target(member)
    }


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
        "conversion_map": _map_types(),
        "group": ["Group"],
        "graphical": ["Graphical"],
    }
    assert sorted(kinds) == sorted(DEFAULTS)
    covered = {"MapBase"}
    for kind, names in kinds.items():
        for name in names:
            covered.add(name)
            assert _defaults(defs[name]) == DEFAULTS[kind], name
    for name, definition in defs.items():
        if name not in covered:
            assert _defaults(definition) == {}, name
    assert "default" not in defs["Timeline"]["properties"]["number_type"]
