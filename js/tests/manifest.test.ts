import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { JsonSyntaxError, parseJson } from "../src/json/parse.js";
import type { JsonObject } from "../src/json/value.js";
import {
  isJsonFloat,
  isJsonObject,
  type Json,
  JsonFloat,
  type Lossless,
} from "../src/json/value.js";
import { canonicalJson, compactJson } from "../src/json/write.js";
import { canonicalOrder, dumps } from "../src/manifest/order.js";
import { parse, validate } from "../src/validate.js";
import {
  bundle,
  fixtureDirectory,
  fixtureFiles,
  fixtureText,
  manifest,
  rejectionFileNames,
  rejectionText,
  repositoryRoot,
  timeline,
  warningFileNames,
  warningText,
} from "./fixtures.js";

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
    ...fixtureFiles().map((file): [string, string] => [file, fixtureText(file)]),
    ...rejectionFileNames().map((file): [string, string] => [
      `rejections/${file}`,
      rejectionText(file),
    ]),
    ...warningFileNames().map((file): [string, string] => [`warnings/${file}`, warningText(file)]),
  ];
}

describe("the standard writer", () => {
  it.each(standardFiles())("round-trips %s byte for byte", (_name, text) => {
    expect(dumps(parseJson(text))).toBe(text);
  });

  it("writes every standard file, keys and unordered arrays reversed, as Python does", () => {
    // A rejection or warning case holds its manifest under `manifest`, which
    // the canonical order does not reach, so only its keys are reversed.
    const reversed = standardFiles().map(([name, text]) =>
      compactJson(reverse(parseJson(text), false, !/^(rejections|warnings)\//.test(name))),
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

  it("refuses text that is not one JSON value where it breaks", () => {
    const refusals = [
      "",
      "[1,]",
      "{1: 2}",
      "01",
      "[1] 2",
      "nul",
      "[1, 2",
      '"abc',
      '["\\x"]',
      '{\n  "a": ,\n}',
      '{\n  "a": 1\n  "b": 2\n}',
    ];
    const read = refusals.map((text) => {
      try {
        parseJson(text);
        return null;
      } catch (error) {
        if (!(error instanceof JsonSyntaxError)) throw error;
        expect(error).toBeInstanceOf(SyntaxError);
        expect(error.name).toBe("JsonSyntaxError");
        return [error.message, error.offset, error.line, error.column];
      }
    });
    expect(read).toEqual([
      ["unexpected end at line 1, column 1 of the JSON text", 0, 1, 1],
      ["unexpected character at line 1, column 4 of the JSON text", 3, 1, 4],
      ["expected a string key at line 1, column 2 of the JSON text", 1, 1, 2],
      ["unexpected text after the JSON value at line 1, column 2 of the JSON text", 1, 1, 2],
      ["unexpected text after the JSON value at line 1, column 5 of the JSON text", 4, 1, 5],
      ["unexpected character at line 1, column 1 of the JSON text", 0, 1, 1],
      ['expected "]" at line 1, column 6 of the JSON text', 5, 1, 6],
      ["unterminated string at line 1, column 5 of the JSON text", 4, 1, 5],
      ["malformed string at line 1, column 2 of the JSON text", 1, 1, 2],
      ["unexpected character at line 2, column 8 of the JSON text", 9, 2, 8],
      ['expected "}" at line 3, column 3 of the JSON text', 13, 3, 3],
    ]);
    expect(() => parseJson("1e400")).toThrow(RangeError);
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
    const value = manifest([timeline("b"), timeline("a")]);
    const given = compactJson(value as Lossless<Json>);
    const ordered = canonicalOrder(value);
    expect((ordered.timelines as JsonObject[]).map((root) => root.id)).toEqual(["a", "b"]);
    expect(compactJson(value as Lossless<Json>)).toBe(given);
    const other = parseJson('{"b": [3, 1], "timeline": {"regions": [{"id": "z"}, {"id": "a"}]}}');
    expect(compactJson(canonicalOrder(other))).toBe(
      '{"b":[3,1],"timeline":{"regions":[{"id":"z"},{"id":"a"}]}}',
    );
  });

  it("refuses a collection it cannot order", () => {
    const value = { timelines: [{ id: "t", regions: [{ id: "r" }, { id: "s" }] }] };
    expect(() => dumps(value)).toThrow(TypeError);
    const members = { timelines: [], groups: [{ id: "g", members: ["a", 5] }] };
    expect(() => canonicalOrder(members)).toThrow(TypeError);
  });

  it("resolves every tie", () => {
    const result = canonicalOrder(tiedManifest());
    validate(result);
    const root = (result.timelines as unknown as JsonObject[])[0] as JsonObject;
    const ids = (entries: unknown) => (entries as JsonObject[]).map((entry) => entry.id);
    expect(ids(root.children)).toEqual(["b", "a", "m", "z"]);
    expect(ids((root.children as JsonObject[])[3]?.children)).toEqual(["x", "y"]);
    expect(ids(root.conversion_maps)).toEqual(["B", "B2", "a2", "\u{FB00}", "\u{1F600}"]);
    expect(ids(root.regions)).toEqual(["rd", "rc", "ra", "rb"]);
    const flow = root.flow_control as JsonObject;
    expect(ids(flow.breaks)).toEqual(["kz", "ka", "kb"]);
    expect(ids(flow.jumps)).toEqual(["je", "js", "jd", "jj"]);
    expect(ids(flow.markers)).toEqual(["starting", "Coda", "\u{E9}", "\u{FB00}!", "\u{1F600}!"]);
  });

  it("compares bare values by exact value", () => {
    const take = timeline("take", "seconds", 10.5, {
      children: [
        timeline("late", "seconds", 1.5, { offset: 2 }),
        timeline("tie-b", "seconds", 1.5, { offset: 0.625 }),
        timeline("tie-a", "seconds", 1.5, { offset: 0.625 }),
        timeline("early", "seconds", 1.5, { offset: new JsonFloat(0) }),
      ],
      regions: [
        { id: "r2", start: 1, end: 2.5 },
        { id: "r1", start: new JsonFloat(1), end: 2 },
      ],
    });
    const result = (canonicalOrder(manifest([take])).timelines as JsonObject[])[0] as JsonObject;
    const ids = (entries: unknown) => (entries as JsonObject[]).map((entry) => entry.id);
    expect(ids(result.children)).toEqual(["early", "tie-a", "tie-b", "late"]);
    expect(ids(result.regions)).toEqual(["r1", "r2"]);
    const mixed = canonicalOrder({
      timelines: [
        {
          id: "q",
          children: [
            { id: "c", offset: [5, 8] },
            { id: "b", offset: 0.625 },
            { id: "a", offset: [2, 1] },
          ],
        },
      ],
    });
    expect(ids(mixed.timelines[0]?.children)).toEqual(["b", "c", "a"]);
  });

  it("orders roots, groups and members, and keeps display orders", () => {
    const value = bundle();
    (value.timelines as JsonObject[]).reverse();
    const groups = value.groups as JsonObject[];
    groups.reverse();
    for (const group of groups) (group.members as string[]).reverse();
    (value.graphical as JsonObject).order = {
      group_2: ["excerpt", "page"],
      group_1: ["performance", "score"],
    };
    const given = compactJson(value as Lossless<Json>);
    const result = canonicalOrder(value);
    expect(compactJson(value as Lossless<Json>)).toBe(given);
    expect((result.timelines as JsonObject[]).map((root) => root.id)).toEqual([
      "annotations",
      "page",
      "performance",
      "recording",
      "score",
    ]);
    expect((result.groups as JsonObject[]).map((group) => group.id)).toEqual([
      "group_1",
      "group_2",
    ]);
    expect((result.groups as JsonObject[]).map((group) => group.members)).toEqual([
      ["performance", "score"],
      ["excerpt", "page"],
    ]);
    expect((result.graphical as JsonObject).order).toEqual({
      group_2: ["excerpt", "page"],
      group_1: ["performance", "score"],
    });
    validate(result);
  });

  it("orders members by code point", () => {
    const value = { timelines: [], groups: [{ id: "g", members: ["\u{1F600}", "\u{FB00}", "b"] }] };
    expect(canonicalOrder(value).groups[0]?.members).toEqual(["b", "\u{FB00}", "\u{1F600}"]);
  });
});

/** A manifest with ties at every key level, own-axis values in mixed forms. */
function tiedManifest(): JsonObject {
  const regions: [string, unknown, unknown][] = [
    ["rb", [2, 1], [6, 1]],
    ["ra", [2, 1], [6, 1]],
    ["rc", [2, 1], [4, 1]],
    ["rd", [5, 8], [2, 3]],
  ];
  const at = (offset: unknown) => ({ offset });
  return manifest([
    timeline("piece", "quarters", [16, 1], {
      children: [
        timeline("z", "quarters", [8, 1], {
          ...at([1, 1]),
          children: [
            timeline("y", "quarters", [2, 1], at([1, 1])),
            timeline("x", "quarters", [2, 1], at([0, 1])),
          ],
        }),
        timeline("m", "quarters", [8, 1], at([1, 1])),
        timeline("b", "quarters", [8, 1], at([5, 8])),
        timeline("a", "quarters", [8, 1], at([2, 3])),
      ],
      conversion_maps: ["\u{1F600}", "\u{FB00}", "B2", "a2", "B"].map((id) => ({
        type: "ShiftMap",
        id,
        source_unit: "quarters",
        target_unit: null,
        offset: [1, 2],
      })),
      regions: regions.map(([id, start, end]) => ({ id, start, end })),
      flow_control: {
        breaks: [
          { id: "kb", coordinate: [12, 1] },
          { id: "ka", coordinate: [12, 1] },
          { id: "kz", coordinate: [5, 8] },
        ],
        jumps: [
          { id: "jj", from_coordinate: [8, 1], to_coordinate: [2, 1], target: "Coda" },
          { id: "jd", from_coordinate: [8, 1], to_coordinate: [2, 1] },
          { id: "js", from_coordinate: [8, 1], to_coordinate: [2, 3] },
          { id: "je", from_coordinate: [5, 8], to_coordinate: [2, 1] },
        ],
        markers: (
          [
            ["\u{1F600}!", [2, 1]],
            ["\u{FB00}!", [2, 1]],
            ["\u{E9}", [2, 1]],
            ["Coda", [2, 1]],
            ["starting", [5, 8]],
          ] as const
        ).map(([id, coordinate]) => ({ id, coordinate })),
      },
    }),
  ]);
}

/**
 * The value with every object's keys reversed, and the items of every array
 * whose order carries no meaning: `timelines` and `groups`, a group's
 * `members`, a timeline's `children`, `conversion_maps` and `regions`, and
 * the `breaks`, `jumps` and `markers` of its `flow_control`.
 */
function reverse(value: unknown, unordered = false, arrays = true): Lossless<Json> {
  if (Array.isArray(value)) {
    const items = value.map((item) => reverse(item, false, arrays));
    return unordered ? items.reverse() : items;
  }
  if (isJsonObject(value)) {
    const members = !arrays
      ? []
      : "timelines" in value
        ? ["timelines", "groups"]
        : "unit" in value && "length" in value
          ? ["children", "conversion_maps", "regions"]
          : "breaks" in value && "jumps" in value && "markers" in value
            ? ["breaks", "jumps", "markers"]
            : "members" in value && "id" in value
              ? ["members"]
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
      "    flow = timeline.get('flow_control', {})",
      "    for entry in flow.get('breaks', []) + flow.get('jumps', []):",
      "        texts.append(json.dumps(entry, sort_keys=True, separators=(',', ':'), ensure_ascii=False))",
      "    for child in timeline.get('children', []):",
      "        visit(child)",
      "for name in json.loads(sys.argv[2]):",
      "    value = json.loads((pathlib.Path(sys.argv[1]) / name).read_text(encoding='utf-8'))",
      "    for root in value.get('timelines', []):",
      "        visit(root)",
      "sys.stdout.buffer.write(json.dumps(texts, ensure_ascii=False).encode('utf-8'))",
    ].join("\n");
    const files = fixtureFiles();
    const python = spawnSync(
      "python3",
      ["-I", "-c", script, fixtureDirectory, JSON.stringify(files)],
      { encoding: "utf8" },
    );
    expect(python.status, python.stderr).toBe(0);
    const expected = JSON.parse(python.stdout) as string[];
    const texts: string[] = [];
    const list = (owner: unknown, key: string) =>
      isJsonObject(owner) && Array.isArray(owner[key]) ? (owner[key] as JsonObject[]) : [];
    const visit = (timeline: JsonObject): void => {
      const flow = timeline.flow_control;
      for (const entry of [...list(flow, "breaks"), ...list(flow, "jumps")]) {
        texts.push(canonicalJson(entry as Lossless<Json>));
      }
      for (const child of list(timeline, "children")) visit(child);
    };
    for (const file of files) {
      for (const root of list(parseJson(fixtureText(file)), "timelines")) visit(root);
    }
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
  it("reads and validates a manifest without losing a float", () => {
    const value = parse(
      '{"timeskeleton": "0.7.0", "timelines": [{"id": "take", "unit": "seconds", "length": 12.0,' +
        ' "children": [{"id": "a", "unit": "seconds", "length": 1.5, "offset": 0.5},' +
        ' {"id": "b", "unit": "seconds", "length": 1.5, "offset": 6.0}]}]}',
    ) as unknown as JsonObject;
    const root = (value.timelines as JsonObject[])[0] as JsonObject;
    const offsets = (root.children as JsonObject[]).map((child) => child.offset);
    expect(offsets).toEqual([0.5, new JsonFloat(6)]);
    expect(isJsonFloat(offsets[1])).toBe(true);
    expect(root.length).toEqual(new JsonFloat(12));
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
    for (const file of fixtureFiles()) {
      for (const atom of atoms(parseJson(fixtureText(file)))) {
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

  it("equals Python's compact text for every fixture, rejection and warning case", () => {
    const files = standardFiles().map(([, text]) => text);
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
