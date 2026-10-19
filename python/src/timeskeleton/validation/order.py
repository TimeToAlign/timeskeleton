"""Graphical display-order and band-order rules."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import Any

from .diagnostics import SchemaValidationError, ValidationCode, _entries, _Path

_DEFAULT_BAND_ORDER = (
    "children_1",
    "conversion_maps_1",
    "",
    "markers_1",
    "regions_1",
    "flow_control_1",
)


def _permutation_problems(
    code: ValidationCode,
    owner: str,
    order: list[str],
    expected: list[str],
    path: _Path,
    messages: tuple[str, str],
) -> Iterator[SchemaValidationError]:
    stranger, missing = messages
    allowed = set(expected)
    listed = set(order)
    for index, entry in enumerate(order):
        if entry not in allowed:
            yield SchemaValidationError(
                code,
                (*path, index),
                stranger.format(entry=repr(entry), owner=repr(owner)),
            )
    for entry in expected:
        if entry not in listed:
            yield SchemaValidationError(
                code,
                path,
                missing.format(entry=repr(entry), owner=repr(owner)),
            )


def order_problems(
    manifest: Mapping[str, Any],
    timelines: Mapping[str, _Path],
    first_group: Mapping[str, int],
) -> Iterator[SchemaValidationError]:
    """Yield unknown order keys and invalid display and band orders.

    ``timelines`` and ``first_group`` are the first occurrence of each timeline
    id and group id, as the identity rules collected them.
    """
    groups = _entries(manifest, "groups")
    orders = (manifest.get("graphical") or {}).get("order") or {}
    for key in sorted(orders):
        path = ("graphical", "order", key)
        if key in first_group:
            group = groups[first_group[key]]
            yield from _permutation_problems(
                "display_order",
                key,
                orders[key],
                group["members"],
                path,
                (
                    "{entry} is not a member of group {owner}",
                    "member {entry} of group {owner} is missing",
                ),
            )
        elif key in timelines:
            bands = [f"{key}/{band}" if band else key for band in _DEFAULT_BAND_ORDER]
            yield from _permutation_problems(
                "band_order",
                key,
                orders[key],
                bands,
                path,
                (
                    "{entry} is not {owner} or one of its bands",
                    "{entry} is missing from the band order of {owner}",
                ),
            )
        else:
            yield SchemaValidationError(
                "order_key",
                path,
                f"{key!r} names no group or timeline of this manifest",
            )
