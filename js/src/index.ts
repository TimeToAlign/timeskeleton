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
export { canonicalManifest, completeManifest, minimalManifest } from "./forms.js";
export { schema } from "./generated/schema.js";
export type {
  Break,
  CompleteBreak,
  CompleteConversionMap,
  CompleteFlowControl,
  CompleteGraphical,
  CompleteGroup,
  CompleteJump,
  CompleteMarker,
  CompleteRegion,
  CompleteTimeline,
  CompleteTimeSkeleton,
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
  LosslessTimeSkeleton,
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
export { JsonSyntaxError, parseJson } from "./json/parse.js";
export {
  isJsonFloat,
  isJsonObject,
  type Json,
  JsonFloat,
  type JsonNumber,
  type Lossless,
} from "./json/value.js";
export { canonicalJson, compactJson } from "./json/write.js";
export { canonicalOrder, dumps } from "./manifest/order.js";
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
  type ValidationCode,
  validate,
} from "./validate.js";
