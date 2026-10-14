from __future__ import annotations

import copy
from typing import Any

import pytest

from timeskeleton import SchemaValidationError, identity_problems, validate


def _problems(value: dict[str, Any]) -> list[tuple[tuple[str | int, ...], str]]:
    return [(problem.path, problem.message) for problem in identity_problems(value)]


def _jump(target: str) -> dict[str, Any]:
    def at(value: int) -> dict[str, Any]:
        return {"unit": "quarters", "number_type": "fraction", "value": [value, 1]}

    return {
        "id": "jump_1",
        "from_coordinate": at(4),
        "to_coordinate": at(0),
        "control_type": "repeat_end",
        "condition": "always",
        "repeat_count": 1,
        "target": target,
        "label": None,
        "meta": {},
    }


def _marker(identifier: str) -> dict[str, Any]:
    coordinate = {"unit": "quarters", "number_type": "fraction", "value": [1, 1]}
    return {"id": identifier, "name": None, "coordinate": coordinate}


def test_the_test_documents_have_no_problem(group_document, bundle_document) -> None:
    assert identity_problems(group_document) == []
    assert identity_problems(bundle_document) == []


def test_elements_of_different_roots_may_share_an_id(bundle_document) -> None:
    for root in bundle_document["timelines"][:2]:
        root["flow_control"]["markers"] = [_marker("m")]
    assert identity_problems(bundle_document) == []


def test_each_root_is_its_own_scope(group_document) -> None:
    group_document["timelines"][1]["flow_control"]["jumps"] = [_jump("nowhere")]
    group_document["timelines"][1]["flow_control"]["markers"] = [_marker("recording")]
    assert _problems(group_document) == [
        (
            ("timelines", 1, "flow_control", "markers", 0, "id"),
            "duplicate id 'recording', first at #/timelines/1/id",
        ),
        (
            ("timelines", 1, "flow_control", "jumps", 0, "target"),
            "'nowhere' names no marker of this timeline",
        ),
    ]


PART_WORDS = ("start", "end", "name", "label", "card")


def _quarters(value: int) -> dict[str, Any]:
    return {"unit": "quarters", "number_type": "fraction", "value": [value, 1]}


def _element(kind: str, identifier: str, load_fixture) -> dict[str, Any]:
    """One element of the kind, carrying the id."""
    if kind == "conversion_maps":
        maps = load_fixture("conversion_maps__maps_quarters")["timeline"]
        element = maps["conversion_maps"][0]
    elif kind == "regions":
        element = {"name": "theme", "start": _quarters(2), "end": _quarters(6)}
        element["meta"] = {}
    elif kind == "breaks":
        element = load_fixture("flow_control")["timeline"]["flow_control"]["breaks"][0]
    elif kind == "jumps":
        element = {**_jump("m"), "target": None}
    else:
        element = _marker(identifier)
    return {**element, "id": identifier}


def _place(timeline: dict[str, Any], kind: str, element: dict[str, Any]) -> tuple:
    """Put the element in the timeline; return the path of its id below it."""
    if kind in ("conversion_maps", "regions"):
        timeline[kind] = [element]
        return (kind, 0, "id")
    timeline["flow_control"][kind] = [element]
    return ("flow_control", kind, 0, "id")


KINDS = ("conversion_maps", "regions", "breaks", "jumps", "markers")


@pytest.mark.parametrize("word", PART_WORDS)
@pytest.mark.parametrize("kind", KINDS)
def test_part_words_are_reserved(
    kind, word, load_fixture, group_document, bundle_document
) -> None:
    for document, index in ((group_document, 1), (bundle_document, 4)):
        root = document["timelines"][index]
        at = _place(root, kind, _element(kind, word, load_fixture))
        assert _problems(document) == [
            (
                ("timelines", index, *at),
                f"id {word!r} is reserved in a group or bundle file",
            )
        ]


def test_what_is_no_part_word(load_fixture, group_document, bundle_document) -> None:
    root = group_document["timelines"][1]
    root["regions"] = [_element("regions", "starts", load_fixture)]
    root["flow_control"]["markers"] = [_marker("Start")]
    assert _problems(group_document) == []
    recording = bundle_document["timelines"][3]
    child = copy.deepcopy(recording["children"]["excerpt"])
    child["timeline"]["id"] = "start"
    child["timeline"]["children"] = {}
    recording["children"]["start"] = child
    assert _problems(bundle_document) == []
    timeline_file = load_fixture("bare")
    region = _element("regions", "label", load_fixture)
    _place(timeline_file["timeline"], "regions", region)
    assert _problems(timeline_file) == []
    validate(timeline_file)


def test_part_words_follow_the_rules_of_every_root(
    load_fixture, group_document
) -> None:
    roots = group_document["timelines"]
    roots[0]["regions"] = [_element("regions", "end", load_fixture)]
    roots[1]["flow_control"]["jumps"] = [_jump("nowhere")]
    assert _problems(group_document) == [
        (
            ("timelines", 1, "flow_control", "jumps", 0, "target"),
            "'nowhere' names no marker of this timeline",
        ),
        (
            ("timelines", 0, "regions", 0, "id"),
            "id 'end' is reserved in a group or bundle file",
        ),
    ]


def test_timeline_ids_are_unique_across_the_file(bundle_document) -> None:
    roots = bundle_document["timelines"]
    roots[4]["children"]["excerpt"] = copy.deepcopy(roots[3]["children"]["excerpt"])
    roots[2]["id"] = "page"
    bundle_document["bundle"]["groups"][0]["members"] = ["page", "score"]
    del bundle_document["graphical"]
    assert _problems(bundle_document) == [
        (("timelines", 2, "id"), "duplicate id 'page', first at #/timelines/1/id"),
        (
            ("timelines", 4, "children", "excerpt", "timeline", "id"),
            "duplicate id 'excerpt', first at "
            "#/timelines/3/children/excerpt/timeline/id",
        ),
        (
            ("bundle", "groups", 1, "members", 1),
            "duplicate member 'page', first at #/bundle/groups/0/members/0",
        ),
    ]


def test_a_repetition_within_one_root_is_reported_once(group_document) -> None:
    child = group_document["timelines"][0]["children"]["second-half"]["timeline"]
    child["id"] = "piece"
    group_document["group"]["members"] = ["piece", "recording"]
    group_document["graphical"]["order"] = ["piece", "recording"]
    assert _problems(group_document) == [
        (
            ("timelines", 0, "children", "second-half", "timeline", "id"),
            "duplicate id 'piece', first at #/timelines/0/id",
        )
    ]


def test_group_ids(group_document, bundle_document) -> None:
    group_document["group"]["id"] = "second-half"
    assert _problems(group_document) == [
        (
            ("group", "id"),
            "duplicate id 'second-half', first at "
            "#/timelines/0/children/second-half/timeline/id",
        )
    ]
    groups = bundle_document["bundle"]["groups"]
    groups[0]["id"] = "score"
    groups[1]["id"] = "score"
    bundle_document["graphical"]["order"] = {"score": ["score", "performance"]}
    assert _problems(bundle_document) == [
        (
            ("bundle", "groups", 0, "id"),
            "duplicate id 'score', first at #/timelines/4/id",
        ),
        (
            ("bundle", "groups", 1, "id"),
            "duplicate id 'score', first at #/timelines/4/id",
        ),
    ]


def test_a_group_id_repeating_a_group_id(bundle_document) -> None:
    bundle_document["bundle"]["groups"][1]["id"] = "group_1"
    del bundle_document["graphical"]["order"]["group_2"]
    assert _problems(bundle_document) == [
        (
            ("bundle", "groups", 1, "id"),
            "duplicate id 'group_1', first at #/bundle/groups/0/id",
        )
    ]


@pytest.mark.parametrize(
    ("identifier", "first"),
    [
        ("annotations", "#/timelines/0/id"),
        ("excerpt", "#/timelines/3/children/excerpt/timeline/id"),
        ("group_2", "#/bundle/groups/1/id"),
    ],
)
def test_the_bundle_id_differs_from_every_timeline_and_group_id(
    identifier: str, first: str, bundle_document
) -> None:
    bundle_document["bundle"]["id"] = identifier
    expected = [(("bundle", "id"), f"duplicate id {identifier!r}, first at {first}")]
    assert _problems(bundle_document) == expected
    with pytest.raises(SchemaValidationError) as caught:
        validate(bundle_document)
    assert (caught.value.path, caught.value.message) == expected[0]


def test_a_bundle_id_names_the_timeline_before_a_group(bundle_document) -> None:
    bundle_document["bundle"]["id"] = "score"
    bundle_document["bundle"]["groups"][1]["id"] = "score"
    bundle_document["graphical"]["order"] = {"group_1": ["score", "performance"]}
    assert _problems(bundle_document) == [
        (
            ("bundle", "groups", 1, "id"),
            "duplicate id 'score', first at #/timelines/4/id",
        ),
        (("bundle", "id"), "duplicate id 'score', first at #/timelines/4/id"),
    ]


def test_a_bundle_id_names_the_first_group_carrying_it(bundle_document) -> None:
    bundle_document["bundle"]["id"] = "group_1"
    bundle_document["bundle"]["groups"][1]["id"] = "group_1"
    del bundle_document["graphical"]["order"]["group_2"]
    assert _problems(bundle_document) == [
        (
            ("bundle", "groups", 1, "id"),
            "duplicate id 'group_1', first at #/bundle/groups/0/id",
        ),
        (("bundle", "id"), "duplicate id 'group_1', first at #/bundle/groups/0/id"),
    ]


def test_members_name_timelines_of_the_file(group_document, bundle_document) -> None:
    group_document["group"]["members"] = ["recording", "second-half", "tempo"]
    group_document["graphical"]["order"].append("tempo")
    assert _problems(group_document) == [
        (("group", "members", 2), "'tempo' names no timeline of this file")
    ]
    bundle_document["bundle"]["groups"][1]["members"] = ["excerpt", "page", "score"]
    bundle_document["graphical"]["order"]["group_2"].append("score")
    assert _problems(bundle_document) == [
        (
            ("bundle", "groups", 1, "members", 2),
            "duplicate member 'score', first at #/bundle/groups/0/members/1",
        )
    ]


def test_no_member_nests_with_another_member_of_its_group(
    group_document, bundle_document
) -> None:
    group_document["group"]["members"] = ["piece", "recording", "second-half"]
    group_document["graphical"]["order"].append("piece")
    assert _problems(group_document) == [
        (
            ("group", "members", 2),
            "member 'second-half' lies inside member 'piece' of the same group",
        )
    ]
    groups = bundle_document["bundle"]["groups"]
    groups[1]["members"] = ["excerpt", "page", "recording", "tempo"]
    bundle_document["graphical"]["order"]["group_2"] += ["recording", "tempo"]
    assert _problems(bundle_document) == [
        (
            ("bundle", "groups", 1, "members", 2),
            "member 'recording' contains member 'excerpt' of the same group",
        ),
        (
            ("bundle", "groups", 1, "members", 3),
            "'tempo' names no timeline of this file",
        ),
    ]


def test_a_member_of_two_groups_is_checked_in_each(bundle_document) -> None:
    groups = bundle_document["bundle"]["groups"]
    groups[0]["members"] = ["excerpt", "performance", "score"]
    groups[1]["members"] = ["excerpt", "page", "recording"]
    bundle_document["graphical"]["order"] = {}
    assert _problems(bundle_document) == [
        (
            ("bundle", "groups", 1, "members", 0),
            "duplicate member 'excerpt', first at #/bundle/groups/0/members/0",
        ),
        (
            ("bundle", "groups", 1, "members", 2),
            "member 'recording' contains member 'excerpt' of the same group",
        ),
    ]


def test_a_parent_and_its_child_may_lie_in_different_groups(bundle_document) -> None:
    groups = bundle_document["bundle"]["groups"]
    groups[0]["members"] = ["performance", "recording", "score"]
    bundle_document["graphical"]["order"]["group_1"].append("recording")
    assert identity_problems(bundle_document) == []
    validate(bundle_document)


def test_every_root_of_a_group_file_contains_a_member(group_document) -> None:
    group_document["group"]["members"] = ["second-half"]
    group_document["graphical"]["order"] = ["second-half"]
    assert _problems(group_document) == [
        (("timelines", 1), "timeline 'recording' contains no member of the group")
    ]


def test_a_bundle_root_needs_no_member(bundle_document) -> None:
    bundle_document["bundle"]["groups"] = []
    bundle_document["graphical"]["order"] = {}
    assert identity_problems(bundle_document) == []


@pytest.mark.parametrize(
    ("order", "expected"),
    [
        (
            ["second-half"],
            [
                (
                    ("graphical", "order"),
                    "member 'recording' of group 'group_1' is missing",
                )
            ],
        ),
        (
            ["second-half", "piece", "recording"],
            [(("graphical", "order", 1), "'piece' is not a member of group 'group_1'")],
        ),
        (
            ["piece"],
            [
                (
                    ("graphical", "order", 0),
                    "'piece' is not a member of group 'group_1'",
                ),
                (
                    ("graphical", "order"),
                    "member 'recording' of group 'group_1' is missing",
                ),
                (
                    ("graphical", "order"),
                    "member 'second-half' of group 'group_1' is missing",
                ),
            ],
        ),
    ],
)
def test_a_group_order_is_a_permutation(order, expected, group_document) -> None:
    group_document["graphical"]["order"] = order
    assert _problems(group_document) == expected


def test_an_absent_order_is_no_problem(group_document, bundle_document) -> None:
    del group_document["graphical"]
    del bundle_document["graphical"]["order"]["group_2"]
    assert identity_problems(group_document) == []
    assert identity_problems(bundle_document) == []
    del bundle_document["graphical"]
    assert identity_problems(bundle_document) == []


def test_bundle_orders_are_visited_by_key(bundle_document) -> None:
    orders = bundle_document["graphical"]["order"]
    orders["\U0001f600"] = []
    orders["ﬀ"] = []
    orders["group_2"] = ["page"]
    assert _problems(bundle_document) == [
        (
            ("graphical", "order", "group_2"),
            "member 'excerpt' of group 'group_2' is missing",
        ),
        (("graphical", "order", "ﬀ"), "'ﬀ' names no group of this bundle"),
        (
            ("graphical", "order", "\U0001f600"),
            "'\U0001f600' names no group of this bundle",
        ),
    ]


def test_the_problems_come_in_the_stated_order(load_fixture, bundle_document) -> None:
    roots = bundle_document["timelines"]
    roots[0]["flow_control"]["jumps"] = [_jump("nowhere")]
    roots[0]["regions"] = [_element("regions", "end", load_fixture)]
    roots[1]["id"] = "annotations"
    bundle_document["bundle"]["id"] = "group_2"
    groups = bundle_document["bundle"]["groups"]
    groups[0]["id"] = "recording"
    groups[0]["members"] = ["performance", "score", "tempo"]
    groups[1]["members"] = ["excerpt", "score"]
    bundle_document["graphical"]["order"] = {
        "group_9": [],
        "group_2": ["excerpt", "page", "score"],
    }
    assert _problems(bundle_document) == [
        (
            ("timelines", 0, "flow_control", "jumps", 0, "target"),
            "'nowhere' names no marker of this timeline",
        ),
        (
            ("timelines", 0, "regions", 0, "id"),
            "id 'end' is reserved in a group or bundle file",
        ),
        (
            ("timelines", 1, "id"),
            "duplicate id 'annotations', first at #/timelines/0/id",
        ),
        (
            ("bundle", "groups", 0, "id"),
            "duplicate id 'recording', first at #/timelines/3/id",
        ),
        (("bundle", "id"), "duplicate id 'group_2', first at #/bundle/groups/1/id"),
        (
            ("bundle", "groups", 0, "members", 2),
            "'tempo' names no timeline of this file",
        ),
        (
            ("bundle", "groups", 1, "members", 1),
            "duplicate member 'score', first at #/bundle/groups/0/members/1",
        ),
        (
            ("graphical", "order", "group_2", 1),
            "'page' is not a member of group 'group_2'",
        ),
        (("graphical", "order", "group_9"), "'group_9' names no group of this bundle"),
    ]
    with pytest.raises(SchemaValidationError) as caught:
        validate(bundle_document)
    assert caught.value.path == ("timelines", 0, "flow_control", "jumps", 0, "target")


STYLED = {
    "styles": {"frame": {"stroke": "#7F00FF"}},
    "statements": [
        {"select": {"element": "group"}, "set": "frame"},
        {"select": {"element": "boundary"}, "set": {"stroke-width": 2}},
        {"select": {"element": "ancestor", "ids": ["piece"]}, "set": {"opacity": 0.5}},
    ],
}


def test_group_and_bundle_files_take_styles_and_statements(
    group_document, bundle_document
) -> None:
    for document in (group_document, bundle_document):
        document["graphical"].update(copy.deepcopy(STYLED))
        validate(document)


@pytest.mark.parametrize("kind", ["group", "bundle"])
def test_an_unknown_graphical_member_is_refused(
    kind: str, group_document, bundle_document
) -> None:
    document = group_document if kind == "group" else bundle_document
    document["graphical"]["arrangement"] = {}
    with pytest.raises(SchemaValidationError) as caught:
        validate(document)
    assert caught.value.path == ("graphical",)


def test_a_bundle_style_takes_the_declaration_of_a_timeline_file(
    bundle_document,
) -> None:
    bundle_document["graphical"]["styles"] = {"frame": {"colour": "#7F00FF"}}
    with pytest.raises(SchemaValidationError) as caught:
        validate(bundle_document)
    assert caught.value.path == ("graphical", "styles", "frame")


def test_0_6_0_knows_ten_element_types(load_fixture) -> None:
    manifest = load_fixture("bare", "0.6.0")
    manifest["graphical"] = {
        "statements": [{"select": {"element": "group"}, "set": {"fill": "#7F00FF"}}]
    }
    with pytest.raises(SchemaValidationError) as caught:
        validate(manifest)
    assert caught.value.path == ("graphical", "statements", 0, "select", "element")
