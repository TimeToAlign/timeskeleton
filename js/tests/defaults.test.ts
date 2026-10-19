import { describe, expect, it } from "vitest";
import { complete, minimal } from "../src/defaults.js";
import { canonicalManifest, completeManifest, minimalManifest } from "../src/forms.js";
import type {
  CompleteFlowControlElement,
  CompleteTimeline,
  CompleteTimeSkeleton,
  Fraction,
  LosslessTimeSkeleton,
} from "../src/generated/types.js";
import type { JsonObject } from "../src/json/value.js";
import { type Json, JsonFloat, type Lossless } from "../src/json/value.js";
import { compactJson } from "../src/json/write.js";
import { dumps } from "../src/manifest/order.js";
import { parse, validate } from "../src/validate.js";
import { bundle, fixtureFiles, fixtureText, manifest, timeline } from "./fixtures.js";

const SMALLEST = {
  timeskeleton: "0.7.0",
  timelines: [{ id: "piece", unit: "quarters", length: [32, 1] }],
};
const REGION = { id: "r", start: [0, 1], end: [1, 1] };
const REPEAT = { id: "b", type: "jump_from", manifestation: "repeat_end" };
const root = (value: unknown) => ((value as JsonObject).timelines as JsonObject[])[0] as JsonObject;

describe("the complete and the minimal form", () => {
  it("completes the smallest file to the literal complete form", () => {
    expect(complete(SMALLEST)).toEqual({
      timeskeleton: "0.7.0",
      name: null,
      meta: {},
      groups: [],
      measure_maps: [],
      timelines: [
        {
          id: "piece",
          unit: "quarters",
          length: [32, 1],
          name: null,
          number_type: "fraction",
          locked: false,
          is_segment_line: false,
          meta: {},
          children: [],
          conversion_maps: [],
          regions: [],
          flow_control: [],
        },
      ],
    });
    expect(minimal(complete(SMALLEST))).toEqual(SMALLEST);
  });

  it("gives every object exactly its defaults", () => {
    const linear = { type: "LinearMap", id: "s", source_unit: null, target_unit: null };
    const table = {
      type: "TableMap",
      id: "t",
      source_unit: "quarters",
      target_unit: "seconds",
      x_values: [
        [0, 1],
        [4, 1],
      ],
      y_values: [0.5, 2.5],
    };
    const view = {
      type: "MeasureNumberMap",
      id: "bar",
      source_unit: "quarters",
      target_unit: null,
      measure_map: "bars",
    };
    const rows = [{ count: 1, qstamp: [0, 1], actual_length: [4, 1] }];
    const value = complete(
      manifest(
        [
          timeline("score", "quarters", [8, 1], {
            regions: [{ id: "r", start: [0, 1], end: [1, 1] }],
            flow_control: [
              { id: "b", type: "flow_marker", manifestation: "fine", coordinate: [1, 1] },
              { id: "j", type: "jump_from", manifestation: "da_capo", coordinate: [1, 1] },
              { id: "again", type: "jump_from", manifestation: "repeat_end", coordinate: [1, 1] },
              { id: "m", type: "jump_to", manifestation: "segno", coordinate: [0, 1] },
            ],
            conversion_maps: [
              {
                type: "ChainMap",
                id: "chain",
                source_unit: null,
                target_unit: null,
                maps: [linear],
              },
              {
                type: "CombinationMap",
                id: "combo",
                source_unit: null,
                target_unit: null,
                maps: { x: { ...linear, id: "x" }, bar: view },
              },
              {
                type: "PiecewiseMap",
                id: "pieces",
                source_unit: "quarters",
                target_unit: "seconds",
                breaks: [
                  [0, 1],
                  [4, 1],
                ],
                maps: [table],
              },
            ],
          }),
        ],
        {
          groups: [{ id: "g", members: ["score"] }],
          measure_maps: [{ id: "bars", rows }],
          graphical: {},
        },
      ),
    );
    const done = root(value);
    expect((done.regions as JsonObject[])[0]).toEqual({
      id: "r",
      start: [0, 1],
      end: [1, 1],
      name: null,
      meta: {},
    });
    const defaults = { name: null, label: null, meta: {} };
    expect(done.flow_control).toEqual([
      { id: "b", type: "flow_marker", manifestation: "fine", coordinate: [1, 1], ...defaults },
      { id: "j", type: "jump_from", manifestation: "da_capo", coordinate: [1, 1], ...defaults },
      {
        id: "again",
        type: "jump_from",
        manifestation: "repeat_end",
        coordinate: [1, 1],
        ...defaults,
        repeat_count: 1,
      },
      { id: "m", type: "jump_to", manifestation: "segno", coordinate: [0, 1], ...defaults },
    ]);
    const [chain, combo, pieces] = done.conversion_maps as [JsonObject, JsonObject, JsonObject];
    expect(chain).toEqual({
      type: "ChainMap",
      id: "chain",
      source_unit: null,
      target_unit: null,
      name: null,
      maps: [{ ...linear, name: null, scalar: 1, offset: 0 }],
    });
    expect(combo.name).toBeNull();
    expect((combo.maps as JsonObject).x).toEqual({
      ...linear,
      id: "x",
      name: null,
      scalar: 1,
      offset: 0,
    });
    expect((combo.maps as JsonObject).bar).toEqual({ ...view, name: null });
    expect(pieces.name).toBeNull();
    expect(pieces.maps).toEqual([{ ...table, name: null, kind: "linear", extrapolate: "none" }]);
    expect(value.groups).toEqual([{ id: "g", members: ["score"], name: null, meta: {} }]);
    expect(value.measure_maps).toEqual([{ id: "bars", rows, name: null, meta: {} }]);
    expect(value.graphical).toEqual({ styles: {}, statements: [], order: {} });
    validate(value);
  });

  it.each([
    ["ticks", "int"],
    ["seconds", "float"],
    ["whole_notes", "fraction"],
    ["pixels", "int"],
  ])("takes the number type of %s from the unit: %s", (unit, numberType) => {
    const value = complete(manifest([timeline("t", unit, null)]));
    expect(root(value).number_type).toBe(numberType);
    expect(Object.hasOwn(root(minimal(value)), "number_type")).toBe(false);
  });

  it("never adds or removes a key whose default is absent", () => {
    const value = complete(SMALLEST) as JsonObject;
    expect(Object.hasOwn(value, "id")).toBe(false);
    expect(Object.hasOwn(value, "graphical")).toBe(false);
    expect(Object.hasOwn(root(value), "offset")).toBe(false);
    const styled = manifest([timeline("score")], { graphical: {} });
    expect(minimal(styled).graphical).toEqual({});
    expect(complete(styled).graphical).toEqual({ styles: {}, statements: [], order: {} });
    const child = manifest([
      timeline("score", "quarters", [8, 1], {
        children: [timeline("c", "quarters", [8, 1], { offset: [0, 1] })],
      }),
    ]);
    expect((root(minimal(child)).children as JsonObject[])[0]?.offset).toEqual([0, 1]);
  });

  it("keeps values other than the default", () => {
    const value = manifest([
      timeline("score", "quarters", 8.5, {
        locked: true,
        number_type: "float",
        flow_control: [{ ...REPEAT, coordinate: 1.5, repeat_count: 2, label: null }],
      }),
    ]);
    expect(minimal(value)).toEqual(
      manifest([
        timeline("score", "quarters", 8.5, {
          locked: true,
          number_type: "float",
          flow_control: [{ ...REPEAT, coordinate: 1.5, repeat_count: 2 }],
        }),
      ]),
    );
  });

  it("takes a value of another type for no default", () => {
    const value = manifest([
      timeline("score", "quarters", [8, 1], {
        flow_control: [{ ...REPEAT, coordinate: [1, 1], repeat_count: new JsonFloat(1) }],
        conversion_maps: [
          {
            type: "LinearMap",
            id: "l",
            source_unit: "quarters",
            target_unit: "seconds",
            scalar: [1, 1],
            offset: new JsonFloat(0),
          },
        ],
      }),
    ]);
    expect(dumps(minimal(value))).toBe(dumps(value));
    expect(dumps(complete(minimal(value)))).toBe(dumps(complete(value)));
  });

  it("passes unknown keys through", () => {
    const value = manifest(
      [
        timeline("score", "quarters", [8, 1], {
          lenght: 1,
          flow_control: [],
          regions: [{ ...REGION, codas: [] }],
        }),
      ],
      { extra: { meta: {} } },
    );
    expect(minimal(value)).toEqual(
      manifest(
        [
          timeline("score", "quarters", [8, 1], {
            lenght: 1,
            regions: [{ ...REGION, codas: [] }],
          }),
        ],
        { extra: { meta: {} } },
      ),
    );
    expect(complete(value).extra).toEqual({ meta: {} });
    expect((root(complete(value)).regions as JsonObject[])[0]?.codas).toEqual([]);
  });

  it("keeps the length in both forms", () => {
    for (const length of [null, [8, 1]]) {
      const value = manifest([timeline("score", "quarters", length)]);
      expect(root(complete(value)).length).toEqual(length);
      expect(root(minimal(value)).length).toEqual(length);
    }
  });

  it("hands out fresh objects, never the table's own", () => {
    const first = complete(SMALLEST) as JsonObject;
    const second = complete(SMALLEST) as JsonObject;
    expect(first.meta).not.toBe(second.meta);
    expect(root(first).flow_control).not.toBe(root(second).flow_control);
  });

  it.each([
    ["the smallest file", SMALLEST],
    ["its complete form", complete(SMALLEST)],
    ["the bundle document", bundle()],
    [
      "unknown keys",
      manifest([
        timeline("score", "quarters", [8, 1], { lenght: 1, regions: [{ ...REGION, codas: [] }] }),
      ]),
    ],
    [
      "a locked parent and a styled manifest",
      manifest(
        [
          timeline("score", "quarters", [8, 1], {
            locked: true,
            children: [timeline("c", "quarters", [8, 1], { offset: [0, 1] })],
          }),
        ],
        { graphical: {} },
      ),
    ],
    [
      "a float repeat count",
      manifest([
        timeline("score", "quarters", [8, 1], {
          flow_control: [{ ...REPEAT, coordinate: [4, 1], repeat_count: new JsonFloat(1) }],
        }),
      ]),
    ],
  ])("round-trips %s", (_name, value) => {
    const given = compactJson(value as Lossless<Json>);
    expect(dumps(minimal(complete(value)))).toBe(dumps(minimal(value)));
    expect(dumps(complete(minimal(value)))).toBe(dumps(complete(value)));
    expect(complete(value)).not.toBe(value);
    expect(minimal(value)).not.toBe(value);
    expect(compactJson(value as Lossless<Json>)).toBe(given);
    validate(complete(value));
    validate(minimal(value));
  });
});

describe("the typed forms", () => {
  const COMPLETE_ROOT: CompleteTimeline = {
    id: "piece",
    name: null,
    unit: "quarters",
    number_type: "fraction",
    length: [32, 1],
    locked: false,
    is_segment_line: false,
    meta: {},
    children: [],
    conversion_maps: [],
    regions: [],
    flow_control: [],
  };
  const COMPLETE: CompleteTimeSkeleton = {
    timeskeleton: "0.7.0",
    name: null,
    meta: {},
    groups: [],
    measure_maps: [],
    timelines: [COMPLETE_ROOT],
  };

  it("type every key with a default as present, and no other", () => {
    // The compiler is the test: each `@ts-expect-error` line must fail to type-check.
    const { number_type: _numberType, ...untyped } = COMPLETE_ROOT;
    // @ts-expect-error a complete timeline states its number type
    const unstated: CompleteTimeline = untyped;
    const { groups: _groups, ...ungrouped } = COMPLETE;
    // @ts-expect-error a complete manifest states its groups
    const groupless: CompleteTimeSkeleton = ungrouped;
    // @ts-expect-error a complete flow-control element states its label
    const uncounted: CompleteFlowControlElement = {
      id: "b",
      type: "flow_marker",
      manifestation: "fine",
      coordinate: 1,
      name: null,
      meta: {},
    };
    // A repeat count is no key of every element, so the complete form keeps it optional.
    const marker: CompleteFlowControlElement = { ...uncounted, label: null };
    // A key whose default is absent stays optional: the manifest's id and
    // graphical block, a root's offset.
    const named: CompleteTimeSkeleton = {
      ...COMPLETE,
      id: "op35",
      graphical: { styles: {}, statements: [], order: {} },
    };
    const placed: CompleteTimeline = { ...COMPLETE_ROOT, offset: [-1, 2] };
    // Numbers are lossless and a Fraction stays a pair.
    const exact: CompleteTimeline = { ...COMPLETE_ROOT, length: [new JsonFloat(32), 10n ** 20n] };
    const pair: Lossless<Fraction> = [1, new JsonFloat(2)];
    // @ts-expect-error a Fraction has two members
    const triple: Lossless<Fraction> = [1, 2, 3];
    // The complete form is a lossless manifest.
    const lossless: LosslessTimeSkeleton = COMPLETE;
    expect([
      unstated,
      groupless,
      uncounted,
      marker,
      named,
      placed,
      exact,
      pair,
      triple,
      lossless,
    ]).toHaveLength(10);
  });

  it("complete, strip and order the literal complete form", () => {
    const smallest = minimalManifest(COMPLETE);
    expect(smallest).toEqual({
      timeskeleton: "0.7.0",
      timelines: [{ id: "piece", unit: "quarters", length: [32, 1] }],
    });
    expect(completeManifest(smallest)).toEqual(COMPLETE);
    const ordered: CompleteTimeSkeleton = canonicalManifest(COMPLETE);
    expect(ordered).toEqual(COMPLETE);
    expect(ordered).not.toBe(COMPLETE);
  });

  const twins = fixtureFiles().filter((file) => file.endsWith(".minimal.json"));

  it("have a minimal twin for every fixture", () => {
    expect(twins.length).toBe(60);
    expect(twins.map((twin) => twin.replace(/\.minimal\.json$/, ".json"))).toEqual(
      fixtureFiles().filter((file) => !file.endsWith(".minimal.json")),
    );
  });

  it.each(twins)("complete %s to its fixture, and back", (twin) => {
    const fixture = fixtureText(twin.replace(/\.minimal\.json$/, ".json"));
    const completed = completeManifest(parse(fixtureText(twin)));
    expect(dumps(completed)).toBe(fixture);
    expect(dumps(canonicalManifest(completed))).toBe(fixture);
    expect(dumps(minimalManifest(completed))).toBe(fixtureText(twin));
  });
});
