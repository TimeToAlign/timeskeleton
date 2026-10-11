import { describe, expect, it } from "vitest";
import {
  declaredVersion,
  jsonPointer,
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
    for (const file of fixtureFileNames(version)) validate(loadFixture(file.slice(0, -5), version));
  });

  it.each(SUPPORTED_VERSIONS)("accepts every %s fixture as plain values", (version) => {
    for (const file of fixtureFileNames(version)) {
      validate(parseJson(fixtureText(file.slice(0, -5), version)));
    }
  });

  it.each(rejectionFileNames())("rejects %s at its stored path", (name) => {
    const testCase = loadRejection(name);
    expect(rejection(testCase.manifest ?? testCase.document).path).toEqual(testCase.path);
    const plainCase = parseJson(rejectionText(name)) as Record<string, unknown>;
    expect(rejection(plainCase.manifest ?? plainCase.document).path).toEqual(testCase.path);
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
    expect(declaring).toHaveLength(45);
    expect(declaredVersion(loadRejection(exempt[0] as string, "0.4.0").manifest)).toBe("9.9.9");
  });

  it("renders a rejection path as a JSON pointer", () => {
    const testCase = loadRejection(rejectionFileNames()[0] as string);
    const error = rejection(testCase.manifest ?? testCase.document);
    expect(error.message.startsWith(`${jsonPointer(error.path)}: `)).toBe(true);
  });

  it("exposes JavaScript's unsafe-integer parsing behavior, which parseJson avoids", () => {
    expect(JSON.parse("9007199254740993")).toBe(9007199254740992);
    expect(parseJson("9007199254740993")).toBe(9007199254740993n);
  });
});
