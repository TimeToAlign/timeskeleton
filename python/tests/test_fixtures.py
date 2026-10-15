from __future__ import annotations

import json
from pathlib import Path

import pytest

from timeskeleton import (
    complete,
    dumps,
    fixture_paths,
    minimal,
    unknown_keys,
    validate,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPOSITORY_ROOT / "fixtures" / "0.7.0"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_fixture_paths_list_every_manifest_but_the_drawings() -> None:
    expected = sorted(
        path
        for path in FIXTURES.rglob("*.json")
        if "drawings" not in path.relative_to(FIXTURES).parts
    )
    assert fixture_paths() == expected
    assert expected


@pytest.mark.parametrize(
    "path", fixture_paths(), ids=lambda path: str(path.relative_to(FIXTURES))
)
def test_every_fixture_is_a_manifest_without_unknown_keys(path: Path) -> None:
    value = _load(path)
    validate(value)
    assert unknown_keys(value) == []
    assert dumps(minimal(complete(value))) == dumps(minimal(value))
    assert dumps(complete(minimal(value))) == dumps(complete(value))


def test_non_ascii_text_is_written_unescaped() -> None:
    text = (FIXTURES / "corpus_score_ms3.json").read_text(encoding="utf-8")
    assert '"label": "MC 15 → start (MC 1)"' in text
    assert "\\u2192" not in text


_GREY = {"stroke": "#404040", "fill": "#404040"}
_SHARED = [
    {"select": {"element": "label"}, "set": _GREY},
    {"select": {"element": "name"}, "set": _GREY},
    {"select": {"element": "map"}, "set": {"side": "below"}},
    {"select": {"ids": ["a"]}, "set": {"display": "none"}},
]
_STYLED_SCORE = {
    "styles": {
        "accent": {
            "stroke": "#1D4ED8",
            "fill": "#1D4ED8",
            "stroke-width": 4,
            "opacity": 0.8,
        }
    },
    "statements": [
        *_SHARED,
        {"select": {"element": "block"}, "set": {"rx": 4}},
        {
            "select": {"class": "ContinuousLogicalTimeline", "element": "timeline"},
            "set": "accent",
        },
        {
            "select": {"class": "QuartersToTicks"},
            "set": {"stroke": "#7C3AED", "stroke-width": 1.5},
        },
        {
            "select": {"element": "map", "modality": "discrete"},
            "set": {"stroke-dasharray": "4 2"},
        },
        {"select": {"element": "region"}, "set": {"stroke": "#800000"}},
        {"select": {"element": "region"}, "set": {"stroke": "#0F766E"}},
        {
            "select": {"element": "jump", "domain": "logical"},
            "set": {"stroke": "#DB2777", "fill": "#DB2777", "stroke-width": 2},
        },
        {
            "select": {"element": "wedge", "within": "score"},
            "set": {"side": "above", "stroke": "#65A30D", "fill": "#65A30D"},
        },
        {
            "select": {"ids": ["score/end"]},
            "set": {"stroke": "#B45309", "fill": "#B45309"},
        },
        {
            "select": {"element": "child", "within": "score"},
            "set": {"display": "inline"},
        },
        {
            "select": {"element": "child", "within": "b"},
            "set": {"stroke": "#EA580C", "fill": "#EA580C"},
        },
        {
            "select": {"element": "label", "within": "score"},
            "set": {"fill": "#4D7C0F", "font-size": 10},
        },
        {"select": {"ids": ["score/end/label"]}, "set": {"fill": "#A16207"}},
        {"select": {"ids": ["score/intro/label"]}, "set": {"fill": "#0E7490"}},
        {"select": {"ids": ["score/da-capo/label"]}, "set": {"fill": "#9D174D"}},
        {
            "select": {"ids": ["score/name"]},
            "set": {
                "fill": "#111827",
                "font-size": 12,
                "content": "Styled score",
                "max-width": 120,
            },
        },
        {"select": {"element": "name", "within": "b"}, "set": {"fill": "#0369A1"}},
    ],
}


def _styled(name: str) -> dict:
    return _load(FIXTURES / name)["graphical"]


def test_the_styled_manifests_carry_their_statements() -> None:
    expected = {
        "styled__score.json": _STYLED_SCORE,
        "styled__performance.json": {
            "statements": [
                *_SHARED,
                {
                    "select": {
                        "element": "wedge",
                        "domain": "physical",
                        "within": "performance",
                    },
                    "set": {"stroke": "#7F00FF", "fill": "#7F00FF"},
                },
            ],
        },
    }
    for name, block in expected.items():
        styled = _styled(name)
        assert styled["statements"] == block["statements"]
        assert styled["styles"] == block.get("styles", {})
    assert [len(value["statements"]) for value in expected.values()] == [21, 5]


# The drawn elements and texts of styled__score: (type, address, timeline it
# belongs to, class, domain, modality, parent address). The map's domain and
# modality are those of its target unit, ticks.
_LOGICAL = ("ContinuousLogicalTimeline", "logical", "continuous")
_SCORE_ELEMENTS = [
    ("timeline", "score", "score", *_LOGICAL, None),
    ("child", "b", "b", *_LOGICAL, "score"),
    ("map", "score/ticks", "score", "QuartersToTicks", "logical", "discrete", "score"),
    ("region", "score/intro", "score", *_LOGICAL, "score"),
    ("jump", "score/da-capo", "score", *_LOGICAL, "score"),
    ("wedge", "score/start", "score", *_LOGICAL, "score"),
    ("wedge", "score/end", "score", *_LOGICAL, "score"),
    ("name", "score/name", "score", *_LOGICAL, "score"),
    ("name", "b/name", "b", *_LOGICAL, "b"),
    ("label", "score/start/label", "score", *_LOGICAL, "score/start"),
    ("label", "score/end/label", "score", *_LOGICAL, "score/end"),
    ("label", "score/intro/label", "score", *_LOGICAL, "score/intro"),
    ("label", "score/da-capo/label", "score", *_LOGICAL, "score/da-capo"),
]
_ANCESTRY = {"score": ["score"], "b": ["b", "score"]}
_DEPTH = {"score": 1, "b": 2}


def _resolve(graphical: dict, element: tuple, prop: str) -> str:
    """Return the value the manifest's own statements give ``prop``.

    Ranks follow docs/drawing.md section 2.5 within one layer: ids, depth of
    within, class, element, the count of domain and modality, position. An
    inherited property no statement sets is taken from the parent.
    """
    kind, address, owner, cls, domain, modality, parent = element
    ranked = []
    for position, statement in enumerate(graphical["statements"]):
        select = statement["select"]
        declaration = statement["set"]
        if isinstance(declaration, str):
            declaration = graphical["styles"][declaration]
        if prop not in declaration:
            continue
        if any(
            (key == "element" and value != kind)
            or (key == "ids" and address not in value)
            or (key == "class" and value != cls)
            or (key == "domain" and value != domain)
            or (key == "modality" and value != modality)
            or (key == "within" and value not in _ANCESTRY[owner])
            for key, value in select.items()
        ):
            continue
        rank = (
            "ids" in select,
            _DEPTH[select["within"]] if "within" in select else 0,
            "class" in select,
            "element" in select,
            ("domain" in select) + ("modality" in select),
            position,
        )
        ranked.append((rank, declaration[prop]))
    if ranked:
        return max(ranked)[1]
    assert parent is not None, (address, prop)
    (parent_element,) = [e for e in _SCORE_ELEMENTS if e[1] == parent]
    return _resolve(graphical, parent_element, prop)


def test_every_styled_score_item_has_its_own_colour() -> None:
    graphical = _styled("styled__score.json")
    painted = {"name": "fill", "label": "fill", "wedge": "fill"}
    colours = {
        element[1]: _resolve(graphical, element, painted.get(element[0], "stroke"))
        for element in _SCORE_ELEMENTS
    }
    assert colours == {
        "score": "#1D4ED8",
        "b": "#EA580C",
        "score/ticks": "#7C3AED",
        "score/intro": "#0F766E",
        "score/da-capo": "#DB2777",
        "score/start": "#65A30D",
        "score/end": "#B45309",
        "score/name": "#111827",
        "b/name": "#0369A1",
        "score/start/label": "#4D7C0F",
        "score/end/label": "#A16207",
        "score/intro/label": "#0E7490",
        "score/da-capo/label": "#9D174D",
    }
    assert len(set(colours.values())) == 13
    for element in _SCORE_ELEMENTS:
        if element[0] in {"timeline", "child", "jump", "wedge"}:
            assert _resolve(graphical, element, "fill") == colours[element[1]]


def test_every_styled_score_item_is_visible() -> None:
    graphical = _styled("styled__score.json")
    declarations = [
        (statement["select"], statement["set"])
        for statement in graphical["statements"]
        if isinstance(statement["set"], dict)
    ] + [(None, style) for style in graphical["styles"].values()]
    for select, declaration in declarations:
        assert declaration.get("stroke-width", 1) > 0
        assert declaration.get("opacity", 1) >= 0.5
        if declaration.get("display") == "none":
            assert select == {"ids": ["a"]}
    content = [
        select for select, declaration in declarations if "content" in declaration
    ]
    assert content == [{"ids": ["score/name"]}]
