// Spec: knowledge/components/idea-board-api.md
// Test helper: a fresh in-memory KV per test, always closed so Deno's resource sanitizer stays quiet.
import { createIdeaStore, type IdeaStore } from "./store/ideas.ts";

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
