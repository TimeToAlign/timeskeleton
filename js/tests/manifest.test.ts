import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  canonicalJson,
  canonicalOrder,
  compactJson,
  dumps,
  FILE_KINDS,
  isJsonFloat,
  isJsonObject,
  type Json,
  JsonFloat,
  type Lossless,
  parse,
  parseJson,
  SCHEMA_VERSION,
  SchemaValidationError,
  validate,
} from "../src/index.js";
import {
  fixtureDirectory,
  fixtureFileNames,
  fixtureText,
  loadFixture,
  rejectionFileNames,
  rejectionText,
  repositoryRoot,
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
    ...FILE_KINDS.flatMap((kind) =>
      fixtureFileNames(SCHEMA_VERSION, kind).map((file): [string, string] => [
        `${kind}/${file}`,
        fixtureText(file.slice(0, -5), SCHEMA_VERSION, kind),
      ]),
    ),
    ...rejectionFileNames().map((file): [string, string] => [
      `rejections/${file}`,
      rejectionText(file),
    ]),
  ];
}

describe("the standard writer", () => {
  it("round-trips all 126 standard files", () => {
    expect(FILE_KINDS.map((kind) => fixtureFileNames(SCHEMA_VERSION, kind).length)).toEqual([
      23, 3, 7,
    ]);
    expect(standardFiles().length).toBe(23 + 3 + 7 + 93);
  });

  it.each(standardFiles())("round-trips %s byte for byte", (_name, text) => {
    expect(dumps(parseJson(text))).toBe(text);
  });

  it("writes every standard file, keys and unordered arrays reversed, as Python does", () => {
    // A rejection case holds its manifest under `manifest`, which the canonical
    // order does not reach, so only its keys are reversed.
    const reversed = standardFiles().map(([name, text]) =>
      compactJson(reverse(parseJson(text), false, !name.startsWith("rejections/"))),
    );
    const script = [
      "import importlib.util, json, sys",
      "spec = importlib.util.spec_from_file_location('manifest', sys.argv[1])",
      "manifest = importlib.util.module_from_spec(spec)",
      "spec.loader.exec_module(manifest)",
      "texts = json.loads(sys.stdin.buffer.read().decode('utf-8'))",
      "out = [manifest.dumps(json.loads(text)) for text in texts]",
      "sys.stdout.buffer.write(json.dumps(out, ensure_ascii=False).encode('utf-8'))",
    ].join("\n");
    const python = spawnSync(
      "python3",
      ["-I", "-c", script, resolve(repositoryRoot, "python/src/timeskeleton/manifest.py")],
      { input: JSON.stringify(reversed), encoding: "utf8" },
    );
    expect(python.status, python.stderr).toBe(0);
    const written = reversed.map((text) => dumps(parseJson(text)));
    expect(written).toEqual(JSON.parse(python.stdout) as string[]);
    expect(written).toEqual(standardFiles().map(([, text]) => text));
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
    expect(compactJson(value as Lossless<Json>)).toBe('{"b":1,"10":2,"2":3}');
  });

  it("refuses text that is not one JSON value", () => {
    for (const text of ["", "[1,]", "{1: 2}", "01", "[1] 2", "nul"]) {
      expect(() => parseJson(text), text).toThrow(SyntaxError);
    }
    expect(() => parseJson("1e400")).toThrow(RangeError);
  });
});

describe("integer boundaries", () => {
  it.each([9007199254740993n, 9223372036854775807n])("validates and writes %s exactly", (value) => {
    const manifest = parseJson(fixtureText("discrete_logical")) as JsonObject;
    const timeline = manifest.timeline as JsonObject;
    (timeline.length as JsonObject).value = value;
    validate(manifest);
    const text = dumps(manifest);
    expect(text).toContain(`"value": ${value}\n`);
    const read = parseJson(text) as JsonObject;
    expect(((read.timeline as JsonObject).length as JsonObject).value).toBe(value);
  });
});

describe("canonical order", () => {
  it("sorts every object by key, array-index keys included", () => {
    const value = parseJson(
      '{"b": 1, "\\ud83d\\ude00": 2, "\\ufb00": 3, "A": {"z": 0, "10": 1, "2": 2}}',
    );
    expect(dumps(value)).toBe(
      [
        "{",
        '  "A": {',
        '    "10": 1,',
        '    "2": 2,',
        '    "z": 0',
        "  },",
        '  "b": 1,',
        '  "\u{FB00}": 3,',
        '  "\u{1F600}": 2',
        "}",
        "",
      ].join("\n"),
    );
  });

  it("copies, and leaves a value that is no manifest unchanged", () => {
    const value = parseJson('{"b": [3, 1], "a": {"timeline": 1}}');
    const ordered = canonicalOrder(value);
    expect(ordered).not.toBe(value);
    expect(compactJson(ordered)).toBe('{"b":[3,1],"a":{"timeline":1}}');
  });

  it("refuses a collection it cannot order", () => {
    const manifest = { timeline: { regions: [{ id: "r" }, { id: "s" }] } };
    expect(() => dumps(manifest)).toThrow(TypeError);
  });

  it("resolves every tie", () => {
    const result = canonicalOrder(tiedManifest());
    validate(result);
    const timeline = result.timeline as unknown as JsonObject;
    const ids = (entries: unknown) => (entries as JsonObject[]).map((entry) => entry.id);
    expect(Object.keys(timeline.children as JsonObject)).toEqual(["z", "m", "b", "a"]);
    expect(ids(timeline.conversion_maps)).toEqual(["B", "B2", "a2", "\u{FB00}", "\u{1F600}"]);
    expect(ids(timeline.regions)).toEqual(["rd", "rc", "ra", "rb"]);
    const flow = timeline.flow_control as JsonObject;
    expect(ids(flow.breaks)).toEqual(["kz", "ka", "kb"]);
    expect(ids(flow.jumps)).toEqual(["je", "js", "jd", "jj"]);
    expect(ids(flow.markers)).toEqual(["start", "Coda", "\u{E9}", "\u{FB00}!", "\u{1F600}!"]);
    const written = (parseJson(dumps(result)) as JsonObject).timeline as JsonObject;
    const children = written.children as Record<string, { timeline: JsonObject }>;
    expect(Object.keys(children)).toEqual(["a", "b", "m", "z"]);
    expect(Object.keys(children.z?.timeline.children as JsonObject)).toEqual(["x", "y"]);
  });
});

function at(numerator: number, denominator = 1): JsonObject {
  return { unit: "quarters", number_type: "fraction", value: [numerator, denominator] };
}

/** The bare fixture, extended with ties at every key level. */
function tiedManifest(): JsonObject {
  const manifest = loadFixture("bare");
  const timeline = manifest.timeline as JsonObject;
  const copyOf = (id: string): JsonObject => ({
    ...(loadFixture("bare").timeline as JsonObject),
    id,
  });

  const nested = copyOf("z");
  nested.children = {
    y: { offset: at(1), timeline: copyOf("y") },
    x: { offset: at(0), timeline: copyOf("x") },
  };
  timeline.children = {
    z: { offset: at(1), timeline: nested },
    m: { offset: at(1), timeline: copyOf("m") },
    b: { offset: at(5, 8), timeline: copyOf("b") },
    a: { offset: at(2, 3), timeline: copyOf("a") },
  };
  timeline.conversion_maps = ["\u{1F600}", "\u{FB00}", "B2", "a2", "B"].map((id) => ({
    type: "ShiftMap",
    id,
    name: id,
    source_unit: "quarters",
    target_unit: null,
    offset: [1, 2],
  }));
  timeline.regions = (
    [
      ["rb", at(2), at(6)],
      ["ra", at(2), at(6)],
      ["rc", at(2), at(4)],
      ["rd", at(5, 8), at(2, 3)],
    ] as const
  ).map(([id, start, end]) => ({ id, name: id, start, end, meta: {} }));
  const flow = timeline.flow_control as JsonObject;
  flow.breaks = (
    [
      ["kb", at(12)],
      ["ka", at(12)],
      ["kz", at(5, 8)],
    ] as const
  ).map(([id, coordinate]) => ({
    id,
    coordinate,
    control_type: "fine",
    condition: "always",
    repeat_count: 1,
    label: null,
    name: null,
    meta: {},
  }));
  flow.jumps = (
    [
      ["jj", at(8), at(2), "Coda"],
      ["jd", at(8), at(2), null],
      ["js", at(8), at(2, 3), null],
      ["je", at(5, 8), at(2), null],
    ] as const
  ).map(([id, from, to, target]) => ({
    id,
    from_coordinate: from,
    to_coordinate: to,
    control_type: "repeat_end",
    condition: "always",
    repeat_count: 1,
    target,
    label: null,
    meta: {},
  }));
  flow.markers = (
    [
      ["\u{1F600}!", at(2)],
      ["\u{FB00}!", at(2)],
      ["\u{E9}", at(2)],
      ["Coda", at(2)],
      ["start", at(5, 8)],
    ] as const
  ).map(([id, coordinate]) => ({ id, name: null, coordinate }));
  return manifest;
}

/**
 * The value with every object's keys reversed, and the items of every array
 * whose order carries no meaning: a timeline's `conversion_maps` and
 * `regions`, and the `breaks`, `jumps` and `markers` of its `flow_control`.
 */
function reverse(value: unknown, unordered = false, arrays = true): Lossless<Json> {
  if (Array.isArray(value)) {
    const items = value.map((item) => reverse(item, false, arrays));
    return unordered ? items.reverse() : items;
  }
  if (isJsonObject(value)) {
    const timeline = arrays && "flow_control" in value && "regions" in value;
    const flow = arrays && "breaks" in value && "jumps" in value && "markers" in value;
    const file = arrays && "timelines" in value;
    const group = arrays && "members" in value && "id" in value;
    const bundle = arrays && "groups" in value && "support_policy" in value;
    const members = timeline
      ? ["conversion_maps", "regions"]
      : flow
        ? Object.keys(value)
        : file
          ? ["timelines"]
          : group
            ? ["members"]
            : bundle
              ? ["groups"]
              : [];
    return Object.fromEntries(
      Object.keys(value)
        .reverse()
        .map((member) => [member, reverse(value[member], members.includes(member), arrays)]),
    ) as Lossless<Json>;
  }
  return value as Lossless<Json>;
}

describe("canonical JSON text", () => {
  it("sorts keys by code point and writes no whitespace", () => {
    const value = {
      "\u{1F600}": { b: true, a: [1, 2.5, null] },
      "\u{FB00}": "\u{FC}",
      "\u{E9}": 1,
      z: "\n",
      a: [],
    };
    expect(canonicalJson(value)).toBe(
      '{"a":[],"z":"\\n","\u{E9}":1,"\u{FB00}":"\u{FC}","\u{1F600}":{"a":[1,2.5,null],"b":true}}',
    );
  });

  it("equals Python's text for every break and jump of every fixture", () => {
    const script = [
      "import json, pathlib, sys",
      "texts = []",
      "def visit(timeline):",
      "    flow = timeline['flow_control']",
      "    for entry in flow['breaks'] + flow['jumps']:",
      "        texts.append(json.dumps(entry, sort_keys=True, separators=(',', ':'), ensure_ascii=False))",
      "    for child in timeline['children'].values():",
      "        visit(child['timeline'])",
      "for path in sorted(pathlib.Path(sys.argv[1]).glob('*.json')):",
      "    visit(json.loads(path.read_text(encoding='utf-8'))['timeline'])",
      "sys.stdout.buffer.write(json.dumps(texts, ensure_ascii=False).encode('utf-8'))",
    ].join("\n");
    const python = spawnSync("python3", ["-I", "-c", script, resolve(fixtureDirectory())], {
      encoding: "utf8",
    });
    expect(python.status, python.stderr).toBe(0);
    const expected = JSON.parse(python.stdout) as string[];
    const texts: string[] = [];
    const visit = (timeline: JsonObject): void => {
      const flow = timeline.flow_control as JsonObject;
      for (const entry of [
        ...(flow.breaks as Lossless<Json>[]),
        ...(flow.jumps as Lossless<Json>[]),
      ]) {
        texts.push(canonicalJson(entry));
      }
      for (const child of Object.values(timeline.children as Record<string, JsonObject>)) {
        visit(child.timeline as JsonObject);
      }
    };
    for (const file of fixtureFileNames()) {
      visit(loadFixture(file.slice(0, -5)).timeline as JsonObject);
    }
    expect(texts.length).toBe(8);
    expect(texts).toEqual(expected);
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
  it("reads and validates a manifest", () => {
    const manifest = parse(fixtureText("continuous_physical")) as unknown as JsonObject;
    expect((manifest.meta as JsonObject).schema_version).toBe("0.7.0");
    const timeline = manifest.timeline as JsonObject;
    const offsets = Object.values(timeline.children as JsonObject).map(
      (child) => ((child as JsonObject).offset as JsonObject).value,
    );
    expect(offsets).toEqual([0.5, new JsonFloat(6)]);
    expect(isJsonFloat(offsets[1])).toBe(true);
  });

  it.each(rejectionFileNames())("refuses %s at its stored path", (name) => {
    const testCase = parseJson(rejectionText(name)) as JsonObject;
    try {
      parse(compactJson(testCase.manifest as Lossless<Json>));
    } catch (error) {
      expect(error).toBeInstanceOf(SchemaValidationError);
      expect((error as SchemaValidationError).path).toEqual(testCase.path);
      return;
    }
    throw new Error("manifest was accepted");
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
  it("is a fixpoint for every value nested in every fixture", () => {
    let count = 0;
    for (const file of fixtureFileNames()) {
      for (const atom of atoms(parseJson(fixtureText(file.slice(0, -5))))) {
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

  it("equals Python's compact text for every fixture and rejection", () => {
    const files = [
      ...fixtureFileNames().map((file) => fixtureText(file.slice(0, -5))),
      ...rejectionFileNames().map((file) => rejectionText(file)),
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
