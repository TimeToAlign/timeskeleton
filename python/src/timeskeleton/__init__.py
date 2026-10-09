"""timeskeleton: the TimeSkeleton document schema, its fixtures and validator.

A TimeSkeleton document is a JSON object ``{"meta": ..., "manifest": ...}``
describing a set of musical timelines as timetoalign serializes them. This
package bundles every published schema version, the golden fixtures emitted
by timetoalign, a validator reporting the path of the first violation, and
the migrations that bring an older document to the latest version.
"""

from __future__ import annotations

from .migrate import MIGRATIONS, migrate
from .validate import (
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    SchemaValidationError,
    UnsupportedVersionError,
    declared_version,
    fixture_paths,
    json_pointer,
    load_schema,
    schema_path,
    validate,
)

__all__ = [
    "MIGRATIONS",
    "SCHEMA_VERSION",
    "SUPPORTED_VERSIONS",
    "SchemaValidationError",
    "UnsupportedVersionError",
    "declared_version",
    "fixture_paths",
    "json_pointer",
    "load_schema",
    "migrate",
    "schema_path",
    "validate",
]
