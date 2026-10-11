from __future__ import annotations

import json
import math

import pytest

from timeskeleton import (
    canonical_json,
    canonical_order,
    dumps,
    fixture_paths,
    migration_paths,
    rejection_paths,
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
    afters = {before.parent.name: after for before, after in migration_paths()}
    return [
        *fixture_paths("0.2.1"),
        *rejection_paths("0.2.1"),
        afters["0.2.0-to-0.2.1"],
        *fixture_paths("0.3.0"),
        *rejection_paths("0.3.0"),
        afters["0.2.1-to-0.3.0"],
        *fixture_paths("0.4.0"),
        *rejection_paths("0.4.0"),
        afters["0.3.0-to-0.4.0"],
    ]


@pytest.mark.parametrize(
    "path", _standard_files(), ids=lambda path: f"{path.parent.name}/{path.name}"
)
def test_standard_files_round_trip_byte_for_byte(path) -> None:
    text = path.read_text(encoding="utf-8")
    assert dumps(json.loads(text)) == text


def test_the_standard_files_number_one_hundred_and_ninety_nine() -> None:
    assert len(_standard_files()) == (16 + 34 + 1) + (20 + 45 + 1) + (34 + 47 + 1)


def test_non_ascii_text_is_written_unescaped() -> None:
    (path,) = [p for p in fixture_paths("0.2.1") if p.name == "corpus_score_ms3.json"]
    text = path.read_text(encoding="utf-8")
    assert '"label": "MC 15 → start (MC 1)"' in text
    assert "\\u2192" not in text


def test_number_corpus() -> None:
    assert dumps(json.loads(NUMBER_CORPUS)) == NUMBER_CORPUS_TEXT


def test_canonical_order_copies_and_reorders_manifests_and_envelopes_only() -> None:
    (path,) = [p for p in fixture_paths("0.2.0") if p.name == "conversion_maps.json"]
    envelope = json.loads(path.read_text(encoding="utf-8"))
    text = json.dumps(envelope)
    ordered = canonical_order(envelope)
    assert json.dumps(envelope) == text
    assert list(ordered["manifest"]["timelines"]) == [
        "maps:quarters",
        "maps:samples",
        "maps:seconds",
        "maps:ticks",
    ]
    assert json.dumps(canonical_order(ordered)) == json.dumps(ordered)
    manifest = json.loads(
        next(
            path
            for path in fixture_paths("0.4.0")
            if path.name == "continuous_logical.json"
        ).read_text(encoding="utf-8")
    )
    assert dumps(canonical_order(manifest)) == dumps(manifest)
    value = {"b": [3, 1], "a": {"manifest": 1}}
    assert json.dumps(canonical_order(value)) == json.dumps(value)


@pytest.mark.parametrize(
    "value", ["\ud800", {"\udfff": 1}, math.nan, math.inf], ids=repr
)
def test_values_the_writer_refuses(value) -> None:
    with pytest.raises(ValueError):
        dumps([value])
    with pytest.raises(ValueError):
        canonical_json([value])


def test_an_unorderable_collection_is_refused() -> None:
    envelope = {"manifest": {"timelines": {"a": {"regions": [{"name": "r"}] * 2}}}}
    with pytest.raises(ValueError, match="cannot put regions in canonical order"):
        dumps(envelope)
