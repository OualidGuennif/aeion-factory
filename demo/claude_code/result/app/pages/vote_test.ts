// Spec: knowledge/components/idea-board-page.md
import { assertEquals, assertStringIncludes } from "@std/assert";
import { App } from "fresh";
import type { State } from "../utils.ts";
import { homeApp, withStore } from "../testing.ts";
import type { IdeaStore } from "../store/ideas.ts";
import { createVoteHandlers } from "./vote.ts";

const voteApp = (ideas: IdeaStore) =>
  new App<State>().route("/ideas/:id/vote", { handler: createVoteHandlers(() => Promise.resolve(ideas)) }).handler();

const vote = (id: string, fields: Record<string, string> = {}) =>
  new Request(`http://localhost/ideas/${id}/vote`, { method: "POST", body: new URLSearchParams(fields) });

Deno.test("a vote without JavaScript counts and returns to the sorted page", () =>
  withStore(async (ideas) => {
    const { id } = await ideas.create({ title: "Vote me", description: "", tags: [] });
    const response = await voteApp(ideas)(vote(id, { sort: "votes" }));
    assertEquals([response.status, response.headers.get("location")], [303, "/?sort=votes"]);
    assertEquals((await ideas.get(id))?.votes, 1);
  }));

Deno.test("an unknown sort returns to the plain page", () =>
  withStore(async (ideas) => {
    const { id } = await ideas.create({ title: "Vote me", description: "", tags: [] });
    const response = await voteApp(ideas)(vote(id, { sort: "https://evil.example" }));
    assertEquals(response.headers.get("location"), "/");
  }));

Deno.test("a vote for an unknown id is a 404 and writes nothing", () =>
  withStore(async (ideas, kv) => {
    await ideas.create({ title: "Existing", description: "", tags: [] });
    const keys = async () => (await Array.fromAsync(kv.list({ prefix: [] }))).map((entry) => entry.key);
    const before = await keys();
    const response = await voteApp(ideas)(vote("01NOTANID0000000000000000"));
    assertEquals(response.status, 404);
    await response.body?.cancel();
    assertEquals(await keys(), before);
  }));

Deno.test("each idea has a vote form that works without JavaScript", () =>
  withStore(async (ideas) => {
    const { id } = await ideas.create({ title: "Vote me", description: "", tags: [] });
    const html = await (await homeApp(ideas)(new Request("http://localhost/?sort=votes"))).text();
    assertStringIncludes(html, `<form method="post" action="/ideas/${id}/vote"`);
    assertStringIncludes(html, '<input type="hidden" name="sort" value="votes"');
  }));
