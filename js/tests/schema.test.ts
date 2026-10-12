import { describe, expect, it } from "vitest";
import {
  SCHEMA_VERSION,
  SUPPORTED_VERSIONS,
  schema,
  schemaDocuments,
  schemas,
} from "../src/index.js";
import { fixtureFileNames, loadFixture, loadSchemaFile } from "./fixtures.js";

const SCHEMA_ID = "https://timetoalign.github.io/timeskeleton/0.6.0/timeskeleton.schema.json";

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
const ID_PATTERN = "^[^/\\u0000-\\u001f]+$";

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

/** The 0.6.0 schema, whose definitions the 0.7.0 timeline and core documents hold. */
const legacy = schemas["0.6.0"];

describe("schema identity", () => {
  it("publishes the latest supported version", () => {
    expect(SCHEMA_VERSION).toBe("0.7.0");
    expect(SUPPORTED_VERSIONS).toEqual(["0.5.0", "0.6.0", "0.7.0"]);
    expect(SUPPORTED_VERSIONS.at(-1)).toBe(SCHEMA_VERSION);
  });

  it("bundles the schema files at the repository root", () => {
    expect(schema).toEqual(loadSchemaFile("0.7.0", "timeline"));
    expect(schemas).toEqual({
      "0.5.0": loadSchemaFile("0.5.0"),
      "0.6.0": loadSchemaFile("0.6.0"),
      "0.7.0": loadSchemaFile("0.7.0", "timeline"),
    });
    expect(schemaDocuments).toEqual({
      "0.5.0": { timeline: loadSchemaFile("0.5.0") },
      "0.6.0": { timeline: loadSchemaFile("0.6.0") },
      "0.7.0": {
        core: loadSchemaFile("0.7.0", "core"),
        timeline: loadSchemaFile("0.7.0", "timeline"),
        group: loadSchemaFile("0.7.0", "group"),
        bundle: loadSchemaFile("0.7.0", "bundle"),
      },
    });
  });

  it.each(["0.5.0", "0.6.0"])("declares %s in its schema", (version) => {
    const versionSchema = loadSchemaFile(version) as {
      $id: string;
      properties: { meta: { properties: { schema_version: { const: string } } } };
    };
    expect(versionSchema.$id).toContain(`/${version}/`);
    expect(versionSchema.properties.meta.properties.schema_version.const).toBe(version);
  });

  it("keeps the manifest format of 0.5.0", () => {
    const withoutVersion = (version: string) => {
      const versionSchema = loadSchemaFile(version) as {
        $id?: string;
        description?: string;
        properties: { meta: { properties: { schema_version: { const?: string } } } };
      };
      delete versionSchema.$id;
      delete versionSchema.description;
      delete versionSchema.properties.meta.properties.schema_version.const;
      return versionSchema;
    };
    expect(withoutVersion("0.5.0")).toEqual(withoutVersion("0.6.0"));
  });

  it("carries the pinned $id, $schema and version constant", () => {
    expect(legacy.$id).toBe(SCHEMA_ID);
    expect(legacy.$schema).toBe("https://json-schema.org/draft/2020-12/schema");
    expect(legacy.properties.meta.properties.schema_version).toEqual({
      const: "0.6.0",
      description: "The timeskeleton release this manifest conforms to.",
    });
  });

  it("holds one timeline", () => {
    const current = loadSchemaFile("0.6.0") as {
      properties: Record<string, unknown>;
      required: string[];
      additionalProperties: boolean;
    };
    expect(Object.keys(current.properties)).toEqual(["meta", "timeline", "graphical"]);
    expect(current.properties.timeline).toEqual({ $ref: "#/$defs/TimelineManifest" });
    expect(current.properties.graphical).toEqual({ $ref: "#/$defs/Graphical" });
    expect(current.required).toEqual(["meta", "timeline"]);
    expect(current.additionalProperties).toBe(false);
  });
});

const CONVERSION_MAP_TYPES = [
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

describe("the graphical block", () => {
  const defs = legacy.$defs as unknown as Record<string, Record<string, unknown>>;

  it("holds named styles and ordered statements", () => {
    const graphical = defs.Graphical as {
      properties: Record<string, Record<string, unknown>>;
      additionalProperties: boolean;
    };
    expect(Object.keys(graphical.properties)).toEqual(["styles", "statements"]);
    expect(graphical.properties.styles?.additionalProperties).toEqual({
      $ref: "#/$defs/Declaration",
    });
    expect(graphical.properties.statements?.items).toEqual({ $ref: "#/$defs/Statement" });
    expect(graphical.additionalProperties).toBe(false);
    const statement = defs.Statement as {
      required: string[];
      properties: { set: { oneOf: Record<string, unknown>[] } };
    };
    expect(statement.required).toEqual(["select", "set"]);
    expect(statement.properties.set.oneOf.map(({ description: _, ...branch }) => branch)).toEqual([
      { $ref: "#/$defs/Declaration" },
      { type: "string" },
    ]);
  });

  it("selects by the six selector members", () => {
    const selector = defs.Selector as {
      properties: Record<string, Record<string, unknown>>;
      additionalProperties: boolean;
    };
    expect(Object.keys(selector.properties)).toEqual([
      "element",
      "ids",
      "domain",
      "modality",
      "class",
      "within",
    ]);
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
    ]);
    expect(selector.properties.ids?.minItems).toBe(1);
    expect(selector.properties.ids?.uniqueItems).toBe(true);
    expect(selector.properties.domain?.enum).toEqual(["graphical", "logical", "physical"]);
    expect(selector.properties.modality?.enum).toEqual(["continuous", "discrete"]);
    expect(selector.properties.class?.enum).toEqual([...TIMELINE_CLASSES, ...CONVERSION_MAP_TYPES]);
    expect(selector.properties.within?.type).toBe("string");
    expect(selector.additionalProperties).toBe(false);
  });

  it("sets the eleven presentation properties", () => {
    const declaration = defs.Declaration as {
      properties: Record<string, Record<string, unknown>>;
      additionalProperties: boolean;
    };
    const { description: _, ...dasharray } = declaration.properties["stroke-dasharray"] ?? {};
    expect({ ...declaration.properties, "stroke-dasharray": dasharray }).toEqual({
      stroke: { $ref: "#/$defs/Paint" },
      "stroke-width": { type: "number", minimum: 0 },
      "stroke-dasharray": {
        type: "string",
        pattern: "^(none|(0|[1-9][0-9]*)(\\.[0-9]+)?( (0|[1-9][0-9]*)(\\.[0-9]+)?)*)$",
      },
      fill: { $ref: "#/$defs/Paint" },
      opacity: { type: "number", minimum: 0, maximum: 1 },
      "font-size": { type: "number", exclusiveMinimum: 0 },
      rx: { type: "number", minimum: 0 },
      display: { type: "string", enum: ["inline", "none"] },
      side: { type: "string", enum: ["above", "below"] },
      content: { type: "string" },
      "max-width": {
        oneOf: [{ type: "number", exclusiveMinimum: 0 }, { const: "none" }],
      },
    });
    expect(defs.Paint?.pattern).toBe("^(#[0-9A-F]{6}|none)$");
    expect(declaration.additionalProperties).toBe(false);
  });
});

describe("schema vocabulary", () => {
  it("enumerates the library's classes, units and number types", () => {
    expect(legacy.$defs.TimelineClass.enum).toEqual(TIMELINE_CLASSES);
    expect(legacy.$defs.TimeUnit.enum).toEqual(TIME_UNITS);
    expect(legacy.$defs.NumberType.enum).toEqual(NUMBER_TYPES);
  });

  it("closes the timeline manifest over fourteen keys", () => {
    const manifest = legacy.$defs.TimelineManifest;
    expect(manifest.required).toEqual(MANIFEST_KEYS);
    expect(Object.keys(manifest.properties)).toEqual(MANIFEST_KEYS);
    expect(manifest.additionalProperties).toBe(false);
    expect(manifest.properties.metric_hierarchy.description).toBe(
      "The metric hierarchy, or null; an object without further constraints.",
    );
  });

  it("excludes empty ids, slashes and control characters from ids and child keys", () => {
    const definitions = Object.values(legacy.$defs) as Array<{
      properties?: Record<string, Record<string, unknown>>;
    }>;
    const definitionsWithId = definitions.filter((definition) => definition.properties?.id);
    expect(definitionsWithId).toHaveLength(26);
    for (const definition of definitionsWithId) {
      expect(definition.properties?.id?.pattern).toBe(ID_PATTERN);
    }
    expect(legacy.$defs.TimelineManifest.properties.children.propertyNames).toEqual({
      pattern: ID_PATTERN,
    });
  });

  it("gives regions, breaks, jumps and markers an id", () => {
    const defs = legacy.$defs;
    expect(defs.Region.required).toEqual(["id", "name", "start", "end", "meta"]);
    expect(defs.Region.properties.name.type).toEqual(["string", "null"]);
    expect(defs.Break.required).toEqual([
      "id",
      "coordinate",
      "control_type",
      "condition",
      "repeat_count",
      "label",
      "name",
      "meta",
    ]);
    expect(defs.Jump.required).toEqual([
      "id",
      "from_coordinate",
      "to_coordinate",
      "control_type",
      "condition",
      "repeat_count",
      "target",
      "label",
      "meta",
    ]);
    expect(defs.Jump.properties.target.type).toEqual(["string", "null"]);
    expect(defs.Marker.required).toEqual(["id", "name", "coordinate"]);
    expect(Object.keys(defs.Marker.properties)).toEqual(["id", "name", "coordinate"]);
    expect(defs.Marker.properties.name.type).toEqual(["string", "null"]);
    expect(defs.Marker.properties.coordinate).toEqual({ $ref: "#/$defs/Coordinate" });
    expect(defs.FlowControl.properties.markers).toEqual({
      type: "array",
      items: { $ref: "#/$defs/Marker" },
    });
    for (const name of ["Region", "Break", "Jump", "Marker"] as const) {
      expect(defs[name].additionalProperties).toBe(false);
    }
  });

  it("defines a nonempty compressed measure-map row list", () => {
    const measureMap = legacy.$defs.MeasureMap;
    const row = legacy.$defs.MeasureMapRow;
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
    const manifest = legacy.$defs.TimelineManifest;
    expect(manifest.if).toEqual({
      properties: { unit: { const: "quarters" } },
      required: ["unit"],
    });
    expect(manifest.else).toEqual({ properties: { measure_map: { type: "null" } } });
  });

  it("states the metrical position map's meter map once", () => {
    const positionMap = legacy.$defs.MetricalPositionMap;
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
  it.each(["0.6.0", "0.7.0"])("contains exactly the 23 single manifests (%s)", (version) => {
    expect(fixtureFileNames(version)).toEqual([
      "bare.json",
      "contiguous.json",
      "continuous_graphical.json",
      "continuous_logical.json",
      "continuous_physical.json",
      "conversion_maps__maps_quarters.json",
      "conversion_maps__maps_samples.json",
      "conversion_maps__maps_seconds.json",
      "conversion_maps__maps_ticks.json",
      "corpus_audio_audio.json",
      "corpus_midi_score_midi.json",
      "corpus_parangonar_parangonada__score_dlt_1.json",
      "corpus_score_ms3.json",
      "corpus_supra_iiif.json",
      "discrete_graphical.json",
      "discrete_logical.json",
      "discrete_physical.json",
      "flow_control.json",
      "map.json",
      "nested.json",
      "styled__performance.json",
      "styled__score.json",
      "with_region.json",
    ]);
  });

  it("contains exactly the group and bundle files of 0.7.0", () => {
    expect(fixtureFileNames("0.7.0", "group")).toEqual([
      "corpus_tilia.json",
      "group_child_member.json",
      "group_number_types.json",
    ]);
    expect(fixtureFileNames("0.7.0", "bundle")).toEqual([
      "bundle_mixed.json",
      "corpus_ieee1599.json",
      "corpus_listen_here.json",
      "corpus_matchfile.json",
      "corpus_mpm.json",
      "corpus_parangonada.json",
      "corpus_tilia.json",
    ]);
    expect(fixtureFileNames("0.6.0", "group")).toEqual([]);
    expect(fixtureFileNames("0.6.0", "bundle")).toEqual([]);
  });

  it("pins the styled blocks", () => {
    const score = loadFixture("styled__score").graphical;
    const performance = loadFixture("styled__performance").graphical;
    expect(score).toEqual({
      styles: {
        accent: { stroke: "#1D4ED8", fill: "#1D4ED8", "stroke-width": 4, opacity: 0.8 },
      },
      statements: [
        { select: { element: "label" }, set: { stroke: "#404040", fill: "#404040" } },
        { select: { element: "name" }, set: { stroke: "#404040", fill: "#404040" } },
        { select: { element: "map" }, set: { side: "below" } },
        { select: { ids: ["a"] }, set: { display: "none" } },
        { select: { element: "block" }, set: { rx: 4 } },
        { select: { class: "ContinuousLogicalTimeline", element: "timeline" }, set: "accent" },
        { select: { class: "QuartersToTicks" }, set: { stroke: "#7C3AED", "stroke-width": 1.5 } },
        { select: { element: "map", modality: "discrete" }, set: { "stroke-dasharray": "4 2" } },
        { select: { element: "region" }, set: { stroke: "#800000" } },
        { select: { element: "region" }, set: { stroke: "#0F766E" } },
        {
          select: { element: "jump", domain: "logical" },
          set: { stroke: "#DB2777", fill: "#DB2777", "stroke-width": 2 },
        },
        {
          select: { element: "wedge", within: "score" },
          set: { side: "above", stroke: "#65A30D", fill: "#65A30D" },
        },
        { select: { ids: ["score/end"] }, set: { stroke: "#B45309", fill: "#B45309" } },
        { select: { element: "child", within: "score" }, set: { display: "inline" } },
        {
          select: { element: "child", within: "b" },
          set: { stroke: "#EA580C", fill: "#EA580C" },
        },
        {
          select: { element: "label", within: "score" },
          set: { fill: "#4D7C0F", "font-size": 10 },
        },
        { select: { ids: ["score/end/label"] }, set: { fill: "#A16207" } },
        { select: { ids: ["intro/label"] }, set: { fill: "#0E7490" } },
        { select: { ids: ["da-capo/label"] }, set: { fill: "#9D174D" } },
        {
          select: { ids: ["score/name"] },
          set: { fill: "#111827", "font-size": 12, content: "Styled score", "max-width": 120 },
        },
        { select: { element: "name", within: "b" }, set: { fill: "#0369A1" } },
      ],
    });
    expect(performance).toEqual({
      statements: [
        { select: { element: "label" }, set: { stroke: "#404040", fill: "#404040" } },
        { select: { element: "name" }, set: { stroke: "#404040", fill: "#404040" } },
        { select: { element: "map" }, set: { side: "below" } },
        { select: { ids: ["a"] }, set: { display: "none" } },
        {
          select: { element: "wedge", domain: "physical", within: "performance" },
          set: { stroke: "#7F00FF", fill: "#7F00FF" },
        },
      ],
    });
  });
});
