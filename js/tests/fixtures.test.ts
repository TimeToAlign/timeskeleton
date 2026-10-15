import { describe, expect, it } from "vitest";
import { complete, minimal, parseJson, unknownKeys, validate } from "../src/index.js";
import { fixtureFiles, fixtureText } from "./fixtures.js";

describe("the fixtures", () => {
  it("are found", () => {
    expect(fixtureFiles().length).toBeGreaterThan(0);
    expect(fixtureFiles().filter((file) => file.startsWith("drawings"))).toEqual([]);
  });

  it.each(fixtureFiles())("%s is a manifest without unknown keys", (file) => {
    const value = parseJson(fixtureText(file));
    validate(value);
    expect(unknownKeys(value)).toEqual([]);
    expect(minimal(complete(value))).toEqual(minimal(value));
    expect(complete(minimal(value))).toEqual(complete(value));
  });
});
