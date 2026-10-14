from __future__ import annotations

import copy
import re
from typing import Any

import pytest

from timeskeleton import (
    FILE_KINDS,
    SCHEMA_DOCUMENTS,
    SchemaValidationError,
    file_kind,
    load_schema,
    schema_documents,
    schema_path,
    validate,
)

BASE = "https://timetoalign.github.io/timeskeleton/0.7.0/"
ID_PATTERN = r"^[^/\u0000-\u001f]+$"
ID = "core.schema.json#/$defs/Id"
CORE = [
    "Coordinate",
    "CoordinateNonnegative",
    "Declaration",
    "ElementType",
    "Fraction",
    "FractionNonnegative",
    "FractionPositive",
    "Graphical",
    "Id",
    "Meta",
    "Number",
    "NumberNonnegative",
    "NumberPositive",
    "NumberType",
    "Paint",
    "Selector",
    "Statement",
    "TimeUnit",
]
REFERENCE = re.compile(
    r"^(?:(core|timeline|group|bundle)\.schema\.json)?#/\$defs/(\w+)"
    r"(?:/properties/(\w+))?$"
)
GRAPHICAL_MEMBERS = {
    "styles": {"$ref": "core.schema.json#/$defs/Graphical/properties/styles"},
    "statements": {"$ref": "core.schema.json#/$defs/Graphical/properties/statements"},
}


def _references(value: Any) -> list[str]:
    if isinstance(value, dict):
        own = [value["$ref"]] if "$ref" in value else []
        return own + [ref for item in value.values() for ref in _references(item)]
    if isinstance(value, list):
        return [ref for item in value for ref in _references(item)]
    return []


def test_the_version_has_four_documents() -> None:
    assert SCHEMA_DOCUMENTS == ("core", "timeline", "group", "bundle")
    assert schema_documents("0.7.0") == SCHEMA_DOCUMENTS
    assert schema_documents() == SCHEMA_DOCUMENTS
    assert schema_path() == schema_path("0.7.0", "timeline")
    for name in SCHEMA_DOCUMENTS:
        path = schema_path("0.7.0", name)
        assert path.is_file()
        assert path.parts[-3:] == ("schema", "0.7.0", f"{name}.schema.json")
        schema = load_schema("0.7.0", name)
        assert schema["$id"] == f"{BASE}{name}.schema.json"
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    with pytest.raises(ValueError, match="schema 0.7.0 has no 'claims' document"):
        schema_path("0.7.0", "claims")


def test_every_reference_is_local_or_relative_and_resolves() -> None:
    definitions = {
        name: load_schema("0.7.0", name)["$defs"] for name in SCHEMA_DOCUMENTS
    }
    for name in SCHEMA_DOCUMENTS:
        for reference in _references(load_schema("0.7.0", name)):
            match = REFERENCE.match(reference)
            assert match is not None, (name, reference)
            target = match.group(1) or name
            assert match.group(2) in definitions[target], (name, reference)
            if match.group(3) is not None:
                members = definitions[target][match.group(2)]["properties"]
                assert match.group(3) in members, (name, reference)


def test_definition_names_are_unique_across_the_documents() -> None:
    names = [
        definition
        for name in SCHEMA_DOCUMENTS
        for definition in load_schema("0.7.0", name)["$defs"]
    ]
    assert len(names) == len(set(names))
    assert sorted(load_schema("0.7.0", "core")["$defs"]) == CORE


def _inline(value: Any) -> Any:
    """Undo the move into core: local references, the id rule written inline."""
    if isinstance(value, list):
        return [_inline(item) for item in value]
    if not isinstance(value, dict):
        return value
    if value.get("$ref") == ID:
        rest = {key: item for key, item in value.items() if key != "$ref"}
        return {"type": "string", "pattern": ID_PATTERN, **rest}
    result = {}
    for key, item in value.items():
        if key == "propertyNames" and item == {"$ref": ID}:
            # A property name is a string, so the key rule needs no type.
            result[key] = {"pattern": ID_PATTERN}
        elif key == "$ref":
            result[key] = item.replace("core.schema.json#", "#")
        else:
            result[key] = _inline(item)
    return result


def test_the_timeline_definitions_are_those_of_0_6_0_moved() -> None:
    old = load_schema("0.6.0")
    core = load_schema("0.7.0", "core")["$defs"]
    timeline = load_schema("0.7.0", "timeline")
    moved = {
        name: _inline(definition)
        for name, definition in {**core, **timeline["$defs"]}.items()
        if name not in ("Id", "Meta")
    }
    manifest = moved["TimelineManifest"]
    del manifest["properties"]["is_segment_line"]
    manifest["required"].remove("is_segment_line")
    element_type = moved["ElementType"]
    assert element_type["enum"][-4:] == ["boundary", "ancestor", "group", "card"]
    del element_type["enum"][-4:]
    element_type["description"] = old["$defs"]["ElementType"]["description"]
    del moved["Selector"]["properties"]["inside"]
    del moved["Declaration"]["properties"]["shadow"]
    assert moved == old["$defs"]
    assert timeline["properties"] == {
        "meta": {"$ref": "core.schema.json#/$defs/Meta"},
        "timeline": old["properties"]["timeline"],
        "graphical": {"$ref": "core.schema.json#/$defs/Graphical"},
    }
    assert (
        _inline(timeline["properties"]["graphical"]) == old["properties"]["graphical"]
    )
    assert (old["title"], timeline["title"]) == (
        "TimeSkeleton manifest",
        "TimeSkeleton timeline file",
    )
    for member in ("type", "required", "additionalProperties"):
        assert timeline[member] == old[member]
    meta = copy.deepcopy(old["properties"]["meta"])
    meta["description"] = "File metadata."
    version = meta["properties"]["schema_version"]
    version["const"] = "0.7.0"
    version["description"] = "The timeskeleton release this file conforms to."
    meta["properties"]["generator"]["description"] = (
        "Free-form identification of the software that wrote the file."
    )
    assert core["Meta"] == meta
    assert core["Id"]["type"] == "string"
    assert core["Id"]["pattern"] == ID_PATTERN


def test_thirty_two_references_name_the_id_rule() -> None:
    counts = {
        name: _references(load_schema("0.7.0", name)).count(ID)
        for name in SCHEMA_DOCUMENTS
    }
    assert counts == {"core": 0, "timeline": 27, "group": 3, "bundle": 2}


def test_the_group_document() -> None:
    schema = load_schema("0.7.0", "group")
    assert schema["title"] == "TimeSkeleton group file"
    assert list(schema["properties"]) == ["meta", "timelines", "group", "graphical"]
    assert schema["required"] == ["meta", "timelines", "group"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["meta"] == {"$ref": "core.schema.json#/$defs/Meta"}
    assert schema["properties"]["timelines"]["items"] == {
        "$ref": "timeline.schema.json#/$defs/TimelineManifest"
    }
    assert schema["properties"]["group"] == {"$ref": "#/$defs/Group"}
    assert schema["properties"]["graphical"] == {"$ref": "#/$defs/GroupGraphical"}
    group = schema["$defs"]["Group"]
    assert list(group["properties"]) == ["id", "name", "meta", "members"]
    assert group["required"] == ["id", "name", "meta", "members"]
    assert group["additionalProperties"] is False
    assert group["properties"]["name"]["type"] == ["string", "null"]
    assert group["properties"]["meta"]["type"] == "object"
    members = group["properties"]["members"]
    assert (members["type"], members["items"], members["uniqueItems"]) == (
        "array",
        {"$ref": ID},
        True,
    )
    order = schema["$defs"]["MemberOrder"]
    assert (order["type"], order["items"], order["uniqueItems"]) == (
        "array",
        {"$ref": ID},
        True,
    )
    graphical = schema["$defs"]["GroupGraphical"]
    assert list(graphical["properties"]) == ["order", "styles", "statements"]
    assert graphical["properties"]["order"]["$ref"] == "#/$defs/MemberOrder"
    for member, reference in GRAPHICAL_MEMBERS.items():
        assert graphical["properties"][member] == reference
    assert graphical["additionalProperties"] is False
    assert "required" not in graphical


def test_the_bundle_document() -> None:
    schema = load_schema("0.7.0", "bundle")
    assert schema["title"] == "TimeSkeleton bundle file"
    assert list(schema["properties"]) == ["meta", "timelines", "bundle", "graphical"]
    assert schema["required"] == ["meta", "timelines", "bundle"]
    assert schema["additionalProperties"] is False
    assert schema["properties"]["timelines"]["items"] == {
        "$ref": "timeline.schema.json#/$defs/TimelineManifest"
    }
    bundle = schema["$defs"]["Bundle"]
    keys = ["id", "name", "meta", "support_policy", "groups"]
    assert list(bundle["properties"]) == keys
    assert bundle["required"] == keys
    assert bundle["additionalProperties"] is False
    assert bundle["properties"]["support_policy"]["enum"] == [
        "omit",
        "clamp",
        "extrapolate",
    ]
    assert bundle["properties"]["groups"]["items"] == {
        "$ref": "group.schema.json#/$defs/Group"
    }
    order = schema["$defs"]["BundleGraphical"]["properties"]["order"]
    assert order["type"] == "object"
    assert order["propertyNames"] == {"$ref": ID}
    assert order["additionalProperties"] == {
        "$ref": "group.schema.json#/$defs/MemberOrder"
    }
    graphical = schema["$defs"]["BundleGraphical"]
    assert list(graphical["properties"]) == ["order", "styles", "statements"]
    for member, reference in GRAPHICAL_MEMBERS.items():
        assert graphical["properties"][member] == reference
    assert graphical["additionalProperties"] is False
    assert "required" not in graphical


@pytest.mark.parametrize(
    ("members", "kind"),
    [
        (["timeline"], "timeline"),
        (["timelines", "group"], "group"),
        (["timelines", "bundle"], "bundle"),
        (["timelines"], None),
        (["timeline", "group"], None),
        (["group", "bundle"], None),
    ],
)
def test_the_file_kind_is_the_one_kind_member(members: list[str], kind) -> None:
    assert FILE_KINDS == ("timeline", "group", "bundle")
    assert file_kind({"meta": {}, **dict.fromkeys(members, {})}) == kind


@pytest.mark.parametrize("value", [[], "group", None, 5])
def test_a_value_that_is_no_object_has_no_kind(value) -> None:
    assert file_kind(value) is None


def test_the_test_documents_validate(group_document, bundle_document) -> None:
    validate(group_document)
    validate(bundle_document)


@pytest.mark.parametrize(
    ("members", "found"),
    [([], "none"), (["timeline", "group"], "'timeline', 'group'")],
)
def test_a_0_7_0_value_holds_exactly_one_kind(
    members: list[str], found: str, group_document
) -> None:
    value: dict[str, Any] = {"meta": {"schema_version": "0.7.0"}}
    for member in members:
        value[member] = copy.deepcopy(
            group_document[member] if member == "group" else {}
        )
    with pytest.raises(SchemaValidationError) as caught:
        validate(value)
    assert caught.value.path == ()
    assert caught.value.message == (
        f"exactly one of 'timeline', 'group' or 'bundle' is required; found {found}"
    )


def test_an_unknown_version_is_rejected_at_its_declaration(group_document) -> None:
    group_document["meta"]["schema_version"] = "9.9.9"
    with pytest.raises(SchemaValidationError) as caught:
        validate(group_document)
    assert caught.value.path == ("meta", "schema_version")
    with pytest.raises(SchemaValidationError) as caught:
        validate({"meta": {"schema_version": "9.9.9"}})
    assert caught.value.path == ("meta", "schema_version")


def test_0_6_0_knows_timeline_files_only(group_document) -> None:
    group_document["meta"]["schema_version"] = "0.6.0"
    del group_document["graphical"]
    with pytest.raises(SchemaValidationError) as caught:
        validate(group_document)
    assert caught.value.path == ()
    assert not caught.value.message.startswith("exactly one of")


def test_the_bundle_document_checks_a_bundle(group_document, bundle_document) -> None:
    group_document["bundle"] = bundle_document["bundle"]
    del group_document["group"], group_document["graphical"]
    with pytest.raises(SchemaValidationError) as caught:
        validate(group_document)
    assert caught.value.path == ("bundle", "groups", 0, "members", 0)
    assert caught.value.message == "'performance' names no timeline of this file"
