import { describe, expect, it } from "vitest";
import {
  compactJson,
  declaredVersion,
  dumps,
  isJsonFloat,
  type Json,
  type Lossless,
  migrate,
  parseJson,
  SCHEMA_VERSION,
  SUPPORTED_VERSIONS,
  UnsupportedVersionError,
  validate,
} from "../src/index.js";
import {
  fixtureFileNames,
  fixtureText,
  loadFixture,
  loadRejection,
  migrationText,
  rejectionFileNames,
  rejectionText,
} from "./fixtures.js";

type JsonObject = Record<string, unknown>;

function read(text: string): JsonObject {
  return parseJson(text) as JsonObject;
}

function withoutGenerator(value: JsonObject): JsonObject {
  delete (value.meta as JsonObject).generator;
  return value;
}

function refusal(value: unknown): UnsupportedVersionError {
  try {
    migrate(value);
  } catch (error) {
    if (error instanceof UnsupportedVersionError) return error;
    throw error;
  }
  throw new Error("value was migrated");
}

describe("migrate", () => {
  it("reproduces the pinned pair", () => {
    const before = migrationText("0.5.0-to-0.6.0", "before.json");
    expect(before).toBe(fixtureText("bare", "0.5.0"));
    const migrated = migrate(read(before));
    expect(dumps(migrated)).toBe(migrationText("0.5.0-to-0.6.0", "after.json"));
    validate(migrated);
  });

  it.each(fixtureFileNames("0.5.0"))("changes only the declaration of %s", (file) => {
    const text = fixtureText(file.slice(0, -5), "0.5.0");
    expect(text.split('"schema_version": "0.5.0"')).toHaveLength(2);
    expect(dumps(migrate(read(text)))).toBe(
      text.replace('"schema_version": "0.5.0"', '"schema_version": "0.6.0"'),
    );
  });

  it.each(fixtureFileNames("0.6.0"))("copies the latest version of %s", (file) => {
    const value = read(fixtureText(file.slice(0, -5), "0.6.0"));
    const migrated = migrate(value);
    expect(migrated).toEqual(value);
    expect(migrated).not.toBe(value);
  });

  it.each(SUPPORTED_VERSIONS)("never changes or shares a %s input", (version) => {
    const text = fixtureText("bare", version);
    const value = read(text);
    const migrated = migrate(value);
    expect(value).toEqual(read(text));
    (migrated.meta as JsonObject).generator = "changed";
    (migrated.timeline as JsonObject).id = "changed";
    (((migrated.timeline as JsonObject).flow_control as JsonObject).markers as unknown[]).push(
      "changed",
    );
    expect(value).toEqual(read(text));
  });

  it.each(SUPPORTED_VERSIONS)("migrates %s to the latest version", (version) => {
    const value = loadFixture("bare");
    (value.meta as JsonObject).schema_version = version;
    expect(declaredVersion(migrate(value))).toBe(SCHEMA_VERSION);
  });

  it("finds the 0.5.0 manifests in the 0.6.0 manifests", () => {
    const names = fixtureFileNames("0.5.0");
    expect(fixtureFileNames("0.6.0")).toEqual(names);
    expect(names).toHaveLength(23);
    for (const file of names) {
      const name = file.slice(0, -5);
      expect(withoutGenerator(migrate(read(fixtureText(name, "0.5.0")))), name).toEqual(
        withoutGenerator(read(fixtureText(name, "0.6.0"))),
      );
    }
  });

  it("finds the 0.5.0 rejection cases in the 0.6.0 cases", () => {
    const names = rejectionFileNames("0.5.0");
    expect(rejectionFileNames("0.6.0")).toEqual(names);
    expect(names).toHaveLength(55);
    const refused = ["meta_schema_version_unknown.json", "root_missing_meta.json"];
    for (const name of names) {
      const before = loadRejection(name, "0.5.0");
      const after = loadRejection(name, "0.6.0");
      expect([before.path, before.reason]).toEqual([after.path, after.reason]);
      if (refused.includes(name)) {
        expect(rejectionText(name, "0.5.0")).toBe(rejectionText(name, "0.6.0"));
      } else {
        expect(migrate(before.manifest), name).toEqual(after.manifest);
      }
    }
  });

  it("keeps exact numbers and the order of keys", () => {
    const text =
      '{"meta":{"schema_version":"0.5.0"},"timeline":{"children":{"10":1.0,"2":123456789012345678}}}';
    const migrated = migrate(parseJson(text)) as JsonObject;
    expect(compactJson(migrated as Lossless<Json>)).toBe(text.replace('"0.5.0"', '"0.6.0"'));
    const children = (migrated.timeline as JsonObject).children as JsonObject;
    expect(isJsonFloat(children["10"])).toBe(true);
    expect(children["2"]).toBe(123456789012345678n);
  });

  it.each([
    [{ schema_version: "9.9.9" }, "9.9.9"],
    [{ schema_version: "0.4.0" }, "0.4.0"],
    [undefined, null],
    [{ schema_version: 5 }, null],
  ])("refuses meta %j as version %j", (meta, version) => {
    const value = loadFixture("bare");
    if (meta === undefined) delete value.meta;
    else value.meta = meta;
    expect(refusal(value).version).toBe(version);
  });

  it("names the supported versions in its refusal", () => {
    const value = loadFixture("bare");
    (value.meta as JsonObject).schema_version = "9.9.9";
    expect(refusal(value).message).toBe(
      'unsupported schema_version "9.9.9"; this package supports 0.5.0, 0.6.0',
    );
  });
});
