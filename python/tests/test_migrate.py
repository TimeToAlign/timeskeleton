from __future__ import annotations

import json

import pytest

from timeskeleton import (
    MIGRATIONS,
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    MigrationError,
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
def test_migration_reproduces_shared_after_byte_for_byte(before, after) -> None:
    result = migrate(json.loads(before.read_text(encoding="utf-8")))
    assert json.dumps(result, indent=2) + "\n" == after.read_text(encoding="utf-8")
    validate(result)


def _before() -> dict:
    ((before, _after),) = migration_paths()
    return json.loads(before.read_text(encoding="utf-8"))


def test_populated_pair_carries_rows_and_the_derived_map_id() -> None:
    result = migrate(_before())
    (timeline,) = result["manifest"]["timelines"].values()
    rows = timeline["measure_map"]
    assert [row["count"] for row in rows] == [1, 2, 3, 4]
    assert rows[0]["offset_within_measure"] == [3, 1]
    assert rows[2]["next"] == ["2", "4"]
    position_map = timeline["conversion_maps"][0]
    assert list(position_map) == [
        "type",
        "id",
        "name",
        "source_unit",
        "target_unit",
        "meter_map",
        "beat_map_id",
    ]
    assert position_map["beat_map_id"] == "map:BeatInMeasureMap_1"


def _first_timeline(document: dict) -> dict:
    return next(iter(document["manifest"]["timelines"].values()))


def _measure(document: dict, index: int) -> dict:
    return _first_timeline(document)["measure_map"]["measures"][index]


@pytest.mark.parametrize(
    ("index", "key", "value"),
    [
        (1, "class", "SplitRegularMeasure"),
        (2, "next", ["m2", "m9"]),
        (2, "next", [["m2"]]),
        (0, "count", True),
    ],
    ids=[
        "measure_class_without_row_form",
        "next_naming_no_measure",
        "next_with_non_string_entry",
        "boolean_count",
    ],
)
def test_unknown_measure_shapes_are_refused_at_their_path(index, key, value) -> None:
    document = _before()
    _measure(document, index)[key] = value
    timeline_id = next(iter(document["manifest"]["timelines"]))
    with pytest.raises(MigrationError) as caught:
        migrate(document)
    assert caught.value.path == (
        "manifest",
        "timelines",
        timeline_id,
        "measure_map",
        "measures",
        index,
        key,
    )


def test_underived_metrical_position_maps_are_refused() -> None:
    document = _before()
    position_map = _first_timeline(document)["conversion_maps"][0]
    position_map["maps"]["beat"]["name"] = "renamed"
    key = next(iter(document["manifest"]["timelines"]))
    with pytest.raises(MigrationError) as caught:
        migrate(document)
    assert caught.value.path == (
        "manifest",
        "timelines",
        key,
        "conversion_maps",
        0,
        "maps",
    )


def test_unknown_conversion_map_types_are_refused_through_the_schema() -> None:
    document = _before()
    _first_timeline(document)["conversion_maps"][1]["type"] = "UnknownMap"
    key = next(iter(document["manifest"]["timelines"]))
    with pytest.raises(MigrationError) as caught:
        migrate(document)
    assert caught.value.path == ("manifest", "timelines", key, "conversion_maps", 1)


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


def test_an_integral_json_number_in_a_pair_reads_as_an_integer() -> None:
    ((_, after),) = migration_paths()
    document = _before()
    assert _measure(document, 1)["qstamp"] == [1, 1]
    _measure(document, 1)["qstamp"] = [1.0, 1]
    assert json.dumps(migrate(document), indent=2) + "\n" == after.read_text(
        encoding="utf-8"
    )
