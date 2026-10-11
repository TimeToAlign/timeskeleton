# 0009. Extract the font metrics with fontTools

Date: 2026-10-11

## Context

The drawing specification measures every text from the advance widths of
DejaVu Sans 2.37. The repository ships `fonts/DejaVuSans.ttf` and
`fonts/dejavu-sans-2.37.metrics.json`, which holds `units_per_em`, the
`hhea` ascender and descender, the advance of glyph 0 and the advance of
every code point of the font's best character map. A development script,
`scripts/extract_font_metrics.py`, derives that file from the TrueType file
once; neither package reads a font at run time.

## Considered options

- fontTools (`fonttools` on PyPI).
- FreeType through `freetype-py`.
- Write the reader ourselves.

## Decision

Use fontTools 4.66.0 as a development dependency of `python/` (the `dev`
dependency group), never a runtime dependency.

- **Fit.** `TTFont` reads the `head`, `hhea`, `hmtx` and `cmap` tables, and
  `getBestCmap()` selects the character map by the platform and encoding
  preference of the OpenType specification, so the script reads the five
  values in a few lines. FreeType answers the same questions through a
  rasterizing library with a native dependency, and reports scaled metrics
  unless asked otherwise.
- **Maintenance.** fontTools is the font toolkit of the type design
  community, maintained since 1999 by a team of maintainers (bus factor well
  above one), released several times a month; licence MIT
  (https://github.com/fonttools/fonttools/blob/main/LICENSE). Its required
  dependencies are none; every other dependency is an optional extra
  (https://pypi.org/project/fonttools/4.66.0/). It has an extensive test
  suite.
- **Writing it ourselves.** Parsing `head`, `hhea`, `hmtx` and the `cmap`
  subtable formats (4 and 12 at least) and reproducing the best-cmap choice
  is a few hundred lines of binary parsing the maintainers would own and
  test, for a script that runs once per font release.
- **Audited version.** 4.66.0, released 2026-09-23 (4.66.1, released
  2026-09-29, is inside the 14-day window).

## Consequences

The metrics file is generated, and the script verifies the SHA-256 of the
TrueType file before reading it. Replacing fontTools only touches the script;
the shipped metrics file and both packages are unaffected. The exit cost is
the reader above.

## Review date

2027-10-11.
