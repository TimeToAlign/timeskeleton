/**
 * The JSON writers. Every writer spells a value as Python's `json.dumps`
 * spells it: every character unescaped except `"`, `\` and the control
 * characters, a float always as a float (`2.0`, `1e-07`) with the digits of
 * Python's `repr`, an integer never with a decimal point or an exponent.
 * `compactJson` keeps each object's key order, `canonicalJson` sorts the keys
 * by Unicode code point, and `emit` is the layout both share with the
 * standard writer (`dumps`, in `../manifest/order.ts`). `spell` quotes a value
 * as the validator's messages do.
 */

import { isJsonObject, type Json, JsonFloat, keysOf, type Lossless } from "./value.js";

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

/**
 * Write a value with Python's `json.dumps` layout: `indent` `null` for no
 * whitespace, or the indentation of one level; `sortKeys` to sort every
 * object's keys by code point, else to keep their order; `depth` the
 * indentation the value starts at.
 */
export function emit(
  value: unknown,
  indent: string | null,
  sortKeys: boolean,
  depth: string,
): string {
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
 * Spell a value as a message quotes it: a number as the standard writer
 * spells it, an array as its items separated by `, ` within brackets (`[32,
 * 1]`, as Python's `repr` spells a list), anything else as compact JSON.
 * Python spells numbers and arrays the same way.
 */
export function spell(value: unknown): string {
  if (Array.isArray(value)) return `[${value.map(spell).join(", ")}]`;
  if (typeof value === "number" || typeof value === "bigint" || value instanceof JsonFloat) {
    return scalar(value);
  }
  return value === undefined ? "undefined" : emit(value, null, false, "");
}
