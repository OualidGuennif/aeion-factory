// Spec: knowledge/components/idea-board-api.md
import { assertEquals } from "@std/assert";
import { withStore } from "../testing.ts";

const allKeys = async (kv: Deno.Kv) => (await Array.fromAsync(kv.list({ prefix: [] }))).map((entry) => entry.key);

Deno.test("one vote adds one", () =>
  withStore(async (ideas) => {
    const { id } = await ideas.create({ title: "Vote me", description: "", tags: [] });
    const result = await ideas.vote(id);
    assertEquals(result.status === "ok" && result.idea.votes, 1);
    assertEquals((await ideas.get(id))?.votes, 1);
  }));

Deno.test("an unknown id writes nothing", () =>
  withStore(async (ideas, kv) => {
    await ideas.create({ title: "Existing", description: "", tags: [] });
    const before = await allKeys(kv);
    assertEquals(await ideas.vote("01NOTANID0000000000000000"), { status: "not_found" });
    assertEquals(await allKeys(kv), before);
  }));

Deno.test("25 concurrent votes are all counted", () =>
  withStore(async (ideas) => {
    const { id } = await ideas.create({ title: "Popular", description: "", tags: [] });
    const results = await Promise.all(Array.from({ length: 25 }, () => ideas.vote(id)));
    assertEquals(results.filter((result) => result.status === "ok").length, 25);
    assertEquals((await ideas.get(id))?.votes, 25);
  }));

Deno.test("the index keeps one key per idea", () =>
  withStore(async (ideas, kv) => {
    const { id } = await ideas.create({ title: "Popular", description: "", tags: [] });
    await Promise.all(Array.from({ length: 25 }, () => ideas.vote(id)));
    const indexed = (await Array.fromAsync(kv.list({ prefix: ["ideas_by_votes"] }))).map((entry) => entry.key);
    assertEquals(indexed, [["ideas_by_votes", 25, id]]);
  }));

Deno.test("sort by votes puts most votes first and breaks ties by newest", () =>
  withStore(async (ideas) => {
    const first = await ideas.create({ title: "First", description: "", tags: [] });
    await ideas.create({ title: "Second", description: "", tags: [] });
    const third = await ideas.create({ title: "Third", description: "", tags: [] });
    for (const id of [first.id, first.id, third.id, third.id]) await ideas.vote(id);
    const titles = async (sort: "votes" | "recent") =>
      (await ideas.list({ limit: 10, sort })).map((idea) => idea.title);
    assertEquals(await titles("votes"), ["Third", "First", "Second"]);
    assertEquals(await titles("recent"), ["Third", "Second", "First"]);
  }));

Deno.test("sort by votes reads more ideas than one getMany batch", () =>
  withStore(async (ideas) => {
    for (let i = 0; i < 12; i++) await ideas.create({ title: `Idea ${i}`, description: "", tags: [] });
    assertEquals((await ideas.list({ limit: 12, sort: "votes" })).length, 12);
  }));
