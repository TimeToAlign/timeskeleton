import { describe, expect, it, vi } from "vitest";
import { completeStyles, type Graphical } from "../src/index.js";

describe("completeStyles", () => {
  it("completes each missing style once in code-point order", () => {
    const graphical: Graphical = {
      statements: [
        { select: {}, set: "😀" },
        { select: {}, set: "ﬀ" },
        { select: {}, set: "😀" },
        { select: {}, set: { opacity: 0.5 } },
      ],
    };
    const original = structuredClone(graphical);
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);

    const result = completeStyles(graphical);

    expect(result).toEqual({
      graphical: {
        statements: original.statements,
        styles: { ﬀ: {}, "😀": {} },
      },
      missing: ["ﬀ", "😀"],
    });
    expect(graphical).toEqual(original);
    expect(result.graphical).not.toBe(graphical);
    expect(warn).toHaveBeenCalledTimes(1);
    expect(warn).toHaveBeenCalledWith("Missing graphical styles: 'ﬀ', '😀'");
    warn.mockRestore();
  });

  it("preserves existing declarations without console output", () => {
    const graphical: Graphical = {
      styles: { kept: { fill: "#ABCDEF" } },
      statements: [{ select: {}, set: "kept" }],
    };
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);

    const result = completeStyles(graphical);

    expect(result).toEqual({ graphical, missing: [] });
    expect(result.graphical).not.toBe(graphical);
    expect(result.graphical.styles).not.toBe(graphical.styles);
    expect(warn).not.toHaveBeenCalled();
    warn.mockRestore();
  });

  it("adds missing styles beside existing ones without changing the input", () => {
    const graphical: Graphical = {
      styles: { kept: { fill: "#000000" } },
      statements: [
        { select: {}, set: "kept" },
        { select: {}, set: "absent" },
      ],
    };
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);

    const result = completeStyles(graphical);

    expect(result.graphical.styles).toEqual({ kept: { fill: "#000000" }, absent: {} });
    expect(result.missing).toEqual(["absent"]);
    expect(graphical.styles).toEqual({ kept: { fill: "#000000" } });
    expect(warn).toHaveBeenCalledTimes(1);
    expect(warn).toHaveBeenCalledWith("Missing graphical styles: 'absent'");
    warn.mockRestore();
  });

  it("completes a style whose name is __proto__", () => {
    const graphical: Graphical = {
      statements: [{ select: {}, set: "__proto__" }],
    };
    const warn = vi.spyOn(console, "warn").mockImplementation(() => undefined);

    const result = completeStyles(graphical);
    warn.mockRestore();

    expect(result.missing).toEqual(["__proto__"]);
    expect(Object.hasOwn(result.graphical.styles ?? {}, "__proto__")).toBe(true);
    expect(
      Object.getOwnPropertyDescriptor(result.graphical.styles ?? {}, "__proto__")?.value,
    ).toEqual({});
    expect(graphical).toEqual({ statements: [{ select: {}, set: "__proto__" }] });
  });
});
