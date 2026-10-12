import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { type FileKind, parseJson, SCHEMA_VERSION } from "../src/index.js";

const here = dirname(fileURLToPath(import.meta.url));

/** The repository root, which holds the only copies of `schema/` and `fixtures/`. */
export const repositoryRoot = resolve(here, "../..");

/** The directory of one file kind's fixtures: timeline files directly, the others in `groups/`, `bundles/`. */
export function fixtureDirectory(
  version: string = SCHEMA_VERSION,
  kind: FileKind = "timeline",
): string {
  const directory = resolve(repositoryRoot, "fixtures", version);
  return kind === "timeline" ? directory : resolve(directory, `${kind}s`);
}

/** Sorted file names of the fixtures of one kind bundled for a version. */
export function fixtureFileNames(
  version: string = SCHEMA_VERSION,
  kind: FileKind = "timeline",
): string[] {
  if (!existsSync(fixtureDirectory(version, kind))) return [];
  return readdirSync(fixtureDirectory(version, kind))
    .filter((name) => name.endsWith(".json"))
    .sort();
}

/** The text of one fixture. */
export function fixtureText(
  name: string,
  version: string = SCHEMA_VERSION,
  kind: FileKind = "timeline",
): string {
  return readFileSync(resolve(fixtureDirectory(version, kind), `${name}.json`), "utf8");
}

/** Read one fixture afresh with the lossless `parseJson`; every call returns a new object. */
export function loadFixture(
  name: string,
  version: string = SCHEMA_VERSION,
): Record<string, unknown> {
  return parseJson(fixtureText(name, version)) as Record<string, unknown>;
}

/**
 * Parse one schema document of a version from the repository root: the one
 * file of 0.5.0 and 0.6.0, or `schema/<version>/<document>.schema.json`.
 */
export function loadSchemaFile(
  version: string = SCHEMA_VERSION,
  document = "timeline",
): Record<string, unknown> {
  const single = resolve(repositoryRoot, "schema", `timeskeleton-${version}.schema.json`);
  const path = existsSync(single)
    ? single
    : resolve(repositoryRoot, "schema", version, `${document}.schema.json`);
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

type JsonObject = Record<string, unknown>;

/** The 0.7.0 `bare` manifest renamed, without a name, with children of 4 quarters. */
function timeline(id: string, children: Record<string, [number, JsonObject]> = {}): JsonObject {
  const value = loadFixture("bare", "0.7.0").timeline as JsonObject;
  value.id = id;
  value.name = null;
  for (const [key, [offset, child]] of Object.entries(children)) {
    (child.length as JsonObject).value = [4, 1];
    (value.children as JsonObject)[key] = {
      offset: { unit: "quarters", number_type: "fraction", value: [offset, 1] },
      timeline: child,
    };
  }
  return value;
}

/** The group document of the test README, built afresh: a child and a root as members. */
export function groupDocument(): JsonObject {
  return {
    meta: { schema_version: "0.7.0" },
    timelines: [
      timeline("piece", { "second-half": [4, timeline("second-half")] }),
      timeline("recording"),
    ],
    group: { id: "group_1", name: "Second half", meta: {}, members: ["recording", "second-half"] },
    graphical: { order: ["second-half", "recording"] },
  };
}

/** The bundle document of the test README, built afresh: two groups, two ungrouped roots. */
export function bundleDocument(): JsonObject {
  const group = (id: string, name: string, members: string[]) => ({ id, name, meta: {}, members });
  return {
    meta: { schema_version: "0.7.0" },
    timelines: [
      timeline("annotations"),
      timeline("page"),
      timeline("performance"),
      timeline("recording", { excerpt: [2, timeline("excerpt")] }),
      timeline("score"),
    ],
    bundle: {
      id: "bundle_1",
      name: "Mixed",
      meta: {},
      support_policy: "omit",
      groups: [
        group("group_1", "Performance", ["performance", "score"]),
        group("group_2", "Facsimile", ["excerpt", "page"]),
      ],
    },
    graphical: { order: { group_1: ["score", "performance"], group_2: ["page", "excerpt"] } },
  };
}
