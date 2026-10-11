import { spawnSync } from "node:child_process";
import { describe, expect, it } from "vitest";
import {
  canonicalOrder,
  compactJson,
  dumps,
  isJsonFloat,
  isJsonObject,
  type Json,
  JsonFloat,
  type Lossless,
  migrate,
  parse,
  parseJson,
  SchemaValidationError,
  split,
  validate,
} from "../src/index.js";
import {
  fixtureFileNames,
  fixtureText,
  migrationText,
  rejectionFileNames,
  rejectionText,
} from "./fixtures.js";

type JsonObject = Record<string, unknown>;

// Shared with the Python suite, character for character.
const NUMBER_CORPUS =
  "[0.1, 2.0, 1e-07, 1e+16, 123456789012345678, -0.0, 5e-324, " +
  "1.7976931348623157e+308, 1E5, 1.50, -0, 100, 0.0001, 1e-05, " +
  '1000000000000000.0, "\\u00e9", "\\ud83d\\ude00", "\\ufb00", ' +
  '"a\\"b\\\\c\\n\\u0001\\u001f"]';
const NUMBER_CORPUS_TEXT = [
  "[",
  "  0.1,",
  "  2.0,",
  "  1e-07,",
  "  1e+16,",
  "  123456789012345678,",
  "  -0.0,",
  "  5e-324,",
  "  1.7976931348623157e+308,",
  "  100000.0,",
  "  1.5,",
  "  0,",
  "  100,",
  "  0.0001,",
  "  1e-05,",
  "  1000000000000000.0,",
  '  "\u{e9}",',
  '  "\u{1F600}",',
  '  "\u{FB00}",',
  '  "a\\"b\\\\c\\n\\u0001\\u001f"',
  "]",
  "",
].join("\n");

function standardFiles(): [string, string][] {
  return [
    ...fixtureFileNames("0.2.1").map((file): [string, string] => [
      `0.2.1/${file}`,
      fixtureText(file.slice(0, -5), "0.2.1"),
    ]),
    ...rejectionFileNames("0.2.1").map((file): [string, string] => [
      `rejections/${file}`,
      rejectionText(file, "0.2.1"),
    ]),
    ["0.2.0-to-0.2.1/after.json", migrationText("0.2.0-to-0.2.1", "after")],
    ...fixtureFileNames("0.3.0").map((file): [string, string] => [
      `0.3.0/${file}`,
      fixtureText(file.slice(0, -5), "0.3.0"),
    ]),
    ...rejectionFileNames("0.3.0").map((file): [string, string] => [
      `rejections/0.3.0/${file}`,
      rejectionText(file, "0.3.0"),
    ]),
    ["0.2.1-to-0.3.0/after.json", migrationText("0.2.1-to-0.3.0", "after")],
    ...fixtureFileNames("0.4.0").map((file): [string, string] => [
      `0.4.0/${file}`,
      fixtureText(file.slice(0, -5), "0.4.0"),
    ]),
    ...rejectionFileNames("0.4.0").map((file): [string, string] => [
      `rejections/0.4.0/${file}`,
      rejectionText(file, "0.4.0"),
    ]),
    ["0.3.0-to-0.4.0/after.json", migrationText("0.3.0-to-0.4.0", "after")],
  ];
}

describe("the standard writer", () => {
  it("round-trips all 199 standard files", () => {
    expect(standardFiles().length).toBe(16 + 34 + 1 + (20 + 45 + 1) + (34 + 47 + 1));
  });

  it.each(standardFiles())("round-trips %s byte for byte", (_name, text) => {
    expect(dumps(parseJson(text))).toBe(text);
  });

  it("writes the number and string corpus exactly as Python does", () => {
    expect(dumps(parseJson(NUMBER_CORPUS))).toBe(NUMBER_CORPUS_TEXT);
  });

  it("spells 2000 doubles exactly as Python's repr", () => {
    // A deterministic xorshift64 sequence.
    let state = 0x9e3779b97f4a7c15n;
    const view = new DataView(new ArrayBuffer(8));
    const hexes: string[] = [];
    const values: number[] = [];
    while (values.length < 2000) {
      state ^= (state << 13n) & 0xffffffffffffffffn;
      state ^= state >> 7n;
      state ^= (state << 17n) & 0xffffffffffffffffn;
      // Odd draws are raw bit patterns (every exponent, subnormals included);
      // even draws scatter around the switch between fixed and exponent notation.
      view.setFloat64(0, (Number(state >> 11n) / 2 ** 53) * 10 ** (Number(state % 44n) - 22));
      if (hexes.length % 2 === 1) view.setBigUint64(0, state);
      const value = view.getFloat64(0);
      if (!Number.isFinite(value)) continue;
      values.push(value);
      hexes.push(view.getBigUint64(0).toString(16).padStart(16, "0"));
    }
    const script = [
      "import json, struct, sys",
      "hexes = json.load(sys.stdin)",
      "print(json.dumps([repr(struct.unpack('>d', bytes.fromhex(h))[0]) for h in hexes]))",
    ].join("\n");
    const python = spawnSync("python3", ["-I", "-c", script], {
      input: JSON.stringify(hexes),
      encoding: "utf8",
    });
    expect(python.status, python.stderr).toBe(0);
    const expected = JSON.parse(python.stdout) as string[];
    const spelled = values.map((value) => {
      const number = Number.isInteger(value) ? new JsonFloat(value) : value;
      return dumps(number).trimEnd();
    });
    expect(spelled).toEqual(expected);
  });
});

describe("parseJson", () => {
  it("keeps integers exact and floats floats", () => {
    const [half, two, big, minusZeroInteger, minusZero, exponent] = parseJson(
      "[0.5, 2.0, 123456789012345678, -0, -0.0, 1E5]",
    ) as unknown[];
    expect(half).toBe(0.5);
    expect(two).toEqual(new JsonFloat(2));
    expect(big).toBe(123456789012345678n);
    expect(Object.is(minusZeroInteger, 0)).toBe(true);
    expect(minusZero).toBeInstanceOf(JsonFloat);
    expect(Object.is((minusZero as JsonFloat).value, -0)).toBe(true);
    expect(exponent).toEqual(new JsonFloat(100000));
  });

  it("keeps the written order of array-index keys", () => {
    const text = '{\n  "b": 1,\n  "10": 2,\n  "2": 3\n}\n';
    const value = parseJson(text) as JsonObject;
    expect(Object.keys(value)).toEqual(["2", "10", "b"]);
    expect(dumps(value)).toBe(text);
  });

  it("refuses text that is not one JSON value", () => {
    for (const text of ["", "[1,]", "{1: 2}", "01", "[1] 2", "nul"]) {
      expect(() => parseJson(text), text).toThrow(SyntaxError);
    }
    expect(() => parseJson("1e400")).toThrow(RangeError);
  });
});

describe("integer boundaries", () => {
  it.each([9007199254740993n, 9223372036854775807n])(
    "validates, migrates and writes %s exactly",
    (value) => {
      const manifest = parseJson(fixtureText("discrete_logical", "0.4.0")) as JsonObject;
      const timeline = manifest.timeline as JsonObject;
      (timeline.length as JsonObject).value = value;
      validate(manifest);
      const result = migrate(manifest) as unknown as JsonObject;
      expect(((result.timeline as JsonObject).length as JsonObject).value).toBe(value);
      expect(dumps(result)).toContain(`"value": ${value}\n`);
    },
  );
});

describe("canonical order", () => {
  it("orders array-index marker names by code point and writes them so", () => {
    const envelope = {
      manifest: {
        timelines: {
          t: { flow_control: { breaks: [], jumps: [], markers: { a: 1, "2": 2, "10": 3 } } },
        },
      },
    };
    const text = dumps(envelope);
    expect(text.indexOf('"10"')).toBeLessThan(text.indexOf('"2"'));
    expect(text.indexOf('"2"')).toBeLessThan(text.indexOf('"a"'));
    expect(dumps(parseJson(text))).toBe(text);
  });

  it("copies, and leaves a value that is no manifest or envelope unchanged", () => {
    const value = parseJson('{"b": [3, 1], "a": {"manifest": 1}}');
    const ordered = canonicalOrder(value);
    expect(ordered).not.toBe(value);
    expect(dumps(ordered)).toBe(
      '{\n  "b": [\n    3,\n    1\n  ],\n  "a": {\n    "manifest": 1\n  }\n}\n',
    );
  });

  it("refuses a collection it cannot order", () => {
    const envelope = {
      manifest: { timelines: { a: { regions: [{ name: "r" }, { name: "s" }] } } },
    };
    expect(() => dumps(envelope)).toThrow(TypeError);
  });
});

describe("values the writer refuses", () => {
  it.each([["\u{D800}"], [{ "\u{DFFF}": 1 }], [Number.NaN], [Number.POSITIVE_INFINITY]])(
    "refuses %s",
    (value) => {
      expect(() => dumps([value])).toThrow(RangeError);
    },
  );

  it("refuses what is no JSON value", () => {
    expect(() => dumps([undefined])).toThrow(TypeError);
  });
});

describe("parse", () => {
  it("reads and validates an envelope", () => {
    const envelope = parse(fixtureText("continuous_physical", "0.2.1")) as unknown as JsonObject;
    expect((envelope.meta as JsonObject).schema_version).toBe("0.2.1");
    const timelines = (envelope.manifest as JsonObject).timelines as JsonObject;
    const timeline = Object.values(timelines)[0] as JsonObject;
    const offsets = Object.values(timeline.children as JsonObject).map(
      (child) => ((child as JsonObject).offset as JsonObject).value,
    );
    expect(offsets).toEqual([0.5, new JsonFloat(6)]);
    expect(isJsonFloat(offsets[1])).toBe(true);
  });

  it.each(rejectionFileNames("0.2.1"))("refuses %s at its stored path", (name) => {
    const testCase = parseJson(rejectionText(name, "0.2.1")) as JsonObject;
    try {
      parse(compactJson(testCase.document as Lossless<Json>));
    } catch (error) {
      expect(error).toBeInstanceOf(SchemaValidationError);
      expect((error as SchemaValidationError).path).toEqual(testCase.path);
      return;
    }
    throw new Error("envelope was accepted");
  });
});

describe("JsonFloat", () => {
  it("is a frozen class told apart by instanceof and isJsonFloat", () => {
    const two = new JsonFloat(2);
    expect(Object.isFrozen(two)).toBe(true);
    expect(two instanceof JsonFloat).toBe(true);
    expect(isJsonFloat(two)).toBe(true);
    expect(isJsonFloat(2)).toBe(false);
    expect(isJsonFloat({ value: 2 })).toBe(false);
    expect(isJsonObject(two)).toBe(false);
    expect(isJsonObject({ value: 2 })).toBe(true);
    expect(() => new JsonFloat(Number.NaN)).toThrow(RangeError);
  });
});

function atoms(value: Lossless<Json>, into: Lossless<Json>[] = []): Lossless<Json>[] {
  into.push(value);
  if (Array.isArray(value)) for (const item of value) atoms(item, into);
  else if (isJsonObject(value))
    for (const item of Object.values(value)) atoms(item as Lossless<Json>, into);
  return into;
}

describe("compactJson", () => {
  it("is a fixpoint for every value nested in every 0.2.1 fixture", () => {
    let count = 0;
    for (const file of fixtureFileNames("0.2.1")) {
      for (const atom of atoms(parseJson(fixtureText(file.slice(0, -5), "0.2.1")))) {
        const text = compactJson(atom);
        expect(compactJson(parseJson(text))).toBe(text);
        count++;
      }
    }
    expect(count).toBeGreaterThan(0);
  });

  it("keeps array-index keys in their written order", () => {
    expect(compactJson(parseJson('{"b": 1, "10": 2.0, "2": [1e-07]}'))).toBe(
      '{"b":1,"10":2.0,"2":[1e-07]}',
    );
  });

  it("equals Python's compact text for every 0.2.1 fixture and rejection", () => {
    const files = [
      ...fixtureFileNames("0.2.1").map((file) => fixtureText(file.slice(0, -5), "0.2.1")),
      ...rejectionFileNames("0.2.1").map((file) => rejectionText(file, "0.2.1")),
    ];
    const script = [
      "import json, sys",
      "texts = json.loads(sys.stdin.buffer.read().decode('utf-8'))",
      "out = [json.dumps(json.loads(t), separators=(',', ':'), ensure_ascii=False) for t in texts]",
      "sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode('utf-8'))",
    ].join("\n");
    const python = spawnSync("python3", ["-I", "-c", script], {
      input: JSON.stringify(files),
      encoding: "utf8",
    });
    expect(python.status, python.stderr).toBe(0);
    expect(files.map((text) => compactJson(parseJson(text)))).toEqual(
      JSON.parse(python.stdout) as string[],
    );
  });
});

describe("parse, migrate, dumps", () => {
  it("gives the Python migration's 0.4.0 after.json", () => {
    const before = parse(migrationText("0.3.0-to-0.4.0", "before"));
    expect(dumps(migrate(before))).toBe(migrationText("0.3.0-to-0.4.0", "after"));
  });

  it.each(fixtureFileNames("0.3.0"))("splits and migrates every member of %s", (file) => {
    const envelope = parse(fixtureText(file.slice(0, -5), "0.3.0"));
    for (const part of split(envelope)) {
      const result = migrate(part) as unknown as JsonObject;
      const rootId = (result.timeline as JsonObject).id;
      const expectedFile = fixtureFileNames("0.4.0").find((name) => {
        const expected = parseJson(fixtureText(name.slice(0, -5), "0.4.0")) as JsonObject;
        return (expected.timeline as JsonObject).id === rootId;
      });
      expect(expectedFile).toBeDefined();
      const expected = parseJson(
        fixtureText((expectedFile as string).slice(0, -5), "0.4.0"),
      ) as JsonObject;
      (result.meta as JsonObject).generator = (expected.meta as JsonObject).generator;
      expect(dumps(result)).toBe(dumps(expected));
    }
  });
});
