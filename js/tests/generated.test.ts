import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { generate, generatedDirectory, orderSchemaFiles } from "../scripts/generate.js";

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
});
