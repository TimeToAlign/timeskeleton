import { describe, expect, it } from "vitest";
import {
  identityProblems,
  SchemaValidationError,
  schemaDocuments,
  validate,
} from "../src/index.js";
import { loadFixture } from "./fixtures.js";

type JsonObject = Record<string, unknown>;

function at(value: number, unit = "quarters", numberType = "fraction"): JsonObject {
  return { unit, number_type: numberType, value: numberType === "fraction" ? [value, 1] : value };
}

/** `bare` (8 quarters) as a segment line with the given offsets and lengths. */
function segmentLine(segments: Record<string, [number, number]>): JsonObject {
  const manifest = loadFixture("bare");
  const line = manifest.timeline as JsonObject;
  line.is_segment_line = true;
  for (const [key, [offset, length]] of Object.entries(segments)) {
    const segment = {
      ...structuredClone(line),
      id: key,
      name: null,
      is_segment_line: false,
      children: {},
      length: at(length),
    };
    (line.children as JsonObject)[key] = { offset: at(offset), timeline: segment };
  }
  return manifest;
}

const root = (manifest: JsonObject) => manifest.timeline as JsonObject;
const segment = (manifest: JsonObject, key: string) =>
  ((root(manifest).children as JsonObject)[key] as JsonObject).timeline as JsonObject;

function problemsOf(manifest: JsonObject): [unknown, string][] {
  return identityProblems(manifest as never).map((problem) => [problem.path, problem.detail]);
}

describe("segment lines", () => {
  it("require the flag after locked", () => {
    const manifest = (
      schemaDocuments["0.7.0"].timeline as unknown as {
        $defs: { TimelineManifest: { properties: JsonObject; required: string[] } };
      }
    ).$defs.TimelineManifest;
    const keys = Object.keys(manifest.properties);
    expect(keys[keys.indexOf("locked") + 1]).toBe("is_segment_line");
    expect(manifest.properties.is_segment_line).toMatchObject({ type: "boolean" });
    expect(manifest.required).toHaveLength(15);
    expect(manifest.required[manifest.required.indexOf("locked") + 1]).toBe("is_segment_line");
  });

  it("accept contiguous, nested and empty segment lines", () => {
    validate(segmentLine({ a: [0, 3], b: [3, 5] }));
    const nested = segmentLine({ a: [0, 4], b: [4, 4] });
    for (const key of ["a", "b"]) {
      const inner = segment(nested, key);
      inner.is_segment_line = true;
      for (const [leaf, offset] of [
        ["x", 0],
        ["y", 2],
      ] as const) {
        (inner.children as JsonObject)[`${key}${leaf}`] = {
          offset: at(offset),
          timeline: {
            ...structuredClone(inner),
            id: `${key}${leaf}`,
            is_segment_line: false,
            children: {},
            length: at(2),
          },
        };
      }
    }
    validate(nested);
    const empty = segmentLine({});
    root(empty).length = at(0);
    validate(empty);
  });

  it("report a segment of another class", () => {
    const manifest = segmentLine({ a: [0, 3], b: [3, 5] });
    segment(manifest, "b").class = "DiscreteLogicalTimeline";
    expect(problemsOf(manifest)).toEqual([
      [
        ["timeline", "children", "b", "timeline", "class"],
        'segment "b" of segment line "bare" is no ContinuousLogicalTimeline',
      ],
    ]);
  });

  it("report a segment with another flag", () => {
    const manifest = segmentLine({ a: [0, 3], b: [3, 0] });
    segment(manifest, "b").is_segment_line = true;
    root(manifest).length = at(3);
    expect(problemsOf(manifest)).toEqual([
      [
        ["timeline", "children", "b", "timeline", "is_segment_line"],
        'segment "b" of segment line "bare" differs from segment "a" in is_segment_line',
      ],
    ]);
  });

  it.each([
    [{ a: [1, 2], b: [3, 5] }, "a", "does not start at 0"],
    [{ a: [0, 3], b: [4, 4] }, "b", "does not start where the one before it ends"],
    [{ a: [0, 3], b: [2, 6] }, "b", "does not start where the one before it ends"],
  ] as [Record<string, [number, number]>, string, string][])(
    "require contiguous segments from 0 (%j)",
    (segments, key, message) => {
      expect(problemsOf(segmentLine(segments))).toEqual([
        [
          ["timeline", "children", key, "offset"],
          `segment "${key}" of segment line "bare" ${message}`,
        ],
      ]);
    },
  );

  it.each([[{ a: [0, 3], b: [3, 4] }], [{}]] as [Record<string, [number, number]>][])(
    "require the segments %j to end at the length",
    (segments) => {
      expect(problemsOf(segmentLine(segments))).toEqual([
        [["timeline", "length"], 'the segments of segment line "bare" do not end at its length'],
      ]);
    },
  );

  it("visit segments in offset order", () => {
    expect(problemsOf(segmentLine({ z: [0, 3], a: [3, 5] }))).toEqual([]);
    expect(problemsOf(segmentLine({ z: [0, 3], a: [4, 4] })).map(([path]) => path)).toEqual([
      ["timeline", "children", "a", "offset"],
    ]);
  });

  it("compare exact values", () => {
    const seconds = (segments: [string, number, number][]): JsonObject => {
      const manifest = segmentLine({});
      const line = root(manifest);
      Object.assign(line, {
        class: "ContinuousPhysicalTimeline",
        unit: "seconds",
        number_type: "float",
        measure_map: null,
        length: at(1.5, "seconds", "float"),
      });
      for (const [key, offset, size] of segments) {
        (line.children as JsonObject)[key] = {
          offset: at(offset, "seconds", "float"),
          timeline: {
            ...structuredClone(line),
            id: key,
            is_segment_line: false,
            children: {},
            length: at(size, "seconds", "float"),
          },
        };
      }
      return manifest;
    };
    validate(
      seconds([
        ["a", 0.5, 0.25],
        ["b", 0.75, 0.75],
        ["c", 0, 0.5],
      ]),
    );
    const inexact = seconds([
      ["a", 0, 0.1],
      ["b", 0.1, 0.2],
      ["c", 0.3, 1.2],
    ]);
    expect(problemsOf(inexact).map(([path]) => path)).toEqual([
      ["timeline", "children", "c", "offset"],
      ["timeline", "length"],
    ]);
  });

  it("list the problems in the stated order", () => {
    const manifest = segmentLine({ a: [0, 3], b: [4, 3] });
    segment(manifest, "b").class = "DiscreteLogicalTimeline";
    segment(manifest, "b").is_segment_line = true;
    expect(problemsOf(manifest).map(([path]) => path)).toEqual([
      ["timeline", "children", "b", "timeline", "class"],
      ["timeline", "children", "b", "timeline", "is_segment_line"],
      ["timeline", "children", "b", "offset"],
      ["timeline", "length"],
      ["timeline", "children", "b", "timeline", "length"],
    ]);
    try {
      validate(manifest);
      throw new Error("value was accepted");
    } catch (error) {
      expect(error).toBeInstanceOf(SchemaValidationError);
      expect((error as SchemaValidationError).path).toEqual([
        "timeline",
        "children",
        "b",
        "timeline",
        "class",
      ]);
    }
  });

  it("check a descendant segment line at its path", () => {
    const manifest = segmentLine({ a: [0, 8] });
    root(manifest).is_segment_line = false;
    segment(manifest, "a").is_segment_line = true;
    expect(problemsOf(manifest)).toEqual([
      [
        ["timeline", "children", "a", "timeline", "length"],
        'the segments of segment line "a" do not end at its length',
      ],
    ]);
  });

  it("never check a timeline that is no segment line", () => {
    const manifest = segmentLine({ a: [1, 2], b: [5, 1] });
    root(manifest).is_segment_line = false;
    expect(problemsOf(manifest)).toEqual([]);
  });
});

describe("the segment_line fixture", () => {
  // [id, name, is_segment_line, locked, absolute start, length]
  const expected = [
    ["form", "Form", true, false, 0, 32],
    ["a", "A", true, true, 0, 8],
    ["a1", null, false, true, 0, 8],
    ["b", "B", true, true, 8, 12],
    ["b1", "b1", false, true, 8, 6],
    ["b2", "b2", false, true, 14, 6],
    ["c", "C", true, true, 20, 12],
    ["c1", null, false, true, 20, 12],
  ];

  it("is the nested form of three sections", () => {
    const manifest = loadFixture("segment_line");
    const found: unknown[] = [];
    const visit = (timeline: JsonObject, start: number): void => {
      expect(timeline.class).toBe("ContinuousLogicalTimeline");
      expect(timeline.number_type).toBe("fraction");
      const length = Number(((timeline.length as JsonObject).value as number[])[0]);
      expect(timeline.length).toEqual(at(length));
      found.push([
        timeline.id,
        timeline.name,
        timeline.is_segment_line,
        timeline.locked,
        start,
        length,
      ]);
      for (const child of Object.values(timeline.children as JsonObject)) {
        const entry = child as JsonObject;
        const offset = Number(((entry.offset as JsonObject).value as number[])[0]);
        expect(entry.offset).toEqual(at(offset));
        visit(entry.timeline as JsonObject, start + offset);
      }
    };
    visit(root(manifest), 0);
    expect(found).toEqual(expected);
    expect(problemsOf(manifest)).toEqual([]);
    validate(manifest);
  });
});
