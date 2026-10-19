"""The validator's diagnostics and the small readers every rule module shares.

The error a rule raises with its code and path, the JSON pointer of a path,
and the readers of a schema-checked object's members. A leaf module: it
imports no rule module and no validator, so the rule modules and
``timeskeleton.validate`` both import it without a cycle.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Literal, TypeAlias

from ..manifest import UNIT_NUMBER_TYPES as UNIT_NUMBER_TYPES

_Path = tuple[str | int, ...]
ValidationCode: TypeAlias = Literal[
    "not_a_manifest",
    "schema",
    "representation",
    "duplicate_id",
    "dangling_target",
    "child_unit",
    "child_offset",
    "child_end",
    "segment_line",
    "reserved_id",
    "group_member",
    "manifest_id",
    "order_key",
    "display_order",
    "band_order",
    "finite_number",
]


def json_pointer(path: Iterable[str | int]) -> str:
    """Render a path as a JSON pointer in URI fragment form (``#`` for the root)."""
    segments = [str(segment).replace("~", "~0").replace("/", "~1") for segment in path]
    return "#" + "".join(f"/{segment}" for segment in segments)


class SchemaValidationError(ValueError):
    """Raised when a value violates the schema or a semantic rule."""

    def __init__(self, code: ValidationCode, path: _Path, message: str) -> None:
        self.code = code
        self.path = path
        self.message = message
        super().__init__(f"{json_pointer(path)}: {message}")


def _entries(owner: Any, key: str) -> list[Any]:
    value = owner.get(key) if isinstance(owner, Mapping) else None
    return value if isinstance(value, list) else []


def number_type_of(timeline: Mapping[str, Any]) -> str:
    """Return the number type of a timeline's axis: its own, or its unit's default."""
    return timeline.get("number_type") or UNIT_NUMBER_TYPES[timeline["unit"]]
