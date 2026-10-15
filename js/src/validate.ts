/**
 * The TimeSkeleton schema and its validator.
 *
 * The schema is one document, `schema/<version>/timeskeleton.schema.json`,
 * bundled by `scripts/generate.ts`, which also derives the TypeScript types in
 * `generated/`. A value is checked for its version marker, then against the
 * schema, then for the representation of its own-axis values and for the
 * identity rules the schema cannot express. Every object of the schema is
 * open: a key it does not declare is kept and reported by `unknownKeys`,
 * never refused.
 */

import { Ajv2020, type ErrorObject } from "ajv/dist/2020.js";
import type { DataValidationCxt } from "ajv/dist/types/index.js";
import { schema } from "./generated/schema.js";
import type { NumberType, TimeSkeleton, TimeUnit } from "./generated/types.js";
import {
  compareCodePoints,
  compareExact,
  exact,
  exactNumber,
  isJsonObject,
  JsonFloat,
  jsonInteger,
  type Lossless,
  parseJson,
  plain,
  type Rational,
  rational,
  spell,
} from "./manifest.js";

/** The schema version this package reads and writes, the only one it supports. */
export const SCHEMA_VERSION = "0.7.0";

/** One step of a path into a value: an object key or an array index. */
export type PathSegment = string | number;

/** Thrown when a manifest's version marker names a version other than `SCHEMA_VERSION`. */
export class UnsupportedVersionError extends Error {
  /** The value of the manifest's `timeskeleton` member. */
  readonly version: unknown;

  constructor(version: unknown) {
    super(
      `unsupported TimeSkeleton version ${spell(version)}; this package reads ${SCHEMA_VERSION} only`,
    );
    this.name = "UnsupportedVersionError";
    this.version = version;
  }
}

/**
 * Thrown when a value violates the schema or a rule checked after it.
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

/** A key the schema does not declare on the object at `path`. */
export interface UnknownKey {
  readonly path: readonly PathSegment[];
  readonly key: string;
}

/** Render a path as a JSON pointer in URI fragment form (`#` for the root). */
export function jsonPointer(path: readonly PathSegment[]): string {
  const segments = path.map((segment) => String(segment).replace(/~/g, "~0").replace(/\//g, "~1"));
  return `#${segments.map((segment) => `/${segment}`).join("")}`;
}

/** The unknown keys found by the running schema check, in the order found. */
let found: UnknownKey[] = [];

const ajv = new Ajv2020({
  strict: false,
  allErrors: true,
  allowUnionTypes: true,
  discriminator: true,
});
// The schema marks every object's undeclared keys with `x-unknown-key`, a
// keyword every other validator ignores; here it records the key and passes.
ajv.addKeyword({
  keyword: "x-unknown-key",
  schemaType: "boolean",
  errors: false,
  validate(_schema: unknown, _data: unknown, _parent: unknown, cxt?: DataValidationCxt) {
    if (cxt !== undefined) {
      const pointer = cxt.instancePath.slice(0, cxt.instancePath.lastIndexOf("/"));
      found.push({ path: toPath(pointer, cxt.rootData), key: String(cxt.parentDataProperty) });
    }
    return true;
  },
});
const check = ajv.compile(schema);

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

/**
 * Check a value through every rule and return its unknown keys.
 *
 * @throws {SchemaValidationError} on the first violation.
 * @throws {UnsupportedVersionError} for a version marker other than `SCHEMA_VERSION`.
 */
function run(value: unknown): UnknownKey[] {
  if (!isJsonObject(value) || !Object.hasOwn(value, "timeskeleton")) {
    throw new SchemaValidationError([], "not a TimeSkeleton manifest");
  }
  if (value.timeskeleton !== SCHEMA_VERSION) throw new UnsupportedVersionError(value.timeskeleton);
  const instance = plain(value);
  found = [];
  const valid = check(instance);
  const keys = found;
  found = [];
  if (!valid) reject(check.errors ?? [], instance);
  const [problem] = [...representationProblems(value), ...identityProblems(value)];
  if (problem !== undefined) throw problem;
  const unique = new Map(keys.map((entry) => [`${jsonPointer(entry.path)} ${entry.key}`, entry]));
  return [...unique.values()].sort(
    (a, b) => comparePaths(a.path, b.path) || compareCodePoints(a.key, b.key),
  );
}

/**
 * Check that `value` is a TimeSkeleton manifest.
 *
 * The version marker is read first: a value that is no object or has no
 * `timeskeleton` member is refused at the root, and a marker other than
 * `SCHEMA_VERSION` raises `UnsupportedVersionError`. The value is then
 * checked against the schema (a value read by `parse` by the exact values of
 * its numbers), then for the representation of every own-axis value (its
 * timeline's number type selects an int, a float or a fraction pair), then
 * for the identity rules (`identityProblems`). Unknown keys are no violation;
 * `unknownKeys` reports them.
 *
 * @throws {SchemaValidationError} on the first violation found, with the path to the offending value.
 * @throws {UnsupportedVersionError} for a version marker other than `SCHEMA_VERSION`.
 */
export function validate(value: unknown): asserts value is TimeSkeleton {
  run(value);
}

/**
 * Return the keys of a manifest that the schema does not declare.
 *
 * Every object of the schema is open, so an undeclared key, a misspelt
 * optional one included, is kept rather than refused; this lists them, each
 * as the path of its object and the key, sorted by path (indices by number,
 * keys by code point, an object before its descendants) and then by key.
 * Python's `unknown_keys` gives the same list. The value of an unknown key is
 * not looked into.
 *
 * @throws {SchemaValidationError} if the value is no valid manifest (see `validate`).
 * @throws {UnsupportedVersionError} for a version marker other than `SCHEMA_VERSION`.
 */
export function unknownKeys(value: unknown): UnknownKey[] {
  return run(value);
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
 * Read a TimeSkeleton manifest without losing a number or the order of a key
 * (see `parseJson`), and check it (see `validate`).
 *
 * @throws {SyntaxError} if the text is not one JSON value.
 * @throws {SchemaValidationError} on the first violation found.
 * @throws {UnsupportedVersionError} for a version marker other than `SCHEMA_VERSION`.
 */
export function parse(text: string): Lossless<TimeSkeleton> {
  const value = parseJson(text);
  validate(value);
  return value as unknown as Lossless<TimeSkeleton>;
}

// -- the values of a manifest ----------------------------------------------------

type JsonObject = Record<string, unknown>;

/** The objects of an array member, or none where it is absent. */
function entries(owner: unknown, key: string): JsonObject[] {
  const value = isJsonObject(owner) ? owner[key] : undefined;
  return Array.isArray(value) ? (value as JsonObject[]) : [];
}

function text(owner: JsonObject, key: string): string {
  return owner[key] as string;
}

/** A timeline's length, or `null` where it is not known. */
function lengthOf(timeline: JsonObject): unknown {
  return timeline.length ?? null;
}

/** The default number type of each unit. */
const UNIT_NUMBER_TYPES: Readonly<Record<TimeUnit, NumberType>> = {
  number: "float",
  floating_measures: "float",
  whole_note: "fraction",
  quarters: "fraction",
  ticks: "int",
  milliseconds: "float",
  seconds: "float",
  minutes: "float",
  samples: "int",
  frames: "int",
  pixels: "int",
  meters: "float",
  centimeters: "float",
  millimeters: "float",
  inches: "float",
  points: "float",
};

/** The number type of a timeline's axis: its own, or its unit's default. */
export function numberTypeOf(timeline: { unit: TimeUnit; number_type?: NumberType }): NumberType {
  return timeline.number_type ?? UNIT_NUMBER_TYPES[timeline.unit];
}

// -- representation ----------------------------------------------------------------

const ARTICLES: Readonly<Record<NumberType, string>> = {
  int: "an int",
  float: "a float",
  fraction: "a fraction",
};

/** The number type a bare Number is written as. */
function writtenAs(value: unknown): NumberType {
  if (Array.isArray(value)) return "fraction";
  return typeof value === "bigint" || (typeof value === "number" && Number.isInteger(value))
    ? "int"
    : "float";
}

/** Whether a bare Number is represented as the axis's number type selects. */
function represents(value: unknown, numberType: NumberType): boolean {
  if (numberType === "fraction") return Array.isArray(value);
  if (Array.isArray(value)) return false;
  if (numberType === "float")
    return writtenAs(value) !== "int" || rewritten(value, "float") !== null;
  return jsonInteger(value) !== null;
}

/**
 * The value written as `numberType` with exactly the same value, spelled as in
 * a manifest, or `null` when no such representation exists.
 */
function rewritten(value: unknown, numberType: NumberType): string | null {
  const exactValue = exact(value);
  if (numberType === "fraction") {
    return `[${exactValue.numerator}, ${exactValue.denominator}]`;
  }
  if (numberType === "int") {
    return exactValue.denominator === 1n ? String(exactValue.numerator) : null;
  }
  const double = Number(exactValue.numerator) / Number(exactValue.denominator);
  if (!Number.isFinite(double)) return null;
  const back = exactNumber(double) as Rational;
  if (!equal(back, exactValue)) return null;
  return spell(Number.isInteger(double) ? new JsonFloat(double) : double);
}

/**
 * The problem of an own-axis value that is not represented as its axis's
 * number type selects, or nothing. The message names the key, the value, the
 * id of the object holding it, the representation found and the one the axis
 * selects, and ends with the value rewritten where an exact rewriting exists.
 */
function* representationProblem(
  key: string,
  owner: JsonObject,
  path: readonly PathSegment[],
  numberType: NumberType,
): Generator<SchemaValidationError> {
  const value = owner[key];
  if (value === undefined || value === null || represents(value, numberType)) return;
  const fix = rewritten(value, numberType) ?? ARTICLES[numberType];
  yield new SchemaValidationError(
    [...path, key],
    `${key} ${spell(value)} of '${text(owner, "id")}' is ${ARTICLES[writtenAs(value)]} on ${ARTICLES[numberType]} axis: write ${fix}`,
  );
}

/**
 * The representation problems of a timeline tree: its offset (on its
 * parent's axis, a root's on its own), its length, its regions' starts and
 * ends, its breaks', jumps' and markers' coordinates, then its children's
 * trees in array order.
 */
function* timelineRepresentation(
  timeline: JsonObject,
  path: readonly PathSegment[],
  offsetType: NumberType | null,
): Generator<SchemaValidationError> {
  const own = numberTypeOf(timeline as { unit: TimeUnit; number_type?: NumberType });
  yield* representationProblem("offset", timeline, path, offsetType ?? own);
  yield* representationProblem("length", timeline, path, own);
  for (const [index, region] of entries(timeline, "regions").entries()) {
    for (const key of ["start", "end"]) {
      yield* representationProblem(key, region, [...path, "regions", index], own);
    }
  }
  const flow = isJsonObject(timeline.flow_control) ? timeline.flow_control : {};
  const members = [
    ["breaks", ["coordinate"]],
    ["jumps", ["from_coordinate", "to_coordinate"]],
    ["markers", ["coordinate"]],
  ] as const;
  for (const [member, keys] of members) {
    for (const [index, entry] of entries(flow, member).entries()) {
      for (const key of keys) {
        yield* representationProblem(key, entry, [...path, "flow_control", member, index], own);
      }
    }
  }
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* timelineRepresentation(child, [...path, "children", index], own);
  }
}

/** The representation problems of every root of a manifest, in array order. */
function* representationProblems(manifest: JsonObject): Generator<SchemaValidationError> {
  for (const [index, root] of entries(manifest, "timelines").entries()) {
    yield* timelineRepresentation(root, ["timelines", index], null);
  }
}

// -- identity ----------------------------------------------------------------------

/**
 * Every id of a timeline tree with its path, in identity order: a timeline's
 * own id, then the ids of its conversion maps, regions, breaks, jumps and
 * markers in array order, then its children's trees in array order.
 */
function* elementIds(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<[string, PathSegment[]]> {
  yield [text(timeline, "id"), [...path, "id"]];
  for (const member of ["conversion_maps", "regions"]) {
    for (const [index, entry] of entries(timeline, member).entries()) {
      yield [text(entry, "id"), [...path, member, index, "id"]];
    }
  }
  for (const member of ["breaks", "jumps", "markers"]) {
    for (const [index, entry] of entries(timeline.flow_control, member).entries()) {
      yield [text(entry, "id"), [...path, "flow_control", member, index, "id"]];
    }
  }
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* elementIds(child, [...path, "children", index]);
  }
}

/** The id of every timeline of a tree with its path, in identity order. */
function* timelineIds(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<[string, PathSegment[]]> {
  yield [text(timeline, "id"), [...path, "id"]];
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* timelineIds(child, [...path, "children", index]);
  }
}

/** A problem for each jump whose target names no marker of its timeline. */
function* danglingTargets(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const flow = timeline.flow_control;
  const markers = new Set(entries(flow, "markers").map((marker) => marker.id));
  for (const [index, jump] of entries(flow, "jumps").entries()) {
    const target = jump.target ?? null;
    if (target !== null && !markers.has(target)) {
      yield new SchemaValidationError(
        [...path, "flow_control", "jumps", index, "target"],
        `${JSON.stringify(target)} names no marker of this timeline`,
      );
    }
  }
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* danglingTargets(child, [...path, "children", index]);
  }
}

function duplicate(
  id: string,
  path: readonly PathSegment[],
  first: readonly PathSegment[],
): SchemaValidationError {
  return new SchemaValidationError(
    path,
    `duplicate id ${JSON.stringify(id)}, first at ${jsonPointer(first)}`,
  );
}

/** The indices of children in offset order, ties by id in code-point order. */
function offsetOrder(children: readonly JsonObject[]): number[] {
  return [...children.keys()].sort(
    (a, b) =>
      compareExact(children[a]?.offset, children[b]?.offset) ||
      compareCodePoints(
        text(children[a] as JsonObject, "id"),
        text(children[b] as JsonObject, "id"),
      ),
  );
}

/**
 * Where each child of a timeline ends on its axis, `null` where unknown: a
 * child of the timeline's unit ends at its offset plus its known length; a
 * segment of unknown length ends where its successor in offset order starts.
 */
function childEnds(timeline: JsonObject): (Rational | null)[] {
  const children = entries(timeline, "children");
  const ends = children.map((child) => {
    const length = lengthOf(child);
    return length !== null && child.unit === timeline.unit
      ? add(exact(child.offset), exact(length))
      : null;
  });
  if (timeline.is_segment_line === true) {
    const order = offsetOrder(children);
    for (const [position, index] of order.entries()) {
      const successor = order[position + 1];
      if (successor !== undefined && lengthOf(children[index] as JsonObject) === null) {
        ends[index] = exact(children[successor]?.offset);
      }
    }
  }
  return ends;
}

/**
 * A problem for each child that does not sit on its parent's axis, child by
 * child in array order, each followed by its own children: a unit other than
 * its parent's, at its `unit`; a negative offset, at its `offset`; where the
 * parent's length is known, an offset beyond it, at the `offset`, or else an
 * end beyond it where the child's end is known (see `childEnds`), at the
 * child's `length`. The end is spelled as the parent's number type writes
 * it, as a fraction pair where that type cannot write it exactly. Values
 * compare exactly. Python's `_child_problems` gives the same problems.
 */
function* childProblems(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const length = lengthOf(timeline);
  const ends = childEnds(timeline);
  for (const [index, child] of entries(timeline, "children").entries()) {
    const at = [...path, "children", index];
    const offset = exact(child.offset);
    const id = text(child, "id");
    const parent = `its parent '${text(timeline, "id")}'`;
    if (child.unit !== timeline.unit) {
      yield new SchemaValidationError(
        [...at, "unit"],
        `child '${id}' has unit '${text(child, "unit")}', ${parent} has '${text(timeline, "unit")}'`,
      );
    }
    if (offset.numerator < 0n) {
      yield new SchemaValidationError(
        [...at, "offset"],
        `offset ${spell(child.offset)} of '${id}' is negative`,
      );
    }
    const end = ends[index] ?? null;
    if (length !== null && exceeds(offset, exact(length))) {
      yield new SchemaValidationError(
        [...at, "offset"],
        `offset ${spell(child.offset)} of '${id}' is beyond the length ${spell(length)} of ${parent}`,
      );
    } else if (length !== null && end !== null && exceeds(end, exact(length))) {
      const pair = [end.numerator, end.denominator];
      const spelled =
        rewritten(pair, numberTypeOf(timeline as { unit: TimeUnit; number_type?: NumberType })) ??
        spell(pair);
      yield new SchemaValidationError(
        [...at, "length"],
        `child '${id}' ends at ${spelled}, beyond the length ${spell(length)} of ${parent}`,
      );
    }
    yield* childProblems(child, at);
  }
}

/**
 * The identity problems of one root, its own scope: duplicates, then targets,
 * then children off their parent's axis or beyond its length, then segment
 * lines.
 */
function rootProblems(root: JsonObject, path: readonly PathSegment[]): SchemaValidationError[] {
  const problems: SchemaValidationError[] = [];
  const first = new Map<string, PathSegment[]>();
  for (const [id, at] of elementIds(root, path)) {
    const earlier = first.get(id);
    if (earlier === undefined) first.set(id, at);
    else problems.push(duplicate(id, at, earlier));
  }
  problems.push(...danglingTargets(root, path));
  problems.push(...childProblems(root, path));
  problems.push(...segmentProblems(root, path));
  return problems;
}

function add(left: Rational, right: Rational): Rational {
  return rational(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator,
  );
}

function equal(left: Rational, right: Rational): boolean {
  return left.numerator === right.numerator && left.denominator === right.denominator;
}

/** Whether `left` is greater than `right`; denominators are positive. */
function exceeds(left: Rational, right: Rational): boolean {
  return left.numerator * right.denominator > right.numerator * left.denominator;
}

/**
 * The problems of every segment line of a timeline tree. A timeline with
 * `is_segment_line` true holds only its segments, visited in offset order
 * (ties by id in code-point order): a segment whose `is_segment_line`
 * differs from the first segment's, at that member (at the segment where it
 * is absent); a segment that does not start where the one before it ends
 * (the first at 0), at its `offset`; then, if the last segment does not end
 * at the segment line's length, one problem at the `length`. A
 * segment of unknown length ends where its successor starts, so the
 * successor's offset is not checked, and the end is not checked where the
 * last segment's length or the segment line's is not known. Values compare
 * exactly; the tree is visited in identity order. Python's
 * `_segment_problems` gives the same problems.
 */
function* segmentProblems(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const children = entries(timeline, "children");
  if (timeline.is_segment_line === true) {
    const order = offsetOrder(children);
    const id = JSON.stringify(timeline.id);
    let end: Rational | null = rational(0n, 1n);
    let flag: boolean | undefined;
    let firstId = "";
    for (const [position, index] of order.entries()) {
      const segment = children[index] as JsonObject;
      const at = [...path, "children", index];
      const name = JSON.stringify(segment.id);
      const segmentFlag = segment.is_segment_line === true;
      if (position === 0) {
        flag = segmentFlag;
        firstId = JSON.stringify(segment.id);
      } else if (segmentFlag !== flag) {
        yield new SchemaValidationError(
          Object.hasOwn(segment, "is_segment_line") ? [...at, "is_segment_line"] : at,
          `segment ${name} of segment line ${id} differs from segment ${firstId} in is_segment_line`,
        );
      }
      const offset = exact(segment.offset);
      if (end !== null && !equal(offset, end)) {
        yield new SchemaValidationError(
          [...at, "offset"],
          `segment ${name} of segment line ${id} does not ${position === 0 ? "start at 0" : "start where the one before it ends"}`,
        );
      }
      const length = lengthOf(segment);
      end = length === null ? null : add(offset, exact(length));
    }
    const length = lengthOf(timeline);
    if (end !== null && length !== null && !equal(end, exact(length))) {
      yield new SchemaValidationError(
        [...path, "length"],
        `the segments of segment line ${id} do not end at its length`,
      );
    }
  }
  for (const [index, child] of children.entries()) {
    yield* segmentProblems(child, [...path, "children", index]);
  }
}

/** The part words, which follow an element's address as its parts and so are no id. */
const PART_WORDS: ReadonlySet<string> = new Set(["start", "end", "name", "label", "card"]);

function reserved(id: string, path: readonly PathSegment[]): SchemaValidationError {
  return new SchemaValidationError(
    path,
    `id ${JSON.stringify(id)} is reserved for the parts of an address`,
  );
}

/**
 * The problems of a display order that is no permutation of a group's
 * members: each entry that is not a member at the entry, then each member
 * missing from the order at the order.
 */
function* orderProblems(
  group: JsonObject,
  order: readonly string[],
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const members = group.members as string[];
  const memberSet = new Set(members);
  const listed = new Set(order);
  const id = JSON.stringify(group.id);
  for (const [index, entry] of order.entries()) {
    if (!memberSet.has(entry)) {
      yield new SchemaValidationError(
        [...path, index],
        `${JSON.stringify(entry)} is not a member of group ${id}`,
      );
    }
  }
  for (const member of members) {
    if (!listed.has(member)) {
      yield new SchemaValidationError(
        path,
        `member ${JSON.stringify(member)} of group ${id} is missing`,
      );
    }
  }
}

/**
 * The ancestor ids of every timeline of the roots, nearest first; where a
 * timeline id repeats (a problem reported on its own), its first occurrence
 * counts.
 */
function ancestorsOf(roots: readonly JsonObject[]): Map<string, readonly string[]> {
  const ancestors = new Map<string, readonly string[]>();
  const visit = (timeline: JsonObject, above: readonly string[]): void => {
    const id = text(timeline, "id");
    if (!ancestors.has(id)) ancestors.set(id, above);
    for (const child of entries(timeline, "children")) visit(child, [id, ...above]);
  };
  for (const root of roots) visit(root, []);
  return ancestors;
}

/**
 * The problems of a group's members, member by member: a member naming no
 * timeline of the manifest (not checked further); a member named by an
 * earlier group; then a member nested with an earlier member of the same
 * group (inside it or containing it), naming the first such earlier member.
 */
function* memberProblems(
  group: JsonObject,
  path: readonly PathSegment[],
  ancestors: Map<string, readonly string[]>,
  firstMember: Map<string, PathSegment[]>,
): Generator<SchemaValidationError> {
  const checked: string[] = [];
  for (const [index, member] of (group.members as string[]).entries()) {
    const at = [...path, index];
    const above = ancestors.get(member);
    if (above === undefined) {
      yield new SchemaValidationError(
        at,
        `${JSON.stringify(member)} names no timeline of this manifest`,
      );
      continue;
    }
    const earlier = firstMember.get(member);
    if (earlier !== undefined) {
      yield new SchemaValidationError(
        at,
        `duplicate member ${JSON.stringify(member)}, first at ${jsonPointer(earlier)}`,
      );
    } else firstMember.set(member, at);
    for (const other of checked) {
      const relation = above.includes(other)
        ? "lies inside"
        : (ancestors.get(other) ?? []).includes(member)
          ? "contains"
          : null;
      if (relation !== null) {
        yield new SchemaValidationError(
          at,
          `member ${JSON.stringify(member)} ${relation} member ${JSON.stringify(other)} of the same group`,
        );
        break;
      }
    }
    checked.push(member);
  }
}

/**
 * The violations of the identity rules in a schema-valid manifest, in this
 * order, one problem per finding:
 *
 * 1. root by root, in array order, each root's tree is its own scope: every
 *    id of a timeline, conversion map, region, break, jump and marker of the
 *    tree is unique within it, each repeated id one problem at its later
 *    occurrence in identity order (a timeline, then its maps, regions,
 *    breaks, jumps and markers, then its children in array order),
 *    `duplicate id "<id>", first at <pointer>`; then each jump whose
 *    non-null `target` names no marker of its own timeline, at the target;
 *    then each child whose `unit` is not its parent's, `child '<id>' has
 *    unit '<u>', its parent '<pid>' has '<pu>'`, whose `offset` is negative,
 *    `offset <v> of '<id>' is negative`, whose `offset` is beyond its
 *    parent's known length, `offset <v> of '<id>' is beyond the length <pl>
 *    of its parent '<pid>'`, or which ends beyond it, `child '<id>' ends at
 *    <e>, beyond the length <pl> of its parent '<pid>'` (see
 *    `childProblems`); then the segment lines (see `segmentProblems`);
 * 2. every id that is a part word (`start`, `end`, `name`, `label`, `card`),
 *    which follow an address as its parts: the manifest's `id`, then root by
 *    root every id of the tree in identity order, then each group's id;
 * 3. a timeline id (of a root or a descendant) repeating a timeline id of an
 *    earlier root, at the later occurrence;
 * 4. a group id equal to a timeline id (first at the timeline) or to the id
 *    of an earlier group (first at that group), at the group's `id`;
 * 5. the manifest's `id` equal to a timeline id or a group id, at `id`, first
 *    at the timeline, else at the first such group;
 * 6. group by group, member by member: a member naming no timeline of the
 *    manifest; a member already named by an earlier group, `duplicate
 *    member`; a member nested with an earlier member of the same group
 *    (inside it or containing it), each at the member;
 * 7. each key of `graphical.order` in code-point order: a key naming no
 *    group, at the key; each entry that is not a member of the group, at the
 *    entry; then each member missing from the order, at the order.
 *
 * A key with a default may be absent; its default applies. Python's
 * `identity_problems` gives the same problems at the same paths, quoting ids
 * as `repr` does where this quotes them as JSON; the four child messages are
 * the same text in both.
 */
export function identityProblems(
  value: TimeSkeleton | Lossless<TimeSkeleton> | JsonObject,
): SchemaValidationError[] {
  const manifest = value as JsonObject;
  const problems: SchemaValidationError[] = [];
  const roots = entries(manifest, "timelines");
  const groups = entries(manifest, "groups");
  for (const [index, root] of roots.entries()) {
    problems.push(...rootProblems(root, ["timelines", index]));
  }
  const manifestId = typeof manifest.id === "string" ? manifest.id : null;
  if (manifestId !== null && PART_WORDS.has(manifestId))
    problems.push(reserved(manifestId, ["id"]));
  for (const [index, root] of roots.entries()) {
    for (const [id, at] of elementIds(root, ["timelines", index])) {
      if (PART_WORDS.has(id)) problems.push(reserved(id, at));
    }
  }
  for (const [index, group] of groups.entries()) {
    const id = text(group, "id");
    if (PART_WORDS.has(id)) problems.push(reserved(id, ["groups", index, "id"]));
  }
  const timelines = new Map<string, PathSegment[]>();
  for (const [index, root] of roots.entries()) {
    const seen = new Map<string, PathSegment[]>();
    for (const [id, path] of timelineIds(root, ["timelines", index])) {
      if (seen.has(id)) continue;
      seen.set(id, path);
      const earlier = timelines.get(id);
      if (earlier !== undefined) problems.push(duplicate(id, path, earlier));
    }
    for (const [id, path] of seen) if (!timelines.has(id)) timelines.set(id, path);
  }
  const firstGroup = new Map<string, number>();
  for (const [index, group] of groups.entries()) {
    const id = text(group, "id");
    const path = ["groups", index, "id"];
    const timeline = timelines.get(id);
    const earlier = firstGroup.get(id);
    if (timeline !== undefined) problems.push(duplicate(id, path, timeline));
    else if (earlier !== undefined) problems.push(duplicate(id, path, ["groups", earlier, "id"]));
    if (earlier === undefined) firstGroup.set(id, index);
  }
  if (manifestId !== null) {
    const groupIndex = firstGroup.get(manifestId);
    const first =
      timelines.get(manifestId) ??
      (groupIndex === undefined ? undefined : ["groups", groupIndex, "id"]);
    if (first !== undefined) problems.push(duplicate(manifestId, ["id"], first));
  }
  const ancestors = ancestorsOf(roots);
  const firstMember = new Map<string, PathSegment[]>();
  for (const [index, group] of groups.entries()) {
    problems.push(...memberProblems(group, ["groups", index, "members"], ancestors, firstMember));
  }
  const graphical = isJsonObject(manifest.graphical) ? manifest.graphical : {};
  const orders = isJsonObject(graphical.order) ? (graphical.order as Record<string, string[]>) : {};
  for (const key of Object.keys(orders).sort(compareCodePoints)) {
    const path = ["graphical", "order", key];
    const index = firstGroup.get(key);
    if (index === undefined) {
      problems.push(
        new SchemaValidationError(path, `${JSON.stringify(key)} names no group of this manifest`),
      );
    } else {
      problems.push(...orderProblems(groups[index] as JsonObject, orders[key] ?? [], path));
    }
  }
  return problems;
}
