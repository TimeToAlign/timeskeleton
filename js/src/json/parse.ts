/**
 * The lossless JSON reader. `parseJson` reads any JSON text without losing
 * a number's written kind or an object's key order (see `./value.ts`), and
 * refuses malformed text with a `JsonSyntaxError` that names where the text
 * breaks: its offset, line and column.
 */

import { type Json, JsonFloat, type JsonNumber, type Lossless, objectFrom } from "./value.js";

/**
 * Malformed JSON text: what was expected and where the text breaks.
 *
 * `offset` counts UTF-16 code units from the start of the text; `line` and
 * `column` count from 1, a line ending at each `\n`, the column in UTF-16
 * code units. It is a `SyntaxError`, so a caller catching `SyntaxError`
 * catches it too.
 */
export class JsonSyntaxError extends SyntaxError {
  readonly offset: number;
  readonly line: number;
  readonly column: number;

  constructor(reason: string, text: string, offset: number) {
    const lines = text.slice(0, offset).split("\n");
    const line = lines.length;
    const column = (lines.at(-1) as string).length + 1;
    super(`${reason} at line ${line}, column ${column} of the JSON text`);
    this.name = "JsonSyntaxError";
    this.offset = offset;
    this.line = line;
    this.column = column;
  }
}

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
 * @throws {JsonSyntaxError} if the text is not one JSON value.
 * @throws {RangeError} if a float is beyond the range of a double.
 */
export function parseJson(text: string): Lossless<Json> {
  let index = 0;

  const fail = (reason: string, at = index): never => {
    throw new JsonSyntaxError(reason, text, at);
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
    try {
      return JSON.parse(text.slice(start, index)) as string;
    } catch {
      return fail("malformed string", start);
    }
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
    if (match === null)
      return fail(character === undefined ? "unexpected end" : "unexpected character");
    index += match[0].length;
    return number(match[0]);
  };

  const result = value();
  space();
  if (index !== text.length) fail("unexpected text after the JSON value");
  return result as Lossless<Json>;
}
