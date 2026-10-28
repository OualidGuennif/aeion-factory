// Spec: knowledge/components/idea-board-api.md
import { dirname } from "@std/path";

// The KV file comes from KV_PATH; its folder is created on first use, never at build time.
export async function openKv(): Promise<Deno.Kv> {
  const path = Deno.env.get("KV_PATH") ?? "./data/ideas.sqlite3";
  if (path !== ":memory:") await Deno.mkdir(dirname(path), { recursive: true });
  return await Deno.openKv(path);
}
