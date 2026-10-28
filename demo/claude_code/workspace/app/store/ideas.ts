// Spec: knowledge/components/idea-board-api.md
import { monotonicUlid } from "@std/ulid";
import type { Idea, NewIdea } from "../domain/idea.ts";

export type IdeaStore = ReturnType<typeof createIdeaStore>;

const ideaKey = (id: string) => ["ideas", id];

export function createIdeaStore(kv: Deno.Kv) {
  return {
    async create(draft: NewIdea): Promise<Idea> {
      // Monotonic ULIDs keep key order equal to creation order within one millisecond.
      const idea: Idea = {
        id: monotonicUlid(),
        ...draft,
        votes: 0,
        createdAt: new Date().toISOString(),
      };
      const result = await kv.atomic().check({
        key: ideaKey(idea.id),
        versionstamp: null,
      }).set(ideaKey(idea.id), idea)
        .commit();
      if (!result.ok) throw new Error("idea id collision");
      return idea;
    },

    async get(id: string): Promise<Idea | null> {
      return (await kv.get<Idea>(ideaKey(id))).value;
    },

    async list({ limit }: { limit: number }): Promise<Idea[]> {
      const entries = kv.list<Idea>({ prefix: ["ideas"] }, {
        reverse: true,
        limit,
      });
      return (await Array.fromAsync(entries)).map((entry) => entry.value);
    },
  };
}
