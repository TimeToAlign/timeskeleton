#!/usr/bin/env python
"""Write the advance-width metrics of the bundled font.

Reads ``fonts/DejaVuSans.ttf`` after verifying its SHA-256 and writes
``fonts/dejavu-sans-2.37.metrics.json`` with the standard writer ``dumps``:
``units_per_em`` (``head``), ``ascender`` and ``descender`` (``hhea``, the
descender as a positive depth), ``fallback`` (the advance of glyph 0) and
``advances``, the advance of every code point of the font's best character
map, keyed by the code point in decimal. ``dumps`` sorts every object's keys
by code point. Run it from ``python/`` with
``uv run python ../scripts/extract_font_metrics.py``.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any

from fontTools.ttLib import TTFont

from timeskeleton import dumps

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
FONT = REPOSITORY_ROOT / "fonts" / "DejaVuSans.ttf"
METRICS = REPOSITORY_ROOT / "fonts" / "dejavu-sans-2.37.metrics.json"
SHA256 = "7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954"
"""The SHA-256 of ``ttf/DejaVuSans.ttf`` in the upstream 2.37 release."""


def metrics(font: Path) -> dict[str, Any]:
    """Return the metrics of a TrueType file, refusing any other file."""
    digest = hashlib.sha256(font.read_bytes()).hexdigest()
    if digest != SHA256:
        raise SystemExit(f"{font}: SHA-256 {digest}, expected {SHA256}")
    tt = TTFont(font)
    advances = tt["hmtx"]
    cmap = tt.getBestCmap()
    return {
        "units_per_em": tt["head"].unitsPerEm,
        "ascender": tt["hhea"].ascent,
        "descender": -tt["hhea"].descent,
        "fallback": advances[tt.getGlyphOrder()[0]][0],
        "advances": {
            str(code_point): advances[cmap[code_point]][0]
            for code_point in sorted(cmap)
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and write the metrics file."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--font", type=Path, default=FONT)
    parser.add_argument("--output", type=Path, default=METRICS)
    args = parser.parse_args(argv)
    args.output.write_text(dumps(metrics(args.font)), encoding="utf-8")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
