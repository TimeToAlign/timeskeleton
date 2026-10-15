import { describe, expect, it } from "vitest";
import {
  compactJson,
  complete,
  dumps,
  type Json,
  JsonFloat,
  type Lossless,
  minimal,
  validate,
} from "../src/index.js";
import { bundle, manifest, timeline } from "./fixtures.js";

type JsonObject = Record<string, unknown>;

const SMALLEST = {
  timeskeleton: "0.7.0",
  timelines: [{ id: "piece", unit: "quarters", length: [32, 1] }],
};
const EMPTY_FLOW = { breaks: [], jumps: [], markers: [] };
const root = (value: unknown) => ((value as JsonObject).timelines as JsonObject[])[0] as JsonObject;

describe("the complete and the minimal form", () => {
  it("completes the smallest file to the literal complete form", () => {
    expect(complete(SMALLEST)).toEqual({
      timeskeleton: "0.7.0",
      name: null,
      meta: {},
      groups: [],
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
          flow_control: EMPTY_FLOW,
          measure_map: null,
          metric_hierarchy: null,
        },
      ],
    });
    expect(minimal(complete(SMALLEST))).toEqual(SMALLEST);
  });

  it("gives every object exactly its defaults", () => {
    const shift = { type: "ShiftMap", id: "s", source_unit: null, target_unit: null, offset: 1 };
    const metric = {
      type: "MetricMap",
      id: "mm",
      source_unit: null,
      target_unit: null,
      starts: [],
      mcs: [],
      mns: [],
      lengths: [],
    };
    const value = complete(
      manifest(
        [
          timeline("score", "quarters", [8, 1], {
            regions: [{ id: "r", start: [0, 1], end: [1, 1] }],
            flow_control: {
              breaks: [{ id: "b", coordinate: [1, 1] }],
              jumps: [{ id: "j", from_coordinate: [1, 1], to_coordinate: [0, 1] }],
              markers: [{ id: "m", coordinate: [0, 1] }],
            },
            conversion_maps: [
              {
                type: "ChainMap",
                id: "chain",
                source_unit: null,
                target_unit: null,
                maps: [shift],
              },
              {
                type: "CombinationMap",
                id: "combo",
                source_unit: null,
                target_unit: null,
                maps: { x: { ...shift, id: "x" } },
                names: ["x"],
              },
              {
                type: "BeatInMeasureMap",
                id: "bim",
                source_unit: null,
                target_unit: null,
                meter_map: metric,
              },
            ],
          }),
        ],
        { groups: [{ id: "g", members: ["score"] }], graphical: {} },
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
    const flow = done.flow_control as Record<string, JsonObject[]>;
    expect(flow.breaks?.[0]).toEqual({
      id: "b",
      coordinate: [1, 1],
      control_type: "section_break",
      condition: "always",
      repeat_count: 1,
      label: null,
      name: null,
      meta: {},
    });
    expect(flow.jumps?.[0]).toEqual({
      id: "j",
      from_coordinate: [1, 1],
      to_coordinate: [0, 1],
      control_type: "repeat_end",
      condition: "first_n",
      repeat_count: 1,
      target: null,
      label: null,
      meta: {},
    });
    expect(flow.markers?.[0]).toEqual({ id: "m", coordinate: [0, 1], name: null });
    const [chain, combo, bim] = done.conversion_maps as [JsonObject, JsonObject, JsonObject];
    expect(chain.name).toBeNull();
    expect((chain.maps as JsonObject[])[0]?.name).toBeNull();
    expect(combo.name).toBeNull();
    expect(((combo.maps as JsonObject).x as JsonObject).name).toBeNull();
    expect(bim.name).toBeNull();
    expect((bim.meter_map as JsonObject).name).toBeNull();
    expect(value.groups).toEqual([{ id: "g", members: ["score"], name: null, meta: {} }]);
    expect(value.graphical).toEqual({ styles: {}, statements: [], order: {} });
    validate(value);
  });

  it.each([
    ["ticks", "int"],
    ["seconds", "float"],
    ["whole_note", "fraction"],
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
        flow_control: { breaks: [{ id: "b", coordinate: 1.5, repeat_count: 2 }], jumps: [] },
      }),
    ]);
    expect(minimal(value)).toEqual(
      manifest([
        timeline("score", "quarters", 8.5, {
          locked: true,
          number_type: "float",
          flow_control: { breaks: [{ id: "b", coordinate: 1.5, repeat_count: 2 }] },
        }),
      ]),
    );
  });

  it("takes a value of another type for no default", () => {
    const value = manifest([
      timeline("score", "quarters", [8, 1], {
        flow_control: { breaks: [{ id: "b", coordinate: [1, 1], repeat_count: new JsonFloat(1) }] },
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
          flow_control: { codas: [], breaks: [] },
        }),
      ],
      { extra: { meta: {} } },
    );
    expect(minimal(value)).toEqual(
      manifest(
        [timeline("score", "quarters", [8, 1], { lenght: 1, flow_control: { codas: [] } })],
        {
          extra: { meta: {} },
        },
      ),
    );
    expect(complete(value).extra).toEqual({ meta: {} });
    expect((root(complete(value)).flow_control as JsonObject).codas).toEqual([]);
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
        timeline("score", "quarters", [8, 1], {
          lenght: 1,
          flow_control: { codas: [], breaks: [] },
        }),
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
          flow_control: {
            jumps: [
              {
                id: "j",
                from_coordinate: [4, 1],
                to_coordinate: [0, 1],
                repeat_count: new JsonFloat(1),
              },
            ],
          },
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
