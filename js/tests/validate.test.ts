import { describe, expect, it } from "vitest";
import { jsonPointer, SchemaValidationError, SUPPORTED_VERSIONS, validate } from "../src/index.js";
import { fixtureFileNames, loadFixture, loadRejection, rejectionFileNames } from "./fixtures.js";

function rejection(document: unknown): SchemaValidationError {
  try {
    validate(document);
  } catch (error) {
    if (error instanceof SchemaValidationError) return error;
    throw error;
  }
  throw new Error("document was accepted");
}

describe("validate", () => {
  it.each(SUPPORTED_VERSIONS)("accepts every %s fixture", (version) => {
    for (const file of fixtureFileNames(version)) validate(loadFixture(file.slice(0, -5), version));
  });

  it.each(rejectionFileNames())("rejects %s at its stored path", (name) => {
    const testCase = loadRejection(name);
    expect(rejection(testCase.document).path).toEqual(testCase.path);
  });

  it("renders a rejection path as a JSON pointer", () => {
    const error = rejection(loadRejection(rejectionFileNames()[0] as string).document);
    expect(error.message.startsWith(`${jsonPointer(error.path)}: `)).toBe(true);
  });

  it("exposes JavaScript's unsafe-integer parsing behavior", () => {
    expect(JSON.parse("9007199254740993")).toBe(9007199254740992);
  });
});
