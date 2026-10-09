from __future__ import annotations

import json

import pytest

from timeskeleton import (
    MIGRATIONS,
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    UnsupportedVersionError,
    fixture_paths,
    migrate,
    validate,
)

from .conftest import FIXTURE_NAMES


def test_no_migration_exists_while_one_version_is_published() -> None:
    assert MIGRATIONS == {}


@pytest.mark.parametrize("name", FIXTURE_NAMES)
def test_latest_documents_migrate_to_an_equal_copy(load_fixture, name: str) -> None:
    document = load_fixture(name)
    result = migrate(document)
    assert result == document
    assert result is not document
    result["meta"]["generator"] = "changed"
    assert document["meta"]["generator"] != "changed"
    for timeline_id, manifest in result["manifest"]["timelines"].items():
        manifest["length"]["value"] = -1.0
        assert document["manifest"]["timelines"][timeline_id]["length"]["value"] != -1.0


@pytest.mark.parametrize("version", SUPPORTED_VERSIONS)
def test_every_supported_version_migrates_to_a_valid_latest_document(
    version: str,
) -> None:
    paths = fixture_paths(version)
    assert paths
    for path in paths:
        with path.open(encoding="utf-8") as handle:
            document = json.load(handle)
        result = migrate(document)
        assert result["meta"]["schema_version"] == SCHEMA_VERSION
        validate(result)


def test_unknown_version_is_refused(load_fixture) -> None:
    document = load_fixture("empty")
    document["meta"]["schema_version"] = "0.2.0"
    with pytest.raises(UnsupportedVersionError) as caught:
        migrate(document)
    assert caught.value.version == "0.2.0"


@pytest.mark.parametrize(
    "document",
    [{"manifest": {"timelines": {}}}, {"meta": {}}, {"meta": {"schema_version": 1}}],
    ids=["no meta", "no schema_version", "non-string schema_version"],
)
def test_missing_version_is_refused(document) -> None:
    with pytest.raises(UnsupportedVersionError) as caught:
        migrate(document)
    assert caught.value.version is None
