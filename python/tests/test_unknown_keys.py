from __future__ import annotations

import json
from importlib import import_module
from pathlib import Path

import pytest

from timeskeleton import (
    SchemaValidationError,
    UnsupportedVersionError,
    dumps,
    unknown_keys,
    validate,
    warning_paths,
)

from .conftest import group, manifest, timeline

WARNINGS = [
    "combination_map_names",
    "declaration_show_projections",
    "declaration_unknown_key",
    "graphical_unknown_key",
    "group_unknown_key",
    "measure_map_row_offset_key",
    "measure_map_row_unknown_key",
    "selector_unknown_key",
    "several_depths",
    "support_policy",
    "timeline_class",
]


def test_the_warning_cases_are_stated() -> None:
    assert [path.stem for path in warning_paths()] == WARNINGS


@pytest.mark.parametrize("path", warning_paths(), ids=lambda path: path.stem)
def test_each_warning_case_lists_its_unknown_keys(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    case = json.loads(text)
    assert sorted(case) == ["manifest", "unknown_keys"]
    assert dumps(case) == text
    validate(case["manifest"])
    assert unknown_keys(case["manifest"]) == case["unknown_keys"]


def test_unknown_keys_at_several_depths() -> None:
    (path,) = [p for p in warning_paths() if p.stem == "several_depths"]
    expected = json.loads(path.read_text(encoding="utf-8"))["unknown_keys"]
    assert [(entry["path"], entry["key"]) for entry in expected] == [
        ([], "x-editor"),
        (["graphical"], "arrangement"),
        (["graphical", "statements", 0], "comment"),
        (["graphical", "statements", 0, "select"], "kind"),
        (["graphical", "statements", 0, "set"], "colour"),
        (["groups", 0], "colour"),
        (["measure_maps", 0], "source"),
        (["measure_maps", 0, "rows", 0], "tempo"),
        (["timelines", 0], "lenght"),
        (["timelines", 0, "children", 0], "x-tilia"),
        (["timelines", 0, "conversion_maps", 0], "note"),
        (["timelines", 0, "conversion_maps", 0, "maps", 0], "note"),
        (["timelines", 0, "flow_control", 0], "glyph"),
        (["timelines", 0, "flow_control", 1], "via"),
        (["timelines", 0, "flow_control", 2], "pause"),
        (["timelines", 0, "regions", 0], "colour"),
    ]


def test_free_objects_maps_and_unknown_values_are_not_looked_into() -> None:
    value = manifest(
        timeline(
            "score",
            meta={"anything": {"deep": 1}},
            regions=[{"id": "r", "start": [0, 1], "end": [1, 1], "meta": {"x": 1}}],
        ),
        meta={"source": "hand"},
        groups=[group("g", "score", meta={"note": 1})],
        graphical={
            "styles": {"any-name": {"stroke": "#000000"}},
            "order": {"g": ["score"]},
            "statements": [{"select": {}, "set": "any-name"}],
        },
    )
    assert unknown_keys(value) == []
    value["x"] = {"inner": {"also": 1}}
    assert unknown_keys(value) == [{"path": [], "key": "x"}]


def test_side_is_no_property() -> None:
    statement = {
        "select": {"element": "map"},
        "set": {"fill": "#000000", "side": "above"},
    }
    value = manifest(
        timeline("score"),
        graphical={"styles": {"below": {"side": "below"}}, "statements": [statement]},
    )
    validate(value)
    assert unknown_keys(value) == [
        {"path": ["graphical", "statements", 0, "set"], "key": "side"},
        {"path": ["graphical", "styles", "below"], "key": "side"},
    ]


def test_unknown_keys_are_sorted() -> None:
    roots = [timeline(f"t{index}") for index in range(11)]
    roots[2]["zz"] = 1
    roots[10]["zz"] = 1
    value = manifest(*roots, zz=1, aa=1, **{"ﬀ": 1, "\U0001f600": 1})
    assert unknown_keys(value) == [
        {"path": [], "key": "aa"},
        {"path": [], "key": "zz"},
        {"path": [], "key": "ﬀ"},
        {"path": [], "key": "\U0001f600"},
        {"path": ["timelines", 2], "key": "zz"},
        {"path": ["timelines", 10], "key": "zz"},
    ]


def test_an_invalid_value_raises_before_any_key_is_listed() -> None:
    with pytest.raises(SchemaValidationError):
        unknown_keys(manifest(timeline("score", length=32), extra=1))
    with pytest.raises(UnsupportedVersionError):
        unknown_keys({"timeskeleton": "9.9.9", "extra": 1})


def test_unknown_keys_uses_one_schema_walk(monkeypatch: pytest.MonkeyPatch) -> None:
    module = import_module("timeskeleton.validate")
    validator = module._marking_validator()
    calls = 0

    class CountingValidator:
        def iter_errors(self, value: object):
            nonlocal calls
            calls += 1
            return validator.iter_errors(value)

    monkeypatch.setattr(module, "_marking_validator", lambda: CountingValidator())
    value = manifest(timeline("score"), extra=True)
    assert unknown_keys(value) == [{"path": [], "key": "extra"}]
    assert calls == 1
