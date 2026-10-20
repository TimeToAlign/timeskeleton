"""Builders for fixtures containing alignment bundles."""

from __future__ import annotations

import json
import tempfile
from fractions import Fraction
from pathlib import Path
from typing import Any

from timetoalign import (
    AlignmentBundle,
    ContinuousLogicalTimeline,
    ContinuousPhysicalTimeline,
    DiscreteGraphicalTimeline,
    DiscretePhysicalTimeline,
    Timeline,
)
from timetoalign.core import FlowControlElement
from timetoalign.loader.alignment import (
    Ieee1599Loader,
    ListenHereLoader,
    MatchfileLoader,
    MpmLoader,
    ParangonadaLoader,
)
from timetoalign.loader.alignment.tilia import TiliaJsonLoader
from timetoalign.testdata import ensure_data
from timetoalign.timelines import SegmentLine
from timetoalign.timelines.flowcontrol import Break, Jump

from . import parts
from .timelines import pages_timeline

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


def _segments(line: Timeline, *segments: Timeline) -> Timeline:
    """Append ``segments`` in order to the segment line ``line`` and return it."""
    for segment in segments:
        line.append_segment(segment)
    return line


def bundle_mixed() -> AlignmentBundle:
    """Build ``bundle_mixed``, the constructed bundle of mixed domains.

    ``bundle_mixed`` ("Mixed") holds two groups, a score with its performance
    and a page with an excerpt of a recording, and one ungrouped timeline. The
    score ``score`` (12 quarters) carries a map to ticks, then a tempo map to
    seconds (half a second per quarter), and a repeat from 8 back to 0;
    the performance ``performance`` (12.5 seconds) a map to samples; the page
    ``page`` (1920 pixels) a map to points; the recording ``recording``
    (441000 samples) and its excerpt ``excerpt`` (88200 samples at 44100) a
    map to seconds each; the ungrouped ``annotations`` (12 quarters) the
    regions "Verse" from 0 to 4 and "Chorus" from 4 to 12, and no map. No
    group names ``recording``, but it contains the member ``excerpt`` and so
    is drawn only as its ancestor line: its map is kept in the manifest but
    not drawn. Every id of a map, region or jump is minted.
    """
    score = parts.with_maps(
        ContinuousLogicalTimeline(
            length=Fraction(12), unit="quarters", uid="score", name="Score"
        ),
        parts.ticks(),
        parts.tempo(),
    )
    parts.with_repeat(score, 8, 0)
    performance = parts.with_maps(
        ContinuousPhysicalTimeline(
            length=12.5, unit="seconds", uid="performance", name="Performance"
        ),
        parts.to_samples(),
    )
    page = parts.with_maps(
        DiscreteGraphicalTimeline(
            length=Fraction(1920), unit="pixels", uid="page", name="Page"
        ),
        parts.to_points(),
    )
    recording = parts.with_maps(
        DiscretePhysicalTimeline(
            length=Fraction(441000), unit="samples", uid="recording", name="Recording"
        ),
        parts.to_seconds(),
    )
    excerpt = parts.with_maps(
        DiscretePhysicalTimeline(
            length=Fraction(88200), unit="samples", uid="excerpt", name="Excerpt"
        ),
        parts.to_seconds(),
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
    return bundle


def bundle_shared_parent() -> AlignmentBundle:
    """Build a bundle whose two groups hold two children of one root.

    The score ``score`` ("Score", 32 quarters) carries a map to ticks, the
    region "Development" from 12 to 20 and a repeat from 12 back to 0. It
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
        return parts.named(ContinuousLogicalTimeline, uid, name, Fraction(length))

    def line(uid: str, name: str, *segments: Timeline) -> Timeline:
        return _segments(
            SegmentLine[ContinuousLogicalTimeline](
                length=0, unit="quarters", uid=uid, name=name
            ),
            *segments,
        )

    score = parts.with_maps(
        parts.named(ContinuousLogicalTimeline, "score", "Score", Fraction(32)),
        parts.ticks(),
    )
    score.create_region(12, 20, name="Development")
    parts.with_repeat(score, 12, 0)
    exposition = parts.holding(
        score,
        parts.with_maps(
            line(
                "exposition",
                "Exposition",
                quarters("exposition_first", "First theme", 6),
                parts.with_maps(
                    quarters("exposition_second", "Second theme", 6), parts.tempo()
                ),
            ),
            parts.ticks(),
        ),
        Fraction(0),
    )
    recapitulation_first = line(
        "recapitulation_first",
        "First theme",
        quarters("recapitulation_first_1", "Phrase 1", 3),
        quarters("recapitulation_first_2", "Phrase 2", 3),
    )
    recapitulation_second = parts.with_maps(
        line(
            "recapitulation_second",
            "Second theme",
            quarters("recapitulation_second_1", "Phrase 1", 3),
            quarters("recapitulation_second_2", "Phrase 2", 3),
        ),
        parts.ticks(),
    )
    recapitulation = parts.holding(
        score,
        line(
            "recapitulation",
            "Recapitulation",
            recapitulation_first,
            recapitulation_second,
        ),
        Fraction(20),
    )
    take_1 = parts.with_maps(
        _segments(
            SegmentLine[ContinuousPhysicalTimeline](
                length=0.0, unit="seconds", uid="take_1", name="Take 1"
            ),
            parts.named(
                ContinuousPhysicalTimeline, "take_1_first", "First theme", 14.0
            ),
            parts.named(
                ContinuousPhysicalTimeline, "take_1_second", "Second theme", 16.0
            ),
        ),
        parts.to_samples(),
    )
    take_2 = parts.named(ContinuousPhysicalTimeline, "take_2", "Take 2", 28.5)
    page = parts.named(DiscreteGraphicalTimeline, "page", "Page", Fraction(1754))
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
    pixels), and no group; the manifest writes them by id, ``pages`` first.
    The score carries a map to ticks and a da capo al fine: the flow marker
    "Fine" at 8 (manifestation ``fine``) and the jump origin "D.C. al Fine"
    from 16 back to 0 (manifestation ``da_capo_al_fine``), which names no
    target. The recording carries a map to
    seconds, the segment line ``pages`` a map to points; its pages carry
    none. Every id of a map or flow-control element is minted.
    """
    score = parts.with_maps(
        parts.named(ContinuousLogicalTimeline, "score", "Score", Fraction(16)),
        parts.ticks(),
    )
    score.flow_control.add_break(
        Break(
            coordinate=score.make_coordinate(8),
            control_type=FlowControlElement.fine,
            label="Fine",
        )
    )
    score.flow_control.add_jump(
        Jump(
            from_coordinate=score.make_coordinate(16),
            to_coordinate=score.make_coordinate(0),
            control_type=FlowControlElement.da_capo_al_fine,
            repeat_count=1,
            label="D.C. al Fine",
        )
    )
    bundle = AlignmentBundle(name="Sketches")
    bundle.add_timeline(score)
    bundle.add_timeline(
        parts.with_maps(
            parts.named(
                DiscretePhysicalTimeline, "recording", "Recording", Fraction(441000)
            ),
            parts.to_seconds(),
        )
    )
    bundle.add_timeline(parts.with_maps(pages_timeline(3), parts.to_points()))
    return bundle


def corpus_parangonada_bundle() -> AlignmentBundle:
    """Load the Parangonada alignment bundle from its corpus specimen."""
    parangonar = ensure_data("parangonar") / "Beethoven_Eroica_op35-cpjku"
    return ParangonadaLoader.from_file(parangonar).create_bundle()


def corpus_matchfile_bundle() -> AlignmentBundle:
    """Load the Matchfile alignment bundle from its corpus specimen."""
    vienna = ensure_data("vienna_1x22") / "Chopin_op10_no3_p01.match"
    return MatchfileLoader.from_file(vienna).create_bundle()


def corpus_mpm_bundle() -> AlignmentBundle:
    """Load the MPM performance bundle from its corpus specimen."""
    mpm = (
        ensure_data("mpm_toolbox")
        / "MPRproject_1971Curzon_VariationXIV"
        / "Beethoven_op35_1971Curzon_Var14only.mpr"
    )
    return MpmLoader.from_file(mpm).create_bundle()


def corpus_ieee1599_bundle() -> AlignmentBundle:
    """Load the IEEE 1599 alignment bundle from its corpus specimen."""
    ieee1599 = ensure_data("ieee1599") / "Khorus Music/khomus.xml"
    return Ieee1599Loader.from_file(ieee1599).create_bundle()


def corpus_listen_here_bundle() -> AlignmentBundle:
    """Load the synthetic two-recording Listen Here! export."""
    with tempfile.TemporaryDirectory() as directory:
        listen_here_path = Path(directory) / "alignment.json"
        listen_here_path.write_text(json.dumps(LISTEN_HERE), encoding="utf-8")
        return ListenHereLoader.from_file(listen_here_path).create_bundle()


def corpus_tilia_bundle() -> AlignmentBundle:
    """Load the TiLiA alignment bundle from its corpus specimen."""
    tilia = ensure_data("score") / parts.TILIA
    return TiliaJsonLoader.from_file(tilia).create_bundle()
