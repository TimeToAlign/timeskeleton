/**
 * The TimeSkeleton schemas and their validators.
 *
 * Versions 0.5.0 and 0.6.0 have one schema document each, for the one file
 * kind they know, the timeline file. From 0.7.0 on a version has four
 * documents: `core` (the shared definitions), `timeline`, `group` and
 * `bundle`, one per file kind, referring to each other by relative `$ref`. The
 * schema objects are bundled from `schema/` at the repository root by
 * `scripts/generate.ts`, which also derives the TypeScript types in
 * `generated/`.
 */

import { Ajv2020, type ErrorObject } from "ajv/dist/2020.js";
import { schemaDocuments } from "./generated/schema.js";
import type {
  TimelineManifest,
  TimeSkeletonBundleFile,
  TimeSkeletonGroupFile,
  TimeSkeletonManifest,
} from "./generated/types.js";
import {
  compareCodePoints,
  compareExact,
  exact,
  type Lossless,
  parseJson,
  plain,
  type Rational,
  rational,
} from "./manifest.js";

/** The latest schema version bundled by this package. */
export const SCHEMA_VERSION = "0.7.0";

/** Every bundled schema version, oldest first. */
export const SUPPORTED_VERSIONS: readonly string[] = ["0.5.0", "0.6.0", "0.7.0"];

/**
 * The file kinds, each named by the top-level member that holds its content.
 * A file of version 0.7.0 or later holds exactly one of these members beside
 * `meta`; versions 0.5.0 and 0.6.0 know the timeline file only.
 */
export const FILE_KINDS = ["timeline", "group", "bundle"] as const;

/** A file kind. */
export type FileKind = (typeof FILE_KINDS)[number];

/** A TimeSkeleton file of any kind. */
export type TimeSkeletonFile =
  | TimeSkeletonManifest
  | TimeSkeletonGroupFile
  | TimeSkeletonBundleFile;

const DOCUMENTS: Readonly<Record<string, Readonly<Record<string, { $id: string }>>>> =
  schemaDocuments;

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

/** The members of `FILE_KINDS` a value holds, in that order. */
function presentKinds(value: unknown): FileKind[] {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return [];
  return FILE_KINDS.filter((kind) => Object.hasOwn(value, kind));
}

/**
 * Return the kind of a file: the one member of `FILE_KINDS` it holds, or
 * `null` for a value that holds none or several of them, or is no object.
 */
export function fileKind(value: unknown): FileKind | null {
  const present = presentKinds(value);
  return present.length === 1 ? (present[0] as FileKind) : null;
}

const ajv = new Ajv2020({
  strict: false,
  allErrors: true,
  allowUnionTypes: true,
  discriminator: true,
});
const registered = new Set<string>();
const validators = new Map<string, ReturnType<typeof ajv.compile>>();

/** Add every schema document of a version to Ajv, once. */
function register(version: string): Readonly<Record<string, { $id: string }>> {
  const documents = DOCUMENTS[version];
  if (documents === undefined) throw new UnsupportedVersionError(version);
  if (!registered.has(version)) {
    for (const schema of Object.values(documents)) ajv.addSchema(schema);
    registered.add(version);
  }
  return documents;
}

/** The validator of one document, with every document of its version registered. */
function validatorFor(version: string, document: string): ReturnType<typeof ajv.compile> {
  const key = `${version}/${document}`;
  let validator = validators.get(key);
  if (validator === undefined) {
    const target = register(version)[document];
    if (target === undefined) throw new UnsupportedVersionError(version);
    validator = ajv.getSchema(target.$id) as ReturnType<typeof ajv.compile>;
    validators.set(key, validator);
  }
  return validator;
}

/** The validator of `meta` alone, as the latest version states it. */
function declarationValidator(): ReturnType<typeof ajv.compile> {
  let validator = validators.get("declaration");
  if (validator === undefined) {
    const core = register(SCHEMA_VERSION).core as { $id: string };
    validator = ajv.compile({
      type: "object",
      required: ["meta"],
      properties: { meta: { $ref: `${core.$id}#/$defs/Meta` } },
    });
    validators.set("declaration", validator);
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

/** The problem of a value holding none or several file kinds. */
function kindProblem(value: unknown): SchemaValidationError {
  const present = presentKinds(value);
  const found =
    present.length === 0 ? "none" : present.map((kind) => JSON.stringify(kind)).join(", ");
  return new SchemaValidationError(
    [],
    `exactly one of "timeline", "group" or "bundle" is required; found ${found}`,
  );
}

/**
 * Check `value` against the schema of the version and kind it declares.
 *
 * A value whose `meta.schema_version` is one of `SUPPORTED_VERSIONS` is
 * checked against that version's schema; from 0.7.0 on, against the document
 * of its kind (`fileKind`), and a value holding none or several of
 * `timeline`, `group` and `bundle` is rejected at the root. Any other value is
 * refused for its declaration alone: its `meta` is checked against the latest
 * version's, which rejects it at `meta.schema_version`, or at the root when it
 * has no `meta`. A value read
 * by `parse` is checked by the exact values of its numbers. A value the schema
 * accepts is then checked for the identity rules the schema cannot express
 * (`identityProblems`).
 *
 * @throws {SchemaValidationError} on the first violation found, with the path to the offending value.
 */
export function validate(value: unknown): asserts value is TimeSkeletonFile {
  const version = declaredVersion(value);
  const kind = fileKind(value);
  let validator: ReturnType<typeof ajv.compile>;
  if (version === null || !SUPPORTED_VERSIONS.includes(version)) {
    validator = declarationValidator();
  } else if (Object.keys(DOCUMENTS[version] ?? {}).length === 1) {
    validator = validatorFor(version, "timeline");
  } else if (kind !== null) validator = validatorFor(version, kind);
  else throw kindProblem(value);
  const instance = plain(value);
  if (!validator(instance)) reject(validator.errors ?? [], instance);
  const [problem] = identityProblems(value as TimeSkeletonFile);
  if (problem !== undefined) throw problem;
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
 * Read a TimeSkeleton file without losing a number or the order of a key
 * (see `parseJson`), and check it against the schema version and kind it
 * declares.
 *
 * @throws {SyntaxError} if the text is not one JSON value.
 * @throws {SchemaValidationError} on the first violation found.
 */
export function parse(text: string): Lossless<TimeSkeletonFile> {
  const value = parseJson(text);
  validate(value);
  return value as unknown as Lossless<TimeSkeletonFile>;
}

/** The keys of a timeline's children in code-point order. */
function childKeys(timeline: TimelineManifest): string[] {
  return Object.keys(timeline.children).sort(compareCodePoints);
}

/**
 * Every id of a timeline tree with its path, in identity order: a timeline's
 * own id, then the ids of its conversion maps, regions, breaks, jumps and
 * markers in array order, then its children's trees in code-point order of
 * their keys.
 */
function* elementIds(
  timeline: TimelineManifest,
  path: readonly PathSegment[],
): Generator<[string, PathSegment[]]> {
  yield [timeline.id, [...path, "id"]];
  for (const member of ["conversion_maps", "regions"] as const) {
    for (const [index, entry] of timeline[member].entries()) {
      yield [entry.id, [...path, member, index, "id"]];
    }
  }
  const flow = timeline.flow_control;
  for (const member of ["breaks", "jumps", "markers"] as const) {
    for (const [index, entry] of flow[member].entries()) {
      yield [entry.id, [...path, "flow_control", member, index, "id"]];
    }
  }
  for (const key of childKeys(timeline)) {
    const child = timeline.children[key] as { timeline: TimelineManifest };
    yield* elementIds(child.timeline, [...path, "children", key, "timeline"]);
  }
}

/** A problem for each jump whose target names no marker of its timeline. */
function* danglingTargets(
  timeline: TimelineManifest,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const flow = timeline.flow_control;
  const markers = new Set(flow.markers.map((marker) => marker.id));
  for (const [index, jump] of flow.jumps.entries()) {
    if (jump.target !== null && !markers.has(jump.target)) {
      yield new SchemaValidationError(
        [...path, "flow_control", "jumps", index, "target"],
        `${JSON.stringify(jump.target)} names no marker of this timeline`,
      );
    }
  }
  for (const key of childKeys(timeline)) {
    const child = timeline.children[key] as { timeline: TimelineManifest };
    yield* danglingTargets(child.timeline, [...path, "children", key, "timeline"]);
  }
}

/** The identity problems of one timeline manifest, its own id scope. */
function timelineProblems(
  timeline: TimelineManifest,
  path: readonly PathSegment[],
): SchemaValidationError[] {
  const problems: SchemaValidationError[] = [];
  const first = new Map<string, PathSegment[]>();
  for (const [id, at] of elementIds(timeline, path)) {
    const earlier = first.get(id);
    if (earlier === undefined) first.set(id, at);
    else problems.push(duplicate(id, at, earlier));
  }
  problems.push(...danglingTargets(timeline, path));
  problems.push(...segmentProblems(timeline, path));
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

/**
 * The problems of every segment line of a timeline tree. A timeline with
 * `is_segment_line` true holds only its segments, visited in offset order
 * (ties by key in code-point order): a segment of another class than the
 * segment line, at its `class`; a segment whose `is_segment_line` differs
 * from the first segment's, at that member; a segment that does not start
 * where the one before it ends (the first at 0), at its `offset`; then, if the
 * last segment does not end at the segment line's length, one problem at the
 * `length`. Coordinates compare by exact value; the tree is visited in
 * identity order. Python's `_segment_problems` gives the same problems.
 */
function* segmentProblems(
  timeline: TimelineManifest,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  if (timeline.is_segment_line === true) {
    const children = timeline.children as Record<
      string,
      { offset: unknown; timeline: TimelineManifest }
    >;
    const keys = Object.keys(children).sort(
      (a, b) => compareExact(children[a]?.offset, children[b]?.offset) || compareCodePoints(a, b),
    );
    const id = JSON.stringify(timeline.id);
    let end = rational(0n, 1n);
    let flag: boolean | undefined;
    for (const [index, key] of keys.entries()) {
      const child = children[key] as { offset: unknown; timeline: TimelineManifest };
      const segment = child.timeline;
      const at = [...path, "children", key];
      if (segment.class !== timeline.class) {
        yield new SchemaValidationError(
          [...at, "timeline", "class"],
          `segment ${JSON.stringify(key)} of segment line ${id} is no ${timeline.class}`,
        );
      }
      if (index === 0) flag = segment.is_segment_line;
      else if (segment.is_segment_line !== flag) {
        yield new SchemaValidationError(
          [...at, "timeline", "is_segment_line"],
          `segment ${JSON.stringify(key)} of segment line ${id} differs from segment ${JSON.stringify(keys[0])} in is_segment_line`,
        );
      }
      const offset = exact(child.offset);
      if (!equal(offset, end)) {
        yield new SchemaValidationError(
          [...at, "offset"],
          `segment ${JSON.stringify(key)} of segment line ${id} does not ${index === 0 ? "start at 0" : "start where the one before it ends"}`,
        );
      }
      end = add(offset, exact(segment.length));
    }
    if (!equal(end, exact(timeline.length))) {
      yield new SchemaValidationError(
        [...path, "length"],
        `the segments of segment line ${id} do not end at its length`,
      );
    }
  }
  for (const key of childKeys(timeline)) {
    const child = timeline.children[key] as { timeline: TimelineManifest };
    yield* segmentProblems(child.timeline, [...path, "children", key, "timeline"]);
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

/** The id of every timeline of a tree with its path, in identity order. */
function* timelineIds(
  timeline: TimelineManifest,
  path: readonly PathSegment[],
): Generator<[string, PathSegment[]]> {
  yield [timeline.id, [...path, "id"]];
  for (const key of childKeys(timeline)) {
    const child = timeline.children[key] as { timeline: TimelineManifest };
    yield* timelineIds(child.timeline, [...path, "children", key, "timeline"]);
  }
}

/**
 * The part words, which no element other than a timeline may carry as its id
 * in a group or bundle file.
 */
const PART_WORDS: ReadonlySet<string> = new Set(["start", "end", "name", "label", "card"]);

/**
 * A problem for each element id of a tree that is a part word. Timeline ids
 * are exempt; the other elements are visited in identity order.
 */
function* partWordProblems(
  timeline: TimelineManifest,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const timelines = new Set([...timelineIds(timeline, path)].map(([, at]) => jsonPointer(at)));
  for (const [id, at] of elementIds(timeline, path)) {
    if (PART_WORDS.has(id) && !timelines.has(jsonPointer(at))) {
      yield new SchemaValidationError(
        at,
        `id ${JSON.stringify(id)} is reserved in a group or bundle file`,
      );
    }
  }
}

/**
 * The first path of every timeline id of a file's roots. Each root is its own
 * id scope under the rules of a timeline file. Then, root by root, each
 * element id other than a timeline id that is a part word is one problem at
 * that id. A timeline id that repeats a timeline id of an earlier root is one
 * problem at its later occurrence (a repetition within one root is that
 * root's problem).
 */
function fileTimelines(
  roots: readonly TimelineManifest[],
  problems: SchemaValidationError[],
): Map<string, PathSegment[]> {
  const first = new Map<string, PathSegment[]>();
  for (const [index, root] of roots.entries()) {
    problems.push(...timelineProblems(root, ["timelines", index]));
  }
  for (const [index, root] of roots.entries()) {
    problems.push(...partWordProblems(root, ["timelines", index]));
  }
  for (const [index, root] of roots.entries()) {
    const seen = new Map<string, PathSegment[]>();
    for (const [id, path] of timelineIds(root, ["timelines", index])) {
      if (seen.has(id)) continue;
      seen.set(id, path);
      const earlier = first.get(id);
      if (earlier !== undefined) problems.push(duplicate(id, path, earlier));
    }
    for (const [id, path] of seen) if (!first.has(id)) first.set(id, path);
  }
  return first;
}

interface GroupValue {
  readonly id: string;
  readonly members: readonly string[];
}

/**
 * The problems of a display order that is no permutation of a group's
 * members: each entry that is not a member at the entry, then each member
 * missing from the order at the order.
 */
function* orderProblems(
  group: GroupValue,
  order: readonly string[],
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const members = new Set(group.members);
  const listed = new Set(order);
  for (const [index, entry] of order.entries()) {
    if (!members.has(entry)) {
      yield new SchemaValidationError(
        [...path, index],
        `${JSON.stringify(entry)} is not a member of group ${JSON.stringify(group.id)}`,
      );
    }
  }
  for (const member of group.members) {
    if (!listed.has(member)) {
      yield new SchemaValidationError(
        path,
        `member ${JSON.stringify(member)} of group ${JSON.stringify(group.id)} is missing`,
      );
    }
  }
}

function dangling(member: string, path: readonly PathSegment[]): SchemaValidationError {
  return new SchemaValidationError(
    path,
    `${JSON.stringify(member)} names no timeline of this file`,
  );
}

/**
 * The ancestor ids of every timeline of the roots, nearest first; where a
 * timeline id repeats (a problem reported on its own), its first occurrence
 * counts.
 */
function ancestorsOf(roots: readonly TimelineManifest[]): Map<string, readonly string[]> {
  const found = new Map<string, readonly string[]>();
  const visit = (timeline: TimelineManifest, above: readonly string[]): void => {
    if (!found.has(timeline.id)) found.set(timeline.id, above);
    for (const key of childKeys(timeline)) {
      const child = timeline.children[key] as { timeline: TimelineManifest };
      visit(child.timeline, [timeline.id, ...above]);
    }
  };
  for (const root of roots) visit(root, []);
  return found;
}

/**
 * The problems of a group's members, member by member: a member naming no
 * timeline of the file (not checked further); in a bundle (`firstMember`
 * given) a member named by an earlier group; then a member nested with an
 * earlier member of the same group (inside it or containing it), naming the
 * first such earlier member.
 */
function* memberProblems(
  group: GroupValue,
  path: readonly PathSegment[],
  ancestors: Map<string, readonly string[]>,
  firstMember: Map<string, PathSegment[]> | null,
): Generator<SchemaValidationError> {
  const checked: string[] = [];
  for (const [index, member] of group.members.entries()) {
    const at = [...path, index];
    const above = ancestors.get(member);
    if (above === undefined) {
      yield dangling(member, at);
      continue;
    }
    if (firstMember !== null) {
      const earlier = firstMember.get(member);
      if (earlier !== undefined) {
        yield new SchemaValidationError(
          at,
          `duplicate member ${JSON.stringify(member)}, first at ${jsonPointer(earlier)}`,
        );
      } else firstMember.set(member, at);
    }
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

function groupProblems(file: TimeSkeletonGroupFile): SchemaValidationError[] {
  const problems: SchemaValidationError[] = [];
  const roots = file.timelines;
  const timelines = fileTimelines(roots, problems);
  const group = file.group;
  const earlier = timelines.get(group.id);
  if (earlier !== undefined) problems.push(duplicate(group.id, ["group", "id"], earlier));
  problems.push(...memberProblems(group, ["group", "members"], ancestorsOf(roots), null));
  const members = new Set(group.members);
  for (const [index, root] of roots.entries()) {
    if (![...timelineIds(root, [])].some(([id]) => members.has(id))) {
      problems.push(
        new SchemaValidationError(
          ["timelines", index],
          `timeline ${JSON.stringify(root.id)} contains no member of the group`,
        ),
      );
    }
  }
  const order = file.graphical?.order;
  if (order !== undefined) problems.push(...orderProblems(group, order, ["graphical", "order"]));
  return problems;
}

function bundleProblems(file: TimeSkeletonBundleFile): SchemaValidationError[] {
  const problems: SchemaValidationError[] = [];
  const timelines = fileTimelines(file.timelines, problems);
  const groups = file.bundle.groups;
  const firstGroup = new Map<string, number>();
  for (const [index, group] of groups.entries()) {
    const path = ["bundle", "groups", index, "id"];
    const timeline = timelines.get(group.id);
    const earlier = firstGroup.get(group.id);
    if (timeline !== undefined) problems.push(duplicate(group.id, path, timeline));
    else if (earlier !== undefined) {
      problems.push(duplicate(group.id, path, ["bundle", "groups", earlier, "id"]));
    }
    if (earlier === undefined) firstGroup.set(group.id, index);
  }
  const bundleId = file.bundle.id;
  const groupIndex = firstGroup.get(bundleId);
  const first =
    timelines.get(bundleId) ??
    (groupIndex === undefined ? undefined : ["bundle", "groups", groupIndex, "id"]);
  if (first !== undefined) problems.push(duplicate(bundleId, ["bundle", "id"], first));
  const ancestors = ancestorsOf(file.timelines);
  const firstMember = new Map<string, PathSegment[]>();
  for (const [groupIndex, group] of groups.entries()) {
    const path = ["bundle", "groups", groupIndex, "members"];
    problems.push(...memberProblems(group, path, ancestors, firstMember));
  }
  const orders = file.graphical?.order ?? {};
  for (const key of Object.keys(orders).sort(compareCodePoints)) {
    const path = ["graphical", "order", key];
    const index = firstGroup.get(key);
    if (index === undefined) {
      problems.push(
        new SchemaValidationError(path, `${JSON.stringify(key)} names no group of this bundle`),
      );
    } else {
      problems.push(...orderProblems(groups[index] as GroupValue, orders[key] ?? [], path));
    }
  }
  return problems;
}

/**
 * The violations of the identity rules in a schema-valid file.
 *
 * **Timeline file.** Every id of the manifest (timelines, conversion maps,
 * regions, breaks, jumps and markers) is unique within it across all kinds:
 * each repeated id is one problem, located at its second occurrence in
 * identity order (a timeline, then its maps, regions, breaks, jumps and
 * markers, then its children by key). A jump's non-null `target` names a
 * marker of the same timeline; each one that does not is one problem, located
 * at the `target`. A segment line's segments are contiguous from 0 to its
 * length, of its class, with one `is_segment_line` value (see
 * `segmentProblems`). The duplicate problems come first, then the targets,
 * then the segment lines.
 *
 * **Group and bundle files**, in this order:
 * 1. each root of `timelines`, in array order, is its own scope under the
 *    timeline-file rules, its problems located under `timelines/<i>`;
 * 2. root by root, in identity order, a conversion-map, region, break, jump or
 *    marker id that is a part word (`start`, `end`, `name`, `label` or `card`,
 *    which follow an element's address as its parts): at that `id`,
 *    `id "<word>" is reserved in a group or bundle file`;
 * 3. a timeline id (of a root or a descendant) repeating a timeline id of an
 *    earlier root: at the later occurrence, `duplicate id`;
 * 4. a group id equal to a timeline id (at the group's `id`, first at the
 *    timeline), or, in a bundle, to the id of an earlier group (first at that
 *    group);
 * 5. in a bundle, a bundle id equal to a timeline id or to a group id (at
 *    `bundle/id`, first at the timeline, else at the first such group);
 * 6. member by member: a member naming no timeline of the file, at the
 *    member; in a bundle, a member already named by an earlier group, at the
 *    later member, `duplicate member`; a member nested with an earlier member
 *    of the same group (inside it or containing it), at the later member;
 * 7. in a group file, a root containing no member, at the root;
 * 8. `graphical.order` (a group file's array, or each entry of a bundle's
 *    object in code-point order of its keys): a key naming no group, at the
 *    key; each entry that is not a member of the group, at the entry; then
 *    each member missing from the order, at the order.
 *
 * Python's `timeskeleton.identity_problems` gives the same problems.
 */
export function identityProblems(
  value: TimeSkeletonFile | Lossless<TimeSkeletonFile>,
): SchemaValidationError[] {
  const kind = fileKind(value);
  if (kind === "group") return groupProblems(value as TimeSkeletonGroupFile);
  if (kind === "bundle") return bundleProblems(value as TimeSkeletonBundleFile);
  return timelineProblems((value as TimeSkeletonManifest).timeline, ["timeline"]);
}
