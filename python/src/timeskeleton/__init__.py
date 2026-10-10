"""timeskeleton: the TimeSkeleton document schema, its fixtures and validator.

A TimeSkeleton document is a JSON object ``{"meta": ..., "manifest": ...}``
describing a set of musical timelines as timetoalign serializes them. This
package bundles every published schema version, the golden fixtures emitted
by timetoalign, a validator reporting the path of the first violation, the
migrations that bring an older document to the latest version, and the
canonical order and standard writer of a document, and the schema and
validator of the geometry a document is drawn as (from 0.3.0 on).
"""

from __future__ import annotations

from .document import canonical_json, canonical_order, dumps
from .migrate import MIGRATIONS, MigrationError, migrate
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
    validate,
    validate_geometry,
)

__all__ = [
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
    "json_pointer",
    "load_geometry_schema",
    "load_schema",
    "migration_paths",
    "migrate",
    "rejection_paths",
    "schema_path",
    "validate",
    "validate_geometry",
]
