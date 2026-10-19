/**
 * The canonical order and the standard writer of a TimeSkeleton manifest.
 *
 * Every array of a manifest whose order carries no meaning has one canonical
 * order: `timelines` by id; in every timeline, `children` by offset, then id,
 * `conversion_maps` by id, `regions` by start, then end, then id, flow-control
 * `breaks` and `markers` by coordinate, then id, `jumps` by from coordinate,
 * then to coordinate, then id; `groups` by id and every group's `members` by
 * code point. Own-axis values compare by exact numeric value, strings by
 * Unicode code point. A `graphical.order` array is a display order and is
 * never re-ordered. Readers accept any order; `dumps` writes the canonical
 * one, every object's keys sorted by code point, two-space indentation and a
 * final newline, the same bytes as Python's `timeskeleton.dumps`.
 */

import { clone, isJsonObject, type JsonObject } from "../json/value.js";
import { compareCodePoints, emit } from "../json/write.js";
import { compareExact } from "../numbers/exact.js";

function text(member: unknown): string {
  if (typeof member !== "string") throw new TypeError(`not a string: ${String(member)}`);
  return member;
}

/** Order by the first comparison that does not tie. */
function by<T>(...comparisons: ((left: T, right: T) => number)[]) {
  return (left: T, right: T): number => {
    for (const compare of comparisons) {
      const result = compare(left, right);
      if (result !== 0) return result;
    }
    return 0;
  };
}

function member(entry: unknown, key: string): unknown {
  return isJsonObject(entry) ? entry[key] : undefined;
}

const byId = (a: unknown, b: unknown): number =>
  compareCodePoints(text(member(a, "id")), text(member(b, "id")));

const at =
  (key: string) =>
  (a: unknown, b: unknown): number =>
    compareExact(member(a, key), member(b, key));

/** Order the arrays of one timeline and of its descendants, in place. */
function orderTimeline(timeline: JsonObject): void {
  if (Array.isArray(timeline.children)) {
    for (const child of timeline.children) if (isJsonObject(child)) orderTimeline(child);
    timeline.children.sort(by(at("offset"), byId));
  }
  if (Array.isArray(timeline.conversion_maps)) timeline.conversion_maps.sort(byId);
  if (Array.isArray(timeline.regions)) timeline.regions.sort(by(at("start"), at("end"), byId));
  const flow = timeline.flow_control;
  if (!isJsonObject(flow)) return;
  if (Array.isArray(flow.breaks)) flow.breaks.sort(by(at("coordinate"), byId));
  if (Array.isArray(flow.jumps))
    flow.jumps.sort(by(at("from_coordinate"), at("to_coordinate"), byId));
  if (Array.isArray(flow.markers)) flow.markers.sort(by(at("coordinate"), byId));
}

/**
 * Return a deep copy of `value` with the arrays of its manifest ordered.
 *
 * A value with a top-level `timelines` array is a manifest: every timeline in
 * it is ordered at every depth and the array itself by id, and its `groups`
 * are ordered by id, each with its `members` by code point. Object keys are
 * left as they are (`dumps` sorts them), and any other JSON value is copied
 * unchanged. Python's `timeskeleton.canonical_order` gives the same order.
 *
 * @throws {TypeError} if a collection holds an entry whose ordering members are missing or of the wrong type.
 */
export function canonicalOrder<T>(value: T): T {
  const result = clone(value);
  const timelines = member(result, "timelines");
  if (!Array.isArray(timelines)) return result;
  for (const timeline of timelines) if (isJsonObject(timeline)) orderTimeline(timeline);
  timelines.sort(byId);
  const groups = member(result, "groups");
  if (Array.isArray(groups)) {
    for (const group of groups) {
      const members = member(group, "members");
      if (Array.isArray(members)) {
        members.sort((a: unknown, b: unknown) => compareCodePoints(text(a), text(b)));
      }
    }
    groups.sort(byId);
  }
  return result;
}

/**
 * Return the standard text of a TimeSkeleton manifest, or of any JSON value.
 *
 * The value is put in `canonicalOrder`, then written with the keys of every
 * object sorted by code point, two-space indentation and a final newline,
 * characters unescaped, every float spelled as Python's `repr` spells it (a
 * plain number with a fractional part, a `JsonFloat`) and every integer
 * without a decimal point (a plain integral number, a `bigint`). Python's
 * `timeskeleton.dumps` writes the same bytes.
 *
 * @throws {RangeError} for a non-finite number or a string with a lone surrogate.
 * @throws {TypeError} for a value that is not JSON, or a collection that cannot be put in canonical order.
 */
export function dumps(value: unknown): string {
  return `${emit(canonicalOrder(value), "  ", true, "")}\n`;
}
