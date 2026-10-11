import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { dumps, fontMetrics, parseJson } from "../src/index.js";
import { repositoryRoot } from "./fixtures.js";

const RELEASE_SHA256 = "7da195a74c55bef988d0d48f9508bd5d849425c1770dba5d7bfc6ce9ed848954";

describe("the bundled font", () => {
  it("is the upstream 2.37 release file, with its licence", () => {
    const font = readFileSync(resolve(repositoryRoot, "fonts", "DejaVuSans.ttf"));
    expect(createHash("sha256").update(font).digest("hex")).toBe(RELEASE_SHA256);
    expect(readFileSync(resolve(repositoryRoot, "fonts", "LICENSE")).byteLength).toBe(8816);
  });

  it("is exported as a package subpath", () => {
    const manifest = parseJson(readFileSync(resolve(repositoryRoot, "js", "package.json"), "utf8"));
    const record = manifest as { exports: Record<string, string>; files: string[] };
    expect(record.exports["./fonts/*"]).toBe("./fonts/*");
    expect(record.files).toContain("fonts");
  });
});

describe("fontMetrics", () => {
  it("holds the stated values", () => {
    expect(Object.keys(fontMetrics)).toEqual([
      "advances",
      "ascender",
      "descender",
      "fallback",
      "units_per_em",
    ]);
    expect(fontMetrics.units_per_em).toBe(2048);
    expect(fontMetrics.ascender).toBe(1901);
    expect(fontMetrics.descender).toBe(483);
    expect(fontMetrics.fallback).toBe(1229);
    expect(Object.keys(fontMetrics.advances)).toHaveLength(5918);
    expect(fontMetrics.advances["9833"]).toBe(966);
    expect(fontMetrics.advances["48"]).toBe(1303);
    expect(fontMetrics.advances["32"]).toBe(651);
  });

  it("equals the metrics file, which the standard writer wrote", () => {
    const text = readFileSync(
      resolve(repositoryRoot, "fonts", "dejavu-sans-2.37.metrics.json"),
      "utf8",
    );
    expect(dumps(parseJson(text))).toBe(text);
    expect(dumps(fontMetrics)).toBe(text);
  });
});
