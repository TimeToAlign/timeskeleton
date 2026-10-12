"""The TimeSkeleton schemas, their fixtures, a validator and the font.

A TimeSkeleton file is a timeline file (one manifest describing one musical
timeline as timetoalign serializes it), a group file (a timeline group with
the timelines it names) or a bundle file (an alignment bundle with all its
timelines and groups). An editor can place many of them on a canvas, but a
file knows nothing about where or how often its object is placed.
"""

from __future__ import annotations

from .font import font_metrics, font_path
from .manifest import canonical_json, canonical_order, dumps
from .migrate import migrate
from .styles import MissingStyleWarning, complete_styles
from .validate import (
    FILE_KINDS,
    SCHEMA_DOCUMENTS,
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    SchemaValidationError,
    UnsupportedVersionError,
    declared_version,
    file_kind,
    fixture_paths,
    identity_problems,
    json_pointer,
    load_schema,
    rejection_paths,
    schema_documents,
    schema_path,
    validate,
)

__all__ = [
    "FILE_KINDS",
    "SCHEMA_DOCUMENTS",
    "SCHEMA_VERSION",
    "SUPPORTED_VERSIONS",
    "SchemaValidationError",
    "MissingStyleWarning",
    "UnsupportedVersionError",
    "canonical_json",
    "canonical_order",
    "complete_styles",
    "declared_version",
    "dumps",
    "file_kind",
    "font_metrics",
    "font_path",
    "fixture_paths",
    "identity_problems",
    "json_pointer",
    "load_schema",
    "migrate",
    "rejection_paths",
    "schema_documents",
    "schema_path",
    "validate",
]
