#!/usr/bin/env python
"""Emit the manifest fixtures of the current schema through timetoalign.

Every manifest is built with public constructors or a public loader, serialized
with ``Timeline.to_dict()``, written with ``timeskeleton.dumps`` and
round-tripped through ``Timeline.from_dict``; a manifest whose order differs
from the library's fails the round trip. A styled manifest also carries a
``graphical`` block composed in this script from ``GRAPHICAL``.
The current schema version is ``timeskeleton.SCHEMA_VERSION``. The fixtures of
a released version are frozen: the script refuses to write into
``fixtures/<version>/`` once the tag ``v<version>`` exists. Map identifiers
come from a per-process counter, so every run in a fresh interpreter emits the
same manifests.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
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


_GREY = {"stroke": "#404040", "fill": "#404040"}
_SHARED_STATEMENTS: list[dict[str, Any]] = [
    {"select": {"element": "label"}, "set": _GREY},
    {"select": {"element": "name"}, "set": _GREY},
    {"select": {"element": "map"}, "set": {"side": "below"}},
    {"select": {"ids": ["a"]}, "set": {"display": "none"}},
]
_GREEN_ABOVE = {"side": "above", "stroke": "#006600", "fill": "#006600"}
_VIOLET = {"stroke": "#7F00FF", "fill": "#7F00FF"}
_ACCENT = {
    "stroke": "#7F00FF",
    "stroke-width": 0,
    "stroke-dasharray": "3 3",
    "fill": "#7F00FF",
    "opacity": 0.5,
    "font-size": 10,
    "rx": 0,
    "display": "inline",
    "side": "above",
    "content": "Styled score",
    "max-width": 160,
}

GRAPHICAL: dict[str, dict[str, dict[str, Any]]] = {
    "styled": {
        "score": {
            "styles": {"accent": _ACCENT},
            "statements": [
                *_SHARED_STATEMENTS,
                {
                    "select": {"element": "wedge", "within": "score"},
                    "set": _GREEN_ABOVE,
                },
                {"select": {"class": "ContinuousLogicalTimeline"}, "set": "accent"},
                {
                    "select": {"domain": "logical", "within": "score"},
                    "set": {"stroke": "#000080", "fill": "#000080"},
                },
                {
                    "select": {"element": "region", "within": "score"},
                    "set": {"stroke": "#800000", "fill": "#800000"},
                },
                {
                    "select": {"element": "region", "within": "score"},
                    "set": {"stroke": "#008080", "fill": "#008080"},
                },
                {
                    "select": {"element": "child", "within": "score"},
                    "set": {"display": "inline"},
                },
                {
                    "select": {"within": "b"},
                    "set": {"stroke": "#FF8000", "fill": "#FF8000"},
                },
            ],
        },
        "perf": {
            "statements": [
                *_SHARED_STATEMENTS,
                {
                    "select": {
                        "element": "wedge",
                        "domain": "physical",
                        "within": "perf",
                    },
                    "set": _VIOLET,
                },
            ]
        },
    },
}
"""The ``graphical`` block of each styled manifest, by fixture name and root id."""


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


def build_manifests() -> dict[str, list[Timeline]]:
    """Return fixture names and top-level timelines in emission order."""
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
    with_region.create_region("theme", 2, 6)
    manifests["with_region"] = [with_region]
    grandchild = ContinuousLogicalTimeline(length=2, unit="quarters")
    child = ContinuousLogicalTimeline(length=8, unit="quarters")
    child.add_child(grandchild, Fraction(3, 2))
    nested = ContinuousLogicalTimeline(length=16, unit="quarters")
    nested.add_child(child, 4)
    manifests["nested"] = [nested]
    manifests["conversion_maps"] = conversion_map_timelines()
    manifests["flow_control"] = [flow_control_timeline()]
    manifests.update(corpus_manifests())
    manifests.update(drawing_manifests())
    manifests["styled"] = styled_timelines()
    return manifests


def manifest(
    timeline: Timeline,
    generator: str,
    graphical: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Wrap one timeline, and a graphical block if any, in a manifest."""
    result: dict[str, Any] = {
        "meta": {"schema_version": SCHEMA_VERSION, "generator": generator},
        "timeline": timeline.to_dict(),
    }
    if graphical is not None:
        result["graphical"] = copy.deepcopy(graphical)
    return result


def write(path: Path, data: dict[str, Any]) -> None:
    """Write one fixture with the standard writer, in canonical order."""
    path.write_text(dumps(data), encoding="utf-8")


def check_round_trip(path: Path) -> int:
    """Confirm that a manifest survives from_dict/to_dict."""
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    timeline = data["timeline"]
    rebuilt = Timeline.from_dict(timeline).to_dict()
    if json.dumps(rebuilt) != json.dumps(timeline):
        raise SystemExit(
            f"{path.name}: timeline {timeline['id']!r} does not round-trip through "
            f"timetoalign.\nexpected: {json.dumps(timeline, indent=2)}\n"
            f"got:      {json.dumps(rebuilt, indent=2)}"
        )
    return 1


def slug(identifier: str) -> str:
    """Return a fixture-safe spelling of a timeline id."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", identifier)


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

    planned: list[tuple[Path, Timeline, str]] = []
    claimed: dict[Path, str] = {}
    for name, timelines in build_manifests().items():
        for timeline in timelines:
            filename = name if len(timelines) == 1 else f"{name}__{slug(timeline.id)}"
            path = args.output / f"{filename}.json"
            if path in claimed:
                raise SystemExit(
                    f"timeline ids {claimed[path]!r} and {timeline.id!r} of {name!r} "
                    f"both produce the file name {path.name}; nothing was written."
                )
            claimed[path] = timeline.id
            planned.append((path, timeline, name))

    args.output.mkdir(parents=True, exist_ok=True)
    for stale in args.output.glob("*.json"):
        stale.unlink()
    written: list[Path] = []
    for path, timeline, name in planned:
        write(
            path,
            manifest(timeline, generator, GRAPHICAL.get(name, {}).get(timeline.id)),
        )
        written.append(path)

    for path in written:
        manifests = check_round_trip(path)
        display = (
            path.relative_to(REPOSITORY_ROOT)
            if path.is_relative_to(REPOSITORY_ROOT)
            else path
        )
        print(f"{display}: {manifests} manifest(s) round-trip")
    print(f"generator: {generator}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
