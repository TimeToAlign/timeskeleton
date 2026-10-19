from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

from timeskeleton import DEFAULTS, SCHEMA_VERSION, load_schema, schema_path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
UNKNOWN = {"x-unknown-key": True}

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
        "MemberOrder",
    ):
        assert gone not in defs


def test_objects_are_open_and_mark_their_unknown_keys() -> None:
    defs = _defs()
    nodes = list(_nodes(load_schema()))
    assert not [node for node, _ in nodes if node.get("additionalProperties") is False]
    marked = []
    for node, inside in nodes:
        is_object = node.get("type") == "object" and "properties" in node
        if inside:
            assert "unevaluatedProperties" not in node
        elif is_object:
            assert node["unevaluatedProperties"] == UNKNOWN
            marked.append(node)
        else:
            assert "unevaluatedProperties" not in node
    for name in ["TimeSkeleton", "Timeline", "Group", "Graphical", *_map_types()]:
        assert defs[name] in marked


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
