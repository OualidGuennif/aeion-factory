import { App, csrf, staticFiles } from "fresh";
import type { State } from "./utils.ts";

export const app = new App<State>();

app.use(staticFiles());

// The home form posts to /: a cross-site Origin or Sec-Fetch-Site is refused with 403.
app.use(csrf());

// File-system routes: pages, and routes/api/[...path].ts which hands /api/* to Hono.
app.fsRoutes();
