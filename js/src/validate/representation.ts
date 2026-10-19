import type { NumberType, TimeUnit } from "../generated/types.js";
import { isJsonObject, JsonFloat, type JsonObject } from "../json/value.js";
import { spell } from "../json/write.js";
import { exact, exactNumber, jsonInteger, type Rational } from "../numbers/exact.js";
import {
  entries,
  jsonPointer,
  numberTypeOf,
  type PathSegment,
  SchemaValidationError,
  text,
} from "./diagnostics.js";

const ARTICLES: Readonly<Record<NumberType, string>> = {
  int: "an int",
  float: "a float",
  fraction: "a fraction",
};

interface MapMembers {
  readonly values?: readonly string[];
  readonly arrays?: readonly string[];
  readonly records?: readonly string[];
}

export const MAP_NUMBER_MEMBERS: Readonly<Record<string, MapMembers>> = {
  IntervalToConstantMap: { arrays: ["boundaries"] },
  LinearMap: { values: ["scalar", "offset"] },
  MetricMap: { arrays: ["starts", "lengths"] },
  PiecewiseMap: { arrays: ["breaks"] },
  QuartersToFloatingMeasures: { arrays: ["x_values", "y_values"] },
  QuartersToMeasureNumber: { arrays: ["boundaries"] },
  QuartersToTicks: { values: ["scalar"] },
  SamplesToSeconds: { values: ["scalar"] },
  ScalarMap: { values: ["scalar"] },
  SecondsToSamples: { values: ["scalar"] },
  ShiftMap: { values: ["offset"] },
  TableMap: { arrays: ["x_values", "y_values"] },
  TicksToQuarters: { values: ["scalar"] },
};

export const MAP_NESTED_MEMBERS: Readonly<Record<string, MapMembers>> = {
  BeatInMeasureMap: { values: ["meter_map"] },
  ChainMap: { arrays: ["maps"] },
  CombinationMap: { records: ["maps"] },
  MetricalPositionMap: { values: ["meter_map"] },
  PiecewiseMap: { arrays: ["maps"] },
};

function writtenAs(value: unknown): NumberType {
  if (Array.isArray(value)) return "fraction";
  return typeof value === "bigint" || (typeof value === "number" && Number.isInteger(value))
    ? "int"
    : "float";
}

function represents(value: unknown, numberType: NumberType): boolean {
  if (numberType === "fraction") return Array.isArray(value);
  if (Array.isArray(value)) return false;
  if (numberType === "float")
    return writtenAs(value) !== "int" || rewritten(value, "float") !== null;
  return jsonInteger(value) !== null;
}

/** Spell an exact rewriting in an axis number type, or return `null`. */
export function rewritten(value: unknown, numberType: NumberType): string | null {
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
  if (back.numerator !== exactValue.numerator || back.denominator !== exactValue.denominator) {
    return null;
  }
  return spell(Number.isInteger(double) ? new JsonFloat(double) : double);
}

function* fractionMemberProblems(
  value: unknown,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  if (!Array.isArray(value)) return;
  for (const [index, member] of value.entries()) {
    if (!(member instanceof JsonFloat)) continue;
    const name = index === 0 ? "numerator" : "denominator";
    yield new SchemaValidationError(
      "representation",
      [...path, index],
      `fraction ${name} ${spell(member)} is a float: write ${rewritten(member, "int")}`,
    );
  }
}

function* representationProblem(
  key: string,
  owner: JsonObject,
  path: readonly PathSegment[],
  numberType: NumberType,
): Generator<SchemaValidationError> {
  const value = owner[key];
  if (value === undefined || value === null) return;
  yield* fractionMemberProblems(value, [...path, key]);
  if (represents(value, numberType)) return;
  const fix = rewritten(value, numberType) ?? ARTICLES[numberType];
  yield new SchemaValidationError(
    "representation",
    [...path, key],
    `${key} ${spell(value)} of '${text(owner, "id")}' is ${ARTICLES[writtenAs(value)]} on ${ARTICLES[numberType]} axis: write ${fix}`,
  );
}

function* conversionMapFractionProblems(
  map: JsonObject,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const type = text(map, "type");
  const members = MAP_NUMBER_MEMBERS[type];
  for (const key of members?.values ?? []) {
    yield* fractionMemberProblems(map[key], [...path, key]);
  }
  for (const key of members?.arrays ?? []) {
    const values = map[key];
    if (!Array.isArray(values)) continue;
    for (const [index, value] of values.entries()) {
      yield* fractionMemberProblems(value, [...path, key, index]);
    }
  }

  const nestedMembers = MAP_NESTED_MEMBERS[type];
  for (const key of nestedMembers?.values ?? []) {
    const nested = map[key];
    if (isJsonObject(nested)) {
      yield* conversionMapFractionProblems(nested, [...path, key]);
    }
  }
  for (const key of nestedMembers?.arrays ?? []) {
    for (const [index, nested] of entries(map, key).entries()) {
      yield* conversionMapFractionProblems(nested, [...path, key, index]);
    }
  }
  for (const key of nestedMembers?.records ?? []) {
    const nestedMaps = map[key];
    if (isJsonObject(nestedMaps)) {
      for (const [name, nested] of Object.entries(nestedMaps)) {
        if (isJsonObject(nested)) {
          yield* conversionMapFractionProblems(nested, [...path, key, name]);
        }
      }
    }
  }
}

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
  for (const [index, map] of entries(timeline, "conversion_maps").entries()) {
    yield* conversionMapFractionProblems(map, [...path, "conversion_maps", index]);
  }
  const measureMap = timeline.measure_map;
  if (Array.isArray(measureMap)) {
    for (const [index, row] of measureMap.entries()) {
      if (!isJsonObject(row)) continue;
      for (const key of ["qstamp", "nominal_length", "actual_length", "offset_within_measure"]) {
        yield* fractionMemberProblems(row[key], [...path, "measure_map", index, key]);
      }
    }
  }
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* timelineRepresentation(child, [...path, "children", index], own);
  }
}

/** Yield fraction-member and own-axis representation violations in manifest order. */
export function* representationProblems(manifest: JsonObject): Generator<SchemaValidationError> {
  for (const [index, root] of entries(manifest, "timelines").entries()) {
    yield* timelineRepresentation(root, ["timelines", index], null);
  }
}

/**
 * Yield non-finite numeric leaves before any value is adapted for Ajv.
 *
 * Only a plain number can be one: a `JsonFloat` refuses a non-finite value
 * when constructed. A leaf is named by its key and the id of the nearest
 * object above it that has one, or else by its JSON pointer.
 */
export function* finiteNumberProblems(
  value: unknown,
  path: readonly PathSegment[] = [],
  ownerId: string | null = null,
  ownerKey: string | null = null,
): Generator<SchemaValidationError> {
  if (typeof value === "number" && !Number.isFinite(value)) {
    const detail =
      ownerId !== null && ownerKey !== null
        ? `${ownerKey} of '${ownerId}' is not a finite number`
        : `${jsonPointer(path)} is not a finite number`;
    yield new SchemaValidationError("finite_number", path, detail);
    return;
  }
  if (Array.isArray(value)) {
    for (const [index, item] of value.entries()) {
      yield* finiteNumberProblems(item, [...path, index], ownerId, ownerKey);
    }
    return;
  }
  if (!isJsonObject(value)) return;
  const id = typeof value.id === "string" ? value.id : ownerId;
  for (const [key, item] of Object.entries(value)) {
    yield* finiteNumberProblems(item, [...path, key], id, key);
  }
}
