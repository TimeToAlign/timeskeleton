/**
 * Migration of a value to the latest schema version.
 *
 * Each step rewrites a value of one version into the next. The steps form one
 * ordered chain from the oldest supported version to `SCHEMA_VERSION`; a later
 * schema version appends one step. Python's `timeskeleton.migrate` holds the
 * same chain.
 */

import { clone } from "./manifest.js";
import { declaredVersion, SUPPORTED_VERSIONS, UnsupportedVersionError } from "./validate.js";

type JsonObject = Record<string, unknown>;

/** One step: the version it reads, the version it writes, and the rewrite of its own copy. */
interface Step {
  readonly source: string;
  readonly target: string;
  readonly apply: (value: JsonObject) => JsonObject;
}

/** A step that only rewrites `meta.schema_version` to `version`. */
function declare(version: string): (value: JsonObject) => JsonObject {
  return (value) => {
    (value.meta as JsonObject).schema_version = version;
    return value;
  };
}

const STEPS: readonly Step[] = [{ source: "0.5.0", target: "0.6.0", apply: declare("0.6.0") }];

/**
 * Return a copy of `value` rewritten to the latest schema version.
 *
 * The value's declared `meta.schema_version` selects where the chain of steps
 * starts; a value already at the latest version is returned as an equal copy.
 * The input is never changed, and the copy keeps what `parseJson` read: exact
 * integers, integral floats and the order of keys. The result is not validated.
 *
 * @throws {UnsupportedVersionError} if the value declares no supported version.
 */
export function migrate<T>(value: T): T {
  let version = declaredVersion(value);
  if (version === null || !SUPPORTED_VERSIONS.includes(version)) {
    throw new UnsupportedVersionError(version);
  }
  let result = clone(value) as unknown as JsonObject;
  for (const step of STEPS) {
    if (version === step.source) {
      result = step.apply(result);
      version = step.target;
    }
  }
  return result as unknown as T;
}
