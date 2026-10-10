#!/usr/bin/env python
"""Emit the golden fixtures of the current schema through timetoalign.

Every document is built with public constructors or a public loader, serialized
with ``Timeline.to_dict()``, written with ``timeskeleton.dumps`` and
round-tripped through ``Timeline.from_dict``; a manifest whose order differs
from the library's fails the round trip. A styled document is such a document
plus a ``graphical`` block written in this script (``GRAPHICAL``); the manifests
are never written by hand.
The current schema version is ``timeskeleton.SCHEMA_VERSION``. The fixtures of
a released version are frozen: the script refuses to write into
``fixtures/<version>/`` once the tag ``v<version>`` exists. Map identifiers
come from a per-process counter, so every run in a fresh interpreter emits the
same documents.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from fractions import Fraction
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np
from timetoalign import (
    ContinuousGraphicalTimeline,
    ContinuousLogicalTimeline,
    ContinuousPhysicalTimeline,
    DiscreteGraphicalTimeline,
    DiscreteLogicalTimeline,
    DiscretePhysicalTimeline,
    Ms3Loader,
    Timeline,
)
from timetoalign.core import ActivationCondition, FlowControlElement
from timetoalign.loader.alignment import ParangonadaLoader
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
from timetoalign.timelines.flowcontrol import Break, Jump

from timeskeleton import SCHEMA_VERSION, dumps

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPOSITORY_ROOT / "fixtures" / SCHEMA_VERSION


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
        QuartersToMeasureNumber(
            boundaries=[Fraction(0), Fraction(4)], mns=["1", "2"]
        ),
        QuartersToTicks(ppq=480),
        RotationMap(4, scale=0.5, base=1, offset=0.25, source_unit="quarters"),
        ScalarMap(
            Fraction(2, 3), source_unit="quarters", target_unit="seconds"
        ),
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
    """Build one timeline with a break, jump, and named marker."""
    timeline = ContinuousLogicalTimeline(
        length=16, unit="quarters", uid="flow:quarters", name="Flow control"
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
            target_name="repeat-start",
            label="Repeat",
            meta={"source": "synthetic"},
        )
    )
    timeline.flow_control.add_marker("repeat-start", 2)
    return timeline


def drawing_documents() -> dict[str, list[Timeline]]:
    """Build the small documents that show one drawn component each.

    Every timeline and map carries an explicit id, so the documents do not
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
    """Build the two timelines of the styled document, one per domain."""
    score = ContinuousLogicalTimeline(
        length=8, unit="quarters", uid="score", name="Score"
    )
    score.add_child(ContinuousLogicalTimeline(length=4, unit="quarters", uid="a"), 0)
    score.add_child(ContinuousLogicalTimeline(length=4, unit="quarters", uid="b"), 4)
    score.add_conversion_map(QuartersToTicks(ppq=480, uid="ticks", name="Ticks"))
    score.create_region("intro", 0, 2)
    score.flow_control.add_jump(
        Jump(
            from_coordinate=score.make_coordinate(8),
            to_coordinate=score.make_coordinate(0),
            control_type=FlowControlElement.da_capo,
            condition=ActivationCondition.always,
            repeat_count=1,
            target_name=None,
            label="D.C.",
            meta={},
        )
    )
    performance = ContinuousPhysicalTimeline(
        length=10.0, unit="seconds", uid="perf", name="Performance"
    )
    performance.add_child(
        ContinuousPhysicalTimeline(length=4.0, unit="seconds", uid="p1"), 1.0
    )
    return [score, performance]


GRAPHICAL: dict[str, dict[str, Any]] = {
    "styled": {
        "styles": [
            {"select": {}, "set": {"show_length": True}},
            {"select": {"element": "label"}, "set": {"colour": "#404040"}},
            {"select": {"element": "map"}, "set": {"side": "below"}},
            {"select": {"ids": ["a"]}, "set": {"visible": False}},
        ],
        "timelines": {
            "score": [
                {
                    "select": {"element": "wedge"},
                    "set": {"side": "above", "colour": "#006600"},
                },
                {"select": {"domain": "logical"}, "set": {"colour": "#000080"}},
                {"select": {"element": "region"}, "set": {"colour": "#800000"}},
                {"select": {"element": "region"}, "set": {"colour": "#008080"}},
                {"select": {"element": "child"}, "set": {"visible": True}},
            ],
            "b": [
                {
                    "select": {},
                    "set": {"colour": "#FF8000", "show_projected_coordinates": True},
                }
            ],
            "perf": [
                {
                    "select": {"element": "wedge", "domain": "physical"},
                    "set": {"colour": "#7F00FF"},
                }
            ],
        },
    },
}
"""The ``graphical`` block of each styled document, by fixture name."""


def corpus_documents() -> dict[str, list[Timeline]]:
    """Load the smallest selected corpus specimens through public loaders."""
    score = ensure_data("score")
    midi = ensure_data("midi")
    audio = ensure_data("audio")
    parangonar = ensure_data("parangonar")
    supra = ensure_data("supra")

    score_path = (
        score
        / "flow_control/flow_only/out_of_the_flow_experience-flow_only.notes.tsv"
    )
    score_timeline = Ms3Loader(auto_discover=True).load(score_path).create_timeline()
    midi_timeline = (
        ScoreMidiLoader()
        .load(midi / "score/beethoven_mtd.mid")
        .create_timeline()
    )
    audio_timeline = (
        AudioLoader()
        .load(audio / "hard_techno/Bass Kick.mp3")
        .create_timeline()
    )
    parangonada_timelines = (
        ParangonadaLoader()
        .load(parangonar / "Beethoven_Eroica_op35-cpjku")
        .create_timelines()
    )
    graphical_timeline = (
        IIIFManifestLoader()
        .load(supra / "image/ifff_manifest.json")
        .create_timeline()
    )
    return {
        "corpus_score_ms3": [score_timeline],
        "corpus_midi_score_midi": [midi_timeline],
        "corpus_audio_audio": [audio_timeline],
        "corpus_parangonar_parangonada": parangonada_timelines,
        "corpus_supra_iiif": [graphical_timeline],
    }


def build_documents() -> dict[str, list[Timeline]]:
    """Return fixture names and top-level timelines in emission order."""
    documents: dict[str, list[Timeline]] = {}
    documents["continuous_logical"] = [
        with_children(
            ContinuousLogicalTimeline, "quarters", 12, [(4, Fraction(1, 3)), (3, 2)]
        )
    ]
    documents["discrete_logical"] = [
        with_children(
            DiscreteLogicalTimeline,
            "ticks",
            Fraction(480),
            [(Fraction(120), Fraction(3)), (Fraction(96), Fraction(7))],
        )
    ]
    documents["continuous_physical"] = [
        with_children(
            ContinuousPhysicalTimeline, "seconds", 12.5, [(4.25, 0.5), (3.0, 6.0)]
        )
    ]
    documents["discrete_physical"] = [
        with_children(
            DiscretePhysicalTimeline,
            "samples",
            Fraction(44100),
            [(Fraction(11025), Fraction(100)), (Fraction(2205), Fraction(20000))],
        )
    ]
    documents["continuous_graphical"] = [
        with_children(
            ContinuousGraphicalTimeline,
            "points",
            600.0,
            [(200.0, 10.0), (150.0, 300.0)],
        )
    ]
    documents["discrete_graphical"] = [
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
    with_region.create_region("theme", 2, 6)
    documents["with_region"] = [with_region]
    documents["empty"] = []
    grandchild = ContinuousLogicalTimeline(length=2, unit="quarters")
    child = ContinuousLogicalTimeline(length=8, unit="quarters")
    child.add_child(grandchild, Fraction(3, 2))
    nested = ContinuousLogicalTimeline(length=16, unit="quarters")
    nested.add_child(child, 4)
    documents["nested"] = [nested]
    documents["conversion_maps"] = conversion_map_timelines()
    documents["flow_control"] = [flow_control_timeline()]
    documents.update(corpus_documents())
    documents.update(drawing_documents())
    documents["styled"] = styled_timelines()
    return documents


def document(
    timelines: list[Timeline],
    generator: str,
    graphical: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Wrap top-level timelines, and a graphical block if any, in the document envelope."""
    result: dict[str, Any] = {
        "meta": {"schema_version": SCHEMA_VERSION, "generator": generator},
        "manifest": {"timelines": {timeline.id: timeline.to_dict() for timeline in timelines}},
    }
    if graphical is not None:
        result["graphical"] = graphical
    return result


def write(path: Path, data: dict[str, Any]) -> None:
    """Write one fixture with the standard writer, in canonical order."""
    path.write_text(dumps(data), encoding="utf-8")


def check_round_trip(path: Path) -> int:
    """Return the number of manifests that survive from_dict/to_dict."""
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    count = 0
    for timeline_id, manifest in data["manifest"]["timelines"].items():
        rebuilt = Timeline.from_dict(manifest).to_dict()
        if json.dumps(rebuilt) != json.dumps(manifest):
            raise SystemExit(
                f"{path.name}: timeline {timeline_id!r} does not round-trip through "
                f"timetoalign.\nexpected: {json.dumps(manifest, indent=2)}\n"
                f"got:      {json.dumps(rebuilt, indent=2)}"
            )
        count += 1
    return count


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, emit all fixtures, and verify their round trips."""
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

    args.output.mkdir(parents=True, exist_ok=True)
    for stale in args.output.glob("*.json"):
        stale.unlink()
    written: list[Path] = []
    for name, timelines in build_documents().items():
        path = args.output / f"{name}.json"
        write(path, document(timelines, generator, GRAPHICAL.get(name)))
        written.append(path)

    for path in written:
        manifests = check_round_trip(path)
        display = path.relative_to(REPOSITORY_ROOT) if path.is_relative_to(REPOSITORY_ROOT) else path
        print(f"{display}: {manifests} manifest(s) round-trip")
    print(f"generator: {generator}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
