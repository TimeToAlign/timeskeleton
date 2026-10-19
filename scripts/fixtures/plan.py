"""The ordered fixture catalogue and the pure plan derived from it."""

from __future__ import annotations

import copy
import re
from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from timetoalign import AlignmentBundle, Timeline, TimelineGroup

from . import bundles, graphical, groups, timelines
from .graphical import GRAPHICAL


@dataclass(frozen=True)
class FixtureCase:
    """One fixture: its name, directory, reader, builder and ``graphical`` entry.

    The reader is the class that reads the directory's manifests as a whole:
    ``Timeline`` a manifest of one root and no group (the top directory),
    ``TimelineGroup`` an anonymous manifest of one group (``groups``) and
    ``AlignmentBundle`` any manifest (``bundles``). Cases sharing a name and
    directory write ``<name>__<slug>.json`` each, the slug spelled from the
    built object's id.
    """

    name: str
    directory: str
    reader: type[Any]
    build: Callable[[], Any]
    graphical: Mapping[str, Any] | None = None


def _case(directory: str, reader: type[Any]) -> Callable[..., FixtureCase]:
    """Return the constructor of the cases of one directory.

    It takes the fixture's name, its builder and, for a styled fixture, the id
    of the root or group whose ``graphical`` entry ``GRAPHICAL`` holds under
    that name; a name or id it does not hold fails when the catalogue is read.
    """

    def case(
        name: str, build: Callable[[], Any], styled: str | None = None
    ) -> FixtureCase:
        graphical = None if styled is None else GRAPHICAL[name][styled]
        return FixtureCase(name, directory, reader, build, graphical)

    return case


_root = _case("", Timeline)
_group = _case("groups", TimelineGroup)
_bundle = _case("bundles", AlignmentBundle)

CATALOGUE = (
    _root("continuous_logical", timelines.continuous_logical_timeline),
    _root("discrete_logical", timelines.discrete_logical_timeline),
    _root("continuous_physical", timelines.continuous_physical_timeline),
    _root("discrete_physical", timelines.discrete_physical_timeline),
    _root("continuous_graphical", timelines.continuous_graphical_timeline),
    _root("discrete_graphical", timelines.discrete_graphical_timeline),
    _root("with_region", timelines.with_region_timeline),
    _root("nested", timelines.nested_timeline),
    _root("conversion_maps", timelines.conversion_maps_quarters),
    _root("conversion_maps", timelines.conversion_maps_ticks),
    _root("conversion_maps", timelines.conversion_maps_samples),
    _root("conversion_maps", timelines.conversion_maps_seconds),
    _root("flow_control", timelines.flow_control_timeline),
    _root("bare", timelines.bare_timeline),
    _root("contiguous", timelines.contiguous_timeline),
    _root("map", timelines.map_timeline),
    _root("styled", timelines.styled_score_timeline, "score"),
    _root("styled", timelines.styled_performance_timeline, "performance"),
    _root("segment_line", timelines.segment_line_timeline),
    _root("locked_root", timelines.locked_root_timeline),
    _root("segment_pages", timelines.pages_timeline),
    _root("segment_pages_locked", timelines.locked_pages_timeline),
    _root("segment_pages_accolades", timelines.accolade_pages_timeline),
    _root("segment_children", timelines.segment_children_timeline),
    _root("corpus_score_ms3", timelines.corpus_score_ms3_timeline),
    _root("corpus_midi_score_midi", timelines.corpus_midi_score_timeline),
    _root("corpus_audio_audio", timelines.corpus_audio_timeline),
    _root(
        "corpus_parangonar_parangonada__score_dlt_1",
        timelines.corpus_parangonada_score_timeline,
    ),
    _root("corpus_supra_iiif", timelines.corpus_supra_iiif_timeline),
    _root("negative_offset", timelines.negative_offset_timeline),
    _root("named_without_id", timelines.named_without_id_bundle),
    _root("unknown_length", timelines.unknown_length_timeline),
    _root("unknown_length_empty", timelines.unknown_length_empty_timeline),
    _root("unknown_length_locked", timelines.unknown_length_locked_timeline),
    _root("unknown_length_child", timelines.unknown_length_child_timeline),
    _root("unknown_length_segments", timelines.unknown_length_segments_timeline),
    _root("map_child_band_order", graphical.map_child_band_order, "melody"),
    _root("map_root_band_order", graphical.map_root_band_order, "melody"),
    _root("styled_score_flow_inner", graphical.styled_score_flow_inner, "score"),
    _root("joint_rows", timelines.joint_rows_timeline),
    _root("child_flow_control", timelines.child_flow_control_timeline),
    _group("group_number_types", groups.number_types_group),
    _group("group_child_member", groups.group_child_member),
    _group("group_styled", groups.styled_group, "group_1"),
    _group("group_parent_right", groups.group_parent_right),
    _group("group_parent_both", groups.group_parent_both),
    _group("group_parent_exact", groups.group_parent_exact),
    _group("group_parents_mixed", groups.group_parents_mixed),
    _group("group_grandchild", groups.group_grandchild),
    _group("corpus_tilia", groups.corpus_tilia_group),
    _group("group_unknown_length", groups.group_unknown_length),
    _bundle("bundle_mixed", bundles.bundle_mixed),
    _bundle("bundle_shared_parent", bundles.bundle_shared_parent),
    _bundle("bundle_ungrouped", bundles.bundle_ungrouped),
    _bundle("corpus_parangonada", bundles.corpus_parangonada_bundle),
    _bundle("corpus_matchfile", bundles.corpus_matchfile_bundle),
    _bundle("corpus_mpm", bundles.corpus_mpm_bundle),
    _bundle("corpus_ieee1599", bundles.corpus_ieee1599_bundle),
    _bundle("corpus_listen_here", bundles.corpus_listen_here_bundle),
    _bundle("corpus_tilia", bundles.corpus_tilia_bundle),
)
"""The fixture cases in emission order; append new cases within their directory."""


@dataclass(frozen=True)
class PlannedFixture:
    """One fully built fixture ready for writing and verification."""

    path: Path
    reader: type[Any]
    item: Any
    source: dict[str, Any]


def _slug(identifier: str) -> str:
    """Return a file-name-safe spelling of an id."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", identifier)


def _compose(
    data: dict[str, Any], generator: str, graphical: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Add the provenance and any ``graphical`` entry to a manifest the library
    wrote.
    """
    result = copy.deepcopy(data)
    result["meta"]["generator"] = generator
    if graphical is not None:
        result.setdefault("graphical", {}).update(copy.deepcopy(graphical))
    return result


def plan(output: Path, generator: str) -> tuple[PlannedFixture, ...]:
    """Build the catalogue in order and return every fixture to write.

    Each object is read back by its case's reader from the composed manifest,
    so the library writes every fixture and twin. Two cases whose file names
    collide stop the run before anything is written.
    """
    counts = Counter((case.directory, case.name) for case in CATALOGUE)
    claimed: dict[Path, str] = {}
    planned: list[PlannedFixture] = []
    for case in CATALOGUE:
        item = case.build()
        filename = case.name
        if counts[case.directory, case.name] > 1:
            filename = f"{filename}__{_slug(item.id)}"
        path = output / case.directory / f"{filename}.json"
        if path in claimed:
            raise SystemExit(
                f"ids {claimed[path]!r} and {item.id!r} of {case.name!r} both "
                f"produce the file name {path.name}; nothing was written."
            )
        claimed[path] = item.id
        source = _compose(item.to_dict(), generator, case.graphical)
        planned.append(
            PlannedFixture(path, case.reader, case.reader.from_dict(source), source)
        )
    return tuple(planned)
