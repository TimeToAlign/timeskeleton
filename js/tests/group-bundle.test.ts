import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  canonicalOrder,
  compactJson,
  dumps,
  identityProblems,
  type Json,
  type Lossless,
  parseJson,
  SchemaValidationError,
  validate,
} from "../src/index.js";
import { bundleDocument, groupDocument, repositoryRoot } from "./fixtures.js";

type JsonObject = Record<string, unknown>;

function problemsOf(value: JsonObject): [unknown, string][] {
  return identityProblems(value as never).map((problem) => [problem.path, problem.detail]);
}

function at(value: number): JsonObject {
  return { unit: "quarters", number_type: "fraction", value: [value, 1] };
}

function jump(target: string): JsonObject {
  return {
    id: "jump_1",
    from_coordinate: at(4),
    to_coordinate: at(0),
    control_type: "repeat_end",
    condition: "always",
    repeat_count: 1,
    target,
    label: null,
    meta: {},
  };
}

function marker(id: string): JsonObject {
  return { id, name: null, coordinate: at(1) };
}

const roots = (value: JsonObject) => value.timelines as JsonObject[];
const flow = (timeline: JsonObject) => timeline.flow_control as JsonObject;
const group = (value: JsonObject) => value.group as JsonObject;
const groups = (value: JsonObject) => (value.bundle as JsonObject).groups as JsonObject[];
const graphical = (value: JsonObject) => value.graphical as JsonObject;
const orders = (value: JsonObject) => graphical(value).order as JsonObject;
const child = (timeline: JsonObject, key: string) =>
  ((timeline.children as JsonObject)[key] as JsonObject).timeline as JsonObject;

describe("identityProblems of group and bundle files", () => {
  it("finds none in the test documents", () => {
    expect(problemsOf(groupDocument())).toEqual([]);
    expect(problemsOf(bundleDocument())).toEqual([]);
  });

  it("lets elements of different roots share an id", () => {
    const value = bundleDocument();
    for (const root of roots(value).slice(0, 2)) flow(root).markers = [marker("m")];
    expect(problemsOf(value)).toEqual([]);
  });

  it("makes each root its own scope", () => {
    const value = groupDocument();
    const recording = roots(value)[1] as JsonObject;
    flow(recording).jumps = [jump("nowhere")];
    flow(recording).markers = [marker("recording")];
    expect(problemsOf(value)).toEqual([
      [
        ["timelines", 1, "flow_control", "markers", 0, "id"],
        'duplicate id "recording", first at #/timelines/1/id',
      ],
      [
        ["timelines", 1, "flow_control", "jumps", 0, "target"],
        '"nowhere" names no marker of this timeline',
      ],
    ]);
  });

  it("keeps timeline ids unique across the file", () => {
    const value = bundleDocument();
    const [, , performance, recording, score] = roots(value) as [
      JsonObject,
      JsonObject,
      JsonObject,
      JsonObject,
      JsonObject,
    ];
    (score.children as JsonObject).excerpt = structuredClone(
      (recording.children as JsonObject).excerpt,
    );
    performance.id = "page";
    (groups(value)[0] as JsonObject).members = ["page", "score"];
    delete value.graphical;
    expect(problemsOf(value)).toEqual([
      [["timelines", 2, "id"], 'duplicate id "page", first at #/timelines/1/id'],
      [
        ["timelines", 4, "children", "excerpt", "timeline", "id"],
        'duplicate id "excerpt", first at #/timelines/3/children/excerpt/timeline/id',
      ],
      [
        ["bundle", "groups", 1, "members", 1],
        'duplicate member "page", first at #/bundle/groups/0/members/0',
      ],
    ]);
  });

  it("reports a repetition within one root once", () => {
    const value = groupDocument();
    child(roots(value)[0] as JsonObject, "second-half").id = "piece";
    group(value).members = ["piece", "recording"];
    graphical(value).order = ["piece", "recording"];
    expect(problemsOf(value)).toEqual([
      [
        ["timelines", 0, "children", "second-half", "timeline", "id"],
        'duplicate id "piece", first at #/timelines/0/id',
      ],
    ]);
  });

  it("keeps group ids apart from timeline ids", () => {
    const value = groupDocument();
    group(value).id = "second-half";
    expect(problemsOf(value)).toEqual([
      [
        ["group", "id"],
        'duplicate id "second-half", first at #/timelines/0/children/second-half/timeline/id',
      ],
    ]);
    const bundle = bundleDocument();
    for (const entry of groups(bundle)) entry.id = "score";
    graphical(bundle).order = { score: ["score", "performance"] };
    expect(problemsOf(bundle)).toEqual([
      [["bundle", "groups", 0, "id"], 'duplicate id "score", first at #/timelines/4/id'],
      [["bundle", "groups", 1, "id"], 'duplicate id "score", first at #/timelines/4/id'],
    ]);
  });

  it("keeps group ids unique among the groups", () => {
    const value = bundleDocument();
    (groups(value)[1] as JsonObject).id = "group_1";
    delete orders(value).group_2;
    expect(problemsOf(value)).toEqual([
      [["bundle", "groups", 1, "id"], 'duplicate id "group_1", first at #/bundle/groups/0/id'],
    ]);
  });

  it("requires members to name timelines of the file", () => {
    const value = groupDocument();
    group(value).members = ["recording", "second-half", "tempo"];
    (graphical(value).order as string[]).push("tempo");
    expect(problemsOf(value)).toEqual([
      [["group", "members", 2], '"tempo" names no timeline of this file'],
    ]);
    const bundle = bundleDocument();
    (groups(bundle)[1] as JsonObject).members = ["excerpt", "page", "score"];
    (orders(bundle).group_2 as string[]).push("score");
    expect(problemsOf(bundle)).toEqual([
      [
        ["bundle", "groups", 1, "members", 2],
        'duplicate member "score", first at #/bundle/groups/0/members/1',
      ],
    ]);
  });

  it("refuses a member nested with another member of its group", () => {
    const value = groupDocument();
    group(value).members = ["piece", "recording", "second-half"];
    (graphical(value).order as string[]).push("piece");
    expect(problemsOf(value)).toEqual([
      [
        ["group", "members", 2],
        'member "second-half" lies inside member "piece" of the same group',
      ],
    ]);
    const bundle = bundleDocument();
    (groups(bundle)[1] as JsonObject).members = ["excerpt", "page", "recording", "tempo"];
    (orders(bundle).group_2 as string[]).push("recording", "tempo");
    expect(problemsOf(bundle)).toEqual([
      [
        ["bundle", "groups", 1, "members", 2],
        'member "recording" contains member "excerpt" of the same group',
      ],
      [["bundle", "groups", 1, "members", 3], '"tempo" names no timeline of this file'],
    ]);
  });

  it("checks a member of two groups in each", () => {
    const value = bundleDocument();
    const [first, second] = groups(value) as [JsonObject, JsonObject];
    first.members = ["excerpt", "performance", "score"];
    second.members = ["excerpt", "page", "recording"];
    graphical(value).order = {};
    expect(problemsOf(value)).toEqual([
      [
        ["bundle", "groups", 1, "members", 0],
        'duplicate member "excerpt", first at #/bundle/groups/0/members/0',
      ],
      [
        ["bundle", "groups", 1, "members", 2],
        'member "recording" contains member "excerpt" of the same group',
      ],
    ]);
  });

  it("allows a parent and its child in different groups", () => {
    const value = bundleDocument();
    (groups(value)[0] as JsonObject).members = ["performance", "recording", "score"];
    (orders(value).group_1 as string[]).push("recording");
    expect(problemsOf(value)).toEqual([]);
    expect(() => validate(value)).not.toThrow();
  });

  it("requires every root of a group file to contain a member", () => {
    const value = groupDocument();
    group(value).members = ["second-half"];
    graphical(value).order = ["second-half"];
    expect(problemsOf(value)).toEqual([
      [["timelines", 1], 'timeline "recording" contains no member of the group'],
    ]);
  });

  it("needs no member in a bundle's root", () => {
    const value = bundleDocument();
    (value.bundle as JsonObject).groups = [];
    graphical(value).order = {};
    expect(problemsOf(value)).toEqual([]);
  });

  it.each([
    [
      ["second-half"],
      [[["graphical", "order"], 'member "recording" of group "group_1" is missing']],
    ],
    [
      ["second-half", "piece", "recording"],
      [[["graphical", "order", 1], '"piece" is not a member of group "group_1"']],
    ],
    [
      ["piece"],
      [
        [["graphical", "order", 0], '"piece" is not a member of group "group_1"'],
        [["graphical", "order"], 'member "recording" of group "group_1" is missing'],
        [["graphical", "order"], 'member "second-half" of group "group_1" is missing'],
      ],
    ],
  ])("requires the order %j to be a permutation", (order, expected) => {
    const value = groupDocument();
    graphical(value).order = order;
    expect(problemsOf(value)).toEqual(expected);
  });

  it("accepts an absent order", () => {
    const value = groupDocument();
    delete value.graphical;
    const bundle = bundleDocument();
    delete orders(bundle).group_2;
    expect(problemsOf(value)).toEqual([]);
    expect(problemsOf(bundle)).toEqual([]);
    delete bundle.graphical;
    expect(problemsOf(bundle)).toEqual([]);
  });

  it("visits a bundle's orders in code-point order of their keys", () => {
    const value = bundleDocument();
    const order = orders(value);
    order["\u{1F600}"] = [];
    order["\u{FB00}"] = [];
    order.group_2 = ["page"];
    expect(problemsOf(value)).toEqual([
      [["graphical", "order", "group_2"], 'member "excerpt" of group "group_2" is missing'],
      [["graphical", "order", "\u{FB00}"], '"\u{FB00}" names no group of this bundle'],
      [["graphical", "order", "\u{1F600}"], '"\u{1F600}" names no group of this bundle'],
    ]);
  });

  it("lists the problems in the stated order", () => {
    const value = bundleDocument();
    flow(roots(value)[0] as JsonObject).jumps = [jump("nowhere")];
    (roots(value)[1] as JsonObject).id = "annotations";
    const [first, second] = groups(value) as JsonObject[];
    (first as JsonObject).id = "recording";
    (first as JsonObject).members = ["performance", "score", "tempo"];
    (second as JsonObject).members = ["excerpt", "score"];
    graphical(value).order = { group_9: [], group_2: ["excerpt", "page", "score"] };
    expect(problemsOf(value)).toEqual([
      [
        ["timelines", 0, "flow_control", "jumps", 0, "target"],
        '"nowhere" names no marker of this timeline',
      ],
      [["timelines", 1, "id"], 'duplicate id "annotations", first at #/timelines/0/id'],
      [["bundle", "groups", 0, "id"], 'duplicate id "recording", first at #/timelines/3/id'],
      [["bundle", "groups", 0, "members", 2], '"tempo" names no timeline of this file'],
      [
        ["bundle", "groups", 1, "members", 1],
        'duplicate member "score", first at #/bundle/groups/0/members/1',
      ],
      [["graphical", "order", "group_2", 1], '"page" is not a member of group "group_2"'],
      [["graphical", "order", "group_9"], '"group_9" names no group of this bundle'],
    ]);
    try {
      validate(value);
      throw new Error("value was accepted");
    } catch (error) {
      expect(error).toBeInstanceOf(SchemaValidationError);
      expect((error as SchemaValidationError).path).toEqual([
        "timelines",
        0,
        "flow_control",
        "jumps",
        0,
        "target",
      ]);
    }
  });
});

describe("the canonical order of group and bundle files", () => {
  it("orders a group file's roots and members, not its display order", () => {
    const value = groupDocument();
    roots(value).reverse();
    (group(value).members as string[]).reverse();
    (roots(value)[0] as JsonObject).regions = [
      { id: "late", name: null, start: at(4), end: at(8), meta: {} },
      { id: "early", name: null, start: at(0), end: at(8), meta: {} },
    ];
    const given = structuredClone(value);
    const result = canonicalOrder(value);
    expect(value).toEqual(given);
    expect(roots(result).map((root) => root.id)).toEqual(["piece", "recording"]);
    expect(group(result).members).toEqual(["recording", "second-half"]);
    expect(graphical(result).order).toEqual(["second-half", "recording"]);
    const regions = (roots(result)[1] as JsonObject).regions as JsonObject[];
    expect(regions.map((region) => region.id)).toEqual(["early", "late"]);
    validate(result);
  });

  it("orders a bundle file's roots, groups and members, not its display orders", () => {
    const value = bundleDocument();
    groups(value).reverse();
    for (const entry of groups(value)) (entry.members as string[]).reverse();
    roots(value).reverse();
    graphical(value).order = { group_2: ["excerpt", "page"], group_1: ["performance", "score"] };
    const result = canonicalOrder(value);
    expect(roots(result).map((root) => root.id)).toEqual([
      "annotations",
      "page",
      "performance",
      "recording",
      "score",
    ]);
    expect(groups(result).map((entry) => entry.id)).toEqual(["group_1", "group_2"]);
    expect(groups(result).map((entry) => entry.members)).toEqual([
      ["performance", "score"],
      ["excerpt", "page"],
    ]);
    expect(orders(result)).toEqual({
      group_2: ["excerpt", "page"],
      group_1: ["performance", "score"],
    });
    validate(result);
  });

  it("orders members by code point", () => {
    const value = { group: { members: ["\u{1F600}", "\u{FB00}", "b"] } };
    expect(canonicalOrder(value).group.members).toEqual(["b", "\u{FB00}", "\u{1F600}"]);
  });

  it.each([{ group: { members: ["a", 5] } }, { bundle: { groups: [{ members: [5, "a"] }] } }])(
    "refuses a member that is no string in %j",
    (value) => {
      expect(() => canonicalOrder(value)).toThrow(TypeError);
    },
  );

  it("writes both test documents, every array reversed, as Python does", () => {
    const documents = [groupDocument(), bundleDocument()];
    const reversed = documents.map((value) => {
      const copy = structuredClone(value);
      roots(copy).reverse();
      if (copy.group !== undefined) (group(copy).members as string[]).reverse();
      if (copy.bundle !== undefined) {
        groups(copy).reverse();
        for (const entry of groups(copy)) (entry.members as string[]).reverse();
      }
      return compactJson(copy as Lossless<Json>);
    });
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
    expect(written).toEqual(documents.map((value) => dumps(value)));
  });
});
