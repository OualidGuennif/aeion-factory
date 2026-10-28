// Spec: knowledge/components/idea-board-api.md
import { assertEquals } from "@std/assert";
import { withStore } from "../testing.ts";
import type { IdeaStore } from "./ideas.ts";

const add = (ideas: IdeaStore, title: string, tags: string[] = [], description = "") =>
  ideas.create({ title, description, tags });

const titles = async (ideas: IdeaStore, filters: Parameters<IdeaStore["list"]>[0]) =>
  (await ideas.list(filters)).map((idea) => idea.title);

Deno.test("create indexes every tag", () =>
  withStore(async (ideas, kv) => {
    const { id } = await add(ideas, "Tagged", ["ui", "sync"]);
    const indexed = await Array.fromAsync(kv.list({ prefix: ["ideas_by_tag"] }));
    assertEquals(indexed.map((entry) => entry.value).sort(), [id, id]);
    assertEquals((await kv.get(["ideas_by_tag", "ui", id])).value, id);
    assertEquals((await kv.get(["ideas_by_tag", "sync", id])).value, id);
  }));

Deno.test("a tag filter is exact", () =>
  withStore(async (ideas) => {
    const tagsByTitle: Record<string, string[]> = {
      One: ["ui"],
      Two: ["ux"],
      Three: ["ui", "ux"],
      Four: ["sync"],
      Five: ["ui", "sync"],
      Six: [],
    };
    for (const [title, tags] of Object.entries(tagsByTitle)) await add(ideas, title, tags);
    for (const tag of ["ui", "ux", "sync"]) {
      const expected = Object.entries(tagsByTitle).filter(([, tags]) => tags.includes(tag)).map(([title]) => title);
      assertEquals((await titles(ideas, { limit: 50, tag })).sort(), expected.sort(), tag);
    }
  }));

Deno.test("q matches the title or the description, ignoring case", () =>
  withStore(async (ideas) => {
    await add(ideas, "Dark mode");
    await add(ideas, "Night shift", [], "A DARK theme for late work");
    await add(ideas, "Offline mode");
    assertEquals(await titles(ideas, { limit: 50, q: "dark" }), ["Night shift", "Dark mode"]);
  }));

Deno.test("regex characters are literal", () =>
  withStore(async (ideas) => {
    await add(ideas, "Match all with .* here");
    await add(ideas, "Plain words");
    assertEquals(await titles(ideas, { limit: 50, q: ".*" }), ["Match all with .* here"]);
    assertEquals(await titles(ideas, { limit: 50, q: "(" }), []);
  }));

Deno.test("tag and q combine with AND and keep each sort", () =>
  withStore(async (ideas) => {
    const older = await add(ideas, "Dark mode", ["ui"]);
    await add(ideas, "Dark terminal", ["cli"]);
    await add(ideas, "Darker buttons", ["ui"]);
    await add(ideas, "Light mode", ["ui"]);
    await ideas.vote(older.id);
    assertEquals(await titles(ideas, { limit: 50, tag: "ui", q: "dark" }), ["Darker buttons", "Dark mode"]);
    assertEquals(await titles(ideas, { limit: 50, tag: "ui", q: "dark", sort: "votes" }), [
      "Dark mode",
      "Darker buttons",
    ]);
  }));

Deno.test("a filtered list still honours the limit", () =>
  withStore(async (ideas) => {
    for (let i = 0; i < 5; i++) await add(ideas, `Idea ${i}`, ["ui"]);
    assertEquals(await titles(ideas, { limit: 2, tag: "ui" }), ["Idea 4", "Idea 3"]);
  }));

Deno.test("search stops at the 500 newest", () =>
  withStore(async (ideas) => {
    await add(ideas, "The needle is oldest");
    for (let i = 0; i < 500; i++) await add(ideas, `Hay ${i}`);
    assertEquals(await titles(ideas, { limit: 50, q: "needle" }), []);
    await add(ideas, "A newer needle");
    assertEquals(await titles(ideas, { limit: 50, q: "needle" }), ["A newer needle"]);
  }));
