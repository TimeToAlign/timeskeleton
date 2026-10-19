/**
 * The canonical spelling of the numbers of a TimeSkeleton manifest.
 *
 * The declared number type decides how a value is read, never its spelling,
 * and writers spell every value canonically: an own-axis value on an int axis
 * as a JSON integer, on a float axis as a float, and every member of a
 * Fraction pair as a JSON integer. A number whose place declares no number
 * type keeps its spelling. `complete` and `canonicalOrder` respell what they
 * return; Python's `timeskeleton` respells the same values.
 */

import type { NumberType } from "../generated/types.js";
import { isJsonObject, JsonFloat, type JsonObject } from "../json/value.js";
import { UNIT_NUMBER_TYPES } from "../validate/diagnostics.js";

interface MapMembers {
  readonly values?: readonly string[];
  readonly arrays?: readonly string[];
  readonly records?: readonly string[];
}

/** The members of each conversion map type that hold a Number. */
export const MAP_NUMBER_MEMBERS: Readonly<Record<string, MapMembers>> = {
  ConstantMap: { values: ["value"] },
  LinearMap: { values: ["scalar", "offset"] },
  PiecewiseMap: { arrays: ["breaks"] },
  TableMap: { arrays: ["x_values", "y_values"] },
};

/** The members of each conversion map type that hold nested conversion maps. */
export const MAP_NESTED_MEMBERS: Readonly<Record<string, MapMembers>> = {
  ChainMap: { arrays: ["maps"] },
  CombinationMap: { records: ["maps"] },
  PiecewiseMap: { arrays: ["maps"] },
};

const ROW_NUMBER_MEMBERS = ["qstamp", "nominal_length", "actual_length", "offset_within_measure"];

/** An integral float as the integer it equals, anything else as it is. */
function integral(value: unknown): unknown {
  if (!(value instanceof JsonFloat) || !Number.isInteger(value.value)) return value;
  if (!Number.isSafeInteger(value.value)) return BigInt(value.value);
  return value.value === 0 ? 0 : value.value;
}

/** A pair with its members spelled as integers, anything else as it is. */
function fraction(value: unknown): unknown {
  return Array.isArray(value) && value.length === 2 ? value.map(integral) : value;
}

/** An own-axis value spelled as its axis's number type selects. */
function onAxis(value: unknown, numberType: NumberType | undefined): unknown {
  if (numberType === "fraction") return fraction(value);
  if (numberType === "int") return integral(value);
  if (numberType === "float") {
    if (typeof value === "number" && Number.isInteger(value)) return new JsonFloat(value);
    if (typeof value === "bigint") {
      const double = Number(value);
      if (Number.isFinite(double) && BigInt(double) === value) return new JsonFloat(double);
    }
  }
  return value;
}

/** The number type of a timeline's axis, or `undefined` where it states none. */
function axisType(timeline: JsonObject): NumberType | undefined {
  const { number_type: numberType, unit } = timeline;
  if (numberType === "int" || numberType === "float" || numberType === "fraction") {
    return numberType;
  }
  return typeof unit === "string" && Object.hasOwn(UNIT_NUMBER_TYPES, unit)
    ? UNIT_NUMBER_TYPES[unit as keyof typeof UNIT_NUMBER_TYPES]
    : undefined;
}

function objects(value: unknown): JsonObject[] {
  return Array.isArray(value) ? value.filter(isJsonObject) : [];
}

function respellMap(map: JsonObject): void {
  const type = map.type;
  if (typeof type !== "string") return;
  const members = Object.hasOwn(MAP_NUMBER_MEMBERS, type) ? MAP_NUMBER_MEMBERS[type] : undefined;
  for (const key of members?.values ?? []) {
    if (Object.hasOwn(map, key)) map[key] = fraction(map[key]);
  }
  for (const key of members?.arrays ?? []) {
    const values = map[key];
    if (Array.isArray(values)) map[key] = values.map(fraction);
  }
  const nested = Object.hasOwn(MAP_NESTED_MEMBERS, type) ? MAP_NESTED_MEMBERS[type] : undefined;
  for (const key of nested?.values ?? []) {
    const inner = map[key];
    if (isJsonObject(inner)) respellMap(inner);
  }
  for (const key of nested?.arrays ?? []) for (const inner of objects(map[key])) respellMap(inner);
  for (const key of nested?.records ?? []) {
    const record = map[key];
    if (isJsonObject(record)) for (const inner of objects(Object.values(record))) respellMap(inner);
  }
}

function respellAxis(
  owner: JsonObject,
  keys: readonly string[],
  numberType: NumberType | undefined,
): void {
  for (const key of keys) {
    if (Object.hasOwn(owner, key)) owner[key] = onAxis(owner[key], numberType);
  }
}

function respellTimeline(timeline: JsonObject, offsetType: NumberType | undefined): void {
  const own = axisType(timeline);
  respellAxis(timeline, ["offset"], offsetType ?? own);
  respellAxis(timeline, ["length"], own);
  for (const region of objects(timeline.regions)) respellAxis(region, ["start", "end"], own);
  const flow = timeline.flow_control;
  if (isJsonObject(flow)) {
    for (const entry of objects(flow.breaks)) respellAxis(entry, ["coordinate"], own);
    for (const entry of objects(flow.jumps)) {
      respellAxis(entry, ["from_coordinate", "to_coordinate"], own);
    }
    for (const entry of objects(flow.markers)) respellAxis(entry, ["coordinate"], own);
  }
  for (const map of objects(timeline.conversion_maps)) respellMap(map);
  for (const child of objects(timeline.children)) respellTimeline(child, own);
}

/**
 * Spell every value of a manifest as its number type selects, in place.
 *
 * An own-axis value on an int axis becomes a JSON integer, on a float axis a
 * float where one equals it exactly (a `JsonFloat` where it is integral), and
 * every member of a Fraction pair (own-axis, conversion-map Numbers at any
 * depth, measure-map rows) a JSON integer where it is integral. Anything else
 * is left as it is, so any value may be given.
 */
export function respell(manifest: unknown): void {
  if (!isJsonObject(manifest)) return;
  for (const timeline of objects(manifest.timelines)) respellTimeline(timeline, undefined);
  for (const measureMap of objects(manifest.measure_maps)) {
    for (const row of objects(measureMap.rows)) {
      for (const key of ROW_NUMBER_MEMBERS) {
        if (Object.hasOwn(row, key)) row[key] = fraction(row[key]);
      }
    }
  }
}
