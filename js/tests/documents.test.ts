import { describe, expect, it } from "vitest";
import {
  dumps,
  FILE_KINDS,
  fileKind,
  parse,
  SchemaValidationError,
  schemaDocuments,
  schemas,
  validate,
} from "../src/index.js";
import { bundleDocument, groupDocument } from "./fixtures.js";

type JsonObject = Record<string, unknown>;

const BASE = "https://timetoalign.github.io/timeskeleton/0.7.0/";
const ID_PATTERN = "^[^/\\u0000-\\u001f]+$";
const ID = "core.schema.json#/$defs/Id";
const NAMES = ["core", "timeline", "group", "bundle"] as const;
const CORE = [
  "Coordinate",
  "CoordinateNonnegative",
  "Fraction",
  "FractionNonnegative",
  "FractionPositive",
  "Id",
  "Meta",
  "Number",
  "NumberNonnegative",
  "NumberPositive",
  "NumberType",
  "TimeUnit",
];
const REFERENCE = /^(?:(core|timeline|group|bundle)\.schema\.json)?#\/\$defs\/(\w+)$/;

const documents = schemaDocuments["0.7.0"] as unknown as Record<string, JsonObject>;

function definitionsOf(name: string): JsonObject {
  return (documents[name] as JsonObject).$defs as JsonObject;
}

function references(value: unknown): string[] {
  if (Array.isArray(value)) return value.flatMap(references);
  if (typeof value !== "object" || value === null) return [];
  const node = value as JsonObject;
  const own = typeof node.$ref === "string" ? [node.$ref] : [];
  return [...own, ...Object.values(node).flatMap(references)];
}

/** Undo the move into core: local references, the id rule written inline. */
function inline(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(inline);
  if (typeof value !== "object" || value === null) return value;
  const node = value as JsonObject;
  if (node.$ref === ID) {
    const { $ref: _, ...rest } = node;
    return { type: "string", pattern: ID_PATTERN, ...rest };
  }
  return Object.fromEntries(
    Object.entries(node).map(([key, item]) => {
      if (key === "propertyNames" && JSON.stringify(item) === JSON.stringify({ $ref: ID })) {
        return [key, { pattern: ID_PATTERN }];
      }
      if (key === "$ref") return [key, (item as string).replace("core.schema.json#", "#")];
      return [key, inline(item)];
    }),
  );
}

function rejection(value: unknown): SchemaValidationError {
  try {
    validate(value);
  } catch (error) {
    if (error instanceof SchemaValidationError) return error;
    throw error;
  }
  throw new Error("value was accepted");
}

describe("the 0.7.0 schema documents", () => {
  it("are four, each at its $id", () => {
    expect(Object.keys(documents)).toEqual([...NAMES]);
    for (const name of NAMES) {
      expect((documents[name] as JsonObject).$id).toBe(`${BASE}${name}.schema.json`);
      expect((documents[name] as JsonObject).$schema).toBe(
        "https://json-schema.org/draft/2020-12/schema",
      );
    }
  });

  it("refer to each other only locally or relatively, and every reference resolves", () => {
    for (const name of NAMES) {
      for (const reference of references(documents[name])) {
        const match = REFERENCE.exec(reference);
        expect(match, `${name}: ${reference}`).not.toBeNull();
        const target = match?.[1] ?? name;
        expect(Object.keys(definitionsOf(target)), reference).toContain(match?.[2]);
      }
    }
  });

  it("give every definition a name of its own", () => {
    const names = NAMES.flatMap((name) => Object.keys(definitionsOf(name)));
    expect(new Set(names).size).toBe(names.length);
    expect(Object.keys(definitionsOf("core")).sort()).toEqual(CORE);
  });

  it("hold the definitions of 0.6.0, moved into core and timeline", () => {
    const legacy = schemas["0.6.0"] as unknown as JsonObject;
    const moved = Object.fromEntries(
      Object.entries({ ...definitionsOf("core"), ...definitionsOf("timeline") })
        .filter(([name]) => name !== "Id" && name !== "Meta")
        .map(([name, definition]) => [name, inline(definition)]),
    );
    const manifest = moved.TimelineManifest as { properties: JsonObject; required: string[] };
    delete manifest.properties.is_segment_line;
    manifest.required = manifest.required.filter((key) => key !== "is_segment_line");
    expect(moved).toEqual(legacy.$defs);
    const timeline = documents.timeline as JsonObject;
    expect([legacy.title, timeline.title]).toEqual([
      "TimeSkeleton manifest",
      "TimeSkeleton timeline file",
    ]);
    const legacyProperties = legacy.properties as JsonObject;
    expect(timeline.properties).toEqual({
      meta: { $ref: "core.schema.json#/$defs/Meta" },
      timeline: legacyProperties.timeline,
      graphical: legacyProperties.graphical,
    });
    const meta = structuredClone(legacyProperties.meta) as {
      description: string;
      properties: { schema_version: JsonObject; generator: JsonObject };
    };
    meta.description = "File metadata.";
    meta.properties.schema_version.const = "0.7.0";
    meta.properties.schema_version.description = "The timeskeleton release this file conforms to.";
    meta.properties.generator.description =
      "Free-form identification of the software that wrote the file.";
    expect(definitionsOf("core").Meta).toEqual(meta);
  });

  it("name the id rule in thirty-two references", () => {
    expect(
      Object.fromEntries(
        NAMES.map((name) => [name, references(documents[name]).filter((ref) => ref === ID).length]),
      ),
    ).toEqual({ core: 0, timeline: 27, group: 3, bundle: 2 });
  });

  it("state the group file literally", () => {
    const group = documents.group as {
      title: string;
      properties: JsonObject;
      required: string[];
      additionalProperties: boolean;
      $defs: Record<string, JsonObject & { properties: JsonObject }>;
    };
    expect(group.title).toBe("TimeSkeleton group file");
    expect(Object.keys(group.properties)).toEqual(["meta", "timelines", "group", "graphical"]);
    expect(group.required).toEqual(["meta", "timelines", "group"]);
    expect(group.additionalProperties).toBe(false);
    expect((group.properties.timelines as JsonObject).items).toEqual({
      $ref: "timeline.schema.json#/$defs/TimelineManifest",
    });
    const definition = group.$defs.Group as JsonObject & { properties: JsonObject };
    expect(Object.keys(definition.properties)).toEqual(["id", "name", "meta", "members"]);
    expect(definition.required).toEqual(["id", "name", "meta", "members"]);
    expect(definition.additionalProperties).toBe(false);
    const members = definition.properties.members as JsonObject;
    expect([members.type, members.items, members.uniqueItems]).toEqual([
      "array",
      { $ref: ID },
      true,
    ]);
    const order = group.$defs.MemberOrder as JsonObject;
    expect([order.type, order.items, order.uniqueItems]).toEqual(["array", { $ref: ID }, true]);
    const graphical = group.$defs.GroupGraphical as JsonObject & { properties: JsonObject };
    expect(Object.keys(graphical.properties)).toEqual(["order"]);
    expect(graphical.additionalProperties).toBe(false);
  });

  it("state the bundle file literally", () => {
    const bundle = documents.bundle as {
      title: string;
      properties: JsonObject;
      required: string[];
      $defs: Record<string, JsonObject & { properties: Record<string, JsonObject> }>;
    };
    expect(bundle.title).toBe("TimeSkeleton bundle file");
    expect(Object.keys(bundle.properties)).toEqual(["meta", "timelines", "bundle", "graphical"]);
    expect(bundle.required).toEqual(["meta", "timelines", "bundle"]);
    const definition = bundle.$defs.Bundle as JsonObject & {
      properties: Record<string, JsonObject>;
    };
    const keys = ["id", "name", "meta", "support_policy", "groups"];
    expect(Object.keys(definition.properties)).toEqual(keys);
    expect(definition.required).toEqual(keys);
    expect(definition.properties.support_policy?.enum).toEqual(["omit", "clamp", "extrapolate"]);
    expect(definition.properties.groups?.items).toEqual({ $ref: "group.schema.json#/$defs/Group" });
    const order = bundle.$defs.BundleGraphical?.properties.order as JsonObject;
    expect(order.propertyNames).toEqual({ $ref: ID });
    expect(order.additionalProperties).toEqual({ $ref: "group.schema.json#/$defs/MemberOrder" });
  });
});

describe("file kinds", () => {
  it.each([
    [["timeline"], "timeline"],
    [["timelines", "group"], "group"],
    [["timelines", "bundle"], "bundle"],
    [["timelines"], null],
    [["timeline", "group"], null],
    [["group", "bundle"], null],
  ])("tells the kind of a value holding %j", (members, kind) => {
    expect(FILE_KINDS).toEqual(["timeline", "group", "bundle"]);
    const value: JsonObject = { meta: {} };
    for (const member of members) value[member] = {};
    expect(fileKind(value)).toBe(kind);
  });

  it.each([[[]], ["group"], [null], [5]])("finds no kind in %j", (value) => {
    expect(fileKind(value)).toBeNull();
  });

  it("validates the test documents, also as parse reads them", () => {
    validate(groupDocument());
    validate(bundleDocument());
    expect(parse(dumps(groupDocument()))).toEqual(groupDocument());
    expect(parse(dumps(bundleDocument()))).toEqual(bundleDocument());
  });

  it.each([
    [[], "none"],
    [["timeline", "group"], '"timeline", "group"'],
  ])("requires exactly one kind in a 0.7.0 value holding %j", (members, found) => {
    const value: JsonObject = { meta: { schema_version: "0.7.0" } };
    for (const member of members) value[member] = member === "group" ? groupDocument().group : {};
    const error = rejection(value);
    expect(error.path).toEqual([]);
    expect(error.detail).toBe(
      `exactly one of "timeline", "group" or "bundle" is required; found ${found}`,
    );
  });

  it("rejects an unknown version at its declaration", () => {
    const value = groupDocument();
    (value.meta as JsonObject).schema_version = "9.9.9";
    expect(rejection(value).path).toEqual(["meta", "schema_version"]);
    expect(rejection({ meta: { schema_version: "9.9.9" } }).path).toEqual([
      "meta",
      "schema_version",
    ]);
  });

  it("knows timeline files only in 0.6.0", () => {
    const value = groupDocument();
    (value.meta as JsonObject).schema_version = "0.6.0";
    delete value.graphical;
    const error = rejection(value);
    expect(error.path).toEqual([]);
    expect(error.detail.startsWith("exactly one of")).toBe(false);
  });

  it("checks a bundle against the bundle document", () => {
    const value = groupDocument();
    value.bundle = bundleDocument().bundle;
    delete value.group;
    delete value.graphical;
    const error = rejection(value);
    expect(error.path).toEqual(["bundle", "groups", 0, "members", 0]);
    expect(error.detail).toBe('"performance" names no timeline of this file');
  });
});
