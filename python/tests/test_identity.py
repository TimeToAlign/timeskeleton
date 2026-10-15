from __future__ import annotations

import copy
import json

import pytest

from timeskeleton import (
    SchemaValidationError,
    identity_problems,
    rejection_paths,
    validate,
)

from .conftest import bundle, group, manifest, timeline


def _problems(value: dict) -> list[tuple[tuple[str | int, ...], str]]:
    return [(problem.path, problem.message) for problem in identity_problems(value)]


def _only(value: dict) -> tuple[tuple[str | int, ...], str]:
    (problem,) = _problems(value)
    with pytest.raises(SchemaValidationError) as caught:
        validate(value)
    assert (caught.value.path, caught.value.message) == problem
    return problem


def _markers(*identifiers: str) -> dict:
    return {
        "markers": [{"id": i, "coordinate": [k, 1]} for k, i in enumerate(identifiers)]
    }


def test_the_bundle_document_has_no_problem() -> None:
    assert _problems(bundle()) == []
    validate(bundle())


def test_a_repeated_id_within_a_root_is_reported_at_its_later_occurrence() -> None:
    child = timeline("c", offset=(0, 1), flow_control=_markers("m"))
    root = timeline("bare", flow_control=_markers("m", "m", "bare"), children=[child])
    assert _problems(manifest(root)) == [
        (
            ("timelines", 0, "flow_control", "markers", 1, "id"),
            "duplicate id 'm', first at #/timelines/0/flow_control/markers/0/id",
        ),
        (
            ("timelines", 0, "flow_control", "markers", 2, "id"),
            "duplicate id 'bare', first at #/timelines/0/id",
        ),
        (
            ("timelines", 0, "children", 0, "flow_control", "markers", 0, "id"),
            "duplicate id 'm', first at #/timelines/0/flow_control/markers/0/id",
        ),
    ]


def test_scopes_are_per_root() -> None:
    validate(
        manifest(
            timeline("a", flow_control=_markers("m")),
            timeline("b", flow_control=_markers("m")),
        )
    )
    score = timeline("score", regions=[{"id": "perf", "start": [0, 1], "end": [1, 1]}])
    take = timeline("take", children=[timeline("perf", offset=(0, 1))])
    validate(manifest(score, take))


def test_targets_stay_within_their_timeline() -> None:
    def jump(identifier: str, target: str | None) -> dict:
        return {
            "id": identifier,
            "from_coordinate": [4, 1],
            "to_coordinate": [0, 1],
            "target": target,
        }

    child = timeline(
        "c",
        offset=(0, 1),
        flow_control={
            "markers": [{"id": "there", "coordinate": [1, 1]}],
            "jumps": [jump("cj", "here")],
        },
    )
    root = timeline(
        "bare",
        flow_control={
            "markers": [{"id": "here", "coordinate": [1, 1]}],
            "jumps": [jump("j1", "here"), jump("j2", None), jump("j3", "there")],
        },
        children=[child],
    )
    assert _problems(manifest(root)) == [
        (
            ("timelines", 0, "flow_control", "jumps", 2, "target"),
            "'there' names no marker of this timeline",
        ),
        (
            ("timelines", 0, "children", 0, "flow_control", "jumps", 0, "target"),
            "'here' names no marker of this timeline",
        ),
    ]


def test_a_child_shares_its_parents_unit() -> None:
    value = manifest(
        timeline("score", children=[timeline("take", "seconds", 4.0, offset=(2, 1))])
    )
    assert _only(value) == (
        ("timelines", 0, "children", 0, "unit"),
        "child 'take' has unit 'seconds', its parent 'score' has 'quarters'",
    )
    number = timeline("n", "number", (4, 1), offset=(0, 1), number_type="fraction")
    assert _only(manifest(timeline("score", children=[number]))) == (
        ("timelines", 0, "children", 0, "unit"),
        "child 'n' has unit 'number', its parent 'score' has 'quarters'",
    )
    grandchild = timeline("b", "ticks", 4, offset=(1, 1))
    value = manifest(
        timeline(
            "score", children=[timeline("a", offset=(0, 1), children=[grandchild])]
        )
    )
    assert _only(value) == (
        ("timelines", 0, "children", 0, "children", 0, "unit"),
        "child 'b' has unit 'ticks', its parent 'a' has 'quarters'",
    )
    assert (
        _problems(manifest(timeline("score", children=[timeline("c", offset=(0, 1))])))
        == []
    )


def test_a_childs_offset_is_not_negative() -> None:
    value = manifest(
        timeline(
            "recording",
            "seconds",
            60.0,
            children=[timeline("take", "seconds", 4.0, offset=-1.5)],
        )
    )
    assert _only(value) == (
        ("timelines", 0, "children", 0, "offset"),
        "offset -1.5 of 'take' is negative",
    )
    value = manifest(timeline("score", children=[timeline("c", offset=(-1, 1000000))]))
    assert _only(value) == (
        ("timelines", 0, "children", 0, "offset"),
        "offset [-1, 1000000] of 'c' is negative",
    )
    grandchild = timeline("b", offset=(-1, 2))
    value = manifest(
        timeline(
            "score", children=[timeline("a", offset=(0, 1), children=[grandchild])]
        )
    )
    assert _only(value) == (
        ("timelines", 0, "children", 0, "children", 0, "offset"),
        "offset [-1, 2] of 'b' is negative",
    )
    for document in (
        manifest(timeline("score", children=[timeline("c", offset=(0, 1))])),
        manifest(
            timeline(
                "recording",
                "seconds",
                60.0,
                children=[timeline("take", "seconds", 4.0, offset=-0.0)],
            )
        ),
        manifest(timeline("take", "seconds", 2.5, offset=-1700000000.25)),
        manifest(timeline("score", offset=[-3, 2])),
    ):
        assert _problems(document) == []
        validate(document)


def test_a_child_lies_within_its_parents_known_length() -> None:
    def recording(length: float, *children: dict) -> dict:
        return manifest(
            timeline("recording", "seconds", length, children=list(children))
        )

    def take(length: float | None, offset: float) -> dict:
        return timeline("take", "seconds", length, offset=offset)

    assert _only(recording(60.0, take(None, 75.0))) == (
        ("timelines", 0, "children", 0, "offset"),
        "offset 75.0 of 'take' is beyond the length 60.0 of its parent 'recording'",
    )
    score = timeline("score", children=[timeline("c", length=(2, 1), offset=(9, 1))])
    assert _only(manifest(score)) == (
        ("timelines", 0, "children", 0, "offset"),
        "offset [9, 1] of 'c' is beyond the length [8, 1] of its parent 'score'",
    )
    coda = timeline("coda", length=(4, 1), offset=(8, 1))
    assert _only(manifest(timeline("score", length=(10, 1), children=[coda]))) == (
        ("timelines", 0, "children", 0, "length"),
        "child 'coda' ends at [12, 1], beyond the length [10, 1] of its parent 'score'",
    )
    assert _only(recording(0.75, take(0.5, 0.5))) == (
        ("timelines", 0, "children", 0, "length"),
        "child 'take' ends at 1.0, beyond the length 0.75 of its parent 'recording'",
    )
    assert _only(recording(0.3, take(0.2, 0.1))) == (
        ("timelines", 0, "children", 0, "length"),
        "child 'take' ends at [10808639105689191, 36028797018963968], beyond the "
        "length 0.3 of its parent 'recording'",
    )
    midi = timeline(
        "midi", "ticks", 480, children=[timeline("m", "ticks", 240, offset=480)]
    )
    assert _only(manifest(midi)) == (
        ("timelines", 0, "children", 0, "length"),
        "child 'm' ends at 720, beyond the length 480 of its parent 'midi'",
    )
    loose = timeline("f", length=2.5, offset=(7, 1), number_type="float")
    assert _only(manifest(timeline("score", children=[loose]))) == (
        ("timelines", 0, "children", 0, "length"),
        "child 'f' ends at [19, 2], beyond the length [8, 1] of its parent 'score'",
    )
    other = timeline("take", "seconds", 100.0, offset=(2, 1))
    assert _problems(manifest(timeline("score", children=[other]))) == [
        (
            ("timelines", 0, "children", 0, "unit"),
            "child 'take' has unit 'seconds', its parent 'score' has 'quarters'",
        )
    ]
    grandchild = timeline("b", length=(2, 1), offset=(3, 1))
    child = timeline("a", length=(4, 1), offset=(0, 1), children=[grandchild])
    assert _only(manifest(timeline("score", children=[child]))) == (
        ("timelines", 0, "children", 0, "children", 0, "length"),
        "child 'b' ends at [5, 1], beyond the length [4, 1] of its parent 'a'",
    )
    line = timeline(
        "line",
        is_segment_line=True,
        children=[
            timeline("a", length=None, offset=(0, 1)),
            timeline("b", length=(1, 1), offset=(10, 1)),
        ],
    )
    assert _problems(manifest(line)) == [
        (
            ("timelines", 0, "children", 0, "length"),
            "child 'a' ends at [10, 1], beyond the length [8, 1] of its parent 'line'",
        ),
        (
            ("timelines", 0, "children", 1, "offset"),
            "offset [10, 1] of 'b' is beyond the length [8, 1] of its parent 'line'",
        ),
        (
            ("timelines", 0, "length"),
            "the segments of segment line 'line' do not end at its length",
        ),
    ]
    for document in (
        recording(60.0, take(None, 60.0)),
        manifest(
            timeline(
                "score",
                length=(10, 1),
                children=[timeline("c", length=(2, 1), offset=(8, 1))],
            )
        ),
        recording(0.75, take(0.25, 0.5)),
        manifest(
            timeline(
                "score",
                length=None,
                children=[timeline("c", length=(8, 1), offset=(100, 1))],
            )
        ),
    ):
        assert _problems(document) == []
        validate(document)


@pytest.mark.parametrize(
    ("name", "message"),
    [
        (
            "child_unit_differs",
            "child 'take' has unit 'seconds', its parent 'score' has 'quarters'",
        ),
        ("child_offset_negative", "offset -1.5 of 'take' is negative"),
        (
            "child_offset_beyond_parent",
            "offset 75.0 of 'take' is beyond the length 60.0 of its parent 'recording'",
        ),
        (
            "child_end_beyond_parent",
            "child 'coda' ends at [12, 1], beyond the length [10, 1] of its parent "
            "'score'",
        ),
    ],
)
def test_the_shared_child_rejections_carry_their_messages(
    name: str, message: str
) -> None:
    (path,) = [path for path in rejection_paths() if path.stem == name]
    case = json.loads(path.read_text(encoding="utf-8"))
    assert _only(case["manifest"]) == (tuple(case["path"]), message)


def _part_word_documents(word: str) -> list[tuple[dict, tuple[str | int, ...]]]:
    region = {"id": word, "start": [0, 1], "end": [1, 1]}
    shift = {
        "type": "ShiftMap",
        "id": word,
        "source_unit": None,
        "target_unit": None,
        "offset": 1,
    }
    flow = {
        "breaks": [{"id": word, "coordinate": [1, 1]}],
        "jumps": [{"id": word, "from_coordinate": [1, 1], "to_coordinate": [0, 1]}],
        "markers": [{"id": word, "coordinate": [1, 1]}],
    }
    documents = [
        (manifest(timeline(word)), ("timelines", 0, "id")),
        (
            manifest(timeline("s", conversion_maps=[shift])),
            ("timelines", 0, "conversion_maps", 0, "id"),
        ),
        (
            manifest(timeline("s", regions=[region])),
            ("timelines", 0, "regions", 0, "id"),
        ),
        (manifest(timeline("s"), groups=[group(word, "s")]), ("groups", 0, "id")),
        (manifest(timeline("s"), id=word), ("id",)),
    ]
    for member, entries in flow.items():
        documents.append(
            (
                manifest(timeline("s", flow_control={member: entries})),
                ("timelines", 0, "flow_control", member, 0, "id"),
            )
        )
    return documents


@pytest.mark.parametrize("word", ["start", "end", "name", "label", "card"])
def test_part_words_are_no_id_anywhere(word: str) -> None:
    for document, path in _part_word_documents(word):
        assert _only(document) == (
            path,
            f"id '{word}' is reserved for the parts of an address",
        )


@pytest.mark.parametrize("word", ["starts", "Start"])
def test_other_words_are_ids(word: str) -> None:
    for document, _ in _part_word_documents(word):
        validate(document)


def test_timeline_ids_are_unique_across_roots() -> None:
    value = manifest(timeline("piece"), timeline("piece"))
    assert _only(value) == (
        ("timelines", 1, "id"),
        "duplicate id 'piece', first at #/timelines/0/id",
    )
    child = timeline("excerpt", offset=(0, 1))
    value = manifest(
        timeline("a", children=[child]), timeline("b", children=[copy.deepcopy(child)])
    )
    assert _only(value) == (
        ("timelines", 1, "children", 0, "id"),
        "duplicate id 'excerpt', first at #/timelines/0/children/0/id",
    )


def test_a_timeline_id_repeated_within_a_root_is_reported_once() -> None:
    value = manifest(timeline("a", children=[timeline("a", offset=(0, 1))]))
    assert _problems(value) == [
        (
            ("timelines", 0, "children", 0, "id"),
            "duplicate id 'a', first at #/timelines/0/id",
        )
    ]


def test_group_ids() -> None:
    value = manifest(timeline("score"), groups=[group("score")])
    assert _only(value) == (
        ("groups", 0, "id"),
        "duplicate id 'score', first at #/timelines/0/id",
    )
    value = manifest(timeline("score"), groups=[group("g"), group("g")])
    assert _only(value) == (
        ("groups", 1, "id"),
        "duplicate id 'g', first at #/groups/0/id",
    )


def test_the_manifest_id() -> None:
    value = manifest(timeline("score"), id="score")
    assert _only(value) == (("id",), "duplicate id 'score', first at #/timelines/0/id")
    value = manifest(timeline("score"), id="g", groups=[group("g")])
    assert _only(value) == (("id",), "duplicate id 'g', first at #/groups/0/id")
    value = manifest(timeline("g"), id="g", groups=[group("g")])
    assert _problems(value) == [
        (("groups", 0, "id"), "duplicate id 'g', first at #/timelines/0/id"),
        (("id",), "duplicate id 'g', first at #/timelines/0/id"),
    ]


def test_members() -> None:
    value = manifest(timeline("score"), groups=[group("g", "tempo")])
    assert _only(value) == (
        ("groups", 0, "members", 0),
        "'tempo' names no timeline of this manifest",
    )
    value = manifest(
        timeline("a"), timeline("b"), groups=[group("g", "a"), group("h", "b", "a")]
    )
    assert _only(value) == (
        ("groups", 1, "members", 1),
        "duplicate member 'a', first at #/groups/0/members/0",
    )
    piece = timeline("piece", children=[timeline("half", offset=(4, 1), length=(4, 1))])
    value = manifest(piece, groups=[group("g", "piece", "half")])
    assert _only(value) == (
        ("groups", 0, "members", 1),
        "member 'half' lies inside member 'piece' of the same group",
    )
    value = manifest(copy.deepcopy(piece), groups=[group("g", "half", "piece")])
    assert _only(value) == (
        ("groups", 0, "members", 1),
        "member 'piece' contains member 'half' of the same group",
    )


def test_a_child_and_its_root_in_other_groups_or_none() -> None:
    value = bundle()
    validate(value)
    value["groups"][0]["members"].append("recording")
    value["graphical"]["order"]["group_1"].append("recording")
    validate(value)


def test_a_group_without_members_stays_valid() -> None:
    validate(manifest(timeline("score"), groups=[group("empty")]))


def test_display_orders() -> None:
    value = bundle()
    value["graphical"]["order"]["g9"] = []
    assert _only(value) == (
        ("graphical", "order", "g9"),
        "'g9' names no group of this manifest",
    )
    value = bundle()
    value["graphical"]["order"]["group_1"] = ["score", "page", "performance"]
    assert _only(value) == (
        ("graphical", "order", "group_1", 1),
        "'page' is not a member of group 'group_1'",
    )
    value = bundle()
    value["graphical"]["order"]["group_2"] = ["page"]
    assert _only(value) == (
        ("graphical", "order", "group_2"),
        "member 'excerpt' of group 'group_2' is missing",
    )
    value = bundle()
    del value["graphical"]["order"]["group_2"]
    validate(value)


def test_every_step_in_order() -> None:
    def jump(target: str) -> dict:
        return {
            "id": "j",
            "from_coordinate": [1, 1],
            "to_coordinate": [0, 1],
            "target": target,
        }

    first = timeline(
        "first",
        flow_control={"jumps": [jump("nowhere")]},
        regions=[{"id": "end", "start": [0, 1], "end": [1, 1]}],
        children=[
            timeline("kid", "seconds", 1.0, offset=(-1, 1)),
            timeline("gone", length=None, offset=(9, 1)),
            timeline("late", offset=(6, 1)),
        ],
    )
    value = manifest(
        first,
        timeline("second"),
        timeline("second"),
        id="g2",
        groups=[group("first", "ghost", "second"), group("g2", "second")],
        graphical={"order": {"zz": [], "g2": ["stranger"]}},
    )
    assert _problems(value) == [
        (
            ("timelines", 0, "flow_control", "jumps", 0, "target"),
            "'nowhere' names no marker of this timeline",
        ),
        (
            ("timelines", 0, "children", 0, "unit"),
            "child 'kid' has unit 'seconds', its parent 'first' has 'quarters'",
        ),
        (
            ("timelines", 0, "children", 0, "offset"),
            "offset [-1, 1] of 'kid' is negative",
        ),
        (
            ("timelines", 0, "children", 1, "offset"),
            "offset [9, 1] of 'gone' is beyond the length [8, 1] of its parent 'first'",
        ),
        (
            ("timelines", 0, "children", 2, "length"),
            "child 'late' ends at [14, 1], beyond the length [8, 1] of its parent "
            "'first'",
        ),
        (
            ("timelines", 0, "regions", 0, "id"),
            "id 'end' is reserved for the parts of an address",
        ),
        (("timelines", 2, "id"), "duplicate id 'second', first at #/timelines/1/id"),
        (("groups", 0, "id"), "duplicate id 'first', first at #/timelines/0/id"),
        (("id",), "duplicate id 'g2', first at #/groups/1/id"),
        (("groups", 0, "members", 0), "'ghost' names no timeline of this manifest"),
        (
            ("groups", 1, "members", 0),
            "duplicate member 'second', first at #/groups/0/members/1",
        ),
        (("graphical", "order", "g2", 0), "'stranger' is not a member of group 'g2'"),
        (("graphical", "order", "g2"), "member 'second' of group 'g2' is missing"),
        (("graphical", "order", "zz"), "'zz' names no group of this manifest"),
    ]
