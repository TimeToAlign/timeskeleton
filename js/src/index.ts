/**
 * @timetoalign/timeskeleton: TimeSkeleton manifest schemas, generated types,
 * validators, migrations, and lossless reading and writing.
 *
 * A manifest describes one musical timeline as timetoalign serializes it. An
 * editor can place many timelines on a canvas, but a manifest knows nothing
 * about where or how often its object is placed. Published envelopes remain
 * validatable and can be migrated and divided with `split`.
 */

export { geometrySchema, geometrySchemas, schema, schemas } from "./generated/schema.js";
export type {
  Anchor,
  Block,
  BreakPrimitive,
  ChildPrimitive,
  Colour,
  Coordinate,
  CoordinateNonnegative,
  ElementType,
  Fraction,
  FractionNonnegative,
  Frame,
  Geometry,
  Graphical,
  Height,
  JumpPrimitive,
  LabelPrimitive,
  LinearMap,
  LinePattern,
  MapPrimitive,
  NumberType,
  Position,
  Primitive,
  RegionPrimitive,
  Side,
  StyleProperties,
  StyleRule,
  StyleRules,
  StyleSelector,
  TimelineClass,
  TimelineManifest,
  TimelinePrimitive,
  TimeSkeletonManifest,
  TimeUnit,
  WedgePrimitive,
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
export {
  ENVELOPE_VERSIONS,
  graphicalForSubtree,
  MIGRATIONS,
  type Migration,
  MigrationError,
  migrate,
  split,
} from "./migrate.js";
export {
  declaredVersion,
  GEOMETRY_VERSIONS,
  jsonPointer,
  type PathSegment,
  parse,
  SCHEMA_VERSION,
  SchemaValidationError,
  SUPPORTED_VERSIONS,
  UnsupportedVersionError,
  validate,
  validateGeometry,
} from "./validate.js";
