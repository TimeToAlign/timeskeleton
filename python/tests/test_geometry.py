from __future__ import annotations

import copy
import json
import xml.etree.ElementTree as ElementTree
from fractions import Fraction

import pytest

from timeskeleton import (
    GEOMETRY_VERSIONS,
    SchemaValidationError,
    UnsupportedVersionError,
    dumps,
    fixture_paths,
    geometry_paths,
    geometry_rejection_paths,
    geometry_schema_path,
    load_geometry_schema,
    load_schema,
    validate_geometry,
)

GEOMETRY_ID = "https://timetoalign.github.io/timeskeleton/0.3.0/geometry.schema.json"
ENVELOPE_SCHEMA_ID = (
    "https://timetoalign.github.io/timeskeleton/0.3.0/timeskeleton.schema.json"
)


def _geometry(path) -> dict:
    return json.loads((path / "geometry.json").read_text(encoding="utf-8"))


def test_geometry_versions_and_schema_identity() -> None:
    assert GEOMETRY_VERSIONS == ("0.3.0",)
    assert geometry_schema_path().name == "geometry-0.3.0.schema.json"
    schema = load_geometry_schema()
    assert schema["$id"] == GEOMETRY_ID
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert (
        schema["properties"]["meta"]["properties"]["schema_version"]["const"] == "0.3.0"
    )
    text = geometry_schema_path().read_text(encoding="utf-8")
    references = {
        reference.split("#")[0]
        for reference in text.split('"$ref": "')[1:]
        for reference in [reference.split('"')[0]]
        if not reference.startswith("#")
    }
    assert references == {ENVELOPE_SCHEMA_ID}
    assert load_schema("0.3.0")["$id"] == ENVELOPE_SCHEMA_ID


def test_the_primitive_union_lists_eight_kinds() -> None:
    primitive = load_geometry_schema()["$defs"]["Primitive"]
    kinds = [
        branch["if"]["properties"]["kind"]["const"] for branch in primitive["allOf"]
    ]
    assert kinds == [
        "timeline",
        "child",
        "map",
        "region",
        "break",
        "jump",
        "wedge",
        "label",
    ]
    assert [branch["then"]["$ref"] for branch in primitive["allOf"]] == [
        f"#/$defs/{kind.capitalize()}Primitive" for kind in kinds
    ]


@pytest.mark.parametrize("accessor", [geometry_schema_path, geometry_paths])
def test_unknown_geometry_version_is_refused(accessor) -> None:
    with pytest.raises(UnsupportedVersionError):
        accessor("0.2.1")


def test_one_specimen_per_envelope_fixture() -> None:
    assert [path.name for path in geometry_paths()] == [
        path.stem for path in fixture_paths("0.3.0")
    ]
    assert len(geometry_paths()) == 20
    for path in geometry_paths():
        assert sorted(item.name for item in path.iterdir()) == [
            "figure.svg",
            "figure.tex",
            "geometry.json",
        ]


@pytest.mark.parametrize("path", geometry_paths(), ids=lambda path: path.name)
def test_every_geometry_fixture_validates_in_standard_text(path) -> None:
    text = (path / "geometry.json").read_text(encoding="utf-8")
    geometry = json.loads(text)
    validate_geometry(geometry)
    assert dumps(geometry) == text


def _exact(value) -> Fraction:
    return Fraction(*value) if isinstance(value, list) else Fraction(value)


@pytest.mark.parametrize("path", geometry_paths(), ids=lambda path: path.name)
def test_every_frame_is_its_name_column_then_its_plot_area(path) -> None:
    for block in _geometry(path)["blocks"]:
        frame = block["frame"]
        names, plot = frame["names"], frame["plot"]
        assert _exact(names["offset"]) == 0
        assert plot["offset"] == names["length"]
        length = _exact(frame["length"])
        if isinstance(frame["length"], float):
            assert frame["length"] == names["length"] + plot["length"]
        else:
            assert length == _exact(names["length"]) + _exact(plot["length"])
        assert block["placement"]["target_unit"] == "number"


@pytest.mark.parametrize("path", geometry_paths(), ids=lambda path: path.name)
def test_every_svg_fixture_parses(path) -> None:
    root = ElementTree.parse(path / "figure.svg").getroot()
    assert root.tag == "{http://www.w3.org/2000/svg}svg"


@pytest.mark.parametrize("path", geometry_rejection_paths(), ids=lambda path: path.stem)
def test_shared_geometry_rejection_is_rejected_at_its_path(path) -> None:
    case = json.loads(path.read_text(encoding="utf-8"))
    with pytest.raises(SchemaValidationError) as caught:
        validate_geometry(case["geometry"])
    assert caught.value.path == tuple(case["path"])


def test_the_geometry_rejections_number_six() -> None:
    assert [path.stem for path in geometry_rejection_paths()] == [
        "frame_plot_offset_string",
        "frame_unknown_member",
        "label_anchor_unknown",
        "primitive_unknown_member",
        "rows_max_negative",
        "wedge_base_float",
    ]


def test_a_primitive_of_an_unknown_kind_is_accepted() -> None:
    (bare,) = [path for path in geometry_paths() if path.name == "bare"]
    geometry = copy.deepcopy(_geometry(bare))
    geometry["blocks"][0]["primitives"].append({"kind": "strip", "values": [1, 2]})
    validate_geometry(geometry)
