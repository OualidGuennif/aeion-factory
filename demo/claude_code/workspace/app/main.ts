import { App, staticFiles } from "fresh";
import type { State } from "./utils.ts";

export const app = new App<State>();

app.use(staticFiles());

// File-system routes: pages, and routes/api/[...path].ts which hands /api/* to Hono.
app.fsRoutes();
