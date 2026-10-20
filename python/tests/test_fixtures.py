from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pytest

from timeskeleton import (
    complete,
    dumps,
    fixture_paths,
    identity_problems,
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
        {"select": {"ids": ["a"]}, "set": {"display": "none"}},
        {"select": {"element": "block"}, "set": {"rx": 4}},
        {
            "select": {"class": "ContinuousLogicalTimeline", "element": "timeline"},
            "set": "accent",
        },
        {
            "select": {"class": "LinearMap"},
            "set": {"stroke": "#7C3AED", "stroke-width": 1.5},
        },
        {
            "select": {"element": "map", "modality": "discrete"},
            "set": {"stroke-dasharray": "4 2"},
        },
        {"select": {"element": "region"}, "set": {"stroke": "#800000"}},
        {"select": {"element": "region"}, "set": {"stroke": "#0F766E"}},
        {
            "select": {"element": "jump_from", "domain": "logical"},
            "set": {"stroke": "#DB2777", "fill": "#DB2777", "stroke-width": 2},
        },
        {
            "select": {"element": "wedge", "within": "score"},
            "set": {"stroke": "#65A30D", "fill": "#65A30D"},
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
    "order": {
        "score": [
            "score/children_1",
            "score/markers_1",
            "score",
            "score/conversion_maps_1",
            "score/regions_1",
            "score/flow_control_1",
        ]
    },
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
        assert styled["order"] == block.get("order", {})
    assert [len(value["statements"]) for value in expected.values()] == [20, 3]


# The drawn elements and texts of styled__score: (type, address, timeline it
# belongs to, class, domain, modality, parent address). The map's domain and
# modality are those of its target unit, ticks.
_LOGICAL = ("ContinuousLogicalTimeline", "logical", "continuous")
_SCORE_ELEMENTS = [
    ("timeline", "score", "score", *_LOGICAL, None),
    ("child", "b", "b", *_LOGICAL, "score"),
    ("map", "score/ticks", "score", "LinearMap", "logical", "discrete", "score"),
    ("region", "score/intro", "score", *_LOGICAL, "score"),
    ("jump_from", "score/da-capo", "score", *_LOGICAL, "score"),
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
        if element[0] in {"timeline", "child", "jump_from", "wedge"}:
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


@pytest.mark.parametrize(
    "name", ["bundle_shared_member.json", "bundle_shared_member.minimal.json"]
)
def test_a_timeline_in_two_groups_passes_every_rule(name: str) -> None:
    value = _load(FIXTURES / "bundles" / name)
    assert [(group["id"], group["members"]) for group in value["groups"]] == [
        ("g1", ["t", "u"]),
        ("g2", ["t", "v"]),
    ]
    validate(value)
    assert identity_problems(value) == []


def _flow_control(timeline: dict) -> list[tuple[str, str]]:
    elements = [
        (element["type"], element["id"]) for element in timeline.get("flow_control", [])
    ]
    for child in timeline.get("children", []):
        elements += _flow_control(child)
    return elements


def test_generated_flow_control_ids_carry_their_type() -> None:
    elements = [
        element
        for path in fixture_paths()
        if not path.name.endswith(".minimal.json")
        for root in _load(path)["timelines"]
        for element in _flow_control(root)
    ]
    generated = Counter(
        (kind, element_id)
        for kind, element_id in elements
        if re.fullmatch(r"[a-z_]+_[1-9][0-9]*", element_id)
    )
    assert all(element_id.startswith(f"{kind}_") for kind, element_id in generated)
    assert generated == {
        ("flow_marker", "flow_marker_1"): 3,
        ("jump_from", "jump_from_1"): 6,
        ("jump_from", "jump_from_2"): 2,
        ("jump_from", "jump_from_3"): 1,
        ("jump_from", "jump_from_4"): 1,
        ("jump_to", "jump_to_1"): 3,
        ("jump_to", "jump_to_2"): 2,
        ("jump_to", "jump_to_3"): 1,
    }
    assert {element_id for kind, element_id in elements} - {
        element_id for kind, element_id in generated
    } == {"fine", "da-capo", "da_capo_al_fine", "dal_segno", "repeat", "segno"}
