import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { beforeAll, describe, expect, it } from "vitest";
import { repositoryRoot } from "./fixtures.js";

const packageDirectory = resolve(repositoryRoot, "js");

/** The files `npm pack` would ship, after refreshing the copied assets once. */
let shipped: string[] = [];

describe("the npm package", () => {
  beforeAll(() => {
    execFileSync(process.execPath, ["scripts/copy-assets.ts"], { cwd: packageDirectory });
    const [report] = JSON.parse(
      execFileSync("npm", ["pack", "--dry-run", "--json", "--ignore-scripts"], {
        cwd: packageDirectory,
        encoding: "utf8",
      }),
    ) as [{ files: { path: string }[] }];
    shipped = report.files.map((file) => file.path);
  }, 120_000);

  it("ships the drawing specification", () => {
    expect(shipped).toContain("docs/drawing.md");
    expect(readFileSync(resolve(packageDirectory, "docs", "drawing.md"))).toEqual(
      readFileSync(resolve(repositoryRoot, "docs", "drawing.md")),
    );
    const manifest = JSON.parse(readFileSync(resolve(packageDirectory, "package.json"), "utf8"));
    expect(manifest.exports["./docs/*"]).toBe("./docs/*");
  });

  it("ships the schema document", () => {
    const path = "schema/0.7.0/timeskeleton.schema.json";
    expect(shipped).toContain(path);
    expect(shipped.filter((file) => file.startsWith("schema/"))).toEqual([path]);
    expect(readFileSync(resolve(packageDirectory, path))).toEqual(
      readFileSync(resolve(repositoryRoot, path)),
    );
  });

  it("ships the repository's licence", () => {
    expect(shipped).toContain("LICENSE");
    expect(readFileSync(resolve(packageDirectory, "LICENSE"))).toEqual(
      readFileSync(resolve(repositoryRoot, "LICENSE")),
    );
  });
});
