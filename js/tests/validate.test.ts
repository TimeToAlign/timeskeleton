import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  compactJson,
  dumps,
  type Json,
  JsonFloat,
  jsonPointer,
  type Lossless,
  parse,
  parseJson,
  SchemaValidationError,
  UnsupportedVersionError,
  validate,
} from "../src/index.js";
import {
  manifest,
  rejectionFileNames,
  rejectionText,
  repositoryRoot,
  timeline,
} from "./fixtures.js";

type JsonObject = Record<string, unknown>;

const SMALLEST = {
  timeskeleton: "0.7.0",
  timelines: [{ id: "piece", unit: "quarters", length: [32, 1] }],
};

const REJECTIONS = [
  "band_id_region",
  "band_order_missing_band",
  "band_order_unknown_entry",
  "break_control_type_unknown",
  "child_end_beyond_parent",
  "child_id_control_character_newline",
  "child_missing_offset",
  "child_offset_beyond_parent",
  "child_offset_fraction_on_float_axis",
  "child_unit_differs",
  "conversion_map_unknown_type",
  "float_axis_int_not_exact",
  "group_id_duplicate",
  "group_id_is_descendant_id",
  "group_id_is_timeline_id",
  "group_member_with_slash",
  "group_members_repeated",
  "group_missing_id",
  "group_missing_members",
  "group_order_not_member",
  "group_order_repeated",
  "id_control_character_tab",
  "id_duplicate_across_kinds",
  "id_empty",
  "id_with_slash",
  "jump_condition_unknown",
  "jump_target_dangling",
  "later_root_missing_unit",
  "length_coordinate_dict",
  "length_fraction_on_int_axis",
  "length_int_on_fraction_axis",
  "length_negative",
  "length_string_fraction",
  "length_three_element_fraction",
  "length_zero_denominator",
  "linear_map_missing_scalar",
  "manifest_id_is_descendant_id",
  "manifest_id_is_group_id",
  "marker_coordinate_dict",
  "markers_object",
  "measure_map_empty",
  "measure_map_not_array",
  "measure_map_on_graphical_timeline",
  "measure_map_row_actual_length_negative",
  "measure_map_row_offset_within_measure_zero",
  "measure_map_row_qstamp_negative",
  "measure_map_row_qstamp_string",
  "measure_map_row_without_count_or_id",
  "member_dangling",
  "member_in_two_groups",
  "members_contain_member",
  "members_inside_member",
  "metric_hierarchy_string",
  "order_missing_member",
  "order_not_array",
  "order_unknown_group",
  "part_word_one_root",
  "part_word_region_card",
  "part_word_region_label",
  "part_word_timeline_id",
  "region_start_float_on_fraction_axis",
  "root_missing_marker",
  "root_missing_timelines",
  "segment_line_flag_not_boolean",
  "segment_line_gap",
  "segment_line_gap_in_later_root",
  "segment_line_not_from_zero",
  "segment_line_segment_flag",
  "segment_line_short_of_length",
  "statement_select_empty_ids",
  "statement_select_inside_unknown_element",
  "statement_select_projection",
  "statement_select_unknown_element",
  "statement_set_content_not_string",
  "statement_set_dasharray_malformed",
  "statement_set_max_width_zero",
  "statement_set_neither_object_nor_string",
  "statement_set_opacity_above_one",
  "statement_set_shadow_lower_case",
  "statement_set_stroke_lower_case",
  "timeline_missing_length",
  "timeline_name_not_string",
  "timeline_number_type_unknown",
  "timeline_unit_unknown",
  "timelines_child_id_duplicate_across_roots",
  "timelines_id_duplicate_across_roots",
  "timelines_root_jump_target_dangling",
  "version_unknown",
];

/**
 * The cases whose offending value `JSON.parse` cannot read: an integer beyond
 * 2^53 comes back as the float next to it.
 */
const LOST_BY_JSON_PARSE = new Set(["float_axis_int_not_exact.json"]);

/** The path and message of the error `validate` raises. */
function problem(value: unknown): [readonly (string | number)[], string] {
  try {
    validate(value);
  } catch (error) {
    if (!(error instanceof SchemaValidationError)) throw error;
    return [error.path, error.detail];
  }
  throw new Error("value was accepted");
}

describe("the version marker", () => {
  it.each([
    ["no marker", { timelines: [] }],
    ["the former declaration", { meta: { schema_version: "0.7.0" }, timelines: [] }],
    ["a list", []],
    ["a string", "0.7.0"],
  ])("refuses %s at the root", (_name, value) => {
    expect(problem(value)).toEqual([[], "not a TimeSkeleton manifest"]);
  });

  it.each(["9.9.9", "0.6.0", "0.7", 7])("refuses version %s as unsupported", (version) => {
    try {
      validate({ timeskeleton: version });
    } catch (error) {
      expect(error).toBeInstanceOf(UnsupportedVersionError);
      expect((error as UnsupportedVersionError).version).toBe(version);
      return;
    }
    throw new Error("value was accepted");
  });

  it("names the version it reads", () => {
    expect(() => validate({ timeskeleton: "9.9.9", timelines: [] })).toThrow(
      'unsupported TimeSkeleton version "9.9.9"; this package reads 0.7.0 only',
    );
  });

  it("accepts the smallest and the empty manifest", () => {
    validate(SMALLEST);
    validate({ timeskeleton: "0.7.0", timelines: [] });
  });
});

describe("own-axis representation", () => {
  it.each([
    [
      timeline("score", "quarters", 32),
      "length 32 of 'score' is an int on a fraction axis: write [32, 1]",
    ],
    [
      timeline("score", "quarters", 0.5),
      "length 0.5 of 'score' is a float on a fraction axis: write [1, 2]",
    ],
    [
      timeline("score", "quarters", 0.1),
      "length 0.1 of 'score' is a float on a fraction axis: write [3602879701896397, 36028797018963968]",
    ],
    [
      timeline("take", "seconds", [3, 4]),
      "length [3, 4] of 'take' is a fraction on a float axis: write 0.75",
    ],
    [
      timeline("take", "seconds", [1, 3]),
      "length [1, 3] of 'take' is a fraction on a float axis: write a float",
    ],
    [
      timeline("midi", "ticks", [480, 1]),
      "length [480, 1] of 'midi' is a fraction on an int axis: write 480",
    ],
    [
      timeline("midi", "ticks", 0.5),
      "length 0.5 of 'midi' is a float on an int axis: write an int",
    ],
    [
      timeline("midi", "ticks", [1, 2]),
      "length [1, 2] of 'midi' is a fraction on an int axis: write an int",
    ],
    [
      timeline("take", "seconds", 9007199254740993n),
      "length 9007199254740993 of 'take' is an int on a float axis: write a float",
    ],
    [
      timeline("take", "seconds", new JsonFloat(2), { number_type: "fraction" }),
      "length 2.0 of 'take' is a float on a fraction axis: write [2, 1]",
    ],
    [
      timeline("score", "quarters", [2, 1], { number_type: "float" }),
      "length [2, 1] of 'score' is a fraction on a float axis: write 2.0",
    ],
    [
      timeline("score", "quarters", [8, 1], { offset: 3 }),
      "offset 3 of 'score' is an int on a fraction axis: write [3, 1]",
    ],
  ])("refuses %o", (root, message) => {
    const key = message.split(" ", 1)[0] as string;
    expect(problem(manifest([root]))).toEqual([["timelines", 0, key], message]);
  });

  it.each(["seconds", "quarters"])("reads a %s child's offset on its parent's axis", (unit) => {
    const child = timeline("take", unit, unit === "seconds" ? 4.5 : [4, 1], { offset: [1, 2] });
    expect(
      problem(manifest([timeline("recording", "seconds", 60.5, { children: [child] })])),
    ).toEqual([
      ["timelines", 0, "children", 0, "offset"],
      "offset [1, 2] of 'take' is a fraction on a float axis: write 0.5",
    ]);
  });

  it.each([
    ["regions", { id: "intro", start: 1, end: [2, 1] }, "start"],
    ["regions", { id: "intro", start: [1, 1], end: 2 }, "end"],
    ["breaks", { id: "fine", coordinate: 4 }, "coordinate"],
    ["markers", { id: "segno", coordinate: 4 }, "coordinate"],
    ["jumps", { id: "back", from_coordinate: 4, to_coordinate: [0, 1] }, "from_coordinate"],
    ["jumps", { id: "back", from_coordinate: [4, 1], to_coordinate: 0 }, "to_coordinate"],
  ] as const)("checks every own-axis value: %s %o", (member, entry, key) => {
    const root =
      member === "regions"
        ? timeline("score", "quarters", [8, 1], { regions: [entry] })
        : timeline("score", "quarters", [8, 1], { flow_control: { [member]: [entry] } });
    const path =
      member === "regions"
        ? ["timelines", 0, "regions", 0, key]
        : ["timelines", 0, "flow_control", member, 0, key];
    const value = (entry as JsonObject)[key];
    expect(problem(manifest([root]))).toEqual([
      path,
      `${key} ${value} of '${entry.id}' is an int on a fraction axis: write [${value}, 1]`,
    ]);
  });

  it.each([
    timeline("midi", "ticks", 8),
    timeline("midi", "ticks", new JsonFloat(8)),
    timeline("take", "seconds", 8),
    timeline("take", "seconds", 0.5),
    timeline("take", "seconds", 9007199254740992n),
    timeline("take", "seconds", 10n ** 20n),
    timeline("score"),
    timeline("score", "quarters", null),
    timeline("take", "seconds", 2.5, { offset: -1700000000.25 }),
    timeline("score", "quarters", [8, 1], { offset: [-3, 2] }),
  ])("accepts %o", (root) => {
    validate(manifest([root]));
  });

  it("raises the first problem", () => {
    const root = timeline("score", "quarters", 8, {
      regions: [{ id: "r", start: 0, end: [1, 1] }],
    });
    expect(problem(manifest([root]))[0]).toEqual(["timelines", 0, "length"]);
  });
});

describe("unknown length", () => {
  it.each([
    ["a root", manifest([timeline("score", "quarters", null)])],
    ["a locked root", manifest([timeline("score", "quarters", null, { locked: true })])],
    [
      "a child",
      manifest([
        timeline("score", "quarters", [8, 1], {
          children: [timeline("c", "quarters", null, { offset: [2, 1] })],
        }),
      ]),
    ],
    [
      "a known child of an unknown parent",
      manifest([
        timeline("score", "quarters", null, {
          children: [timeline("c", "quarters", [8, 1], { offset: [2, 1] })],
        }),
      ]),
    ],
    [
      "a group member",
      manifest([timeline("score"), timeline("perf", "seconds", null)], {
        groups: [{ id: "g", members: ["perf", "score"] }],
      }),
    ],
  ])("is no violation on %s", (_name, value) => {
    validate(value);
  });
});

describe("the shared rejection cases", () => {
  it("are stated", () => {
    expect(rejectionFileNames()).toEqual(REJECTIONS.map((name) => `${name}.json`));
  });

  it.each(rejectionFileNames())("refuse %s at the stored path", (name) => {
    const text = rejectionText(name);
    const testCase = parseJson(text) as JsonObject;
    expect(dumps(testCase)).toBe(text);
    const readings = [
      () => validate(testCase.manifest),
      () => validate((JSON.parse(text) as JsonObject).manifest),
      () => parse(compactJson(testCase.manifest as Lossless<Json>)),
    ];
    for (const [index, read] of readings.entries()) {
      if (index === 1 && LOST_BY_JSON_PARSE.has(name)) {
        // JSON.parse rounds the integer to the float next to it, which validates.
        read();
        continue;
      }
      if (testCase.error === "UnsupportedVersionError") {
        expect(testCase.path).toEqual(["timeskeleton"]);
        expect(read).toThrow(UnsupportedVersionError);
        continue;
      }
      expect(testCase.error).toBeUndefined();
      try {
        read();
      } catch (error) {
        expect(error).toBeInstanceOf(SchemaValidationError);
        expect((error as SchemaValidationError).path).toEqual(testCase.path);
        continue;
      }
      throw new Error(`${name} was accepted`);
    }
  });
});

describe("errors and paths", () => {
  it("render as JSON pointers", () => {
    try {
      validate(manifest([timeline("score", "beats")]));
    } catch (error) {
      expect((error as SchemaValidationError).path).toEqual(["timelines", 0, "unit"]);
      expect((error as Error).message.startsWith("#/timelines/0/unit: ")).toBe(true);
    }
    expect(jsonPointer([])).toBe("#");
    expect(jsonPointer(["a/b", "c~d", 0])).toBe("#/a~1b/c~0d/0");
  });
});

describe("integer boundaries", () => {
  it("reads beyond the safe range only with parseJson", () => {
    expect(JSON.parse("9007199254740993")).toBe(9007199254740992);
    expect(parseJson("9007199254740993")).toBe(9007199254740993n);
  });

  it.each([9007199254740993n, 9223372036854775807n])("validates and writes %s exactly", (value) => {
    const document = manifest([timeline("midi", "ticks", value)]);
    validate(document);
    const text = dumps(document);
    expect(text).toContain(`"length": ${value},\n`);
    const read = parseJson(text) as JsonObject;
    expect(((read.timelines as JsonObject[])[0] as JsonObject).length).toBe(value);
  });
});

describe("the graphical block", () => {
  const styled = (declaration: JsonObject) =>
    manifest([timeline("score")], {
      graphical: { statements: [{ select: { element: "timeline" }, set: declaration }] },
    });

  it.each([
    { "stroke-width": 0, rx: 0 },
    { opacity: 0 },
    { opacity: 1 },
    { "font-size": 0.5, "max-width": 1 },
    { "max-width": "none", content: "Score" },
    { "stroke-dasharray": "none" },
    { "stroke-dasharray": "4 2.5" },
  ])("accepts %o", (declaration) => {
    validate(styled(declaration));
  });

  it.each([
    [{ "stroke-width": -1 }, "stroke-width"],
    [{ rx: -0.5 }, "rx"],
    [{ opacity: -0.1 }, "opacity"],
    [{ opacity: 1.1 }, "opacity"],
    [{ "font-size": 0 }, "font-size"],
    [{ "max-width": 0 }, "max-width"],
    [{ content: 5 }, "content"],
    [{ "stroke-dasharray": "4,2" }, "stroke-dasharray"],
  ])("refuses %o at the property", (declaration, member) => {
    expect(problem(styled(declaration))[0]).toEqual(["graphical", "statements", 0, "set", member]);
  });

  it.each([
    { select: { element: "card" }, set: { rx: 5 } },
    { select: { inside: "ancestor" }, set: { opacity: 0.35 } },
    { select: { element: "card" }, set: { shadow: "#B8BEC8" } },
    { select: { element: "band" }, set: { display: "none" } },
    { select: { inside: "band" }, set: { opacity: 0.5 } },
    { select: { ids: ["score/regions_1"] }, set: { display: "inline" } },
    ...["markers", "conversion_maps", "children", "regions", "flow_control"].map((kind) => ({
      select: { element: "band", class: kind },
      set: { display: "none" },
    })),
  ])("accepts %o", (statement) => {
    validate(manifest([timeline("score")], { graphical: { statements: [statement] } }));
  });

  const ENTRY =
    "^[^/\\u0000-\\u001f]+(/(markers|conversion_maps|children|regions|flow_control)_[1-9][0-9]*)?$";

  it.each([
    [["score/foo"], 0],
    [["score/regions_0"], 0],
    [["score", "score/regions_1", "score/region_1"], 2],
  ])("refuses the order entry of %o by the schema", (order, index) => {
    const value = manifest([timeline("score")], { graphical: { order: { score: order } } });
    expect(problem(value)).toEqual([
      ["graphical", "order", "score", index],
      `must match pattern "${ENTRY}"`,
    ]);
  });

  it("refuses a repeated band order entry by the schema", () => {
    const value = manifest([timeline("score")], {
      graphical: { order: { score: ["score", "score/markers_1", "score"] } },
    });
    expect(problem(value)).toEqual([
      ["graphical", "order", "score"],
      "must NOT have duplicate items (items ## 2 and 0 are identical)",
    ]);
  });

  it("accepts the defaults of the drawing specification", () => {
    const text = readFileSync(resolve(repositoryRoot, "docs", "drawing.md"), "utf8");
    const section = text.split("\n## 4. Defaults\n", 2)[1] as string;
    const block = (section.split("```json\n", 2)[1] as string).split("\n```", 1)[0] as string;
    const defaults = parseJson(block) as JsonObject;
    expect(Object.keys(defaults.styles as JsonObject).length).toBe(3);
    expect((defaults.statements as unknown[]).length).toBe(30);
    validate({ ...SMALLEST, graphical: defaults });
  });

  it("leaves names unrestricted", () => {
    validate(manifest([timeline("score", "quarters", [8, 1], { name: "tab\there\nnewline" })]));
  });
});
