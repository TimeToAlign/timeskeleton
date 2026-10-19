import type { NumberType, TimeUnit } from "../generated/types.js";
import type { JsonObject } from "../json/value.js";
import { compareCodePoints, spell } from "../json/write.js";
import { compareExact, exact, type Rational, rational } from "../numbers/exact.js";
import {
  entries,
  lengthOf,
  numberTypeOf,
  type PathSegment,
  SchemaValidationError,
  text,
} from "./diagnostics.js";
import { rewritten } from "./representation.js";

/** The indices of children in offset order, ties by id in code-point order. */
export function offsetOrder(children: readonly JsonObject[]): number[] {
  return [...children.keys()].sort(
    (a, b) =>
      compareExact(children[a]?.offset, children[b]?.offset) ||
      compareCodePoints(
        text(children[a] as JsonObject, "id"),
        text(children[b] as JsonObject, "id"),
      ),
  );
}

/** The exact sum of two rationals. */
export function add(left: Rational, right: Rational): Rational {
  return rational(
    left.numerator * right.denominator + right.numerator * left.denominator,
    left.denominator * right.denominator,
  );
}

/** Where each child ends, with an unknown segment ending at its successor. */
export function childEnds(timeline: JsonObject): (Rational | null)[] {
  const children = entries(timeline, "children");
  const ends = children.map((child) => {
    const length = lengthOf(child);
    return length !== null && child.unit === timeline.unit
      ? add(exact(child.offset), exact(length))
      : null;
  });
  if (timeline.is_segment_line === true) {
    const order = offsetOrder(children);
    for (const [position, index] of order.entries()) {
      const successor = order[position + 1];
      if (successor !== undefined && lengthOf(children[index] as JsonObject) === null) {
        ends[index] = exact(children[successor]?.offset);
      }
    }
  }
  return ends;
}

function exceeds(left: Rational, right: Rational): boolean {
  return left.numerator * right.denominator > right.numerator * left.denominator;
}

/** Yield children that do not sit on their parent's axis or within its known end. */
export function* timelineContainmentProblems(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const length = lengthOf(timeline);
  const ends = childEnds(timeline);
  for (const [index, child] of entries(timeline, "children").entries()) {
    const at = [...path, "children", index];
    const offset = exact(child.offset);
    const id = text(child, "id");
    const parent = `its parent '${text(timeline, "id")}'`;
    if (child.unit !== timeline.unit) {
      yield new SchemaValidationError(
        "child_unit",
        [...at, "unit"],
        `child '${id}' has unit '${text(child, "unit")}', ${parent} has '${text(timeline, "unit")}'`,
      );
    }
    const end = ends[index] ?? null;
    if (length !== null && exceeds(offset, exact(length))) {
      yield new SchemaValidationError(
        "child_offset",
        [...at, "offset"],
        `offset ${spell(child.offset)} of '${id}' is beyond the length ${spell(length)} of ${parent}`,
      );
    } else if (length !== null && end !== null && exceeds(end, exact(length))) {
      const pair = [end.numerator, end.denominator];
      const spelled =
        rewritten(pair, numberTypeOf(timeline as { unit: TimeUnit; number_type?: NumberType })) ??
        spell(pair);
      yield new SchemaValidationError(
        "child_end",
        [...at, "length"],
        `child '${id}' ends at ${spelled}, beyond the length ${spell(length)} of ${parent}`,
      );
    }
    yield* timelineContainmentProblems(child, at);
  }
}
