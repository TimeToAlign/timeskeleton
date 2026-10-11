import { spawnSync } from "node:child_process";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  canonicalJson,
  compactJson,
  declaredVersion,
  dumps,
  ENVELOPE_VERSIONS,
  isJsonObject,
  type Json,
  JsonFloat,
  type Lossless,
  MIGRATIONS,
  MigrationError,
  migrate,
  parseJson,
  SCHEMA_VERSION,
  SUPPORTED_VERSIONS,
  split,
  validate,
} from "../src/index.js";
import { clone } from "../src/manifest.js";
import {
  fixtureDirectory,
  fixtureFileNames,
  fixtureText,
  loadFixture,
  migrationFixture,
  migrationPairs,
  migrationText,
  splitFixture,
} from "./fixtures.js";

type JsonObject = Record<string, unknown>;
type LosslessJson = Lossless<Json>;

function firstTimeline(envelope: JsonObject): [string, JsonObject] {
  const timelines = (envelope.manifest as JsonObject).timelines as JsonObject;
  const [entry] = Object.entries(timelines);
  return entry as [string, JsonObject];
}

function measure(envelope: JsonObject, index: number): JsonObject {
  const [, timeline] = firstTimeline(envelope);
  return ((timeline.measure_map as JsonObject).measures as JsonObject[])[index] as JsonObject;
}

function refusal(envelope: JsonObject): MigrationError {
  try {
    migrate(envelope);
  } catch (error) {
    if (error instanceof MigrationError) return error;
    throw error;
  }
  throw new Error("envelope was migrated");
}

/** Apply the one migration registered for the fixture's version. */
function step(value: JsonObject): JsonObject {
  const registered = MIGRATIONS[declaredVersion(value) as string];
  if (registered === undefined) throw new Error("no migration registered");
  return registered[1](clone(value));
}

/** The standard formatting without the canonical order. */
function text(value: unknown): string {
  const pretty = (item: unknown, depth: number): string => {
    const indent = "  ".repeat(depth);
    const inner = "  ".repeat(depth + 1);
    if (Array.isArray(item)) {
      if (item.length === 0) return "[]";
      return `[\n${item.map((entry) => `${inner}${pretty(entry, depth + 1)}`).join(",\n")}\n${indent}]`;
    }
    if (isJsonObject(item)) {
      const entries = Object.entries(item);
      if (entries.length === 0) return "{}";
      return `{\n${entries
        .map(([key, entry]) => `${inner}${compactJson(key)}: ${pretty(entry, depth + 1)}`)
        .join(",\n")}\n${indent}}`;
    }
    return compactJson(item as Lossless<Json>);
  };
  return `${pretty(value, 0)}\n`;
}

/** The standard writer of the fixture's version: canonical order from 0.2.1. */
function write(value: JsonObject): string {
  const version = declaredVersion(value);
  return version === "0.1.0" || version === "0.2.0" ? text(value) : dumps(value);
}

describe("migrate", () => {
  it("registers every migration through 0.4.0", () => {
    expect(
      Object.fromEntries(Object.entries(MIGRATIONS).map(([source, [target]]) => [source, target])),
    ).toEqual({
      "0.1.0": "0.2.0",
      "0.2.0": "0.2.1",
      "0.2.1": "0.3.0",
      "0.3.0": "0.4.0",
    });
  });

  it.each(migrationPairs())("reproduces the %s pair byte for byte", (pair) => {
    const [source, target] = pair.split("-to-");
    const before = migrationFixture("before", pair);
    expect(declaredVersion(before)).toBe(source);
    const result = step(before);
    expect((result.meta as JsonObject).schema_version).toBe(target);
    expect(write(result)).toBe(migrationText(pair, "after"));
    validate(result);
    const roots = ((before.manifest as JsonObject | undefined)?.timelines ?? {}) as JsonObject;
    if (target === "0.4.0" || Object.keys(roots).length === 1) validate(migrate(before));
    else for (const part of split(before)) validate(migrate(part));
  });

  it("carries rows and the derived map id", () => {
    const [, timeline] = firstTimeline(step(migrationFixture("before")));
    const rows = timeline.measure_map as JsonObject[];
    expect(rows.map((row) => row.count)).toEqual([1, 2, 3, 4]);
    expect(rows[0]?.offset_within_measure).toEqual([3, 1]);
    expect(rows[2]?.next).toEqual(["2", "4"]);
    const positionMap = (timeline.conversion_maps as JsonObject[])[0] as JsonObject;
    expect(Object.keys(positionMap)).toEqual([
      "type",
      "id",
      "name",
      "source_unit",
      "target_unit",
      "meter_map",
      "beat_map_id",
    ]);
    expect(positionMap.beat_map_id).toBe("map:BeatInMeasureMap_1");
  });

  it.each([
    [1, "class", "SplitRegularMeasure"],
    [2, "next", ["m2", "m9"]],
    [2, "next", [["m2"]]],
    [0, "count", true],
  ] as const)("refuses measure %i with an unknown %s at its path", (index, key, value) => {
    const envelope = migrationFixture("before");
    measure(envelope, index)[key] = value;
    const [id] = firstTimeline(envelope);
    expect(refusal(envelope).path).toEqual([
      "manifest",
      "timelines",
      id,
      "measure_map",
      "measures",
      index,
      key,
    ]);
  });

  it("reads an integral JSON number in a pair as an integer", () => {
    const envelope = migrationFixture("before");
    expect(measure(envelope, 1).qstamp).toEqual([1, 1]);
    measure(envelope, 1).qstamp = parseJson("[1.0, 1]");
    expect((measure(envelope, 1).qstamp as unknown[])[0]).toBeInstanceOf(JsonFloat);
    expect(write(step(envelope))).toBe(migrationText("0.1.0-to-0.2.0", "after"));
  });

  it("refuses a metrical position map whose maps are not derived", () => {
    const envelope = migrationFixture("before");
    const [id, timeline] = firstTimeline(envelope);
    const positionMap = (timeline.conversion_maps as JsonObject[])[0] as JsonObject;
    ((positionMap.maps as JsonObject).beat as JsonObject).name = "renamed";
    expect(refusal(envelope).path).toEqual([
      "manifest",
      "timelines",
      id,
      "conversion_maps",
      0,
      "maps",
    ]);
  });

  it("refuses an unknown conversion map type through the schema", () => {
    const envelope = migrationFixture("before");
    const [id, timeline] = firstTimeline(envelope);
    ((timeline.conversion_maps as JsonObject[])[1] as JsonObject).type = "UnknownMap";
    expect(refusal(envelope).path).toEqual(["manifest", "timelines", id, "conversion_maps", 1]);
  });

  it.each(SUPPORTED_VERSIONS)(
    "brings every one-root %s fixture to a valid latest value",
    (version) => {
      for (const file of fixtureFileNames(version)) {
        const value = loadFixture(file.slice(0, -5), version);
        const roots = ((value.manifest as JsonObject | undefined)?.timelines ?? {}) as JsonObject;
        if (version !== "0.4.0" && Object.keys(roots).length !== 1) continue;
        const result = migrate(value);
        expect(result.meta.schema_version).toBe(SCHEMA_VERSION);
        validate(result);
      }
    },
  );
});

// -- 0.2.0 to 0.2.1: canonical order ----------------------------------------------

function at(numerator: number, denominator = 1): JsonObject {
  return { unit: "quarters", number_type: "fraction", value: [numerator, denominator] };
}

/** The 0.2.0 flow-control fixture, extended with ties at every key level. */
function tiedEnvelope(): JsonObject {
  const envelope = loadFixture("flow_control", "0.2.0");
  const timelines = (envelope.manifest as JsonObject).timelines as JsonObject;
  const timeline = timelines["flow:quarters"] as JsonObject;
  const pristine = clone(timeline);
  const copyOf = (id: string): JsonObject => ({ ...clone(pristine), id });

  const nested = copyOf("z");
  nested.children = {
    y: { offset: at(1), timeline: copyOf("y") },
    x: { offset: at(0), timeline: copyOf("x") },
  };
  timeline.children = {
    z: { offset: at(1), timeline: nested },
    m: { offset: at(1), timeline: copyOf("m") },
    b: { offset: at(5, 8), timeline: copyOf("b") },
    a: { offset: at(2, 3), timeline: copyOf("a") },
  };
  timeline.conversion_maps = ["\u{1F600}", "\u{FB00}", "b", "a", "B"].map((id) => ({
    type: "ShiftMap",
    id,
    name: id,
    source_unit: "quarters",
    target_unit: null,
    offset: [1, 2],
  }));
  timeline.regions = (
    [
      ["b", at(2), at(6)],
      ["a", at(2), at(6)],
      ["c", at(2), at(4)],
      ["d", at(5, 8), at(2, 3)],
    ] as const
  ).map(([name, start, end]) => ({ name, start, end, meta: {} }));
  const flow = timeline.flow_control as JsonObject;
  const [fine] = flow.breaks as JsonObject[];
  flow.breaks = [
    { ...fine, condition: "always", label: "always" },
    { ...fine, coordinate: at(5, 8), label: "early" },
    fine,
  ];
  const [repeat] = flow.jumps as JsonObject[];
  flow.jumps = [
    repeat,
    { ...repeat, control_type: "da_capo", label: "DaCapo" },
    { ...repeat, to_coordinate: at(2, 3), label: "short" },
    { ...repeat, from_coordinate: at(5, 8), label: "early" },
  ];
  for (const name of ["\u{1F600}", "\u{FB00}", "\u{E9}", "Coda"]) {
    (flow.markers as JsonObject)[name] = at(2);
  }
  timelines["\u{1F600}"] = copyOf("\u{1F600}");
  timelines.Flow = copyOf("Flow");
  return envelope;
}

function orders(envelope: JsonObject): Record<string, unknown[]> {
  const timelines = (envelope.manifest as JsonObject).timelines as Record<string, JsonObject>;
  const score = timelines.score as JsonObject;
  const perf = timelines.perf as JsonObject;
  const children = score.children as Record<string, { timeline: JsonObject }>;
  const nested = children.z as { timeline: JsonObject };
  const flow = score.flow_control as JsonObject;
  const pick = (entries: unknown, key: string) =>
    (entries as JsonObject[]).map((entry) => entry[key]);
  return {
    timelines: Object.keys(timelines),
    children: Object.keys(children),
    nested: Object.keys(nested.timeline.children as JsonObject),
    maps: pick(score.conversion_maps, "id"),
    regions: pick(score.regions, "name"),
    breaks: pick(flow.breaks, "label"),
    jumps: pick(flow.jumps, "label"),
    markers: Object.keys(flow.markers as JsonObject),
    "int regions": pick(perf.regions, "name"),
  };
}

describe("the canonical order of 0.2.1", () => {
  it("is the library's: every 0.2.0 fixture migrates to its 0.2.1 fixture", () => {
    const previous = fixtureFileNames("0.2.0");
    expect(previous).toEqual(fixtureFileNames("0.2.1"));
    const reordered: string[] = [];
    for (const file of previous) {
      const name = file.slice(0, -5);
      const envelope = loadFixture(name, "0.2.0");
      const expected = loadFixture(name, "0.2.1");
      const result = step(envelope);
      (result.meta as JsonObject).generator = (expected.meta as JsonObject).generator;
      expect(dumps(result), name).toBe(fixtureText(name, "0.2.1"));
      envelope.meta = result.meta;
      if (text(envelope) !== text(result)) reordered.push(file);
    }
    expect(reordered).toEqual([
      "conversion_maps.json",
      "corpus_parangonar_parangonada.json",
      "corpus_score_ms3.json",
    ]);
  });

  it("moves the pair from insertion order to canonical order", () => {
    const before = migrationFixture("before", "0.2.0-to-0.2.1");
    expect(orders(before)).toEqual({
      timelines: ["score", "perf"],
      children: ["z", "m", "b", "a"],
      nested: ["y", "x"],
      maps: ["shift", "scale", "label"],
      regions: ["verse", "intro", "alpha", "coda"],
      breaks: ["early", "section", "fine"],
      jumps: ["first", "repeat", "inner", "segno"],
      markers: ["segno", "coda", "Fine"],
      "int regions": ["late", "early"],
    });
    expect(orders(step(before))).toEqual({
      timelines: ["perf", "score"],
      children: ["b", "a", "m", "z"],
      nested: ["x", "y"],
      maps: ["label", "scale", "shift"],
      regions: ["coda", "intro", "alpha", "verse"],
      breaks: ["early", "fine", "section"],
      jumps: ["first", "inner", "segno", "repeat"],
      markers: ["Fine", "coda", "segno"],
      "int regions": ["early", "late"],
    });
  });

  it("resolves every tie", () => {
    const result = step(tiedEnvelope());
    validate(result);
    const timelines = (result.manifest as JsonObject).timelines as JsonObject;
    expect(Object.keys(timelines)).toEqual(["Flow", "flow:quarters", "\u{1F600}"]);
    const timeline = timelines["flow:quarters"] as JsonObject;
    const children = timeline.children as Record<string, { timeline: JsonObject }>;
    expect(Object.keys(children)).toEqual(["b", "a", "m", "z"]);
    const nested = children.z as { timeline: JsonObject };
    expect(Object.keys(nested.timeline.children as JsonObject)).toEqual(["x", "y"]);
    expect((timeline.conversion_maps as JsonObject[]).map((entry) => entry.id)).toEqual([
      "B",
      "a",
      "b",
      "\u{FB00}",
      "\u{1F600}",
    ]);
    expect((timeline.regions as JsonObject[]).map((entry) => entry.name)).toEqual([
      "d",
      "c",
      "a",
      "b",
    ]);
    const flow = timeline.flow_control as JsonObject;
    expect((flow.breaks as JsonObject[]).map((entry) => entry.label)).toEqual([
      "early",
      "Fine",
      "always",
    ]);
    expect((flow.jumps as JsonObject[]).map((entry) => entry.label)).toEqual([
      "early",
      "short",
      "DaCapo",
      "Repeat",
    ]);
    expect(Object.keys(flow.markers as JsonObject)).toEqual([
      "Coda",
      "repeat-start",
      "\u{E9}",
      "\u{FB00}",
      "\u{1F600}",
    ]);
  });

  it("refuses an invalid envelope at the path of the input", () => {
    const envelope = tiedEnvelope();
    const timelines = (envelope.manifest as JsonObject).timelines as JsonObject;
    const flow = (timelines["flow:quarters"] as JsonObject).flow_control as JsonObject;
    ((flow.breaks as JsonObject[])[0] as JsonObject).control_type = "pause";
    const error = refusal(envelope);
    expect(error.path).toEqual([
      "manifest",
      "timelines",
      "flow:quarters",
      "flow_control",
      "breaks",
      0,
      "control_type",
    ]);
    expect(error.detail.startsWith("no 0.2.1 shape: ")).toBe(true);
  });
});

describe("canonical JSON text", () => {
  it("sorts keys by code point and writes no whitespace", () => {
    const value = {
      "\u{1F600}": { b: true, a: [1, 2.5, null] },
      "\u{FB00}": "\u{FC}",
      "\u{E9}": 1,
      z: "\n",
      a: [],
    };
    expect(canonicalJson(value)).toBe(
      '{"a":[],"z":"\\n","\u{E9}":1,"\u{FB00}":"\u{FC}","\u{1F600}":{"a":[1,2.5,null],"b":true}}',
    );
  });

  it("equals Python's text for every break and jump of every 0.2.1 fixture", () => {
    const script = [
      "import json, pathlib, sys",
      "texts = []",
      "def visit(timeline):",
      "    flow = timeline['flow_control']",
      "    for entry in flow['breaks'] + flow['jumps']:",
      "        texts.append(json.dumps(entry, sort_keys=True, separators=(',', ':'), ensure_ascii=False))",
      "    for child in timeline['children'].values():",
      "        visit(child['timeline'])",
      "for path in sorted(pathlib.Path(sys.argv[1]).glob('*.json')):",
      "    for timeline in json.loads(path.read_text(encoding='utf-8'))['manifest']['timelines'].values():",
      "        visit(timeline)",
      "sys.stdout.buffer.write(json.dumps(texts, ensure_ascii=False).encode('utf-8'))",
    ].join("\n");
    const python = spawnSync("python3", ["-I", "-c", script, resolve(fixtureDirectory("0.2.1"))], {
      encoding: "utf8",
    });
    expect(python.status, python.stderr).toBe(0);
    const expected = JSON.parse(python.stdout) as string[];

    const texts: string[] = [];
    const visit = (timeline: JsonObject): void => {
      const flow = timeline.flow_control as JsonObject;
      for (const entry of [...(flow.breaks as LosslessJson[]), ...(flow.jumps as LosslessJson[])]) {
        texts.push(canonicalJson(entry));
      }
      for (const child of Object.values(timeline.children as Record<string, JsonObject>)) {
        visit(child.timeline as JsonObject);
      }
    };
    for (const file of fixtureFileNames("0.2.1")) {
      const envelope = loadFixture(file.slice(0, -5), "0.2.1");
      const timelines = (envelope.manifest as JsonObject).timelines as JsonObject;
      for (const timeline of Object.values(timelines)) visit(timeline as JsonObject);
    }
    expect(texts.length).toBe(7);
    expect(texts).toEqual(expected);
  });
});

describe("the 0.2.1 to 0.3.0 step", () => {
  it("declares 0.3.0 and changes nothing else", () => {
    const before = migrationText("0.2.1-to-0.3.0", "before");
    expect(before.split('"schema_version": "0.2.1"').length).toBe(2);
    const expected = before.replace('"schema_version": "0.2.1"', '"schema_version": "0.3.0"');
    expect(migrationText("0.2.1-to-0.3.0", "after")).toBe(expected);
    expect(dumps(step(parseJson(before) as JsonObject))).toBe(expected);
  });

  it("refuses an invalid envelope at its path", () => {
    const envelope = loadFixture("flow_control", "0.2.1");
    const timelines = (envelope.manifest as JsonObject).timelines as JsonObject;
    const flow = (timelines["flow:quarters"] as JsonObject).flow_control as JsonObject;
    ((flow.breaks as JsonObject[])[0] as JsonObject).control_type = "pause";
    let caught: unknown;
    try {
      step(envelope);
    } catch (error) {
      caught = error;
    }
    expect(caught).toBeInstanceOf(MigrationError);
    const error = caught as MigrationError;
    expect(error.path).toEqual([
      "manifest",
      "timelines",
      "flow:quarters",
      "flow_control",
      "breaks",
      0,
      "control_type",
    ]);
    expect(error.detail.startsWith("no 0.3.0 shape: ")).toBe(true);
  });
});

describe("the 0.3.0 to 0.4.0 step and split", () => {
  it("preserves styles and filters timeline containers", () => {
    const before = migrationFixture("before", "0.3.0-to-0.4.0");
    const result = step(before);
    const timelines = (before.manifest as JsonObject).timelines as JsonObject;
    expect(result.timeline).toEqual(timelines.melody);
    expect(result.graphical).toEqual({
      styles: (before.graphical as JsonObject).styles,
      timelines: {
        melody: ((before.graphical as JsonObject).timelines as JsonObject).melody,
        phrase: ((before.graphical as JsonObject).timelines as JsonObject).phrase,
      },
    });
  });

  it.each(["styled", "empty"])("asks for split when migrating %s", (name) => {
    const error = refusal(loadFixture(name, "0.3.0"));
    expect(error.path).toEqual(["manifest", "timelines"]);
    expect(error.detail).toContain("split");
  });

  it("reproduces every split output byte for byte", () => {
    const fixture = splitFixture();
    expect(split(parseJson(fixture.before)).map(dumps)).toEqual(
      fixture.after.map(([, content]) => content),
    );
  });

  it("reproduces all 0.4.0 manifests after split and migrate", () => {
    const expected = new Map(
      fixtureFileNames("0.4.0").map((file) => {
        const value = loadFixture(file.slice(0, -5), "0.4.0");
        return [(value.timeline as JsonObject).id as string, value] as const;
      }),
    );
    const names: string[] = [];
    for (const file of fixtureFileNames("0.3.0")) {
      for (const envelope of split(loadFixture(file.slice(0, -5), "0.3.0"))) {
        const result = migrate(envelope) as unknown as JsonObject;
        const rootId = (result.timeline as JsonObject).id as string;
        const wanted = expected.get(rootId) as JsonObject;
        expect(result.timeline).toEqual(wanted.timeline);
        expect(result.graphical).toEqual(wanted.graphical);
        names.push(rootId);
      }
    }
    expect(names.sort()).toEqual([...expected.keys()].sort());
  });

  it("refuses a timeline that is no object at the timeline", () => {
    const error = refusal({
      meta: { schema_version: "0.3.0" },
      manifest: { timelines: { a: 5 } },
      graphical: { timelines: { a: [] } },
    });
    expect(error).toBeInstanceOf(MigrationError);
    expect(error.path).toEqual(["timeline"]);
  });

  it("writes the canonical order", () => {
    const envelope = loadFixture("nested", "0.3.0");
    const [timeline] = Object.values((envelope.manifest as JsonObject).timelines as JsonObject);
    const children = (timeline as JsonObject).children as Record<string, JsonObject>;
    const [childId] = Object.keys(children) as [string];
    const earlier = clone(children[childId]) as JsonObject;
    ((earlier.offset as JsonObject).value as unknown[]) = [1, 1];
    (earlier.timeline as JsonObject).id = "tl:early";
    children["tl:early"] = earlier;
    expect(Object.keys(children)).toEqual([childId, "tl:early"]);
    const result = migrate(envelope) as unknown as JsonObject;
    expect(Object.keys((result.timeline as JsonObject).children as JsonObject)).toEqual([
      "tl:early",
      childId,
    ]);
  });

  it.each([
    ["0.1.0", 8],
    ["0.2.0", 29],
    ["0.2.1", 29],
    ["0.3.0", 34],
  ] as const)("divides every %s envelope fixture into %i envelopes", (version, count) => {
    expect(ENVELOPE_VERSIONS).toContain(version);
    let total = 0;
    for (const file of fixtureFileNames(version)) {
      for (const part of split(loadFixture(file.slice(0, -5), version))) {
        expect(declaredVersion(part)).toBe("0.3.0");
        validate(part);
        total += 1;
      }
    }
    expect(total).toBe(count);
  });

  it("names the published envelope versions", () => {
    expect(ENVELOPE_VERSIONS).toEqual(["0.1.0", "0.2.0", "0.2.1", "0.3.0"]);
  });

  it("returns no envelopes for the empty fixture", () => {
    expect(split(loadFixture("empty", "0.3.0"))).toEqual([]);
  });

  it("refuses a 0.4.0 manifest at meta.schema_version", () => {
    try {
      split(loadFixture("bare", "0.4.0"));
    } catch (error) {
      expect(error).toBeInstanceOf(MigrationError);
      expect((error as MigrationError).path).toEqual(["meta", "schema_version"]);
      return;
    }
    throw new Error("manifest was split");
  });
});
