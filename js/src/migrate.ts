/**
 * Migrations between schema versions.
 *
 * A migration is a pure function from a document at one version to the same
 * document at the next version, declaring that version. `migrate` chains them
 * from the declared version up to `SCHEMA_VERSION`. Each migration is
 * pinned by a fixture pair (the document before and after) in the test suite.
 */

import {
  canonicalOrder,
  clone,
  exactNumber,
  isJsonObject,
  jsonInteger,
  type Rational,
  rational,
} from "./document.js";
import type { TimeSkeletonDocument } from "./generated/types.js";
import {
  declaredVersion,
  jsonPointer,
  type PathSegment,
  SCHEMA_VERSION,
  SchemaValidationError,
  SUPPORTED_VERSIONS,
  UnsupportedVersionError,
  validate,
} from "./validate.js";

export type Migration = (document: Record<string, unknown>) => Record<string, unknown>;

type Path = readonly PathSegment[];
type JsonObject = Record<string, unknown>;

/**
 * Thrown when a document holds a member whose shape a migration does not know.
 *
 * `path` locates the offending value and `detail` says why; `message` reads
 * `<JSON pointer>: <detail>`.
 */
export class MigrationError extends Error {
  readonly path: readonly PathSegment[];
  /** Why the member cannot be migrated, without the path. */
  readonly detail: string;

  constructor(path: Path, detail: string) {
    super(`${jsonPointer(path)}: ${detail}`);
    this.name = "MigrationError";
    this.path = path;
    this.detail = detail;
  }
}

const isObject = isJsonObject;

/** Whether two JSON values are equal, numbers by value as in Python (`1 == 1.0`). */
function sameJson(left: unknown, right: unknown): boolean {
  if (Array.isArray(left) || Array.isArray(right)) {
    return (
      Array.isArray(left) &&
      Array.isArray(right) &&
      left.length === right.length &&
      left.every((item, index) => sameJson(item, right[index]))
    );
  }
  if (isObject(left) || isObject(right)) {
    if (!isObject(left) || !isObject(right)) return false;
    const keys = Object.keys(left);
    return (
      keys.length === Object.keys(right).length &&
      keys.every((key) => key in right && sameJson(left[key], right[key]))
    );
  }
  const a = exactNumber(left);
  const b = exactNumber(right);
  if (a !== null && b !== null) return equal(a, b);
  return left === right;
}

// -- exact rationals ------------------------------------------------------------

function add(left: Rational, right: Rational): Rational {
  return rational(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator,
  );
}

function equal(left: Rational | null, right: Rational | null): boolean {
  if (left === null || right === null) return left === right;
  return left.numerator === right.numerator && left.denominator === right.denominator;
}

/** A JSON integer: a number where it is safe, else a bigint. */
function integerValue(value: bigint): number | bigint {
  const safe = BigInt(Number.MAX_SAFE_INTEGER);
  return value >= -safe && value <= safe ? Number(value) : value;
}

function pair(value: Rational): [number | bigint, number | bigint] {
  return [integerValue(value.numerator), integerValue(value.denominator)];
}

// -- 0.1.0 to 0.2.0 ---------------------------------------------------------------

const MEASURE_CLASSES = [
  "Measure",
  "RegularMeasure",
  "IrregularMeasure",
  "MeasureConstituent",
  "CadenzaMeasure",
];
const MEASURE_KEYS = [
  "class",
  "id",
  "count",
  "qstamp",
  "number",
  "name",
  "time_signature",
  "nominal_length",
  "actual_length",
  "start_repeat",
  "end_repeat",
  "next",
  "volta",
];
const ROW_KEYS = [
  "ID",
  "count",
  "qstamp",
  "number",
  "name",
  "time_signature",
  "nominal_length",
  "actual_length",
  "start_repeat",
  "end_repeat",
  "next",
  "volta",
  "offset_within_measure",
] as const;
const QUARTER_KEYS = ["qstamp", "nominal_length", "actual_length", "offset_within_measure"];

interface MeasureValues {
  ID: string;
  count: number;
  qstamp: Rational | null;
  number: number | null;
  name: string | null;
  time_signature: string | null;
  nominal_length: Rational | null;
  actual_length: Rational | null;
  start_repeat: unknown;
  end_repeat: unknown;
  next: string[];
  volta: unknown;
  offset_within_measure: Rational | null;
}

/** Read a 0.1.0 measure quarter value: a Fraction pair, or null. */
function quarters(value: unknown, path: Path): Rational | null {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value) && value.length === 2) {
    const [numerator, denominator] = value.map(jsonInteger);
    if (numerator !== null && numerator !== undefined && denominator && denominator > 0n) {
      return rational(numerator, denominator);
    }
  }
  throw new MigrationError(path, `expected a Fraction pair or null, got ${JSON.stringify(value)}`);
}

/** Return the class a 0.2.0 reader derives from a measure's values. */
function measureClass(measure: MeasureValues): string {
  const signature = measure.time_signature;
  if (measure.nominal_length === null) return "Measure";
  if (typeof signature === "string" && signature.toLowerCase() === "cadenza") {
    return "CadenzaMeasure";
  }
  if (measure.offset_within_measure !== null) return "MeasureConstituent";
  if (equal(measure.actual_length, measure.nominal_length)) return "RegularMeasure";
  return "IrregularMeasure";
}

/** Read the tagged-measure measure map timetoalign wrote at 0.1.0. */
function readMeasures(value: unknown, path: Path): MeasureValues[] {
  if (!isObject(value) || Object.keys(value).join() !== "measures") {
    throw new MigrationError(path, "expected an object whose only member is 'measures'");
  }
  const items = value.measures;
  if (!Array.isArray(items) || items.length === 0) {
    throw new MigrationError([...path, "measures"], "expected a non-empty array");
  }
  const ids = new Map<string, string>();
  const stated: unknown[] = [];
  const measures = items.map((item: unknown, index): MeasureValues => {
    const position = index + 1;
    const itemPath: Path = [...path, "measures", index];
    if (!isObject(item)) throw new MigrationError(itemPath, "expected a tagged measure object");
    const tag = item.class;
    if (typeof tag !== "string" || !MEASURE_CLASSES.includes(tag)) {
      throw new MigrationError(
        [...itemPath, "class"],
        `no row form for class ${JSON.stringify(tag)}`,
      );
    }
    const expected = [
      ...MEASURE_KEYS,
      ...(tag === "MeasureConstituent" ? ["offset_within_measure"] : []),
    ];
    const difference = [
      ...Object.keys(item).filter((key) => !expected.includes(key)),
      ...expected.filter((key) => !(key in item)),
    ].sort();
    if (difference.length > 0) {
      throw new MigrationError(
        [...itemPath, difference[0] as string],
        "not a 0.1.0 measure member",
      );
    }
    if (jsonInteger(item.count) !== BigInt(position)) {
      throw new MigrationError([...itemPath, "count"], `expected count ${position}`);
    }
    const identifier = item.id;
    if (typeof identifier !== "string") {
      throw new MigrationError([...itemPath, "id"], "expected a string");
    }
    // timetoalign spelled the default identity "m<count>"; the row ID's
    // default is String(count).
    const rowId = identifier === `m${position}` ? String(position) : identifier;
    ids.set(identifier, rowId);
    stated.push(item.next);
    const measure: MeasureValues = {
      ID: rowId,
      count: position,
      qstamp: quarters(item.qstamp, [...itemPath, "qstamp"]),
      number: item.number as number | null,
      name: item.name as string | null,
      time_signature: item.time_signature as string | null,
      nominal_length: quarters(item.nominal_length, [...itemPath, "nominal_length"]),
      actual_length: quarters(item.actual_length, [...itemPath, "actual_length"]),
      start_repeat: item.start_repeat,
      end_repeat: item.end_repeat,
      next: [],
      volta: item.volta,
      offset_within_measure: null,
    };
    const offset = quarters(item.offset_within_measure, [...itemPath, "offset_within_measure"]);
    measure.offset_within_measure = offset === null || offset.numerator === 0n ? null : offset;
    if (measureClass(measure) !== tag) {
      throw new MigrationError(
        [...itemPath, "class"],
        `a row with these values reads as ${measureClass(measure)}, not ${tag}`,
      );
    }
    return measure;
  });
  measures.forEach((measure, index) => {
    const successors = stated[index];
    const following = measures[index + 1];
    if (successors === null) {
      measure.next = following === undefined ? [] : [following.ID];
    } else if (
      Array.isArray(successors) &&
      successors.every((entry) => typeof entry === "string" && ids.has(entry))
    ) {
      measure.next = successors.map((entry) => ids.get(entry as string) as string);
    } else {
      throw new MigrationError(
        [...path, "measures", index, "next"],
        "expected null or measure ids of this map",
      );
    }
  });
  return measures;
}

/** Compress measures into rows exactly as timetoalign's MeasureMap.to_rows. */
function rows(measures: readonly MeasureValues[]): JsonObject[] {
  const last = measures.length - 1;

  function encoded(values: Record<string, unknown>): JsonObject {
    const row: JsonObject = {};
    for (const key of ROW_KEYS) {
      const value = values[key];
      if (value === null || value === undefined) continue;
      row[key] = QUARTER_KEYS.includes(key) ? pair(value as Rational) : value;
    }
    return row;
  }

  function rowFor(index: number): JsonObject {
    const measure = measures[index] as MeasureValues;
    const number = measure.number ?? measure.count;
    return encoded({
      ...measure,
      ID: measure.ID === String(measure.count) ? null : measure.ID,
      number,
      name: measure.name ?? String(number),
      next: index < last || measure.next.length > 0 ? measure.next : null,
    });
  }

  function defaultSuccessor(index: number): JsonObject {
    const measure = measures[index] as MeasureValues;
    const successor = rowFor(index);
    delete successor.ID;
    delete successor.volta;
    delete successor.offset_within_measure;
    successor.count = measure.count + 1;
    if (measure.qstamp !== null && measure.actual_length !== null) {
      successor.qstamp = pair(add(measure.qstamp, measure.actual_length));
    }
    if (measure.actual_length !== null) {
      delete successor.actual_length;
      if (measure.nominal_length !== null) {
        successor.actual_length = pair(measure.nominal_length);
      }
    }
    if (measure.number !== null) {
      successor.number = measure.number + 1;
      if (measure.name !== null) successor.name = String(measure.number + 1);
    }
    successor.start_repeat = false;
    successor.end_repeat = false;
    successor.next = [(measures[index + 2] as MeasureValues).ID];
    return successor;
  }

  return measures
    .map((_, index) => index)
    .filter(
      (index) =>
        index === 0 || index === last || !sameJson(rowFor(index), defaultSuccessor(index - 1)),
    )
    .map(rowFor);
}

/** Keep the meter map once and name the derived beat map by its id. */
function metricalPositionMap(value: JsonObject, path: Path): JsonObject {
  const expected = [
    "type",
    "id",
    "name",
    "source_unit",
    "target_unit",
    "maps",
    "names",
    "meter_map",
  ];
  const difference = [
    ...Object.keys(value).filter((key) => !expected.includes(key)),
    ...expected.filter((key) => !(key in value)),
  ].sort();
  if (difference.length > 0) {
    throw new MigrationError(
      [...path, difference[0] as string],
      "not a 0.1.0 MetricalPositionMap member",
    );
  }
  const maps = value.maps;
  const beat = isObject(maps) ? maps.beat : undefined;
  const derived =
    isObject(maps) &&
    sameJson(Object.keys(maps).sort(), ["beat", "mc"]) &&
    sameJson(value.names, ["mc", "beat"]) &&
    sameJson(maps.mc, value.meter_map) &&
    isObject(beat) &&
    typeof beat.id === "string" &&
    sameJson(beat, {
      type: "BeatInMeasureMap",
      id: beat.id,
      name: "beat_in_measure",
      source_unit: "quarters",
      target_unit: null,
      meter_map: value.meter_map,
    });
  if (!derived) {
    throw new MigrationError([...path, "maps"], "the maps are not the two derived from meter_map");
  }
  return {
    type: value.type,
    id: value.id,
    name: value.name,
    source_unit: value.source_unit,
    target_unit: value.target_unit,
    meter_map: value.meter_map,
    beat_map_id: (beat as JsonObject).id,
  };
}

/** Migrate one conversion map, descending into the maps it composes. */
function conversionMap(value: unknown, path: Path): unknown {
  if (!isObject(value)) return value;
  const kind = value.type;
  if (kind === "MetricalPositionMap") return metricalPositionMap(value, path);
  const result: JsonObject = { ...value };
  if ((kind === "ChainMap" || kind === "PiecewiseMap") && Array.isArray(value.maps)) {
    result.maps = value.maps.map((item: unknown, index) =>
      conversionMap(item, [...path, "maps", index]),
    );
  }
  if (kind === "CombinationMap" && isObject(value.maps)) {
    result.maps = Object.fromEntries(
      Object.entries(value.maps).map(([name, item]) => [
        name,
        conversionMap(item, [...path, "maps", name]),
      ]),
    );
  }
  return result;
}

/** Migrate one timeline manifest and its children in place. */
function migrateTimeline(manifest: JsonObject, path: Path): void {
  if (isObject(manifest.measure_map)) {
    manifest.measure_map = rows(readMeasures(manifest.measure_map, [...path, "measure_map"]));
  }
  if (Array.isArray(manifest.conversion_maps)) {
    manifest.conversion_maps = manifest.conversion_maps.map((item: unknown, index) =>
      conversionMap(item, [...path, "conversion_maps", index]),
    );
  }
  if (isObject(manifest.children)) {
    for (const [key, child] of Object.entries(manifest.children)) {
      if (isObject(child) && isObject(child.timeline)) {
        migrateTimeline(child.timeline, [...path, "children", key, "timeline"]);
      }
    }
  }
}

/**
 * Give the members 0.1.0 left opaque their 0.2.0 shapes.
 *
 * 0.1.0 specified only the envelope, a timeline's top level and its
 * coordinates. This step rewrites the shapes timetoalign wrote at 0.1.0 that
 * 0.2.0 specifies differently: a tagged-measure `measure_map` becomes
 * compressed Measure Map rows, and a `MetricalPositionMap`, at any depth of the
 * conversion maps, keeps its meter map once and names its derived beat map by
 * `beat_map_id`. Every other member is kept as it is, and the result must then
 * satisfy 0.2.0: a member whose shape the step does not know is refused with
 * its path.
 *
 * @throws {MigrationError} at the path of the first member that cannot be migrated.
 */
function migrate010To020(document: JsonObject): JsonObject {
  const manifest = document.manifest;
  const timelines = isObject(manifest) ? manifest.timelines : undefined;
  if (isObject(timelines)) {
    for (const [key, timeline] of Object.entries(timelines)) {
      if (isObject(timeline)) migrateTimeline(timeline, ["manifest", "timelines", key]);
    }
  }
  return stamped(document, "0.2.0");
}

// -- 0.2.0 to 0.2.1 ---------------------------------------------------------------

/**
 * Write the document in the canonical order of 0.2.1.
 *
 * 0.2.1 specifies the same shapes as 0.2.0 and fixes the order of every
 * collection whose order carries no meaning (see `canonicalOrder`). The
 * document is validated against 0.2.1 before it is reordered, since the order
 * does not affect validity, so a refusal names the path of the input.
 *
 * @throws {MigrationError} at the path of the first member with no 0.2.1 shape.
 */
function migrate020To021(document: JsonObject): JsonObject {
  return canonicalOrder(stamped(document, "0.2.1"));
}

// -- 0.2.1 to 0.3.0 ---------------------------------------------------------------

/**
 * Declare 0.3.0.
 *
 * 0.3.0 keeps every definition of 0.2.1 and adds the optional `graphical`
 * block, which a 0.2.1 document does not carry, so the shapes are unchanged.
 * The document is validated against 0.3.0 and then put in canonical order.
 *
 * @throws {MigrationError} at the path of the first member with no 0.3.0 shape.
 */
function migrate021To030(document: JsonObject): JsonObject {
  return canonicalOrder(stamped(document, "0.3.0"));
}

/** Return `document` declaring `version`, refused unless valid at it. */
function stamped(document: JsonObject, version: string): JsonObject {
  const meta = isObject(document.meta) ? document.meta : {};
  const result: JsonObject = { ...document, meta: { ...meta, schema_version: version } };
  try {
    validate(result);
  } catch (error) {
    if (error instanceof SchemaValidationError) {
      throw new MigrationError(error.path, `no ${version} shape: ${error.detail}`);
    }
    throw error;
  }
  return result;
}

/**
 * Source version to `[target version, migration]`. Each migration returns the
 * document declaring its target version.
 */
export const MIGRATIONS: Readonly<Record<string, readonly [string, Migration]>> = {
  "0.1.0": ["0.2.0", migrate010To020],
  "0.2.0": ["0.2.1", migrate020To021],
  "0.2.1": ["0.3.0", migrate021To030],
};

/**
 * Return a deep copy of `document` brought to `SCHEMA_VERSION`.
 *
 * A document already at the latest version is copied unchanged and not
 * validated; call `validate` on it when the input is untrusted. A migrated
 * document satisfies the latest schema.
 *
 * @throws {UnsupportedVersionError} if `meta.schema_version` is missing, not a string, or not supported.
 * @throws {MigrationError} if a member cannot be migrated, at its path.
 */
export function migrate(document: unknown): TimeSkeletonDocument {
  const version = declaredVersion(document);
  if (version === null || !SUPPORTED_VERSIONS.includes(version)) {
    throw new UnsupportedVersionError(version);
  }
  let result = clone(document) as Record<string, unknown>;
  let current = version;
  while (current !== SCHEMA_VERSION) {
    const step = MIGRATIONS[current];
    if (step === undefined) {
      throw new UnsupportedVersionError(current);
    }
    const [next, apply] = step;
    result = apply(result);
    current = next;
  }
  return result as unknown as TimeSkeletonDocument;
}
