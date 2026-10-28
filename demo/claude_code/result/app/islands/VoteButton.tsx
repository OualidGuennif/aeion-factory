// Spec: knowledge/components/idea-board-page.md
// Enhances one idea's vote form: with JavaScript it posts to the API and updates the count in place;
// without it, the same form posts to /ideas/:id/vote and the server redirects back.
import { useState } from "preact/hooks";
import type { TargetedSubmitEvent } from "preact";
import type { Sort } from "../store/ideas.ts";

interface VoteButtonProps {
  id: string;
  title: string;
  votes: number;
  sort: Sort;
}

const label = (votes: number) => `${votes} ${votes === 1 ? "vote" : "votes"}`;

export default function VoteButton({ id, title, votes, sort }: VoteButtonProps) {
  const [count, setCount] = useState(votes);
  const [sending, setSending] = useState(false);
  const [failed, setFailed] = useState(false);

  async function submit(event: TargetedSubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setSending(true);
    try {
      const response = await fetch(`/api/ideas/${id}/vote`, { method: "POST" });
      // The server's count wins: other people may have voted since the page was rendered.
      if (response.ok) setCount((await response.json()).idea.votes);
      setFailed(!response.ok);
    } catch {
      setFailed(true);
    } finally {
      setSending(false);
    }
  }

  return (
    <form method="post" action={`/ideas/${id}/vote`} class="vote" onSubmit={submit}>
      <input type="hidden" name="sort" value={sort} />
      <span class="votes" aria-live="polite">{label(count)}</span>
      <button type="submit" class="vote-button" disabled={sending}>
        Vote<span class="sr-only">{` for ${title}`}</span>
      </button>
      {failed && <span class="vote-error" role="status">Vote not saved. Try again.</span>}
    </form>
  );
}
