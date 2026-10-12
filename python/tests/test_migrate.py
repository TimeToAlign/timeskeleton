from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from timeskeleton import (
    FILE_KINDS,
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


def _pair_directory(pair: str) -> Path:
    """A pinned migration pair, found beside the bundled fixtures."""
    return fixture_paths("0.5.0")[0].parents[1] / "migrations" / pair


def _without_generator(value: dict) -> dict:
    del value["meta"]["generator"]
    return value


def _at_latest(value: dict) -> dict:
    """The value declaring 0.7.0, with ``is_segment_line: false`` on every timeline."""

    def mark(timeline: dict) -> None:
        timeline["is_segment_line"] = False
        for child in timeline["children"].values():
            mark(child["timeline"])

    result = copy.deepcopy(value)
    result["meta"]["schema_version"] = "0.7.0"
    mark(result["timeline"])
    return result


def test_the_pinned_pairs() -> None:
    first = _pair_directory("0.5.0-to-0.6.0")
    second = _pair_directory("0.6.0-to-0.7.0")
    for directory, source in ((first, "0.5.0"), (second, "0.6.0")):
        (bare,) = [path for path in fixture_paths(source) if path.name == "bare.json"]
        assert (directory / "before.json").read_bytes() == bare.read_bytes()
    before = (first / "before.json").read_text(encoding="utf-8")
    assert (first / "after.json").read_text(encoding="utf-8") == before.replace(
        '"schema_version": "0.5.0"', '"schema_version": "0.6.0"'
    )
    before = (second / "before.json").read_text(encoding="utf-8")
    assert (second / "after.json").read_text(encoding="utf-8") == before.replace(
        '"schema_version": "0.6.0"', '"schema_version": "0.7.0"'
    ).replace(
        '    "id": "bare",\n', '    "id": "bare",\n    "is_segment_line": false,\n'
    )
    for directory in (first, second):
        value = _read(directory / "before.json")
        migrated = migrate(value)
        assert dumps(migrated) == dumps(_at_latest(value))
        validate(migrated)
    assert dumps(migrate(_read(second / "before.json"))) == (
        second / "after.json"
    ).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "path",
    [*fixture_paths("0.5.0"), *fixture_paths("0.6.0")],
    ids=lambda path: f"{path.parent.name}/{path.stem}",
)
def test_only_the_declaration_and_the_flag_change(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count(f'"schema_version": "{path.parent.name}"') == 1
    assert dumps(migrate(json.loads(text))) == dumps(_at_latest(json.loads(text)))


def test_every_timeline_is_marked(load_fixture) -> None:
    migrated = migrate(load_fixture("nested", "0.6.0"))
    root = migrated["timeline"]
    (child,) = [entry["timeline"] for entry in root["children"].values()]
    (grandchild,) = [entry["timeline"] for entry in child["children"].values()]
    assert [timeline["is_segment_line"] for timeline in (root, child, grandchild)] == [
        False,
        False,
        False,
    ]
    original = load_fixture("nested", "0.6.0")
    del root["is_segment_line"], child["is_segment_line"], grandchild["is_segment_line"]
    migrated["meta"]["schema_version"] = "0.6.0"
    assert migrated == original


@pytest.mark.parametrize(
    "path",
    [path for kind in FILE_KINDS for path in fixture_paths("0.7.0", kind)],
    ids=lambda path: path.stem,
)
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
    assert declared_version(migrate(value)) == SCHEMA_VERSION == "0.7.0"


MINTED_CHILDREN = {"notes": "clt_2", "controls": "clt_3"}
"""The store-built children of ``corpus_score_ms3``: 0.6.0 id -> 0.7.0 id."""


def _with_minted_children(value: dict) -> dict:
    """Rename the store-built children as 0.7.0 does: a minted id, the store name."""
    children = value["timeline"]["children"]
    renamed = {}
    for store, minted in MINTED_CHILDREN.items():
        child = children.pop(store)
        child["timeline"]["id"] = minted
        child["timeline"]["name"] = store
        renamed[minted] = child
    assert children == {}
    value["timeline"]["children"] = renamed
    return value


@pytest.mark.parametrize(("old", "new"), [("0.5.0", "0.6.0"), ("0.6.0", "0.7.0")])
def test_the_manifests_of_a_version_are_those_of_the_one_before(old, new) -> None:
    before = {path.name: path for path in fixture_paths(old)}
    after = {path.name: path for path in fixture_paths(new)}
    assert sorted(before) == sorted(after)
    assert len(after) == 23
    for name, path in before.items():
        expected = _without_generator(migrate(_read(path)))
        if (new, name) == ("0.7.0", "corpus_score_ms3.json"):
            assert expected != _without_generator(migrate(_read(after[name])))
            expected = _with_minted_children(expected)
        assert expected == _without_generator(migrate(_read(after[name]))), name


@pytest.mark.parametrize(
    ("old", "new", "count"), [("0.5.0", "0.6.0", 55), ("0.6.0", "0.7.0", 93)]
)
def test_the_rejection_cases_hold_those_of_the_version_before(old, new, count) -> None:
    before = {path.name: path for path in rejection_paths(old)}
    after = {path.name: path for path in rejection_paths(new)}
    assert set(before) <= set(after)
    assert len(before) == 55
    assert len(after) == count
    refused = {"meta_schema_version_unknown.json", "root_missing_meta.json"}
    for name, path in before.items():
        earlier, later = _read(path), _read(after[name])
        assert earlier["path"] == later["path"]
        if (new, name) == ("0.7.0", "root_missing_timeline.json"):
            assert later["reason"] == (
                "A file holds exactly one of timeline, group and bundle beside meta; "
                "this one holds none."
            )
        else:
            assert earlier["reason"] == later["reason"]
        if name in refused and new == "0.6.0":
            assert path.read_bytes() == after[name].read_bytes()
        elif name in refused:
            # migrate refuses these; 0.7.0 gives their timeline the new flag.
            earlier["manifest"]["timeline"]["is_segment_line"] = False
            assert earlier == later
        else:
            assert declared_version(later["manifest"]) == new
            assert migrate(earlier["manifest"]) == migrate(later["manifest"]), name


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
        "unsupported schema_version '9.9.9'; this package supports 0.5.0, 0.6.0, 0.7.0"
    )
