from __future__ import annotations

import copy
import json
from typing import Any

import pytest

from timeskeleton import (
    ENVELOPE_VERSIONS,
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
    split,
    split_paths,
    validate,
)


def test_registered_migrations() -> None:
    assert {source: target for source, (target, _step) in MIGRATIONS.items()} == {
        "0.1.0": "0.2.0",
        "0.2.0": "0.2.1",
        "0.2.1": "0.3.0",
        "0.3.0": "0.4.0",
    }


def _step(value: dict) -> dict:
    """Apply the one migration registered for the fixture's version."""
    _target, step = MIGRATIONS[declared_version(value)]
    return step(copy.deepcopy(value))


def _text(value: dict) -> str:
    """The standard formatting without the canonical order."""
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def _write(value: dict) -> str:
    """The standard writer of the fixture's version: canonical order from 0.2.1."""
    unordered = declared_version(value) in ("0.1.0", "0.2.0")
    return _text(value) if unordered else dumps(value)


@pytest.mark.parametrize(
    "before, after", migration_paths(), ids=lambda path: path.parent.name
)
def test_each_step_reproduces_its_pair_byte_for_byte(before, after) -> None:
    source, target = before.parent.name.split("-to-")
    envelope = json.loads(before.read_text(encoding="utf-8"))
    assert declared_version(envelope) == source
    result = _step(envelope)
    assert result["meta"]["schema_version"] == target
    assert _write(result) == after.read_text(encoding="utf-8")
    validate(result)
    roots = envelope.get("manifest", {}).get("timelines", {})
    if target == "0.4.0" or len(roots) == 1:
        validate(migrate(envelope))
    else:
        for part in split(envelope):
            validate(migrate(part))


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


def _first_timeline(envelope: dict) -> dict:
    return next(iter(envelope["manifest"]["timelines"].values()))


def _measure(envelope: dict, index: int) -> dict:
    return _first_timeline(envelope)["measure_map"]["measures"][index]


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
    envelope = _before()
    _measure(envelope, index)[key] = value
    timeline_id = next(iter(envelope["manifest"]["timelines"]))
    with pytest.raises(MigrationError) as caught:
        migrate(envelope)
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
    envelope = _before()
    position_map = _first_timeline(envelope)["conversion_maps"][0]
    position_map["maps"]["beat"]["name"] = "renamed"
    key = next(iter(envelope["manifest"]["timelines"]))
    with pytest.raises(MigrationError) as caught:
        migrate(envelope)
    assert caught.value.path == (
        "manifest",
        "timelines",
        key,
        "conversion_maps",
        0,
        "maps",
    )


def test_unknown_conversion_map_types_are_refused_through_the_schema() -> None:
    envelope = _before()
    _first_timeline(envelope)["conversion_maps"][1]["type"] = "UnknownMap"
    key = next(iter(envelope["manifest"]["timelines"]))
    with pytest.raises(MigrationError) as caught:
        migrate(envelope)
    assert caught.value.path == ("manifest", "timelines", key, "conversion_maps", 1)


@pytest.mark.parametrize("version", SUPPORTED_VERSIONS)
def test_every_supported_version_migrates_to_a_valid_latest_manifest(
    version: str,
) -> None:
    for path in fixture_paths(version):
        value = json.loads(path.read_text(encoding="utf-8"))
        roots = value.get("manifest", {}).get("timelines", {})
        if version != "0.4.0" and len(roots) != 1:
            continue
        result = migrate(value)
        assert result["meta"]["schema_version"] == SCHEMA_VERSION
        validate(result)


def test_unknown_or_missing_version_is_refused(load_fixture) -> None:
    envelope = load_fixture("empty", "0.3.0")
    envelope["meta"]["schema_version"] = "unknown"
    with pytest.raises(UnsupportedVersionError):
        migrate(envelope)


def test_an_integral_json_number_in_a_pair_reads_as_an_integer() -> None:
    envelope = _before()
    assert _measure(envelope, 1)["qstamp"] == [1, 1]
    expected = _write(_step(envelope))
    _measure(envelope, 1)["qstamp"] = [1.0, 1]
    assert _write(_step(envelope)) == expected


# -- 0.2.0 to 0.2.1: canonical order -------------------------------------------


def test_every_0_2_0_fixture_migrates_to_the_library_s_0_2_1_fixture() -> None:
    previous = {path.name: path for path in fixture_paths("0.2.0")}
    current = {path.name: path for path in fixture_paths("0.2.1")}
    assert sorted(previous) == sorted(current)
    reordered = []
    for name, path in previous.items():
        envelope = json.loads(path.read_text(encoding="utf-8"))
        expected = json.loads(current[name].read_text(encoding="utf-8"))
        result = _step(envelope)
        result["meta"]["generator"] = expected["meta"]["generator"]
        assert dumps(result) == current[name].read_text(encoding="utf-8"), name
        envelope["meta"] = result["meta"]
        if _text(envelope) != _text(result):
            reordered.append(name)
    assert sorted(reordered) == [
        "conversion_maps.json",
        "corpus_parangonar_parangonada.json",
        "corpus_score_ms3.json",
    ]


def _orders(envelope: dict) -> dict[str, list]:
    timelines = envelope["manifest"]["timelines"]
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


def _tied_envelope(load_fixture) -> dict[str, Any]:
    """The 0.2.0 flow-control fixture, extended with ties at every key level."""
    envelope = load_fixture("flow_control", "0.2.0")
    timelines = envelope["manifest"]["timelines"]
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
    return envelope


def test_every_tie_resolves_to_the_canonical_order(load_fixture) -> None:
    result = _step(_tied_envelope(load_fixture))
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


def test_the_step_refuses_an_invalid_envelope_at_the_input_path(load_fixture) -> None:
    envelope = _tied_envelope(load_fixture)
    flow = envelope["manifest"]["timelines"]["flow:quarters"]["flow_control"]
    flow["breaks"][0]["control_type"] = "pause"
    with pytest.raises(MigrationError) as caught:
        migrate(envelope)
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


# -- 0.2.1 to 0.3.0: the version only -------------------------------------------


def test_the_0_3_0_step_declares_its_version_and_changes_nothing_else() -> None:
    (before, after) = [
        pair for pair in migration_paths() if pair[0].parent.name == "0.2.1-to-0.3.0"
    ][0]
    before_text = before.read_text(encoding="utf-8")
    assert before_text.count('"schema_version": "0.2.1"') == 1
    expected = before_text.replace(
        '"schema_version": "0.2.1"', '"schema_version": "0.3.0"'
    )
    assert after.read_text(encoding="utf-8") == expected
    assert dumps(_step(json.loads(before_text))) == expected


def test_the_0_3_0_step_refuses_an_invalid_envelope_at_its_path(load_fixture) -> None:
    envelope = load_fixture("flow_control", "0.2.1")
    flow = envelope["manifest"]["timelines"]["flow:quarters"]["flow_control"]
    flow["breaks"][0]["control_type"] = "pause"
    with pytest.raises(MigrationError) as caught:
        _step(envelope)
    assert caught.value.path == (
        "manifest",
        "timelines",
        "flow:quarters",
        "flow_control",
        "breaks",
        0,
        "control_type",
    )
    assert caught.value.message.startswith("no 0.3.0 shape: ")


# -- 0.3.0 to 0.4.0: one manifest ---------------------------------------------


def test_the_0_4_0_step_preserves_styles_and_filters_timeline_rules() -> None:
    before = _pair("0.3.0-to-0.4.0")
    result = _step(before)
    assert result["timeline"] == before["manifest"]["timelines"]["melody"]
    assert result["graphical"] == {
        "styles": before["graphical"]["styles"],
        "timelines": {
            "melody": before["graphical"]["timelines"]["melody"],
            "phrase": before["graphical"]["timelines"]["phrase"],
        },
    }


@pytest.mark.parametrize("name", ["styled", "empty"])
def test_migrating_an_envelope_without_one_root_requests_split(
    name, load_fixture
) -> None:
    with pytest.raises(MigrationError) as caught:
        migrate(load_fixture(name, "0.3.0"))
    assert caught.value.path == ("manifest", "timelines")
    assert "split" in caught.value.message


def test_split_reproduces_its_outputs_byte_for_byte() -> None:
    before, after_paths = split_paths()
    envelope = json.loads(before.read_text(encoding="utf-8"))
    assert [dumps(value) for value in split(envelope)] == [
        path.read_text(encoding="utf-8") for path in after_paths
    ]


def test_split_then_migrate_reproduces_every_0_4_0_manifest() -> None:
    expected = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in fixture_paths("0.4.0")
    }
    actual = []
    for path in fixture_paths("0.3.0"):
        envelope = json.loads(path.read_text(encoding="utf-8"))
        for part in split(envelope):
            result = migrate(part)
            root_id = result["timeline"]["id"]
            candidates = [
                (name, value)
                for name, value in expected.items()
                if value["timeline"]["id"] == root_id
            ]
            assert len(candidates) == 1
            name, wanted = candidates[0]
            assert result["timeline"] == wanted["timeline"]
            assert result.get("graphical") == wanted.get("graphical")
            actual.append(name)
    assert sorted(actual) == sorted(expected)


def test_split_empty_is_empty(load_fixture) -> None:
    assert split(load_fixture("empty", "0.3.0")) == []


def test_split_refuses_a_0_4_0_manifest(load_fixture) -> None:
    with pytest.raises(MigrationError) as caught:
        split(load_fixture("bare", "0.4.0"))
    assert caught.value.path == ("meta", "schema_version")


def test_the_0_4_0_step_refuses_a_timeline_that_is_no_object() -> None:
    envelope = {
        "meta": {"schema_version": "0.3.0"},
        "manifest": {"timelines": {"a": 5}},
        "graphical": {"timelines": {"a": []}},
    }
    with pytest.raises(MigrationError) as caught:
        migrate(envelope)
    assert caught.value.path == ("timeline",)


def test_the_0_4_0_step_writes_the_canonical_order(load_fixture) -> None:
    envelope = load_fixture("nested", "0.3.0")
    (timeline,) = envelope["manifest"]["timelines"].values()
    (child_id,) = timeline["children"]
    earlier = copy.deepcopy(timeline["children"][child_id])
    earlier["offset"]["value"] = [1, 1]
    earlier["timeline"]["id"] = "tl:early"
    timeline["children"]["tl:early"] = earlier
    assert list(timeline["children"]) == [child_id, "tl:early"]
    result = migrate(envelope)
    assert list(result["timeline"]["children"]) == ["tl:early", child_id]


@pytest.mark.parametrize(
    ("version", "count"),
    [("0.1.0", 8), ("0.2.0", 29), ("0.2.1", 29), ("0.3.0", 34)],
)
def test_split_divides_every_envelope_fixture_of_every_envelope_version(
    version: str, count: int
) -> None:
    assert version in ENVELOPE_VERSIONS
    results = [
        part
        for path in fixture_paths(version)
        for part in split(json.loads(path.read_text(encoding="utf-8")))
    ]
    assert len(results) == count
    for part in results:
        assert declared_version(part) == "0.3.0"
        validate(part)


def test_the_envelope_versions_are_the_published_envelopes() -> None:
    assert ENVELOPE_VERSIONS == ("0.1.0", "0.2.0", "0.2.1", "0.3.0")
