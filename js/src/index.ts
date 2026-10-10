/**
 * @timetoalign/timeskeleton: the TimeSkeleton document schema, generated
 * types, a validator, migrations, and the lossless reader, canonical order and
 * standard writer of a document.
 *
 * A TimeSkeleton document is a JSON object `{ meta, manifest }` describing a
 * set of musical timelines as timetoalign serializes them.
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
export { schema, schemas } from "./generated/schema.js";
export type {
  Coordinate,
  CoordinateNonnegative,
  Fraction,
  FractionNonnegative,
  NumberType,
  TimelineClass,
  TimelineManifest,
  TimeSkeletonDocument,
  TimeUnit,
} from "./generated/types.js";
export { MIGRATIONS, type Migration, MigrationError, migrate } from "./migrate.js";
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
