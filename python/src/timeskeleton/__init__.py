"""The TimeSkeleton manifest schemas, fixtures, validators and migrations.

A manifest describes one musical timeline as timetoalign serializes it. An
editor can place many such timelines on a canvas, but the manifest knows
nothing about where or how often its object is placed. Published envelopes
remain validatable and can be migrated and divided with :func:`split`.
"""

from __future__ import annotations

from .manifest import canonical_json, canonical_order, dumps
from .migrate import (
    ENVELOPE_VERSIONS,
    MIGRATIONS,
    MigrationError,
    graphical_for_subtree,
    migrate,
    split,
)
from .validate import (
    GEOMETRY_VERSIONS,
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    SchemaValidationError,
    UnsupportedVersionError,
    declared_version,
    fixture_paths,
    geometry_paths,
    geometry_rejection_paths,
    geometry_schema_path,
    json_pointer,
    load_geometry_schema,
    load_schema,
    migration_paths,
    rejection_paths,
    schema_path,
    split_paths,
    validate,
    validate_geometry,
)

__all__ = [
    "ENVELOPE_VERSIONS",
    "GEOMETRY_VERSIONS",
    "MIGRATIONS",
    "MigrationError",
    "SCHEMA_VERSION",
    "SUPPORTED_VERSIONS",
    "SchemaValidationError",
    "UnsupportedVersionError",
    "canonical_json",
    "canonical_order",
    "declared_version",
    "dumps",
    "fixture_paths",
    "geometry_paths",
    "geometry_rejection_paths",
    "geometry_schema_path",
    "graphical_for_subtree",
    "json_pointer",
    "load_geometry_schema",
    "load_schema",
    "migration_paths",
    "migrate",
    "rejection_paths",
    "schema_path",
    "split",
    "split_paths",
    "validate",
    "validate_geometry",
]
