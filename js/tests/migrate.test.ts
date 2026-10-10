import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  MIGRATIONS,
  MigrationError,
  migrate,
  SCHEMA_VERSION,
  SUPPORTED_VERSIONS,
  validate,
} from "../src/index.js";
import { fixtureFileNames, loadFixture, migrationFixture, repositoryRoot } from "./fixtures.js";

type JsonObject = Record<string, unknown>;

function firstTimeline(document: JsonObject): [string, JsonObject] {
  const timelines = (document.manifest as JsonObject).timelines as JsonObject;
  const [entry] = Object.entries(timelines);
  return entry as [string, JsonObject];
}

function measure(document: JsonObject, index: number): JsonObject {
  const [, timeline] = firstTimeline(document);
  return ((timeline.measure_map as JsonObject).measures as JsonObject[])[index] as JsonObject;
}

function refusal(document: JsonObject): MigrationError {
  try {
    migrate(document);
  } catch (error) {
    if (error instanceof MigrationError) return error;
    throw error;
  }
  throw new Error("document was migrated");
}

describe("migrate", () => {
  it("registers the 0.1.0 to 0.2.0 migration", () => {
    expect(MIGRATIONS["0.1.0"]?.[0]).toBe("0.2.0");
  });

  it("reproduces the shared after fixture byte for byte", () => {
    const after = readFileSync(
      resolve(repositoryRoot, "fixtures", "migrations", "0.1.0-to-0.2.0", "after.json"),
      "utf8",
    );
    const result = migrate(migrationFixture("before"));
    expect(`${JSON.stringify(result, null, 2)}\n`).toBe(after);
    validate(result);
  });

  it("carries rows and the derived map id", () => {
    const [, timeline] = firstTimeline(
      migrate(migrationFixture("before")) as unknown as JsonObject,
    );
    const rows = timeline.measure_map as JsonObject[];
    expect(rows.map((row) => row.count)).toEqual([1, 2, 3, 4]);
    expect(rows[0]?.offset_within_measure).toEqual([3, 1]);
    expect(rows[2]?.next).toEqual(["2", "4"]);
    const positionMap = (timeline.conversion_maps as JsonObject[])[0] as JsonObject;
    expect(Object.keys(positionMap)).toEqual([
      "type",
      "id",
      "name",
      "source_unit",
      "target_unit",
      "meter_map",
      "beat_map_id",
    ]);
    expect(positionMap.beat_map_id).toBe("map:BeatInMeasureMap_1");
  });

  it.each([
    [1, "class", "SplitRegularMeasure"],
    [2, "next", ["m2", "m9"]],
    [2, "next", [["m2"]]],
    [0, "count", true],
  ] as const)("refuses measure %i with an unknown %s at its path", (index, key, value) => {
    const document = migrationFixture("before");
    measure(document, index)[key] = value;
    const [id] = firstTimeline(document);
    expect(refusal(document).path).toEqual([
      "manifest",
      "timelines",
      id,
      "measure_map",
      "measures",
      index,
      key,
    ]);
  });

  it("reads an integral JSON number in a pair as an integer", () => {
    const document = migrationFixture("before");
    expect(measure(document, 1).qstamp).toEqual([1, 1]);
    measure(document, 1).qstamp = JSON.parse("[1.0, 1]");
    const after = readFileSync(
      resolve(repositoryRoot, "fixtures", "migrations", "0.1.0-to-0.2.0", "after.json"),
      "utf8",
    );
    expect(`${JSON.stringify(migrate(document), null, 2)}\n`).toBe(after);
  });

  it("refuses a metrical position map whose maps are not derived", () => {
    const document = migrationFixture("before");
    const [id, timeline] = firstTimeline(document);
    const positionMap = (timeline.conversion_maps as JsonObject[])[0] as JsonObject;
    ((positionMap.maps as JsonObject).beat as JsonObject).name = "renamed";
    expect(refusal(document).path).toEqual([
      "manifest",
      "timelines",
      id,
      "conversion_maps",
      0,
      "maps",
    ]);
  });

  it("refuses an unknown conversion map type through the schema", () => {
    const document = migrationFixture("before");
    const [id, timeline] = firstTimeline(document);
    ((timeline.conversion_maps as JsonObject[])[1] as JsonObject).type = "UnknownMap";
    expect(refusal(document).path).toEqual(["manifest", "timelines", id, "conversion_maps", 1]);
  });

  it.each(SUPPORTED_VERSIONS)("brings every %s fixture to a valid latest document", (version) => {
    for (const file of fixtureFileNames(version)) {
      const result = migrate(loadFixture(file.slice(0, -5), version));
      expect(result.meta.schema_version).toBe(SCHEMA_VERSION);
      validate(result);
    }
  });
});
