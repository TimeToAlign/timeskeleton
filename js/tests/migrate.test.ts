import { describe, expect, it } from "vitest";
import {
  compactJson,
  declaredVersion,
  dumps,
  FILE_KINDS,
  type FileKind,
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

/** The store-built children of `corpus_score_ms3`: 0.6.0 id -> 0.7.0 id. */
const MINTED_CHILDREN: Record<string, string> = { notes: "clt_2", controls: "clt_3" };

/** Rename the store-built children as 0.7.0 does: a minted id, the store name. */
function withMintedChildren(value: JsonObject): JsonObject {
  const timeline = value.timeline as JsonObject;
  const children = timeline.children as JsonObject;
  const renamed: JsonObject = {};
  for (const [store, minted] of Object.entries(MINTED_CHILDREN)) {
    const child = children[store] as JsonObject;
    (child.timeline as JsonObject).id = minted;
    (child.timeline as JsonObject).name = store;
    renamed[minted] = child;
  }
  expect(Object.keys(children).sort()).toEqual(Object.keys(MINTED_CHILDREN).sort());
  timeline.children = renamed;
  return value;
}

/** The value declaring 0.7.0, with `is_segment_line: false` on every timeline. */
function atLatest(value: JsonObject): JsonObject {
  const mark = (timeline: JsonObject): void => {
    timeline.is_segment_line = false;
    for (const entry of Object.values(timeline.children as JsonObject)) {
      mark((entry as JsonObject).timeline as JsonObject);
    }
  };
  (value.meta as JsonObject).schema_version = "0.7.0";
  mark(value.timeline as JsonObject);
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
  it("reproduces the pinned pairs", () => {
    for (const source of ["0.5.0", "0.6.0"]) {
      const target = source === "0.5.0" ? "0.6.0" : "0.7.0";
      expect(migrationText(`${source}-to-${target}`, "before.json")).toBe(
        fixtureText("bare", source),
      );
    }
    const first = migrationText("0.5.0-to-0.6.0", "before.json");
    expect(migrationText("0.5.0-to-0.6.0", "after.json")).toBe(
      first.replace('"schema_version": "0.5.0"', '"schema_version": "0.6.0"'),
    );
    const second = migrationText("0.6.0-to-0.7.0", "before.json");
    expect(migrationText("0.6.0-to-0.7.0", "after.json")).toBe(
      second
        .replace('"schema_version": "0.6.0"', '"schema_version": "0.7.0"')
        .replace('    "id": "bare",\n', '    "id": "bare",\n    "is_segment_line": false,\n'),
    );
    for (const text of [first, second]) {
      const migrated = migrate(read(text));
      expect(dumps(migrated)).toBe(dumps(atLatest(read(text))));
      validate(migrated);
    }
    expect(dumps(migrate(read(second)))).toBe(migrationText("0.6.0-to-0.7.0", "after.json"));
  });

  it.each(
    ["0.5.0", "0.6.0"].flatMap((version) =>
      fixtureFileNames(version).map((file) => [version, file] as const),
    ),
  )("changes only the declaration and the flag of %s/%s", (version, file) => {
    const text = fixtureText(file.slice(0, -5), version);
    expect(text.split(`"schema_version": "${version}"`)).toHaveLength(2);
    expect(dumps(migrate(read(text)))).toBe(dumps(atLatest(read(text))));
  });

  it("marks every timeline", () => {
    const migrated = migrate(read(fixtureText("nested", "0.6.0")));
    const root = migrated.timeline as JsonObject;
    const [child] = Object.values(root.children as JsonObject).map(
      (entry) => (entry as JsonObject).timeline as JsonObject,
    );
    const [grandchild] = Object.values((child as JsonObject).children as JsonObject).map(
      (entry) => (entry as JsonObject).timeline as JsonObject,
    );
    expect([root, child, grandchild].map((timeline) => timeline?.is_segment_line)).toEqual([
      false,
      false,
      false,
    ]);
    for (const timeline of [root, child, grandchild]) delete timeline?.is_segment_line;
    (migrated.meta as JsonObject).schema_version = "0.6.0";
    expect(migrated).toEqual(read(fixtureText("nested", "0.6.0")));
  });

  it.each(
    FILE_KINDS.flatMap((kind) => fixtureFileNames("0.7.0", kind).map((file) => [kind, file])),
  )("copies the latest version of %s %s", (kind, file) => {
    const value = read(fixtureText(file.slice(0, -5), "0.7.0", kind as FileKind));
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
    expect(SCHEMA_VERSION).toBe("0.7.0");
  });

  it.each([
    ["0.5.0", "0.6.0"],
    ["0.6.0", "0.7.0"],
  ])("finds the %s manifests in the %s manifests", (old, current) => {
    const names = fixtureFileNames(old);
    expect(fixtureFileNames(current)).toEqual(names);
    expect(names).toHaveLength(23);
    for (const file of names) {
      const name = file.slice(0, -5);
      let expected = withoutGenerator(migrate(read(fixtureText(name, old))));
      const actual = withoutGenerator(migrate(read(fixtureText(name, current))));
      if (current === "0.7.0" && name === "corpus_score_ms3") {
        expect(expected).not.toEqual(actual);
        expected = withMintedChildren(expected);
      }
      expect(expected, name).toEqual(actual);
    }
  });

  it.each([
    ["0.5.0", "0.6.0", 55],
    ["0.6.0", "0.7.0", 93],
  ])("finds the %s rejection cases in the %s cases", (old, current, count) => {
    const names = rejectionFileNames(old);
    const later = rejectionFileNames(current);
    expect(names).toHaveLength(55);
    expect(later).toHaveLength(count);
    const refused = ["meta_schema_version_unknown.json", "root_missing_meta.json"];
    for (const name of names) {
      expect(later).toContain(name);
      const before = loadRejection(name, old);
      const after = loadRejection(name, current);
      expect(before.path).toEqual(after.path);
      if (current === "0.7.0" && name === "root_missing_timeline.json") {
        expect(after.reason).toBe(
          "A file holds exactly one of timeline, group and bundle beside meta; this one holds none.",
        );
      } else expect(before.reason).toBe(after.reason);
      if (refused.includes(name) && current === "0.6.0") {
        expect(rejectionText(name, old)).toBe(rejectionText(name, current));
      } else if (refused.includes(name)) {
        // migrate refuses these; 0.7.0 gives their timeline the new flag.
        (
          (before.manifest as Record<string, unknown>).timeline as Record<string, unknown>
        ).is_segment_line = false;
        expect(before).toEqual(after);
      } else {
        expect(declaredVersion(after.manifest)).toBe(current);
        expect(migrate(before.manifest), name).toEqual(migrate(after.manifest));
      }
    }
  });

  it("keeps exact numbers and the order of keys", () => {
    const text =
      '{"meta":{"schema_version":"0.5.0"},"timeline":{"children":{"10":1.0,"2":123456789012345678}}}';
    const migrated = migrate(parseJson(text)) as JsonObject;
    expect(compactJson(migrated as Lossless<Json>)).toBe(
      text.replace('"0.5.0"', '"0.7.0"').replace("}}}", '},"is_segment_line":false}}'),
    );
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
      'unsupported schema_version "9.9.9"; this package supports 0.5.0, 0.6.0, 0.7.0',
    );
  });
});
