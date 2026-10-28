// Spec: knowledge/components/idea-board-page.md
import { assertEquals } from "@std/assert";
import { messageFor, parseIdeaForm } from "./form.ts";

const form = (fields: Record<string, string>) => {
  const data = new FormData();
  for (const [name, value] of Object.entries(fields)) data.set(name, value);
  return data;
};

Deno.test("tags are split, trimmed, lowercased and empties dropped", () => {
  assertEquals(parseIdeaForm(form({ title: "Dark mode", tags: " UI, ,a11y ,, Night-Shift " })), {
    title: "Dark mode",
    description: "",
    tags: ["ui", "a11y", "night-shift"],
  });
});

Deno.test("missing fields become empty strings, so validation reports them", () => {
  assertEquals(parseIdeaForm(new FormData()), { title: "", description: "", tags: [] });
});

Deno.test("an uploaded file is not text", () => {
  const data = new FormData();
  data.set("title", new File(["x"], "title.txt"));
  assertEquals(parseIdeaForm(data).title, "");
});

Deno.test("every reason code has a message", () => {
  const reasons = [
    "required",
    "too_short",
    "too_long",
    "not_string",
    "not_array",
    "too_many",
    "bad_tag",
    "duplicate",
    "unknown_field",
    "not_object",
    "malformed_json",
  ];
  for (const reason of reasons) assertEquals(messageFor(reason).startsWith("Unexpected"), false, reason);
  assertEquals(messageFor("nope"), "Unexpected error (nope).");
});
