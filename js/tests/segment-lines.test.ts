import { describe, expect, it } from "vitest";
import { identityProblems, validate } from "../src/index.js";
import { manifest, timeline } from "./fixtures.js";

type JsonObject = Record<string, unknown>;
type Problem = [readonly (string | number)[], string];

const ID = 'segment line "line"';
const AT = ["timelines", 0];

function segment(
  id: string,
  offset: unknown,
  length: unknown,
  unit = "quarters",
  rest: JsonObject = {},
): JsonObject {
  return timeline(id, unit, length, { offset, ...rest });
}

function line(segments: JsonObject[], length: unknown = [8, 1], unit = "quarters"): JsonObject {
  return manifest([timeline("line", unit, length, { is_segment_line: true, children: segments })]);
}

function problems(value: JsonObject): Problem[] {
  const found = identityProblems(value).map((p): Problem => [p.path, p.detail]);
  if (found.length === 0) validate(value);
  return found;
}

describe("segment lines", () => {
  it.each([
    ["two segments", line([segment("a", [0, 1], [3, 1]), segment("b", [3, 1], [5, 1])])],
    ["empty of length 0", line([], [0, 1])],
    ["empty of unknown length", line([], null)],
    ["offset order", line([segment("b", [3, 1], [5, 1]), segment("a", [0, 1], [3, 1])])],
    [
      "nested",
      line([
        segment("a", [0, 1], [4, 1], "quarters", {
          is_segment_line: true,
          children: [segment("a1", [0, 1], [1, 1]), segment("a2", [1, 1], [3, 1])],
        }),
        segment("b", [4, 1], [4, 1], "quarters", {
          is_segment_line: true,
          children: [segment("b1", [0, 1], [4, 1])],
        }),
      ]),
    ],
    [
      "exact floats",
      line(
        [
          segment("a", 0, 0.5, "seconds"),
          segment("b", 0.5, 0.25, "seconds"),
          segment("c", 0.75, 0.25, "seconds"),
        ],
        1,
        "seconds",
      ),
    ],
  ])("accepts %s", (_name, value) => {
    expect(problems(value)).toEqual([]);
  });

  it("reports each rule once", () => {
    expect(
      problems(line([segment("a", [0, 1], [3, 1]), segment("b", [3, 1], 5, "ticks")])),
    ).toEqual([
      [
        [...AT, "children", 1, "unit"],
        "child 'b' has unit 'ticks', its parent 'line' has 'quarters'",
      ],
    ]);
    expect(
      problems(
        line([
          segment("a", [0, 1], [3, 1]),
          segment("b", [3, 1], [5, 1], "quarters", { is_segment_line: true }),
        ]),
      ),
    ).toEqual([
      [
        [...AT, "children", 1, "is_segment_line"],
        `segment "b" of ${ID} differs from segment "a" in is_segment_line`,
      ],
      [
        [...AT, "children", 1, "length"],
        'the segments of segment line "b" do not end at its length',
      ],
    ]);
    expect(
      problems(
        line([
          segment("a", [0, 1], [3, 1], "quarters", { is_segment_line: true }),
          segment("b", [3, 1], [5, 1]),
        ]),
      )[0],
    ).toEqual([
      [...AT, "children", 1],
      `segment "b" of ${ID} differs from segment "a" in is_segment_line`,
    ]);
    expect(problems(line([segment("a", [1, 1], [7, 1])]))).toEqual([
      [[...AT, "children", 0, "offset"], `segment "a" of ${ID} does not start at 0`],
    ]);
    for (const start of [4, 2]) {
      expect(
        problems(line([segment("a", [0, 1], [3, 1]), segment("b", [start, 1], [8 - start, 1])])),
      ).toEqual([
        [
          [...AT, "children", 1, "offset"],
          `segment "b" of ${ID} does not start where the one before it ends`,
        ],
      ]);
    }
    expect(problems(line([segment("a", [0, 1], [7, 1])]))).toEqual([
      [[...AT, "length"], `the segments of ${ID} do not end at its length`],
    ]);
    expect(problems(line([]))).toEqual([
      [[...AT, "length"], `the segments of ${ID} do not end at its length`],
    ]);
  });

  it("compares exactly", () => {
    const value = line(
      [
        segment("a", 0, 0.1, "seconds"),
        segment("b", 0.1, 0.2, "seconds"),
        segment("c", 0.3, 0.7, "seconds"),
      ],
      1,
      "seconds",
    );
    expect(problems(value)).toEqual([
      [
        [...AT, "children", 2, "offset"],
        `segment "c" of ${ID} does not start where the one before it ends`,
      ],
      [[...AT, "length"], `the segments of ${ID} do not end at its length`],
    ]);
  });

  it.each([
    ["unknown first", line([segment("a", [0, 1], null), segment("b", [5, 1], [3, 1])])],
    [
      "unknown first, late successor",
      line([segment("a", [0, 1], null), segment("b", [7, 1], [1, 1])]),
    ],
    ["unknown last", line([segment("a", [0, 1], [3, 1]), segment("b", [3, 1], null)])],
    ["unknown line", line([segment("a", [0, 1], [3, 1]), segment("b", [3, 1], [5, 1])], null)],
    [
      "unknown line, long segments",
      line([segment("a", [0, 1], [3, 1]), segment("b", [3, 1], [9, 1])], null),
    ],
  ])("skips what needs an unknown length: %s", (_name, value) => {
    expect(problems(value)).toEqual([]);
  });

  it("still checks contiguity on a line of unknown length", () => {
    expect(
      problems(line([segment("a", [0, 1], [3, 1]), segment("b", [4, 1], [4, 1])], null)),
    ).toEqual([
      [
        [...AT, "children", 1, "offset"],
        `segment "b" of ${ID} does not start where the one before it ends`,
      ],
    ]);
  });

  it("reports in order, segment lines among the descendants at their own path", () => {
    const value = line([
      segment("a", [0, 1], [3, 1]),
      segment("b", [3, 1], 1, "ticks"),
      segment("c", [4, 1], [1, 1], "quarters", { is_segment_line: true }),
      segment("d", [5, 1], [1, 1], "quarters", { is_segment_line: true }),
    ]);
    expect(problems(value)).toEqual([
      [
        [...AT, "children", 1, "unit"],
        "child 'b' has unit 'ticks', its parent 'line' has 'quarters'",
      ],
      [
        [...AT, "children", 2, "is_segment_line"],
        `segment "c" of ${ID} differs from segment "a" in is_segment_line`,
      ],
      [
        [...AT, "children", 3, "is_segment_line"],
        `segment "d" of ${ID} differs from segment "a" in is_segment_line`,
      ],
      [[...AT, "length"], `the segments of ${ID} do not end at its length`],
      [
        [...AT, "children", 2, "length"],
        'the segments of segment line "c" do not end at its length',
      ],
      [
        [...AT, "children", 3, "length"],
        'the segments of segment line "d" do not end at its length',
      ],
    ]);
  });

  it("never checks a timeline that is no segment line", () => {
    const value = manifest([
      timeline("free", "quarters", [8, 1], {
        children: [timeline("x", "quarters", [1, 1], { offset: [5, 1] })],
      }),
    ]);
    expect(problems(value)).toEqual([]);
  });
});
