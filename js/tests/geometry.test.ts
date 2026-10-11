import { readdirSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  dumps,
  GEOMETRY_VERSIONS,
  geometrySchema,
  geometrySchemas,
  parseJson,
  SchemaValidationError,
  validateGeometry,
} from "../src/index.js";
import { repositoryRoot } from "./fixtures.js";

type JsonObject = Record<string, unknown>;

const directory = resolve(repositoryRoot, "fixtures", "0.3.0");
const specimens = readdirSync(resolve(directory, "geometry"), { withFileTypes: true })
  .filter((entry) => entry.isDirectory())
  .map((entry) => entry.name)
  .sort();
const geometryText = (name: string) =>
  readFileSync(resolve(directory, "geometry", name, "geometry.json"), "utf8");
const rejections = readdirSync(resolve(directory, "geometry-rejections")).sort();

describe("the geometry schema", () => {
  it("is bundled for 0.3.0", () => {
    const file = JSON.parse(
      readFileSync(resolve(repositoryRoot, "schema", "geometry-0.3.0.schema.json"), "utf8"),
    ) as unknown;
    expect(GEOMETRY_VERSIONS).toEqual(["0.3.0"]);
    expect(geometrySchemas).toEqual({ "0.3.0": file });
    expect(geometrySchema).toEqual(file);
  });
});

describe("validateGeometry", () => {
  it("has one geometry fixture per envelope fixture", () => {
    const envelopes = readdirSync(directory)
      .filter((name) => name.endsWith(".json"))
      .map((name) => name.slice(0, -5))
      .sort();
    expect(specimens).toEqual(envelopes);
    expect(specimens).toHaveLength(20);
  });

  it.each(specimens)("accepts the geometry fixture of %s in standard text", (name) => {
    const text = geometryText(name);
    const geometry = parseJson(text);
    validateGeometry(geometry);
    expect(dumps(geometry)).toBe(text);
  });

  it.each(rejections)("rejects %s at its stored path", (name) => {
    const testCase = parseJson(
      readFileSync(resolve(directory, "geometry-rejections", name), "utf8"),
    ) as JsonObject;
    let caught: unknown;
    try {
      validateGeometry(testCase.geometry);
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(SchemaValidationError);
    expect((caught as SchemaValidationError).path).toEqual(testCase.path);
  });

  it("accepts a primitive of an unknown kind", () => {
    const geometry = parseJson(geometryText("bare")) as JsonObject;
    const block = (geometry.blocks as JsonObject[])[0] as JsonObject;
    (block.primitives as JsonObject[]).push({ kind: "strip", values: [1, 2] });
    validateGeometry(geometry);
  });
});
