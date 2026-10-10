/**
 * The TimeSkeleton schema and its validator.
 *
 * The schema object is bundled from `schema/timeskeleton-<version>.schema.json`
 * at the repository root by `scripts/generate.ts`, which also derives the
 * TypeScript types in `generated/`.
 */

import { Ajv2020, type ErrorObject } from "ajv/dist/2020.js";
import { schemas } from "./generated/schema.js";
import type { TimeSkeletonDocument } from "./generated/types.js";

/** The schema version this release publishes: the latest one. */
export const SCHEMA_VERSION = "0.2.0";

/** Every schema version this release validates and migrates, oldest first. */
export const SUPPORTED_VERSIONS: readonly string[] = ["0.1.0", "0.2.0"];

const SCHEMAS: Readonly<Record<string, object>> = schemas;

/** One step of a path into a document: an object key or an array index. */
export type PathSegment = string | number;

/** Thrown when a document declares a schema version this release does not know. */
export class UnsupportedVersionError extends Error {
  /** The declared version, or `null` when the document carries no string `meta.schema_version`. */
  readonly version: string | null;

  constructor(version: string | null) {
    super(
      `unsupported schema_version ${JSON.stringify(version)}; this release supports ${SUPPORTED_VERSIONS.join(", ")}`,
    );
    this.name = "UnsupportedVersionError";
    this.version = version;
  }
}

/**
 * Thrown when a document violates the schema.
 *
 * `path` locates the offending value; `message` reads
 * `<JSON pointer>: <the validator's description>`, the pointer in URI fragment
 * form (`#` for the document root).
 */
export class SchemaValidationError extends Error {
  readonly path: readonly PathSegment[];

  constructor(path: readonly PathSegment[], detail: string) {
    super(`${jsonPointer(path)}: ${detail}`);
    this.name = "SchemaValidationError";
    this.path = path;
  }
}

/** Render a path as a JSON pointer in URI fragment form (`#` for the root). */
export function jsonPointer(path: readonly PathSegment[]): string {
  const segments = path.map((segment) => String(segment).replace(/~/g, "~0").replace(/\//g, "~1"));
  return `#${segments.map((segment) => `/${segment}`).join("")}`;
}

/** Return `meta.schema_version` if present as a string, else `null`. */
export function declaredVersion(document: unknown): string | null {
  if (typeof document !== "object" || document === null) {
    return null;
  }
  const meta = (document as Record<string, unknown>).meta;
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

/** Convert an Ajv instance path to segments, typing array indices as numbers. */
function toPath(instancePath: string, document: unknown): PathSegment[] {
  if (instancePath === "") {
    return [];
  }
  const path: PathSegment[] = [];
  let cursor: unknown = document;
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
 * Pick the error to report: the first one with the deepest path.
 *
 * With the discriminator enabled, Ajv reports the selected `oneOf` branch's
 * value error directly. The deepest path points closest to the offending
 * value; ties go to the first reported, matching the Python validator.
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
 * Check `document` against the schema version it declares.
 *
 * A document whose `meta.schema_version` is one of `SUPPORTED_VERSIONS` is
 * checked against that version's schema. Any other document is checked
 * against the latest schema, which rejects it at `meta.schema_version`.
 *
 * @throws {SchemaValidationError} on the first violation found, with the path to the offending value.
 */
export function validate(document: unknown): asserts document is TimeSkeletonDocument {
  const version = declaredVersion(document);
  const target =
    version !== null && SUPPORTED_VERSIONS.includes(version) ? version : SCHEMA_VERSION;
  const validator = validatorFor(target);
  if (validator(document)) {
    return;
  }
  const error = select(validator.errors ?? []);
  if (error === undefined) {
    throw new SchemaValidationError([], "document is invalid");
  }
  throw new SchemaValidationError(
    toPath(error.instancePath, document),
    error.message ?? error.keyword,
  );
}
