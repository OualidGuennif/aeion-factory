// Spec: knowledge/components/idea-board-page.md
// The one store the page and the API share; KV opens on the first request, not when the build imports it.
import { createIdeaStore, type IdeaStore } from "./ideas.ts";
import { openKv } from "./kv.ts";

let store: Promise<IdeaStore> | undefined;

export const getIdeas = () => store ??= openKv().then(createIdeaStore);
