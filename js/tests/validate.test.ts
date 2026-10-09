import { describe, expect, it } from "vitest";
import { jsonPointer, type PathSegment, SchemaValidationError, validate } from "../src/index.js";
import { FIXTURE_NAMES, loadFixture } from "./fixtures.js";

type Document = Record<string, unknown>;
type Mutation = (document: Document) => PathSegment[];

/** Return the path prefix and manifest of the first top-level timeline. */
function firstTimeline(document: Document): [PathSegment[], Document] {
  const manifest = document.manifest as Document;
  const timelines = manifest.timelines as Record<string, Document>;
  const timelineId = Object.keys(timelines)[0] as string;
  return [["manifest", "timelines", timelineId], timelines[timelineId] as Document];
}

function length(document: Document): [PathSegment[], Document] {
  const [prefix, timeline] = firstTimeline(document);
  return [[...prefix, "length"], timeline.length as Document];
}

const REJECTIONS: Record<string, Mutation> = {
  "unknown root key": (document) => {
    document.extra = 1;
    return [];
  },
  "missing required key": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    delete timeline.locked;
    return prefix;
  },
  "class outside the enum": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    timeline.class = "Timeline";
    return [...prefix, "class"];
  },
  "unit outside the enum": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    timeline.unit = "beats";
    return [...prefix, "unit"];
  },
  "fraction coordinate with a bare integer": (document) => {
    const [prefix, coordinate] = length(document);
    coordinate.value = 12;
    return [...prefix, "value"];
  },
  "zero denominator": (document) => {
    const [prefix, coordinate] = length(document);
    coordinate.value = [12, 0];
    return [...prefix, "value", 1];
  },
  "negative length": (document) => {
    const [prefix, coordinate] = length(document);
    coordinate.value = [-12, 1];
    return [...prefix, "value", 0];
  },
  "three-element fraction": (document) => {
    const [prefix, coordinate] = length(document);
    coordinate.value = [1, 2, 3];
    return [...prefix, "value"];
  },
  "string fraction": (document) => {
    const [prefix, coordinate] = length(document);
    coordinate.value = "12/1";
    return [...prefix, "value"];
  },
  "coordinate without unit": (document) => {
    const [prefix, coordinate] = length(document);
    delete coordinate.unit;
    return prefix;
  },
  "int number type with a fraction value": (document) => {
    const [prefix, coordinate] = length(document);
    coordinate.number_type = "int";
    return [...prefix, "value"];
  },
  "schema_version 0.2.0": (document) => {
    (document.meta as Document).schema_version = "0.2.0";
    return ["meta", "schema_version"];
  },
};

function rejection(document: unknown): SchemaValidationError {
  try {
    validate(document);
  } catch (error) {
    if (error instanceof SchemaValidationError) {
      return error;
    }
    throw error;
  }
  throw new Error("document was accepted");
}

describe("validate accepts", () => {
  it.each(FIXTURE_NAMES)("fixture %s", (name) => {
    const document: unknown = loadFixture(name);
    validate(document);
    expect(typeof document.manifest.timelines).toBe("object");
  });
});

describe("validate rejects", () => {
  it.each(Object.entries(REJECTIONS))("%s at its path", (_name, mutate) => {
    const document = loadFixture("continuous_logical");
    const expected = mutate(document);
    expect(rejection(document).path).toEqual(expected);
  });

  it("renders the path as a JSON pointer in the message", () => {
    const document = loadFixture("continuous_logical");
    const expected = (REJECTIONS["class outside the enum"] as Mutation)(document);
    const error = rejection(document);
    const prefix = `${jsonPointer(expected)}: `;
    expect(error.message.startsWith(prefix)).toBe(true);
    expect(error.message.length).toBeGreaterThan(prefix.length);
    expect(error.name).toBe("SchemaValidationError");
  });
});

describe("jsonPointer", () => {
  it("renders the root, nested keys with escapes, and indices", () => {
    expect(jsonPointer([])).toBe("#");
    expect(jsonPointer(["manifest", "timelines", "tl:1", "class"])).toBe(
      "#/manifest/timelines/tl:1/class",
    );
    expect(jsonPointer(["a/b", "c~d", 0])).toBe("#/a~1b/c~0d/0");
  });
});
