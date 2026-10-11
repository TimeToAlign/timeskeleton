from __future__ import annotations

import copy
import json
import math
from typing import Any

import pytest

from timeskeleton import (
    canonical_json,
    canonical_order,
    dumps,
    fixture_paths,
    rejection_paths,
    validate,
)

# Shared with the JavaScript suite, character for character.
NUMBER_CORPUS = (
    "[0.1, 2.0, 1e-07, 1e+16, 123456789012345678, -0.0, 5e-324, "
    "1.7976931348623157e+308, 1E5, 1.50, -0, 100, 0.0001, 1e-05, "
    '1000000000000000.0, "\\u00e9", "\\ud83d\\ude00", "\\ufb00", '
    '"a\\"b\\\\c\\n\\u0001\\u001f"]'
)
NUMBER_CORPUS_TEXT = (
    "[\n"
    "  0.1,\n"
    "  2.0,\n"
    "  1e-07,\n"
    "  1e+16,\n"
    "  123456789012345678,\n"
    "  -0.0,\n"
    "  5e-324,\n"
    "  1.7976931348623157e+308,\n"
    "  100000.0,\n"
    "  1.5,\n"
    "  0,\n"
    "  100,\n"
    "  0.0001,\n"
    "  1e-05,\n"
    "  1000000000000000.0,\n"
    '  "é",\n'
    '  "\U0001f600",\n'
    '  "ﬀ",\n'
    '  "a\\"b\\\\c\\n\\u0001\\u001f"\n'
    "]\n"
)


def _standard_files() -> list:
    return [*fixture_paths(), *rejection_paths()]


@pytest.mark.parametrize(
    "path", _standard_files(), ids=lambda path: f"{path.parent.name}/{path.name}"
)
def test_standard_files_round_trip_byte_for_byte(path) -> None:
    text = path.read_text(encoding="utf-8")
    assert dumps(json.loads(text)) == text


def test_the_standard_files_number_seventy_eight() -> None:
    assert len(_standard_files()) == 23 + 55


def test_non_ascii_text_is_written_unescaped() -> None:
    (path,) = [p for p in fixture_paths() if p.name == "corpus_score_ms3.json"]
    text = path.read_text(encoding="utf-8")
    assert '"label": "MC 15 → start (MC 1)"' in text
    assert "\\u2192" not in text


def test_number_corpus() -> None:
    assert dumps(json.loads(NUMBER_CORPUS)) == NUMBER_CORPUS_TEXT


def test_canonical_order_copies_and_reorders_manifests_only(load_fixture) -> None:
    manifest = load_fixture("continuous_logical")
    text = json.dumps(manifest)
    assert dumps(canonical_order(manifest)) == dumps(manifest)
    assert json.dumps(manifest) == text
    value = {"b": [3, 1], "a": {"timeline": 1}}
    assert json.dumps(canonical_order(value)) == json.dumps(value)


def test_the_writer_sorts_every_object_by_key() -> None:
    value = {"b": 1, "\U0001f600": 2, "\ufb00": 3, "A": {"z": 0, "10": 1, "2": 2}}
    assert dumps(value) == (
        "{\n"
        '  "A": {\n'
        '    "10": 1,\n'
        '    "2": 2,\n'
        '    "z": 0\n'
        "  },\n"
        '  "b": 1,\n'
        '  "\ufb00": 3,\n'
        '  "\U0001f600": 2\n'
        "}\n"
    )


def _at(numerator: int, denominator: int = 1) -> dict[str, Any]:
    return {
        "unit": "quarters",
        "number_type": "fraction",
        "value": [numerator, denominator],
    }


def _tied_manifest(load_fixture) -> dict[str, Any]:
    """The bare fixture, extended with ties at every key level."""
    manifest = load_fixture("bare")
    timeline = manifest["timeline"]
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
        for map_id in ["\U0001f600", "\ufb00", "B2", "a2", "B"]
    ]
    timeline["regions"] = [
        {"id": region_id, "name": region_id, "start": start, "end": end, "meta": {}}
        for region_id, start, end in [
            ("rb", _at(2), _at(6)),
            ("ra", _at(2), _at(6)),
            ("rc", _at(2), _at(4)),
            ("rd", _at(5, 8), _at(2, 3)),
        ]
    ]
    flow = timeline["flow_control"]
    flow["breaks"] = [
        {
            "id": break_id,
            "coordinate": coordinate,
            "control_type": "fine",
            "condition": "always",
            "repeat_count": 1,
            "label": None,
            "name": None,
            "meta": {},
        }
        for break_id, coordinate in [
            ("kb", _at(12)),
            ("ka", _at(12)),
            ("kz", _at(5, 8)),
        ]
    ]
    flow["jumps"] = [
        {
            "id": jump_id,
            "from_coordinate": start,
            "to_coordinate": end,
            "control_type": "repeat_end",
            "condition": "always",
            "repeat_count": 1,
            "target": target,
            "label": None,
            "meta": {},
        }
        for jump_id, start, end, target in [
            ("jj", _at(8), _at(2), "Coda"),
            ("jd", _at(8), _at(2), None),
            ("js", _at(8), _at(2, 3), None),
            ("je", _at(5, 8), _at(2), None),
        ]
    ]
    flow["markers"] = [
        {"id": marker_id, "name": None, "coordinate": coordinate}
        for marker_id, coordinate in [
            ("\U0001f600!", _at(2)),
            ("\ufb00!", _at(2)),
            ("\u00e9", _at(2)),
            ("Coda", _at(2)),
            ("start", _at(5, 8)),
        ]
    ]
    return manifest


def test_every_tie_resolves_to_the_canonical_order(load_fixture) -> None:
    result = canonical_order(_tied_manifest(load_fixture))
    validate(result)
    timeline = result["timeline"]
    assert list(timeline["children"]) == ["z", "m", "b", "a"]
    assert [entry["id"] for entry in timeline["conversion_maps"]] == [
        "B",
        "B2",
        "a2",
        "\ufb00",
        "\U0001f600",
    ]
    assert [entry["id"] for entry in timeline["regions"]] == ["rd", "rc", "ra", "rb"]
    flow = timeline["flow_control"]
    assert [entry["id"] for entry in flow["breaks"]] == ["kz", "ka", "kb"]
    assert [entry["id"] for entry in flow["jumps"]] == ["je", "js", "jd", "jj"]
    assert [entry["id"] for entry in flow["markers"]] == [
        "start",
        "Coda",
        "\u00e9",
        "\ufb00!",
        "\U0001f600!",
    ]
    written = json.loads(dumps(result))["timeline"]
    assert list(written["children"]) == ["a", "b", "m", "z"]
    assert list(written["children"]["z"]["timeline"]["children"]) == ["x", "y"]


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


@pytest.mark.parametrize(
    "value", ["\ud800", {"\udfff": 1}, math.nan, math.inf], ids=repr
)
def test_values_the_writer_refuses(value) -> None:
    with pytest.raises(ValueError):
        dumps([value])
    with pytest.raises(ValueError):
        canonical_json([value])


def test_an_unorderable_collection_is_refused() -> None:
    manifest = {"timeline": {"regions": [{"id": "r"}] * 2}}
    with pytest.raises(ValueError, match="cannot put regions in canonical order"):
        dumps(manifest)
