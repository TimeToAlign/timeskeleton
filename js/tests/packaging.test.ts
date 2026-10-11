import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { repositoryRoot } from "./fixtures.js";

const packageDirectory = resolve(repositoryRoot, "js");

describe("the npm package", () => {
  it("ships the drawing specification", () => {
    execFileSync(process.execPath, ["scripts/copy-assets.ts"], { cwd: packageDirectory });
    const [report] = JSON.parse(
      execFileSync("npm", ["pack", "--dry-run", "--json", "--ignore-scripts"], {
        cwd: packageDirectory,
        encoding: "utf8",
      }),
    ) as [{ files: { path: string }[] }];
    expect(report.files.map((file) => file.path)).toContain("docs/drawing.md");
    expect(readFileSync(resolve(packageDirectory, "docs", "drawing.md"))).toEqual(
      readFileSync(resolve(repositoryRoot, "docs", "drawing.md")),
    );
    const manifest = JSON.parse(readFileSync(resolve(packageDirectory, "package.json"), "utf8"));
    expect(manifest.exports["./docs/*"]).toBe("./docs/*");
  });
});
