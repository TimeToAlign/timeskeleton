import { readdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseJson, SCHEMA_VERSION } from "../src/index.js";

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

/** Directory names of the migration pairs, `<source>-to-<target>`, sorted. */
export function migrationPairs(): string[] {
  return readdirSync(resolve(repositoryRoot, "fixtures", "migrations"))
    .filter((name) => /^\d+\.\d+\.\d+-to-\d+\.\d+\.\d+$/.test(name))
    .sort();
}

/** The split input text and sorted output file names. */
export function splitFixture(): { before: string; after: readonly [string, string][] } {
  const root = resolve(repositoryRoot, "fixtures", "migrations", "split", "0.3.0");
  return {
    before: readFileSync(resolve(root, "before.json"), "utf8"),
    after: readdirSync(resolve(root, "after"))
      .sort()
      .map((name) => [name, readFileSync(resolve(root, "after", name), "utf8")]),
  };
}

/** The text of one side of a migration pair. */
export function migrationText(pair: string, name: "before" | "after"): string {
  return readFileSync(
    resolve(repositoryRoot, "fixtures", "migrations", pair, `${name}.json`),
    "utf8",
  );
}

/** Parse one side of a migration pair afresh; the pair defaults to 0.1.0 to 0.2.0. */
export function migrationFixture(
  name: "before" | "after",
  pair = "0.1.0-to-0.2.0",
): Record<string, unknown> {
  return parseJson(migrationText(pair, name)) as Record<string, unknown>;
}
