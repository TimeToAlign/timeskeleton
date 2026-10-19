/** The TimeSkeleton schema validator and its public diagnostics. */

import { Ajv2020, type ErrorObject } from "ajv/dist/2020.js";
import { schema } from "./generated/schema.js";
import type { LosslessTimeSkeleton } from "./generated/types.js";
import { parseJson } from "./json/parse.js";
import { isJsonObject, type JsonObject, plain } from "./json/value.js";
import { compareCodePoints, spell } from "./json/write.js";
import { jsonPointer, type PathSegment, SchemaValidationError } from "./validate/diagnostics.js";
import { identityProblems as semanticProblems } from "./validate/identity.js";
import { finiteNumberProblems, representationProblems } from "./validate/representation.js";

export type { JsonObject } from "./json/value.js";
export {
  entries,
  jsonPointer,
  lengthOf,
  numberTypeOf,
  type PathSegment,
  SchemaValidationError,
  text,
  UNIT_NUMBER_TYPES,
  type ValidationCode,
} from "./validate/diagnostics.js";

/** The schema version this package reads and writes, the only one it supports. */
export const SCHEMA_VERSION = "0.7.0";

/** Thrown when a manifest's version marker names a version other than `SCHEMA_VERSION`. */
export class UnsupportedVersionError extends Error {
  readonly version: unknown;

  constructor(version: unknown) {
    super(
      `unsupported TimeSkeleton version ${spell(version)}; this package reads ${SCHEMA_VERSION} only`,
    );
    this.name = "UnsupportedVersionError";
    this.version = version;
  }
}

/** A key the schema does not declare on the object at `path`. */
export interface UnknownKey {
  readonly path: readonly PathSegment[];
  readonly key: string;
}

const OPTIONS = {
  strict: false,
  allErrors: true,
  allowUnionTypes: true,
  discriminator: true,
} as const;

type Node = Readonly<Record<string, unknown>>;

const BRANCHES = new Set(["oneOf", "anyOf", "if", "then", "else"]);

/** The definitions some `allOf` refers to: shared bases, not objects. */
function allOfBases(node: unknown, found = new Set<string>()): Set<string> {
  if (Array.isArray(node)) {
    for (const item of node) allOfBases(item, found);
  } else if (typeof node === "object" && node !== null) {
    for (const entry of ((node as Node).allOf ?? []) as Node[]) {
      found.add((entry.$ref as string).slice("#/$defs/".length));
    }
    for (const value of Object.values(node)) allOfBases(value, found);
  }
  return found;
}

/** Copy `node` with every declared object outside a branch closed. */
function close(node: unknown, inside: boolean, bases: ReadonlySet<string>): unknown {
  if (Array.isArray(node)) return node.map((item) => close(item, inside, bases));
  if (typeof node !== "object" || node === null) return node;
  const closed: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(node)) {
    if (BRANCHES.has(key)) closed[key] = close(value, true, bases);
    else if (key === "$defs" || key === "properties") {
      closed[key] = Object.fromEntries(
        Object.entries(value as Node).map(([name, member]) => [
          name,
          key === "$defs" && bases.has(name) ? member : close(member, false, bases),
        ]),
      );
    } else if (["default", "const", "enum"].includes(key)) closed[key] = value;
    else closed[key] = close(value, inside, bases);
  }
  const object = node as Node;
  if (!inside && object.type === "object" && "properties" in object) {
    closed.unevaluatedProperties = false;
  }
  return closed;
}

/**
 * The schema with every object closed, the walk that finds unknown keys.
 *
 * The document keeps its objects open; this variant, built in memory only,
 * sets `unevaluatedProperties: false` on every object node with `properties`
 * outside a `oneOf`/`anyOf` branch or an `if`/`then`/`else` arm, except the
 * bases an `allOf` shares, so a key no definition declares fails where it
 * stands.
 */
function closedSchema(document: Node): Node {
  return close(document, false, allOfBases(document)) as Node;
}

const check = new Ajv2020(OPTIONS).compile(schema);
const marking = new Ajv2020(OPTIONS).compile(closedSchema(schema));

/** Convert an Ajv instance path to segments, typing array indices as numbers. */
function toPath(instancePath: string, value: unknown): PathSegment[] {
  if (instancePath === "") return [];
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
      cursor = isJsonObject(cursor) ? cursor[key] : undefined;
    }
  }
  return path;
}

/** Pick the deepest diagnostic leaf, with the first reported leaf winning ties. */
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

/** Order paths segment by segment: indices by number, keys by code point, prefixes first. */
function comparePaths(left: readonly PathSegment[], right: readonly PathSegment[]): number {
  for (let index = 0; index < Math.min(left.length, right.length); index += 1) {
    const a = left[index] as PathSegment;
    const b = right[index] as PathSegment;
    if (a === b) continue;
    if (typeof a === "number" && typeof b === "number") return a < b ? -1 : 1;
    return compareCodePoints(String(a), String(b));
  }
  return left.length - right.length;
}

function first(problems: Iterable<SchemaValidationError>): SchemaValidationError | undefined {
  return problems[Symbol.iterator]().next().value;
}

/** Check a value through every rule and return unknown keys from its schema walk. */
function run(value: unknown): UnknownKey[] {
  if (!isJsonObject(value) || !Object.hasOwn(value, "timeskeleton")) {
    throw new SchemaValidationError("not_a_manifest", [], "not a TimeSkeleton manifest");
  }
  if (value.timeskeleton !== SCHEMA_VERSION) throw new UnsupportedVersionError(value.timeskeleton);

  const finite = first(finiteNumberProblems(value));
  if (finite !== undefined) throw finite;

  const instance = plain(value);
  const found: UnknownKey[] = [];
  if (!marking(instance)) {
    // The closed variant refuses undeclared keys; the document decides validity.
    if (!check(instance)) reject(check.errors ?? [], instance);
    for (const error of marking.errors ?? []) {
      if (error.keyword !== "unevaluatedProperties") continue;
      found.push({
        path: toPath(error.instancePath, instance),
        key: String(error.params.unevaluatedProperty),
      });
    }
  }

  const representation = first(representationProblems(value));
  if (representation !== undefined) throw representation;
  const semantic = first(semanticProblems(value));
  if (semantic !== undefined) throw semantic;

  const unique = new Map(found.map((entry) => [`${jsonPointer(entry.path)} ${entry.key}`, entry]));
  return [...unique.values()].sort(
    (a, b) => comparePaths(a.path, b.path) || compareCodePoints(a.key, b.key),
  );
}

/**
 * Check that `value` is a TimeSkeleton manifest. A checked value is typed as
 * the lossless form `parseJson` returns: its numbers may be `bigint`s and
 * `JsonFloat`s, and a Fraction is a pair of them.
 */
export function validate(value: unknown): asserts value is LosslessTimeSkeleton {
  run(value);
}

/** Return the sorted unknown keys of a valid manifest. */
export function unknownKeys(value: unknown): UnknownKey[] {
  return run(value);
}

function reject(errors: readonly ErrorObject[], instance: unknown): never {
  const error = select(errors);
  if (error === undefined) {
    throw new SchemaValidationError("schema", [], "value is invalid");
  }
  throw new SchemaValidationError(
    "schema",
    toPath(error.instancePath, instance),
    error.message ?? error.keyword,
  );
}

/** Read lossless JSON and validate it as a TimeSkeleton manifest. */
export function parse(text: string): LosslessTimeSkeleton {
  const value = parseJson(text);
  validate(value);
  return value;
}

/** Return every semantic violation in the long-established identity order. */
export function identityProblems(
  value: LosslessTimeSkeleton | JsonObject,
): SchemaValidationError[] {
  return [...semanticProblems(value)];
}
