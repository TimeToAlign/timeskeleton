"""The TimeSkeleton manifest schema, its fixtures, a validator and the font.

A manifest describes one musical timeline as timetoalign serializes it. An
editor can place many such timelines on a canvas, but the manifest knows
nothing about where or how often its object is placed.
"""

from __future__ import annotations

from .font import font_metrics, font_path
from .manifest import canonical_json, canonical_order, dumps
from .styles import MissingStyleWarning, complete_styles
from .validate import (
    SCHEMA_VERSION,
    SUPPORTED_VERSIONS,
    SchemaValidationError,
    UnsupportedVersionError,
    declared_version,
    fixture_paths,
    json_pointer,
    load_schema,
    rejection_paths,
    schema_path,
    validate,
)

__all__ = [
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
    "font_metrics",
    "font_path",
    "fixture_paths",
    "json_pointer",
    "load_schema",
    "rejection_paths",
    "schema_path",
    "validate",
]
