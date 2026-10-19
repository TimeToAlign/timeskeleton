import { describe, expect, it } from "vitest";
import {
  identityProblems,
  isJsonObject,
  JsonFloat,
  SchemaValidationError,
  validate,
} from "../src/index.js";
import type { JsonObject } from "../src/json/value.js";
import { bundle, group, manifest, rejectionCase, timeline } from "./fixtures.js";

type Problem = [readonly (string | number)[], string];

function problems(value: JsonObject): Problem[] {
  return identityProblems(value).map((problem) => [problem.path, problem.detail]);
}

/** The one problem of a value, which `validate` raises too. */
function only(value: JsonObject): Problem {
  const found = problems(value);
  expect(found.length).toBe(1);
  try {
    validate(value);
  } catch (error) {
    expect(error).toBeInstanceOf(SchemaValidationError);
    expect([
      (error as SchemaValidationError).path,
      (error as SchemaValidationError).detail,
    ]).toEqual(found[0]);
    return found[0] as Problem;
  }
  throw new Error("value was accepted");
}

const markers = (...ids: string[]) => ({
  markers: ids.map((id, index) => ({ id, coordinate: [index, 1] })),
});

const jump = (id: string, target: string | null) => ({
  id,
  from_coordinate: [4, 1],
  to_coordinate: [0, 1],
  target,
});

describe("identity", () => {
  it("finds nothing in the bundle document", () => {
    expect(problems(bundle())).toEqual([]);
    validate(bundle());
  });

  it("reports a repeated id within a root at its later occurrence", () => {
    const child = timeline("c", "quarters", [8, 1], { offset: [0, 1], flow_control: markers("m") });
    const root = timeline("bare", "quarters", [8, 1], {
      flow_control: markers("m", "m", "bare"),
      children: [child],
    });
    expect(problems(manifest([root]))).toEqual([
      [
        ["timelines", 0, "flow_control", "markers", 1, "id"],
        'duplicate id "m", first at #/timelines/0/flow_control/markers/0/id',
      ],
      [
        ["timelines", 0, "flow_control", "markers", 2, "id"],
        'duplicate id "bare", first at #/timelines/0/id',
      ],
      [
        ["timelines", 0, "children", 0, "flow_control", "markers", 0, "id"],
        'duplicate id "m", first at #/timelines/0/flow_control/markers/0/id',
      ],
    ]);
  });

  it("scopes ids per root", () => {
    validate(
      manifest([
        timeline("a", "quarters", [8, 1], { flow_control: markers("m") }),
        timeline("b", "quarters", [8, 1], { flow_control: markers("m") }),
      ]),
    );
    validate(
      manifest([
        timeline("score", "quarters", [8, 1], {
          regions: [{ id: "perf", start: [0, 1], end: [1, 1] }],
        }),
        timeline("take", "quarters", [8, 1], {
          children: [timeline("perf", "quarters", [8, 1], { offset: [0, 1] })],
        }),
      ]),
    );
  });

  it("keeps targets within their timeline", () => {
    const child = timeline("c", "quarters", [8, 1], {
      offset: [0, 1],
      flow_control: {
        markers: [{ id: "there", coordinate: [1, 1] }],
        jumps: [jump("cj", "here")],
      },
    });
    const root = timeline("bare", "quarters", [8, 1], {
      flow_control: {
        markers: [{ id: "here", coordinate: [1, 1] }],
        jumps: [jump("j1", "here"), jump("j2", null), jump("j3", "there")],
      },
      children: [child],
    });
    expect(problems(manifest([root]))).toEqual([
      [
        ["timelines", 0, "flow_control", "jumps", 2, "target"],
        '"there" names no marker of this timeline',
      ],
      [
        ["timelines", 0, "children", 0, "flow_control", "jumps", 0, "target"],
        '"here" names no marker of this timeline',
      ],
    ]);
  });

  /** A document for each place an id is checked, with the path of `word` in it. */
  const idDocuments = (word: string): [JsonObject, (string | number)[]][] => {
    const shift = { type: "ShiftMap", id: word, source_unit: null, target_unit: null, offset: 1 };
    const flow: Record<string, JsonObject[]> = {
      breaks: [{ id: word, coordinate: [1, 1] }],
      jumps: [{ id: word, from_coordinate: [1, 1], to_coordinate: [0, 1] }],
      markers: [{ id: word, coordinate: [1, 1] }],
    };
    return [
      [manifest([timeline(word)]), ["timelines", 0, "id"]],
      [
        manifest([
          timeline("s", "quarters", [8, 1], {
            children: [timeline(word, "quarters", [8, 1], { offset: [0, 1] })],
          }),
        ]),
        ["timelines", 0, "children", 0, "id"],
      ],
      [
        manifest([timeline("s", "quarters", [8, 1], { conversion_maps: [shift] })]),
        ["timelines", 0, "conversion_maps", 0, "id"],
      ],
      [
        manifest([
          timeline("s", "quarters", [8, 1], {
            regions: [{ id: word, start: [0, 1], end: [1, 1] }],
          }),
        ]),
        ["timelines", 0, "regions", 0, "id"],
      ],
      [manifest([timeline("s")], { groups: [group(word, ["s"])] }), ["groups", 0, "id"]],
      [manifest([timeline("s")], { id: word }), ["id"]],
      ...Object.entries(flow).map(([member, entries]): [JsonObject, (string | number)[]] => [
        manifest([timeline("s", "quarters", [8, 1], { flow_control: { [member]: entries } })]),
        ["timelines", 0, "flow_control", member, 0, "id"],
      ]),
    ];
  };

  it.each(["start", "end", "name", "label", "card"])(
    "refuses the part word %s as any id",
    (word) => {
      for (const [document, path] of idDocuments(word)) {
        expect(only(document)).toEqual([
          path,
          `id ${JSON.stringify(word)} is reserved for the parts of an address`,
        ]);
      }
    },
  );

  it.each(["regions_1", "children_10", "markers_7", "conversion_maps_1", "flow_control_2"])(
    "refuses the band id %s as any id",
    (word) => {
      for (const [document, path] of idDocuments(word)) {
        expect(only(document)).toEqual([
          path,
          `id ${JSON.stringify(word)} is reserved for the bands of a timeline`,
        ]);
      }
    },
  );

  it.each([
    "starts",
    "Start",
    "markers",
    "conversion_maps",
    "children",
    "regions",
    "flow_control",
    "regions_0",
    "regions_01",
    "Regions_1",
    "regions_1x",
    "band_1",
  ])("accepts %s as any id", (word) => {
    for (const [document] of idDocuments(word)) validate(document);
  });

  it("keeps timeline ids unique across roots", () => {
    expect(only(manifest([timeline("piece"), timeline("piece")]))).toEqual([
      ["timelines", 1, "id"],
      'duplicate id "piece", first at #/timelines/0/id',
    ]);
    const child = () => timeline("excerpt", "quarters", [8, 1], { offset: [0, 1] });
    const value = manifest([
      timeline("a", "quarters", [8, 1], { children: [child()] }),
      timeline("b", "quarters", [8, 1], { children: [child()] }),
    ]);
    expect(only(value)).toEqual([
      ["timelines", 1, "children", 0, "id"],
      'duplicate id "excerpt", first at #/timelines/0/children/0/id',
    ]);
  });

  it("reports a timeline id repeated within a root once", () => {
    const value = manifest([
      timeline("a", "quarters", [8, 1], {
        children: [timeline("a", "quarters", [8, 1], { offset: [0, 1] })],
      }),
    ]);
    expect(problems(value)).toEqual([
      [["timelines", 0, "children", 0, "id"], 'duplicate id "a", first at #/timelines/0/id'],
    ]);
  });

  it("keeps group ids apart", () => {
    expect(only(manifest([timeline("score")], { groups: [group("score", [])] }))).toEqual([
      ["groups", 0, "id"],
      'duplicate id "score", first at #/timelines/0/id',
    ]);
    expect(
      only(manifest([timeline("score")], { groups: [group("g", []), group("g", [])] })),
    ).toEqual([["groups", 1, "id"], 'duplicate id "g", first at #/groups/0/id']);
  });

  it("keeps the manifest id apart", () => {
    expect(only(manifest([timeline("score")], { id: "score" }))).toEqual([
      ["id"],
      'duplicate id "score", first at #/timelines/0/id',
    ]);
    expect(only(manifest([timeline("score")], { id: "g", groups: [group("g", [])] }))).toEqual([
      ["id"],
      'duplicate id "g", first at #/groups/0/id',
    ]);
    expect(problems(manifest([timeline("g")], { id: "g", groups: [group("g", [])] }))).toEqual([
      [["groups", 0, "id"], 'duplicate id "g", first at #/timelines/0/id'],
      [["id"], 'duplicate id "g", first at #/timelines/0/id'],
    ]);
  });

  it("checks members", () => {
    expect(only(manifest([timeline("score")], { groups: [group("g", ["tempo"])] }))).toEqual([
      ["groups", 0, "members", 0],
      '"tempo" names no timeline of this manifest',
    ]);
    const twice = manifest([timeline("a"), timeline("b")], {
      groups: [group("g", ["a"]), group("h", ["b", "a"])],
    });
    expect(only(twice)).toEqual([
      ["groups", 1, "members", 1],
      'duplicate member "a", first at #/groups/0/members/0',
    ]);
    const piece = () =>
      timeline("piece", "quarters", [8, 1], {
        children: [timeline("half", "quarters", [4, 1], { offset: [4, 1] })],
      });
    expect(only(manifest([piece()], { groups: [group("g", ["piece", "half"])] }))).toEqual([
      ["groups", 0, "members", 1],
      'member "half" lies inside member "piece" of the same group',
    ]);
    expect(only(manifest([piece()], { groups: [group("g", ["half", "piece"])] }))).toEqual([
      ["groups", 0, "members", 1],
      'member "piece" contains member "half" of the same group',
    ]);
  });

  it("accepts a child and its root in other groups or none", () => {
    const value = bundle();
    validate(value);
    ((value.groups as unknown as [JsonObject])[0].members as string[]).push("recording");
    (((value.graphical as unknown as JsonObject).order as JsonObject).group_1 as string[]).push(
      "recording",
    );
    validate(value);
  });

  it("keeps a group without members", () => {
    validate(manifest([timeline("score")], { groups: [group("empty", [])] }));
  });

  it("checks display orders", () => {
    const order = (value: JsonObject) => (value.graphical as JsonObject).order as JsonObject;
    let value = bundle();
    order(value).g9 = [];
    expect(only(value)).toEqual([
      ["graphical", "order", "g9"],
      '"g9" names no group or timeline of this manifest',
    ]);
    value = bundle();
    order(value).group_1 = ["score", "page", "performance"];
    expect(only(value)).toEqual([
      ["graphical", "order", "group_1", 1],
      '"page" is not a member of group "group_1"',
    ]);
    value = bundle();
    order(value).group_2 = ["page"];
    expect(only(value)).toEqual([
      ["graphical", "order", "group_2"],
      'member "excerpt" of group "group_2" is missing',
    ]);
    value = bundle();
    delete order(value).group_2;
    validate(value);
  });

  /** `score` with a child `take` holding a child `bar`, with these orders. */
  const banded = (order: JsonObject, rest: JsonObject = {}) =>
    manifest(
      [
        timeline("score", "quarters", [8, 1], {
          children: [
            timeline("take", "quarters", [4, 1], {
              offset: [0, 1],
              children: [timeline("bar", "quarters", [2, 1], { offset: [0, 1] })],
            }),
          ],
        }),
      ],
      { ...rest, graphical: { order } },
    );

  it("accepts a band order at a root and at a descendant", () => {
    for (const value of [
      banded({
        score: [
          "score/children_1",
          "score/conversion_maps_1",
          "score",
          "score/markers_1",
          "score/regions_1",
          "score/flow_control_1",
        ],
      }),
      banded({
        score: [
          "score/children_1",
          "score/markers_1",
          "score",
          "score/conversion_maps_1",
          "score/regions_1",
          "score/flow_control_1",
        ],
      }),
      banded({
        take: [
          "take/flow_control_1",
          "take/regions_1",
          "take/markers_1",
          "take",
          "take/conversion_maps_1",
          "take/children_1",
        ],
        bar: [
          "bar",
          "bar/children_1",
          "bar/conversion_maps_1",
          "bar/markers_1",
          "bar/regions_1",
          "bar/flow_control_1",
        ],
      }),
    ]) {
      expect(problems(value)).toEqual([]);
      validate(value);
    }
  });

  it("checks band orders", () => {
    expect(problems(banded({ score: ["score"] }))).toEqual(
      [
        "score/children_1",
        "score/conversion_maps_1",
        "score/markers_1",
        "score/regions_1",
        "score/flow_control_1",
      ].map((address) => [
        ["graphical", "order", "score"],
        `${JSON.stringify(address)} is missing from the band order of "score"`,
      ]),
    );
    const strangers = banded({
      score: [
        "take/regions_1",
        "score/children_1",
        "score/conversion_maps_1",
        "score",
        "take",
        "score/markers_1",
        "score/regions_1",
        "score/flow_control_1",
        "score/regions_2",
      ],
    });
    expect(problems(strangers)).toEqual([
      [["graphical", "order", "score", 0], '"take/regions_1" is not "score" or one of its bands'],
      [["graphical", "order", "score", 4], '"take" is not "score" or one of its bands'],
      [["graphical", "order", "score", 8], '"score/regions_2" is not "score" or one of its bands'],
    ]);
    const swapped = banded({
      bar: [
        "bar/children_1",
        "bar/conversion_maps_1",
        "bar",
        "bar/markers_1",
        "take/regions_1",
        "bar/flow_control_1",
      ],
    });
    expect(problems(swapped)).toEqual([
      [["graphical", "order", "bar", 4], '"take/regions_1" is not "bar" or one of its bands'],
      [["graphical", "order", "bar"], '"bar/regions_1" is missing from the band order of "bar"'],
    ]);
    expect(only(banded({ nothing: [] }))).toEqual([
      ["graphical", "order", "nothing"],
      '"nothing" names no group or timeline of this manifest',
    ]);
  });

  it("reads a key naming a group and a timeline as the group's", () => {
    const value = banded({ score: ["score"] }, { groups: [group("score", [])] });
    expect(problems(value)).toEqual([
      [["groups", 0, "id"], 'duplicate id "score", first at #/timelines/0/id'],
      [["graphical", "order", "score", 0], '"score" is not a member of group "score"'],
    ]);
  });

  it("requires a child to share its parent's unit", () => {
    expect(
      only(
        manifest([
          timeline("score", "quarters", [8, 1], {
            children: [timeline("take", "seconds", 4, { offset: [2, 1] })],
          }),
        ]),
      ),
    ).toEqual([
      ["timelines", 0, "children", 0, "unit"],
      "child 'take' has unit 'seconds', its parent 'score' has 'quarters'",
    ]);
    const number = timeline("n", "number", [4, 1], { offset: [0, 1], number_type: "fraction" });
    expect(only(manifest([timeline("score", "quarters", [8, 1], { children: [number] })]))).toEqual(
      [
        ["timelines", 0, "children", 0, "unit"],
        "child 'n' has unit 'number', its parent 'score' has 'quarters'",
      ],
    );
    const grandchild = timeline("b", "ticks", 4, { offset: [1, 1] });
    const parent = timeline("a", "quarters", [8, 1], { offset: [0, 1], children: [grandchild] });
    expect(only(manifest([timeline("score", "quarters", [8, 1], { children: [parent] })]))).toEqual(
      [
        ["timelines", 0, "children", 0, "children", 0, "unit"],
        "child 'b' has unit 'ticks', its parent 'a' has 'quarters'",
      ],
    );
    const same = timeline("c", "quarters", [8, 1], { offset: [0, 1] });
    expect(
      problems(manifest([timeline("score", "quarters", [8, 1], { children: [same] })])),
    ).toEqual([]);
  });

  it("accepts a negative offset, of a child or a root", () => {
    const take = (offset: unknown) =>
      manifest([
        timeline("recording", "seconds", 60, {
          children: [timeline("take", "seconds", 4, { offset })],
        }),
      ]);
    const child = (offset: unknown) =>
      manifest([
        timeline("score", "quarters", [8, 1], {
          children: [timeline("c", "quarters", [8, 1], { offset })],
        }),
      ]);
    const grandchild = timeline("b", "quarters", [8, 1], { offset: [-1, 2] });
    const parent = timeline("a", "quarters", [8, 1], { offset: [0, 1], children: [grandchild] });
    for (const value of [
      take(-1.5),
      child([-1, 1000000]),
      manifest([timeline("score", "quarters", [8, 1], { children: [parent] })]),
      {
        timeskeleton: "0.7.0",
        timelines: [
          {
            id: "piece",
            unit: "quarters",
            length: [32, 1],
            children: [{ id: "take", unit: "quarters", offset: [-3, 2], length: [4, 1] }],
          },
        ],
      },
      child([0, 1]),
      take(-0),
      manifest([timeline("take", "seconds", 2.5, { offset: -1700000000.25 })]),
      manifest([timeline("score", "quarters", [8, 1], { offset: [-3, 2] })]),
    ]) {
      expect(problems(value)).toEqual([]);
      validate(value);
    }
    const long = timeline("take", "quarters", [40, 1], { offset: [-3, 2] });
    expect(only(manifest([timeline("piece", "quarters", [32, 1], { children: [long] })]))).toEqual([
      ["timelines", 0, "children", 0, "length"],
      "child 'take' ends at [77, 2], beyond the length [32, 1] of its parent 'piece'",
    ]);
  });

  it("requires a child to lie within its parent's known length", () => {
    const recording = (length: unknown, ...children: JsonObject[]) =>
      manifest([timeline("recording", "seconds", length, { children })]);
    const take = (length: unknown, offset: unknown) =>
      timeline("take", "seconds", length, { offset });
    const score = (length: unknown, ...children: JsonObject[]) =>
      manifest([timeline("score", "quarters", length, { children })]);
    expect(only(recording(new JsonFloat(60), take(null, new JsonFloat(75))))).toEqual([
      ["timelines", 0, "children", 0, "offset"],
      "offset 75.0 of 'take' is beyond the length 60.0 of its parent 'recording'",
    ]);
    expect(only(score([8, 1], timeline("c", "quarters", [2, 1], { offset: [9, 1] })))).toEqual([
      ["timelines", 0, "children", 0, "offset"],
      "offset [9, 1] of 'c' is beyond the length [8, 1] of its parent 'score'",
    ]);
    expect(only(score([10, 1], timeline("coda", "quarters", [4, 1], { offset: [8, 1] })))).toEqual([
      ["timelines", 0, "children", 0, "length"],
      "child 'coda' ends at [12, 1], beyond the length [10, 1] of its parent 'score'",
    ]);
    expect(only(recording(0.75, take(0.5, 0.5)))).toEqual([
      ["timelines", 0, "children", 0, "length"],
      "child 'take' ends at 1.0, beyond the length 0.75 of its parent 'recording'",
    ]);
    expect(only(recording(0.3, take(0.2, 0.1)))).toEqual([
      ["timelines", 0, "children", 0, "length"],
      "child 'take' ends at [10808639105689191, 36028797018963968], beyond the length 0.3 of its parent 'recording'",
    ]);
    const midi = timeline("midi", "ticks", 480, {
      children: [timeline("m", "ticks", 240, { offset: 480 })],
    });
    expect(only(manifest([midi]))).toEqual([
      ["timelines", 0, "children", 0, "length"],
      "child 'm' ends at 720, beyond the length 480 of its parent 'midi'",
    ]);
    const loose = timeline("f", "quarters", 2.5, { offset: [7, 1], number_type: "float" });
    expect(only(score([8, 1], loose))).toEqual([
      ["timelines", 0, "children", 0, "length"],
      "child 'f' ends at [19, 2], beyond the length [8, 1] of its parent 'score'",
    ]);
    const other = timeline("take", "seconds", new JsonFloat(100), { offset: [2, 1] });
    expect(problems(score([8, 1], other))).toEqual([
      [
        ["timelines", 0, "children", 0, "unit"],
        "child 'take' has unit 'seconds', its parent 'score' has 'quarters'",
      ],
    ]);
    const grandchild = timeline("b", "quarters", [2, 1], { offset: [3, 1] });
    const child = timeline("a", "quarters", [4, 1], { offset: [0, 1], children: [grandchild] });
    expect(only(score([8, 1], child))).toEqual([
      ["timelines", 0, "children", 0, "children", 0, "length"],
      "child 'b' ends at [5, 1], beyond the length [4, 1] of its parent 'a'",
    ]);
    const line = timeline("line", "quarters", [8, 1], {
      is_segment_line: true,
      children: [
        timeline("a", "quarters", null, { offset: [0, 1] }),
        timeline("b", "quarters", [1, 1], { offset: [10, 1] }),
      ],
    });
    expect(problems(manifest([line]))).toEqual([
      [
        ["timelines", 0, "children", 0, "length"],
        "child 'a' ends at [10, 1], beyond the length [8, 1] of its parent 'line'",
      ],
      [
        ["timelines", 0, "children", 1, "offset"],
        "offset [10, 1] of 'b' is beyond the length [8, 1] of its parent 'line'",
      ],
      [["timelines", 0, "length"], 'the segments of segment line "line" do not end at its length'],
    ]);
    for (const value of [
      recording(new JsonFloat(60), take(null, new JsonFloat(60))),
      score([10, 1], timeline("c", "quarters", [2, 1], { offset: [8, 1] })),
      recording(0.75, take(0.25, 0.5)),
      score(null, timeline("c", "quarters", [8, 1], { offset: [100, 1] })),
    ]) {
      expect(problems(value)).toEqual([]);
      validate(value);
    }
  });

  it.each([
    ["band_id_region", 'id "regions_1" is reserved for the bands of a timeline'],
    ["band_order_missing_band", '"score/markers_1" is missing from the band order of "score"'],
    ["band_order_unknown_entry", '"score/regions_2" is not "score" or one of its bands'],
    ["order_unknown_group", '"group_9" names no group or timeline of this manifest'],
    ["child_unit_differs", "child 'take' has unit 'seconds', its parent 'score' has 'quarters'"],
    [
      "child_offset_beyond_parent",
      "offset 75.0 of 'take' is beyond the length 60.0 of its parent 'recording'",
    ],
    [
      "child_end_beyond_parent",
      "child 'coda' ends at [12, 1], beyond the length [10, 1] of its parent 'score'",
    ],
  ])("states the message of the shared case %s", (name, message) => {
    const testCase = rejectionCase(`${name}.json`);
    if (!isJsonObject(testCase.manifest)) throw new Error(`${name} holds no manifest object`);
    expect(only(testCase.manifest)).toEqual([testCase.path, message]);
  });

  it("reports every step in order", () => {
    const first = timeline("first", "quarters", [8, 1], {
      flow_control: {
        jumps: [{ id: "j", from_coordinate: [1, 1], to_coordinate: [0, 1], target: "nowhere" }],
      },
      regions: [
        { id: "end", start: [0, 1], end: [1, 1] },
        { id: "regions_3", start: [0, 1], end: [1, 1] },
      ],
      children: [
        timeline("kid", "seconds", 1, { offset: [-1, 1] }),
        timeline("gone", "quarters", null, { offset: [9, 1] }),
        timeline("late", "quarters", [8, 1], { offset: [6, 1] }),
      ],
    });
    const value = manifest([first, timeline("second"), timeline("second")], {
      id: "g2",
      groups: [group("first", ["ghost", "second"]), group("g2", ["second"])],
      graphical: {
        order: {
          zz: [],
          kid: [
            "kid/children_1",
            "kid/conversion_maps_1",
            "kid",
            "kid/markers_1",
            "kid/regions_2",
            "kid/flow_control_1",
          ],
          g2: ["stranger"],
        },
      },
    });
    expect(problems(value)).toEqual([
      [
        ["timelines", 0, "flow_control", "jumps", 0, "target"],
        '"nowhere" names no marker of this timeline',
      ],
      [
        ["timelines", 0, "children", 0, "unit"],
        "child 'kid' has unit 'seconds', its parent 'first' has 'quarters'",
      ],
      [
        ["timelines", 0, "children", 1, "offset"],
        "offset [9, 1] of 'gone' is beyond the length [8, 1] of its parent 'first'",
      ],
      [
        ["timelines", 0, "children", 2, "length"],
        "child 'late' ends at [14, 1], beyond the length [8, 1] of its parent 'first'",
      ],
      [["timelines", 0, "regions", 0, "id"], 'id "end" is reserved for the parts of an address'],
      [
        ["timelines", 0, "regions", 1, "id"],
        'id "regions_3" is reserved for the bands of a timeline',
      ],
      [["timelines", 2, "id"], 'duplicate id "second", first at #/timelines/1/id'],
      [["groups", 0, "id"], 'duplicate id "first", first at #/timelines/0/id'],
      [["id"], 'duplicate id "g2", first at #/groups/1/id'],
      [["groups", 0, "members", 0], '"ghost" names no timeline of this manifest'],
      [["groups", 1, "members", 0], 'duplicate member "second", first at #/groups/0/members/1'],
      [["graphical", "order", "g2", 0], '"stranger" is not a member of group "g2"'],
      [["graphical", "order", "g2"], 'member "second" of group "g2" is missing'],
      [["graphical", "order", "kid", 4], '"kid/regions_2" is not "kid" or one of its bands'],
      [["graphical", "order", "kid"], '"kid/regions_1" is missing from the band order of "kid"'],
      [["graphical", "order", "zz"], '"zz" names no group or timeline of this manifest'],
    ]);
    expect(identityProblems(value).map((problem) => problem.code)).toEqual([
      "dangling_target",
      "child_unit",
      "child_offset",
      "child_end",
      ...Array<string>(2).fill("reserved_id"),
      ...Array<string>(2).fill("duplicate_id"),
      "manifest_id",
      ...Array<string>(2).fill("group_member"),
      ...Array<string>(2).fill("display_order"),
      ...Array<string>(2).fill("band_order"),
      "order_key",
    ]);
    expect(() => validate(value)).toThrow(identityProblems(value)[0]?.message);
  });
});
