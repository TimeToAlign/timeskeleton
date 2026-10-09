import { describe, expect, it } from "vitest";
import { SCHEMA_VERSION, SUPPORTED_VERSIONS, schema } from "../src/index.js";
import { FIXTURE_NAMES, fixtureFileNames, loadSchemaFile } from "./fixtures.js";

const SCHEMA_ID = "https://timetoalign.github.io/timeskeleton/0.1.0/timeskeleton.schema.json";

const TIMELINE_CLASSES = [
  "ContinuousLogicalTimeline",
  "ContinuousPhysicalTimeline",
  "ContinuousGraphicalTimeline",
  "DiscreteLogicalTimeline",
  "DiscretePhysicalTimeline",
  "DiscreteGraphicalTimeline",
];

const TIME_UNITS = [
  "number",
  "floating_measures",
  "whole_note",
  "quarters",
  "ticks",
  "milliseconds",
  "seconds",
  "minutes",
  "samples",
  "frames",
  "pixels",
  "meters",
  "centimeters",
  "millimeters",
  "inches",
  "points",
];

const NUMBER_TYPES = ["int", "float", "fraction"];

const MANIFEST_KEYS = [
  "id",
  "name",
  "class",
  "unit",
  "number_type",
  "length",
  "locked",
  "meta",
  "children",
  "conversion_maps",
  "regions",
  "flow_control",
  "measure_map",
  "metric_hierarchy",
];

describe("schema identity", () => {
  it("publishes the latest supported version", () => {
    expect(SCHEMA_VERSION).toBe("0.1.0");
    expect(SUPPORTED_VERSIONS).toEqual(["0.1.0"]);
    expect(SUPPORTED_VERSIONS.at(-1)).toBe(SCHEMA_VERSION);
  });

  it("bundles the schema file at the repository root", () => {
    expect(schema).toEqual(loadSchemaFile());
  });

  it("carries the pinned $id, $schema and version constant", () => {
    expect(schema.$id).toBe(SCHEMA_ID);
    expect(schema.$schema).toBe("https://json-schema.org/draft/2020-12/schema");
    expect(schema.properties.meta.properties.schema_version).toEqual({
      const: SCHEMA_VERSION,
      description: "The timeskeleton release this document conforms to.",
    });
  });
});

describe("schema vocabulary", () => {
  it("enumerates the library's classes, units and number types", () => {
    expect(schema.$defs.TimelineClass.enum).toEqual(TIMELINE_CLASSES);
    expect(schema.$defs.TimeUnit.enum).toEqual(TIME_UNITS);
    expect(schema.$defs.NumberType.enum).toEqual(NUMBER_TYPES);
  });

  it("closes the timeline manifest over fourteen keys", () => {
    const manifest = schema.$defs.TimelineManifest;
    expect(manifest.required).toEqual(MANIFEST_KEYS);
    expect(Object.keys(manifest.properties)).toEqual(MANIFEST_KEYS);
    expect(manifest.additionalProperties).toBe(false);
  });
});

describe("fixture set", () => {
  it("is exactly the nine documents", () => {
    expect(fixtureFileNames()).toEqual(FIXTURE_NAMES.map((name) => `${name}.json`));
  });
});
