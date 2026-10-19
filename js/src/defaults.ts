/**
 * The defaults of a TimeSkeleton manifest: the complete and the minimal form.
 *
 * Every key with a default may be left out of a manifest, and a reader
 * supplies the default. The complete form writes every such key, its default
 * included; the minimal form leaves out exactly the keys whose value is the
 * default. Either form reads to the same manifest, and each converts to the
 * other. A key whose default is "absent" (a manifest's `id` and `graphical`,
 * a root's `offset`) is never added and never removed. Unknown keys pass
 * through untouched.
 */

import type {
  CompleteTimeSkeleton,
  LosslessTimeSkeleton,
  NumberType,
  TimeUnit,
} from "./generated/types.js";
import { clone, isJsonObject, JsonFloat, type JsonObject } from "./json/value.js";
import { respell } from "./manifest/spelling.js";
import { exactNumber } from "./numbers/exact.js";
import { numberTypeOf } from "./validate/diagnostics.js";

/**
 * The default of every key that has one, by the kind of object holding it.
 * A timeline's `number_type` defaults to its unit's default number type,
 * which `numberTypeOf` gives. Python's `timeskeleton.defaults` holds the same
 * table, and the schema declares each value as the key's `default`.
 */
export const DEFAULTS = {
  manifest: { name: null, meta: {}, groups: [] },
  timeline: {
    name: null,
    locked: false,
    is_segment_line: false,
    meta: {},
    children: [],
    conversion_maps: [],
    regions: [],
    flow_control: { breaks: [], jumps: [], markers: [] },
    measure_map: null,
    metric_hierarchy: null,
  },
  flow_control: { breaks: [], jumps: [], markers: [] },
  region: { name: null, meta: {} },
  break: {
    control_type: "section_break",
    condition: "always",
    repeat_count: 1,
    label: null,
    name: null,
    meta: {},
  },
  jump: {
    control_type: "repeat_end",
    condition: "first_n",
    repeat_count: 1,
    target: null,
    label: null,
    meta: {},
  },
  marker: { name: null },
  conversion_map: { name: null },
  group: { name: null, meta: {} },
  graphical: { styles: {}, statements: [], order: {} },
} as const;

type Kind = keyof typeof DEFAULTS;

/** A pass over one object of a manifest: complete it, or strip its defaults. */
type Pass = (owner: JsonObject, kind: Kind) => void;

function objects(owner: JsonObject, key: string): JsonObject[] {
  const value = owner[key];
  return Array.isArray(value) ? value.filter(isJsonObject) : [];
}

/** Apply a pass to a conversion map and to the maps it holds. */
function visitMap(map: JsonObject, pass: Pass): void {
  pass(map, "conversion_map");
  const maps = map.maps;
  const nested = Array.isArray(maps) ? maps : isJsonObject(maps) ? Object.values(maps) : [];
  for (const entry of nested) if (isJsonObject(entry)) visitMap(entry, pass);
  if (isJsonObject(map.meter_map)) visitMap(map.meter_map, pass);
}

/** Apply a pass to a timeline and to everything it holds. */
function visitTimeline(timeline: JsonObject, pass: Pass): void {
  pass(timeline, "timeline");
  for (const child of objects(timeline, "children")) visitTimeline(child, pass);
  for (const map of objects(timeline, "conversion_maps")) visitMap(map, pass);
  for (const region of objects(timeline, "regions")) pass(region, "region");
  const flow = timeline.flow_control;
  if (isJsonObject(flow)) {
    pass(flow, "flow_control");
    for (const entry of objects(flow, "breaks")) pass(entry, "break");
    for (const entry of objects(flow, "jumps")) pass(entry, "jump");
    for (const entry of objects(flow, "markers")) pass(entry, "marker");
  }
}

/** Apply a pass to every object of a manifest that has defaults, outermost first. */
function visitManifest(manifest: unknown, pass: Pass): void {
  if (!isJsonObject(manifest)) return;
  pass(manifest, "manifest");
  for (const timeline of objects(manifest, "timelines")) visitTimeline(timeline, pass);
  for (const group of objects(manifest, "groups")) pass(group, "group");
  if (isJsonObject(manifest.graphical)) pass(manifest.graphical, "graphical");
}

const UNITS = new Set<string>([
  "number",
  "floating_measures",
  "whole_note",
  "quarters",
  "ticks",
  "milliseconds",
  "seconds",
  "minutes",
  "samples",
  "frames",
  "pixels",
  "meters",
  "centimeters",
  "millimeters",
  "inches",
  "points",
]);

/** The default number type of a timeline, or `undefined` where its unit is none. */
function defaultNumberType(timeline: JsonObject): NumberType | undefined {
  return typeof timeline.unit === "string" && UNITS.has(timeline.unit)
    ? numberTypeOf({ unit: timeline.unit as TimeUnit })
    : undefined;
}

const completeOne: Pass = (owner, kind) => {
  for (const [key, value] of Object.entries(DEFAULTS[kind])) {
    if (!Object.hasOwn(owner, key)) owner[key] = clone(value as unknown);
  }
  if (kind === "timeline" && !Object.hasOwn(owner, "number_type")) {
    const numberType = defaultNumberType(owner);
    if (numberType !== undefined) owner.number_type = numberType;
  }
};

/** Whether a JSON number is written as an integer: a `bigint` or an integral plain number. */
function integral(value: unknown): boolean {
  return typeof value === "bigint" || (typeof value === "number" && Number.isInteger(value));
}

/**
 * Whether two JSON values are identical: numbers in type and value (a
 * `JsonFloat` 1 is not the integer 1), booleans only to booleans.
 */
function same(left: unknown, right: unknown): boolean {
  const a = exactNumber(left);
  const b = exactNumber(right);
  if (a !== null || b !== null) {
    return (
      a !== null &&
      b !== null &&
      integral(left) === integral(right) &&
      a.numerator === b.numerator &&
      a.denominator === b.denominator
    );
  }
  if (Array.isArray(left) || Array.isArray(right)) {
    return (
      Array.isArray(left) &&
      Array.isArray(right) &&
      left.length === right.length &&
      left.every((item, index) => same(item, right[index]))
    );
  }
  if (isJsonObject(left) || isJsonObject(right)) {
    if (!isJsonObject(left) || !isJsonObject(right)) return false;
    const keys = Object.keys(left);
    return (
      keys.length === Object.keys(right).length &&
      keys.every((key) => Object.hasOwn(right, key) && same(left[key], right[key]))
    );
  }
  return left === right && !(left instanceof JsonFloat);
}

const stripOne: Pass = (owner, kind) => {
  for (const [key, value] of Object.entries(DEFAULTS[kind])) {
    if (Object.hasOwn(owner, key) && same(owner[key], value)) delete owner[key];
  }
  if (kind === "timeline" && Object.hasOwn(owner, "number_type")) {
    if (owner.number_type === defaultNumberType(owner)) delete owner.number_type;
  }
};

/**
 * Return a copy of a manifest in the complete form: every key with a default
 * that is absent is added with its default, at every depth (a timeline's
 * `number_type` is its unit's default). Keys whose default is "absent" are
 * never added, present keys keep their values, spelled as their number type
 * selects (as `canonicalOrder` spells them), and unknown keys pass through.
 * Any other value is copied, its manifest-shaped parts completed, so a
 * graphical block alone completes as `complete({ graphical }).graphical`.
 * Python's `timeskeleton.complete` gives the same value.
 */
export function complete(value: LosslessTimeSkeleton): CompleteTimeSkeleton;
export function complete<T>(value: T): T;
export function complete(value: unknown): unknown {
  const result = clone(value);
  respell(result);
  visitManifest(result, completeOne);
  return result;
}

/**
 * Return a copy of a manifest in the minimal form: the complete form without
 * every key whose value is its default in type and value (`repeat_count:
 * 1.0`, read by `parseJson` as a `JsonFloat`, is not the default `1` and
 * stays). A default
 * container (an empty `flow_control`) goes as a whole; a container holding
 * more keeps only those. `minimal(complete(x))` equals `minimal(x)` and
 * `complete(minimal(x))` equals `complete(x)`. Python's
 * `timeskeleton.minimal` gives the same value.
 */
export function minimal(value: LosslessTimeSkeleton): LosslessTimeSkeleton;
export function minimal<T>(value: T): T;
export function minimal(value: unknown): unknown {
  const result = complete(value);
  visitManifest(result, stripOne);
  return result;
}
