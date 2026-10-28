// Spec: knowledge/components/idea-board-page.md
import { createHomeHandlers, HomePage } from "../pages/home.tsx";
import { getIdeas } from "../store/shared.ts";

// The route only wires the page to the shared store; the logic lives in pages/home.tsx.
export const handler = createHomeHandlers(getIdeas);

export default HomePage;
