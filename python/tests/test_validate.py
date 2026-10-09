from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

from timeskeleton import SchemaValidationError, json_pointer, validate

from .conftest import FIXTURE_NAMES

Path = tuple[str | int, ...]
Mutation = Callable[[dict[str, Any]], Path]


def _timeline(document: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    """Return the path prefix and the manifest of the first top-level timeline."""
    timelines = document["manifest"]["timelines"]
    timeline_id = next(iter(timelines))
    return ("manifest", "timelines", timeline_id), timelines[timeline_id]


def _unknown_root_key(document: dict[str, Any]) -> Path:
    document["extra"] = 1
    return ()


def _missing_meta(document: dict[str, Any]) -> Path:
    del document["meta"]
    return ()


def _missing_required_key(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    del timeline["locked"]
    return prefix


def _name_not_string(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["name"] = 1
    return (*prefix, "name")


def _class_outside_enum(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["class"] = "Timeline"
    return (*prefix, "class")


def _unit_outside_enum(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["unit"] = "beats"
    return (*prefix, "unit")


def _number_type_outside_enum(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["number_type"] = "decimal"
    return (*prefix, "number_type")


def _float_numerator(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["length"]["numerator"] = 1.5
    return (*prefix, "length", "numerator")


def _one_sided_ratio(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["length"]["denominator"] = None
    return (*prefix, "length")


def _denominator_zero(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["length"]["denominator"] = 0
    return (*prefix, "length", "denominator")


def _string_numerator_12a(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["length"]["numerator"] = "12a"
    return (*prefix, "length", "numerator")


def _child_offset_float_numerator(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    child_id = next(iter(timeline["children"]))
    timeline["children"][child_id]["offset"]["numerator"] = 0.5
    return (*prefix, "children", child_id, "offset", "numerator")


def _region_not_object(document: dict[str, Any]) -> Path:
    prefix, timeline = _timeline(document)
    timeline["regions"] = [1]
    return (*prefix, "regions", 0)


def _schema_version_0_2_0(document: dict[str, Any]) -> Path:
    document["meta"]["schema_version"] = "0.2.0"
    return ("meta", "schema_version")


REJECTIONS: list[Mutation] = [
    _unknown_root_key,
    _missing_meta,
    _missing_required_key,
    _name_not_string,
    _class_outside_enum,
    _unit_outside_enum,
    _number_type_outside_enum,
    _float_numerator,
    _one_sided_ratio,
    _denominator_zero,
    _string_numerator_12a,
    _child_offset_float_numerator,
    _region_not_object,
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


def test_rejection_path_segments_keep_their_types(load_fixture) -> None:
    document = load_fixture("continuous_logical")
    _region_not_object(document)
    with pytest.raises(SchemaValidationError) as caught:
        validate(document)
    assert caught.value.path[-1] == 0
    assert isinstance(caught.value.path[-1], int)
