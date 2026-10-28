// Spec: knowledge/components/idea-board-api.md
import { monotonicUlid } from "@std/ulid";
import type { Idea, NewIdea } from "../domain/idea.ts";

export type IdeaStore = ReturnType<typeof createIdeaStore>;
export type Sort = "recent" | "votes";
export type VoteResult = { status: "ok"; idea: Idea } | { status: "not_found" } | { status: "busy" };

export interface ListOptions {
  limit: number;
  sort?: Sort;
  tag?: string;
  q?: string;
}

const ideaKey = (id: string) => ["ideas", id];
const votesKey = (idea: Idea) => ["ideas_by_votes", idea.votes, idea.id];

const VOTE_ATTEMPTS = 10;
const GET_MANY_MAX = 10;
const SEARCH_BOUND = 500;

// Contenders that lost a commit wait a random, growing delay, so they stop colliding on the next attempt.
const backoff = (attempt: number) => new Promise((done) => setTimeout(done, Math.random() * 2 ** attempt));

export function createIdeaStore(kv: Deno.Kv) {
  // An index entry's value is an idea id; getMany reads at most 10 keys per call.
  async function readIndex(prefix: Deno.KvKey, limit: number): Promise<Idea[]> {
    const ids = (await Array.fromAsync(kv.list<string>({ prefix }, { reverse: true, limit })))
      .map((entry) => entry.value);
    const ideas: Idea[] = [];
    for (let start = 0; start < ids.length; start += GET_MANY_MAX) {
      const batch = await kv.getMany<Idea[]>(ids.slice(start, start + GET_MANY_MAX).map(ideaKey));
      ideas.push(...batch.flatMap((entry) => entry.value ? [entry.value] : []));
    }
    return ideas;
  }

  async function newest(limit: number): Promise<Idea[]> {
    return (await Array.fromAsync(kv.list<Idea>({ prefix: ["ideas"] }, { reverse: true, limit })))
      .map((entry) => entry.value);
  }

  // Filtering reads at most the 500 newest candidates (with the tag, when there is one), then sorts those.
  async function filtered({ limit, sort, tag, q }: ListOptions & { sort: Sort }): Promise<Idea[]> {
    const candidates = tag ? await readIndex(["ideas_by_tag", tag], SEARCH_BOUND) : await newest(SEARCH_BOUND);
    // includes(), never a RegExp: a "q" of ".*" matches only those two characters.
    const needle = q?.toLowerCase();
    const matches = needle
      ? candidates.filter((idea) => `${idea.title}\n${idea.description}`.toLowerCase().includes(needle))
      : candidates;
    // Candidates come newest first and sort() is stable, so vote ties stay newest first.
    if (sort === "votes") matches.sort((a, b) => b.votes - a.votes);
    return matches.slice(0, limit);
  }

  return {
    async create(draft: NewIdea): Promise<Idea> {
      // Monotonic ULIDs keep key order equal to creation order within one millisecond.
      const idea: Idea = { id: monotonicUlid(), ...draft, votes: 0, createdAt: new Date().toISOString() };
      // The idea and every index key land in one commit, or none of them does.
      const operation = kv.atomic()
        .check({ key: ideaKey(idea.id), versionstamp: null })
        .set(ideaKey(idea.id), idea)
        .set(votesKey(idea), idea.id);
      for (const tag of idea.tags) operation.set(["ideas_by_tag", tag, idea.id], idea.id);
      const result = await operation.commit();
      if (!result.ok) throw new Error("idea id collision");
      return idea;
    },

    async get(id: string): Promise<Idea | null> {
      return (await kv.get<Idea>(ideaKey(id))).value;
    },

    list({ limit, sort = "recent", tag, q }: ListOptions): Promise<Idea[]> {
      if (tag || q) return filtered({ limit, sort, tag, q });
      // The votes index sorts by votes, then by id; reversed, ties come newest first.
      if (sort === "votes") return readIndex(["ideas_by_votes"], limit);
      return newest(limit);
    },

    async vote(id: string): Promise<VoteResult> {
      for (let attempt = 0; attempt < VOTE_ATTEMPTS; attempt++) {
        const entry = await kv.get<Idea>(ideaKey(id));
        if (entry.value === null) return { status: "not_found" };
        // The idea and its index key move together, only if nobody voted since the read.
        const idea = { ...entry.value, votes: entry.value.votes + 1 };
        const result = await kv.atomic()
          .check(entry)
          .set(ideaKey(id), idea)
          .delete(votesKey(entry.value))
          .set(votesKey(idea), id)
          .commit();
        if (result.ok) return { status: "ok", idea };
        await backoff(attempt);
      }
      return { status: "busy" };
    },
  };
}
