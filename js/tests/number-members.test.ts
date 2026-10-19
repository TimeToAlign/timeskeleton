import { describe, expect, it } from "vitest";
import { MAP_NESTED_MEMBERS, MAP_NUMBER_MEMBERS } from "../src/manifest/spelling.js";
import { loadSchemaFile } from "./fixtures.js";

type Node = Record<string, unknown>;
type MemberTable = Readonly<
  Record<
    string,
    {
      readonly values?: readonly string[];
      readonly arrays?: readonly string[];
      readonly records?: readonly string[];
    }
  >
>;

const REFERENCE_PREFIX = "#/$defs/";

function object(value: unknown): Node | undefined {
  return typeof value === "object" && value !== null && !Array.isArray(value)
    ? (value as Node)
    : undefined;
}

function referenceName(value: unknown): string | undefined {
  const reference = object(value)?.$ref;
  return typeof reference === "string" && reference.startsWith(REFERENCE_PREFIX)
    ? reference.slice(REFERENCE_PREFIX.length)
    : undefined;
}

function recordedFacts(table: MemberTable): string[] {
  const facts: string[] = [];
  for (const [mapName, members] of Object.entries(table)) {
    for (const [kind, keys] of Object.entries(members)) {
      for (const key of keys) facts.push(`${mapName}.${kind}.${key}`);
    }
  }
  return facts.sort();
}

function schemaFacts(): { number: string[]; nested: string[] } {
  const definitions = object(loadSchemaFile().$defs) as Node;
  const branches = object(definitions.ConversionMap)?.oneOf as Node[];
  const mapNames = branches.map((branch) => referenceName(branch) as string);
  const numberDefinitions = new Set([
    "Number",
    ...Object.keys(definitions).filter((name) => name.startsWith("Fraction")),
  ]);
  const mapDefinitions = new Set(["ConversionMap", ...mapNames]);
  const number: string[] = [];
  const nested: string[] = [];

  for (const mapName of mapNames) {
    const properties = object(object(definitions[mapName])?.properties) as Node;
    for (const [key, memberValue] of Object.entries(properties)) {
      const member = object(memberValue) as Node;
      const directReference = referenceName(member);
      const branchReferences = ((member.anyOf ?? []) as unknown[]).map(referenceName);
      const itemReference = referenceName(member.items);
      const additionalReference = referenceName(member.additionalProperties);
      const branchHoldsNumber = branchReferences.some(
        (reference) => reference !== undefined && numberDefinitions.has(reference),
      );
      if (
        (directReference !== undefined && numberDefinitions.has(directReference)) ||
        branchHoldsNumber
      ) {
        number.push(`${mapName}.values.${key}`);
      }
      if (
        member.type === "array" &&
        itemReference !== undefined &&
        numberDefinitions.has(itemReference)
      ) {
        number.push(`${mapName}.arrays.${key}`);
      }
      if (directReference !== undefined && mapDefinitions.has(directReference)) {
        nested.push(`${mapName}.values.${key}`);
      }
      if (
        member.type === "array" &&
        itemReference !== undefined &&
        mapDefinitions.has(itemReference)
      ) {
        nested.push(`${mapName}.arrays.${key}`);
      }
      if (
        member.type === "object" &&
        additionalReference !== undefined &&
        mapDefinitions.has(additionalReference)
      ) {
        nested.push(`${mapName}.records.${key}`);
      }
    }
  }
  return { number: number.sort(), nested: nested.sort() };
}

function expectExact(
  label: string,
  expected: readonly string[],
  recorded: readonly string[],
): void {
  const difference = (left: readonly string[], right: readonly string[]): string[] => {
    const remaining = [...right];
    return left.filter((entry) => {
      const index = remaining.indexOf(entry);
      if (index === -1) return true;
      remaining.splice(index, 1);
      return false;
    });
  };
  const missing = difference(expected, recorded);
  const extra = difference(recorded, expected);
  expect(
    { missing, extra },
    `${label}: missing ${missing.join(", ") || "none"}; extra ${extra.join(", ") || "none"}`,
  ).toEqual({ missing: [], extra: [] });
}

describe("conversion-map respelling coverage", () => {
  it("matches number and nested-map members derived from the schema", () => {
    const facts = schemaFacts();
    expectExact("number members", facts.number, recordedFacts(MAP_NUMBER_MEMBERS));
    expectExact("nested-map members", facts.nested, recordedFacts(MAP_NESTED_MEMBERS));
  });
});
