"""Builders for fixtures containing one timeline group."""

from __future__ import annotations

from fractions import Fraction

from timetoalign import (
    ContinuousLogicalTimeline,
    ContinuousPhysicalTimeline,
    DiscreteGraphicalTimeline,
    DiscreteLogicalTimeline,
    DiscretePhysicalTimeline,
    TimelineGroup,
)
from timetoalign.loader.alignment.tilia import TiliaJsonLoader
from timetoalign.maps import LinearMap
from timetoalign.testdata import ensure_data

from . import parts
from .timelines import four_bars


def number_types_group() -> TimelineGroup:
    """Build a group of three timelines whose axes have different number types.

    Quarters as fractions, seconds as floats and pixels as integers, listed in
    a display order that differs from their id order.
    """
    score = ContinuousLogicalTimeline(
        length=Fraction(12), unit="quarters", uid="score", name="Score"
    )
    performance = ContinuousPhysicalTimeline(
        length=12.5, unit="seconds", uid="performance", name="Performance"
    )
    page = DiscreteGraphicalTimeline(
        length=Fraction(1920), unit="pixels", uid="page", name="Page"
    )
    return TimelineGroup(name="Edition", timelines=[score, page, performance])


def styled_group() -> TimelineGroup:
    """Build the group of ``number_types_group`` with maps, a region and a jump.

    The score ``score`` carries a map to ticks, the region "Theme" from 0 to 8
    and a repeat jump from 8 back to 0; the performance ``performance`` a map
    to samples; the page ``page`` a map to points. Every id of a map, region or
    jump is minted. ``group_styled`` holds it with the styles and statements
    of ``GRAPHICAL``.
    """
    group = number_types_group()
    score = parts.with_maps(group.get_timeline("score"), parts.ticks())
    score.create_region(0, 8, name="Theme")
    parts.with_repeat(score, 8, 0)
    parts.with_maps(group.get_timeline("performance"), parts.to_samples())
    parts.with_maps(group.get_timeline("page"), parts.to_points())
    return group


def group_child_member() -> TimelineGroup:
    """Build ``group_child_member``, the group of a child and a recording.

    The group "Second half" groups the child ``second-half``
    ("Second half", 8 quarters), the second half of the root ``piece``
    ("Piece", 16 quarters) placed at offset 8, with the whole recording
    ``recording`` ("Recording", 10.0 seconds).
    """
    piece = ContinuousLogicalTimeline(
        length=Fraction(16), unit="quarters", uid="piece", name="Piece"
    )
    second_half = ContinuousLogicalTimeline(
        length=Fraction(8), unit="quarters", uid="second-half", name="Second half"
    )
    piece.add_child(second_half, Fraction(8))
    recording = ContinuousPhysicalTimeline(
        length=10.0, unit="seconds", uid="recording", name="Recording"
    )
    return TimelineGroup(name="Second half", timelines=[second_half, recording])


def _piece_member_group(uid: str, name: str, length: int, offset: int) -> TimelineGroup:
    """Build a group of a child of a piece and a whole recording.

    The piece ``piece`` ("Piece", 16 quarters) holds the child ``uid``
    (``name``, ``length`` quarters) at ``offset``; the group, named as the
    child, lists the child and then the root ``recording`` ("Recording", 10.0
    seconds), as ``group_child_member`` does with the piece's second half.
    """
    piece = parts.named(ContinuousLogicalTimeline, "piece", "Piece", Fraction(16))
    child = parts.holding(
        piece,
        parts.named(ContinuousLogicalTimeline, uid, name, Fraction(length)),
        Fraction(offset),
    )
    recording = parts.named(ContinuousPhysicalTimeline, "recording", "Recording", 10.0)
    return TimelineGroup(name=name, timelines=[child, recording])


def group_parent_right() -> TimelineGroup:
    """Build the group of the piece's first half, ``first-half`` (8 at 0).

    The piece runs on to the right of the child member only.
    """
    return _piece_member_group("first-half", "First half", 8, 0)


def group_parent_both() -> TimelineGroup:
    """Build the group of the piece's middle, ``middle`` (8 at 4).

    The piece runs on to both sides of the child member.
    """
    return _piece_member_group("middle", "Middle", 8, 4)


def group_parent_exact() -> TimelineGroup:
    """Build the group of the whole piece as its child, ``whole`` (16 at 0).

    The piece coincides with the child member.
    """
    return _piece_member_group("whole", "Whole", 16, 0)


def group_parents_mixed() -> TimelineGroup:
    """Build a group of three child members of different parents and one root.

    The sonata ``sonata`` ("Sonata", 48 quarters, ``locked=True``) holds the
    exposition ``exposition`` ("Exposition", 32 quarters) at 16; the session
    ``session`` ("Session", 90.0 seconds) holds the take ``take`` ("Take",
    25.5 seconds) at 30.0, which carries a map to samples; the page ``page``
    ("Page", 1754 pixels) holds the system ``system`` ("System", 600 pixels)
    at 0. The group "Exposition" lists ``exposition``, ``take``, ``system``
    and the root ``audio`` ("Audio", 1323000 samples), which carries a map to
    seconds. Both map ids are minted.
    """
    sonata = ContinuousLogicalTimeline(
        length=Fraction(48), unit="quarters", uid="sonata", name="Sonata", locked=True
    )
    exposition = parts.holding(
        sonata,
        parts.named(
            ContinuousLogicalTimeline, "exposition", "Exposition", Fraction(32)
        ),
        Fraction(16),
    )
    session = parts.named(ContinuousPhysicalTimeline, "session", "Session", 90.0)
    take = parts.holding(
        session,
        parts.with_maps(
            parts.named(ContinuousPhysicalTimeline, "take", "Take", 25.5),
            parts.to_samples(),
        ),
        30.0,
    )
    page = parts.named(DiscreteGraphicalTimeline, "page", "Page", Fraction(1754))
    system = parts.holding(
        page,
        parts.named(DiscreteGraphicalTimeline, "system", "System", Fraction(600)),
        Fraction(0),
    )
    audio = parts.with_maps(
        parts.named(DiscretePhysicalTimeline, "audio", "Audio", Fraction(1323000)),
        parts.to_seconds(),
    )
    return TimelineGroup(name="Exposition", timelines=[exposition, take, system, audio])


def group_grandchild() -> TimelineGroup:
    """Build a group of a grandchild of quarters and a root in seconds.

    The score ``score`` ("Score", 64 quarters) holds the movement
    ``movement`` ("Movement", 16 quarters) at 16, which holds the theme
    ``theme`` ("Theme", 8 quarters) at 8; the group "Theme" lists ``theme``
    and the root ``recording`` ("Recording", 12.0 seconds).
    """
    score = parts.named(ContinuousLogicalTimeline, "score", "Score", Fraction(64))
    movement = parts.holding(
        score,
        parts.named(ContinuousLogicalTimeline, "movement", "Movement", Fraction(16)),
        Fraction(16),
    )
    theme = parts.holding(
        movement,
        parts.named(ContinuousLogicalTimeline, "theme", "Theme", Fraction(8)),
        Fraction(8),
    )
    recording = parts.named(ContinuousPhysicalTimeline, "recording", "Recording", 12.0)
    return TimelineGroup(name="Theme", timelines=[theme, recording])


def corpus_tilia_group() -> TimelineGroup:
    """Load the group a public TiLiA loader builds from its corpus specimen."""
    tilia = ensure_data("score") / parts.TILIA
    return TiliaJsonLoader.from_file(tilia).create_group()


def group_unknown_length() -> TimelineGroup:
    """Build a group whose member is of unknown length.

    The group "Edition" lists the performance ``performance`` of unknown
    length (seconds, with the region ``region_1`` from 0.0 to 9.5) and the
    score ``score`` (12 quarters), both unnamed.
    """
    performance = ContinuousPhysicalTimeline(
        length=None, unit="seconds", uid="performance"
    )
    parts.with_region(performance, 0.0, 9.5, "region_1")
    return TimelineGroup(
        name="Edition", timelines=[performance, parts.quarters("score", Fraction(12))]
    )


def group_measure_map() -> TimelineGroup:
    """Build a group of a score and its MIDI rendering sharing one measure map.

    The group "Edition" lists the score ``score`` ("Score", 16 quarters) and
    the rendering ``midi`` ("MIDI", 7680 ticks). Both hold the measure map of
    ``four_bars``, so the manifest writes one entry of ``measure_maps`` that
    both name: ``score`` through its ``MeasureRecordMap``, ``midi`` through a
    ``ChainMap`` of the ``LinearMap`` ``ppq`` of ticks to quarters (480 per
    quarter) and its ``MeasureRecordMap``. Every other id of a map or of the
    measure map is minted.
    """
    bars = four_bars()
    score = parts.named(ContinuousLogicalTimeline, "score", "Score", Fraction(16))
    score.add_measure_map(bars)
    midi = DiscreteLogicalTimeline(
        length=Fraction(7680), unit="ticks", uid="midi", name="MIDI"
    )
    midi.add_measure_map(
        bars,
        to_quarters=LinearMap(
            scalar=Fraction(1, 480),
            source_unit="ticks",
            target_unit="quarters",
            uid="ppq",
        ),
    )
    return TimelineGroup(name="Edition", timelines=[score, midi])
