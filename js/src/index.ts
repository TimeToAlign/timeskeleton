/**
 * @timetoalign/timeskeleton: the TimeSkeleton document schema, generated
 * types, a validator, migrations, and the lossless reader, canonical order and
 * standard writer of a document.
 *
 * A TimeSkeleton document is a JSON object `{ meta, manifest }` describing a
 * set of musical timelines as timetoalign serializes them; its geometry is the
 * drawing laid out from it (`docs/geometry.md`).
 */

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
} from "./document.js";
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
  TimeSkeletonDocument,
  TimeUnit,
  WedgePrimitive,
} from "./generated/types.js";
export { MIGRATIONS, type Migration, MigrationError, migrate } from "./migrate.js";
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
