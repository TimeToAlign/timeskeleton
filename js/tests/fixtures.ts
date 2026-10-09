import { readdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { SCHEMA_VERSION } from "../src/index.js";

const here = dirname(fileURLToPath(import.meta.url));

/** The repository root, which holds the only copies of `schema/` and `fixtures/`. */
export const repositoryRoot = resolve(here, "../..");

export const FIXTURE_NAMES = [
  "continuous_graphical",
  "continuous_logical",
  "continuous_physical",
  "discrete_graphical",
  "discrete_logical",
  "discrete_physical",
  "empty",
  "nested",
  "with_region",
] as const;

export type FixtureName = (typeof FIXTURE_NAMES)[number];

export function fixtureDirectory(version: string = SCHEMA_VERSION): string {
  return resolve(repositoryRoot, "fixtures", version);
}

/** Sorted file names of the fixtures bundled for a version. */
export function fixtureFileNames(version: string = SCHEMA_VERSION): string[] {
  return readdirSync(fixtureDirectory(version))
    .filter((name) => name.endsWith(".json"))
    .sort();
}

/** Parse one fixture afresh; every call returns a new object. */
export function loadFixture(
  name: string,
  version: string = SCHEMA_VERSION,
): Record<string, unknown> {
  const text = readFileSync(resolve(fixtureDirectory(version), `${name}.json`), "utf8");
  return JSON.parse(text) as Record<string, unknown>;
}

/** Parse the schema file of a version from the repository root. */
export function loadSchemaFile(version: string = SCHEMA_VERSION): Record<string, unknown> {
  const path = resolve(repositoryRoot, "schema", `timeskeleton-${version}.schema.json`);
  return JSON.parse(readFileSync(path, "utf8")) as Record<string, unknown>;
}
