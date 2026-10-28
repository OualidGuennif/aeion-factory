// Spec: knowledge/components/idea-board-api.md
import { define } from "../../utils.ts";
import { createApi } from "../../api/app.ts";
import { createIdeaStore } from "../../store/ideas.ts";
import { openKv } from "../../store/kv.ts";

// KV opens on the first request, not when the build imports this module.
let api: Promise<ReturnType<typeof createApi>> | undefined;
const getApi = () => api ??= openKv().then((kv) => createApi({ ideas: createIdeaStore(kv) }));

// Fresh hands every /api/* request to Hono unchanged; no API logic lives here.
export const handler = define.handlers(async (ctx) => (await getApi()).fetch(ctx.req));
