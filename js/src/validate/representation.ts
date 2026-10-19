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
    "representation",
    [...path, key],
    `${key} ${spell(value)} of '${text(owner, "id")}' is ${ARTICLES[writtenAs(value)]} on ${ARTICLES[numberType]} axis: write ${fix}`,
  );
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
  for (const [index, entry] of entries(timeline, "flow_control").entries()) {
    yield* representationProblem("coordinate", entry, [...path, "flow_control", index], own);
  }
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* timelineRepresentation(child, [...path, "children", index], own);
  }
}

/** Yield own-axis representation violations in manifest order. */
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
