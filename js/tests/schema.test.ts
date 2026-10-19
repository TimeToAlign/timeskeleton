import { describe, expect, it } from "vitest";
import { DEFAULTS } from "../src/defaults.js";
import { schema } from "../src/generated/schema.js";
import { UNIT_NUMBER_TYPES } from "../src/validate.js";
import { loadSchemaFile } from "./fixtures.js";

type Node = Record<string, unknown>;

const UNKNOWN = { "x-unknown-key": true };
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

const document: Node = schema;
const defs = document.$defs as Record<string, Node>;
const properties = (name: string) => defs[name]?.properties as Record<string, Node>;
const target = (node: Node): Node =>
  typeof node.$ref === "string" ? (defs[node.$ref.slice("#/$defs/".length)] as Node) : node;
/** The conversion map types: the definitions `ConversionMap` chooses between. */
const mapTypes = ((defs.ConversionMap as Node).oneOf as Node[]).map((branch) =>
  (branch.$ref as string).slice("#/$defs/".length),
);

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

  it("keeps every object open and marks its unknown keys", () => {
    const all = [...nodes(document)];
    expect(all.filter(([node]) => node.additionalProperties === false)).toEqual([]);
    const marked: Node[] = [];
    for (const [node, inside] of all) {
      const object = node.type === "object" && "properties" in node;
      if (!inside && object) {
        expect(node.unevaluatedProperties).toEqual(UNKNOWN);
        marked.push(node);
      } else expect(node.unevaluatedProperties).toBeUndefined();
    }
    for (const name of ["TimeSkeleton", "Timeline", "Group", "Graphical", ...mapTypes]) {
      expect(marked).toContain(defs[name]);
    }
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
    const kinds: Record<keyof typeof DEFAULTS, string[]> = {
      manifest: ["TimeSkeleton"],
      timeline: ["Timeline"],
      flow_control: ["FlowControl"],
      region: ["Region"],
      break: ["Break"],
      jump: ["Jump"],
      marker: ["Marker"],
      conversion_map: mapTypes,
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
});
