from __future__ import annotations

import copy

import pytest

from timeskeleton import (
    SchemaValidationError,
    identity_problems,
    rejection_case,
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


def _targets(*identifiers: str) -> list[dict]:
    return [
        {"id": i, "type": "jump_to", "manifestation": "segno", "coordinate": [k, 1]}
        for k, i in enumerate(identifiers)
    ]


def test_the_bundle_document_has_no_problem() -> None:
    assert _problems(bundle()) == []
    validate(bundle())


def test_a_repeated_id_within_a_root_is_reported_at_its_later_occurrence() -> None:
    child = timeline("c", offset=(0, 1), flow_control=_targets("m"))
    root = timeline("bare", flow_control=_targets("m", "m", "bare"), children=[child])
    assert _problems(manifest(root)) == [
        (
            ("timelines", 0, "flow_control", 1, "id"),
            "duplicate id 'm', first at #/timelines/0/flow_control/0/id",
        ),
        (
            ("timelines", 0, "flow_control", 2, "id"),
            "duplicate id 'bare', first at #/timelines/0/id",
        ),
        (
            ("timelines", 0, "children", 0, "flow_control", 0, "id"),
            "duplicate id 'm', first at #/timelines/0/flow_control/0/id",
        ),
    ]


def test_scopes_are_per_root() -> None:
    validate(
        manifest(
            timeline("a", flow_control=_targets("m")),
            timeline("b", flow_control=_targets("m")),
        )
    )
    score = timeline("score", regions=[{"id": "perf", "start": [0, 1], "end": [1, 1]}])
    take = timeline("take", children=[timeline("perf", offset=(0, 1))])
    validate(manifest(score, take))


def test_a_nested_map_id_shares_its_root_s_scope() -> None:
    def linear(identifier: str) -> dict:
        return {
            "type": "LinearMap",
            "id": identifier,
            "source_unit": None,
            "target_unit": None,
        }

    units = {"source_unit": None, "target_unit": None}
    chain = {"type": "ChainMap", "id": "c", "maps": [linear("l"), linear("l")]} | units
    piecewise = {
        "type": "PiecewiseMap",
        "id": "p",
        "breaks": [[0, 1], [4, 1]],
        "maps": [linear("l")],
    } | units
    combination = {
        "type": "CombinationMap",
        "id": "cmap_1",
        "maps": {"output": linear("cmap_1")},
    } | units
    region = {"id": "l", "start": [0, 1], "end": [1, 1]}
    held = ("timelines", 0, "conversion_maps", 0, "maps")
    assert _only(manifest(timeline("s", conversion_maps=[chain]))) == (
        (*held, 1, "id"),
        "duplicate id 'l', first at #/timelines/0/conversion_maps/0/maps/0/id",
    )
    assert _only(
        manifest(timeline("s", conversion_maps=[piecewise], regions=[region]))
    ) == ((*held, 0, "id"), "duplicate id 'l', first at #/timelines/0/regions/0/id")
    assert _only(manifest(timeline("s", conversion_maps=[combination]))) == (
        (*held, "output", "id"),
        "duplicate id 'cmap_1', first at #/timelines/0/conversion_maps/0/id",
    )
    validate(
        manifest(
            timeline("a", conversion_maps=[piecewise]),
            timeline("b", conversion_maps=[piecewise]),
        )
    )


def test_targets_stay_within_their_timeline() -> None:
    def jump(
        identifier: str, target: str | None, manifestation: str = "dal_segno"
    ) -> dict:
        element = {
            "id": identifier,
            "type": "jump_from",
            "manifestation": manifestation,
            "coordinate": [4, 1],
        }
        return element if target is None else {**element, "target": target}

    fine = {
        "id": "fine",
        "type": "flow_marker",
        "manifestation": "fine",
        "coordinate": [6, 1],
    }
    child = timeline(
        "c",
        offset=(0, 1),
        flow_control=[*_targets("there"), jump("cj", "here")],
    )
    root = timeline(
        "bare",
        flow_control=[
            *_targets("here"),
            fine,
            jump("j1", "here"),
            jump("j2", None, "da_capo"),
            jump("j3", "there"),
            jump("j4", "fine"),
            jump("j5", None, "repeat_end"),
        ],
        children=[child],
    )
    assert _problems(manifest(root)) == [
        (
            ("timelines", 0, "flow_control", 4, "target"),
            "'there' names no jump_to of this timeline",
        ),
        (
            ("timelines", 0, "flow_control", 5, "target"),
            "'fine' names no jump_to of this timeline",
        ),
        (
            ("timelines", 0, "children", 0, "flow_control", 1, "target"),
            "'here' names no jump_to of this timeline",
        ),
    ]


ROWS = [{"count": 1, "qstamp": [0, 1], "actual_length": [4, 1]}]


def _table(x_values: list, y_values: list, identifier: str = "tempo") -> dict:
    return {
        "type": "TableMap",
        "id": identifier,
        "source_unit": "quarters",
        "target_unit": None,
        "x_values": x_values,
        "y_values": y_values,
    }


def _piecewise(breaks: list, maps: list) -> dict:
    return {
        "type": "PiecewiseMap",
        "id": "sections",
        "source_unit": "quarters",
        "target_unit": None,
        "breaks": breaks,
        "maps": maps,
    }


def _linear(identifier: str) -> dict:
    return {
        "type": "LinearMap",
        "id": identifier,
        "source_unit": None,
        "target_unit": None,
    }


def _view(identifier: str, reference: str) -> dict:
    return {
        "type": "MeasureNumberMap",
        "id": identifier,
        "source_unit": "quarters",
        "target_unit": None,
        "measure_map": reference,
    }


def _maps(*conversion_maps: dict) -> dict:
    return manifest(timeline("score", conversion_maps=list(conversion_maps)))


def test_a_table_maps_arrays_agree() -> None:
    assert _only(_maps(_table([[0, 1], [4, 1], [8, 1]], [60, 72]))) == (
        ("timelines", 0, "conversion_maps", 0, "y_values"),
        "TableMap 'tempo' has 3 x values and 2 y values",
    )
    assert _only(_maps(_table([[0, 1], [2, 1], 2.0], [1, 2, 3]))) == (
        ("timelines", 0, "conversion_maps", 0, "x_values", 2),
        "x value 2.0 of TableMap 'tempo' does not exceed the one before it",
    )
    accepted = _maps(_table([[0, 1], 0.5, [3, 4]], [1, 2, 3]))
    assert _problems(accepted) == []
    validate(accepted)


def test_a_piecewise_map_has_one_map_per_interval() -> None:
    assert _only(_maps(_piecewise([[0, 1], [8, 1], [16, 1]], [_linear("a")]))) == (
        ("timelines", 0, "conversion_maps", 0, "maps"),
        "PiecewiseMap 'sections' has 1 map for 3 breaks; it needs 2 maps",
    )
    pieces = _piecewise([[0, 1], [8, 1], [4, 1]], [_linear("a"), _linear("b")])
    assert _only(_maps(pieces)) == (
        ("timelines", 0, "conversion_maps", 0, "breaks", 2),
        "break [4, 1] of PiecewiseMap 'sections' does not exceed the one before it",
    )


def test_nested_maps_are_checked_at_their_own_paths() -> None:
    def repeated(identifier: str) -> dict:
        return _table([[1, 1], [1, 1]], [1, 2], identifier)

    chain = {
        "type": "ChainMap",
        "id": "chain",
        "source_unit": "quarters",
        "target_unit": None,
        "maps": [repeated("tc")],
    }
    both = {
        "type": "CombinationMap",
        "id": "both",
        "source_unit": "quarters",
        "target_unit": None,
        "maps": {"b": repeated("tb"), "a": repeated("ta")},
    }
    pieces = _piecewise([[0, 1], [8, 1]], [repeated("tp")])
    child = timeline("c", offset=(0, 1), conversion_maps=[repeated("tk")])
    root = timeline("score", conversion_maps=[chain, both, pieces], children=[child])
    message = "x value [1, 1] of TableMap {} does not exceed the one before it"
    assert _problems(manifest(root)) == [
        (
            ("timelines", 0, "conversion_maps", 0, "maps", 0, "x_values", 1),
            message.format("'tc'"),
        ),
        (
            ("timelines", 0, "conversion_maps", 1, "maps", "a", "x_values", 1),
            message.format("'ta'"),
        ),
        (
            ("timelines", 0, "conversion_maps", 1, "maps", "b", "x_values", 1),
            message.format("'tb'"),
        ),
        (
            ("timelines", 0, "conversion_maps", 2, "maps", 0, "x_values", 1),
            message.format("'tp'"),
        ),
        (
            ("timelines", 0, "children", 0, "conversion_maps", 0, "x_values", 1),
            message.format("'tk'"),
        ),
    ]
    assert {problem.code for problem in identity_problems(manifest(root))} == {
        "conversion_map"
    }


def _record(identifier: str = "bars") -> dict:
    return {
        "type": "MeasureRecordMap",
        "id": identifier,
        "source_unit": "quarters",
        "target_unit": None,
        "measure_map": "measures",
    }


def _scale(
    source: str | None, target: str | None = "quarters", identifier: str = "scale"
) -> dict:
    return {
        "type": "LinearMap",
        "id": identifier,
        "source_unit": source,
        "target_unit": target,
        "scalar": [1, 480],
    }


def _holder(kind: str, source: str | None, maps: list | dict, **rest: object) -> dict:
    identifier = {"ChainMap": "chain", "CombinationMap": "both"}.get(kind, "sections")
    return {
        "type": kind,
        "id": identifier,
        "source_unit": source,
        "target_unit": None,
        "maps": maps,
        **rest,
    }


def _ticks(*conversion_maps: dict, children: list | None = None) -> dict:
    root = timeline(
        "score",
        "ticks",
        3840,
        conversion_maps=list(conversion_maps),
        children=children or [],
    )
    return manifest(root, measure_maps=[{"id": "measures", "rows": ROWS}])


def test_a_map_converts_from_its_timelines_unit() -> None:
    assert _only(_ticks(_record())) == (
        ("timelines", 0, "conversion_maps", 0, "source_unit"),
        "MeasureRecordMap 'bars' has source unit 'quarters', its timeline 'score' "
        "has 'ticks'",
    )
    child = timeline("c", "ticks", 960, offset=0, conversion_maps=[_record()])
    assert _only(_ticks(children=[child])) == (
        ("timelines", 0, "children", 0, "conversion_maps", 0, "source_unit"),
        "MeasureRecordMap 'bars' has source unit 'quarters', its timeline 'c' "
        "has 'ticks'",
    )
    chained = _holder("ChainMap", "ticks", [_scale("ticks"), _record()])
    loose = _scale(None, None, "loose")
    held = _scale("seconds", identifier="held")
    unstated = _holder("PiecewiseMap", None, [held], breaks=[0, 960])
    accepted = _ticks(chained, loose, unstated)
    assert _problems(accepted) == []
    validate(accepted)


def test_a_held_map_converts_from_its_holders_source_unit() -> None:
    later = _scale("seconds", identifier="later")
    chain = _holder("ChainMap", "quarters", [_scale("ticks"), later])
    assert _only(_maps(chain)) == (
        ("timelines", 0, "conversion_maps", 0, "maps", 0, "source_unit"),
        "LinearMap 'scale' has source unit 'ticks', its ChainMap 'chain' has "
        "'quarters'",
    )
    both = _holder("CombinationMap", "ticks", {"bar": _record("bar")})
    assert _only(_ticks(both)) == (
        ("timelines", 0, "conversion_maps", 0, "maps", "bar", "source_unit"),
        "MeasureRecordMap 'bar' has source unit 'quarters', its CombinationMap "
        "'both' has 'ticks'",
    )
    pieces = _holder(
        "PiecewiseMap", "quarters", [_scale("seconds")], breaks=[[0, 1], [8, 1]]
    )
    assert _only(_maps(pieces)) == (
        ("timelines", 0, "conversion_maps", 0, "maps", 0, "source_unit"),
        "LinearMap 'scale' has source unit 'seconds', its PiecewiseMap "
        "'sections' has 'quarters'",
    )
    assert {problem.code for problem in identity_problems(_maps(chain))} == {
        "conversion_map"
    }


def test_a_measure_view_names_a_measure_map() -> None:
    both = {
        "type": "CombinationMap",
        "id": "both",
        "source_unit": "quarters",
        "target_unit": None,
        "maps": {"bar": _view("bar", "ghost")},
    }
    value = manifest(
        timeline("score", conversion_maps=[_view("number", "ghost"), both]),
        measure_maps=[{"id": "measures", "rows": ROWS}],
    )
    assert _problems(value) == [
        (
            ("timelines", 0, "conversion_maps", 0, "measure_map"),
            "'ghost' names no measure map of this manifest",
        ),
        (
            ("timelines", 0, "conversion_maps", 1, "maps", "bar", "measure_map"),
            "'ghost' names no measure map of this manifest",
        ),
    ]
    assert {problem.code for problem in identity_problems(value)} == {"dangling_target"}
    named = manifest(
        timeline("score", conversion_maps=[_view("number", "measures")]),
        timeline("take", "seconds", 60.0),
        measure_maps=[{"id": "measures", "rows": ROWS}],
    )
    assert _problems(named) == []
    validate(named)


def test_measure_map_ids_share_the_manifest_scope() -> None:
    value = manifest(
        timeline("score"),
        groups=[group("g", "score")],
        measure_maps=[
            {"id": identifier, "rows": ROWS} for identifier in ("score", "g", "m", "m")
        ],
    )
    assert _problems(value) == [
        (("measure_maps", 0, "id"), "duplicate id 'score', first at #/timelines/0/id"),
        (("measure_maps", 1, "id"), "duplicate id 'g', first at #/groups/0/id"),
        (("measure_maps", 3, "id"), "duplicate id 'm', first at #/measure_maps/2/id"),
    ]
    assert {problem.code for problem in identity_problems(value)} == {"duplicate_id"}
    named = manifest(
        timeline("score"), id="m", measure_maps=[{"id": "m", "rows": ROWS}]
    )
    assert _only(named) == (("id",), "duplicate id 'm', first at #/measure_maps/0/id")
    assert [problem.code for problem in identity_problems(named)] == ["manifest_id"]


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


def test_a_negative_offset_is_accepted_on_a_child_or_a_root() -> None:
    def take(offset: float) -> dict:
        return manifest(
            timeline(
                "recording",
                "seconds",
                60.0,
                children=[timeline("take", "seconds", 4.0, offset=offset)],
            )
        )

    grandchild = timeline("b", offset=(-1, 2))
    for document in (
        take(-1.5),
        manifest(timeline("score", children=[timeline("c", offset=(-1, 1000000))])),
        manifest(
            timeline(
                "score", children=[timeline("a", offset=(0, 1), children=[grandchild])]
            )
        ),
        {
            "timeskeleton": "0.7.0",
            "timelines": [
                {
                    "id": "piece",
                    "unit": "quarters",
                    "length": [32, 1],
                    "children": [
                        {
                            "id": "take",
                            "unit": "quarters",
                            "offset": [-3, 2],
                            "length": [4, 1],
                        }
                    ],
                }
            ],
        },
        manifest(timeline("score", children=[timeline("c", offset=(0, 1))])),
        take(-0.0),
        manifest(timeline("take", "seconds", 2.5, offset=-1700000000.25)),
        manifest(timeline("score", offset=[-3, 2])),
    ):
        assert _problems(document) == []
        validate(document)
    long = timeline("take", length=(40, 1), offset=(-3, 2))
    value = manifest(timeline("piece", length=(32, 1), children=[long]))
    assert _only(value) == (
        ("timelines", 0, "children", 0, "length"),
        "child 'take' ends at [77, 2], beyond the length [32, 1] of its parent 'piece'",
    )


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
        (
            "child_offset_beyond_parent",
            "offset 75.0 of 'take' is beyond the length 60.0 of its parent 'recording'",
        ),
        (
            "child_end_beyond_parent",
            "child 'coda' ends at [12, 1], beyond the length [10, 1] of its parent "
            "'score'",
        ),
        ("band_id_region", "id 'regions_1' is reserved for the bands of a timeline"),
        (
            "band_order_unknown_entry",
            "'score/regions_2' is not 'score' or one of its bands",
        ),
        (
            "band_order_missing_band",
            "'score/markers_1' is missing from the band order of 'score'",
        ),
        (
            "order_unknown_group",
            "'group_9' names no group or timeline of this manifest",
        ),
    ],
)
def test_the_shared_identity_rejections_carry_their_messages(
    name: str, message: str
) -> None:
    (path,) = [path for path in rejection_paths() if path.stem == name]
    case = rejection_case(path)
    assert _only(case.manifest) == (case.path, message)


def _id_documents(word: str) -> list[tuple[dict, tuple[str | int, ...]]]:
    """``word`` as the id of each kind, with the path of that id."""
    region = {"id": word, "start": [0, 1], "end": [1, 1]}
    linear = {
        "type": "LinearMap",
        "id": word,
        "source_unit": None,
        "target_unit": None,
    }
    rows = [{"count": 1, "qstamp": [0, 1], "actual_length": [4, 1]}]
    flow = [
        {
            "id": word,
            "type": "flow_marker",
            "manifestation": "fine",
            "coordinate": [1, 1],
        },
        {
            "id": word,
            "type": "jump_from",
            "manifestation": "da_capo",
            "coordinate": [1, 1],
        },
        {"id": word, "type": "jump_to", "manifestation": "coda", "coordinate": [1, 1]},
    ]
    holders = [
        (
            {"type": "ChainMap", "id": "c", "maps": [linear]},
            ("maps", 0, "id"),
        ),
        (
            {
                "type": "PiecewiseMap",
                "id": "p",
                "breaks": [[0, 1], [4, 1]],
                "maps": [linear],
            },
            ("maps", 0, "id"),
        ),
        (
            {"type": "CombinationMap", "id": "o", "maps": {"output": linear}},
            ("maps", "output", "id"),
        ),
    ]
    documents = [
        (manifest(timeline(word)), ("timelines", 0, "id")),
        (
            manifest(timeline("s", conversion_maps=[linear])),
            ("timelines", 0, "conversion_maps", 0, "id"),
        ),
        *(
            (
                manifest(
                    timeline(
                        "s",
                        conversion_maps=[
                            {"source_unit": None, "target_unit": None} | holder
                        ],
                    )
                ),
                ("timelines", 0, "conversion_maps", 0, *at),
            )
            for holder, at in holders
        ),
        (
            manifest(timeline("s", regions=[region])),
            ("timelines", 0, "regions", 0, "id"),
        ),
        (manifest(timeline("s"), groups=[group(word, "s")]), ("groups", 0, "id")),
        (
            manifest(timeline("s"), measure_maps=[{"id": word, "rows": rows}]),
            ("measure_maps", 0, "id"),
        ),
        (manifest(timeline("s"), id=word), ("id",)),
    ]
    for element in flow:
        documents.append(
            (
                manifest(timeline("s", flow_control=[element])),
                ("timelines", 0, "flow_control", 0, "id"),
            )
        )
    return documents


@pytest.mark.parametrize("word", ["start", "end", "name", "label", "card"])
def test_part_words_are_no_id_anywhere(word: str) -> None:
    for document, path in _id_documents(word):
        assert _only(document) == (
            path,
            f"id '{word}' is reserved for the parts of an address",
        )


@pytest.mark.parametrize(
    "word",
    [
        "markers_1",
        "conversion_maps_1",
        "children_1",
        "regions_1",
        "flow_control_1",
        "regions_12",
        "flow_control_907",
    ],
)
def test_band_ids_are_no_id_anywhere(word: str) -> None:
    for document, path in _id_documents(word):
        assert _only(document) == (
            path,
            f"id '{word}' is reserved for the bands of a timeline",
        )


@pytest.mark.parametrize(
    "word",
    [
        "starts",
        "Start",
        "markers",
        "conversion_maps",
        "children",
        "regions",
        "flow_control",
        "regions_0",
        "regions_01",
        "region_1",
        "Regions_1",
        "regions_1a",
    ],
)
def test_other_words_are_ids(word: str) -> None:
    for document, _ in _id_documents(word):
        assert _problems(document) == []
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
    value = manifest(timeline("a"), groups=[group("g", "a", "a")])
    assert [
        (problem.code, problem.path, problem.message)
        for problem in identity_problems(value)
    ] == [
        (
            "group_member",
            ("groups", 0, "members", 1),
            "duplicate member 'a', first at #/groups/0/members/0",
        )
    ]
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


def test_a_timeline_in_two_groups() -> None:
    value = manifest(
        timeline("t"),
        timeline("u"),
        timeline("v"),
        groups=[group("g1", "t", "u"), group("g2", "t", "v")],
    )
    assert _problems(value) == []
    validate(value)


def test_a_group_without_members_stays_valid() -> None:
    validate(manifest(timeline("score"), groups=[group("empty")]))


def test_display_orders() -> None:
    value = bundle()
    value["graphical"]["order"]["g9"] = []
    assert _only(value) == (
        ("graphical", "order", "g9"),
        "'g9' names no group or timeline of this manifest",
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


SCORE_BANDS = [
    "score/children_1",
    "score/markers_1",
    "score",
    "score/conversion_maps_1",
    "score/regions_1",
    "score/flow_control_1",
]
"""The band order of the README's example."""

B_BANDS = [
    "b/flow_control_1",
    "b/regions_1",
    "b/markers_1",
    "b",
    "b/conversion_maps_1",
    "b/children_1",
]
"""The reverse of the default band order, for the child ``b``."""


def _band_orders(**orders: list[str]) -> dict:
    """``score`` with its child ``b`` grouped with ``perf``, and the given orders."""
    return manifest(
        timeline("score", children=[timeline("b", length=(4, 1), offset=(0, 1))]),
        timeline("perf", "seconds", 61.5),
        groups=[group("g", "perf", "score")],
        graphical={"order": {"g": ["score", "perf"], **orders}},
    )


def test_band_orders_at_a_root_and_at_a_descendant() -> None:
    default = [
        "score/children_1",
        "score/conversion_maps_1",
        "score",
        "score/markers_1",
        "score/regions_1",
        "score/flow_control_1",
    ]
    for value in (
        _band_orders(score=default),
        _band_orders(score=SCORE_BANDS),
        _band_orders(b=B_BANDS),
        _band_orders(score=SCORE_BANDS, b=B_BANDS),
    ):
        assert _problems(value) == []
        validate(value)


@pytest.mark.parametrize(
    "stranger", ["score/regions_2", "regions_1", "b/regions_1", "b", "ghost"]
)
def test_a_band_order_entry_that_is_no_band_of_its_timeline(stranger: str) -> None:
    assert _only(_band_orders(score=[*SCORE_BANDS, stranger])) == (
        ("graphical", "order", "score", 6),
        f"'{stranger}' is not 'score' or one of its bands",
    )


def test_a_band_order_missing_an_address() -> None:
    assert _only(_band_orders(score=SCORE_BANDS[:-1])) == (
        ("graphical", "order", "score"),
        "'score/flow_control_1' is missing from the band order of 'score'",
    )
    assert _problems(_band_orders(score=[])) == [
        (
            ("graphical", "order", "score"),
            f"'{address}' is missing from the band order of 'score'",
        )
        for address in [
            "score/children_1",
            "score/conversion_maps_1",
            "score",
            "score/markers_1",
            "score/regions_1",
            "score/flow_control_1",
        ]
    ]


def test_a_band_order_is_held_to_its_own_timelines_bands() -> None:
    order = [
        "b/flow_control_1",
        "score/regions_1",
        "b/markers_1",
        "b",
        "b/conversion_maps_1",
        "b/children_1",
    ]
    assert _problems(_band_orders(b=order)) == [
        (
            ("graphical", "order", "b", 1),
            "'score/regions_1' is not 'b' or one of its bands",
        ),
        (
            ("graphical", "order", "b"),
            "'b/regions_1' is missing from the band order of 'b'",
        ),
    ]


def test_every_step_in_order() -> None:
    jump = {
        "id": "j",
        "type": "jump_from",
        "manifestation": "dal_segno",
        "coordinate": [1, 1],
        "target": "nowhere",
    }
    first = timeline(
        "first",
        flow_control=[jump],
        conversion_maps=[
            _view("bars", "no-measures"),
            _table([[0, 1], [4, 1], [8, 1]], [60, 72]),
        ],
        regions=[
            {"id": "end", "start": [0, 1], "end": [1, 1]},
            {"id": "regions_1", "start": [0, 1], "end": [1, 1]},
        ],
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
        groups=[
            group("first", "ghost", "second"),
            group("g2", "second"),
            group("children_2"),
        ],
        measure_maps=[{"id": "first", "rows": ROWS}],
        graphical={
            "order": {
                "zz": [],
                "kid": [
                    "kid/regions_2",
                    "kid",
                    "kid/children_1",
                    "kid/conversion_maps_1",
                    "kid/markers_1",
                    "kid/regions_1",
                ],
                "g2": ["stranger"],
            }
        },
    )
    assert _problems(value) == [
        (
            ("timelines", 0, "flow_control", 0, "target"),
            "'nowhere' names no jump_to of this timeline",
        ),
        (
            ("timelines", 0, "conversion_maps", 0, "measure_map"),
            "'no-measures' names no measure map of this manifest",
        ),
        (
            ("timelines", 0, "conversion_maps", 1, "y_values"),
            "TableMap 'tempo' has 3 x values and 2 y values",
        ),
        (
            ("timelines", 0, "children", 0, "unit"),
            "child 'kid' has unit 'seconds', its parent 'first' has 'quarters'",
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
        (
            ("timelines", 0, "regions", 1, "id"),
            "id 'regions_1' is reserved for the bands of a timeline",
        ),
        (
            ("groups", 2, "id"),
            "id 'children_2' is reserved for the bands of a timeline",
        ),
        (("timelines", 2, "id"), "duplicate id 'second', first at #/timelines/1/id"),
        (("groups", 0, "id"), "duplicate id 'first', first at #/timelines/0/id"),
        (
            ("measure_maps", 0, "id"),
            "duplicate id 'first', first at #/timelines/0/id",
        ),
        (("id",), "duplicate id 'g2', first at #/groups/1/id"),
        (("groups", 0, "members", 0), "'ghost' names no timeline of this manifest"),
        (("graphical", "order", "g2", 0), "'stranger' is not a member of group 'g2'"),
        (("graphical", "order", "g2"), "member 'second' of group 'g2' is missing"),
        (
            ("graphical", "order", "kid", 0),
            "'kid/regions_2' is not 'kid' or one of its bands",
        ),
        (
            ("graphical", "order", "kid"),
            "'kid/flow_control_1' is missing from the band order of 'kid'",
        ),
        (
            ("graphical", "order", "zz"),
            "'zz' names no group or timeline of this manifest",
        ),
    ]
    assert [problem.code for problem in identity_problems(value)] == [
        *["dangling_target"] * 2,
        "conversion_map",
        "child_unit",
        "child_offset",
        "child_end",
        *["reserved_id"] * 3,
        *["duplicate_id"] * 3,
        "manifest_id",
        "group_member",
        *["display_order"] * 2,
        *["band_order"] * 2,
        "order_key",
    ]
    with pytest.raises(SchemaValidationError) as caught:
        validate(value)
    assert (caught.value.path, caught.value.message) == _problems(value)[0]
