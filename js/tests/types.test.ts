import { describe, expect, it } from "vitest";
import type { Timeline, TimeSkeleton } from "../src/index.js";

// The compiler is the test here: each `@ts-expect-error` line must fail to
// type-check, so a looser generation of the types breaks the typecheck gate.

describe("the generated types", () => {
  it("take only declared keys, with length required and nullable", () => {
    const free: TimeSkeleton = {
      timeskeleton: "0.7.0",
      meta: { anything: { goes: true } },
      timelines: [{ id: "piece", unit: "quarters", length: null, meta: { x: 1 } }],
    };
    const child: Timeline = {
      id: "score",
      unit: "quarters",
      length: [8, 1],
      children: [{ id: "perf", unit: "seconds", length: 2.5, offset: [1, 1] }],
    };
    // @ts-expect-error a misspelt key is no Timeline key
    const misspelt: Timeline = { id: "a", unit: "quarters", length: null, lenght: 1 };
    // @ts-expect-error a timeline states its length
    const unsized: Timeline = { id: "a", unit: "quarters" };
    const parent: Timeline = {
      id: "a",
      unit: "quarters",
      length: null,
      // @ts-expect-error a child carries its offset
      children: [{ id: "b", unit: "quarters", length: null }],
    };
    expect([free, child, misspelt, unsized, parent].length).toBe(5);
  });
});
