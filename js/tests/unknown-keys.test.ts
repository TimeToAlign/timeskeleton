import { describe, expect, it } from "vitest";
import {
  dumps,
  parseJson,
  SchemaValidationError,
  UnsupportedVersionError,
  unknownKeys,
  validate,
} from "../src/index.js";
import type { JsonObject } from "../src/json/value.js";
import { group, manifest, timeline, warningFileNames, warningText } from "./fixtures.js";

const WARNINGS = [
  "declaration_show_projections",
  "declaration_unknown_key",
  "graphical_unknown_key",
  "group_unknown_key",
  "measure_map_row_offset_key",
  "measure_map_row_unknown_key",
  "metrical_position_map_with_maps",
  "selector_unknown_key",
  "several_depths",
  "support_policy",
  "timeline_class",
];

describe("unknown keys", () => {
  it("has the stated warning cases", () => {
    expect(warningFileNames()).toEqual(WARNINGS.map((name) => `${name}.json`));
  });

  it.each(warningFileNames())("lists the unknown keys of %s as Python does", (name) => {
    const text = warningText(name);
    const testCase = parseJson(text) as JsonObject;
    expect(Object.keys(testCase).sort()).toEqual(["manifest", "unknown_keys"]);
    expect(dumps(testCase)).toBe(text);
    validate(testCase.manifest);
    expect(dumps(unknownKeys(testCase.manifest))).toBe(dumps(testCase.unknown_keys));
  });

  it("finds them at several depths, in order", () => {
    const testCase = parseJson(warningText("several_depths.json")) as JsonObject;
    expect(unknownKeys(testCase.manifest).map((entry) => [entry.path, entry.key])).toEqual([
      [[], "x-editor"],
      [["graphical"], "arrangement"],
      [["graphical", "statements", 0], "comment"],
      [["graphical", "statements", 0, "select"], "kind"],
      [["graphical", "statements", 0, "set"], "colour"],
      [["groups", 0], "colour"],
      [["timelines", 0], "lenght"],
      [["timelines", 0, "children", 0], "x-tilia"],
      [["timelines", 0, "conversion_maps", 0], "note"],
      [["timelines", 0, "conversion_maps", 0, "maps", 0], "note"],
      [["timelines", 0, "flow_control"], "codas"],
      [["timelines", 0, "flow_control", "breaks", 0], "pause"],
      [["timelines", 0, "flow_control", "jumps", 0], "via"],
      [["timelines", 0, "flow_control", "markers", 0], "glyph"],
      [["timelines", 0, "measure_map", 0], "tempo"],
      [["timelines", 0, "regions", 0], "colour"],
    ]);
  });

  it("does not look into free objects, maps keyed by data or unknown values", () => {
    const value = manifest(
      [
        timeline("score", "quarters", [8, 1], {
          meta: { anything: { deep: 1 } },
          metric_hierarchy: { levels: [] },
          regions: [{ id: "r", start: [0, 1], end: [1, 1], meta: { x: 1 } }],
        }),
      ],
      {
        meta: { source: "hand" },
        groups: [group("g", ["score"], { meta: { note: 1 } })],
        graphical: {
          styles: { "any-name": { stroke: "#000000" } },
          order: { g: ["score"] },
          statements: [{ select: {}, set: "any-name" }],
        },
      },
    );
    expect(unknownKeys(value)).toEqual([]);
    value.x = { inner: { also: 1 } };
    expect(unknownKeys(value)).toEqual([{ path: [], key: "x" }]);
  });

  it("reports side as an unknown key of a declaration", () => {
    const value = manifest([timeline("score")], {
      graphical: {
        styles: { below: { side: "below" } },
        statements: [{ select: { element: "map" }, set: { fill: "#000000", side: "above" } }],
      },
    });
    expect(unknownKeys(value)).toEqual([
      { path: ["graphical", "statements", 0, "set"], key: "side" },
      { path: ["graphical", "styles", "below"], key: "side" },
    ]);
  });

  it("sorts keys by code point and indices by number", () => {
    const roots = Array.from({ length: 11 }, (_, index) => timeline(`t${index}`));
    (roots[2] as JsonObject).zz = 1;
    (roots[10] as JsonObject).zz = 1;
    const value = manifest(roots, { zz: 1, aa: 1, "\u{FB00}": 1, "\u{1F600}": 1 });
    expect(unknownKeys(value)).toEqual([
      { path: [], key: "aa" },
      { path: [], key: "zz" },
      { path: [], key: "\u{FB00}" },
      { path: [], key: "\u{1F600}" },
      { path: ["timelines", 2], key: "zz" },
      { path: ["timelines", 10], key: "zz" },
    ]);
  });

  it("raises for an invalid value before listing any key", () => {
    expect(() => unknownKeys(manifest([timeline("score", "quarters", 32)], { extra: 1 }))).toThrow(
      SchemaValidationError,
    );
    expect(() => unknownKeys({ timeskeleton: "9.9.9", extra: 1 })).toThrow(UnsupportedVersionError);
  });
});
