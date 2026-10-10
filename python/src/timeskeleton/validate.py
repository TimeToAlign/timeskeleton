"""The TimeSkeleton schema and its validator.

The schema files and the golden fixtures live at the repository root and are
bundled into the wheel under ``timeskeleton/schema`` and
``timeskeleton/fixtures``. The resource helpers below find them in either
place, so the package works from an installed wheel and from a source
checkout alike.
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

SCHEMA_VERSION = "0.2.0"
"""The schema version this release publishes: the latest one."""

SUPPORTED_VERSIONS: tuple[str, ...] = ("0.1.0", "0.2.0")
"""Every schema version this release validates and migrates, oldest first."""


class UnsupportedVersionError(ValueError):
    """Raised when a document declares a schema version this release does not know.

    Attributes:
        version: The declared version, or ``None`` when the document carries no
            string ``meta.schema_version``.
    """

    def __init__(self, version: object) -> None:
        self.version = version
        supported = ", ".join(SUPPORTED_VERSIONS)
        super().__init__(
            f"unsupported schema_version {version!r}; this release supports {supported}"
        )


class SchemaValidationError(ValueError):
    """Raised when a document violates the schema.

    Attributes:
        path: The location of the offending value as a tuple of object keys and
            array indices, empty for the document root.
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


def fixture_paths(version: str = SCHEMA_VERSION) -> list[Path]:
    """Return the bundled fixture documents for ``version``, sorted by name.

    Raises:
        UnsupportedVersionError: If no fixtures of that version are bundled.
    """
    _require_supported(version)
    return sorted((_data_root() / "fixtures" / version).glob("*.json"))


def rejection_paths(version: str = SCHEMA_VERSION) -> list[Path]:
    """Return the shared rejection cases for ``version``, sorted by name."""
    _require_supported(version)
    return sorted((_data_root() / "fixtures" / "rejections" / version).glob("*.json"))


def migration_paths() -> list[tuple[Path, Path]]:
    """Return sorted ``(before, after)`` migration fixture pairs."""
    root = _data_root() / "fixtures" / "migrations"
    return sorted(
        (directory / "before.json", directory / "after.json")
        for directory in root.iterdir()
        if directory.is_dir()
        and (directory / "before.json").is_file()
        and (directory / "after.json").is_file()
    )


@cache
def _validator(version: str) -> Draft202012Validator:
    schema = load_schema(version)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def declared_version(document: object) -> str | None:
    """Return ``meta.schema_version`` if present as a string, else ``None``."""
    if not isinstance(document, Mapping):
        return None
    meta = document.get("meta")
    if not isinstance(meta, Mapping):
        return None
    version = meta.get("schema_version")
    return version if isinstance(version, str) else None


def _leaf_errors(error: ValidationError) -> Iterable[ValidationError]:
    """Yield the leaves beneath a validator error, left to right."""
    if not error.context:
        yield error
        return
    for child in error.context:
        yield from _leaf_errors(child)


def _candidate_leaves(error: ValidationError) -> Iterable[ValidationError]:
    """Yield diagnostic leaves for the selected discriminated branch."""
    if error.validator != "oneOf" or not isinstance(error.instance, Mapping):
        yield from _leaf_errors(error)
        return
    discriminator = error.schema.get("discriminator", {}).get("propertyName")
    if discriminator is None:
        branch_for_type = {"int": 0, "float": 1, "fraction": 2}
        branch = branch_for_type.get(error.instance.get("number_type"))
        if branch is not None:
            selected = [
                child
                for child in error.context
                if child.schema_path and child.schema_path[0] == branch
            ]
            if selected:
                for child in selected:
                    yield from _leaf_errors(child)
                return
        yield from _leaf_errors(error)
        return
    value = error.instance.get(discriminator)
    branch = next(
        (
            index
            for index, candidate in enumerate(error.schema.get("oneOf", []))
            if candidate.get("$ref", "").rsplit("/", 1)[-1] == value
            or candidate.get("properties", {}).get(discriminator, {}).get("const")
            == value
        ),
        None,
    )
    if branch is None:
        yield error
        return
    selected = [
        child
        for child in error.context
        if child.schema_path and child.schema_path[0] == branch
    ]
    if not selected:
        yield from _leaf_errors(error)
        return
    for child in selected:
        yield from _leaf_errors(child)


def _select(errors: Iterable[ValidationError]) -> ValidationError | None:
    """Pick the error to report: the first leaf with the deepest path.

    A failed ``oneOf`` holds its branch diagnostics in ``context``. Looking at
    its leaves keeps the reported location as close as possible to the bad
    value, matching the Ajv validator. Ties go to the first reported leaf.
    """
    best: ValidationError | None = None
    for error in errors:
        for leaf in _candidate_leaves(error):
            if best is None or len(leaf.absolute_path) > len(best.absolute_path):
                best = leaf
    return best


def validate(document: Mapping[str, Any]) -> None:
    """Check ``document`` against the schema version it declares.

    A document whose ``meta.schema_version`` is one of ``SUPPORTED_VERSIONS``
    is checked against that version's schema. Any other document is checked
    against the latest schema, which rejects it at ``meta.schema_version``.

    Raises:
        SchemaValidationError: On the first violation found, with the path to
            the offending value.
    """
    version = declared_version(document)
    target = version if version in SUPPORTED_VERSIONS else SCHEMA_VERSION
    error = _select(_validator(target).iter_errors(document))
    if error is not None:
        path = tuple(error.absolute_path)
        if error.validator == "const" and path[-1:] == ("class",):
            path = path[:-1]
        raise SchemaValidationError(path, error.message)
