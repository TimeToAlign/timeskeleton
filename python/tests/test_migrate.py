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
    migration_paths,
    validate,
)


def test_registered_migration() -> None:
    target, _migration = MIGRATIONS["0.1.0"]
    assert target == "0.2.0"


@pytest.mark.parametrize("before, after", migration_paths())
def test_migration_reproduces_shared_after(before, after) -> None:
    assert migrate(json.loads(before.read_text(encoding="utf-8"))) == json.loads(
        after.read_text(encoding="utf-8")
    )


@pytest.mark.parametrize("version", SUPPORTED_VERSIONS)
def test_every_supported_version_migrates_to_a_valid_latest_document(
    version: str,
) -> None:
    for path in fixture_paths(version):
        result = migrate(json.loads(path.read_text(encoding="utf-8")))
        assert result["meta"]["schema_version"] == SCHEMA_VERSION
        validate(result)


def test_unknown_or_missing_version_is_refused(load_fixture) -> None:
    document = load_fixture("empty")
    document["meta"]["schema_version"] = "unknown"
    with pytest.raises(UnsupportedVersionError):
        migrate(document)
