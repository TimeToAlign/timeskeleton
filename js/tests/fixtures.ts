import { readdirSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { parseJson, SCHEMA_VERSION } from "../src/index.js";

const here = dirname(fileURLToPath(import.meta.url));

/** The repository root, which holds the only copies of `schema/` and `fixtures/`. */
export const repositoryRoot = resolve(here, "../..");

/** The directory of the manifest fixtures. */
export const fixtureDirectory = resolve(repositoryRoot, "fixtures", SCHEMA_VERSION);

/**
 * The manifest fixtures, as paths relative to `fixtureDirectory`, sorted:
 * every `*.json` below it except the drawings.
 */
export function fixtureFiles(directory = ""): string[] {
  const files: string[] = [];
  for (const name of readdirSync(resolve(fixtureDirectory, directory)).sort()) {
    const path = join(directory, name);
    if (statSync(resolve(fixtureDirectory, path)).isDirectory()) {
      if (path !== "drawings") files.push(...fixtureFiles(path));
    } else if (name.endsWith(".json")) files.push(path);
  }
  return files.sort();
}

/** The text of one fixture, by its path relative to `fixtureDirectory`. */
export function fixtureText(path: string): string {
  return readFileSync(resolve(fixtureDirectory, path), "utf8");
}

function caseDirectory(kind: "rejections" | "warnings"): string {
  return resolve(repositoryRoot, "fixtures", kind, SCHEMA_VERSION);
}

export function rejectionFileNames(): string[] {
  return readdirSync(caseDirectory("rejections")).sort();
}

/** The text of one rejection case. */
export function rejectionText(name: string): string {
  return readFileSync(resolve(caseDirectory("rejections"), name), "utf8");
}

export function warningFileNames(): string[] {
  return readdirSync(caseDirectory("warnings")).sort();
}

/** The text of one warning case. */
export function warningText(name: string): string {
  return readFileSync(resolve(caseDirectory("warnings"), name), "utf8");
}

/** Parse the schema document from the repository root. */
export function loadSchemaFile(): Record<string, unknown> {
  const path = resolve(repositoryRoot, "schema", SCHEMA_VERSION, "timeskeleton.schema.json");
  return parseJson(readFileSync(path, "utf8")) as Record<string, unknown>;
}

type JsonObject = Record<string, unknown>;

/** A timeline of the minimal form. */
export function timeline(
  id: string,
  unit = "quarters",
  length: unknown = [8, 1],
  members: JsonObject = {},
): JsonObject {
  return { id, unit, length, ...members };
}

/** A manifest of the given roots in the minimal form. */
export function manifest(timelines: JsonObject[], members: JsonObject = {}): JsonObject {
  return { timeskeleton: "0.7.0", timelines, ...members };
}

export function group(id: string, members: string[], rest: JsonObject = {}): JsonObject {
  return { id, members, ...rest };
}

/** A named manifest: two groups, two ungrouped roots, a child as a member. */
export function bundle(): JsonObject {
  return manifest(
    [
      timeline("annotations"),
      timeline("page", "pixels", 1200),
      timeline("performance", "seconds", 61.5),
      timeline("recording", "seconds", 120.5, {
        children: [timeline("excerpt", "seconds", 30.5, { offset: 2.5 })],
      }),
      timeline("score"),
    ],
    {
      id: "op35",
      name: "Mixed",
      groups: [group("group_1", ["performance", "score"]), group("group_2", ["excerpt", "page"])],
      graphical: { order: { group_1: ["score", "performance"], group_2: ["page", "excerpt"] } },
    },
  );
}
