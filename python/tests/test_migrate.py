from __future__ import annotations

import json
from pathlib import Path

import pytest

from timeskeleton import (
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    UnsupportedVersionError,
    declared_version,
    dumps,
    fixture_paths,
    migrate,
    rejection_paths,
    validate,
)


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pair_directory() -> Path:
    """The pinned migration pair, found beside the bundled fixtures."""
    return fixture_paths("0.5.0")[0].parents[1] / "migrations" / "0.5.0-to-0.6.0"


def _without_generator(value: dict) -> dict:
    del value["meta"]["generator"]
    return value


def test_the_pinned_pair() -> None:
    before = _pair_directory() / "before.json"
    after = _pair_directory() / "after.json"
    (bare,) = [path for path in fixture_paths("0.5.0") if path.name == "bare.json"]
    assert before.read_bytes() == bare.read_bytes()
    migrated = migrate(_read(before))
    assert dumps(migrated) == after.read_text(encoding="utf-8")
    validate(migrated)


@pytest.mark.parametrize("path", fixture_paths("0.5.0"), ids=lambda path: path.stem)
def test_only_the_declaration_changes(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count('"schema_version": "0.5.0"') == 1
    assert dumps(migrate(json.loads(text))) == text.replace(
        '"schema_version": "0.5.0"', '"schema_version": "0.6.0"'
    )


@pytest.mark.parametrize("path", fixture_paths("0.6.0"), ids=lambda path: path.stem)
def test_the_latest_version_is_copied(path: Path) -> None:
    value = _read(path)
    migrated = migrate(value)
    assert migrated == value
    assert migrated is not value


@pytest.mark.parametrize("version", SUPPORTED_VERSIONS)
def test_the_input_is_never_changed(version: str) -> None:
    (path,) = [p for p in fixture_paths(version) if p.name == "bare.json"]
    value = _read(path)
    migrated = migrate(value)
    assert value == _read(path)
    migrated["meta"]["generator"] = "changed"
    migrated["timeline"]["id"] = "changed"
    migrated["timeline"]["flow_control"]["markers"].append("changed")
    assert value == _read(path)


@pytest.mark.parametrize("version", SUPPORTED_VERSIONS)
def test_the_chain_reaches_the_latest_version(version: str, load_fixture) -> None:
    value = load_fixture("bare")
    value["meta"]["schema_version"] = version
    assert declared_version(migrate(value)) == SCHEMA_VERSION


def test_the_0_6_0_manifests_are_the_0_5_0_manifests() -> None:
    old = {path.name: path for path in fixture_paths("0.5.0")}
    new = {path.name: path for path in fixture_paths("0.6.0")}
    assert sorted(old) == sorted(new)
    assert len(new) == 23
    for name, path in old.items():
        assert _without_generator(migrate(_read(path))) == _without_generator(
            _read(new[name])
        ), name


def test_the_0_6_0_rejection_cases_are_the_0_5_0_cases() -> None:
    old = {path.name: path for path in rejection_paths("0.5.0")}
    new = {path.name: path for path in rejection_paths("0.6.0")}
    assert sorted(old) == sorted(new)
    assert len(new) == 55
    refused = {"meta_schema_version_unknown.json", "root_missing_meta.json"}
    for name, path in old.items():
        before, after = _read(path), _read(new[name])
        assert (before["path"], before["reason"]) == (after["path"], after["reason"])
        if name in refused:
            assert path.read_bytes() == new[name].read_bytes()
        else:
            assert migrate(before["manifest"]) == after["manifest"], name


@pytest.mark.parametrize(
    ("meta", "version"),
    [
        ({"schema_version": "9.9.9"}, "9.9.9"),
        ({"schema_version": "0.4.0"}, "0.4.0"),
        (None, None),
        ({"schema_version": 5}, None),
    ],
)
def test_an_unsupported_version_is_refused(meta, version, load_fixture) -> None:
    value = load_fixture("bare")
    if meta is None:
        del value["meta"]
    else:
        value["meta"] = meta
    with pytest.raises(UnsupportedVersionError) as caught:
        migrate(value)
    assert caught.value.version == version


def test_the_refusal_names_the_supported_versions(load_fixture) -> None:
    value = load_fixture("bare")
    value["meta"]["schema_version"] = "9.9.9"
    with pytest.raises(UnsupportedVersionError) as caught:
        migrate(value)
    assert str(caught.value) == (
        "unsupported schema_version '9.9.9'; this package supports 0.5.0, 0.6.0"
    )
