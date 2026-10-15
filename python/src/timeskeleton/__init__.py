"""The TimeSkeleton schema, its fixtures, a validator and the font.

A TimeSkeleton manifest is one JSON object holding the version marker
``timeskeleton`` and an array of root timelines, each describing a musical
timeline as timetoalign serializes it, optionally named, optionally
attributing timelines to groups and optionally styled for drawing. An editor
can place many manifests on a canvas, but a manifest knows nothing about
where or how often it is placed.
"""

from __future__ import annotations

from .defaults import DEFAULTS, complete, minimal
from .font import font_metrics, font_path
from .manifest import canonical_json, canonical_order, dumps
from .styles import MissingStyleWarning, complete_styles
from .validate import (
    SCHEMA_VERSION,
    SchemaValidationError,
    UnsupportedVersionError,
    fixture_paths,
    identity_problems,
    json_pointer,
    load_schema,
    number_type_of,
    rejection_paths,
    schema_path,
    unknown_keys,
    validate,
    warning_paths,
)

__all__ = [
    "DEFAULTS",
    "SCHEMA_VERSION",
    "SchemaValidationError",
    "MissingStyleWarning",
    "UnsupportedVersionError",
    "canonical_json",
    "canonical_order",
    "complete",
    "complete_styles",
    "dumps",
    "font_metrics",
    "font_path",
    "fixture_paths",
    "identity_problems",
    "json_pointer",
    "load_schema",
    "minimal",
    "number_type_of",
    "rejection_paths",
    "schema_path",
    "unknown_keys",
    "validate",
    "warning_paths",
]
