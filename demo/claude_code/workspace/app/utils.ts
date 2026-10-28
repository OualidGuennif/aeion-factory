import { createDefine } from "fresh";

// The type of ctx.state shared by middlewares, layouts and routes.
// deno-lint-ignore no-empty-interface
export interface State {}

export const define = createDefine<State>();
