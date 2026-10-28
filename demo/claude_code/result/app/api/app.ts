// Spec: knowledge/components/idea-board-api.md
import { Hono } from "@hono/hono";
import { bodyLimit } from "@hono/hono/body-limit";
import { parseFilters } from "../domain/filters.ts";
import { validateNewIdea } from "../domain/idea.ts";
import type { IdeaStore, Sort } from "../store/ideas.ts";
import { VERSION } from "../version.ts";

export interface ApiDeps {
  ideas: IdeaStore;
}

const MAX_BODY_BYTES = 8 * 1024;

export function createApi({ ideas }: ApiDeps) {
  const api = new Hono().basePath("/api");

  // Health is GET-only; other methods get an explicit JSON 405 rather than Hono's default 404.
  api.get("/health", (c) => c.json({ status: "ok", version: VERSION }));
  api.all("/health", (c) => c.json({ error: "method_not_allowed" }, 405));

  api.post(
    "/ideas",
    bodyLimit({
      maxSize: MAX_BODY_BYTES,
      onError: (c) => c.json({ error: "too_large" }, 413),
    }),
    async (c) => {
      if (
        !(c.req.header("content-type") ?? "").startsWith("application/json")
      ) {
        return c.json({ error: "unsupported_media_type" }, 415);
      }
      let body: unknown;
      try {
        body = await c.req.json();
      } catch {
        return c.json({
          error: "invalid",
          field: "body",
          reason: "malformed_json",
        }, 400);
      }
      const draft = validateNewIdea(body);
      if (!draft.ok) {
        return c.json({
          error: "invalid",
          field: draft.field,
          reason: draft.reason,
        }, 400);
      }
      return c.json({ idea: await ideas.create(draft.value) }, 201);
    },
  );

  api.get("/ideas", async (c) => {
    const limit = parseLimit(c.req.query("limit"));
    if (limit === null) {
      return c.json({
        error: "invalid",
        field: "limit",
        reason: "out_of_range",
      }, 400);
    }
    const sort = parseSort(c.req.query("sort"));
    if (sort === null) {
      return c.json({ error: "invalid", field: "sort", reason: "out_of_range" }, 400);
    }
    const filters = parseFilters(new URL(c.req.url).searchParams);
    if (!filters.ok) {
      return c.json({ error: "invalid", field: filters.field, reason: filters.reason }, 400);
    }
    const listed = await ideas.list({ limit, sort, ...filters.value });
    return c.json({ ideas: listed, count: listed.length });
  });

  api.post("/ideas/:id/vote", async (c) => {
    const result = await ideas.vote(c.req.param("id"));
    if (result.status === "not_found") return c.json({ error: "not_found" }, 404);
    if (result.status === "busy") return c.json({ error: "busy" }, 503);
    return c.json({ idea: result.idea });
  });

  api.get("/ideas/:id", async (c) => {
    const idea = await ideas.get(c.req.param("id"));
    return idea ? c.json({ idea }) : c.json({ error: "not_found" }, 404);
  });

  // Errors stay JSON and never leak the exception message.
  api.notFound((c) => c.json({ error: "not_found" }, 404));
  api.onError((error, c) => {
    console.error(error);
    return c.json({ error: "internal" }, 500);
  });
  return api;
}

// An integer from 1 to 50, default 20; anything else is refused rather than clamped.
function parseLimit(raw: string | undefined): number | null {
  if (raw === undefined) return 20;
  if (!/^\d+$/.test(raw)) return null;
  const limit = Number(raw);
  return limit >= 1 && limit <= 50 ? limit : null;
}

function parseSort(raw: string | undefined): Sort | null {
  if (raw === undefined) return "recent";
  return raw === "recent" || raw === "votes" ? raw : null;
}
