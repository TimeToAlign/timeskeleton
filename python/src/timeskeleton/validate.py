"""The TimeSkeleton schema validator and its public diagnostics."""

from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from .validation.diagnostics import UNIT_NUMBER_TYPES as UNIT_NUMBER_TYPES
from .validation.diagnostics import SchemaValidationError, _Path
from .validation.diagnostics import ValidationCode as ValidationCode
from .validation.diagnostics import _entries as _entries
from .validation.diagnostics import json_pointer as json_pointer
from .validation.diagnostics import number_type_of as number_type_of
from .validation.identity import identity_problems as _semantic_problems
from .validation.representation import (
    finite_number_problems,
    representation_problems,
)

SCHEMA_VERSION = "0.7.0"
"""The schema version this package reads and writes, the only one it supports."""


class UnsupportedVersionError(ValueError):
    """Raised when a manifest's version marker names another version."""

    def __init__(self, version: object) -> None:
        self.version = version
        super().__init__(
            f"unsupported TimeSkeleton version {version!r}; this package reads "
            f"{SCHEMA_VERSION} only"
        )


def _data_root() -> Path:
    package = Path(str(files("timeskeleton")))
    if (package / "schema").is_dir():
        return package
    return Path(__file__).resolve().parents[3]


def schema_path() -> Path:
    """Return the path of the schema document."""
    return _data_root() / "schema" / SCHEMA_VERSION / "timeskeleton.schema.json"


@cache
def load_schema() -> dict[str, Any]:
    """Return the cached parsed schema document; treat it as read-only."""
    with schema_path().open(encoding="utf-8") as handle:
        return json.load(handle)


def fixture_paths() -> list[Path]:
    """Return every bundled manifest fixture, excluding drawings."""
    directory = _data_root() / "fixtures" / SCHEMA_VERSION
    return sorted(
        path
        for path in directory.rglob("*.json")
        if "drawings" not in path.relative_to(directory).parts
    )


def rejection_paths() -> list[Path]:
    """Return the shared rejection cases, sorted by name."""
    directory = _data_root() / "fixtures" / "rejections" / SCHEMA_VERSION
    return sorted(directory.glob("*.json"))


@dataclass(frozen=True)
class RejectionCase:
    """One shared rejection case, read for validation.

    Attributes:
        manifest: The value to validate, with any non-finite number in place.
        path: Where the validator reports the problem.
        code: The rule's code, or ``None`` where the case raises an error
            without one.
        error: The name of the error class where it is not
            ``SchemaValidationError``, else ``None``.
        reason: The rule the case breaks, in words.
    """

    manifest: Any
    path: _Path
    code: str | None
    error: str | None
    reason: str


_NON_FINITE = {"NaN": math.nan, "Infinity": math.inf, "-Infinity": -math.inf}


def rejection_case(path: Path) -> RejectionCase:
    """Read one shared rejection case from ``path``.

    JSON holds no NaN and no infinity, so a case about the finite rule stores
    a finite placeholder at its path and names the value to put there under
    ``non_finite``; the reader puts it in place.

    Raises:
        ValueError: If the file is not JSON or names an unknown non-finite value.
    """
    case = loads(path.read_text(encoding="utf-8"))
    location = tuple(case["path"])
    manifest = case["manifest"]
    if "non_finite" in case:
        name = case["non_finite"]
        if name not in _NON_FINITE:
            raise ValueError(f"{path.name}: {name!r} names no non-finite number")
        owner = manifest
        for segment in location[:-1]:
            owner = owner[segment]
        owner[location[-1]] = _NON_FINITE[name]
    return RejectionCase(
        manifest=manifest,
        path=location,
        code=case["code"],
        error=case.get("error"),
        reason=case["reason"],
    )


def warning_paths() -> list[Path]:
    """Return the shared warning cases, sorted by name."""
    directory = _data_root() / "fixtures" / "warnings" / SCHEMA_VERSION
    return sorted(directory.glob("*.json"))


def loads(text: str) -> Any:
    """Read JSON text as ``parseJson`` reads it in the JavaScript package.

    Integers stay exact at any size and floats stay floats; the constants
    ``NaN``, ``Infinity`` and ``-Infinity`` and a float beyond the range of a
    double are refused.

    Raises:
        ValueError: If the text is not one JSON value or holds a non-finite number.
    """

    def floating(source: str) -> float:
        value = float(source)
        if not math.isfinite(value):
            raise ValueError(f"{source} is beyond the range of a double")
        return value

    def constant(source: str) -> Any:
        raise ValueError(f"{source} is not a JSON number")

    return json.loads(text, parse_float=floating, parse_constant=constant)


_BRANCHES = ("oneOf", "anyOf", "if", "then", "else")


def _allof_bases(node: Any) -> Iterator[str]:
    """Yield the definitions some ``allOf`` refers to: shared bases, not objects."""
    if isinstance(node, list):
        for item in node:
            yield from _allof_bases(item)
    elif isinstance(node, Mapping):
        for entry in node.get("allOf", ()):
            yield entry["$ref"].removeprefix("#/$defs/")
        for value in node.values():
            yield from _allof_bases(value)


def _close(node: Any, inside: bool, bases: frozenset[str]) -> Any:
    """Copy ``node`` with every declared object outside a branch closed."""
    if isinstance(node, list):
        return [_close(item, inside, bases) for item in node]
    if not isinstance(node, Mapping):
        return node
    closed: dict[str, Any] = {}
    for key, value in node.items():
        if key in _BRANCHES:
            closed[key] = _close(value, True, bases)
        elif key == "$defs":
            closed[key] = {
                name: member if name in bases else _close(member, False, bases)
                for name, member in value.items()
            }
        elif key == "properties":
            closed[key] = {
                name: _close(member, False, bases) for name, member in value.items()
            }
        elif key in ("default", "const", "enum"):
            closed[key] = value
        else:
            closed[key] = _close(value, inside, bases)
    if not inside and node.get("type") == "object" and "properties" in node:
        closed["unevaluatedProperties"] = False
    return closed


def _closed_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    """Return the schema with every object closed, the walk that finds unknown keys.

    The document keeps its objects open; this variant, built in memory only,
    sets ``unevaluatedProperties: false`` on every object node with
    ``properties`` outside a ``oneOf``/``anyOf`` branch or an
    ``if``/``then``/``else`` arm, except the bases an ``allOf`` shares, so a
    key no definition declares fails where it stands.
    """
    return _close(schema, False, frozenset(_allof_bases(schema)))


@cache
def _marking_validator() -> Any:
    schema = load_schema()
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(_closed_schema(schema))


def _branch_tag(candidate: Mapping[str, Any], tag: str) -> Any:
    reference = candidate.get("$ref")
    if isinstance(reference, str) and reference.startswith("#/$defs/"):
        candidate = load_schema()["$defs"][reference.removeprefix("#/$defs/")]
    return candidate.get("properties", {}).get(tag, {}).get("const")


def _candidate_leaves(error: ValidationError) -> Iterable[ValidationError]:
    if (
        error.validator in ("oneOf", "anyOf")
        and error.context
        and any(
            all(_key_failures_only(child) for child in branch)
            for branch in _branches(error)
        )
    ):
        return
    children = list(error.context or ())
    tag = error.schema.get("discriminator", {}).get("propertyName")
    if (
        error.validator == "oneOf"
        and tag is not None
        and isinstance(error.instance, Mapping)
    ):
        value = error.instance.get(tag)
        branch = next(
            (
                index
                for index, candidate in enumerate(error.schema["oneOf"])
                if value is not None and _branch_tag(candidate, tag) == value
            ),
            None,
        )
        children = [
            child
            for child in children
            if branch is not None
            and child.schema_path
            and child.schema_path[0] == branch
        ]
    if not children:
        if error.validator != "unevaluatedProperties":
            yield error
        return
    for child in children:
        yield from _candidate_leaves(child)


def _select(errors: Iterable[ValidationError]) -> ValidationError | None:
    best: ValidationError | None = None
    for error in errors:
        for leaf in _candidate_leaves(error):
            if best is None or len(leaf.absolute_path) > len(best.absolute_path):
                best = leaf
    return best


def _key_failures_only(error: ValidationError) -> bool:
    if error.validator == "unevaluatedProperties":
        return True
    if error.validator in ("oneOf", "anyOf") and error.context:
        return any(
            all(_key_failures_only(child) for child in branch)
            for branch in _branches(error)
        )
    return False


def _branches(error: ValidationError) -> Iterable[list[ValidationError]]:
    grouped: dict[Any, list[ValidationError]] = defaultdict(list)
    for child in error.context or ():
        grouped[child.relative_schema_path[0]].append(child)
    return grouped.values()


def _declared(node: Mapping[str, Any]) -> set[str]:
    """The keys an object node declares, its ``allOf`` bases' included, at any depth."""
    declared = set(node["properties"])
    for entry in node.get("allOf", ()):
        declared |= _declared(
            load_schema()["$defs"][entry["$ref"].removeprefix("#/$defs/")]
        )
    return declared


def _keys(errors: Iterable[ValidationError]) -> Iterator[tuple[_Path, str]]:
    for error in errors:
        if error.validator == "unevaluatedProperties":
            declared = _declared(error.schema)
            path = tuple(error.absolute_path)
            for key in error.instance:
                if key not in declared:
                    yield path, key
        elif error.validator in ("oneOf", "anyOf"):
            for branch in _branches(error):
                if all(_key_failures_only(child) for child in branch):
                    yield from _keys(branch)


def _check(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, Mapping) or "timeskeleton" not in value:
        raise SchemaValidationError("not_a_manifest", (), "not a TimeSkeleton manifest")
    if value["timeskeleton"] != SCHEMA_VERSION:
        raise UnsupportedVersionError(value["timeskeleton"])

    finite = next(finite_number_problems(value), None)
    if finite is not None:
        raise finite

    errors = list(_marking_validator().iter_errors(value))
    error = _select(errors)
    if error is not None:
        raise SchemaValidationError("schema", tuple(error.absolute_path), error.message)

    representation = next(representation_problems(value), None)
    if representation is not None:
        raise representation
    semantic = next(_semantic_problems(value), None)
    if semantic is not None:
        raise semantic

    found = set(_keys(errors))
    return [
        {"path": list(path), "key": key}
        for path, key in sorted(found, key=lambda entry: (entry[0], entry[1]))
    ]


def validate(value: Mapping[str, Any]) -> None:
    """Check ``value`` and raise the first schema or semantic violation."""
    _check(value)


def unknown_keys(value: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return sorted unknown keys from the same schema walk used for validation."""
    return _check(value)


def identity_problems(value: Mapping[str, Any]) -> list[SchemaValidationError]:
    """Return all semantic violations in the established identity order.

    Root by root: duplicates, dangling targets, conversion maps, containment
    and segment lines; then reserved ids, cross-root timeline ids, group ids,
    measure-map ids, the manifest id, group members, and graphical orders.
    """
    return list(_semantic_problems(value))
