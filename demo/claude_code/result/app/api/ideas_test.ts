// Spec: knowledge/components/idea-board-api.md
import { assertEquals } from "@std/assert";
import { createApi } from "./app.ts";
import { withStore } from "../testing.ts";

const json = (body: unknown) => ({
  method: "POST",
  headers: { "content-type": "application/json" },
  body: typeof body === "string" ? body : JSON.stringify(body),
});

Deno.test("POST /api/ideas creates an idea", () =>
  withStore(async (ideas) => {
    const api = createApi({ ideas });
    const response = await api.request(
      "/api/ideas",
      json({ title: "Dark mode", tags: ["ui"] }),
    );
    assertEquals(response.status, 201);
    const { idea } = await response.json();
    assertEquals([idea.title, idea.description, idea.tags, idea.votes], [
      "Dark mode",
      "",
      ["ui"],
      0,
    ]);
    assertEquals(await ideas.get(idea.id), idea);
  }));

Deno.test("an invalid idea is a 400 naming the field", () =>
  withStore(async (ideas) => {
    const response = await createApi({ ideas }).request(
      "/api/ideas",
      json({ title: "x" }),
    );
    assertEquals(response.status, 400);
    assertEquals(await response.json(), {
      error: "invalid",
      field: "title",
      reason: "too_short",
    });
  }));

Deno.test("invalid writes nothing", () =>
  withStore(async (ideas, kv) => {
    const api = createApi({ ideas });
    await api.request("/api/ideas", json({ title: "x" }));
    await api.request("/api/ideas", json({ title: "Fine", votes: 3 }));
    await api.request("/api/ideas", json("{not json"));
    assertEquals((await Array.fromAsync(kv.list({ prefix: [] }))).length, 0);
  }));

Deno.test("malformed JSON is a 400 on the body", () =>
  withStore(async (ideas) => {
    const response = await createApi({ ideas }).request(
      "/api/ideas",
      json("{not json"),
    );
    assertEquals(await response.json(), {
      error: "invalid",
      field: "body",
      reason: "malformed_json",
    });
  }));

Deno.test("a non-JSON content type is a 415", () =>
  withStore(async (ideas) => {
    const response = await createApi({ ideas }).request("/api/ideas", {
      method: "POST",
      headers: { "content-type": "text/plain" },
      body: "title=x",
    });
    assertEquals(response.status, 415);
    assertEquals(await response.json(), { error: "unsupported_media_type" });
  }));

Deno.test("a body over 8 KiB is a 413", () =>
  withStore(async (ideas) => {
    const response = await createApi({ ideas }).request(
      "/api/ideas",
      json({ title: "abc", description: "d".repeat(9000) }),
    );
    assertEquals(response.status, 413);
    assertEquals(await response.json(), { error: "too_large" });
  }));

Deno.test("GET /api/ideas lists newest first with a count", () =>
  withStore(async (ideas) => {
    const api = createApi({ ideas });
    for (const title of ["first", "second", "third"]) {
      await api.request("/api/ideas", json({ title }));
    }
    const body = await (await api.request("/api/ideas?limit=2")).json();
    assertEquals(body.count, 2);
    assertEquals(body.ideas.map((idea: { title: string }) => idea.title), [
      "third",
      "second",
    ]);
  }));

Deno.test("a limit outside 1-50 is refused", () =>
  withStore(async (ideas) => {
    const api = createApi({ ideas });
    for (const limit of ["0", "51", "x", "1.5", ""]) {
      const response = await api.request(`/api/ideas?limit=${limit}`);
      assertEquals(response.status, 400, `limit=${limit}`);
      assertEquals(await response.json(), {
        error: "invalid",
        field: "limit",
        reason: "out_of_range",
      });
    }
    assertEquals((await api.request("/api/ideas?limit=50")).status, 200);
  }));

Deno.test("GET /api/ideas/:id returns the idea or a 404", () =>
  withStore(async (ideas) => {
    const api = createApi({ ideas });
    const created = await ideas.create({
      title: "Find me",
      description: "",
      tags: [],
    });
    assertEquals(await (await api.request(`/api/ideas/${created.id}`)).json(), {
      idea: created,
    });
    const missing = await api.request("/api/ideas/01ARZ3NDEKTSV4RRFFQ69G5FAV");
    assertEquals(missing.status, 404);
    assertEquals(await missing.json(), { error: "not_found" });
  }));
