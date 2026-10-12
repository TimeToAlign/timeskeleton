/**
 * @timetoalign/timeskeleton: the TimeSkeleton schemas, generated types, a
 * validator, lossless reading and writing, and the font that measures a
 * drawing's text.
 *
 * A TimeSkeleton file is a timeline file (one manifest describing one musical
 * timeline as timetoalign serializes it), a group file (a timeline group with
 * the timelines it names) or a bundle file (an alignment bundle with all its
 * timelines and groups). An editor can place many of them on a canvas, but a
 * file knows nothing about where or how often its object is placed.
 */

export { type FontMetrics, fontMetrics } from "./font.js";
export { schema, schemaDocuments, schemas } from "./generated/schema.js";
export type {
  Bundle,
  BundleGraphical,
  Coordinate,
  CoordinateNonnegative,
  Declaration,
  ElementType,
  Fraction,
  FractionNonnegative,
  Graphical,
  Group,
  GroupGraphical,
  Id,
  LinearMap,
  Marker,
  MemberOrder,
  Meta,
  NumberType,
  Paint,
  Selector,
  Statement,
  TimelineClass,
  TimelineManifest,
  TimeSkeletonBundleFile,
  TimeSkeletonGroupFile,
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
export { migrate } from "./migrate.js";
export { completeStyles } from "./styles.js";
export {
  declaredVersion,
  FILE_KINDS,
  type FileKind,
  fileKind,
  identityProblems,
  jsonPointer,
  type PathSegment,
  parse,
  SCHEMA_VERSION,
  SchemaValidationError,
  SUPPORTED_VERSIONS,
  type TimeSkeletonFile,
  UnsupportedVersionError,
  validate,
} from "./validate.js";
