/**
 * @timetoalign/timeskeleton: the TimeSkeleton document schema, generated
 * types, a validator and migrations.
 *
 * A TimeSkeleton document is a JSON object `{ meta, manifest }` describing a
 * set of musical timelines as timetoalign serializes them.
 */

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
  SCHEMA_VERSION,
  SchemaValidationError,
  SUPPORTED_VERSIONS,
  UnsupportedVersionError,
  validate,
} from "./validate.js";
