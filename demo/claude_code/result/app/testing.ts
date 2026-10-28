// Spec: knowledge/components/idea-board-api.md
// Test helpers: a fresh in-memory KV per test, always closed so Deno's resource sanitizer stays quiet,
// and the home route mounted alone on a given store.
import { App, type PageProps } from "fresh";
import type { VNode } from "preact";
import { createIdeaStore, type IdeaStore } from "./store/ideas.ts";
import { createHomeHandlers, HomePage } from "./pages/home.tsx";
import type { State } from "./utils.ts";

export async function withStore(
  run: (ideas: IdeaStore, kv: Deno.Kv) => Promise<void>,
) {
  const kv = await Deno.openKv(":memory:");
  try {
    await run(createIdeaStore(kv), kv);
  } finally {
    kv.close();
  }
}

// App.route types every page as PageProps<unknown>; fsRoutes accepts the typed page, so the helper casts.
export const homeApp = (ideas: IdeaStore) =>
  new App<State>().route("/", {
    handler: createHomeHandlers(() => Promise.resolve(ideas)),
    component: HomePage as (props: PageProps) => VNode,
  }).handler();
