import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { generate, generatedDirectory, schemaSource } from "../scripts/generate.js";
import { schema } from "../src/generated/schema.js";

type Node = Record<string, unknown>;

/** The names a generated module exports, sorted. */
function exportsOf(text: string): string[] {
  return [...text.matchAll(/^export (?:interface|type|const) (\w+)/gm)]
    .map((match) => match[1] as string)
    .sort();
}

const committed = (name: string) => readFileSync(resolve(generatedDirectory, name), "utf8");
const defs = (schema as Node).$defs as Record<string, Node>;
const mapTypes = ((defs.ConversionMap as Node).oneOf as Node[]).map((branch) =>
  (branch.$ref as string).slice("#/$defs/".length),
);

describe("generated files", () => {
  it("export what a fresh run of the generator exports", async () => {
    const fresh = await generate();
    expect(Object.keys(fresh).sort()).toEqual(["font.ts", "schema.ts", "types.ts"]);
    for (const [name, content] of Object.entries(fresh)) {
      expect(exportsOf(committed(name)), name).toEqual(exportsOf(content));
    }
  });

  it("come from the one schema document", () => {
    expect(schemaSource()).toBe("0.7.0/timeskeleton.schema.json");
  });

  it("export every definition, its complete form where it has defaults, and no former name", () => {
    const definitions = Object.keys(defs);
    const completed = [
      "TimeSkeleton",
      "Timeline",
      "Group",
      "Graphical",
      "ConversionMap",
      "MapBase",
      "MeasureView",
      ...mapTypes,
      "Region",
      "FlowControlElement",
      "MeasureMap",
    ];
    expect(exportsOf(committed("types.ts"))).toEqual(
      [
        ...definitions,
        ...completed.map((name) => `Complete${name}`),
        "LosslessTimeSkeleton",
      ].sort(),
    );
    for (const name of [
      "TimeSkeletonManifest",
      "TimeSkeletonGroupFile",
      "TimeSkeletonBundleFile",
      "Bundle",
      "TimelineClass",
    ]) {
      expect(definitions).not.toContain(name);
    }
  });
});
