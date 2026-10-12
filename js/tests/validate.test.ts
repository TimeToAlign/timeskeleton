import { describe, expect, it } from "vitest";
import {
  declaredVersion,
  identityProblems,
  jsonPointer,
  parse,
  parseJson,
  SchemaValidationError,
  SUPPORTED_VERSIONS,
  validate,
} from "../src/index.js";
import {
  fixtureFileNames,
  fixtureText,
  loadFixture,
  loadRejection,
  rejectionFileNames,
  rejectionText,
} from "./fixtures.js";

function rejection(value: unknown): SchemaValidationError {
  try {
    validate(value);
  } catch (error) {
    if (error instanceof SchemaValidationError) return error;
    throw error;
  }
  throw new Error("value was accepted");
}

describe("validate", () => {
  it.each(SUPPORTED_VERSIONS)("accepts every %s fixture", (version) => {
    for (const file of fixtureFileNames(version)) {
      expect(parse(fixtureText(file.slice(0, -5), version))).toBeDefined();
    }
  });

  it.each(SUPPORTED_VERSIONS)("accepts every %s fixture as JSON.parse reads it", (version) => {
    for (const file of fixtureFileNames(version)) {
      validate(JSON.parse(fixtureText(file.slice(0, -5), version)));
    }
  });

  it.each(
    SUPPORTED_VERSIONS.flatMap((version) =>
      rejectionFileNames(version).map((name) => [version, name] as const),
    ),
  )("rejects %s/%s at its stored path", (version, name) => {
    const testCase = loadRejection(name, version);
    expect(rejection(testCase.manifest).path).toEqual(testCase.path);
    const plainCase = parseJson(rejectionText(name, version)) as Record<string, unknown>;
    expect(rejection(plainCase.manifest).path).toEqual(testCase.path);
  });

  it("holds 55 rejection cases per version", () => {
    expect(SUPPORTED_VERSIONS.map((version) => rejectionFileNames(version).length)).toEqual([
      55, 55,
    ]);
  });

  it.each(SUPPORTED_VERSIONS)(
    "has every rejection declare its version except the two without a declaration (%s)",
    (version) => {
      const declared = new Map(
        rejectionFileNames(version).map((name) => [
          name,
          declaredVersion(loadRejection(name, version).manifest),
        ]),
      );
      expect(declared.get("meta_schema_version_unknown.json")).toBe("9.9.9");
      expect(declared.get("root_missing_meta.json")).toBeNull();
      declared.delete("meta_schema_version_unknown.json");
      declared.delete("root_missing_meta.json");
      expect(declared.size).toBe(53);
      expect(new Set(declared.values())).toEqual(new Set([version]));
    },
  );

  it("renders a rejection path as a JSON pointer", () => {
    const testCase = loadRejection(rejectionFileNames()[0] as string);
    const error = rejection(testCase.manifest);
    expect(error.message.startsWith(`${jsonPointer(error.path)}: `)).toBe(true);
  });

  it.each(["0.3.0", "0.1.0", "0.4.0", "1.0.0"])(
    "rejects a manifest declaring %s at its declaration",
    (version) => {
      const manifest = loadFixture("bare");
      (manifest.meta as Record<string, unknown>).schema_version = version;
      expect(rejection(manifest).path).toEqual(["meta", "schema_version"]);
    },
  );

  it("exposes JavaScript's unsafe-integer parsing behavior, which parseJson avoids", () => {
    expect(JSON.parse("9007199254740993")).toBe(9007199254740992);
    expect(parseJson("9007199254740993")).toBe(9007199254740993n);
  });

  it.each([
    {
      "stroke-width": 0,
      "stroke-dasharray": "none",
      opacity: 0,
      "font-size": 0.1,
      rx: 0,
      content: "row\tname",
      "max-width": "none",
    },
    { "stroke-dasharray": "0 1.5 2", opacity: 1, "max-width": 1 },
  ])("accepts exact graphical property boundaries %#", (declaration) => {
    const manifest = loadFixture("bare");
    manifest.graphical = { styles: { valid: declaration } };
    validate(manifest);
  });

  it.each([
    ["stroke-width", -0.1],
    ["stroke-dasharray", "3,3"],
    ["opacity", -0.1],
    ["opacity", 1.1],
    ["font-size", 0],
    ["rx", -0.1],
    ["content", 5],
    ["max-width", 0],
  ])("rejects graphical %s value %j at the property", (propertyName, value) => {
    const manifest = loadFixture("bare");
    manifest.graphical = { styles: { invalid: { [propertyName]: value } } };
    expect(rejection(manifest).path).toEqual(["graphical", "styles", "invalid", propertyName]);
  });

  it("leaves names unrestricted", () => {
    const manifest = loadFixture("bare");
    (manifest.timeline as Record<string, unknown>).name = "name\0with\tcontrols";
    validate(manifest);
  });
});

type JsonObject = Record<string, unknown>;

function coordinate(value: number): JsonObject {
  return { unit: "quarters", number_type: "fraction", value: [value, 1] };
}

function marker(id: string): JsonObject {
  return { id, name: null, coordinate: coordinate(1) };
}

function jump(id: string, target: string | null): JsonObject {
  return {
    id,
    from_coordinate: coordinate(4),
    to_coordinate: coordinate(0),
    control_type: "repeat_end",
    condition: "always",
    repeat_count: 1,
    target,
    label: null,
    meta: {},
  };
}

/** Add a copy of the root, without its children, as child `id` at offset 0. */
function withChild(manifest: JsonObject, id: string): JsonObject {
  const root = manifest.timeline as JsonObject;
  const child = { ...(parseJson(JSON.stringify(root)) as JsonObject), id, children: {} };
  (root.children as JsonObject)[id] = { offset: coordinate(0), timeline: child };
  return child;
}

function flowOf(timeline: unknown): JsonObject {
  return (timeline as JsonObject).flow_control as JsonObject;
}

function problemsOf(manifest: JsonObject): [unknown, string][] {
  return identityProblems(manifest as never).map((problem) => [problem.path, problem.detail]);
}

describe("identityProblems", () => {
  it("finds none in any fixture", () => {
    for (const file of fixtureFileNames()) {
      expect(identityProblems(loadFixture(file.slice(0, -5)) as never), file).toEqual([]);
    }
  });

  it("reports each repeated id once, at its later occurrence", () => {
    const manifest = loadFixture("bare");
    const child = withChild(manifest, "c");
    flowOf(manifest.timeline).markers = [marker("m"), marker("m"), marker("bare")];
    flowOf(child).markers = [marker("m")];
    expect(problemsOf(manifest)).toEqual([
      [
        ["timeline", "flow_control", "markers", 1, "id"],
        'duplicate id "m", first at #/timeline/flow_control/markers/0/id',
      ],
      [
        ["timeline", "flow_control", "markers", 2, "id"],
        'duplicate id "bare", first at #/timeline/id',
      ],
      [
        ["timeline", "children", "c", "timeline", "flow_control", "markers", 0, "id"],
        'duplicate id "m", first at #/timeline/flow_control/markers/0/id',
      ],
    ]);
    expect(rejection(manifest).path).toEqual(["timeline", "flow_control", "markers", 1, "id"]);
  });

  it("visits children in code-point order of their keys", () => {
    const manifest = loadFixture("bare");
    for (const key of ["\u{1F600}", "\u{FB00}"]) {
      flowOf(withChild(manifest, key)).markers = [marker("shared")];
    }
    expect(problemsOf(manifest).map(([path]) => path)).toEqual([
      ["timeline", "children", "\u{1F600}", "timeline", "flow_control", "markers", 0, "id"],
    ]);
  });

  it("requires a jump's target to name a marker of its own timeline", () => {
    const manifest = loadFixture("bare");
    const child = withChild(manifest, "c");
    const flow = flowOf(manifest.timeline);
    flow.markers = [marker("here")];
    flow.jumps = [jump("j1", "here"), jump("j2", null), jump("j3", "there")];
    flowOf(child).markers = [marker("there")];
    flowOf(child).jumps = [jump("j4", "here")];
    expect(problemsOf(manifest)).toEqual([
      [
        ["timeline", "flow_control", "jumps", 2, "target"],
        '"there" names no marker of this timeline',
      ],
      [
        ["timeline", "children", "c", "timeline", "flow_control", "jumps", 0, "target"],
        '"here" names no marker of this timeline',
      ],
    ]);
  });

  it("lists duplicates before dangling targets", () => {
    const manifest = loadFixture("bare");
    const flow = flowOf(manifest.timeline);
    flow.jumps = [jump("j", "nowhere")];
    flow.markers = [marker("j")];
    expect(problemsOf(manifest).map(([path]) => path)).toEqual([
      ["timeline", "flow_control", "markers", 0, "id"],
      ["timeline", "flow_control", "jumps", 0, "target"],
    ]);
  });
});
