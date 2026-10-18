#!/usr/bin/env python
"""Emit the fixtures of the current schema through timetoalign.

Every fixture is a manifest of the one shape, emitted into
``fixtures/<version>/``. The directories sort the manifests by content: one
root timeline and no group directly in it, one group in its ``groups/``, and
alignment bundles in its ``bundles/`` directory. Every timeline, group and
bundle is built with public constructors or a public loader and written with
its ``to_dict()``. The script adds the manifest's provenance to its free
``meta`` (``meta.generator``) and, for a styled manifest, the ``graphical``
styles and statements of ``GRAPHICAL``; the class that reads the directory's
manifests as a whole reads the result back, and its ``to_dict()`` writes the
fixture in the complete form and ``to_dict(minimal=True)`` its minimal twin
``<name>.minimal.json``. Both are written with ``timeskeleton.dumps``, read
back, validated, checked against ``timeskeleton.complete`` and
``timeskeleton.minimal``, and round-tripped through the library; a manifest
whose array order differs from the canonical order fails. Every builder
entry emits exactly the files it builds. The current schema version is
``timeskeleton.SCHEMA_VERSION``. The fixtures of a released version are
frozen: the script refuses to write into ``fixtures/<version>/`` once the tag
``v<version>`` exists. An id the script does not give is minted by
timetoalign as ``<prefix>_<N>`` with N the smallest positive integer not yet
taken in its scope, so it depends on the construction order in the script
and on nothing built before, and every run emits the same files.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
from timetoalign import (
    AlignmentBundle,
    ContinuousGraphicalTimeline,
    ContinuousLogicalTimeline,
    ContinuousPhysicalTimeline,
    DiscreteGraphicalTimeline,
    DiscreteLogicalTimeline,
    DiscretePhysicalTimeline,
    Ms3Loader,
    Timeline,
    TimelineGroup,
)
from timetoalign.core import ActivationCondition, FlowControlElement
from timetoalign.loader.alignment import (
    Ieee1599Loader,
    ListenHereLoader,
    MatchfileLoader,
    MpmLoader,
    ParangonadaLoader,
)
from timetoalign.loader.alignment.tilia import TiliaJsonLoader
from timetoalign.loader.graphical.iiif import IIIFManifestLoader
from timetoalign.loader.midi.score import ScoreMidiLoader
from timetoalign.loader.physical.audio import AudioLoader
from timetoalign.maps import (
    BeatInMeasureMap,
    ChainMap,
    CombinationMap,
    ConstantMap,
    FloorMap,
    InterpolationMap,
    IntervalToConstantMap,
    LinearMap,
    MetricalPositionMap,
    MetricMap,
    PiecewiseMap,
    QuartersToFloatingMeasures,
    QuartersToMeasureNumber,
    QuartersToTicks,
    RotationMap,
    SamplesToSeconds,
    ScalarMap,
    SecondsToSamples,
    ShiftMap,
    TableMap,
    TicksToQuarters,
)
from timetoalign.testdata import ensure_data
from timetoalign.timelines import SegmentLine
from timetoalign.timelines.flowcontrol import Break, Jump, Marker

from timeskeleton import (
    SCHEMA_VERSION,
    canonical_order,
    complete,
    dumps,
    minimal,
    unknown_keys,
    validate,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPOSITORY_ROOT / "fixtures" / SCHEMA_VERSION
READERS: dict[str, Any] = {
    "": Timeline,
    "groups": TimelineGroup,
    "bundles": AlignmentBundle,
}
"""The class reading the manifests of each directory as a whole, by directory.

``Timeline.from_dict`` reads a manifest of one root and no group,
``TimelineGroup.from_dict`` an anonymous manifest of one group and
``AlignmentBundle.from_dict`` any manifest.
"""


def with_children(
    cls: type[Timeline],
    unit: str,
    length: Any,
    children: list[tuple[Any, Any]],
) -> Timeline:
    """Build a timeline of ``cls`` with one child per length/offset pair."""
    parent = cls(length=length, unit=unit)
    for child_length, offset in children:
        parent.add_child(cls(length=child_length, unit=unit), offset)
    return parent


def conversion_map_timelines() -> list[Timeline]:
    """Build timelines carrying every registered conversion-map class."""
    meter_for_position = MetricMap(
        starts=[Fraction(0), Fraction(4)],
        mcs=[1, 2],
        mns=["1", "2"],
        lengths=[Fraction(4), Fraction(4)],
    )
    # Construct this first so its implicit BeatInMeasureMap has the stable _1 id.
    metrical_position = MetricalPositionMap(meter_for_position)
    meter_for_beat = MetricMap(
        starts=[Fraction(0), Fraction(3)],
        mcs=[1, 2],
        mns=["1", "2"],
        lengths=[Fraction(3), Fraction(3)],
    )

    quarters = ContinuousLogicalTimeline(
        length=16, unit="quarters", uid="maps:quarters", name="Quarter-note maps"
    )
    quarter_maps = [
        metrical_position,
        BeatInMeasureMap(meter_for_beat),
        ChainMap(
            [
                ScalarMap(
                    Fraction(1, 2),
                    source_unit="quarters",
                    target_unit="seconds",
                ),
                ScalarMap(60, source_unit="seconds", target_unit="minutes"),
            ]
        ),
        CombinationMap(
            {
                "label": ConstantMap(value="verse", source_unit="quarters"),
                "beat": RotationMap(4, base=1, source_unit="quarters"),
            }
        ),
        ConstantMap(value="section-a", source_unit="quarters"),
        FloorMap(4, base=1, source_unit="quarters"),
        InterpolationMap(
            source_coords=np.array([0.0, 8.0, 16.0]),
            target_coords=np.array([0.0, 4.25, 9.0]),
            source_id="maps:quarters",
            target_id="maps:seconds",
            source_unit="quarters",
            target_unit="seconds",
        ),
        IntervalToConstantMap(
            boundaries=[Fraction(0), Fraction(8)],
            values=["opening", "closing"],
            source_unit="quarters",
        ),
        LinearMap(
            scalar=Fraction(3, 2),
            offset=Fraction(1, 3),
            source_unit="quarters",
            target_unit="seconds",
        ),
        MetricMap(
            starts=[Fraction(0), Fraction(4)],
            mcs=[1, 2],
            mns=["1", "2"],
            lengths=[Fraction(4), Fraction(4)],
        ),
        PiecewiseMap(
            breaks=[Fraction(0), Fraction(8), Fraction(16)],
            maps=[ShiftMap(offset=1), ShiftMap(offset=2)],
            source_unit="quarters",
            target_unit="seconds",
        ),
        QuartersToFloatingMeasures(
            x_values=[Fraction(0), Fraction(4), Fraction(8)],
            y_values=[1.0, 2.0, 3.0],
        ),
        QuartersToMeasureNumber(boundaries=[Fraction(0), Fraction(4)], mns=["1", "2"]),
        QuartersToTicks(ppq=480),
        RotationMap(4, scale=0.5, base=1, offset=0.25, source_unit="quarters"),
        ScalarMap(Fraction(2, 3), source_unit="quarters", target_unit="seconds"),
        ShiftMap(offset=Fraction(1, 2), source_unit="quarters"),
        TableMap(
            x_values=[Fraction(0), Fraction(4)],
            y_values=[0.0, 2.5],
            kind="linear",
            extrapolate="constant",
            source_unit="quarters",
            target_unit="seconds",
        ),
    ]
    for conversion_map in quarter_maps:
        quarters.add_conversion_map(conversion_map)

    ticks = DiscreteLogicalTimeline(
        length=960, unit="ticks", uid="maps:ticks", name="Tick maps"
    )
    ticks.add_conversion_map(TicksToQuarters(ppq=480))

    samples = DiscretePhysicalTimeline(
        length=96000, unit="samples", uid="maps:samples", name="Sample maps"
    )
    samples.add_conversion_map(SamplesToSeconds(sample_rate=48000))

    seconds = ContinuousPhysicalTimeline(
        length=2.0, unit="seconds", uid="maps:seconds", name="Second maps"
    )
    seconds.add_conversion_map(SecondsToSamples(sample_rate=48000))
    return [quarters, ticks, samples, seconds]


def flow_control_timeline() -> Timeline:
    """Build one timeline with a break, and a jump to a named marker."""
    timeline = ContinuousLogicalTimeline(
        length=16, unit="quarters", uid="flow:quarters", name="Flow control"
    )
    marker = timeline.flow_control.add_marker(
        Marker(timeline.make_coordinate(2), name="repeat-start")
    )
    timeline.flow_control.add_break(
        Break(
            coordinate=timeline.make_coordinate(12),
            control_type=FlowControlElement.fine,
            condition=ActivationCondition.after_dc_ds,
            repeat_count=1,
            label="Fine",
            name="fine",
            meta={"source": "synthetic"},
        )
    )
    timeline.flow_control.add_jump(
        Jump(
            from_coordinate=timeline.make_coordinate(8),
            to_coordinate=timeline.make_coordinate(2),
            control_type=FlowControlElement.repeat_end,
            condition=ActivationCondition.first_n,
            repeat_count=2,
            target=marker.id,
            label="Repeat",
            meta={"source": "synthetic"},
        )
    )
    return timeline


def drawing_manifests() -> dict[str, list[Timeline]]:
    """Build the small manifests that show one drawn component each.

    Every timeline and map carries an explicit id, so the manifests do not
    depend on the order in which the script constructs them.
    """
    bare = ContinuousLogicalTimeline(length=8, unit="quarters", uid="bare", name="Bare")

    piece = ContinuousLogicalTimeline(
        length=8, unit="quarters", uid="piece", name="Piece"
    )
    piece.add_child(ContinuousLogicalTimeline(length=3, unit="quarters", uid="a"), 0)
    piece.add_child(ContinuousLogicalTimeline(length=5, unit="quarters", uid="b"), 3)
    piece.add_child(ContinuousLogicalTimeline(length=2, unit="quarters", uid="c"), 1)

    melody = ContinuousLogicalTimeline(
        length=8, unit="quarters", uid="melody", name="Melody"
    )
    phrase = ContinuousLogicalTimeline(
        length=4, unit="quarters", uid="phrase", name="Phrase"
    )
    melody.add_child(phrase, 2)
    melody.add_conversion_map(
        ScalarMap(
            Fraction(1, 2),
            source_unit="quarters",
            target_unit="seconds",
            uid="tempo",
            name="Tempo",
        )
    )
    phrase.add_conversion_map(QuartersToTicks(ppq=480, uid="ticks", name="Ticks"))
    return {"bare": [bare], "contiguous": [piece], "map": [melody]}


def styled_timelines() -> list[Timeline]:
    """Build the two timelines of the styled fixture, one per domain."""
    score = ContinuousLogicalTimeline(
        length=8, unit="quarters", uid="score", name="Score"
    )
    score.add_child(ContinuousLogicalTimeline(length=4, unit="quarters", uid="a"), 0)
    score.add_child(ContinuousLogicalTimeline(length=4, unit="quarters", uid="b"), 4)
    score.add_conversion_map(QuartersToTicks(ppq=480, uid="ticks", name="Ticks"))
    score.create_region(0, 2, id="intro", name="intro")
    score.flow_control.add_jump(
        Jump(
            from_coordinate=score.make_coordinate(8),
            to_coordinate=score.make_coordinate(0),
            control_type=FlowControlElement.da_capo,
            condition=ActivationCondition.always,
            repeat_count=1,
            target=None,
            label="D.C.",
            id="da-capo",
            meta={},
        )
    )
    performance = ContinuousPhysicalTimeline(
        length=10.0, unit="seconds", uid="performance", name="Performance"
    )
    performance.add_child(
        ContinuousPhysicalTimeline(length=4.0, unit="seconds", uid="excerpt"), 1.0
    )
    return [score, performance]


def segment_line_timeline() -> Timeline:
    """Build a nested segment line of quarters: a form of three sections.

    The root ``form`` (32 quarters) holds the segments ``a`` (8), ``b`` (12)
    and ``c`` (12), each a segment line itself: ``a`` holds ``a1`` and ``c``
    holds ``c1``, both without a name, and ``b`` holds ``b1`` and ``b2`` (6
    each). The absolute spans are a 0-8, b 8-20 (b1 8-14, b2 14-20) and c
    20-32. Quarters take their default number type, fraction.
    """
    line = SegmentLine[ContinuousLogicalTimeline]

    def section(uid: str, name: str, *segments: Timeline) -> Timeline:
        result = line(length=0, unit="quarters", uid=uid, name=name)
        for segment in segments:
            result.append_segment(segment)
        return result

    def segment(uid: str, length: int, name: str | None = None) -> Timeline:
        return ContinuousLogicalTimeline(
            length=length, unit="quarters", uid=uid, name=name
        )

    return section(
        "form",
        "Form",
        section("a", "A", segment("a1", 8)),
        section("b", "B", segment("b1", 6, "b1"), segment("b2", 6, "b2")),
        section("c", "C", segment("c1", 12)),
    )


def locked_root_timeline() -> Timeline:
    """Build a root of quarters locked at construction, holding one child.

    The root ``score`` ("Score", 16 quarters, ``locked=True``) holds the child
    ``coda`` ("Coda", 4 quarters) at offset 12, ending at the root's end.
    """
    score = ContinuousLogicalTimeline(
        length=16, unit="quarters", uid="score", name="Score", locked=True
    )
    score.add_child(
        ContinuousLogicalTimeline(length=4, unit="quarters", uid="coda", name="Coda"),
        12,
    )
    return score


def pages_timeline(count: int = 4) -> Timeline:
    """Build an unlocked segment line of pixel pages.

    The root ``pages`` ("Pages") holds the segments ``page_1`` ("Page 1") to
    ``page_<count>`` ("Page <count>"), each 1754 pixels, so the line is
    ``1754 * count`` pixels long.
    """
    pages = SegmentLine[DiscreteGraphicalTimeline](
        length=Fraction(0), unit="pixels", uid="pages", name="Pages"
    )
    for number in range(1, count + 1):
        pages.append_segment(
            DiscreteGraphicalTimeline(
                length=Fraction(1754),
                unit="pixels",
                uid=f"page_{number}",
                name=f"Page {number}",
            )
        )
    return pages


def locked_pages_timeline() -> Timeline:
    """Build the segment line of ``pages_timeline`` and lock it once built.

    The four pages of 1754 pixels each make the locked line 7016 pixels long.
    """
    pages = pages_timeline()
    pages.lock()
    return pages


def accolade_pages_timeline() -> Timeline:
    """Build an unlocked segment line of pixel pages, each a line of accolades.

    The root ``pages`` ("Pages", 7016 pixels) holds the segments ``page_1``
    ("Page 1") to ``page_4`` ("Page 4"), each a segment line of 1754 pixels
    whose segments are the accolades ``page_<N>_accolade_1`` to
    ``page_<N>_accolade_4``, named "1" to "4", of 400, 450, 452 and 452 pixels.
    """
    line = SegmentLine[DiscreteGraphicalTimeline]
    pages = line(length=Fraction(0), unit="pixels", uid="pages", name="Pages")
    for number in range(1, 5):
        page = line(
            length=Fraction(0),
            unit="pixels",
            uid=f"page_{number}",
            name=f"Page {number}",
        )
        for accolade, length in enumerate((400, 450, 452, 452), start=1):
            page.append_segment(
                DiscreteGraphicalTimeline(
                    length=Fraction(length),
                    unit="pixels",
                    uid=f"page_{number}_accolade_{accolade}",
                    name=str(accolade),
                )
            )
        pages.append_segment(page)
    return pages


def segment_children_timeline() -> Timeline:
    """Build an unlocked root of quarters whose three children are segment lines.

    The root ``piece`` ("Piece", 32 quarters) holds ``intro`` ("Intro") at
    offset 2 with the segments ``i1`` and ``i2`` (3 each), ``theme``
    ("Theme") at offset 6 with ``t1``, ``t2`` and ``t3`` (4 each), and
    ``coda`` ("Coda") at offset 22 with ``c1`` (5) and ``c2`` (3); each
    segment is named as its id. The absolute spans are intro 2-8, theme 6-18
    and coda 22-30, so intro and theme overlap.
    """
    piece = ContinuousLogicalTimeline(
        length=32, unit="quarters", uid="piece", name="Piece"
    )
    for uid, name, offset, segments in (
        ("intro", "Intro", 2, (("i1", 3), ("i2", 3))),
        ("theme", "Theme", 6, (("t1", 4), ("t2", 4), ("t3", 4))),
        ("coda", "Coda", 22, (("c1", 5), ("c2", 3))),
    ):
        child = SegmentLine[ContinuousLogicalTimeline](
            length=0, unit="quarters", uid=uid, name=name
        )
        for segment_id, length in segments:
            child.append_segment(
                ContinuousLogicalTimeline(
                    length=length, unit="quarters", uid=segment_id, name=segment_id
                )
            )
        piece.add_child(child, offset)
    return piece


_GREY = {"stroke": "#404040", "fill": "#404040"}
_SHARED_STATEMENTS: list[dict[str, Any]] = [
    {"select": {"element": "label"}, "set": _GREY},
    {"select": {"element": "name"}, "set": _GREY},
    {"select": {"element": "map"}, "set": {"side": "below"}},
    {"select": {"ids": ["a"]}, "set": {"display": "none"}},
]
_VIOLET = {"stroke": "#7F00FF", "fill": "#7F00FF"}
_ACCENT = {"stroke": "#1D4ED8", "fill": "#1D4ED8", "stroke-width": 4, "opacity": 0.8}

GRAPHICAL: dict[str, dict[str, dict[str, Any]]] = {
    "styled": {
        "score": {
            "styles": {"accent": _ACCENT},
            "statements": [
                *_SHARED_STATEMENTS,
                {"select": {"element": "block"}, "set": {"rx": 4}},
                {
                    "select": {
                        "class": "ContinuousLogicalTimeline",
                        "element": "timeline",
                    },
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
                {
                    "select": {"ids": ["score/intro/label"]},
                    "set": {"fill": "#0E7490"},
                },
                {
                    "select": {"ids": ["score/da-capo/label"]},
                    "set": {"fill": "#9D174D"},
                },
                {
                    "select": {"ids": ["score/name"]},
                    "set": {
                        "fill": "#111827",
                        "font-size": 12,
                        "content": "Styled score",
                        "max-width": 120,
                    },
                },
                {
                    "select": {"element": "name", "within": "b"},
                    "set": {"fill": "#0369A1"},
                },
            ],
        },
        "performance": {
            "statements": [
                *_SHARED_STATEMENTS,
                {
                    "select": {
                        "element": "wedge",
                        "domain": "physical",
                        "within": "performance",
                    },
                    "set": _VIOLET,
                },
            ]
        },
    },
    "group_styled": {
        "group_1": {
            "styles": {"frame-highlight": {"stroke": "#7F00FF"}},
            "statements": [
                {"select": {"element": "group"}, "set": "frame-highlight"},
                {
                    "select": {"element": "name", "ids": ["group_1/name"]},
                    "set": {"fill": "#7F00FF"},
                },
                {
                    "select": {"element": "card", "inside": "group"},
                    "set": {"shadow": "#C4B5FD", "rx": 2},
                },
            ],
        },
    },
}
"""The ``graphical`` styles and statements of each styled manifest, by fixture
name and the id of its root (a manifest of one root) or of its group (a
manifest of one group).

The script adds an entry to the manifest's ``graphical``; the library reads it
back as styling it keeps unread and writes it beside its own
``graphical.order``. An element other than a timeline, a group or the
manifest is addressed ``<root id>/<element id>`` (``score/intro``).

``group_styled`` gives every group frame the named style ``frame-highlight``
(a violet stroke), fills the group's title, ``group_1/name``, violet, and
gives every card held by a group frame a light violet shadow and a corner
radius of 2.

In ``styled__score`` every drawn element and every text takes its own colour
under the cascade of ``docs/drawing.md`` (statements numbered from 0 in the
list, the four shared ones first):

==========================  =========  ==========================================
Item                        Colour     Set by
==========================  =========  ==========================================
root line ``score``         #1D4ED8    5, the style ``accent`` (class and element)
child line ``b``            #EA580C    14 (element ``child`` within ``b``)
map ``score/ticks``         #7C3AED    6 (class ``QuartersToTicks``)
brace ``score/intro``       #0F766E    9, which outranks 8 by its position
jump ``score/da-capo``      #DB2777    10 (element ``jump``, domain ``logical``)
wedge ``score/start``       #65A30D    11 (element ``wedge`` within ``score``)
wedge ``score/end``         #B45309    12 (``ids``)
name ``score/name``         #111827    19 (``ids``; also ``content``)
name ``b/name``             #0369A1    20 (element ``name`` within ``b``)
label of ``score/start``    #4D7C0F    15 (element ``label`` within ``score``)
label of ``score/end``      #A16207    16 (``ids``)
label of ``score/intro``    #0E7490    17 (``ids``)
label of ``score/da-capo``  #9D174D    18 (``ids``)
==========================  =========  ==========================================

A stroke and the fill of one element share its colour. Statement 13 displays
every child of ``score``; the shared ``ids`` statement 3 outranks it and hides
the child ``a``.
"""


def corpus_manifests() -> dict[str, list[Timeline]]:
    """Load the smallest selected corpus specimens through public loaders.

    Of the Parangonada timelines only the discrete score ``score:dlt_1`` is
    emitted.
    """
    score = ensure_data("score")
    midi = ensure_data("midi")
    audio = ensure_data("audio")
    parangonar = ensure_data("parangonar")
    supra = ensure_data("supra")

    score_path = (
        score / "flow_control/flow_only/out_of_the_flow_experience-flow_only.notes.tsv"
    )
    score_timeline = Ms3Loader(auto_discover=True).load(score_path).create_timeline()
    midi_timeline = (
        ScoreMidiLoader().load(midi / "score/beethoven_mtd.mid").create_timeline()
    )
    audio_timeline = (
        AudioLoader().load(audio / "hard_techno/Bass Kick.mp3").create_timeline()
    )
    (parangonada_score,) = [
        timeline
        for timeline in ParangonadaLoader()
        .load(parangonar / "Beethoven_Eroica_op35-cpjku")
        .create_timelines()
        if timeline.id == "score:dlt_1"
    ]
    graphical_timeline = (
        IIIFManifestLoader().load(supra / "image/ifff_manifest.json").create_timeline()
    )
    return {
        "corpus_score_ms3": [score_timeline],
        "corpus_midi_score_midi": [midi_timeline],
        "corpus_audio_audio": [audio_timeline],
        "corpus_parangonar_parangonada__score_dlt_1": [parangonada_score],
        "corpus_supra_iiif": [graphical_timeline],
    }


def _ticks() -> QuartersToTicks:
    """Return a map of quarters to ticks, 480 per quarter, its id minted."""
    return QuartersToTicks(ppq=480)


def _tempo() -> ScalarMap:
    """Return a tempo map of quarters to seconds, half a second per quarter, its
    id minted.
    """
    return ScalarMap(Fraction(1, 2), source_unit="quarters", target_unit="seconds")


def _to_samples() -> SecondsToSamples:
    """Return a map of seconds to samples, 44100 per second, its id minted."""
    return SecondsToSamples(sample_rate=44100)


def _to_seconds() -> SamplesToSeconds:
    """Return a map of samples to seconds, 44100 per second, its id minted."""
    return SamplesToSeconds(sample_rate=44100)


def _to_points() -> ScalarMap:
    """Return a map of pixels to points, 3/4 of a point each, its id minted."""
    return ScalarMap(Fraction(3, 4), source_unit="pixels", target_unit="points")


def _with_maps(timeline: Timeline, *maps: Any) -> Timeline:
    """Attach ``maps`` to ``timeline`` in order and return the timeline."""
    for conversion_map in maps:
        timeline.add_conversion_map(conversion_map)
    return timeline


def _with_repeat(timeline: Timeline, source: Any, destination: Any) -> Timeline:
    """Give ``timeline`` a jump from ``source`` back to ``destination``.

    The jump is a repeat end taken the first time only (``first_n``, one
    repeat), labelled "Repeat", its id minted.
    """
    timeline.flow_control.add_jump(
        Jump(
            from_coordinate=timeline.make_coordinate(source),
            to_coordinate=timeline.make_coordinate(destination),
            control_type=FlowControlElement.repeat_end,
            condition=ActivationCondition.first_n,
            repeat_count=1,
            label="Repeat",
        )
    )
    return timeline


def _segments(line: Timeline, *segments: Timeline) -> Timeline:
    """Append ``segments`` in order to the segment line ``line`` and return it."""
    for segment in segments:
        line.append_segment(segment)
    return line


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
    jump is minted.
    """
    group = number_types_group()
    score = _with_maps(group.get_timeline("score"), _ticks())
    score.create_region(0, 8, name="Theme")
    _with_repeat(score, 8, 0)
    _with_maps(group.get_timeline("performance"), _to_samples())
    _with_maps(group.get_timeline("page"), _to_points())
    return group


def group_constructions() -> dict[str, list[TimelineGroup]]:
    """Build the groups constructed directly, one manifest each.

    ``group_number_types`` is the group of ``number_types_group``.
    ``group_child_member`` groups the second half of a score, a child of the
    score placed at its exact offset, with a whole performance.
    ``group_styled`` is the group of ``styled_group``, which adds conversion
    maps, a region and a jump to that of ``number_types_group``, and carries
    the styles and statements of ``GRAPHICAL``.
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
    child_member = TimelineGroup(name="Second half", timelines=[second_half, recording])
    return {
        "group_number_types": [number_types_group()],
        "group_child_member": [child_member],
        "group_styled": [styled_group()],
    }


def bundle_constructions() -> dict[str, list[AlignmentBundle]]:
    """Build the bundle constructed directly.

    ``bundle_mixed`` ("Mixed") holds two groups, a score with its performance
    and a page with an excerpt of a recording, and one ungrouped timeline. The
    score ``score`` (12 quarters) carries a map to ticks, then a tempo map to
    seconds (half a second per quarter), and a repeat jump from 8 back to 0;
    the performance ``performance`` (12.5 seconds) a map to samples; the page
    ``page`` (1920 pixels) a map to points; the recording ``recording``
    (441000 samples) and its excerpt ``excerpt`` (88200 samples at 44100) a
    map to seconds each; the ungrouped ``annotations`` (12 quarters) the
    regions "Verse" from 0 to 4 and "Chorus" from 4 to 12, and no map. No
    group names ``recording``, but it contains the member ``excerpt`` and so
    is drawn only as its ancestor line: its map is kept in the manifest but
    not drawn. Every id of a map, region or jump is minted.
    """
    score = _with_maps(
        ContinuousLogicalTimeline(
            length=Fraction(12), unit="quarters", uid="score", name="Score"
        ),
        _ticks(),
        _tempo(),
    )
    _with_repeat(score, 8, 0)
    performance = _with_maps(
        ContinuousPhysicalTimeline(
            length=12.5, unit="seconds", uid="performance", name="Performance"
        ),
        _to_samples(),
    )
    page = _with_maps(
        DiscreteGraphicalTimeline(
            length=Fraction(1920), unit="pixels", uid="page", name="Page"
        ),
        _to_points(),
    )
    recording = _with_maps(
        DiscretePhysicalTimeline(
            length=Fraction(441000), unit="samples", uid="recording", name="Recording"
        ),
        _to_seconds(),
    )
    excerpt = _with_maps(
        DiscretePhysicalTimeline(
            length=Fraction(88200), unit="samples", uid="excerpt", name="Excerpt"
        ),
        _to_seconds(),
    )
    recording.add_child(excerpt, Fraction(44100))
    annotations = ContinuousLogicalTimeline(
        length=Fraction(12), unit="quarters", uid="annotations", name="Annotations"
    )
    annotations.create_region(0, 4, name="Verse")
    annotations.create_region(4, 12, name="Chorus")
    bundle = AlignmentBundle(name="Mixed")
    bundle.add_timeline(score, as_group="Performance")
    bundle.add_timeline(performance, grouped_with=score.id)
    bundle.add_timeline(page, as_group="Facsimile")
    bundle.add_timeline(excerpt, grouped_with=page.id)
    bundle.add_timeline(annotations)
    return {"bundle_mixed": [bundle]}


def _timeline(cls: type[Timeline], uid: str, name: str, length: Any) -> Timeline:
    """Build an unlocked timeline of ``cls`` in its domain's usual unit."""
    unit = {
        ContinuousLogicalTimeline: "quarters",
        ContinuousPhysicalTimeline: "seconds",
        DiscreteLogicalTimeline: "ticks",
        DiscretePhysicalTimeline: "samples",
        DiscreteGraphicalTimeline: "pixels",
    }[cls]
    return cls(length=length, unit=unit, uid=uid, name=name)


def _holding(parent: Timeline, child: Timeline, offset: Any) -> Timeline:
    """Add ``child`` to ``parent`` at ``offset`` and return the child."""
    parent.add_child(child, offset)
    return child


def _piece_member_group(uid: str, name: str, length: int, offset: int) -> TimelineGroup:
    """Build a group of a child of a piece and a whole recording.

    The piece ``piece`` ("Piece", 16 quarters) holds the child ``uid``
    (``name``, ``length`` quarters) at ``offset``; the group, named as the
    child, lists the child and then the root ``recording`` ("Recording", 10.0
    seconds), as ``group_child_member`` does with the piece's second half.
    """
    piece = _timeline(ContinuousLogicalTimeline, "piece", "Piece", Fraction(16))
    child = _holding(
        piece,
        _timeline(ContinuousLogicalTimeline, uid, name, Fraction(length)),
        Fraction(offset),
    )
    recording = _timeline(ContinuousPhysicalTimeline, "recording", "Recording", 10.0)
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
    exposition = _holding(
        sonata,
        _timeline(ContinuousLogicalTimeline, "exposition", "Exposition", Fraction(32)),
        Fraction(16),
    )
    session = _timeline(ContinuousPhysicalTimeline, "session", "Session", 90.0)
    take = _holding(
        session,
        _with_maps(
            _timeline(ContinuousPhysicalTimeline, "take", "Take", 25.5), _to_samples()
        ),
        30.0,
    )
    page = _timeline(DiscreteGraphicalTimeline, "page", "Page", Fraction(1754))
    system = _holding(
        page,
        _timeline(DiscreteGraphicalTimeline, "system", "System", Fraction(600)),
        Fraction(0),
    )
    audio = _with_maps(
        _timeline(DiscretePhysicalTimeline, "audio", "Audio", Fraction(1323000)),
        _to_seconds(),
    )
    return TimelineGroup(name="Exposition", timelines=[exposition, take, system, audio])


def group_grandchild() -> TimelineGroup:
    """Build a group of a grandchild of quarters and a root in seconds.

    The score ``score`` ("Score", 64 quarters) holds the movement
    ``movement`` ("Movement", 16 quarters) at 16, which holds the theme
    ``theme`` ("Theme", 8 quarters) at 8; the group "Theme" lists ``theme``
    and the root ``recording`` ("Recording", 12.0 seconds).
    """
    score = _timeline(ContinuousLogicalTimeline, "score", "Score", Fraction(64))
    movement = _holding(
        score,
        _timeline(ContinuousLogicalTimeline, "movement", "Movement", Fraction(16)),
        Fraction(16),
    )
    theme = _holding(
        movement,
        _timeline(ContinuousLogicalTimeline, "theme", "Theme", Fraction(8)),
        Fraction(8),
    )
    recording = _timeline(ContinuousPhysicalTimeline, "recording", "Recording", 12.0)
    return TimelineGroup(name="Theme", timelines=[theme, recording])


def parent_groups() -> dict[str, list[TimelineGroup]]:
    """Return the groups whose members include children, one manifest each."""
    builders: dict[str, Callable[[], TimelineGroup]] = {
        "group_parent_right": group_parent_right,
        "group_parent_both": group_parent_both,
        "group_parent_exact": group_parent_exact,
        "group_parents_mixed": group_parents_mixed,
        "group_grandchild": group_grandchild,
    }
    return {name: [build()] for name, build in builders.items()}


def bundle_shared_parent() -> AlignmentBundle:
    """Build a bundle whose two groups hold two children of one root.

    The score ``score`` ("Score", 32 quarters) carries a map to ticks, the
    region "Development" from 12 to 20 and a repeat jump from 12 back to 0. It
    holds two segment lines: the exposition ``exposition`` ("Exposition", 12
    quarters) at 0, which carries a map to ticks, of the segments
    ``exposition_first`` ("First theme") and ``exposition_second`` ("Second
    theme"), 6 quarters each, the second carrying a tempo map to seconds (half
    a second per quarter); and the recapitulation ``recapitulation``
    ("Recapitulation", 12 quarters) at 20, of two segment lines of 6 quarters,
    each of two segments of 3 quarters: ``recapitulation_first`` ("First
    theme") of ``recapitulation_first_1`` ("Phrase 1") and
    ``recapitulation_first_2`` ("Phrase 2"), and ``recapitulation_second``
    ("Second theme"), which carries a map to ticks, of
    ``recapitulation_second_1`` ("Phrase 1") and ``recapitulation_second_2``
    ("Phrase 2"). The bundle "Sonata" groups ``exposition`` with the take
    ``take_1`` ("Take 1", 30.0 seconds) as "Exposition" and ``recapitulation``
    with the take ``take_2`` ("Take 2", 28.5 seconds) as "Recapitulation".
    ``take_1`` is a segment line, which carries a map to samples, of
    ``take_1_first`` ("First theme", 14.0 seconds) and ``take_1_second``
    ("Second theme", 16.0 seconds); ``take_2`` is a plain timeline. The page
    ``page`` ("Page", 1754 pixels) is ungrouped. No group names ``score``, but
    it contains both members and so is drawn only as their ancestor line: its
    map, region and repeat are kept in the manifest but not drawn. Every id of
    a map, region or jump is minted.
    """

    def quarters(uid: str, name: str, length: int) -> Timeline:
        return _timeline(ContinuousLogicalTimeline, uid, name, Fraction(length))

    def line(uid: str, name: str, *segments: Timeline) -> Timeline:
        return _segments(
            SegmentLine[ContinuousLogicalTimeline](
                length=0, unit="quarters", uid=uid, name=name
            ),
            *segments,
        )

    score = _with_maps(
        _timeline(ContinuousLogicalTimeline, "score", "Score", Fraction(32)), _ticks()
    )
    score.create_region(12, 20, name="Development")
    _with_repeat(score, 12, 0)
    exposition = _holding(
        score,
        _with_maps(
            line(
                "exposition",
                "Exposition",
                quarters("exposition_first", "First theme", 6),
                _with_maps(quarters("exposition_second", "Second theme", 6), _tempo()),
            ),
            _ticks(),
        ),
        Fraction(0),
    )
    recapitulation_first = line(
        "recapitulation_first",
        "First theme",
        quarters("recapitulation_first_1", "Phrase 1", 3),
        quarters("recapitulation_first_2", "Phrase 2", 3),
    )
    recapitulation_second = _with_maps(
        line(
            "recapitulation_second",
            "Second theme",
            quarters("recapitulation_second_1", "Phrase 1", 3),
            quarters("recapitulation_second_2", "Phrase 2", 3),
        ),
        _ticks(),
    )
    recapitulation = _holding(
        score,
        line(
            "recapitulation",
            "Recapitulation",
            recapitulation_first,
            recapitulation_second,
        ),
        Fraction(20),
    )
    take_1 = _with_maps(
        _segments(
            SegmentLine[ContinuousPhysicalTimeline](
                length=0.0, unit="seconds", uid="take_1", name="Take 1"
            ),
            _timeline(ContinuousPhysicalTimeline, "take_1_first", "First theme", 14.0),
            _timeline(
                ContinuousPhysicalTimeline, "take_1_second", "Second theme", 16.0
            ),
        ),
        _to_samples(),
    )
    take_2 = _timeline(ContinuousPhysicalTimeline, "take_2", "Take 2", 28.5)
    page = _timeline(DiscreteGraphicalTimeline, "page", "Page", Fraction(1754))
    bundle = AlignmentBundle(name="Sonata")
    bundle.add_timeline(exposition, as_group="Exposition")
    bundle.add_timeline(take_1, grouped_with="exposition")
    bundle.add_timeline(recapitulation, as_group="Recapitulation")
    bundle.add_timeline(take_2, grouped_with="recapitulation")
    bundle.add_timeline(page)
    return bundle


def bundle_ungrouped() -> AlignmentBundle:
    """Build a bundle of three ungrouped roots, one of them a segment line.

    The bundle "Sketches" holds the score ``score`` ("Score", 16 quarters),
    the recording ``recording`` ("Recording", 441000 samples) and the
    segment line ``pages`` of ``pages_timeline`` with three pages (5262
    pixels), in that order, and no group. The score carries a map to ticks
    and a da capo al fine: the break "Fine" at 8 (``fine``, taken after a
    da capo or dal segno) and the jump "D.C. al Fine" from 16 back to 0
    (``da_capo_al_fine``, taken after the first pass, one repeat). The
    recording carries a map to seconds, the segment line ``pages`` a map to
    points; its pages carry none. Every id of a map, break or jump is minted.
    """
    score = _with_maps(
        _timeline(ContinuousLogicalTimeline, "score", "Score", Fraction(16)), _ticks()
    )
    score.flow_control.add_break(
        Break(
            coordinate=score.make_coordinate(8),
            control_type=FlowControlElement.fine,
            condition=ActivationCondition.after_dc_ds,
            label="Fine",
        )
    )
    score.flow_control.add_jump(
        Jump(
            from_coordinate=score.make_coordinate(16),
            to_coordinate=score.make_coordinate(0),
            control_type=FlowControlElement.da_capo_al_fine,
            condition=ActivationCondition.after_first,
            repeat_count=1,
            label="D.C. al Fine",
        )
    )
    bundle = AlignmentBundle(name="Sketches")
    bundle.add_timeline(score)
    bundle.add_timeline(
        _with_maps(
            _timeline(
                DiscretePhysicalTimeline, "recording", "Recording", Fraction(441000)
            ),
            _to_seconds(),
        )
    )
    bundle.add_timeline(_with_maps(pages_timeline(3), _to_points()))
    return bundle


def parent_bundles() -> dict[str, list[AlignmentBundle]]:
    """Return the bundles of children and of ungrouped roots, one manifest each."""
    builders: dict[str, Callable[[], AlignmentBundle]] = {
        "bundle_shared_parent": bundle_shared_parent,
        "bundle_ungrouped": bundle_ungrouped,
    }
    return {name: [build()] for name, build in builders.items()}


LISTEN_HERE: dict[str, Any] = {
    "header": {"ref": "rec-ref.mp3", "createdBy": "Listen Here! v0.20.0"},
    "body": {
        "audio": {
            "rec-a.mp3": {"times": [0.0, 0.02, 0.04], "peaks": [], "duration": 0.04},
            "rec-ref.mp3": {"times": [0.0, 0.025, 0.05], "peaks": [], "duration": 0.05},
        }
    },
}
"""A Listen Here! export of two recordings on a three-column reference grid.

No corpus holds a Listen Here! export, so the script writes this one to a
temporary directory and loads it.
"""


TILIA = "bruckner5_scherzo/harnoncourt/Bruckner5_Scherzo.json"
"""The TiLiA export, in the ``score`` corpus, whose group and bundle are emitted."""


def corpus_groups() -> dict[str, list[TimelineGroup]]:
    """Load the groups the loaders build from corpus specimens."""
    tilia = ensure_data("score") / TILIA
    return {"corpus_tilia": [TiliaJsonLoader.from_file(tilia).create_group()]}


def corpus_bundles() -> dict[str, list[AlignmentBundle]]:
    """Load the bundles the alignment loaders build from corpus specimens."""
    parangonar = ensure_data("parangonar") / "Beethoven_Eroica_op35-cpjku"
    vienna = ensure_data("vienna_1x22") / "Chopin_op10_no3_p01.match"
    mpm = (
        ensure_data("mpm_toolbox")
        / "MPRproject_1971Curzon_VariationXIV"
        / "Beethoven_op35_1971Curzon_Var14only.mpr"
    )
    ieee1599 = ensure_data("ieee1599") / "Khorus Music/khomus.xml"
    tilia = ensure_data("score") / TILIA
    with tempfile.TemporaryDirectory() as directory:
        listen_here_path = Path(directory) / "alignment.json"
        listen_here_path.write_text(json.dumps(LISTEN_HERE), encoding="utf-8")
        listen_here = ListenHereLoader.from_file(listen_here_path).create_bundle()
    builders: dict[str, Callable[[], AlignmentBundle]] = {
        "corpus_parangonada": ParangonadaLoader.from_file(parangonar).create_bundle,
        "corpus_matchfile": MatchfileLoader.from_file(vienna).create_bundle,
        "corpus_mpm": MpmLoader.from_file(mpm).create_bundle,
        "corpus_ieee1599": lambda: Ieee1599Loader.from_file(ieee1599).create_bundle(),
        "corpus_listen_here": lambda: listen_here,
        "corpus_tilia": TiliaJsonLoader.from_file(tilia).create_bundle,
    }
    return {name: [build()] for name, build in builders.items()}


def negative_offset_timeline() -> Timeline:
    """Build a root whose origin lies before the zero of its unit's axis.

    The recording ``recording`` ("Recording", 30.0 seconds) carries the
    offset -2.5. The library keeps a root's offset as read from a manifest,
    so the recording is written, given its offset and read back.
    """
    recording = ContinuousPhysicalTimeline(
        length=30.0, unit="seconds", uid="recording", name="Recording"
    )
    data = recording.to_dict()
    data["timelines"][0]["offset"] = -2.5
    return Timeline.from_dict(data)


def named_without_id_bundle() -> AlignmentBundle:
    """Build a named manifest without an id: a bundle of one ungrouped root.

    The bundle "Sketch", given no id, holds the score ``score`` ("Score", 16
    quarters).
    """
    bundle = AlignmentBundle(name="Sketch")
    bundle.add_timeline(
        _timeline(ContinuousLogicalTimeline, "score", "Score", Fraction(16))
    )
    return bundle


def _quarters(uid: str, length: Any, **keywords: Any) -> Timeline:
    """Build an unnamed timeline of quarters; a length of None is unknown."""
    return ContinuousLogicalTimeline(
        length=length, unit="quarters", uid=uid, **keywords
    )


def _with_region(timeline: Timeline, start: Any, end: Any, uid: str) -> Timeline:
    """Give ``timeline`` the region ``uid`` from ``start`` to ``end``."""
    timeline.create_region(start, end, id=uid)
    return timeline


def unknown_length_timelines() -> dict[str, list[Timeline]]:
    """Build the manifests of one root drawing timelines of unknown length.

    - ``unknown_length``: the root ``score`` of unknown length holds the
      region ``region_1`` from 2 to 8, the marker ``marker_1`` at 6 and the
      child ``coda`` (4 quarters) at 10; its content reaches 14.
    - ``unknown_length_empty``: the root ``score`` of unknown length and
      nothing else.
    - ``unknown_length_locked``: ``locked_root`` with its length unknown,
      the locked root ``score`` holding ``coda`` (4 quarters) at 12.
    - ``unknown_length_child``: the root ``score`` (32 quarters) holds the
      child ``movement`` of unknown length at 8, with the region
      ``region_1`` from 0 to 6.
    - ``unknown_length_segments``: the segment line ``form`` of unknown
      length holds ``a`` of unknown length at 0 (region ``region_1`` from 0
      to 4), ``b`` (6 quarters) at 8 and ``c`` of unknown length at 14
      (region ``region_2`` from 0 to 3).

    Every timeline is of quarters and unnamed.
    """
    score = _with_region(_quarters("score", None), 2, 8, "region_1")
    score.flow_control.add_marker(Marker(score.make_coordinate(6), id="marker_1"))
    score.add_child(_quarters("coda", 4), 10)

    locked = _quarters("score", None, locked=True)
    locked.add_child(_quarters("coda", 4), 12)

    known = _quarters("score", Fraction(32))
    known.add_child(_with_region(_quarters("movement", None), 0, 6, "region_1"), 8)

    form = SegmentLine[ContinuousLogicalTimeline](
        length=None, unit="quarters", uid="form"
    )
    form.add_child(_with_region(_quarters("a", None), 0, 4, "region_1"), 0)
    form.add_child(_quarters("b", 6), 8)
    form.add_child(_with_region(_quarters("c", None), 0, 3, "region_2"), 14)
    return {
        "unknown_length": [score],
        "unknown_length_empty": [_quarters("score", None)],
        "unknown_length_locked": [locked],
        "unknown_length_child": [known],
        "unknown_length_segments": [form],
    }


def group_unknown_length() -> TimelineGroup:
    """Build a group whose member is of unknown length.

    The group "Edition" lists the performance ``performance`` of unknown
    length (seconds, with the region ``region_1`` from 0.0 to 9.5) and the
    score ``score`` (12 quarters), both unnamed.
    """
    performance = ContinuousPhysicalTimeline(
        length=None, unit="seconds", uid="performance"
    )
    _with_region(performance, 0.0, 9.5, "region_1")
    return TimelineGroup(
        name="Edition", timelines=[performance, _quarters("score", Fraction(12))]
    )


def build_groups() -> dict[str, list[Any]]:
    """Return the names and groups of the manifests of one group.

    The constructions come before the corpora, the group with a member of
    unknown length last.
    """
    return {
        **group_constructions(),
        **parent_groups(),
        **corpus_groups(),
        "group_unknown_length": [group_unknown_length()],
    }


def build_bundles() -> dict[str, list[Any]]:
    """Return the names and bundles of the bundle manifests.

    The constructions come before the corpora.
    """
    return {**bundle_constructions(), **parent_bundles(), **corpus_bundles()}


def build_timelines() -> dict[str, list[Any]]:
    """Return the names and objects of the manifests of one root and no group.

    The synthetic manifests come first, then the corpus manifests, then the
    manifests of the manifest's own keys and of unknown lengths.
    """
    manifests: dict[str, list[Any]] = {}
    manifests["continuous_logical"] = [
        with_children(
            ContinuousLogicalTimeline, "quarters", 12, [(4, Fraction(1, 3)), (3, 2)]
        )
    ]
    manifests["discrete_logical"] = [
        with_children(
            DiscreteLogicalTimeline,
            "ticks",
            Fraction(480),
            [(Fraction(120), Fraction(3)), (Fraction(96), Fraction(7))],
        )
    ]
    manifests["continuous_physical"] = [
        with_children(
            ContinuousPhysicalTimeline, "seconds", 12.5, [(4.25, 0.5), (3.0, 6.0)]
        )
    ]
    manifests["discrete_physical"] = [
        with_children(
            DiscretePhysicalTimeline,
            "samples",
            Fraction(44100),
            [(Fraction(11025), Fraction(100)), (Fraction(2205), Fraction(20000))],
        )
    ]
    manifests["continuous_graphical"] = [
        with_children(
            ContinuousGraphicalTimeline,
            "points",
            600.0,
            [(200.0, 10.0), (150.0, 300.0)],
        )
    ]
    manifests["discrete_graphical"] = [
        with_children(
            DiscreteGraphicalTimeline,
            "pixels",
            Fraction(1920),
            [(Fraction(640), Fraction(16)), (Fraction(480), Fraction(1000))],
        )
    ]
    with_region = with_children(
        ContinuousLogicalTimeline, "quarters", 12, [(4, Fraction(1, 3)), (3, 2)]
    )
    with_region.create_region(2, 6, name="theme")
    manifests["with_region"] = [with_region]
    grandchild = ContinuousLogicalTimeline(length=2, unit="quarters")
    child = ContinuousLogicalTimeline(length=8, unit="quarters")
    child.add_child(grandchild, Fraction(3, 2))
    nested = ContinuousLogicalTimeline(length=16, unit="quarters")
    nested.add_child(child, 4)
    manifests["nested"] = [nested]
    manifests["conversion_maps"] = conversion_map_timelines()
    manifests["flow_control"] = [flow_control_timeline()]
    manifests.update(drawing_manifests())
    manifests["styled"] = styled_timelines()
    manifests["segment_line"] = [segment_line_timeline()]
    manifests["locked_root"] = [locked_root_timeline()]
    manifests["segment_pages"] = [pages_timeline()]
    manifests["segment_pages_locked"] = [locked_pages_timeline()]
    manifests["segment_pages_accolades"] = [accolade_pages_timeline()]
    manifests["segment_children"] = [segment_children_timeline()]
    manifests.update(corpus_manifests())
    manifests["negative_offset"] = [negative_offset_timeline()]
    manifests["named_without_id"] = [named_without_id_bundle()]
    manifests.update(unknown_length_timelines())
    return manifests


def build_fixtures() -> dict[str, list[Any]]:
    """Return every fixture's name, prefixed by its directory, and its objects.

    The manifests of one root come first, then those of one group
    (``groups/``), then the bundles (``bundles/``).
    """
    return {
        **build_timelines(),
        **{f"groups/{name}": items for name, items in build_groups().items()},
        **{f"bundles/{name}": items for name, items in build_bundles().items()},
    }


def slug(identifier: str) -> str:
    """Return a fixture-safe spelling of an id."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", identifier)


def compose(data: dict[str, Any], generator: str, graphical: Any) -> dict[str, Any]:
    """Add the provenance and any styling to a manifest the library wrote."""
    result = copy.deepcopy(data)
    result["meta"]["generator"] = generator
    if graphical is not None:
        result.setdefault("graphical", {}).update(copy.deepcopy(graphical))
    return result


def plan(output: Path, generator: str) -> list[tuple[Path, Any, Any, dict[str, Any]]]:
    """Return every fixture to write: its path, reader, object and manifest.

    The object is read back from the composed manifest by the reader, the
    class of the fixture's directory, so that the library writes every
    fixture and twin.
    """
    planned: list[tuple[Path, Any, Any, dict[str, Any]]] = []
    claimed: dict[Path, str] = {}
    for name, objects in build_fixtures().items():
        directory, _, builder = name.rpartition("/")
        for item in objects:
            filename = name if len(objects) == 1 else f"{name}__{slug(item.id)}"
            path = output / f"{filename}.json"
            if path in claimed:
                raise SystemExit(
                    f"ids {claimed[path]!r} and {item.id!r} of {name!r} both produce "
                    f"the file name {path.name}; nothing was written."
                )
            claimed[path] = item.id
            graphical = GRAPHICAL.get(builder, {}).get(item.id)
            data = compose(item.to_dict(), generator, graphical)
            reader = READERS[directory]
            planned.append((path, reader, reader.from_dict(data), data))
    return planned


def twin_path(path: Path) -> Path:
    """Return the path of a fixture's minimal twin, ``<name>.minimal.json``."""
    return path.with_name(f"{path.stem}.minimal.json")


def library_order(value: dict[str, Any]) -> str:
    """Return a manifest's JSON text with sorted keys and arrays as they stand."""
    return json.dumps(value, sort_keys=True)


def check(path: Path, reader: Any) -> None:
    """Confirm the laws a fixture and its minimal twin obey.

    Both validate without unknown keys; ``minimal`` of the fixture is the
    twin and ``complete`` of the twin the fixture; the library reads both to
    objects writing the same manifests, writes each as it stands (its arrays
    already in canonical order), and the text ``dumps`` writes is the file's.
    """
    text = path.read_text(encoding="utf-8")
    twin_text = twin_path(path).read_text(encoding="utf-8")
    fixture, twin = json.loads(text), json.loads(twin_text)
    problems: list[str] = []
    for label, value in (("fixture", fixture), ("twin", twin)):
        validate(value)
        if unknown_keys(value):
            problems.append(f"the {label} has unknown keys {unknown_keys(value)}")
    if dumps(minimal(fixture)) != twin_text:
        problems.append("minimal(fixture) is not the twin")
    if dumps(complete(twin)) != text:
        problems.append("complete(twin) is not the fixture")
    for label, value in (("fixture", fixture), ("twin", twin)):
        read = reader.from_dict(value)
        written = read.to_dict()
        written_minimal = read.to_dict(minimal=True)
        if library_order(written) != library_order(fixture):
            problems.append(f"the {label} read and written is not the fixture")
        if library_order(written_minimal) != library_order(twin):
            problems.append(f"the {label} read and written minimal is not the twin")
        if library_order(canonical_order(written)) != library_order(written):
            problems.append(f"the {label} read is written out of canonical order")
    if problems:
        raise SystemExit(f"{path.name}: " + "; ".join(problems))


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, emit the fixtures and their twins, and check them."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--timetoalign-commit",
        required=True,
        help="short commit of the timetoalign checkout the interpreter runs",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=FIXTURE_DIR,
        help=f"destination directory (default: fixtures/{SCHEMA_VERSION}/)",
    )
    args = parser.parse_args(argv)
    generator = f"timetoalign {version('timetoalign')} ({args.timetoalign_commit})"
    tag = f"v{SCHEMA_VERSION}"
    tagged = subprocess.run(
        ["git", "-C", str(REPOSITORY_ROOT), "tag", "--list", tag],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    if tag in tagged and args.output.resolve() == FIXTURE_DIR.resolve():
        raise SystemExit(
            f"{tag} is released; its fixtures in {FIXTURE_DIR} are frozen. "
            "Emit into another directory with --output."
        )

    planned = plan(args.output, generator)
    for directory in READERS:
        (args.output / directory).mkdir(parents=True, exist_ok=True)
        for stale in (args.output / directory).glob("*.json"):
            stale.unlink()
    for path, _, item, _ in planned:
        path.write_text(dumps(item.to_dict()), encoding="utf-8")
        twin_path(path).write_text(dumps(item.to_dict(minimal=True)), encoding="utf-8")

    for path, reader, _, data in planned:
        check(path, reader)
        if dumps(complete(data)) != path.read_text(encoding="utf-8"):
            raise SystemExit(
                f"{path.name}: the library did not write back its manifest"
            )
        display = (
            path.relative_to(REPOSITORY_ROOT)
            if path.is_relative_to(REPOSITORY_ROOT)
            else path
        )
        print(f"{display}: the fixture and its minimal twin hold")
    print(f"generator: {generator}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
