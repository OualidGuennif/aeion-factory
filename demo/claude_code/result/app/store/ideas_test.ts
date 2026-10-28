// Spec: knowledge/components/idea-board-api.md
import { assertEquals, assertMatch } from "@std/assert";
import { withStore } from "../testing.ts";

const draft = (title: string, tags: string[] = []) => ({
  title,
  description: "",
  tags,
});

Deno.test("create then get returns the same idea", () =>
  withStore(async (ideas) => {
    const created = await ideas.create(draft("Dark mode", ["ui"]));
    assertMatch(created.id, /^[0-9A-HJKMNP-TV-Z]{26}$/);
    assertEquals(created.votes, 0);
    assertEquals(created.tags, ["ui"]);
    assertEquals(new Date(created.createdAt).toISOString(), created.createdAt);
    assertEquals(await ideas.get(created.id), created);
  }));

Deno.test("a missing id is null", () =>
  withStore(async (ideas) => {
    assertEquals(await ideas.get("01ARZ3NDEKTSV4RRFFQ69G5FAV"), null);
  }));

Deno.test("list is newest first, even within one millisecond", () =>
  withStore(async (ideas) => {
    const titles = ["one", "two", "three", "four", "five"];
    for (const title of titles) await ideas.create(draft(title));
    const listed = await ideas.list({ limit: 20 });
    assertEquals(listed.map((idea) => idea.title), [...titles].reverse());
  }));

Deno.test("list honours the limit", () =>
  withStore(async (ideas) => {
    for (let i = 0; i < 7; i++) await ideas.create(draft(`idea ${i}`));
    assertEquals((await ideas.list({ limit: 3 })).map((idea) => idea.title), [
      "idea 6",
      "idea 5",
      "idea 4",
    ]);
  }));
