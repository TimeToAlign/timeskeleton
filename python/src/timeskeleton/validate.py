"""The TimeSkeleton schemas and their validators.

A manifest or published envelope is checked against
``timeskeleton-<version>.schema.json``; the
geometry of its drawing (``docs/geometry.md``), from 0.3.0 on, against
``geometry-<version>.schema.json``. The schema files and the manifest and envelope
fixtures live at the repository root and are bundled into the wheel under
``timeskeleton/schema`` and ``timeskeleton/fixtures``. The resource helpers
below find them in either place, so the package works from an installed
wheel and from a source checkout alike.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

SCHEMA_VERSION = "0.4.0"
"""The latest schema version bundled by this package."""

SUPPORTED_VERSIONS: tuple[str, ...] = (
    "0.1.0",
    "0.2.0",
    "0.2.1",
    "0.3.0",
    "0.4.0",
)
"""Every bundled schema version, oldest first."""

GEOMETRY_VERSIONS: tuple[str, ...] = ("0.3.0",)
"""Every schema version with a geometry schema, oldest first."""


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
    """Raised when a manifest or envelope violates its schema.

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
    """Return the directory holding ``schema/`` and ``fixtures/``."""
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


def geometry_schema_path(version: str = GEOMETRY_VERSIONS[-1]) -> Path:
    """Return the path of the geometry schema file for ``version``.

    Raises:
        UnsupportedVersionError: If no geometry schema of that version is bundled.
    """
    if version not in GEOMETRY_VERSIONS:
        raise UnsupportedVersionError(version)
    return _data_root() / "schema" / f"geometry-{version}.schema.json"


@cache
def load_geometry_schema(version: str = GEOMETRY_VERSIONS[-1]) -> dict[str, Any]:
    """Return the parsed geometry schema for ``version``.

    The result is cached and shared; treat it as read-only.

    Raises:
        UnsupportedVersionError: If no geometry schema of that version is bundled.
    """
    with geometry_schema_path(version).open(encoding="utf-8") as handle:
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


def geometry_paths(version: str = GEOMETRY_VERSIONS[-1]) -> list[Path]:
    """Return the geometry fixture directories for ``version``, sorted by name.

    Each directory is named after the envelope fixture it draws and holds
    ``geometry.json``, ``figure.svg`` and ``figure.tex``.
    """
    if version not in GEOMETRY_VERSIONS:
        raise UnsupportedVersionError(version)
    root = _data_root() / "fixtures" / version / "geometry"
    return sorted(path for path in root.iterdir() if path.is_dir())


def geometry_rejection_paths(version: str = GEOMETRY_VERSIONS[-1]) -> list[Path]:
    """Return the shared geometry rejection cases for ``version``, sorted by name.

    Each case is ``{"geometry", "path", "reason"}``: a geometry the geometry
    schema rejects, and the path both validators report.
    """
    if version not in GEOMETRY_VERSIONS:
        raise UnsupportedVersionError(version)
    root = _data_root() / "fixtures" / version / "geometry-rejections"
    return sorted(root.glob("*.json"))


def migration_paths() -> list[tuple[Path, Path]]:
    """Return sorted ``(before, after)`` migration fixture pairs."""
    root = _data_root() / "fixtures" / "migrations"
    return sorted(
        (directory / "before.json", directory / "after.json")
        for directory in root.iterdir()
        if directory.is_dir()
        and re.fullmatch(r"\d+\.\d+\.\d+-to-\d+\.\d+\.\d+", directory.name)
        and (directory / "before.json").is_file()
        and (directory / "after.json").is_file()
    )


def split_paths() -> tuple[Path, list[Path]]:
    """Return the split input and its outputs, sorted by name."""
    root = _data_root() / "fixtures" / "migrations" / "split" / "0.3.0"
    return root / "before.json", sorted((root / "after").glob("*.json"))


@cache
def _validator(version: str) -> Draft202012Validator:
    schema = load_schema(version)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@cache
def _geometry_validator(version: str) -> Draft202012Validator:
    schema = load_geometry_schema(version)
    Draft202012Validator.check_schema(schema)
    # The geometry schema refers to the envelope schema of its version by
    # that schema's $id. Embedded under $defs, the envelope schema is a
    # resource of its own that those references resolve to.
    combined = {
        **schema,
        "$defs": {**schema["$defs"], "envelope": load_schema(version)},
    }
    return Draft202012Validator(combined)


@cache
def _geometry_definitions(version: str) -> dict[str, Any]:
    """Both schemas' definitions, for resolving discriminated candidates.

    A candidate reference ``#/$defs/<name>`` is local to the schema holding
    it, the envelope schema or the geometry schema; their definition names
    are disjoint, so one table resolves both.
    """
    definitions = {**load_schema(version)["$defs"]}
    definitions.update(load_geometry_schema(version)["$defs"])
    return {"$defs": definitions}


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

    Raises:
        SchemaValidationError: On the first violation found, with the path to
            the offending value.
    """
    version = declared_version(value)
    target = version if version in SUPPORTED_VERSIONS else SCHEMA_VERSION
    error = _select(_validator(target).iter_errors(value), load_schema(target))
    if error is not None:
        raise SchemaValidationError(tuple(error.absolute_path), error.message)


def validate_geometry(geometry: Mapping[str, Any]) -> None:
    """Check ``geometry`` against the geometry schema of the version it declares.

    A geometry whose ``meta.schema_version`` is one of ``GEOMETRY_VERSIONS`` is
    checked against that version's geometry schema; any other is checked
    against the latest one, which rejects it at ``meta.schema_version``.

    Raises:
        SchemaValidationError: On the first violation found under the shared
            path rule, with the path to the offending value.
    """
    version = declared_version(geometry)
    target = version if version in GEOMETRY_VERSIONS else GEOMETRY_VERSIONS[-1]
    error = _select(
        _geometry_validator(target).iter_errors(geometry),
        _geometry_definitions(target),
    )
    if error is not None:
        raise SchemaValidationError(tuple(error.absolute_path), error.message)
