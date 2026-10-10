/**
 * Migrations between schema versions.
 *
 * A migration is a pure function from a document at one version to the same
 * document at the next version. `migrate` chains them from the declared
 * version up to `SCHEMA_VERSION` and stamps the result. Each migration is
 * pinned by a fixture pair (the document before and after) in the test suite.
 */

import type { TimeSkeletonDocument } from "./generated/types.js";
import {
  declaredVersion,
  SCHEMA_VERSION,
  SUPPORTED_VERSIONS,
  UnsupportedVersionError,
} from "./validate.js";

export type Migration = (document: Record<string, unknown>) => Record<string, unknown>;

/** Source version to `[target version, migration]`. */
export const MIGRATIONS: Readonly<Record<string, readonly [string, Migration]>> = {
  "0.1.0": ["0.2.0", (document) => document],
};

/**
 * Return a deep copy of `document` brought to `SCHEMA_VERSION`.
 *
 * A document already at the latest version is copied unchanged. The result
 * is not validated; call `validate` on it when the input is untrusted.
 *
 * @throws {UnsupportedVersionError} if `meta.schema_version` is missing, not a string, or not supported.
 */
export function migrate(document: unknown): TimeSkeletonDocument {
  const version = declaredVersion(document);
  if (version === null || !SUPPORTED_VERSIONS.includes(version)) {
    throw new UnsupportedVersionError(version);
  }
  let result = structuredClone(document) as Record<string, unknown>;
  let current = version;
  while (current !== SCHEMA_VERSION) {
    const step = MIGRATIONS[current];
    if (step === undefined) {
      throw new UnsupportedVersionError(current);
    }
    const [next, apply] = step;
    result = apply(result);
    (result.meta as Record<string, unknown>).schema_version = next;
    current = next;
  }
  return result as unknown as TimeSkeletonDocument;
}
