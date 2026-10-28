// Spec: knowledge/components/idea-board-page.md
// The vote form's server side, for browsers without JavaScript; the island calls the API instead.
import { define } from "../utils.ts";
import type { IdeaStore } from "../store/ideas.ts";

export function createVoteHandlers(getIdeas: () => Promise<IdeaStore>) {
  return define.handlers({
    async POST(ctx) {
      const ideas = await getIdeas();
      const form = await ctx.req.formData().catch(() => new FormData());
      const result = await ideas.vote(ctx.params.id);
      if (result.status === "not_found") return new Response("Idea not found.", { status: 404 });
      if (result.status === "busy") return new Response("Too many votes at once. Try again.", { status: 503 });
      // Only a known sort goes into the redirect, so the form cannot send the browser elsewhere.
      const location = form.get("sort") === "votes" ? "/?sort=votes" : "/";
      return new Response(null, { status: 303, headers: { location } });
    },
  });
}
