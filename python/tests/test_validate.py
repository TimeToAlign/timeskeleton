from __future__ import annotations

import json

import pytest

from timeskeleton import (
    SUPPORTED_VERSIONS,
    SchemaValidationError,
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
        validate(case["document"])
    assert caught.value.path == tuple(case["path"])


def test_error_renders_as_json_pointer() -> None:
    case = json.loads(rejection_paths()[0].read_text(encoding="utf-8"))
    with pytest.raises(SchemaValidationError) as caught:
        validate(case["document"])
    assert str(caught.value).startswith(f"{json_pointer(caught.value.path)}: ")


def test_json_pointer_rendering() -> None:
    assert json_pointer(()) == "#"
    assert json_pointer(("a/b", "c~d", 0)) == "#/a~1b/c~0d/0"


@pytest.mark.parametrize("value", [9007199254740993, 9223372036854775807])
def test_integer_boundaries_validate_migrate_and_preserve(
    value: int, load_fixture
) -> None:
    from timeskeleton import migrate

    document = load_fixture("discrete_logical")
    timeline = next(iter(document["manifest"]["timelines"].values()))
    timeline["length"]["value"] = value
    validate(document)
    result = migrate(document)
    result_timeline = next(iter(result["manifest"]["timelines"].values()))
    assert result_timeline["length"]["value"] == value
