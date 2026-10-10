import { describe, expect, it } from "vitest";
import { MIGRATIONS, migrate, SCHEMA_VERSION, SUPPORTED_VERSIONS, validate } from "../src/index.js";
import { fixtureFileNames, loadFixture, migrationFixture } from "./fixtures.js";

describe("migrate", () => {
  it("registers the 0.1.0 to 0.2.0 migration", () => {
    expect(MIGRATIONS["0.1.0"]?.[0]).toBe("0.2.0");
  });

  it("reproduces the shared after fixture", () => {
    expect(migrate(migrationFixture("before"))).toEqual(migrationFixture("after"));
  });

  it.each(SUPPORTED_VERSIONS)("brings every %s fixture to a valid latest document", (version) => {
    for (const file of fixtureFileNames(version)) {
      const result = migrate(loadFixture(file.slice(0, -5), version));
      expect(result.meta.schema_version).toBe(SCHEMA_VERSION);
      validate(result);
    }
  });
});
