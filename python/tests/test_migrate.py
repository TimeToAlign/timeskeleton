from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from timeskeleton import (
    MIGRATIONS,
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    MigrationError,
    UnsupportedVersionError,
    canonical_json,
    declared_version,
    dumps,
    fixture_paths,
    migrate,
    migration_paths,
    validate,
)


def test_registered_migrations() -> None:
    assert {source: target for source, (target, _step) in MIGRATIONS.items()} == {
        "0.1.0": "0.2.0",
        "0.2.0": "0.2.1",
    }


def _step(document: dict) -> dict:
    """Apply the one migration registered for the document's version."""
    _target, step = MIGRATIONS[declared_version(document)]
    return step(copy.deepcopy(document))


def _text(document: dict) -> str:
    """The standard formatting without the canonical order."""
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def _write(document: dict) -> str:
    """The standard writer of the document's version: canonical order from 0.2.1."""
    unordered = declared_version(document) in ("0.1.0", "0.2.0")
    return _text(document) if unordered else dumps(document)


@pytest.mark.parametrize(
    "before, after", migration_paths(), ids=lambda path: path.parent.name
)
def test_each_step_reproduces_its_pair_byte_for_byte(before, after) -> None:
    source, target = before.parent.name.split("-to-")
    document = json.loads(before.read_text(encoding="utf-8"))
    assert declared_version(document) == source
    result = _step(document)
    assert result["meta"]["schema_version"] == target
    assert _write(result) == after.read_text(encoding="utf-8")
    validate(result)
    validate(migrate(document))


def _pair(name: str) -> dict:
    (before,) = [
        before for before, _after in migration_paths() if before.parent.name == name
    ]
    return json.loads(before.read_text(encoding="utf-8"))


def _before() -> dict:
    return _pair("0.1.0-to-0.2.0")


def test_populated_pair_carries_rows_and_the_derived_map_id() -> None:
    result = _step(_before())
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
    document = _before()
    assert _measure(document, 1)["qstamp"] == [1, 1]
    expected = _write(_step(document))
    _measure(document, 1)["qstamp"] = [1.0, 1]
    assert _write(_step(document)) == expected


# -- 0.2.0 to 0.2.1: canonical order -------------------------------------------


def test_every_0_2_0_fixture_migrates_to_the_library_s_0_2_1_fixture() -> None:
    previous = {path.name: path for path in fixture_paths("0.2.0")}
    current = {path.name: path for path in fixture_paths("0.2.1")}
    assert sorted(previous) == sorted(current)
    reordered = []
    for name, path in previous.items():
        document = json.loads(path.read_text(encoding="utf-8"))
        expected = json.loads(current[name].read_text(encoding="utf-8"))
        result = _step(document)
        result["meta"]["generator"] = expected["meta"]["generator"]
        assert dumps(result) == current[name].read_text(encoding="utf-8"), name
        document["meta"] = result["meta"]
        if _text(document) != _text(result):
            reordered.append(name)
    assert sorted(reordered) == [
        "conversion_maps.json",
        "corpus_parangonar_parangonada.json",
        "corpus_score_ms3.json",
    ]


def _orders(document: dict) -> dict[str, list]:
    timelines = document["manifest"]["timelines"]
    score = timelines["score"]
    flow = score["flow_control"]
    return {
        "timelines": list(timelines),
        "children": list(score["children"]),
        "nested": list(score["children"]["z"]["timeline"]["children"]),
        "maps": [entry["id"] for entry in score["conversion_maps"]],
        "regions": [entry["name"] for entry in score["regions"]],
        "breaks": [entry["label"] for entry in flow["breaks"]],
        "jumps": [entry["label"] for entry in flow["jumps"]],
        "markers": list(flow["markers"]),
        "int regions": [entry["name"] for entry in timelines["perf"]["regions"]],
    }


def test_the_pair_moves_from_insertion_order_to_canonical_order() -> None:
    before = _pair("0.2.0-to-0.2.1")
    after = _step(before)
    assert _orders(before) == {
        "timelines": ["score", "perf"],
        "children": ["z", "m", "b", "a"],
        "nested": ["y", "x"],
        "maps": ["shift", "scale", "label"],
        "regions": ["verse", "intro", "alpha", "coda"],
        "breaks": ["early", "section", "fine"],
        "jumps": ["first", "repeat", "inner", "segno"],
        "markers": ["segno", "coda", "Fine"],
        "int regions": ["late", "early"],
    }
    assert _orders(after) == {
        "timelines": ["perf", "score"],
        "children": ["b", "a", "m", "z"],
        "nested": ["x", "y"],
        "maps": ["label", "scale", "shift"],
        "regions": ["coda", "intro", "alpha", "verse"],
        "breaks": ["early", "fine", "section"],
        "jumps": ["first", "inner", "segno", "repeat"],
        "markers": ["Fine", "coda", "segno"],
        "int regions": ["early", "late"],
    }


def _at(numerator: int, denominator: int = 1) -> dict[str, Any]:
    return {
        "unit": "quarters",
        "number_type": "fraction",
        "value": [numerator, denominator],
    }


def _tied_document(load_fixture) -> dict[str, Any]:
    """The 0.2.0 flow-control fixture, extended with ties at every key level."""
    document = load_fixture("flow_control", "0.2.0")
    timelines = document["manifest"]["timelines"]
    timeline = timelines["flow:quarters"]
    pristine = copy.deepcopy(timeline)

    def copy_of(timeline_id: str) -> dict[str, Any]:
        return {**copy.deepcopy(pristine), "id": timeline_id}

    nested = copy_of("z")
    nested["children"] = {
        "y": {"offset": _at(1), "timeline": copy_of("y")},
        "x": {"offset": _at(0), "timeline": copy_of("x")},
    }
    timeline["children"] = {
        "z": {"offset": _at(1), "timeline": nested},
        "m": {"offset": _at(1), "timeline": copy_of("m")},
        "b": {"offset": _at(5, 8), "timeline": copy_of("b")},
        "a": {"offset": _at(2, 3), "timeline": copy_of("a")},
    }
    timeline["conversion_maps"] = [
        {
            "type": "ShiftMap",
            "id": map_id,
            "name": map_id,
            "source_unit": "quarters",
            "target_unit": None,
            "offset": [1, 2],
        }
        for map_id in ["\U0001f600", "\ufb00", "b", "a", "B"]
    ]
    timeline["regions"] = [
        {"name": name, "start": start, "end": end, "meta": {}}
        for name, start, end in [
            ("b", _at(2), _at(6)),
            ("a", _at(2), _at(6)),
            ("c", _at(2), _at(4)),
            ("d", _at(5, 8), _at(2, 3)),
        ]
    ]
    flow = timeline["flow_control"]
    (fine,) = flow["breaks"]
    flow["breaks"] = [
        {**fine, "condition": "always", "label": "always"},
        {**fine, "coordinate": _at(5, 8), "label": "early"},
        fine,
    ]
    (repeat,) = flow["jumps"]
    flow["jumps"] = [
        repeat,
        {**repeat, "control_type": "da_capo", "label": "DaCapo"},
        {**repeat, "to_coordinate": _at(2, 3), "label": "short"},
        {**repeat, "from_coordinate": _at(5, 8), "label": "early"},
    ]
    for name in ["\U0001f600", "\ufb00", "\u00e9", "Coda"]:
        flow["markers"][name] = _at(2)
    timelines["\U0001f600"] = copy_of("\U0001f600")
    timelines["Flow"] = copy_of("Flow")
    return document


def test_every_tie_resolves_to_the_canonical_order(load_fixture) -> None:
    result = migrate(_tied_document(load_fixture))
    validate(result)
    timelines = result["manifest"]["timelines"]
    assert list(timelines) == ["Flow", "flow:quarters", "\U0001f600"]
    timeline = timelines["flow:quarters"]
    assert list(timeline["children"]) == ["b", "a", "m", "z"]
    assert list(timeline["children"]["z"]["timeline"]["children"]) == ["x", "y"]
    assert [entry["id"] for entry in timeline["conversion_maps"]] == [
        "B",
        "a",
        "b",
        "\ufb00",
        "\U0001f600",
    ]
    assert [entry["name"] for entry in timeline["regions"]] == ["d", "c", "a", "b"]
    flow = timeline["flow_control"]
    assert [entry["label"] for entry in flow["breaks"]] == ["early", "Fine", "always"]
    assert [entry["label"] for entry in flow["jumps"]] == [
        "early",
        "short",
        "DaCapo",
        "Repeat",
    ]
    assert list(flow["markers"]) == [
        "Coda",
        "repeat-start",
        "\u00e9",
        "\ufb00",
        "\U0001f600",
    ]


def test_canonical_json_text() -> None:
    value = {
        "\U0001f600": {"b": True, "a": [1, 2.5, None]},
        "\ufb00": "\u00fc",
        "\u00e9": 1,
        "z": "\n",
        "a": [],
    }
    assert canonical_json(value) == (
        '{"a":[],"z":"\\n","\u00e9":1,"\ufb00":"\u00fc",'
        '"\U0001f600":{"a":[1,2.5,null],"b":true}}'
    )


def test_the_step_refuses_an_invalid_document_at_the_input_path(load_fixture) -> None:
    document = _tied_document(load_fixture)
    flow = document["manifest"]["timelines"]["flow:quarters"]["flow_control"]
    flow["breaks"][0]["control_type"] = "pause"
    with pytest.raises(MigrationError) as caught:
        migrate(document)
    assert caught.value.path == (
        "manifest",
        "timelines",
        "flow:quarters",
        "flow_control",
        "breaks",
        0,
        "control_type",
    )
    assert caught.value.message.startswith("no 0.2.1 shape: ")
