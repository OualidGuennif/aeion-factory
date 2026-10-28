// Spec: knowledge/components/idea-board-page.md
import { createVoteHandlers } from "../../../pages/vote.ts";
import { getIdeas } from "../../../store/shared.ts";

// The route only wires the vote form to the shared store; the logic lives in pages/vote.ts.
export const handler = createVoteHandlers(getIdeas);
