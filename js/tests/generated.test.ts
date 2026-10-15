import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { generate, generatedDirectory, schemaSource } from "../scripts/generate.js";

describe("generated files", () => {
  it("equal a fresh run of the generator", async () => {
    const fresh = await generate();
    expect(Object.keys(fresh).sort()).toEqual(["font.ts", "schema.ts", "types.ts"]);
    for (const [name, content] of Object.entries(fresh)) {
      const committed = readFileSync(resolve(generatedDirectory, name), "utf8");
      expect(committed).toBe(content);
    }
  });

  it("come from the one schema document", () => {
    expect(schemaSource()).toBe("0.7.0/timeskeleton.schema.json");
  });

  it("export the public definitions and none of the former ones", () => {
    const types = readFileSync(resolve(generatedDirectory, "types.ts"), "utf8");
    const exported = (name: string) =>
      new RegExp(`^export (?:interface|type) ${name}\\b`, "m").test(types);
    for (const name of [
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
    ]) {
      expect(exported(name), name).toBe(true);
    }
    for (const name of [
      "TimeSkeletonManifest",
      "TimeSkeletonGroupFile",
      "TimeSkeletonBundleFile",
      "Bundle",
      "Meta",
      "TimelineClass",
    ]) {
      expect(exported(name), name).toBe(false);
    }
  });
});
