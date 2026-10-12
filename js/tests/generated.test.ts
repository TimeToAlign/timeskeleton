import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  generate,
  generatedDirectory,
  orderSchemaFiles,
  schemaVersions,
} from "../scripts/generate.js";

describe("generated files", () => {
  it("equal a fresh run of the generator", async () => {
    const fresh = await generate();
    expect(Object.keys(fresh).sort()).toEqual(["font.ts", "schema.ts", "types.ts"]);
    for (const [name, content] of Object.entries(fresh)) {
      const committed = readFileSync(resolve(generatedDirectory, name), "utf8");
      expect(committed).toBe(content);
    }
  });

  it("order schema files by parsed version, not by text", () => {
    expect(
      orderSchemaFiles([
        "timeskeleton-0.10.0.schema.json",
        "README.md",
        "timeskeleton-0.9.0.schema.json",
        "timeskeleton-1.0.0.schema.json",
      ]),
    ).toEqual([
      "timeskeleton-0.9.0.schema.json",
      "timeskeleton-0.10.0.schema.json",
      "timeskeleton-1.0.0.schema.json",
    ]);
  });

  it("order version directories among the schema files", () => {
    expect(
      orderSchemaFiles(["0.10.0", "timeskeleton-0.6.0.schema.json", "0.7.0", "0.7", "README.md"]),
    ).toEqual(["timeskeleton-0.6.0.schema.json", "0.7.0", "0.10.0"]);
  });

  it("find every schema version at the repository root", () => {
    expect(schemaVersions()).toEqual([
      { version: "0.5.0", documents: { timeline: "timeskeleton-0.5.0.schema.json" } },
      { version: "0.6.0", documents: { timeline: "timeskeleton-0.6.0.schema.json" } },
      {
        version: "0.7.0",
        documents: {
          core: "0.7.0/core.schema.json",
          timeline: "0.7.0/timeline.schema.json",
          group: "0.7.0/group.schema.json",
          bundle: "0.7.0/bundle.schema.json",
        },
      },
    ]);
  });

  it("name the root type of every file kind", async () => {
    const types = readFileSync(resolve(generatedDirectory, "types.ts"), "utf8");
    for (const name of [
      "TimeSkeletonManifest",
      "TimeSkeletonGroupFile",
      "TimeSkeletonBundleFile",
      "Group",
      "Bundle",
      "Meta",
      "MemberOrder",
    ]) {
      expect(types).toMatch(new RegExp(`^export (?:interface|type) ${name}\\b`, "m"));
    }
  });
});
