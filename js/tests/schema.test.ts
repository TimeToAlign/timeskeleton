import { describe, expect, it } from "vitest";
import { SCHEMA_VERSION, SUPPORTED_VERSIONS, schema, schemas } from "../src/index.js";
import { fixtureFileNames, loadSchemaFile } from "./fixtures.js";

const SCHEMA_ID = "https://timetoalign.github.io/timeskeleton/0.2.0/timeskeleton.schema.json";

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

const MEASURE_MAP_ROW_KEYS = [
  "ID",
  "count",
  "qstamp",
  "number",
  "name",
  "time_signature",
  "nominal_length",
  "actual_length",
  "start_repeat",
  "end_repeat",
  "next",
  "volta",
  "offset_within_measure",
];

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
    expect(SCHEMA_VERSION).toBe("0.2.0");
    expect(SUPPORTED_VERSIONS).toEqual(["0.1.0", "0.2.0"]);
    expect(SUPPORTED_VERSIONS.at(-1)).toBe(SCHEMA_VERSION);
  });

  it("bundles the schema file at the repository root", () => {
    expect(schema).toEqual(loadSchemaFile());
    expect(schemas).toEqual({ "0.1.0": loadSchemaFile("0.1.0"), "0.2.0": loadSchemaFile("0.2.0") });
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

  it("defines a nonempty compressed measure-map row list", () => {
    const measureMap = schema.$defs.MeasureMap;
    const row = schema.$defs.MeasureMapRow;
    expect(measureMap.type).toBe("array");
    expect(measureMap.items).toEqual({ $ref: "#/$defs/MeasureMapRow" });
    expect(measureMap.minItems).toBe(1);
    expect(Object.keys(row.properties)).toEqual(MEASURE_MAP_ROW_KEYS);
    expect(row.anyOf).toEqual([{ required: ["ID"] }, { required: ["count"] }]);
    expect(row.additionalProperties).toBe(false);
    expect(row.properties.actual_length.$ref).toBe("#/$defs/NumberPositive");
    expect(row.properties.offset_within_measure.$ref).toBe("#/$defs/NumberPositive");
    expect(row.properties.qstamp.$ref).toBe("#/$defs/NumberNonnegative");
    expect(row.properties.nominal_length.anyOf).toEqual([
      { $ref: "#/$defs/NumberPositive" },
      { type: "null" },
    ]);
  });

  it("admits a measure map on a quarters timeline only", () => {
    const manifest = schema.$defs.TimelineManifest;
    expect(manifest.if).toEqual({
      properties: { unit: { const: "quarters" } },
      required: ["unit"],
    });
    expect(manifest.else).toEqual({ properties: { measure_map: { type: "null" } } });
  });

  it("states the metrical position map's meter map once", () => {
    const positionMap = schema.$defs.MetricalPositionMap;
    expect(positionMap.required).toEqual([
      "type",
      "id",
      "name",
      "source_unit",
      "target_unit",
      "meter_map",
      "beat_map_id",
    ]);
    expect(positionMap.additionalProperties).toBe(false);
  });
});

describe("fixture set", () => {
  it("contains the synthetic, map, flow-control, and corpus documents", () => {
    expect(fixtureFileNames()).toHaveLength(16);
    expect(fixtureFileNames()).toContain("conversion_maps.json");
    expect(fixtureFileNames()).toContain("flow_control.json");
  });
});
