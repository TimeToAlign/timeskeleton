from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from timeskeleton import SchemaValidationError, json_pointer, validate

from .conftest import FIXTURE_NAMES

Path = tuple[str | int, ...]
Mutation = Callable[[dict[str, Any]], Path]


def _timeline(document: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    """Return the path prefix and manifest of the first top-level timeline."""
    timelines = document["manifest"]["timelines"]
    timeline_id = next(iter(timelines))
    return ("manifest", "timelines", timeline_id), timelines[timeline_id]


def _unknown_root_key(document: dict[str, Any]) -> Path:
    document["extra"] = 1
    return ()


def _missing_required_key(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    del timeline["locked"]
    return prefix


def _class_outside_enum(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["class"] = "Timeline"
    return (*prefix, "class")


def _unit_outside_enum(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["unit"] = "beats"
    return (*prefix, "unit")


def _length(document: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    prefix, timeline = _timeline(document)
    return (*prefix, "length"), timeline["length"]


def _fraction_coordinate_with_bare_integer(document: dict[str, Any]) -> Path:
    prefix, length = _length(document)
    length["value"] = 12
    return (*prefix, "value")


def _zero_denominator(document: dict[str, Any]) -> Path:
    prefix, length = _length(document)
    length["value"] = [12, 0]
    return (*prefix, "value", 1)


def _negative_length(document: dict[str, Any]) -> Path:
    prefix, length = _length(document)
    length["value"] = [-12, 1]
    return (*prefix, "value", 0)


def _three_element_fraction(document: dict[str, Any]) -> Path:
    prefix, length = _length(document)
    length["value"] = [1, 2, 3]
    return (*prefix, "value")


def _string_fraction(document: dict[str, Any]) -> Path:
    prefix, length = _length(document)
    length["value"] = "12/1"
    return (*prefix, "value")


def _coordinate_without_unit(document: dict[str, Any]) -> Path:
    prefix, length = _length(document)
    del length["unit"]
    return prefix


def _int_number_type_with_fraction_value(document: dict[str, Any]) -> Path:
    prefix, length = _length(document)
    length["number_type"] = "int"
    return (*prefix, "value")


def _schema_version_0_2_0(document: dict[str, Any]) -> Path:
    document["meta"]["schema_version"] = "0.2.0"
    return ("meta", "schema_version")


REJECTIONS: list[Mutation] = [
    _unknown_root_key,
    _missing_required_key,
    _class_outside_enum,
    _unit_outside_enum,
    _fraction_coordinate_with_bare_integer,
    _zero_denominator,
    _negative_length,
    _three_element_fraction,
    _string_fraction,
    _coordinate_without_unit,
    _int_number_type_with_fraction_value,
    _schema_version_0_2_0,
]


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_every_fixture_validates(load_fixture, name: str) -> None:
    validate(load_fixture(name))


@pytest.mark.parametrize("mutate", REJECTIONS, ids=lambda f: f.__name__.lstrip("_"))
def test_one_mutation_is_rejected_at_its_path(load_fixture, mutate: Mutation) -> None:
    document = load_fixture("continuous_logical")
    expected = mutate(document)
    with pytest.raises(SchemaValidationError) as caught:
        validate(document)
    assert caught.value.path == expected


def test_error_renders_as_json_pointer(load_fixture) -> None:
    document = load_fixture("continuous_logical")
    expected = _class_outside_enum(document)
    with pytest.raises(SchemaValidationError) as caught:
        validate(document)
    error = caught.value
    assert isinstance(error.message, str) and error.message
    assert str(error) == f"{json_pointer(expected)}: {error.message}"


def test_json_pointer_rendering() -> None:
    assert json_pointer(()) == "#"
    assert json_pointer(("manifest", "timelines", "tl:1", "class")) == (
        "#/manifest/timelines/tl:1/class"
    )
    assert json_pointer(("a/b", "c~d", 0)) == "#/a~1b/c~0d/0"
