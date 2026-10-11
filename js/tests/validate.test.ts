import { describe, expect, it } from "vitest";
import {
  declaredVersion,
  jsonPointer,
  parse,
  parseJson,
  SchemaValidationError,
  SUPPORTED_VERSIONS,
  validate,
} from "../src/index.js";
import {
  fixtureFileNames,
  fixtureText,
  loadFixture,
  loadRejection,
  rejectionFileNames,
  rejectionText,
} from "./fixtures.js";

function rejection(value: unknown): SchemaValidationError {
  try {
    validate(value);
  } catch (error) {
    if (error instanceof SchemaValidationError) return error;
    throw error;
  }
  throw new Error("value was accepted");
}

describe("validate", () => {
  it.each(SUPPORTED_VERSIONS)("accepts every %s fixture", (version) => {
    for (const file of fixtureFileNames(version)) {
      expect(parse(fixtureText(file.slice(0, -5), version))).toBeDefined();
    }
  });

  it.each(SUPPORTED_VERSIONS)("accepts every %s fixture as JSON.parse reads it", (version) => {
    for (const file of fixtureFileNames(version)) {
      validate(JSON.parse(fixtureText(file.slice(0, -5), version)));
    }
  });

  it.each(rejectionFileNames())("rejects %s at its stored path", (name) => {
    const testCase = loadRejection(name);
    expect(rejection(testCase.manifest).path).toEqual(testCase.path);
    const plainCase = parseJson(rejectionText(name)) as Record<string, unknown>;
    expect(rejection(plainCase.manifest).path).toEqual(testCase.path);
  });

  it("has every 0.4.0 rejection declare 0.4.0 except the two without a declaration", () => {
    const exempt = ["meta_schema_version_unknown.json", "root_missing_meta.json"];
    const declaring: string[] = [];
    for (const name of rejectionFileNames("0.4.0")) {
      const version = declaredVersion(loadRejection(name, "0.4.0").manifest);
      if (exempt.includes(name)) expect(version).not.toBe("0.4.0");
      else {
        expect(version, name).toBe("0.4.0");
        declaring.push(name);
      }
    }
    expect(declaring).toHaveLength(48);
    expect(declaredVersion(loadRejection(exempt[0] as string, "0.4.0").manifest)).toBe("9.9.9");
  });

  it("renders a rejection path as a JSON pointer", () => {
    const testCase = loadRejection(rejectionFileNames()[0] as string);
    const error = rejection(testCase.manifest);
    expect(error.message.startsWith(`${jsonPointer(error.path)}: `)).toBe(true);
  });

  it.each(["0.3.0", "0.1.0", "1.0.0"])(
    "rejects a manifest declaring %s at its declaration",
    (version) => {
      const manifest = loadFixture("bare");
      (manifest.meta as Record<string, unknown>).schema_version = version;
      expect(rejection(manifest).path).toEqual(["meta", "schema_version"]);
    },
  );

  it("exposes JavaScript's unsafe-integer parsing behavior, which parseJson avoids", () => {
    expect(JSON.parse("9007199254740993")).toBe(9007199254740992);
    expect(parseJson("9007199254740993")).toBe(9007199254740993n);
  });

  it.each([
    {
      "stroke-width": 0,
      "stroke-dasharray": "none",
      opacity: 0,
      "font-size": 0.1,
      rx: 0,
      content: "row\tname",
      "max-width": "none",
    },
    { "stroke-dasharray": "0 1.5 2", opacity: 1, "max-width": 1 },
  ])("accepts exact graphical property boundaries %#", (declaration) => {
    const manifest = loadFixture("bare");
    manifest.graphical = { styles: { valid: declaration } };
    validate(manifest);
  });

  it.each([
    ["stroke-width", -0.1],
    ["stroke-dasharray", "3,3"],
    ["opacity", -0.1],
    ["opacity", 1.1],
    ["font-size", 0],
    ["rx", -0.1],
    ["content", 5],
    ["max-width", 0],
  ])("rejects graphical %s value %j at the property", (propertyName, value) => {
    const manifest = loadFixture("bare");
    manifest.graphical = { styles: { invalid: { [propertyName]: value } } };
    expect(rejection(manifest).path).toEqual(["graphical", "styles", "invalid", propertyName]);
  });

  it("leaves names unrestricted", () => {
    const manifest = loadFixture("bare");
    (manifest.timeline as Record<string, unknown>).name = "name\0with\tcontrols";
    validate(manifest);
  });
});
