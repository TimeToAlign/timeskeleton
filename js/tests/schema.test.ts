import { describe, expect, it } from "vitest";
import { DEFAULTS, schema } from "../src/index.js";
import { loadSchemaFile } from "./fixtures.js";

type Node = Record<string, unknown>;

const UNKNOWN = { "x-unknown-key": true };
const TIMELINE_CLASSES = [
  "ContinuousLogicalTimeline",
  "ContinuousPhysicalTimeline",
  "ContinuousGraphicalTimeline",
  "DiscreteLogicalTimeline",
  "DiscretePhysicalTimeline",
  "DiscreteGraphicalTimeline",
];
const MAP_TYPES = [
  "BeatInMeasureMap",
  "ChainMap",
  "CombinationMap",
  "ConstantMap",
  "FloorMap",
  "InterpolationMap",
  "IntervalToConstantMap",
  "LinearMap",
  "MetricMap",
  "MetricalPositionMap",
  "PiecewiseMap",
  "QuartersToFloatingMeasures",
  "QuartersToMeasureNumber",
  "QuartersToTicks",
  "RotationMap",
  "SamplesToSeconds",
  "ScalarMap",
  "SecondsToSamples",
  "ShiftMap",
  "TableMap",
  "TicksToQuarters",
];
const PUBLIC = [
  "TimeSkeleton",
  "Timeline",
  "Group",
  "Graphical",
  "ConversionMap",
  "Coordinate",
  "Number",
  "Fraction",
  "TimeUnit",
  "NumberType",
  "Id",
  "MeasureMapRow",
];

const document = schema as unknown as Node;
const defs = document.$defs as Record<string, Node>;
const properties = (name: string) => defs[name]?.properties as Record<string, Node>;

/** Every schema node with whether it lies in a branch or an arm. */
function* nodes(node: unknown, inside = false): Generator<[Node, boolean]> {
  if (Array.isArray(node)) {
    for (const item of node) yield* nodes(item, inside);
    return;
  }
  if (typeof node !== "object" || node === null) return;
  const value = node as Node;
  yield [value, inside];
  for (const [key, child] of Object.entries(value)) {
    if (["oneOf", "anyOf", "if", "then", "else"].includes(key)) yield* nodes(child, true);
    else if (key === "properties" || key === "$defs") {
      for (const member of Object.values(child as Node)) yield* nodes(member, false);
    } else if (!["default", "const", "enum"].includes(key)) yield* nodes(child, inside);
  }
}

describe("the schema document", () => {
  it("is the bundled file, with one root", () => {
    expect(JSON.parse(JSON.stringify(loadSchemaFile()))).toEqual(document);
    expect(document.$id).toBe(
      "https://timetoalign.github.io/timeskeleton/0.7.0/timeskeleton.schema.json",
    );
    expect(document.$schema).toBe("https://json-schema.org/draft/2020-12/schema");
    expect(document.$ref).toBe("#/$defs/TimeSkeleton");
  });

  it("refers locally, without anchors", () => {
    const all = [...nodes(document)].map(([node]) => node);
    const references = all.filter((node) => typeof node.$ref === "string");
    expect(references.length).toBeGreaterThan(0);
    for (const node of references) {
      const reference = node.$ref as string;
      expect(reference.startsWith("#/$defs/")).toBe(true);
      expect(Object.hasOwn(defs, reference.slice("#/$defs/".length))).toBe(true);
    }
    expect(all.filter((node) => "$anchor" in node)).toEqual([]);
  });

  it("holds the public definitions and none of the former ones", () => {
    for (const name of PUBLIC) expect(Object.hasOwn(defs, name)).toBe(true);
    for (const name of [
      "Meta",
      "TimelineClass",
      "TimelineManifest",
      "Bundle",
      "GroupGraphical",
      "BundleGraphical",
      "CoordinateNonnegative",
    ]) {
      expect(Object.hasOwn(defs, name)).toBe(false);
    }
  });

  it("states the manifest", () => {
    expect(Object.keys(properties("TimeSkeleton"))).toEqual([
      "$schema",
      "timeskeleton",
      "id",
      "name",
      "meta",
      "timelines",
      "groups",
      "graphical",
    ]);
    expect(defs.TimeSkeleton?.required).toEqual(["timeskeleton", "timelines"]);
    expect(properties("TimeSkeleton").timeskeleton?.const).toBe("0.7.0");
    expect(properties("TimeSkeleton").$schema?.type).toBe("string");
  });

  it("states the timeline", () => {
    const timeline = properties("Timeline");
    expect(Object.keys(timeline)).toEqual([
      "id",
      "name",
      "unit",
      "number_type",
      "length",
      "offset",
      "locked",
      "is_segment_line",
      "meta",
      "children",
      "conversion_maps",
      "regions",
      "flow_control",
      "measure_map",
      "metric_hierarchy",
    ]);
    expect(defs.Timeline?.required).toEqual(["id", "unit", "length"]);
    expect(timeline.length?.anyOf).toEqual([
      { $ref: "#/$defs/NumberNonnegative" },
      { type: "null" },
    ]);
    expect(timeline.offset?.$ref).toBe("#/$defs/Number");
    expect(timeline.children?.items).toEqual({ $ref: "#/$defs/Timeline", required: ["offset"] });
    expect(timeline.locked?.description).toBe("Whether the timeline's length is fixed.");
    for (const [name, keys] of [
      ["Region", ["start", "end"]],
      ["Break", ["coordinate"]],
      ["Jump", ["from_coordinate", "to_coordinate"]],
      ["Marker", ["coordinate"]],
    ] as const) {
      for (const key of keys) expect(properties(name)[key]).toEqual({ $ref: "#/$defs/Number" });
    }
  });

  it("states groups, the graphical block and the conversion maps", () => {
    expect(Object.keys(properties("Group"))).toEqual(["id", "name", "meta", "members"]);
    expect(defs.Group?.required).toEqual(["id", "members"]);
    expect(Object.keys(properties("Graphical"))).toEqual(["styles", "statements", "order"]);
    expect(defs.Graphical?.required).toBeUndefined();
    expect(properties("Graphical").order?.propertyNames).toEqual({ $ref: "#/$defs/Id" });
    expect(properties("Graphical").order?.additionalProperties).toEqual({
      $ref: "#/$defs/MemberOrder",
    });
    expect([...nodes(document)].filter(([node]) => "support_policy" in node)).toEqual([]);
    for (const name of MAP_TYPES) {
      const members = properties(name);
      expect(members.type?.const).toBe(name);
      expect(Object.hasOwn(members, "name")).toBe(true);
      const required = defs[name]?.required as string[];
      expect([...required].sort()).toEqual(
        Object.keys(members)
          .filter((k) => k !== "name")
          .sort(),
      );
    }
  });

  it("keeps every object open and marks its unknown keys", () => {
    const all = [...nodes(document)];
    expect(all.filter(([node]) => node.additionalProperties === false)).toEqual([]);
    let marked = 0;
    for (const [node, inside] of all) {
      const object = node.type === "object" && "properties" in node;
      if (!inside && object) {
        expect(node.unevaluatedProperties).toEqual(UNKNOWN);
        marked += 1;
      } else expect(node.unevaluatedProperties).toBeUndefined();
    }
    expect(marked).toBe(MAP_TYPES.length + 14);
    for (const node of [
      properties("TimeSkeleton").meta,
      properties("Timeline").meta,
      properties("Timeline").metric_hierarchy,
      properties("Region").meta,
      properties("Break").meta,
      properties("Jump").meta,
      properties("Group").meta,
    ]) {
      expect(node?.additionalProperties).toBe(true);
      expect(node?.properties).toBeUndefined();
    }
  });

  it("declares on every marked object what its branches and arms declare", () => {
    for (const [node, inside] of nodes(document)) {
      if (inside || node.unevaluatedProperties === undefined) continue;
      const declared = new Set(Object.keys(node.properties as Node));
      expect(node.patternProperties).toBeUndefined();
      const branches = [
        ...((node.oneOf ?? []) as Node[]),
        ...((node.anyOf ?? []) as Node[]),
        ...(["if", "then", "else"].map((key) => node[key] ?? {}) as Node[]),
      ];
      for (const branch of branches) {
        for (const key of Object.keys((branch.properties ?? {}) as Node)) {
          expect(declared.has(key)).toBe(true);
        }
      }
    }
  });

  it("declares the defaults of the table and no other", () => {
    const kinds: Record<keyof typeof DEFAULTS, string[]> = {
      manifest: ["TimeSkeleton"],
      timeline: ["Timeline"],
      flow_control: ["FlowControl"],
      region: ["Region"],
      break: ["Break"],
      jump: ["Jump"],
      marker: ["Marker"],
      conversion_map: MAP_TYPES,
      group: ["Group"],
      graphical: ["Graphical"],
    };
    expect(Object.keys(kinds).sort()).toEqual(Object.keys(DEFAULTS).sort());
    const covered = new Set<string>();
    for (const [kind, names] of Object.entries(kinds)) {
      for (const name of names) {
        covered.add(name);
        const declared = Object.fromEntries(
          Object.entries(properties(name))
            .filter(([, member]) => "default" in member)
            .map(([key, member]) => [key, member.default]),
        );
        expect(declared).toEqual(DEFAULTS[kind as keyof typeof DEFAULTS]);
      }
    }
    for (const [name, definition] of Object.entries(defs)) {
      if (covered.has(name)) continue;
      const members = Object.values((definition.properties ?? {}) as Record<string, Node>);
      expect(members.filter((member) => "default" in member)).toEqual([]);
    }
    expect(properties("Timeline").number_type?.default).toBeUndefined();
  });

  it("states the vocabulary", () => {
    expect(defs.TimeUnit?.enum).toHaveLength(16);
    expect(defs.NumberType?.enum).toEqual(["int", "float", "fraction"]);
    expect(defs.Id?.pattern).toBe("^[^/\\u0000-\\u001f]+$");
    expect(defs.ElementType?.enum).toEqual([
      "block",
      "timeline",
      "child",
      "map",
      "region",
      "break",
      "jump",
      "wedge",
      "name",
      "label",
      "boundary",
      "ancestor",
      "group",
      "card",
    ]);
    const selector = properties("Selector");
    expect(Object.keys(selector)).toEqual([
      "element",
      "ids",
      "domain",
      "modality",
      "class",
      "within",
      "inside",
    ]);
    expect(selector.class?.enum).toEqual([...TIMELINE_CLASSES, ...MAP_TYPES]);
    expect(Object.keys(properties("Declaration"))).toEqual([
      "stroke",
      "stroke-width",
      "stroke-dasharray",
      "fill",
      "opacity",
      "font-size",
      "rx",
      "display",
      "side",
      "content",
      "max-width",
      "shadow",
    ]);
    expect(defs.Paint?.pattern).toBe("^(#[0-9A-F]{6}|none)$");
  });
});
