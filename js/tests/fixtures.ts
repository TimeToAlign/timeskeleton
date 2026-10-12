import { readdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseJson, SCHEMA_VERSION } from "../src/index.js";

const here = dirname(fileURLToPath(import.meta.url));

/** The repository root, which holds the only copies of `schema/` and `fixtures/`. */
export const repositoryRoot = resolve(here, "../..");

export function fixtureDirectory(version: string = SCHEMA_VERSION): string {
  return resolve(repositoryRoot, "fixtures", version);
}

/** Sorted file names of the fixtures bundled for a version. */
export function fixtureFileNames(version: string = SCHEMA_VERSION): string[] {
  return readdirSync(fixtureDirectory(version))
    .filter((name) => name.endsWith(".json"))
    .sort();
}

/** The text of one fixture. */
export function fixtureText(name: string, version: string = SCHEMA_VERSION): string {
  return readFileSync(resolve(fixtureDirectory(version), `${name}.json`), "utf8");
}

/** Read one fixture afresh with the lossless `parseJson`; every call returns a new object. */
export function loadFixture(
  name: string,
  version: string = SCHEMA_VERSION,
): Record<string, unknown> {
  return parseJson(fixtureText(name, version)) as Record<string, unknown>;
}

/** Parse the schema file of a version from the repository root. */
export function loadSchemaFile(version: string = SCHEMA_VERSION): Record<string, unknown> {
  const path = resolve(repositoryRoot, "schema", `timeskeleton-${version}.schema.json`);
  return JSON.parse(readFileSync(path, "utf8")) as Record<string, unknown>;
}

export function rejectionFileNames(version: string = SCHEMA_VERSION): string[] {
  return readdirSync(resolve(repositoryRoot, "fixtures", "rejections", version)).sort();
}

/** The text of one rejection case. */
export function rejectionText(name: string, version: string = SCHEMA_VERSION): string {
  return readFileSync(resolve(repositoryRoot, "fixtures", "rejections", version, name), "utf8");
}

export function loadRejection(
  name: string,
  version: string = SCHEMA_VERSION,
): Record<string, unknown> {
  return parseJson(rejectionText(name, version)) as Record<string, unknown>;
}

/** The text of one file of a migration pair, e.g. `("0.5.0-to-0.6.0", "before.json")`. */
export function migrationText(pair: string, file: string): string {
  return readFileSync(resolve(repositoryRoot, "fixtures", "migrations", pair, file), "utf8");
}
