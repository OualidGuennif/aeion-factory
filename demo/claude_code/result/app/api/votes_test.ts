// Spec: knowledge/components/idea-board-api.md
import { assertEquals } from "@std/assert";
import { createApi } from "./app.ts";
import { withStore } from "../testing.ts";

Deno.test("POST /api/ideas/:id/vote returns the idea with one more vote", () =>
  withStore(async (ideas) => {
    const { id } = await ideas.create({ title: "Vote me", description: "", tags: [] });
    const response = await createApi({ ideas }).request(`/api/ideas/${id}/vote`, { method: "POST" });
    assertEquals(response.status, 200);
    assertEquals((await response.json()).idea.votes, 1);
  }));

Deno.test("a vote for an unknown id is a JSON 404", () =>
  withStore(async (ideas) => {
    const response = await createApi({ ideas }).request("/api/ideas/01NOTANID0000000000000000/vote", {
      method: "POST",
    });
    assertEquals([response.status, await response.json()], [404, { error: "not_found" }]);
  }));

Deno.test("a vote still conflicting after its retries is a 503 busy", () =>
  withStore(async (ideas) => {
    const busy = { ...ideas, vote: () => Promise.resolve({ status: "busy" as const }) };
    const response = await createApi({ ideas: busy }).request("/api/ideas/any/vote", { method: "POST" });
    assertEquals([response.status, await response.json()], [503, { error: "busy" }]);
  }));

Deno.test("GET /api/ideas?sort=votes lists most votes first", () =>
  withStore(async (ideas) => {
    await ideas.create({ title: "Quiet", description: "", tags: [] });
    const loud = await ideas.create({ title: "Loud", description: "", tags: [] });
    await ideas.vote(loud.id);
    const quiet = await ideas.create({ title: "Newest", description: "", tags: [] });
    const body = await (await createApi({ ideas }).request("/api/ideas?sort=votes")).json();
    assertEquals(body.ideas.map((idea: { title: string }) => idea.title), ["Loud", "Newest", "Quiet"]);
    assertEquals(quiet.votes, 0);
  }));

Deno.test("an unknown sort is a 400 naming the field", () =>
  withStore(async (ideas) => {
    const response = await createApi({ ideas }).request("/api/ideas?sort=popular");
    assertEquals([response.status, await response.json()], [400, {
      error: "invalid",
      field: "sort",
      reason: "out_of_range",
    }]);
  }));
