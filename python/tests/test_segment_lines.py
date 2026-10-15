from __future__ import annotations

from typing import Any

import pytest

from timeskeleton import identity_problems, validate

from .conftest import manifest, timeline

ID = "segment line 'line'"


def _segment(
    identifier: str, offset: Any, length: Any, unit: str = "quarters", **rest: Any
) -> dict:
    return timeline(identifier, unit, length, offset=offset, **rest)


def _line(*segments: dict, length: Any = (8, 1), unit: str = "quarters") -> dict:
    return manifest(
        timeline("line", unit, length, is_segment_line=True, children=list(segments))
    )


def _problems(value: dict) -> list[tuple[tuple[str | int, ...], str]]:
    validate_problems = [(p.path, p.message) for p in identity_problems(value)]
    if not validate_problems:
        validate(value)
    return validate_problems


AT = ("timelines", 0)


@pytest.mark.parametrize(
    "value",
    [
        _line(_segment("a", (0, 1), (3, 1)), _segment("b", (3, 1), (5, 1))),
        _line(length=(0, 1)),
        _line(length=None),
        _line(_segment("b", (3, 1), (5, 1)), _segment("a", (0, 1), (3, 1))),
        _line(
            _segment(
                "a",
                (0, 1),
                (4, 1),
                is_segment_line=True,
                children=[
                    _segment("a1", (0, 1), (1, 1)),
                    _segment("a2", (1, 1), (3, 1)),
                ],
            ),
            _segment(
                "b",
                (4, 1),
                (4, 1),
                is_segment_line=True,
                children=[_segment("b1", (0, 1), (4, 1))],
            ),
        ),
        _line(
            _segment("a", 0.0, 0.5, "seconds"),
            _segment("b", 0.5, 0.25, "seconds"),
            _segment("c", 0.75, 0.25, "seconds"),
            length=1.0,
            unit="seconds",
        ),
    ],
    ids=[
        "two segments",
        "empty of length 0",
        "empty of unknown length",
        "offset order",
        "nested",
        "exact floats",
    ],
)
def test_valid_segment_lines(value: dict) -> None:
    assert _problems(value) == []


def test_each_rule_one_problem() -> None:
    value = _line(_segment("a", (0, 1), (3, 1)), _segment("b", (3, 1), 5, "ticks"))
    assert _problems(value) == [
        (
            (*AT, "children", 1, "unit"),
            "child 'b' has unit 'ticks', its parent 'line' has 'quarters'",
        )
    ]
    value = _line(
        _segment("a", (0, 1), (3, 1)),
        _segment("b", (3, 1), (5, 1), is_segment_line=True),
    )
    assert _problems(value) == [
        (
            (*AT, "children", 1, "is_segment_line"),
            f"segment 'b' of {ID} differs from segment 'a' in is_segment_line",
        ),
        (
            (*AT, "children", 1, "length"),
            "the segments of segment line 'b' do not end at its length",
        ),
    ]
    value = _line(
        _segment("a", (0, 1), (3, 1), is_segment_line=True),
        _segment("b", (3, 1), (5, 1)),
    )
    assert _problems(value)[0] == (
        (*AT, "children", 1),
        f"segment 'b' of {ID} differs from segment 'a' in is_segment_line",
    )
    value = _line(_segment("a", (1, 1), (7, 1)))
    assert _problems(value) == [
        ((*AT, "children", 0, "offset"), f"segment 'a' of {ID} does not start at 0")
    ]
    for offset in ((4, 1), (2, 1)):
        value = _line(
            _segment("a", (0, 1), (3, 1)), _segment("b", offset, (8 - offset[0], 1))
        )
        assert _problems(value) == [
            (
                (*AT, "children", 1, "offset"),
                f"segment 'b' of {ID} does not start where the one before it ends",
            )
        ]
    value = _line(_segment("a", (0, 1), (7, 1)))
    assert _problems(value) == [
        ((*AT, "length"), f"the segments of {ID} do not end at its length")
    ]
    assert _problems(_line()) == [
        ((*AT, "length"), f"the segments of {ID} do not end at its length")
    ]


def test_exact_values() -> None:
    value = _line(
        _segment("a", 0.0, 0.1, "seconds"),
        _segment("b", 0.1, 0.2, "seconds"),
        _segment("c", 0.3, 0.7, "seconds"),
        length=1.0,
        unit="seconds",
    )
    assert _problems(value) == [
        (
            (*AT, "children", 2, "offset"),
            f"segment 'c' of {ID} does not start where the one before it ends",
        ),
        ((*AT, "length"), f"the segments of {ID} do not end at its length"),
    ]


@pytest.mark.parametrize(
    "value",
    [
        _line(_segment("a", (0, 1), None), _segment("b", (5, 1), (3, 1))),
        _line(_segment("a", (0, 1), None), _segment("b", (7, 1), (1, 1))),
        _line(_segment("a", (0, 1), (3, 1)), _segment("b", (3, 1), None)),
        _line(
            _segment("a", (0, 1), (3, 1)), _segment("b", (3, 1), (5, 1)), length=None
        ),
        _line(
            _segment("a", (0, 1), (3, 1)), _segment("b", (3, 1), (9, 1)), length=None
        ),
    ],
    ids=[
        "unknown first",
        "unknown first, late successor",
        "unknown last",
        "unknown line",
        "unknown line, long segments",
    ],
)
def test_unknown_lengths_skip_what_needs_them(value: dict) -> None:
    assert _problems(value) == []


def test_an_unknown_line_still_checks_contiguity() -> None:
    value = _line(
        _segment("a", (0, 1), (3, 1)), _segment("b", (4, 1), (4, 1)), length=None
    )
    assert _problems(value) == [
        (
            (*AT, "children", 1, "offset"),
            f"segment 'b' of {ID} does not start where the one before it ends",
        )
    ]


def test_order_and_scope() -> None:
    inner = _segment("d", (5, 1), (1, 1), is_segment_line=True)
    value = _line(
        _segment("a", (0, 1), (3, 1)),
        _segment("b", (3, 1), 1, "ticks"),
        _segment("c", (4, 1), (1, 1), is_segment_line=True),
        inner,
    )
    assert _problems(value) == [
        (
            (*AT, "children", 1, "unit"),
            "child 'b' has unit 'ticks', its parent 'line' has 'quarters'",
        ),
        (
            (*AT, "children", 2, "is_segment_line"),
            f"segment 'c' of {ID} differs from segment 'a' in is_segment_line",
        ),
        (
            (*AT, "children", 3, "is_segment_line"),
            f"segment 'd' of {ID} differs from segment 'a' in is_segment_line",
        ),
        ((*AT, "length"), f"the segments of {ID} do not end at its length"),
        (
            (*AT, "children", 2, "length"),
            "the segments of segment line 'c' do not end at its length",
        ),
        (
            (*AT, "children", 3, "length"),
            "the segments of segment line 'd' do not end at its length",
        ),
    ]


def test_a_timeline_that_is_no_segment_line_is_never_checked() -> None:
    value = manifest(
        timeline("free", children=[timeline("x", offset=(5, 1), length=(1, 1))])
    )
    assert _problems(value) == []
