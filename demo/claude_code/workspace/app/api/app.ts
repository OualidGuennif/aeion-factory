// Spec: knowledge/components/idea-board-api.md
import { Hono } from "@hono/hono";
import { VERSION } from "../version.ts";

export function createApi() {
  const api = new Hono().basePath("/api");

  // Health is GET-only; other methods get an explicit JSON 405 rather than Hono's default 404.
  api.get("/health", (c) => c.json({ status: "ok", version: VERSION }));
  api.all("/health", (c) => c.json({ error: "method_not_allowed" }, 405));

  // Errors stay JSON and never leak the exception message.
  api.notFound((c) => c.json({ error: "not_found" }, 404));
  api.onError((error, c) => {
    console.error(error);
    return c.json({ error: "internal" }, 500);
  });
  return api;
}
