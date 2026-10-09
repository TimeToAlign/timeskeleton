import { describe, expect, it } from "vitest";
import { jsonPointer, type PathSegment, SchemaValidationError, validate } from "../src/index.js";
import { FIXTURE_NAMES, loadFixture } from "./fixtures.js";

type Document = Record<string, unknown>;
type Mutation = (document: Document) => PathSegment[];

/** Return the path prefix and the manifest of the first top-level timeline. */
function firstTimeline(document: Document): [PathSegment[], Document] {
  const manifest = document.manifest as Document;
  const timelines = manifest.timelines as Record<string, Document>;
  const timelineId = Object.keys(timelines)[0] as string;
  return [["manifest", "timelines", timelineId], timelines[timelineId] as Document];
}

function rational(timeline: Document, member: "length"): Document {
  return timeline[member] as Document;
}

const REJECTIONS: Record<string, Mutation> = {
  "unknown root key": (document) => {
    document.extra = 1;
    return [];
  },
  "missing meta": (document) => {
    delete document.meta;
    return [];
  },
  "missing required key": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    delete timeline.locked;
    return prefix;
  },
  "name neither string nor null": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    timeline.name = 1;
    return [...prefix, "name"];
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
  "number_type outside the enum": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    timeline.number_type = "decimal";
    return [...prefix, "number_type"];
  },
  "float numerator": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    rational(timeline, "length").numerator = 1.5;
    return [...prefix, "length", "numerator"];
  },
  "one-sided ratio": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    rational(timeline, "length").denominator = null;
    return [...prefix, "length"];
  },
  "denominator 0": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    rational(timeline, "length").denominator = 0;
    return [...prefix, "length", "denominator"];
  },
  'string numerator "12a"': (document) => {
    const [prefix, timeline] = firstTimeline(document);
    rational(timeline, "length").numerator = "12a";
    return [...prefix, "length", "numerator"];
  },
  "child offset with float numerator": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    const children = timeline.children as Record<string, Document>;
    const childId = Object.keys(children)[0] as string;
    const offset = (children[childId] as Document).offset as Document;
    offset.numerator = 0.5;
    return [...prefix, "children", childId, "offset", "numerator"];
  },
  "region that is not an object": (document) => {
    const [prefix, timeline] = firstTimeline(document);
    timeline.regions = [1];
    return [...prefix, "regions", 0];
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
    // Narrowed by the assertion signature: no cast is needed below.
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

  it("types array indices as numbers", () => {
    const document = loadFixture("continuous_logical");
    (REJECTIONS["region that is not an object"] as Mutation)(document);
    expect(rejection(document).path.at(-1)).toBe(0);
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
