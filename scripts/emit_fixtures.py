#!/usr/bin/env python
"""Emit the fixtures of the current schema through timetoalign.

Three file kinds are emitted into ``fixtures/<version>/``: timeline files
directly in it, group files in its ``groups/`` and bundle files in its
``bundles/`` directory. Every timeline is built with public constructors or a
public loader and serialized with ``Timeline.to_dict()``; every group with
``TimelineGroup.to_dict()`` and every bundle with ``AlignmentBundle.to_dict()``.
Each file is wrapped with ``meta``, written with ``timeskeleton.dumps``, read
back, validated and round-tripped through the matching ``from_dict``; a file
whose order differs from the library's fails the round trip. A file is emitted
only when its structural signature differs from that of every file of its kind
before it; the script names each file it skips on standard error. A styled
manifest also carries a ``graphical`` block composed in this script from
``GRAPHICAL``. ``--kinds`` restricts the run to some file kinds; the others
are left as they are. The current schema version is
``timeskeleton.SCHEMA_VERSION``. The fixtures of a released version are
frozen: the script refuses to write into ``fixtures/<version>/`` once the tag
``v<version>`` exists. Map identifiers come from a per-process counter, so
every run in a fresh interpreter emits the same files.
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
from timetoalign.timelines.flowcontrol import Break, Jump, Marker

from timeskeleton import FILE_KINDS, SCHEMA_VERSION, dumps, validate

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPOSITORY_ROOT / "fixtures" / SCHEMA_VERSION
SUBDIRECTORY = {"timeline": None, "group": "groups", "bundle": "bundles"}
"""Where each file kind lies below a version's fixture directory."""


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
                    "select": {"ids": ["intro/label"]},
                    "set": {"fill": "#0E7490"},
                },
                {"select": {"ids": ["da-capo/label"]}, "set": {"fill": "#9D174D"}},
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
}
"""The ``graphical`` block of each styled manifest, by fixture name and root id.

In ``styled__score`` every drawn element and every text takes its own colour
under the cascade of ``docs/drawing.md`` (statements numbered from 0 in the
list, the four shared ones first):

========================  =========  ==========================================
Item                      Colour     Set by
========================  =========  ==========================================
root line ``score``       #1D4ED8    5, the style ``accent`` (class and element)
child line ``b``          #EA580C    14 (element ``child`` within ``b``)
map ``ticks``             #7C3AED    6 (class ``QuartersToTicks``)
brace ``intro``           #0F766E    9, which outranks 8 by its position
jump ``da-capo``          #DB2777    10 (element ``jump``, domain ``logical``)
wedge ``score/start``     #65A30D    11 (element ``wedge`` within ``score``)
wedge ``score/end``       #B45309    12 (``ids``)
name ``score/name``       #111827    19 (``ids``; also ``content``)
name ``b/name``           #0369A1    20 (element ``name`` within ``b``)
label of ``score/start``  #4D7C0F    15 (element ``label`` within ``score``)
label of ``score/end``    #A16207    16 (``ids``)
label of ``intro``        #0E7490    17 (``ids``)
label of ``da-capo``      #9D174D    18 (``ids``)
========================  =========  ==========================================

A stroke and the fill of one element share its colour. Statement 13 displays
every child of ``score``; the shared ``ids`` statement 3 outranks it and hides
the child ``a``.
"""


def corpus_manifests() -> dict[str, list[Timeline]]:
    """Load the smallest selected corpus specimens through public loaders."""
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
    parangonada_timelines = (
        ParangonadaLoader()
        .load(parangonar / "Beethoven_Eroica_op35-cpjku")
        .create_timelines()
    )
    graphical_timeline = (
        IIIFManifestLoader().load(supra / "image/ifff_manifest.json").create_timeline()
    )
    return {
        "corpus_score_ms3": [score_timeline],
        "corpus_midi_score_midi": [midi_timeline],
        "corpus_audio_audio": [audio_timeline],
        "corpus_parangonar_parangonada": parangonada_timelines,
        "corpus_supra_iiif": [graphical_timeline],
    }


def group_constructions() -> dict[str, list[TimelineGroup]]:
    """Build the groups constructed directly, one per group file.

    ``group_number_types`` groups three timelines whose axes have different
    number types (quarters as fractions, seconds as floats, pixels as
    integers), listed in a display order that differs from their id order.
    ``group_child_member`` groups the second half of a score, a child of the
    score placed at its exact offset, with a whole performance.
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
    number_types = TimelineGroup(name="Edition", timelines=[score, page, performance])

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
    return {"group_number_types": [number_types], "group_child_member": [child_member]}


def bundle_constructions() -> dict[str, list[AlignmentBundle]]:
    """Build the bundle constructed directly.

    ``bundle_mixed`` holds two groups, a score with its performance and a page
    with an excerpt of a recording (a child of the recording, whose root
    joins the bundle ungrouped), and one more ungrouped timeline.
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
    recording = DiscretePhysicalTimeline(
        length=Fraction(441000), unit="samples", uid="recording", name="Recording"
    )
    excerpt = DiscretePhysicalTimeline(
        length=Fraction(88200), unit="samples", uid="excerpt", name="Excerpt"
    )
    recording.add_child(excerpt, Fraction(44100))
    annotations = ContinuousLogicalTimeline(
        length=Fraction(12), unit="quarters", uid="annotations", name="Annotations"
    )
    bundle = AlignmentBundle(name="Mixed")
    bundle.add_timeline(score, as_group="Performance")
    bundle.add_timeline(performance, grouped_with=score.id)
    bundle.add_timeline(page, as_group="Facsimile")
    bundle.add_timeline(excerpt, grouped_with=page.id)
    bundle.add_timeline(annotations)
    return {"bundle_mixed": [bundle]}


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


def build_groups() -> dict[str, list[TimelineGroup]]:
    """Return group fixture names and groups, constructions before corpora."""
    return {**group_constructions(), **corpus_groups()}


def build_bundles() -> dict[str, list[AlignmentBundle]]:
    """Return bundle fixture names and bundles, constructions before corpora."""
    return {**bundle_constructions(), **corpus_bundles()}


def build_manifests() -> dict[str, list[Timeline]]:
    """Return fixture names and top-level timelines in emission order.

    The synthetic manifests come first and the corpus manifests last, so that a
    synthetic manifest wins over a corpus manifest of the same structural
    signature (see ``signature``).
    """
    manifests: dict[str, list[Timeline]] = {}
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
    manifests.update(corpus_manifests())
    return manifests


def wrap(content: dict[str, Any], generator: str) -> dict[str, Any]:
    """Prefix a file's content with its ``meta``."""
    return {
        "meta": {"schema_version": SCHEMA_VERSION, "generator": generator},
        **content,
    }


def manifest(
    timeline: Timeline,
    generator: str,
    graphical: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Wrap one timeline, and a graphical block if any, in a manifest."""
    result = wrap({"timeline": timeline.to_dict()}, generator)
    if graphical is not None:
        result["graphical"] = copy.deepcopy(graphical)
    return result


def write(path: Path, data: dict[str, Any]) -> None:
    """Write one fixture with the standard writer, in canonical order."""
    path.write_text(dumps(data), encoding="utf-8")


ROUND_TRIPS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "timeline": lambda data: {
        "timeline": Timeline.from_dict(data["timeline"]).to_dict()
    },
    "group": lambda data: TimelineGroup.from_dict(data).to_dict(),
    "bundle": lambda data: AlignmentBundle.from_dict(data).to_dict(),
}
"""Rebuild a file's content (without ``meta``) through the library, by kind.

A timeline file's ``graphical`` block is composed in this script, so only its
``timeline`` takes part; a group's or bundle's ``graphical.order`` is the
library's own.
"""


def check_round_trip(path: Path, kind: str) -> int:
    """Confirm that a file validates and survives from_dict/to_dict.

    Object keys carry no order (the file has them sorted), so both sides are
    compared with sorted keys; arrays are compared as they stand, so a library
    whose order differs from the canonical order fails.
    """
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    validate(data)
    content = {key: value for key, value in data.items() if key != "meta"}
    if kind == "timeline":
        content = {"timeline": content["timeline"]}
    rebuilt = ROUND_TRIPS[kind](content)
    if json.dumps(rebuilt, sort_keys=True) != json.dumps(content, sort_keys=True):
        raise SystemExit(
            f"{path.name}: the {kind} file does not round-trip through "
            f"timetoalign.\nexpected: {json.dumps(content, indent=2)}\n"
            f"got:      {json.dumps(rebuilt, indent=2)}"
        )
    return 1


def timeline_signature(timeline: dict[str, Any]) -> tuple[Any, ...]:
    """Return the structure of one timeline dict and of its descendants.

    Values, ids, names, units, lengths and offsets are left out; the class, the
    lock, the conversion-map types and the numbers of regions, breaks, jumps
    and markers remain, with the children's signatures in canonical order.
    """
    flow_control = timeline["flow_control"]
    return (
        timeline["class"],
        timeline["locked"],
        tuple(conversion_map["type"] for conversion_map in timeline["conversion_maps"]),
        len(timeline["regions"]),
        len(flow_control["breaks"]),
        len(flow_control["jumps"]),
        len(flow_control["markers"]),
        tuple(
            timeline_signature(child["timeline"])
            for child in timeline["children"].values()
        ),
    )


def _timeline_trees(roots: list[dict[str, Any]]) -> dict[str, tuple[str, int]]:
    """Return the class and depth of every timeline of the roots, by id."""
    found: dict[str, tuple[str, int]] = {}

    def visit(timeline: dict[str, Any], depth: int) -> None:
        found[timeline["id"]] = (timeline["class"], depth)
        for child in timeline["children"].values():
            visit(child["timeline"], depth + 1)

    for root in roots:
        visit(root, 0)
    return found


def _members(group: dict[str, Any], trees: dict[str, tuple[str, int]]) -> tuple:
    """Return the class and depth of each member of a group, sorted."""
    return tuple(sorted(trees[member] for member in group["members"]))


def signature(data: dict[str, Any]) -> tuple[Any, ...]:
    """Return the structural signature of a file.

    Two files of one kind with one signature exercise the same combination of
    timeline classes, conversion-map types and timeline components, so only
    the first of them is emitted. A timeline file's ``graphical`` block takes
    part as its canonical JSON text. A group or bundle file contributes the
    signatures of its roots, and the class and depth (0 for a root) of the
    members of each of its groups; a bundle also the number of its ungrouped
    roots.
    """
    if "timeline" in data:
        graphical = data.get("graphical")
        return (
            timeline_signature(data["timeline"]),
            None if graphical is None else json.dumps(graphical, sort_keys=True),
        )
    roots = data["timelines"]
    trees = _timeline_trees(roots)
    structure = tuple(sorted(timeline_signature(root) for root in roots))
    if "group" in data:
        return (structure, _members(data["group"], trees))
    groups = data["bundle"]["groups"]
    grouped = {member for group in groups for member in group["members"]}
    ungrouped = sum(1 for root in roots if root["id"] not in grouped)
    return (
        structure,
        tuple(sorted(_members(group, trees) for group in groups)),
        ungrouped,
    )


def slug(identifier: str) -> str:
    """Return a fixture-safe spelling of a timeline id."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", identifier)


def plan(kind: str, output: Path, generator: str) -> list[tuple[Path, dict[str, Any]]]:
    """Return the files of one kind to write, one per new structural signature."""
    directory = output if SUBDIRECTORY[kind] is None else output / SUBDIRECTORY[kind]
    builders: dict[str, Callable[[], dict[str, list[Any]]]] = {
        "timeline": build_manifests,
        "group": build_groups,
        "bundle": build_bundles,
    }
    planned: list[tuple[Path, dict[str, Any]]] = []
    claimed: dict[Path, str] = {}
    for name, objects in builders[kind]().items():
        for item in objects:
            filename = name if len(objects) == 1 else f"{name}__{slug(item.id)}"
            path = directory / f"{filename}.json"
            if path in claimed:
                raise SystemExit(
                    f"ids {claimed[path]!r} and {item.id!r} of {name!r} both produce "
                    f"the file name {path.name}; nothing was written."
                )
            claimed[path] = item.id
            if kind == "timeline":
                graphical = GRAPHICAL.get(name, {}).get(item.id)
                data = manifest(item, generator, graphical)
            else:
                data = wrap(item.to_dict(), generator)
            planned.append((path, data))

    emitted: list[tuple[Path, dict[str, Any]]] = []
    first_of: dict[tuple[Any, ...], Path] = {}
    for path, data in planned:
        key = signature(data)
        if key in first_of:
            print(
                f"skipped {kind} {path.stem}: same structure as {first_of[key].stem}",
                file=sys.stderr,
            )
            continue
        first_of[key] = path
        emitted.append((path, data))
    return emitted


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, emit the fixtures, and verify their round trips."""
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
    parser.add_argument(
        "--kinds",
        nargs="+",
        choices=FILE_KINDS,
        default=list(FILE_KINDS),
        help="the file kinds to emit (default: all); the others are left as they are",
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

    emitted = {kind: plan(kind, args.output, generator) for kind in args.kinds}
    written: list[tuple[Path, str]] = []
    for kind, files in emitted.items():
        subdirectory = SUBDIRECTORY[kind]
        directory = args.output if subdirectory is None else args.output / subdirectory
        directory.mkdir(parents=True, exist_ok=True)
        for stale in directory.glob("*.json"):
            stale.unlink()
        for path, data in files:
            write(path, data)
            written.append((path, kind))

    for path, kind in written:
        count = check_round_trip(path, kind)
        display = (
            path.relative_to(REPOSITORY_ROOT)
            if path.is_relative_to(REPOSITORY_ROOT)
            else path
        )
        print(f"{display}: {count} {kind} file round-trips")
    print(f"generator: {generator}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
