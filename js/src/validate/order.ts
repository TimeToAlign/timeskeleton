import { isJsonObject, type JsonObject } from "../json/value.js";
import { compareCodePoints } from "../json/write.js";
import { entries, type PathSegment, SchemaValidationError } from "./diagnostics.js";

function* permutationProblems(
  code: "display_order" | "band_order",
  order: readonly string[],
  expected: readonly string[],
  path: readonly PathSegment[],
  stranger: (entry: string) => string,
  missing: (item: string) => string,
): Generator<SchemaValidationError> {
  const wanted = new Set(expected);
  const listed = new Set(order);
  for (const [index, entry] of order.entries()) {
    if (!wanted.has(entry)) {
      yield new SchemaValidationError(code, [...path, index], stranger(entry));
    }
  }
  for (const item of expected) {
    if (!listed.has(item)) yield new SchemaValidationError(code, path, missing(item));
  }
}

function* displayOrderProblems(
  group: JsonObject,
  order: readonly string[],
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const id = JSON.stringify(group.id);
  yield* permutationProblems(
    "display_order",
    order,
    group.members as string[],
    path,
    (entry) => `${JSON.stringify(entry)} is not a member of group ${id}`,
    (member) => `member ${JSON.stringify(member)} of group ${id} is missing`,
  );
}

function defaultBandOrder(id: string): string[] {
  return [
    `${id}/children_1`,
    `${id}/conversion_maps_1`,
    id,
    `${id}/markers_1`,
    `${id}/regions_1`,
    `${id}/flow_control_1`,
  ];
}

function* bandOrderProblems(
  timeline: string,
  order: readonly string[],
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const id = JSON.stringify(timeline);
  yield* permutationProblems(
    "band_order",
    order,
    defaultBandOrder(timeline),
    path,
    (entry) => `${JSON.stringify(entry)} is not ${id} or one of its bands`,
    (address) => `${JSON.stringify(address)} is missing from the band order of ${id}`,
  );
}

/**
 * Yield unknown order keys, display-order problems and band-order problems.
 *
 * `timelines` and `firstGroup` are the first occurrence of each timeline id
 * and group id, as the identity rules collected them.
 */
export function* orderProblems(
  manifest: JsonObject,
  timelines: ReadonlyMap<string, readonly PathSegment[]>,
  firstGroup: ReadonlyMap<string, number>,
): Generator<SchemaValidationError> {
  const groups = entries(manifest, "groups");
  const graphical = isJsonObject(manifest.graphical) ? manifest.graphical : {};
  const orders = isJsonObject(graphical.order) ? (graphical.order as Record<string, string[]>) : {};
  for (const key of Object.keys(orders).sort(compareCodePoints)) {
    const path = ["graphical", "order", key];
    const order = orders[key] ?? [];
    const index = firstGroup.get(key);
    if (index !== undefined) {
      yield* displayOrderProblems(groups[index] as JsonObject, order, path);
    } else if (timelines.has(key)) {
      yield* bandOrderProblems(key, order, path);
    } else {
      yield new SchemaValidationError(
        "order_key",
        path,
        `${JSON.stringify(key)} names no group or timeline of this manifest`,
      );
    }
  }
}
