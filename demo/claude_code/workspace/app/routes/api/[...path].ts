// Spec: knowledge/components/idea-board-api.md
import { define } from "../../utils.ts";
import { createApi } from "../../api/app.ts";

const api = createApi();

// Fresh hands every /api/* request to Hono unchanged; no API logic lives here.
export const handler = define.handlers((ctx) => api.fetch(ctx.req));
