import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { generate, generatedDirectory } from "../scripts/generate.js";

describe("generated files", () => {
  it("equal a fresh run of the generator", async () => {
    const fresh = await generate();
    expect(Object.keys(fresh).sort()).toEqual(["schema.ts", "types.ts"]);
    for (const [name, content] of Object.entries(fresh)) {
      const committed = readFileSync(resolve(generatedDirectory, name), "utf8");
      expect(committed).toBe(content);
    }
  });
});
