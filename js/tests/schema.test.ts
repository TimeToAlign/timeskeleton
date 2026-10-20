import { Ajv2020 } from "ajv/dist/2020.js";
import { describe, expect, it } from "vitest";
import { DEFAULTS } from "../src/defaults.js";
import { schema } from "../src/generated/schema.js";
import { UNIT_NUMBER_TYPES } from "../src/validate.js";
import { loadSchemaFile } from "./fixtures.js";

type Node = Record<string, unknown>;

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
  "MeasureMap",
  "MeasureMapRow",
];

const MAP_TYPES = [
  "ChainMap",
  "CombinationMap",
  "ConstantMap",
  "FloatingMeasureMap",
  "LinearMap",
  "MeasureBeatMap",
  "MeasureNumberMap",
  "MeasureRecordMap",
  "PiecewiseMap",
  "TableMap",
];

const MEASURE_VIEWS: Readonly<Record<string, string | null>> = {
  FloatingMeasureMap: "floating_measures",
  MeasureBeatMap: null,
  MeasureNumberMap: null,
  MeasureRecordMap: null,
};

const document: Node = schema;
const defs = document.$defs as Record<string, Node>;
const properties = (name: string) => defs[name]?.properties as Record<string, Node>;
const target = (node: Node): Node =>
  typeof node.$ref === "string" ? (defs[node.$ref.slice("#/$defs/".length)] as Node) : node;
/** The conversion map types: the definitions `ConversionMap` chooses between. */
const mapTypes = ((defs.ConversionMap as Node).oneOf as Node[]).map((branch) =>
  (branch.$ref as string).slice("#/$defs/".length),
);

/** The defaults a definition declares, through references and its bases. */
function defaultsOf(definition: Node): Record<string, unknown> {
  const members = { ...((definition.properties ?? {}) as Record<string, Node>) };
  for (const entry of (definition.allOf ?? []) as Node[]) {
    for (const [key, value] of Object.entries(defaultsOf(target(entry)))) {
      if (!(key in members)) members[key] = { default: value };
    }
  }
  return Object.fromEntries(
    Object.entries(members)
      .map(([key, member]) => [key, "default" in member ? member : target(member)] as const)
      .filter(([, owner]) => "default" in owner)
      .map(([key, owner]) => [key, owner.default]),
  );
}

/** The keys a node declares, its `allOf` bases' included, at any depth. */
function declaredKeys(node: Node): Set<string> {
  const declared = new Set(Object.keys((node.properties ?? {}) as Node));
  for (const entry of (node.allOf ?? []) as Node[]) {
    for (const key of declaredKeys(target(entry))) declared.add(key);
  }
  return declared;
}

/** Every key of the document that begins with `x-`. */
function customKeys(node: unknown): string[] {
  if (Array.isArray(node)) return node.flatMap(customKeys);
  if (typeof node !== "object" || node === null) return [];
  const own = Object.keys(node).filter((key) => key.startsWith("x-"));
  return [...own, ...Object.values(node).flatMap(customKeys)];
}

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
    expect(references.map((node) => node.$ref)).toContain("#/$defs/Timeline");
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

  it("chooses between the ten map types", () => {
    expect(mapTypes).toEqual(MAP_TYPES);
    expect(properties("Selector").class?.enum).toEqual([
      "ContinuousLogicalTimeline",
      "ContinuousPhysicalTimeline",
      "ContinuousGraphicalTimeline",
      "DiscreteLogicalTimeline",
      "DiscretePhysicalTimeline",
      "DiscreteGraphicalTimeline",
      ...MAP_TYPES,
      "markers",
      "conversion_maps",
      "children",
      "regions",
      "flow_control",
    ]);
    expect(properties("MeasureView").source_unit?.const).toBe("quarters");
    for (const [name, unit] of Object.entries(MEASURE_VIEWS)) {
      expect(defs[name]?.allOf, name).toEqual([{ $ref: "#/$defs/MeasureView" }]);
      expect(properties(name).target_unit?.const, name).toBe(unit);
    }
  });

  it("states the default number type of every unit in the unit table", () => {
    const unit = defs.TimeUnit as Node;
    expect(unit.type).toBe("string");
    expect(unit.enum).toBeUndefined();
    const entries = unit.oneOf as Node[];
    expect(entries.map((entry) => entry.const)).toEqual(Object.keys(UNIT_NUMBER_TYPES));
    const pattern =
      /^(Logical|Physical|Graphical), (continuous|discrete); default number type (int|float|fraction)\.$/;
    for (const entry of entries) {
      expect(Object.keys(entry).sort()).toEqual(["const", "description"]);
      const match = pattern.exec(entry.description as string);
      expect(match?.[3]).toBe(UNIT_NUMBER_TYPES[entry.const as keyof typeof UNIT_NUMBER_TYPES]);
    }
  });

  it("defines a repeated shape once", () => {
    expect(defs.Name).toEqual({
      type: ["string", "null"],
      description: "Human-readable name, or null when none was given.",
      default: null,
    });
    expect(defs.Meta).toEqual({
      type: "object",
      additionalProperties: true,
      description: "Free-form metadata.",
      default: {},
    });
    const names = [
      "TimeSkeleton",
      "Timeline",
      "Group",
      "Region",
      "FlowControlElement",
      "MeasureMap",
      "MapBase",
    ];
    for (const owner of names) expect(properties(owner).name?.$ref).toBe("#/$defs/Name");
    const metas = [
      "TimeSkeleton",
      "Timeline",
      "Group",
      "Region",
      "FlowControlElement",
      "MeasureMap",
    ];
    for (const owner of metas) expect(properties(owner).meta?.$ref).toBe("#/$defs/Meta");
    for (const [node] of nodes(document)) {
      const members = (node.properties ?? {}) as Record<string, Node>;
      if ("meta" in members) expect(members.meta?.$ref).toBe("#/$defs/Meta");
      expect(members.name?.type).not.toEqual(["string", "null"]);
    }
  });

  it("extends the map base in every conversion map", () => {
    const base = defs.MapBase as Node;
    const baseKeys = Object.keys(base.properties as Node);
    expect(baseKeys).toEqual(["type", "id", "name", "source_unit", "target_unit"]);
    expect(base.required).toEqual(["type", "id", "source_unit", "target_unit"]);
    const view = defs.MeasureView as Node;
    expect(view.type).toBe("object");
    expect(view.allOf).toEqual([{ $ref: "#/$defs/MapBase" }]);
    expect(Object.keys(view.properties as Node)).toEqual(["source_unit", "measure_map"]);
    expect(properties("MeasureView").source_unit?.const).toBe("quarters");
    expect(view.required).toEqual(["measure_map"]);
    const bases = [...baseKeys, ...Object.keys(view.properties as Node)];
    for (const name of mapTypes) {
      const definition = defs[name] as Node;
      expect(definition.type).toBe("object");
      const parent = name in MEASURE_VIEWS ? "MeasureView" : "MapBase";
      expect(definition.allOf, name).toEqual([{ $ref: `#/$defs/${parent}` }]);
      const own = Object.keys(definition.properties as Node).filter((key) => bases.includes(key));
      const units = name in MEASURE_VIEWS ? ["target_unit"] : [];
      expect(own, name).toEqual(["type", ...units]);
      for (const key of units) expect(properties(name)[key], name).toHaveProperty("const");
      expect(properties(name).type).toEqual({ const: name });
      const required = definition.required as string[];
      expect(required).toContain("type");
      for (const key of ["id", "source_unit", "target_unit"]) expect(required).not.toContain(key);
    }
  });

  it("refers by ID and addresses by Address", () => {
    const selector = properties("Selector");
    expect(selector.within?.$ref).toBe("#/$defs/Id");
    expect(selector.ids?.items).toEqual({ $ref: "#/$defs/Address" });
    expect(properties("FlowControlElement").target?.$ref).toBe("#/$defs/Id");
    expect(properties("MeasureView").measure_map?.$ref).toBe("#/$defs/Id");
    const address = new Ajv2020({ strict: false }).compile({
      $ref: "#/$defs/Address",
      $defs: defs,
    });
    for (const accepted of ["score", "score/regions_1", "score/region_1/label", "a b/c"]) {
      expect(address(accepted), accepted).toBe(true);
    }
    for (const refused of ["", "/score", "score/", "score//label", "score/a\tb"]) {
      expect(address(refused), refused).toBe(false);
    }
  });

  it("keeps every object open without a custom keyword", () => {
    const all = [...nodes(document)].map(([node]) => node);
    expect(all.filter((node) => node.additionalProperties === false)).toEqual([]);
    expect(all.filter((node) => "unevaluatedProperties" in node)).toEqual([]);
    expect(customKeys(document)).toEqual([]);
    expect(all.filter((node) => node.additionalProperties === true)).toEqual([defs.Meta]);
    expect(defs.Meta?.properties).toBeUndefined();
  });

  it("declares on every object what its branches and arms declare", () => {
    for (const [node, inside] of nodes(document)) {
      if (inside || node.type !== "object" || node.properties === undefined) continue;
      const declared = declaredKeys(node);
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

  it("tags every branch of a discriminated union with a distinct constant", () => {
    const unions = [...nodes(document)].filter(([node]) => "discriminator" in node);
    expect(unions.map(([node]) => (node.discriminator as Node).propertyName).sort()).toEqual([
      "number_type",
      "type",
    ]);
    for (const [node] of unions) {
      const key = (node.discriminator as Node).propertyName as string;
      const tags = (node.oneOf as Node[]).map(
        (branch) => ((target(branch).properties as Record<string, Node>)[key] as Node).const,
      );
      expect(tags.every((tag) => typeof tag === "string")).toBe(true);
      expect(new Set(tags).size).toBe(tags.length);
      const required = (branch: Node) => (target(branch).required ?? node.required) as string[];
      for (const branch of node.oneOf as Node[]) expect(required(branch)).toContain(key);
    }
  });

  it("declares the defaults of the table and no other", () => {
    type Kind = keyof typeof DEFAULTS;
    const kinds: Partial<Record<Kind, string[]>> = {
      manifest: ["TimeSkeleton"],
      timeline: ["Timeline"],
      region: ["Region"],
      measure_map: ["MeasureMap"],
      group: ["Group"],
      graphical: ["Graphical"],
    };
    const own: Readonly<Record<string, Kind>> = { LinearMap: "linear_map", TableMap: "table_map" };
    const element = ["flow_control_element", "repeat_end"];
    expect(
      [...Object.keys(kinds), "conversion_map", ...Object.values(own), ...element].sort(),
    ).toEqual(Object.keys(DEFAULTS).sort());
    const covered = new Set<string>(["MapBase", "MeasureView", "FlowControlElement"]);
    const flowControl = defs.FlowControlElement as Node;
    expect(defaultsOf(flowControl)).toEqual(DEFAULTS.flow_control_element);
    const repeatEnd = (flowControl.then as Node).else as Node;
    expect(((repeatEnd.if as Node).properties as Node).manifestation).toEqual({
      const: "repeat_end",
    });
    expect(defaultsOf(repeatEnd.then as Node)).toEqual(DEFAULTS.repeat_end);
    for (const [kind, names] of Object.entries(kinds)) {
      for (const name of names) {
        covered.add(name);
        expect(defaultsOf(defs[name] as Node), name).toEqual(DEFAULTS[kind as Kind]);
      }
    }
    for (const name of mapTypes) {
      covered.add(name);
      const added = Object.hasOwn(own, name) ? DEFAULTS[own[name] as Kind] : {};
      expect(defaultsOf(defs[name] as Node), name).toEqual({
        ...DEFAULTS.conversion_map,
        ...added,
      });
    }
    for (const [name, definition] of Object.entries(defs)) {
      if (!covered.has(name)) expect(defaultsOf(definition), name).toEqual({});
    }
    expect(properties("Timeline").number_type?.default).toBeUndefined();
  });
});
