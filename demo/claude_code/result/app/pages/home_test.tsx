// Spec: knowledge/components/idea-board-page.md
import { assertEquals, assertStringIncludes } from "@std/assert";
import { homeApp, withStore } from "../testing.ts";

const post = (fields: Record<string, string>) =>
  new Request("http://localhost/", { method: "POST", body: new URLSearchParams(fields) });

Deno.test("an empty board says so", async () => {
  await withStore(async (ideas) => {
    const response = await homeApp(ideas)(new Request("http://localhost/"));
    const html = await response.text();
    assertEquals(response.status, 200);
    assertStringIncludes(html, "<h1>Idea Board</h1>");
    assertStringIncludes(html, "No ideas yet.");
  });
});

Deno.test("ideas are listed newest first with their votes and tags", async () => {
  await withStore(async (ideas) => {
    await ideas.create({ title: "Older idea", description: "", tags: [] });
    await ideas.create({ title: "Newer idea", description: "Some detail", tags: ["ux"] });
    const html = await (await homeApp(ideas)(new Request("http://localhost/"))).text();
    assertEquals(html.indexOf("Newer idea") < html.indexOf("Older idea"), true);
    assertStringIncludes(html, "Some detail");
    assertStringIncludes(html, "0 votes");
    assertStringIncludes(html, "#ux");
  });
});

Deno.test("the form posts to / without JavaScript", async () => {
  await withStore(async (ideas) => {
    const html = await (await homeApp(ideas)(new Request("http://localhost/"))).text();
    assertStringIncludes(html, '<form method="post" action="/"');
  });
});

Deno.test("a valid POST / stores the idea and redirects to /", async () => {
  await withStore(async (ideas) => {
    const response = await homeApp(ideas)(post({ title: "Offline mode", tags: "UX, sync" }));
    assertEquals(response.status, 303);
    assertEquals(response.headers.get("location"), "/");
    const [stored] = await ideas.list({ limit: 1 });
    assertEquals([stored.title, stored.tags], ["Offline mode", ["ux", "sync"]]);
  });
});

Deno.test("POST / refuses what the API refuses", async () => {
  await withStore(async (ideas) => {
    const response = await homeApp(ideas)(post({ title: "x", description: "kept text" }));
    const html = await response.text();
    assertEquals(response.status, 400);
    assertStringIncludes(html, "Use at least 3 characters.");
    assertStringIncludes(html, 'value="x"');
    assertStringIncludes(html, "kept text");
    assertEquals(await ideas.list({ limit: 1 }), []);
  });
});

Deno.test("an error is linked to its field", async () => {
  await withStore(async (ideas) => {
    const html = await (await homeApp(ideas)(post({ title: "x" }))).text();
    assertStringIncludes(html, 'aria-invalid="true"');
    assertStringIncludes(html, 'aria-describedby="title-error"');
    assertStringIncludes(html, 'id="title-error"');
    for (const field of ["title", "description", "tags"]) assertStringIncludes(html, `<label for="${field}"`);
  });
});

Deno.test("a script title is shown as text", async () => {
  await withStore(async (ideas) => {
    await ideas.create({ title: "<script>alert(1)</script>", description: "", tags: [] });
    const html = await (await homeApp(ideas)(new Request("http://localhost/"))).text();
    // Preact escapes "<" in text, which is enough to stop a tag; ">" may stay as is.
    assertStringIncludes(html, "&lt;script>alert(1)&lt;/script>");
    assertEquals(html.includes("<script>alert(1)"), false);
  });
});

Deno.test("no inline styles", async () => {
  await withStore(async (ideas) => {
    await ideas.create({ title: "Styled idea", description: "", tags: ["a"] });
    const html = await (await homeApp(ideas)(post({ title: "x" }))).text();
    assertEquals(html.includes("style="), false);
  });
});

Deno.test("sort by votes", async () => {
  await withStore(async (ideas) => {
    const loud = await ideas.create({ title: "Loud idea", description: "", tags: [] });
    await ideas.create({ title: "Quiet idea", description: "", tags: [] });
    await ideas.vote(loud.id);
    const html = await (await homeApp(ideas)(new Request("http://localhost/?sort=votes"))).text();
    assertEquals(html.indexOf("Loud idea") < html.indexOf("Quiet idea"), true);
    assertStringIncludes(html, '<a href="/?sort=votes" aria-current="page">Most voted</a>');
    assertStringIncludes(html, '<a href="/" aria-current="false">Newest</a>');
    assertEquals(html.match(/aria-current="(page|true)"/g)?.length, 1);
    assertStringIncludes(html, "1 vote<");
  });
});

Deno.test("filters combine and are kept", async () => {
  await withStore(async (ideas) => {
    await ideas.create({ title: "Dark mode", description: "", tags: ["ui"] });
    await ideas.create({ title: "Light theme", description: "", tags: ["ui"] });
    await ideas.create({ title: "Dark API", description: "", tags: ["api"] });
    const url = "http://localhost/?sort=votes&tag=ui&q=dark";
    const html = await (await homeApp(ideas)(new Request(url))).text();
    assertStringIncludes(html, "Dark mode");
    assertEquals(html.includes("Light theme"), false);
    assertEquals(html.includes("Dark API"), false);
    // Sort links keep the filters; the tag link keeps the sort and the search.
    assertStringIncludes(html, '<a href="/?tag=ui&amp;q=dark" aria-current="false">Newest</a>');
    assertStringIncludes(html, '<a href="/?sort=votes&amp;tag=ui&amp;q=dark" aria-current="page">Most voted</a>');
    assertStringIncludes(html, '<a href="/?sort=votes&amp;tag=ui&amp;q=dark" aria-current="false">#ui</a>');
    // The search form carries the sort and the tag; clearing keeps only the sort.
    assertStringIncludes(html, 'name="sort" value="votes"');
    assertStringIncludes(html, 'name="tag" value="ui"');
    assertStringIncludes(html, 'value="dark"');
    assertStringIncludes(html, '<a href="/?sort=votes" aria-current="false">Clear filters</a>');
    assertEquals(html.match(/aria-current="(page|true)"/g)?.length, 1);
  });
});

Deno.test("an invalid filter is dropped and no match says so", async () => {
  await withStore(async (ideas) => {
    await ideas.create({ title: "Dark mode", description: "", tags: ["ui"] });
    const html = await (await homeApp(ideas)(new Request("http://localhost/?tag=Bad!&q=nothing"))).text();
    assertEquals(html.includes('name="tag"'), false);
    assertStringIncludes(html, "No ideas match these filters.");
  });
});

Deno.test("a script search is shown as text", async () => {
  await withStore(async (ideas) => {
    const q = encodeURIComponent("<script>alert(1)</script>");
    const html = await (await homeApp(ideas)(new Request(`http://localhost/?q=${q}`))).text();
    assertEquals(html.includes("<script>alert(1)"), false);
    assertStringIncludes(html, "&lt;script>alert(1)&lt;/script>");
  });
});
