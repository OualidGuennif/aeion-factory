// Spec: knowledge/components/idea-board-api.md
import { assertEquals } from "@std/assert";
import { parseFilters } from "./filters.ts";

const parse = (query: string) => parseFilters(new URLSearchParams(query));

Deno.test("no filter is an empty filter", () => {
  assertEquals(parse(""), { ok: true, value: {} });
});

Deno.test("a valid tag and a trimmed q are kept", () => {
  assertEquals(parse("tag=ui&q=%20Dark%20"), { ok: true, value: { tag: "ui", q: "Dark" } });
});

Deno.test("a blank q reads as absent", () => {
  assertEquals(parse("q=%20%20"), { ok: true, value: {} });
});

Deno.test("a tag outside the pattern is refused", () => {
  assertEquals(parse("tag=Bad_Tag"), { ok: false, field: "tag", reason: "bad_tag" });
});

Deno.test("q over 50 characters is refused, 50 is accepted", () => {
  assertEquals(parse(`q=${"a".repeat(51)}`), { ok: false, field: "q", reason: "too_long" });
  assertEquals(parse(`q=${"a".repeat(50)}`).ok, true);
});
