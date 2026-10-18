/**
 * @timetoalign/timeskeleton: the TimeSkeleton schema, generated types, a
 * validator, the complete and minimal forms, lossless reading and writing,
 * and the font that measures a drawing's text.
 *
 * A TimeSkeleton manifest is one JSON object holding the version marker
 * `timeskeleton` and an array of root timelines, each describing a musical
 * timeline as timetoalign serializes it, optionally named, optionally
 * attributing timelines to groups and optionally styled for drawing. An
 * editor can place many manifests on a canvas, but a manifest knows nothing
 * about where or how often it is placed.
 */

export { complete, DEFAULTS, minimal } from "./defaults.js";
export { type FontMetrics, fontMetrics } from "./font.js";
export { schema } from "./generated/schema.js";
export type {
  Break,
  ConversionMap,
  Coordinate,
  Declaration,
  ElementType,
  FlowControl,
  Fraction,
  Graphical,
  Group,
  Id,
  Jump,
  LinearMap,
  Marker,
  MeasureMapRow,
  Number,
  NumberType,
  Order,
  Paint,
  Region,
  Selector,
  Statement,
  Timeline,
  TimeSkeleton,
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
  identityProblems,
  jsonPointer,
  numberTypeOf,
  type PathSegment,
  parse,
  SCHEMA_VERSION,
  SchemaValidationError,
  type UnknownKey,
  UnsupportedVersionError,
  unknownKeys,
  validate,
} from "./validate.js";
