/**
 * @timetoalign/timeskeleton: the TimeSkeleton manifest schema, generated
 * types, a validator, lossless reading and writing, and the font that
 * measures a drawing's text.
 *
 * A manifest describes one musical timeline as timetoalign serializes it. An
 * editor can place many timelines on a canvas, but a manifest knows nothing
 * about where or how often its object is placed.
 */

export { type FontMetrics, fontMetrics } from "./font.js";
export { schema, schemas } from "./generated/schema.js";
export type {
  Coordinate,
  CoordinateNonnegative,
  Declaration,
  ElementType,
  Fraction,
  FractionNonnegative,
  Graphical,
  LinearMap,
  NumberType,
  Paint,
  Selector,
  Statement,
  TimelineClass,
  TimelineManifest,
  TimeSkeletonManifest,
  TimeUnit,
} from "./generated/types.js";
export {
  canonicalJson,
  canonicalOrder,
  compactJson,
  dumps,
  isJsonFloat,
  isJsonObject,
  type Json,
  JsonFloat,
  type JsonNumber,
  type Lossless,
  parseJson,
} from "./manifest.js";
export { completeStyles } from "./styles.js";
export {
  declaredVersion,
  jsonPointer,
  type PathSegment,
  parse,
  SCHEMA_VERSION,
  SchemaValidationError,
  SUPPORTED_VERSIONS,
  UnsupportedVersionError,
  validate,
} from "./validate.js";
