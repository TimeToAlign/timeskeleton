import { describe, expect, it } from "vitest";
import {
  MIGRATIONS,
  migrate,
  SCHEMA_VERSION,
  SUPPORTED_VERSIONS,
  UnsupportedVersionError,
  validate,
} from "../src/index.js";
import { FIXTURE_NAMES, fixtureFileNames, loadFixture } from "./fixtures.js";

type Document = Record<string, unknown>;

function unsupported(document: unknown): UnsupportedVersionError {
  try {
    migrate(document);
  } catch (error) {
    if (error instanceof UnsupportedVersionError) {
      return error;
    }
    throw error;
  }
  throw new Error("document was migrated");
}

describe("migrate", () => {
  it("has no migration while one version is published", () => {
    expect(MIGRATIONS).toEqual({});
  });

  it.each(FIXTURE_NAMES)("returns an equal, independent copy of %s", (name) => {
    const document = loadFixture(name);
    const result = migrate(document) as unknown as Document;
    expect(result).toEqual(document);
    expect(result).not.toBe(document);
    (result.meta as Document).generator = "changed";
    expect((document.meta as Document).generator).not.toBe("changed");
    const timelines = (result.manifest as Document).timelines as Record<string, Document>;
    const original = (document.manifest as Document).timelines as Record<string, Document>;
    for (const [timelineId, manifest] of Object.entries(timelines)) {
      (manifest.length as Document).value = -1;
      expect(((original[timelineId] as Document).length as Document).value).not.toBe(-1);
    }
  });

  it.each(SUPPORTED_VERSIONS)("brings every %s fixture to a valid latest document", (version) => {
    const names = fixtureFileNames(version);
    expect(names.length).toBeGreaterThan(0);
    for (const file of names) {
      const result = migrate(loadFixture(file.slice(0, -".json".length), version));
      expect(result.meta.schema_version).toBe(SCHEMA_VERSION);
      validate(result);
    }
  });

  it("refuses an unknown version", () => {
    const document = loadFixture("empty");
    (document.meta as Document).schema_version = "0.2.0";
    const error = unsupported(document);
    expect(error.version).toBe("0.2.0");
    expect(error.name).toBe("UnsupportedVersionError");
  });

  it.each([
    ["no meta", { manifest: { timelines: {} } }],
    ["no schema_version", { meta: {} }],
    ["non-string schema_version", { meta: { schema_version: 1 } }],
  ])("refuses a document with %s", (_name, document) => {
    expect(unsupported(document).version).toBeNull();
  });
});
