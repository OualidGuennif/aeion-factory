// Spec: knowledge/components/idea-board-api.md
import { assertEquals, assertStringIncludes } from "@std/assert";
import { createApi } from "./app.ts";
import { VERSION } from "../version.ts";

const api = createApi();

Deno.test("health answers ok with the app version", async () => {
  const response = await api.request("/api/health");
  assertEquals(response.status, 200);
  assertStringIncludes(
    response.headers.get("content-type") ?? "",
    "application/json",
  );
  assertEquals(await response.json(), { status: "ok", version: VERSION });
});

Deno.test("unknown route is a JSON 404", async () => {
  const response = await api.request("/api/nope");
  assertEquals(response.status, 404);
  assertStringIncludes(
    response.headers.get("content-type") ?? "",
    "application/json",
  );
  assertEquals(await response.json(), { error: "not_found" });
});

Deno.test("wrong method is a JSON 405", async () => {
  const response = await api.request("/api/health", { method: "POST" });
  assertEquals(response.status, 405);
  assertEquals(await response.json(), { error: "method_not_allowed" });
});

Deno.test("an exception is a bare JSON 500", async () => {
  const failing = createApi();
  failing.get("/boom", () => {
    throw new Error("secret detail");
  });
  const response = await failing.request("/api/boom");
  assertEquals(response.status, 500);
  assertEquals(await response.json(), { error: "internal" });
});

Deno.test("the API module does not import Fresh", async () => {
  const source = await Deno.readTextFile(new URL("./app.ts", import.meta.url));
  assertEquals(/from\s+["']fresh/.test(source), false);
});
