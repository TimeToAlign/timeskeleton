/**
 * The TimeSkeleton schemas and their validators.
 *
 * The schema objects are bundled from `schema/timeskeleton-<version>.schema.json`
 * and, from 0.3.0 on, `schema/geometry-<version>.schema.json` (the geometry of
 * a drawing, `docs/geometry.md`) at the repository root by
 * `scripts/generate.ts`, which also derives the TypeScript types in
 * `generated/`.
 */

import { Ajv2020, type ErrorObject } from "ajv/dist/2020.js";
import { geometrySchemas, schemas } from "./generated/schema.js";
import type { Geometry, TimeSkeletonManifest } from "./generated/types.js";
import { type Lossless, parseJson, plain } from "./manifest.js";

/** The latest schema version bundled by this package. */
export const SCHEMA_VERSION = "0.4.0";

/** Every bundled schema version, oldest first. */
export const SUPPORTED_VERSIONS: readonly string[] = ["0.1.0", "0.2.0", "0.2.1", "0.3.0", "0.4.0"];

/** Every schema version with a geometry schema, oldest first. */
export const GEOMETRY_VERSIONS: readonly string[] = ["0.3.0"];

const SCHEMAS: Readonly<Record<string, object>> = schemas;
const GEOMETRY_SCHEMAS: Readonly<Record<string, object>> = geometrySchemas;

/** One step of a path into a value: an object key or an array index. */
export type PathSegment = string | number;

/** Thrown when a value declares a schema version this release does not know. */
export class UnsupportedVersionError extends Error {
  /** The declared version, or `null` when the value carries no string `meta.schema_version`. */
  readonly version: string | null;

  constructor(version: string | null) {
    super(
      `unsupported schema_version ${JSON.stringify(version)}; this package supports ${SUPPORTED_VERSIONS.join(", ")}`,
    );
    this.name = "UnsupportedVersionError";
    this.version = version;
  }
}

/**
 * Thrown when a value violates the schema.
 *
 * `path` locates the offending value and `detail` is the validator's
 * description; `message` reads `<JSON pointer>: <detail>`, the pointer in URI
 * fragment form (`#` for the value root).
 */
export class SchemaValidationError extends Error {
  readonly path: readonly PathSegment[];
  /** The validator's description of the violation, without the path. */
  readonly detail: string;

  constructor(path: readonly PathSegment[], detail: string) {
    super(`${jsonPointer(path)}: ${detail}`);
    this.name = "SchemaValidationError";
    this.path = path;
    this.detail = detail;
  }
}

/** Render a path as a JSON pointer in URI fragment form (`#` for the root). */
export function jsonPointer(path: readonly PathSegment[]): string {
  const segments = path.map((segment) => String(segment).replace(/~/g, "~0").replace(/\//g, "~1"));
  return `#${segments.map((segment) => `/${segment}`).join("")}`;
}

/** Return `meta.schema_version` if present as a string, else `null`. */
export function declaredVersion(value: unknown): string | null {
  if (typeof value !== "object" || value === null) {
    return null;
  }
  const meta = (value as Record<string, unknown>).meta;
  if (typeof meta !== "object" || meta === null) {
    return null;
  }
  const version = (meta as Record<string, unknown>).schema_version;
  return typeof version === "string" ? version : null;
}

const ajv = new Ajv2020({
  strict: false,
  allErrors: true,
  allowUnionTypes: true,
  discriminator: true,
});
const validators = new Map<string, ReturnType<typeof ajv.compile>>();

function validatorFor(version: string): ReturnType<typeof ajv.compile> {
  let validator = validators.get(version);
  if (validator === undefined) {
    const versionSchema = SCHEMAS[version];
    if (versionSchema === undefined) {
      throw new UnsupportedVersionError(version);
    }
    validator = ajv.compile(versionSchema);
    validators.set(version, validator);
  }
  return validator;
}

const geometryValidators = new Map<string, ReturnType<typeof ajv.compile>>();

function geometryValidatorFor(version: string): ReturnType<typeof ajv.compile> {
  let validator = geometryValidators.get(version);
  if (validator === undefined) {
    const geometrySchema = GEOMETRY_SCHEMAS[version];
    if (geometrySchema === undefined) {
      throw new UnsupportedVersionError(version);
    }
    // The geometry schema refers to the envelope schema of its version by
    // that schema's $id, which compiling the envelope schema registers.
    validatorFor(version);
    validator = ajv.compile(geometrySchema);
    geometryValidators.set(version, validator);
  }
  return validator;
}

/** Convert an Ajv instance path to segments, typing array indices as numbers. */
function toPath(instancePath: string, value: unknown): PathSegment[] {
  if (instancePath === "") {
    return [];
  }
  const path: PathSegment[] = [];
  let cursor: unknown = value;
  for (const raw of instancePath.slice(1).split("/")) {
    const key = raw.replace(/~1/g, "/").replace(/~0/g, "~");
    if (Array.isArray(cursor)) {
      const index = Number(key);
      path.push(index);
      cursor = cursor[index];
    } else {
      path.push(key);
      cursor =
        typeof cursor === "object" && cursor !== null
          ? (cursor as Record<string, unknown>)[key]
          : undefined;
    }
  }
  return path;
}

/**
 * Pick the error to report under the shared path rule.
 *
 * The rule, shared with the Python validator: among the diagnostic leaves of
 * every violation, report the one with the deepest instance path; ties go to
 * the first leaf reported. A discriminated `oneOf` contributes only the
 * candidate whose tag `const` equals the instance's tag value, or itself when
 * no candidate carries that value. Ajv's `discriminator` keyword applies that
 * selection; the shared rejection fixtures pin the paths both validators report.
 */
function select(errors: readonly ErrorObject[]): ErrorObject | undefined {
  let best: ErrorObject | undefined;
  let bestDepth = -1;
  for (const error of errors) {
    const depth = error.instancePath === "" ? 0 : error.instancePath.split("/").length - 1;
    if (depth > bestDepth) {
      best = error;
      bestDepth = depth;
    }
  }
  return best;
}

/**
 * Check `value` against the schema version it declares.
 *
 * A value whose `meta.schema_version` is one of `SUPPORTED_VERSIONS` is
 * checked against that version's schema. Any other value is checked
 * against the latest schema, which rejects it at `meta.schema_version`. A
 * value read by `parse` is checked by the exact values of its numbers.
 *
 * @throws {SchemaValidationError} on the first violation found, with the path to the offending value.
 */
export function validate(value: unknown): asserts value is TimeSkeletonManifest {
  const version = declaredVersion(value);
  const target =
    version !== null && SUPPORTED_VERSIONS.includes(version) ? version : SCHEMA_VERSION;
  const validator = validatorFor(target);
  const instance = plain(value);
  if (!validator(instance)) reject(validator.errors ?? [], instance);
}

/** Throw the error the shared path rule selects among a failed validation's errors. */
function reject(errors: readonly ErrorObject[], instance: unknown): never {
  const error = select(errors);
  if (error === undefined) {
    throw new SchemaValidationError([], "value is invalid");
  }
  throw new SchemaValidationError(
    toPath(error.instancePath, instance),
    error.message ?? error.keyword,
  );
}

/**
 * Check `geometry` against the geometry schema of the version it declares.
 *
 * A geometry whose `meta.schema_version` is one of `GEOMETRY_VERSIONS` is
 * checked against that version's geometry schema; any other is checked
 * against the latest one, which rejects it at `meta.schema_version`. A value
 * read by `parseJson` is checked by the exact values of its numbers.
 *
 * @throws {SchemaValidationError} on the first violation found under the shared path rule.
 */
export function validateGeometry(geometry: unknown): asserts geometry is Geometry {
  const version = declaredVersion(geometry);
  const latest = GEOMETRY_VERSIONS[GEOMETRY_VERSIONS.length - 1] as string;
  const target = version !== null && GEOMETRY_VERSIONS.includes(version) ? version : latest;
  const validator = geometryValidatorFor(target);
  const instance = plain(geometry);
  if (!validator(instance)) reject(validator.errors ?? [], instance);
}

/**
 * Read a TimeSkeleton value without losing a number or the order of a key
 * (see `parseJson`), and check it against the schema version it declares.
 *
 * @throws {SyntaxError} if the text is not one JSON value.
 * @throws {SchemaValidationError} on the first violation found.
 */
export function parse(text: string): Lossless<TimeSkeletonManifest> {
  const value = parseJson(text);
  validate(value);
  return value as unknown as Lossless<TimeSkeletonManifest>;
}
