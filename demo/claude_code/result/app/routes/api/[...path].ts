// Spec: knowledge/components/idea-board-api.md
import { define } from "../../utils.ts";
import { createApi } from "../../api/app.ts";
import { getIdeas } from "../../store/shared.ts";

// Built on the first request, over the store the page uses too.
let api: Promise<ReturnType<typeof createApi>> | undefined;
const getApi = () => api ??= getIdeas().then((ideas) => createApi({ ideas }));

// Fresh hands every /api/* request to Hono unchanged; no API logic lives here.
export const handler = define.handlers(async (ctx) => (await getApi()).fetch(ctx.req));
