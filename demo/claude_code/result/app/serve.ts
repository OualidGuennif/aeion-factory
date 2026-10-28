// Spec: knowledge/components/idea-board-api.md
// `deno serve` ignores PORT, so production starts here: the port comes from the process, default 8000.
const port = Number(Deno.env.get("PORT") ?? "8000");
// The build output exists only after `deno task build`; a computed specifier keeps type checking independent of it.
const entry = new URL("./_fresh/server.js", import.meta.url).href;
const server: { default: { fetch: Deno.ServeHandler } } = await import(entry);
Deno.serve({ port }, server.default.fetch);
