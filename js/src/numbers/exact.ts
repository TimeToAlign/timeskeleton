/**
 * Exact values of the numbers a manifest states. Every JSON number and every
 * `[numerator, denominator]` Fraction has one exact rational value (a finite
 * double is a dyadic rational), so values written in different number types
 * compare without rounding, as the canonical order and the validator's
 * containment rules compare them. An integral float counts as the integer it
 * equals, as in Python.
 */

import { JsonFloat } from "../json/value.js";
import { spell } from "../json/write.js";

/** An exact rational number in lowest terms with a positive denominator. */
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

/** The rational `numerator / denominator` in lowest terms; the denominator is positive. */
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

/**
 * The exact value of a bare Number: a JSON number, or a `[numerator,
 * denominator]` pair (an integral float in the pair counts as the integer it
 * equals, as in Python).
 *
 * @throws {TypeError} if the value is no Number.
 */
export function exact(value: unknown): Rational {
  if (Array.isArray(value) && value.length === 2) {
    const [numerator, denominator] = value.map(jsonInteger);
    if (numerator !== null && numerator !== undefined && denominator && denominator > 0n) {
      return rational(numerator, denominator);
    }
  }
  const result = exactNumber(value);
  if (result === null) throw new TypeError(`not a Number: ${spell(value)}`);
  return result;
}

/** Compare two bare Numbers by exact value. */
export function compareExact(left: unknown, right: unknown): number {
  const a = exact(left);
  const b = exact(right);
  const difference = a.numerator * b.denominator - b.numerator * a.denominator;
  return difference < 0n ? -1 : difference > 0n ? 1 : 0;
}
