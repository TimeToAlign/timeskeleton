"""Builders for fixtures containing one root timeline and no group."""

from __future__ import annotations

from fractions import Fraction
from typing import Any

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
)
from timetoalign.core import FlowControlElement
from timetoalign.loader.alignment import (
    ParangonadaLoader,
)
from timetoalign.loader.graphical.iiif import IIIFManifestLoader
from timetoalign.loader.midi.score import ScoreMidiLoader
from timetoalign.loader.physical.audio import AudioLoader
from timetoalign.maps import (
    ChainMap,
    CombinationMap,
    ConstantMap,
    FloatingMeasureMap,
    LinearMap,
    MeasureBeatMap,
    MeasureNumberMap,
    PiecewiseMap,
    QuartersToTicks,
    SamplesToSeconds,
    ScalarMap,
    SecondsToSamples,
    TableMap,
    TicksToQuarters,
)
from timetoalign.testdata import ensure_data
from timetoalign.timelines import MeasureMap, SegmentLine
from timetoalign.timelines.flowcontrol import Break, Jump, Marker

from . import parts


def _with_children(
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


def continuous_logical_timeline() -> Timeline:
    """Build 12 quarters with children at one third and two quarters."""
    return _with_children(
        ContinuousLogicalTimeline, "quarters", 12, [(4, Fraction(1, 3)), (3, 2)]
    )


def discrete_logical_timeline() -> Timeline:
    """Build 480 ticks with two children at integer logical coordinates."""
    return _with_children(
        DiscreteLogicalTimeline,
        "ticks",
        Fraction(480),
        [(Fraction(120), Fraction(3)), (Fraction(96), Fraction(7))],
    )


def continuous_physical_timeline() -> Timeline:
    """Build 12.5 seconds with two children at float physical coordinates."""
    return _with_children(
        ContinuousPhysicalTimeline, "seconds", 12.5, [(4.25, 0.5), (3.0, 6.0)]
    )


def discrete_physical_timeline() -> Timeline:
    """Build 44100 samples with two children at integer physical coordinates."""
    return _with_children(
        DiscretePhysicalTimeline,
        "samples",
        Fraction(44100),
        [(Fraction(11025), Fraction(100)), (Fraction(2205), Fraction(20000))],
    )


def continuous_graphical_timeline() -> Timeline:
    """Build 600 points with two children at float graphical coordinates."""
    return _with_children(
        ContinuousGraphicalTimeline,
        "points",
        600.0,
        [(200.0, 10.0), (150.0, 300.0)],
    )


def discrete_graphical_timeline() -> Timeline:
    """Build 1920 pixels with two children at integer graphical coordinates."""
    return _with_children(
        DiscreteGraphicalTimeline,
        "pixels",
        Fraction(1920),
        [(Fraction(640), Fraction(16)), (Fraction(480), Fraction(1000))],
    )


def with_region_timeline() -> Timeline:
    """Build the continuous logical axis with a named region from 2 to 6."""
    timeline = continuous_logical_timeline()
    timeline.create_region(2, 6, name="theme")
    return timeline


def nested_timeline() -> Timeline:
    """Build three levels of continuous logical timelines."""
    grandchild = ContinuousLogicalTimeline(length=2, unit="quarters")
    child = ContinuousLogicalTimeline(length=8, unit="quarters")
    child.add_child(grandchild, Fraction(3, 2))
    nested = ContinuousLogicalTimeline(length=16, unit="quarters")
    nested.add_child(child, 4)
    return nested


def four_bars() -> MeasureMap:
    """Return a measure map of four bars of 4/4, 16 quarters, its id minted."""
    return MeasureMap.from_rows([{"count": 1, "time_signature": "4/4"}, {"count": 4}])


def conversion_maps_quarters() -> Timeline:
    """Build the quarter axis carrying every conversion-map type.

    The timeline ``maps:quarters`` ("Quarter-note maps", 16 quarters) holds
    the measure map of ``four_bars`` through its ``MeasureRecordMap`` and
    reads it through the three other measure views, then carries a
    ``ChainMap`` of quarters to seconds to minutes, a ``CombinationMap`` of
    the outputs ``section`` (a ``ConstantMap``) and ``measure`` (a
    ``MeasureNumberMap``), a ``ConstantMap``, a ``PiecewiseMap`` of two
    ``LinearMap``s, a ``LinearMap``, and three ``TableMap``s: linear and
    constant beyond its anchors, previous and undefined beyond them, linear
    and linear beyond them. Every map id is minted.
    """
    quarters = ContinuousLogicalTimeline(
        length=16, unit="quarters", uid="maps:quarters", name="Quarter-note maps"
    )
    quarters.add_measure_map(four_bars())
    bars = quarters.measure_map
    quarter_maps = [
        MeasureNumberMap(bars),
        FloatingMeasureMap(bars),
        MeasureBeatMap(bars),
        ChainMap(
            [
                LinearMap(
                    scalar=Fraction(1, 2), source_unit="quarters", target_unit="seconds"
                ),
                LinearMap(
                    scalar=Fraction(1, 60), source_unit="seconds", target_unit="minutes"
                ),
            ]
        ),
        CombinationMap(
            {
                "section": ConstantMap(value="verse", source_unit="quarters"),
                "measure": MeasureNumberMap(bars),
            }
        ),
        ConstantMap(value="section-a", source_unit="quarters"),
        PiecewiseMap(
            breaks=[Fraction(0), Fraction(8), Fraction(16)],
            maps=[
                LinearMap(offset=1, source_unit="quarters", target_unit="seconds"),
                LinearMap(offset=2, source_unit="quarters", target_unit="seconds"),
            ],
            source_unit="quarters",
            target_unit="seconds",
        ),
        LinearMap(
            scalar=Fraction(3, 2),
            offset=Fraction(1, 3),
            source_unit="quarters",
            target_unit="seconds",
        ),
        TableMap(
            x_values=[Fraction(0), Fraction(4)],
            y_values=[0.0, 2.5],
            kind="linear",
            extrapolate="constant",
            source_unit="quarters",
            target_unit="seconds",
        ),
        TableMap(
            x_values=[Fraction(0), Fraction(8)],
            y_values=[60, 72],
            kind="previous",
            extrapolate="error",
            source_unit="quarters",
        ),
        TableMap(
            x_values=[Fraction(0), Fraction(8), Fraction(16)],
            y_values=[0.0, 4.25, 9.0],
            kind="linear",
            extrapolate="extrapolate",
            source_unit="quarters",
            target_unit="seconds",
        ),
    ]
    for conversion_map in quarter_maps:
        quarters.add_conversion_map(conversion_map)
    return quarters


def conversion_maps_ticks() -> Timeline:
    """Build the tick axis carrying the registered map back to quarters."""
    ticks = DiscreteLogicalTimeline(
        length=960, unit="ticks", uid="maps:ticks", name="Tick maps"
    )
    ticks.add_conversion_map(TicksToQuarters(ppq=480))
    return ticks


def conversion_maps_samples() -> Timeline:
    """Build the sample axis carrying the registered map to seconds."""
    samples = DiscretePhysicalTimeline(
        length=96000, unit="samples", uid="maps:samples", name="Sample maps"
    )
    samples.add_conversion_map(SamplesToSeconds(sample_rate=48000))
    return samples


def conversion_maps_seconds() -> Timeline:
    """Build the second axis carrying the registered map to samples."""
    seconds = ContinuousPhysicalTimeline(
        length=2.0, unit="seconds", uid="maps:seconds", name="Second maps"
    )
    seconds.add_conversion_map(SecondsToSamples(sample_rate=48000))
    return seconds


def flow_control_timeline() -> Timeline:
    """Build one timeline with every element type of flow control.

    The root ``flow:quarters`` ("Flow control", 16 quarters) holds the jump
    target ``repeat-start`` (a repeat start) at 2, the flow marker ``fine``
    ("Fine") at 12, the jump origin "Repeat" at 8, a repeat end back to
    ``repeat-start`` taken twice, the jump target ``segno`` at 4 and the jump
    origin "D.S." at 16, a dal segno to ``segno``. The elements' ids are
    minted.
    """
    timeline = ContinuousLogicalTimeline(
        length=16, unit="quarters", uid="flow:quarters", name="Flow control"
    )
    marker = timeline.flow_control.add_marker(
        Marker(
            timeline.make_coordinate(2),
            name="repeat-start",
            control_type=FlowControlElement.repeat_start,
        )
    )
    timeline.flow_control.add_break(
        Break(
            coordinate=timeline.make_coordinate(12),
            control_type=FlowControlElement.fine,
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
            repeat_count=2,
            target=marker.id,
            label="Repeat",
            meta={"source": "synthetic"},
        )
    )
    segno = timeline.flow_control.add_marker(
        Marker(
            timeline.make_coordinate(4),
            name="segno",
            control_type=FlowControlElement.segno,
        )
    )
    timeline.flow_control.add_jump(
        Jump(
            from_coordinate=timeline.make_coordinate(16),
            to_coordinate=timeline.make_coordinate(4),
            control_type=FlowControlElement.dal_segno,
            target=segno.id,
            label="D.S.",
        )
    )
    return timeline


def bare_timeline() -> Timeline:
    """Build one named timeline with no content."""
    return ContinuousLogicalTimeline(length=8, unit="quarters", uid="bare", name="Bare")


def contiguous_timeline() -> Timeline:
    """Build children that touch and overlap on one named timeline."""
    piece = ContinuousLogicalTimeline(
        length=8, unit="quarters", uid="piece", name="Piece"
    )
    piece.add_child(ContinuousLogicalTimeline(length=3, unit="quarters", uid="a"), 0)
    piece.add_child(ContinuousLogicalTimeline(length=5, unit="quarters", uid="b"), 3)
    piece.add_child(ContinuousLogicalTimeline(length=2, unit="quarters", uid="c"), 1)
    return piece


def map_timeline() -> Timeline:
    """Build maps on a root and its child, with every id explicit.

    The root ``melody`` ("Melody", 8 quarters) carries the tempo map ``tempo``
    ("Tempo", half a second per quarter) and holds the child ``phrase``
    ("Phrase", 4 quarters) at 2, which carries the map to ticks ``ticks``
    ("Ticks", 480 per quarter).
    """
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
    return melody


def styled_score_timeline() -> Timeline:
    """Build ``styled__score``, the logical timeline of the styled fixture.

    It holds children, a map, a region and a jump origin.

    The root ``score`` ("Score", 8 quarters) holds the children ``a`` and ``b``
    (4 quarters each) at 0 and 4, and carries the map to ticks ``ticks``
    ("Ticks"), the region ``intro`` from 0 to 2 and the jump origin
    ``da-capo`` ("D.C."), a da capo from 8 back to the start without a target.
    """
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
            target=None,
            label="D.C.",
            id="da-capo",
            meta={},
        )
    )
    return score


def styled_performance_timeline() -> Timeline:
    """Build ``styled__performance``, the physical timeline of the styled fixture.

    The root ``performance`` ("Performance", 10.0 seconds) holds the child
    ``excerpt`` (4.0 seconds) at 1.0.
    """
    performance = ContinuousPhysicalTimeline(
        length=10.0, unit="seconds", uid="performance", name="Performance"
    )
    performance.add_child(
        ContinuousPhysicalTimeline(length=4.0, unit="seconds", uid="excerpt"), 1.0
    )
    return performance


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


def corpus_score_ms3_timeline() -> Timeline:
    """Load the ms3 score with measure-map and flow-control data."""
    score = ensure_data("score")
    score_path = (
        score / "flow_control/flow_only/out_of_the_flow_experience-flow_only.notes.tsv"
    )
    return Ms3Loader(auto_discover=True).load(score_path).create_timeline()


def corpus_midi_score_timeline() -> Timeline:
    """Load a score MIDI file through the public score-MIDI loader."""
    midi = ensure_data("midi")
    return ScoreMidiLoader().load(midi / "score/beethoven_mtd.mid").create_timeline()


def corpus_audio_timeline() -> Timeline:
    """Load an audio file through the public audio loader."""
    audio = ensure_data("audio")
    return AudioLoader().load(audio / "hard_techno/Bass Kick.mp3").create_timeline()


def corpus_parangonada_score_timeline() -> Timeline:
    """Load only the discrete score ``score:dlt_1`` of a Parangonada alignment."""
    parangonar = ensure_data("parangonar")
    (score,) = [
        timeline
        for timeline in ParangonadaLoader()
        .load(parangonar / "Beethoven_Eroica_op35-cpjku")
        .create_timelines()
        if timeline.id == "score:dlt_1"
    ]
    return score


def corpus_supra_iiif_timeline() -> Timeline:
    """Load an IIIF manifest through the public graphical loader."""
    supra = ensure_data("supra")
    return (
        IIIFManifestLoader().load(supra / "image/ifff_manifest.json").create_timeline()
    )


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
        parts.named(ContinuousLogicalTimeline, "score", "Score", Fraction(16))
    )
    return bundle


def unknown_length_timeline() -> Timeline:
    """Build ``unknown_length``, a root of unknown length with content.

    The root ``score`` of unknown length holds the region ``region_1`` from 2
    to 8, the jump target ``marker_1`` (a segno) at 6 and the child ``coda``
    (4 quarters) at 10; its content reaches 14. Every timeline is of quarters
    and unnamed.
    """
    score = parts.with_region(parts.quarters("score", None), 2, 8, "region_1")
    score.flow_control.add_marker(
        Marker(
            score.make_coordinate(6),
            control_type=FlowControlElement.segno,
            id="marker_1",
        )
    )
    score.add_child(parts.quarters("coda", 4), 10)
    return score


def unknown_length_empty_timeline() -> Timeline:
    """Build ``unknown_length_empty``: the root ``score`` of unknown length and
    nothing else.
    """
    return parts.quarters("score", None)


def unknown_length_locked_timeline() -> Timeline:
    """Build ``unknown_length_locked``: ``locked_root`` with its length unknown.

    The locked root ``score`` holds ``coda`` (4 quarters) at 12.
    """
    locked = parts.quarters("score", None, locked=True)
    locked.add_child(parts.quarters("coda", 4), 12)
    return locked


def unknown_length_child_timeline() -> Timeline:
    """Build ``unknown_length_child``, a known root with a child of unknown length.

    The root ``score`` (32 quarters) holds the child ``movement`` of unknown
    length at 8, with the region ``region_1`` from 0 to 6.
    """
    known = parts.quarters("score", Fraction(32))
    known.add_child(
        parts.with_region(parts.quarters("movement", None), 0, 6, "region_1"), 8
    )
    return known


def unknown_length_segments_timeline() -> Timeline:
    """Build ``unknown_length_segments``, a segment line of unknown length.

    The segment line ``form`` of unknown length holds ``a`` of unknown length
    at 0 (region ``region_1`` from 0 to 4), ``b`` (6 quarters) at 8 and ``c``
    of unknown length at 14 (region ``region_2`` from 0 to 3).
    """
    form = SegmentLine[ContinuousLogicalTimeline](
        length=None, unit="quarters", uid="form"
    )
    form.add_child(parts.with_region(parts.quarters("a", None), 0, 4, "region_1"), 0)
    form.add_child(parts.quarters("b", 6), 8)
    form.add_child(parts.with_region(parts.quarters("c", None), 0, 3, "region_2"), 14)
    return form


def joint_rows_timeline() -> Timeline:
    """Build a root of two children whose own children share rows at two depths.

    The root ``piece`` ("Piece", 16 quarters) holds ``b`` ("B", 6 quarters) at
    0 and ``d`` ("D", 8 quarters) at 8; ``b`` holds ``b1`` ("B1", 4 quarters)
    at 1, which holds ``b11`` ("B11", 2 quarters) at 1, and ``d`` holds ``d1``
    ("D1", 4 quarters) at 2, which holds ``d11`` ("D11", 2 quarters) at 1.
    ``b`` carries the map to ticks ``ticks_b``; ``d1`` the map to ticks
    ``ticks_d1`` and the tempo map ``tempo_d1``, ``d11`` likewise ``ticks_d11``
    and ``tempo_d11``; no other timeline carries a map. Each depth's two lines
    lie in one row, so their children bands are laid out together: the one map
    of ``b`` against none on ``d`` sets the common start of the children bands
    of ``b`` and ``d``, the two maps of ``d1`` against none on ``b1`` that of
    ``b1`` and ``d1``, and the maps of ``d11`` widen the row of ``b11`` and
    ``d11``. Every id is given.
    """

    def quarters(uid: str, name: str, length: int) -> Timeline:
        return parts.named(ContinuousLogicalTimeline, uid, name, Fraction(length))

    piece = quarters("piece", "Piece", 16)
    b = parts.holding(
        piece,
        parts.with_maps(quarters("b", "B", 6), parts.ticks("ticks_b")),
        Fraction(0),
    )
    d = parts.holding(piece, quarters("d", "D", 8), Fraction(8))
    b1 = parts.holding(b, quarters("b1", "B1", 4), Fraction(1))
    parts.holding(b1, quarters("b11", "B11", 2), Fraction(1))
    d1 = parts.holding(
        d,
        parts.with_maps(
            quarters("d1", "D1", 4), parts.ticks("ticks_d1"), parts.tempo("tempo_d1")
        ),
        Fraction(2),
    )
    parts.holding(
        d1,
        parts.with_maps(
            quarters("d11", "D11", 2),
            parts.ticks("ticks_d11"),
            parts.tempo("tempo_d11"),
        ),
        Fraction(1),
    )
    return piece


def child_flow_control_timeline() -> Timeline:
    """Build a root whose one child holds flow control, the root none.

    The root ``piece`` ("Piece", 16 quarters) holds the child ``verse``
    ("Verse", 8 quarters) at 4, which carries a da capo al fine: the flow
    marker ``fine`` ("Fine") at 4 and the jump origin ``da_capo_al_fine``
    ("D.C. al Fine") from 8 back to 0, which names no target. The defaults
    hide the flow control band of a
    child, so a drawing shows them only under a statement that displays the
    band ``verse/flow_control_1``.
    """
    piece = parts.named(ContinuousLogicalTimeline, "piece", "Piece", Fraction(16))
    verse = parts.holding(
        piece,
        parts.named(ContinuousLogicalTimeline, "verse", "Verse", Fraction(8)),
        Fraction(4),
    )
    verse.flow_control.add_break(
        Break(
            coordinate=verse.make_coordinate(4),
            control_type=FlowControlElement.fine,
            label="Fine",
            id="fine",
        )
    )
    verse.flow_control.add_jump(
        Jump(
            from_coordinate=verse.make_coordinate(8),
            to_coordinate=verse.make_coordinate(0),
            control_type=FlowControlElement.da_capo_al_fine,
            label="D.C. al Fine",
            id="da_capo_al_fine",
        )
    )
    return piece


def conversion_maps_whole_notes() -> Timeline:
    """Build the whole-note axis reading a measure map through a ``ChainMap``.

    The timeline ``maps:whole_notes`` ("Whole-note maps", 4 whole notes)
    holds the measure map of ``four_bars``: its ``MeasureRecordMap`` follows
    the ``LinearMap`` of whole notes to quarters (times 4) in a ``ChainMap``.
    Every map id is minted.
    """
    whole_notes = ContinuousLogicalTimeline(
        length=4, unit="whole_notes", uid="maps:whole_notes", name="Whole-note maps"
    )
    whole_notes.add_measure_map(four_bars())
    return whole_notes


def child_jumps_timeline() -> Timeline:
    """Build a root whose one child holds jumps to a target and to its start.

    The root ``piece`` ("Piece", 16 quarters) holds the child ``verse``
    ("Verse", 8 quarters) at 4, which carries the jump target ``segno`` (a
    segno) at 2, the jump origin ``repeat`` ("Repeat") at 4, a repeat end
    taken twice back to the child's start without a target, and the jump
    origin ``dal_segno`` ("D.S.") at 8, a dal segno to ``segno``; the root
    holds no flow control.
    """
    piece = parts.named(ContinuousLogicalTimeline, "piece", "Piece", Fraction(16))
    verse = parts.holding(
        piece,
        parts.named(ContinuousLogicalTimeline, "verse", "Verse", Fraction(8)),
        Fraction(4),
    )
    segno = verse.flow_control.add_marker(
        Marker(
            verse.make_coordinate(2),
            control_type=FlowControlElement.segno,
            id="segno",
        )
    )
    verse.flow_control.add_jump(
        Jump(
            from_coordinate=verse.make_coordinate(4),
            to_coordinate=verse.make_coordinate(0),
            control_type=FlowControlElement.repeat_end,
            repeat_count=2,
            label="Repeat",
            id="repeat",
        )
    )
    verse.flow_control.add_jump(
        Jump(
            from_coordinate=verse.make_coordinate(8),
            to_coordinate=verse.make_coordinate(2),
            control_type=FlowControlElement.dal_segno,
            target=segno.id,
            label="D.S.",
            id="dal_segno",
        )
    )
    return piece
