"""The TimeSkeleton schemas and their validators.

A manifest is checked against ``timeskeleton-<version>.schema.json``, then
for the identity rules the schema cannot express. The schema files, the
manifest fixtures, the font and the drawing specification live at the
repository root and are bundled into the wheel under ``timeskeleton/schema``,
``timeskeleton/fixtures``, ``timeskeleton/fonts`` and ``timeskeleton/docs``.
The resource helpers below find them in either place, so the package works
from an installed wheel and from a source checkout alike.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

SCHEMA_VERSION = "0.5.0"
"""The latest schema version bundled by this package."""

SUPPORTED_VERSIONS: tuple[str, ...] = ("0.5.0",)
"""Every bundled schema version, oldest first."""


class UnsupportedVersionError(ValueError):
    """Raised when a value declares a schema version this release does not know.

    Attributes:
        version: The declared version, or ``None`` when the value carries no
            string ``meta.schema_version``.
    """

    def __init__(self, version: object) -> None:
        self.version = version
        supported = ", ".join(SUPPORTED_VERSIONS)
        super().__init__(
            f"unsupported schema_version {version!r}; this package supports {supported}"
        )


class SchemaValidationError(ValueError):
    """Raised when a manifest violates its schema.

    Attributes:
        path: The location of the offending value as a tuple of object keys and
            array indices, empty for the value root.
        message: The validator's description of the violation.
    """

    def __init__(self, path: tuple[str | int, ...], message: str) -> None:
        self.path = path
        self.message = message
        super().__init__(f"{json_pointer(path)}: {message}")


def json_pointer(path: Iterable[str | int]) -> str:
    """Render a path as a JSON pointer in URI fragment form (``#`` for the root)."""
    segments = [str(segment).replace("~", "~0").replace("/", "~1") for segment in path]
    return "#" + "".join(f"/{segment}" for segment in segments)


def _data_root() -> Path:
    """Return the directory holding ``schema/``, ``fixtures/`` and ``fonts/``."""
    package = Path(str(files("timeskeleton")))
    if (package / "schema").is_dir():
        return package
    return Path(__file__).resolve().parents[3]


def _require_supported(version: str) -> None:
    if version not in SUPPORTED_VERSIONS:
        raise UnsupportedVersionError(version)


def schema_path(version: str = SCHEMA_VERSION) -> Path:
    """Return the path of the schema file for ``version``.

    Raises:
        UnsupportedVersionError: If no schema of that version is bundled.
    """
    _require_supported(version)
    return _data_root() / "schema" / f"timeskeleton-{version}.schema.json"


@cache
def load_schema(version: str = SCHEMA_VERSION) -> dict[str, Any]:
    """Return the parsed schema for ``version``.

    The result is cached and shared; treat it as read-only.

    Raises:
        UnsupportedVersionError: If no schema of that version is bundled.
    """
    with schema_path(version).open(encoding="utf-8") as handle:
        return json.load(handle)


def fixture_paths(version: str = SCHEMA_VERSION) -> list[Path]:
    """Return the bundled fixtures for ``version``, sorted by name.

    Raises:
        UnsupportedVersionError: If no fixtures of that version are bundled.
    """
    _require_supported(version)
    return sorted((_data_root() / "fixtures" / version).glob("*.json"))


def rejection_paths(version: str = SCHEMA_VERSION) -> list[Path]:
    """Return the shared rejection cases for ``version``, sorted by name."""
    _require_supported(version)
    return sorted((_data_root() / "fixtures" / "rejections" / version).glob("*.json"))


@cache
def _validator(version: str) -> Draft202012Validator:
    schema = load_schema(version)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def declared_version(value: object) -> str | None:
    """Return ``meta.schema_version`` if present as a string, else ``None``."""
    if not isinstance(value, Mapping):
        return None
    meta = value.get("meta")
    if not isinstance(meta, Mapping):
        return None
    version = meta.get("schema_version")
    return version if isinstance(version, str) else None


def _branch_tag(candidate: Mapping[str, Any], root: Mapping[str, Any], tag: str) -> Any:
    """Return the ``const`` a ``oneOf`` candidate requires of the tag property.

    A candidate is either inline or a local ``#/$defs/<name>`` reference,
    which is resolved against the root schema.
    """
    reference = candidate.get("$ref")
    if isinstance(reference, str) and reference.startswith("#/$defs/"):
        candidate = root["$defs"][reference.removeprefix("#/$defs/")]
    return candidate.get("properties", {}).get(tag, {}).get("const")


def _candidate_leaves(
    error: ValidationError, root: Mapping[str, Any]
) -> Iterable[ValidationError]:
    """Yield the diagnostic leaves beneath one validator error, left to right.

    A failed ``oneOf``, ``anyOf`` or ``$ref`` holds its sub-errors in
    ``context``. A discriminated ``oneOf`` descends only into the candidate
    whose tag ``const`` equals the instance's tag value, and is itself the
    leaf when no candidate carries that value. Every other error descends
    into all its sub-errors.
    """
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
                if value is not None and _branch_tag(candidate, root, tag) == value
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
        yield error
        return
    for child in children:
        yield from _candidate_leaves(child, root)


def _select(
    errors: Iterable[ValidationError], root: Mapping[str, Any]
) -> ValidationError | None:
    """Pick the error to report under the shared path rule.

    The rule, shared with the TypeScript validator: among the diagnostic
    leaves of every violation, report the one with the deepest instance
    path; ties go to the first leaf reported. A discriminated ``oneOf``
    contributes only the candidate its tag selects.
    """
    best: ValidationError | None = None
    for error in errors:
        for leaf in _candidate_leaves(error, root):
            if best is None or len(leaf.absolute_path) > len(best.absolute_path):
                best = leaf
    return best


def validate(value: Mapping[str, Any]) -> None:
    """Check ``value`` against the schema version it declares.

    A value whose ``meta.schema_version`` is one of ``SUPPORTED_VERSIONS``
    is checked against that version's schema. Any other value is checked
    against the latest schema, which rejects it at ``meta.schema_version``.

    A value the schema accepts is then checked for the identity rules the
    schema cannot express (:func:`identity_problems`).

    Raises:
        SchemaValidationError: On the first violation found, with the path to
            the offending value.
    """
    version = declared_version(value)
    target = version if version in SUPPORTED_VERSIONS else SCHEMA_VERSION
    error = _select(_validator(target).iter_errors(value), load_schema(target))
    if error is not None:
        raise SchemaValidationError(tuple(error.absolute_path), error.message)
    problems = identity_problems(value)
    if problems:
        raise problems[0]


def _element_ids(
    timeline: Mapping[str, Any], path: tuple[str | int, ...]
) -> Iterable[tuple[str, tuple[str | int, ...]]]:
    """Yield every id of a timeline tree with its path, in identity order.

    A timeline contributes its own id, then the ids of its conversion maps,
    regions, breaks, jumps and markers in array order, then its children's
    trees in code-point order of their keys.
    """
    yield timeline["id"], (*path, "id")
    for member in ("conversion_maps", "regions"):
        for index, entry in enumerate(timeline[member]):
            yield entry["id"], (*path, member, index, "id")
    flow = timeline["flow_control"]
    for member in ("breaks", "jumps", "markers"):
        for index, entry in enumerate(flow[member]):
            yield entry["id"], (*path, "flow_control", member, index, "id")
    for key in sorted(timeline["children"]):
        yield from _element_ids(
            timeline["children"][key]["timeline"], (*path, "children", key, "timeline")
        )


def _dangling_targets(
    timeline: Mapping[str, Any], path: tuple[str | int, ...]
) -> Iterable[SchemaValidationError]:
    """Yield a problem for each jump whose target names no marker of its timeline."""
    flow = timeline["flow_control"]
    markers = {marker["id"] for marker in flow["markers"]}
    for index, jump in enumerate(flow["jumps"]):
        if jump["target"] is not None and jump["target"] not in markers:
            yield SchemaValidationError(
                (*path, "flow_control", "jumps", index, "target"),
                f"{jump['target']!r} names no marker of this timeline",
            )
    for key in sorted(timeline["children"]):
        yield from _dangling_targets(
            timeline["children"][key]["timeline"], (*path, "children", key, "timeline")
        )


def identity_problems(value: Mapping[str, Any]) -> list[SchemaValidationError]:
    """Return the violations of the identity rules in a schema-valid manifest.

    Every id of a manifest (timelines, conversion maps, regions, breaks, jumps
    and markers) is unique within it across all kinds: each repeated id is one
    problem, located at its second occurrence in identity order (a timeline,
    then its maps, regions, breaks, jumps and markers, then its children by
    key). A jump's non-null ``target`` names a marker of the same timeline;
    each one that does not is one problem, located at the ``target``. The
    duplicate problems come first.
    """
    problems: list[SchemaValidationError] = []
    first: dict[str, tuple[str | int, ...]] = {}
    for identifier, path in _element_ids(value["timeline"], ("timeline",)):
        if identifier in first:
            earlier = json_pointer(first[identifier])
            problems.append(
                SchemaValidationError(
                    path, f"duplicate id {identifier!r}, first at {earlier}"
                )
            )
        else:
            first[identifier] = path
    problems.extend(_dangling_targets(value["timeline"], ("timeline",)))
    return problems
