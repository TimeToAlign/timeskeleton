/**
 * JSON values as `parseJson` reads them. A JSON number keeps its written
 * kind: a safe integer or a float with a fractional part is a plain number,
 * an integer beyond `Number.MAX_SAFE_INTEGER` a `bigint`, an integral float
 * (`2.0`) a `JsonFloat`. `Lossless<T>` is any generated type with its numbers
 * read that way, tuples kept as tuples. An object read by `parseJson` keeps
 * the written order of its keys, array-index keys included; `clone`, `plain`
 * and the compact writer honour that order.
 */

/**
 * A float whose value is an integer, such as `2.0`, `1e+16` or `-0.0`.
 *
 * A JavaScript number cannot tell `2.0` from `2`. `parseJson` returns these floats
 * wrapped, so that `dumps` writes them back as floats; every other float is a
 * plain number, which is never an integer.
 */
export class JsonFloat {
  readonly value: number;

  constructor(value: number) {
    if (!Number.isFinite(value)) throw new RangeError(`not a finite float: ${value}`);
    this.value = value;
    Object.freeze(this);
  }
}

/**
 * A number as `parseJson` reads it: a `number` (a safe integer, or a
 * float with a fractional part), a `bigint` (an integer beyond
 * `Number.MAX_SAFE_INTEGER`), or a `JsonFloat` (an integral float).
 */
export type JsonNumber = number | bigint | JsonFloat;

/** Any JSON value, as `JSON.parse` returns it. */
export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };

/**
 * The type `T` with every number as `parseJson` reads it. Arrays map element
 * by element and tuples stay tuples, so a `[numerator, denominator]` Fraction
 * is a pair of `JsonNumber`s.
 */
export type Lossless<T> = T extends number
  ? JsonNumber
  : T extends readonly unknown[]
    ? number extends T["length"]
      ? T extends unknown[]
        ? Lossless<T[number]>[]
        : readonly Lossless<T[number]>[]
      : { [Index in keyof T]: Lossless<T[Index]> }
    : T extends object
      ? { [Key in keyof T]: Lossless<T[Key]> }
      : T;

/** A JSON object. */
export type JsonObject = Record<string, unknown>;

/**
 * The order of an object's keys, where it differs from `Object.keys`.
 *
 * JavaScript lists array-index keys (`"2"`, `"10"`) first and in numeric order,
 * whatever order they were written in. `parseJson` records the written order of
 * an object holding such keys here, and `compactJson` honours it.
 */
const KEY_ORDER = Symbol("timeskeleton.keyOrder");

const INDEX_KEY = /^(?:0|[1-9]\d{0,9})$/;

function isIndexKey(key: string): boolean {
  return INDEX_KEY.test(key) && Number(key) < 2 ** 32 - 1;
}

/** Whether a value is a `JsonFloat`, an integral float read by `parseJson`. */
export function isJsonFloat(value: unknown): value is JsonFloat {
  return value instanceof JsonFloat;
}

/** Whether a value is a JSON object (not an array, not a `JsonFloat`). */
export function isJsonObject(value: unknown): value is JsonObject {
  return (
    typeof value === "object" &&
    value !== null &&
    !Array.isArray(value) &&
    !(value instanceof JsonFloat)
  );
}

/** Build an object whose keys keep the given order, the last value of a repeated key winning. */
export function objectFrom(entries: Iterable<readonly [string, unknown]>): JsonObject {
  const result: JsonObject = {};
  const order: string[] = [];
  for (const [key, value] of entries) {
    if (!Object.hasOwn(result, key)) order.push(key);
    Object.defineProperty(result, key, {
      value,
      enumerable: true,
      writable: true,
      configurable: true,
    });
  }
  if (order.some(isIndexKey)) {
    Object.defineProperty(result, KEY_ORDER, { value: order, writable: true });
  }
  return result;
}

/** The keys of an object in their intended order: the written order where one was recorded. */
export function keysOf(value: JsonObject): string[] {
  const own = Object.keys(value);
  const order = (value as { [KEY_ORDER]?: string[] })[KEY_ORDER];
  if (order === undefined) return own;
  const present = new Set(own);
  const listed = order.filter((key) => present.has(key));
  const seen = new Set(listed);
  return [...listed, ...own.filter((key) => !seen.has(key))];
}

/** A deep copy that keeps `JsonFloat`, `bigint` and the order of keys. */
export function clone<T>(value: T): T {
  if (Array.isArray(value)) return value.map(clone) as T;
  if (isJsonObject(value)) {
    return objectFrom(keysOf(value).map((key) => [key, clone(value[key])])) as T;
  }
  return value;
}

/** The value with every `JsonFloat` and `bigint` as a plain number. */
export function plain(value: unknown): unknown {
  if (value instanceof JsonFloat) return value.value;
  if (typeof value === "bigint") return Number(value);
  if (Array.isArray(value)) return value.map(plain);
  if (isJsonObject(value)) return objectFrom(keysOf(value).map((key) => [key, plain(value[key])]));
  return value;
}
