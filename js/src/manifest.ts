/**
 * Lossless reading, the canonical order and the standard writer of a
 * TimeSkeleton manifest.
 *
 * Every collection of a manifest whose order carries no meaning has one
 * canonical order, so equal values are equal text: at every depth, `children`
 * by offset, then id; `conversion_maps` by id; `regions` by start, then end, then name; flow-control `breaks` by
 * coordinate, then canonical JSON text; `jumps` by from coordinate, then to
 * coordinate, then canonical JSON text; `markers` by name. Coordinates compare
 * by exact numeric value, strings by Unicode code point. Readers accept any
 * order; writers emit the canonical one.
 *
 * The standard writer emits text with every character unescaped except `"`,
 * `\` and the control characters, two-space indentation and a final newline.
 * A float is always written as a float (`2.0`, `1e-07`), spelled as Python's
 * `repr` spells it; an integer never carries a decimal point or an exponent.
 * Both packages write the same value as the same bytes.
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

/** The type `T` with every number as `parseJson` reads it. */
export type Lossless<T> = T extends number
  ? JsonNumber
  : T extends readonly (infer Item)[]
    ? Lossless<Item>[]
    : T extends object
      ? { [Key in keyof T]: Lossless<T[Key]> }
      : T;

type JsonObject = Record<string, unknown>;

/**
 * The order of an object's keys, where it differs from `Object.keys`.
 *
 * JavaScript lists array-index keys (`"2"`, `"10"`) first and in numeric order,
 * whatever order they were written in. `parseJson` and `canonicalOrder` record the
 * intended order of an object holding such keys here, and `dumps` honours it.
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

/** Build an object whose keys keep the given order. */
function objectFrom(entries: Iterable<readonly [string, unknown]>): JsonObject {
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

/** The keys of an object in their intended order. */
function keysOf(value: JsonObject): string[] {
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

// -- reading ----------------------------------------------------------------------

const NUMBER = /-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/y;
const SAFE = BigInt(Number.MAX_SAFE_INTEGER);

function number(source: string): JsonNumber {
  if (/[.eE]/.test(source)) {
    const value = Number(source);
    if (!Number.isFinite(value)) throw new RangeError(`${source} is beyond the range of a double`);
    return Number.isInteger(value) ? new JsonFloat(value) : value;
  }
  const integer = BigInt(source);
  return integer >= -SAFE && integer <= SAFE ? Number(integer) : integer;
}

/**
 * Parse any JSON text without losing a number or the order of a key.
 *
 * Integers keep their exact value (a `bigint` beyond the safe range), floats
 * stay floats (an integral float is a `JsonFloat`), and an object's keys keep
 * their written order even where JavaScript would list array-index keys first.
 * The text `-0` is the integer `0`, as in Python. Strings are read exactly as
 * `JSON.parse` reads them, lone surrogates included.
 *
 * @throws {SyntaxError} if the text is not one JSON value.
 * @throws {RangeError} if a float is beyond the range of a double.
 */
export function parseJson(text: string): Lossless<Json> {
  let index = 0;

  const fail = (what: string): never => {
    throw new SyntaxError(`${what} at position ${index} of the JSON text`);
  };
  const space = (): void => {
    while (index < text.length && " \t\n\r".includes(text[index] as string)) index++;
  };
  const expect = (token: string): void => {
    if (!text.startsWith(token, index)) fail(`expected ${JSON.stringify(token)}`);
    index += token.length;
  };

  const string = (): string => {
    const start = index;
    index++;
    for (;;) {
      const character = text[index];
      if (character === undefined) fail("unterminated string");
      if (character === '"') break;
      index += character === "\\" ? 2 : 1;
    }
    index++;
    return JSON.parse(text.slice(start, index)) as string;
  };

  const value = (): unknown => {
    space();
    const character = text[index];
    if (character === "{") {
      index++;
      const entries: [string, unknown][] = [];
      space();
      if (text[index] === "}") {
        index++;
        return objectFrom(entries);
      }
      for (;;) {
        space();
        if (text[index] !== '"') fail("expected a string key");
        const key = string();
        space();
        expect(":");
        entries.push([key, value()]);
        space();
        if (text[index] === ",") {
          index++;
          continue;
        }
        expect("}");
        return objectFrom(entries);
      }
    }
    if (character === "[") {
      index++;
      const items: unknown[] = [];
      space();
      if (text[index] === "]") {
        index++;
        return items;
      }
      for (;;) {
        items.push(value());
        space();
        if (text[index] === ",") {
          index++;
          continue;
        }
        expect("]");
        return items;
      }
    }
    if (character === '"') return string();
    for (const [token, literal] of [
      ["true", true],
      ["false", false],
      ["null", null],
    ] as const) {
      if (text.startsWith(token, index)) {
        index += token.length;
        return literal;
      }
    }
    NUMBER.lastIndex = index;
    const match = NUMBER.exec(text);
    if (match === null) return fail("unexpected character");
    index += match[0].length;
    return number(match[0]);
  };

  const result = value();
  space();
  if (index !== text.length) fail("unexpected text after the JSON value");
  return result as Lossless<Json>;
}

// -- writing ----------------------------------------------------------------------

const LONE_SURROGATE = /[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/;

function quoted(value: string): string {
  if (LONE_SURROGATE.test(value)) {
    throw new RangeError(`a string holds a lone surrogate: ${JSON.stringify(value)}`);
  }
  // JSON.stringify escapes exactly what Python's json.dumps(ensure_ascii=False)
  // escapes in a well-formed string: '"', '\' and the control characters.
  return JSON.stringify(value);
}

/** Spell a finite double as Python's `repr` does. */
function float(value: number): string {
  if (!Number.isFinite(value)) throw new RangeError(`${value} is not a JSON number`);
  if (value === 0) return Object.is(value, -0) ? "-0.0" : "0.0";
  const sign = value < 0 ? "-" : "";
  // Number::toString yields the shortest digits that round-trip, as repr does.
  const [mantissa = "", exponent = "0"] = String(Math.abs(value)).split("e");
  const [whole = "", fraction = ""] = mantissa.split(".");
  let digits = whole + fraction;
  let point = whole.length + Number(exponent);
  const leading = (digits.match(/^0*/) as RegExpMatchArray)[0].length;
  digits = digits.slice(leading).replace(/0+$/, "");
  point -= leading;
  if (point <= -4 || point > 16) {
    const power = point - 1;
    const significand = digits.length === 1 ? digits : `${digits[0]}.${digits.slice(1)}`;
    const magnitude = String(Math.abs(power)).padStart(2, "0");
    return `${sign}${significand}e${power < 0 ? "-" : "+"}${magnitude}`;
  }
  if (point <= 0) return `${sign}0.${"0".repeat(-point)}${digits}`;
  if (point >= digits.length) return `${sign}${digits}${"0".repeat(point - digits.length)}.0`;
  return `${sign}${digits.slice(0, point)}.${digits.slice(point)}`;
}

function scalar(value: unknown): string {
  if (value === null) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "string") return quoted(value);
  if (typeof value === "bigint") return value.toString();
  if (value instanceof JsonFloat) return float(value.value);
  if (typeof value === "number") {
    // A plain number with a fractional part, or -0, can only be a float.
    if (!Number.isInteger(value) || Object.is(value, -0)) return float(value);
    return BigInt(value).toString();
  }
  throw new TypeError(`not a JSON value: ${String(value)}`);
}

/** Write a value with Python's `json.dumps` layout. */
function emit(value: unknown, indent: string | null, sortKeys: boolean, depth: string): string {
  const inner = indent === null ? "" : depth + indent;
  const open = indent === null ? "" : `\n${inner}`;
  const close = indent === null ? "" : `\n${depth}`;
  const comma = indent === null ? "," : `,\n${inner}`;
  const colon = indent === null ? ":" : ": ";
  if (Array.isArray(value)) {
    if (value.length === 0) return "[]";
    const items = value.map((item) => emit(item, indent, sortKeys, inner));
    return `[${open}${items.join(comma)}${close}]`;
  }
  if (isJsonObject(value)) {
    const keys = sortKeys ? Object.keys(value).sort(compareCodePoints) : keysOf(value);
    if (keys.length === 0) return "{}";
    const members = keys.map(
      (key) => `${quoted(key)}${colon}${emit(value[key], indent, sortKeys, inner)}`,
    );
    return `{${open}${members.join(comma)}${close}}`;
  }
  return scalar(value);
}

/**
 * The canonical JSON text of a value: keys sorted by code point, no
 * whitespace, numbers and strings spelled as Python spells them. It breaks ties
 * in the canonical order; Python's `timeskeleton.canonical_json` gives the same
 * text.
 */
export function canonicalJson(value: Lossless<Json>): string {
  return emit(value, null, true, "");
}

/**
 * The compact JSON text of a value: no whitespace, every object's keys in
 * their own order (the written order for a value read by `parseJson`), numbers
 * and strings spelled as Python spells them, as `json.dumps(value,
 * separators=(",", ":"), ensure_ascii=False)` does. `parseJson` reads it back
 * to an equal value.
 *
 * @throws {RangeError} for a non-finite number or a string with a lone surrogate.
 * @throws {TypeError} for a value that is not JSON.
 */
export function compactJson(value: Lossless<Json>): string {
  return emit(value, null, false, "");
}

/**
 * Return the standard text of any JSON value.
 *
 * The value is put in `canonicalOrder`, then written with two-space
 * indentation and a final newline, characters unescaped, every float spelled as
 * Python's `repr` spells it (a plain number with a fractional part, a
 * `JsonFloat`) and every integer without a decimal point (a plain integral
 * number, a `bigint`). Python's `timeskeleton.dumps` writes the same bytes.
 *
 * @throws {RangeError} for a non-finite number or a string with a lone surrogate.
 * @throws {TypeError} for a value that is not JSON, or a collection that cannot be put in canonical order.
 */
export function dumps(value: unknown): string {
  return `${emit(canonicalOrder(value), "  ", false, "")}\n`;
}

// -- the canonical order ------------------------------------------------------------

/** Compare strings by Unicode code point, not by UTF-16 code unit. */
export function compareCodePoints(left: string, right: string): number {
  let i = 0;
  let j = 0;
  while (i < left.length && j < right.length) {
    const a = left.codePointAt(i) as number;
    const b = right.codePointAt(j) as number;
    if (a !== b) return a < b ? -1 : 1;
    i += a > 0xffff ? 2 : 1;
    j += b > 0xffff ? 2 : 1;
  }
  if (i < left.length) return 1;
  return j < right.length ? -1 : 0;
}

/** An exact rational number with a positive denominator. */
export interface Rational {
  readonly numerator: bigint;
  readonly denominator: bigint;
}

function gcd(left: bigint, right: bigint): bigint {
  let a = left < 0n ? -left : left;
  let b = right < 0n ? -right : right;
  while (b !== 0n) [a, b] = [b, a % b];
  return a;
}

export function rational(numerator: bigint, denominator: bigint): Rational {
  const divisor = gcd(numerator, denominator) || 1n;
  return { numerator: numerator / divisor, denominator: denominator / divisor };
}

/** The exact value of a double: every finite double is a dyadic rational. */
function doubleRational(value: number): Rational {
  if (Number.isInteger(value)) return rational(BigInt(value), 1n);
  const view = new DataView(new ArrayBuffer(8));
  view.setFloat64(0, value);
  const bits = view.getBigUint64(0);
  const negative = bits >> 63n === 1n;
  const exponent = Number((bits >> 52n) & 0x7ffn);
  const fraction = bits & 0xfffffffffffffn;
  const mantissa = exponent === 0 ? fraction : fraction | (1n << 52n);
  const power = (exponent === 0 ? 1 : exponent) - 1075;
  const signed = negative ? -mantissa : mantissa;
  return power >= 0
    ? rational(signed << BigInt(power), 1n)
    : rational(signed, 1n << BigInt(-power));
}

/**
 * The integer a JSON number states, or `null` if it is none.
 *
 * An integral float counts as the integer it equals, as in Python.
 */
export function jsonInteger(value: unknown): bigint | null {
  if (typeof value === "bigint") return value;
  const number = value instanceof JsonFloat ? value.value : value;
  return typeof number === "number" && Number.isInteger(number) ? BigInt(number) : null;
}

/** The exact value of any JSON number, or `null` if the value is no number. */
export function exactNumber(value: unknown): Rational | null {
  if (typeof value === "bigint") return rational(value, 1n);
  if (value instanceof JsonFloat) return doubleRational(value.value);
  if (typeof value === "number" && Number.isFinite(value)) return doubleRational(value);
  return null;
}

function exact(coordinate: unknown): Rational {
  const value = isJsonObject(coordinate) ? coordinate.value : undefined;
  if (Array.isArray(value) && value.length === 2) {
    const [numerator, denominator] = value.map(jsonInteger);
    if (numerator !== null && numerator !== undefined && denominator && denominator !== 0n) {
      return rational(numerator, denominator);
    }
  }
  const result = exactNumber(value);
  if (result === null) throw new TypeError(`not a coordinate: ${String(coordinate)}`);
  return result;
}

function compareExact(left: unknown, right: unknown): number {
  const a = exact(left);
  const b = exact(right);
  const sign = a.denominator * b.denominator > 0n ? 1n : -1n;
  const difference = (a.numerator * b.denominator - b.numerator * a.denominator) * sign;
  return difference < 0n ? -1 : difference > 0n ? 1 : 0;
}

function text(member: unknown): string {
  if (typeof member !== "string") throw new TypeError(`not a string: ${String(member)}`);
  return member;
}

/** Order by the first comparison that does not tie. */
function by<T>(...comparisons: ((left: T, right: T) => number)[]) {
  return (left: T, right: T): number => {
    for (const compare of comparisons) {
      const result = compare(left, right);
      if (result !== 0) return result;
    }
    return 0;
  };
}

type Entry = [string, unknown];

function member(entry: unknown, key: string): unknown {
  return isJsonObject(entry) ? entry[key] : undefined;
}

function sortedObject(value: JsonObject, compare: (a: Entry, b: Entry) => number): JsonObject {
  const entries: Entry[] = keysOf(value).map((key) => [key, value[key]]);
  return objectFrom(entries.sort(compare));
}

function orderTimeline(manifest: JsonObject): void {
  if (isJsonObject(manifest.children)) {
    for (const child of Object.values(manifest.children)) {
      const timeline = member(child, "timeline");
      if (isJsonObject(timeline)) orderTimeline(timeline);
    }
    manifest.children = sortedObject(
      manifest.children,
      by<Entry>(
        (a, b) => compareExact(member(a[1], "offset"), member(b[1], "offset")),
        (a, b) => compareCodePoints(a[0], b[0]),
      ),
    );
  }
  if (Array.isArray(manifest.conversion_maps)) {
    manifest.conversion_maps.sort((a, b) =>
      compareCodePoints(text(member(a, "id")), text(member(b, "id"))),
    );
  }
  if (Array.isArray(manifest.regions)) {
    manifest.regions.sort(
      by<unknown>(
        (a, b) => compareExact(member(a, "start"), member(b, "start")),
        (a, b) => compareExact(member(a, "end"), member(b, "end")),
        (a, b) => compareCodePoints(text(member(a, "name")), text(member(b, "name"))),
      ),
    );
  }
  const flow = manifest.flow_control;
  if (!isJsonObject(flow)) return;
  const json = (a: unknown, b: unknown) =>
    compareCodePoints(canonicalJson(a as Lossless<Json>), canonicalJson(b as Lossless<Json>));
  if (Array.isArray(flow.breaks)) {
    flow.breaks.sort(
      by<unknown>((a, b) => compareExact(member(a, "coordinate"), member(b, "coordinate")), json),
    );
  }
  if (Array.isArray(flow.jumps)) {
    flow.jumps.sort(
      by<unknown>(
        (a, b) => compareExact(member(a, "from_coordinate"), member(b, "from_coordinate")),
        (a, b) => compareExact(member(a, "to_coordinate"), member(b, "to_coordinate")),
        json,
      ),
    );
  }
  if (isJsonObject(flow.markers)) {
    flow.markers = sortedObject(flow.markers, (a, b) => compareCodePoints(a[0], b[0]));
  }
}

/**
 * Return a deep copy of `value` with its manifest ordered.
 *
 * A top-level `timeline` orders that timeline manifest. Any other JSON value
 * is copied unchanged. Python's
 * `timeskeleton.canonical_order` gives the same order.
 *
 * @throws {TypeError} if a collection holds an entry whose ordering members are missing or of the wrong type.
 */
export function canonicalOrder<T>(value: T): T {
  const result = clone(value);
  const timeline = member(result, "timeline");
  if (isJsonObject(timeline)) orderTimeline(timeline);
  return result;
}
