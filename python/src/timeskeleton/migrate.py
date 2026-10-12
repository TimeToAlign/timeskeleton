"""Migration of a value to the latest schema version.

Each step rewrites a value of one version into the next. The steps form one
ordered chain from the oldest supported version to ``SCHEMA_VERSION``; a later
schema version appends one step.
"""

from __future__ import annotations

import copy
from collections.abc import Callable, Mapping
from typing import Any

from .validate import SUPPORTED_VERSIONS, UnsupportedVersionError, declared_version


def _declare(version: str) -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Return a step that only rewrites ``meta.schema_version`` to ``version``."""

    def step(value: dict[str, Any]) -> dict[str, Any]:
        value["meta"]["schema_version"] = version
        return value

    return step


def _mark_plain(timeline: Any) -> None:
    """Write ``is_segment_line: false`` on a timeline and every descendant.

    ``migrate`` does not validate, so whatever is not a timeline object, or
    not a child entry holding one, is left as it is.
    """
    if not isinstance(timeline, dict):
        return
    timeline["is_segment_line"] = False
    children = timeline.get("children")
    if isinstance(children, dict):
        for child in children.values():
            if isinstance(child, dict):
                _mark_plain(child.get("timeline"))


def _to_segment_lines(value: dict[str, Any]) -> dict[str, Any]:
    """0.6.0 to 0.7.0: the declaration, and no timeline is a segment line.

    A 0.6.0 value is a timeline file and knows no segment lines, so every
    timeline, the root and every descendant, gains ``is_segment_line: false``.
    """
    _mark_plain(value.get("timeline"))
    return _declare("0.7.0")(value)


_STEPS: tuple[tuple[str, str, Callable[[dict[str, Any]], dict[str, Any]]], ...] = (
    ("0.5.0", "0.6.0", _declare("0.6.0")),
    ("0.6.0", "0.7.0", _to_segment_lines),
)
"""``(source, target, step)`` in version order; each step mutates its own copy."""


def migrate(value: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of ``value`` rewritten to the latest schema version.

    The value's declared ``meta.schema_version`` selects where the chain of
    steps starts; a value already at the latest version is returned as an equal
    copy. The input is never changed. The result is not validated.

    Raises:
        UnsupportedVersionError: If the value declares no supported version.
    """
    version = declared_version(value)
    if version not in SUPPORTED_VERSIONS:
        raise UnsupportedVersionError(version)
    result = copy.deepcopy(dict(value))
    for source, target, step in _STEPS:
        if version == source:
            result = step(result)
            version = target
    return result
