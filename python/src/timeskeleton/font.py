"""The font that measures every text of a drawing.

``docs/drawing.md`` draws every text in DejaVu Sans 2.37 and measures it from
the font's advance widths. The TrueType file, its licence and its metrics are
bundled with the package.
"""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from .validate import _data_root

FONT_FILE = "DejaVuSans.ttf"
METRICS_FILE = "dejavu-sans-2.37.metrics.json"


def font_path() -> Path:
    """Return the path of the bundled ``DejaVuSans.ttf``."""
    return _data_root() / "fonts" / FONT_FILE


@cache
def _metrics() -> dict[str, Any]:
    with (_data_root() / "fonts" / METRICS_FILE).open(encoding="utf-8") as handle:
        return json.load(handle)


def font_metrics() -> dict[str, Any]:
    """Return the bundled font's metrics.

    The members are ``units_per_em``, ``ascender``, ``descender`` (a positive
    depth), ``fallback`` (the advance of glyph 0, counted for an unmapped code
    point) and ``advances``, the advance of every mapped code point keyed by
    the code point in decimal. The result is cached and shared; treat it as
    read-only.
    """
    return _metrics()
