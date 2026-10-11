/**
 * The font that measures every text of a drawing.
 *
 * `docs/drawing.md` draws every text in DejaVu Sans 2.37 and measures it from
 * the font's advance widths. The TrueType file and its licence are shipped
 * as `@timetoalign/timeskeleton/fonts/DejaVuSans.ttf` and
 * `@timetoalign/timeskeleton/fonts/LICENSE`; the metrics are bundled here.
 */

export { fontMetrics } from "./generated/font.js";

/** The advance-width metrics of a font, in font units. */
export interface FontMetrics {
  readonly units_per_em: number;
  readonly ascender: number;
  /** The descender as a positive depth. */
  readonly descender: number;
  /** The advance of glyph 0, counted for a code point the font does not map. */
  readonly fallback: number;
  /** The advance of every mapped code point, keyed by the code point in decimal. */
  readonly advances: Readonly<Record<string, number>>;
}
