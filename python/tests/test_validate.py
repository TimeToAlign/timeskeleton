from __future__ import annotations

import json

import pytest

from timeskeleton import (
    SUPPORTED_VERSIONS,
    SchemaValidationError,
    declared_version,
    dumps,
    fixture_paths,
    json_pointer,
    rejection_paths,
    validate,
)


@pytest.mark.parametrize("version", SUPPORTED_VERSIONS)
def test_every_fixture_validates(version: str) -> None:
    paths = fixture_paths(version)
    assert paths
    for path in paths:
        validate(json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("path", rejection_paths(), ids=lambda path: path.stem)
def test_shared_rejection_is_rejected_at_its_path(path) -> None:
    case = json.loads(path.read_text(encoding="utf-8"))
    with pytest.raises(SchemaValidationError) as caught:
        validate(case["manifest"])
    assert caught.value.path == tuple(case["path"])


def test_every_0_4_0_rejection_declares_0_4_0_except_two() -> None:
    exempt = {"meta_schema_version_unknown", "root_missing_meta"}
    declaring = set()
    for path in rejection_paths("0.4.0"):
        manifest = json.loads(path.read_text(encoding="utf-8"))["manifest"]
        if path.stem in exempt:
            assert declared_version(manifest) != "0.4.0"
        else:
            assert declared_version(manifest) == "0.4.0", path.stem
            declaring.add(path.stem)
    assert len(declaring) == 48
    assert (
        declared_version(
            json.loads(
                next(
                    path
                    for path in rejection_paths("0.4.0")
                    if path.stem == "meta_schema_version_unknown"
                ).read_text(encoding="utf-8")
            )["manifest"]
        )
        == "9.9.9"
    )


def test_error_renders_as_json_pointer() -> None:
    case = json.loads(rejection_paths()[0].read_text(encoding="utf-8"))
    with pytest.raises(SchemaValidationError) as caught:
        validate(case["manifest"])
    assert str(caught.value).startswith(f"{json_pointer(caught.value.path)}: ")


def test_json_pointer_rendering() -> None:
    assert json_pointer(()) == "#"
    assert json_pointer(("a/b", "c~d", 0)) == "#/a~1b/c~0d/0"


@pytest.mark.parametrize("value", [9007199254740993, 9223372036854775807])
def test_integer_boundaries_validate_and_preserve(value: int, load_fixture) -> None:
    manifest = load_fixture("discrete_logical")
    manifest["timeline"]["length"]["value"] = value
    validate(manifest)
    assert json.loads(dumps(manifest))["timeline"]["length"]["value"] == value


@pytest.mark.parametrize(
    "declaration",
    [
        {
            "stroke-width": 0,
            "stroke-dasharray": "none",
            "opacity": 0,
            "font-size": 0.1,
            "rx": 0,
            "content": "row\tname",
            "max-width": "none",
        },
        {
            "stroke-dasharray": "0 1.5 2",
            "opacity": 1,
            "max-width": 1,
        },
    ],
)
def test_graphical_property_bounds_accept_exact_valid_values(
    declaration, load_fixture
) -> None:
    manifest = load_fixture("bare")
    manifest["graphical"] = {"styles": {"valid": declaration}}
    validate(manifest)


@pytest.mark.parametrize(
    ("property_name", "value"),
    [
        ("stroke-width", -0.1),
        ("stroke-dasharray", "3,3"),
        ("opacity", -0.1),
        ("opacity", 1.1),
        ("font-size", 0),
        ("rx", -0.1),
        ("content", 5),
        ("max-width", 0),
    ],
)
def test_graphical_property_bounds_reject_at_the_property(
    property_name, value, load_fixture
) -> None:
    manifest = load_fixture("bare")
    manifest["graphical"] = {"styles": {"invalid": {property_name: value}}}
    with pytest.raises(SchemaValidationError) as caught:
        validate(manifest)
    assert caught.value.path == ("graphical", "styles", "invalid", property_name)


def test_names_remain_unrestricted(load_fixture) -> None:
    manifest = load_fixture("bare")
    manifest["timeline"]["name"] = "name\x00with\tcontrols"
    validate(manifest)


@pytest.mark.parametrize("version", ["0.3.0", "0.1.0", "1.0.0"])
def test_any_other_declared_version_is_rejected_at_its_declaration(
    version: str, load_fixture
) -> None:
    manifest = load_fixture("bare")
    manifest["meta"]["schema_version"] = version
    with pytest.raises(SchemaValidationError) as caught:
        validate(manifest)
    assert caught.value.path == ("meta", "schema_version")
