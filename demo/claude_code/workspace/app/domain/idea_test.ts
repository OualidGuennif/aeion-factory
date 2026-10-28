// Spec: knowledge/components/idea-board-api.md
import { assertEquals } from "@std/assert";
import { validateNewIdea } from "./idea.ts";

function refusal(input: unknown) {
  const result = validateNewIdea(input);
  return result.ok ? "accepted" : `${result.field}:${result.reason}`;
}

Deno.test("a minimal idea is trimmed and gets defaults", () => {
  assertEquals(validateNewIdea({ title: "  Dark mode  " }), {
    ok: true,
    value: { title: "Dark mode", description: "", tags: [] },
  });
});

Deno.test("a full idea keeps its description and tags", () => {
  const result = validateNewIdea({
    title: "Dark mode",
    description: " Easier at night ",
    tags: ["ui", "a-11y"],
  });
  assertEquals(result, {
    ok: true,
    value: {
      title: "Dark mode",
      description: "Easier at night",
      tags: ["ui", "a-11y"],
    },
  });
});

Deno.test("the body must be an object", () => {
  assertEquals(refusal(null), "body:not_object");
  assertEquals(refusal([]), "body:not_object");
  assertEquals(refusal("title"), "body:not_object");
});

Deno.test("title: required, too_short, too_long", () => {
  assertEquals(refusal({}), "title:required");
  assertEquals(refusal({ title: 42 }), "title:required");
  assertEquals(refusal({ title: "   " }), "title:required");
  assertEquals(refusal({ title: " ab " }), "title:too_short");
  assertEquals(refusal({ title: "abc" }), "accepted");
  assertEquals(refusal({ title: "x".repeat(80) }), "accepted");
  assertEquals(refusal({ title: "x".repeat(81) }), "title:too_long");
});

Deno.test("description: not_string, too_long", () => {
  assertEquals(
    refusal({ title: "abc", description: 1 }),
    "description:not_string",
  );
  assertEquals(
    refusal({ title: "abc", description: "d".repeat(500) }),
    "accepted",
  );
  assertEquals(
    refusal({ title: "abc", description: "d".repeat(501) }),
    "description:too_long",
  );
});

Deno.test("tags: not_array, too_many, bad_tag, duplicate", () => {
  assertEquals(refusal({ title: "abc", tags: "ui" }), "tags:not_array");
  assertEquals(
    refusal({ title: "abc", tags: ["a", "b", "c", "d", "e"] }),
    "accepted",
  );
  assertEquals(
    refusal({ title: "abc", tags: ["a", "b", "c", "d", "e", "f"] }),
    "tags:too_many",
  );
  assertEquals(refusal({ title: "abc", tags: ["UI"] }), "tags:bad_tag");
  assertEquals(refusal({ title: "abc", tags: ["a b"] }), "tags:bad_tag");
  assertEquals(refusal({ title: "abc", tags: [""] }), "tags:bad_tag");
  assertEquals(
    refusal({ title: "abc", tags: ["x".repeat(21)] }),
    "tags:bad_tag",
  );
  assertEquals(refusal({ title: "abc", tags: [1] }), "tags:bad_tag");
  assertEquals(refusal({ title: "abc", tags: ["ui", "ui"] }), "tags:duplicate");
});

Deno.test("an unknown field is refused and named", () => {
  assertEquals(refusal({ title: "abc", votes: 99 }), "votes:unknown_field");
});

Deno.test("the first failing field wins, in the documented order", () => {
  assertEquals(
    refusal({ title: "x", description: 1, extra: true }),
    "title:too_short",
  );
  assertEquals(
    refusal({ title: "abc", description: 1, tags: "x" }),
    "description:not_string",
  );
});
