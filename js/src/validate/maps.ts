/** Conversion-map rules: the source units and the members of a map that must agree. */

import { isJsonObject, type JsonObject } from "../json/value.js";
import { compareCodePoints, spell } from "../json/write.js";
import { compareExact } from "../numbers/exact.js";
import { entries, type PathSegment, SchemaValidationError, text } from "./diagnostics.js";

/** The conversion map types that read a measure map. */
export const MEASURE_VIEWS: ReadonlySet<string> = new Set([
  "MeasureRecordMap",
  "MeasureNumberMap",
  "FloatingMeasureMap",
  "MeasureBeatMap",
]);

/** What a map converts from: the unit its source unit must be and who demands it. */
type Reader = readonly [unit: string, owner: string] | null;

function* held(
  map: JsonObject,
  path: PathSegment[],
  reader: Reader,
): Generator<[JsonObject, PathSegment[], Reader]> {
  yield [map, path, reader];
  const source = map.source_unit;
  const holder: Reader =
    typeof source === "string"
      ? [source, `its ${text(map, "type")} ${JSON.stringify(text(map, "id"))}`]
      : null;
  const { maps } = map;
  if (Array.isArray(maps)) {
    const chain = map.type === "ChainMap";
    for (const [index, entry] of (maps as JsonObject[]).entries()) {
      const first = !chain || index === 0;
      yield* held(entry, [...path, "maps", index], first ? holder : null);
    }
  } else if (isJsonObject(maps)) {
    for (const name of Object.keys(maps).sort(compareCodePoints)) {
      yield* held(maps[name] as JsonObject, [...path, "maps", name], holder);
    }
  }
}

function* timelineHeld(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<[JsonObject, PathSegment[], Reader]> {
  const reader: Reader = [
    text(timeline, "unit"),
    `its timeline ${JSON.stringify(text(timeline, "id"))}`,
  ];
  for (const [index, entry] of entries(timeline, "conversion_maps").entries()) {
    yield* held(entry, [...path, "conversion_maps", index], reader);
  }
}

/**
 * Yield a timeline's conversion maps with their paths, each before those it
 * holds. A `CombinationMap`'s outputs carry no order; they are visited by
 * name, in code-point order.
 */
export function* timelineMaps(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<[JsonObject, PathSegment[]]> {
  for (const [map, at] of timelineHeld(timeline, path)) yield [map, at];
}

function count(number: number, noun: string): string {
  return number === 1 ? `${number} ${noun}` : `${number} ${noun}s`;
}

function* increasing(
  map: JsonObject,
  key: string,
  noun: string,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const values = map[key] as unknown[];
  for (let index = 1; index < values.length; index += 1) {
    if (compareExact(values[index], values[index - 1]) <= 0) {
      yield new SchemaValidationError(
        "conversion_map",
        [...path, key, index],
        `${noun} ${spell(values[index])} of ${text(map, "type")} ${JSON.stringify(text(map, "id"))} does not exceed the one before it`,
      );
    }
  }
}

function* mapProblems(
  map: JsonObject,
  path: readonly PathSegment[],
  reader: Reader,
): Generator<SchemaValidationError> {
  const id = JSON.stringify(text(map, "id"));
  const source = map.source_unit;
  if (reader !== null && typeof source === "string" && source !== reader[0]) {
    yield new SchemaValidationError(
      "conversion_map",
      [...path, "source_unit"],
      `${text(map, "type")} ${id} has source unit ${JSON.stringify(source)}, ${reader[1]} has ${JSON.stringify(reader[0])}`,
    );
  }
  if (map.type === "TableMap") {
    const xValues = map.x_values as unknown[];
    const yValues = map.y_values as unknown[];
    if (xValues.length !== yValues.length) {
      yield new SchemaValidationError(
        "conversion_map",
        [...path, "y_values"],
        `TableMap ${id} has ${xValues.length} x values and ${yValues.length} y values`,
      );
    }
    yield* increasing(map, "x_values", "x value", path);
  } else if (map.type === "PiecewiseMap") {
    const breaks = map.breaks as unknown[];
    const maps = map.maps as unknown[];
    if (maps.length !== breaks.length - 1) {
      yield new SchemaValidationError(
        "conversion_map",
        [...path, "maps"],
        `PiecewiseMap ${id} has ${count(maps.length, "map")} for ${breaks.length} breaks; it needs ${count(breaks.length - 1, "map")}`,
      );
    }
    yield* increasing(map, "breaks", "break", path);
  }
}

/**
 * Yield the map rules a timeline tree breaks: source units, arrays that agree.
 * A map attached to a timeline converts from the timeline's unit; a map a
 * `PiecewiseMap` or `CombinationMap` holds, and a `ChainMap`'s first map,
 * from its holder's source unit. A null source unit on either side checks
 * nothing.
 */
export function* timelineMapProblems(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  for (const [map, at, reader] of timelineHeld(timeline, path)) {
    yield* mapProblems(map, at, reader);
  }
  for (const [index, child] of entries(timeline, "children").entries()) {
    yield* timelineMapProblems(child, [...path, "children", index]);
  }
}
