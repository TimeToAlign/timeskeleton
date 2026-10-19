import type { JsonObject } from "../json/value.js";
import { exact, type Rational, rational } from "../numbers/exact.js";
import { add, offsetOrder } from "./containment.js";
import { entries, lengthOf, type PathSegment, SchemaValidationError } from "./diagnostics.js";

function equal(left: Rational, right: Rational): boolean {
  return left.numerator === right.numerator && left.denominator === right.denominator;
}

/** Yield segment-line violations for one timeline tree. */
export function* timelineSegmentProblems(
  timeline: JsonObject,
  path: readonly PathSegment[],
): Generator<SchemaValidationError> {
  const children = entries(timeline, "children");
  if (timeline.is_segment_line === true) {
    const order = offsetOrder(children);
    const id = JSON.stringify(timeline.id);
    let end: Rational | null = rational(0n, 1n);
    let flag: boolean | undefined;
    let firstId = "";
    for (const [position, index] of order.entries()) {
      const segment = children[index] as JsonObject;
      const at = [...path, "children", index];
      const name = JSON.stringify(segment.id);
      const segmentFlag = segment.is_segment_line === true;
      if (position === 0) {
        flag = segmentFlag;
        firstId = JSON.stringify(segment.id);
      } else if (segmentFlag !== flag) {
        yield new SchemaValidationError(
          "segment_line",
          Object.hasOwn(segment, "is_segment_line") ? [...at, "is_segment_line"] : at,
          `segment ${name} of segment line ${id} differs from segment ${firstId} in is_segment_line`,
        );
      }
      const offset = exact(segment.offset);
      if (end !== null && !equal(offset, end)) {
        yield new SchemaValidationError(
          "segment_line",
          [...at, "offset"],
          `segment ${name} of segment line ${id} does not ${position === 0 ? "start at 0" : "start where the one before it ends"}`,
        );
      }
      const length = lengthOf(segment);
      end = length === null ? null : add(offset, exact(length));
    }
    const length = lengthOf(timeline);
    if (end !== null && length !== null && !equal(end, exact(length))) {
      yield new SchemaValidationError(
        "segment_line",
        [...path, "length"],
        `the segments of segment line ${id} do not end at its length`,
      );
    }
  }
  for (const [index, child] of children.entries()) {
    yield* timelineSegmentProblems(child, [...path, "children", index]);
  }
}
