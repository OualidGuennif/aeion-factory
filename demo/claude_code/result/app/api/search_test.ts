// Spec: knowledge/components/idea-board-api.md
import { assertEquals } from "@std/assert";
import { createApi } from "./app.ts";
import { withStore } from "../testing.ts";

Deno.test("a bad tag is a 400 naming the field", () =>
  withStore(async (ideas) => {
    const response = await createApi({ ideas }).request("/api/ideas?tag=Bad_Tag");
    assertEquals([response.status, await response.json()], [400, {
      error: "invalid",
      field: "tag",
      reason: "bad_tag",
    }]);
  }));

Deno.test("a q over 50 characters is a 400 naming the field", () =>
  withStore(async (ideas) => {
    const response = await createApi({ ideas }).request(`/api/ideas?q=${"x".repeat(51)}`);
    assertEquals([response.status, await response.json()], [400, { error: "invalid", field: "q", reason: "too_long" }]);
  }));

Deno.test("tag and q filter the list and keep its shape", () =>
  withStore(async (ideas) => {
    await ideas.create({ title: "Dark mode", description: "", tags: ["ui"] });
    await ideas.create({ title: "Dark terminal", description: "", tags: ["cli"] });
    const body = await (await createApi({ ideas }).request("/api/ideas?tag=ui&q=DARK")).json();
    assertEquals([body.count, body.ideas[0].title], [1, "Dark mode"]);
  }));
