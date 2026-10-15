import { describe, expect, it } from "vitest";
import {
  identityProblems,
  JsonFloat,
  parseJson,
  SchemaValidationError,
  validate,
} from "../src/index.js";
import { bundle, group, manifest, rejectionText, timeline } from "./fixtures.js";

type JsonObject = Record<string, unknown>;
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

  const partWordDocuments = (word: string): [JsonObject, (string | number)[]][] => {
    const shift = { type: "ShiftMap", id: word, source_unit: null, target_unit: null, offset: 1 };
    const flow: Record<string, JsonObject[]> = {
      breaks: [{ id: word, coordinate: [1, 1] }],
      jumps: [{ id: word, from_coordinate: [1, 1], to_coordinate: [0, 1] }],
      markers: [{ id: word, coordinate: [1, 1] }],
    };
    return [
      [manifest([timeline(word)]), ["timelines", 0, "id"]],
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
      for (const [document, path] of partWordDocuments(word)) {
        expect(only(document)).toEqual([
          path,
          `id ${JSON.stringify(word)} is reserved for the parts of an address`,
        ]);
      }
    },
  );

  it.each(["starts", "Start"])("accepts %s as any id", (word) => {
    for (const [document] of partWordDocuments(word)) validate(document);
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
      '"g9" names no group of this manifest',
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
    const testCase = parseJson(rejectionText(`${name}.json`)) as JsonObject;
    expect(only(testCase.manifest as JsonObject)).toEqual([testCase.path, message]);
  });

  it("reports every step in order", () => {
    const first = timeline("first", "quarters", [8, 1], {
      flow_control: {
        jumps: [{ id: "j", from_coordinate: [1, 1], to_coordinate: [0, 1], target: "nowhere" }],
      },
      regions: [{ id: "end", start: [0, 1], end: [1, 1] }],
      children: [
        timeline("kid", "seconds", 1, { offset: [-1, 1] }),
        timeline("gone", "quarters", null, { offset: [9, 1] }),
        timeline("late", "quarters", [8, 1], { offset: [6, 1] }),
      ],
    });
    const value = manifest([first, timeline("second"), timeline("second")], {
      id: "g2",
      groups: [group("first", ["ghost", "second"]), group("g2", ["second"])],
      graphical: { order: { zz: [], g2: ["stranger"] } },
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
      [["timelines", 2, "id"], 'duplicate id "second", first at #/timelines/1/id'],
      [["groups", 0, "id"], 'duplicate id "first", first at #/timelines/0/id'],
      [["id"], 'duplicate id "g2", first at #/groups/1/id'],
      [["groups", 0, "members", 0], '"ghost" names no timeline of this manifest'],
      [["groups", 1, "members", 0], 'duplicate member "second", first at #/groups/0/members/1'],
      [["graphical", "order", "g2", 0], '"stranger" is not a member of group "g2"'],
      [["graphical", "order", "g2"], 'member "second" of group "g2" is missing'],
      [["graphical", "order", "zz"], '"zz" names no group of this manifest'],
    ]);
  });
});
