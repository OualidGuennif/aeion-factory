// Spec: knowledge/components/idea-board-page.md
// The home page: its handlers take the store as a parameter, so tests run them on an in-memory KV.
import { page, type PageProps } from "fresh";
import { define } from "../utils.ts";
import { type Idea, validateNewIdea } from "../domain/idea.ts";
import { type FieldError, type IdeaFormValues, parseIdeaForm } from "../domain/form.ts";
import { type Filters, parseFilters } from "../domain/filters.ts";
import type { IdeaStore, Sort } from "../store/ideas.ts";
import NewIdeaForm from "../islands/NewIdeaForm.tsx";
import VoteButton from "../islands/VoteButton.tsx";

export interface HomeData {
  ideas: Idea[];
  sort: Sort;
  filters: Filters;
  values: IdeaFormValues;
  error?: FieldError;
}

const LIST_LIMIT = 20;
const EMPTY: IdeaFormValues = { title: "", description: "", tags: [] };

// The page is lenient: an unknown sort reads as the default, where the API refuses it.
const readSort = (url: URL): Sort => url.searchParams.get("sort") === "votes" ? "votes" : "recent";

// Each filter is parsed alone, so an invalid one is dropped and the other still applies.
function readFilters(url: URL): Filters {
  const only = (name: "tag" | "q"): Filters => {
    const value = url.searchParams.get(name);
    const parsed = parseFilters(new URLSearchParams(value === null ? {} : { [name]: value }));
    return parsed.ok ? parsed.value : {};
  };
  return { ...only("tag"), ...only("q") };
}

// Every link to the board goes through here, so sort and filters are always kept together.
function boardHref(sort: Sort, { tag, q }: Filters): string {
  const params = new URLSearchParams();
  if (sort === "votes") params.set("sort", "votes");
  if (tag) params.set("tag", tag);
  if (q) params.set("q", q);
  const query = params.toString();
  return query ? `/?${query}` : "/";
}

export function createHomeHandlers(getIdeas: () => Promise<IdeaStore>) {
  return define.handlers<HomeData>({
    async GET(ctx) {
      const ideas = await getIdeas();
      const sort = readSort(ctx.url);
      const filters = readFilters(ctx.url);
      const listed = await ideas.list({ limit: LIST_LIMIT, sort, ...filters });
      return page({ ideas: listed, sort, filters, values: EMPTY });
    },
    async POST(ctx) {
      const ideas = await getIdeas();
      // A body that is not a form reads as an empty one, so validation names the missing title.
      const form = await ctx.req.formData().catch(() => new FormData());
      const values = parseIdeaForm(form);
      const draft = validateNewIdea(values);
      if (!draft.ok) {
        const error = { field: draft.field, reason: draft.reason };
        const listed = await ideas.list({ limit: LIST_LIMIT });
        return page({ ideas: listed, sort: "recent", filters: {}, values, error }, { status: 400 });
      }
      await ideas.create(draft.value);
      // Post/redirect/get: a reload after adding does not post the idea twice.
      return new Response(null, { status: 303, headers: { location: "/" } });
    },
  });
}

function IdeaItem({ idea, sort, filters }: { idea: Idea; sort: Sort; filters: Filters }) {
  return (
    <li class="idea">
      <h3 class="idea-title">{idea.title}</h3>
      {idea.description && <p class="idea-description">{idea.description}</p>}
      {idea.tags.length > 0 && (
        <ul class="tags" aria-label="Tags">
          {idea.tags.map((tag) => (
            <li key={tag} class="tag">
              <a href={boardHref(sort, { ...filters, tag })} aria-current="false">{`#${tag}`}</a>
            </li>
          ))}
        </ul>
      )}
      <p class="idea-meta">
        <time dateTime={idea.createdAt}>{idea.createdAt.slice(0, 10)}</time>
      </p>
      <VoteButton id={idea.id} title={idea.title} votes={idea.votes} sort={sort} />
    </li>
  );
}

function SearchForm({ sort, filters }: { sort: Sort; filters: Filters }) {
  return (
    <form class="search" method="get" action="/" role="search">
      <label for="q">Search ideas</label>
      <div class="search-row">
        <input id="q" name="q" type="search" maxLength={50} value={filters.q ?? ""} />
        {sort === "votes" && <input type="hidden" name="sort" value="votes" />}
        {filters.tag && <input type="hidden" name="tag" value={filters.tag} />}
        <button type="submit">Search</button>
      </div>
    </form>
  );
}

function ActiveFilters({ sort, filters }: { sort: Sort; filters: Filters }) {
  return (
    <p class="active-filters">
      <span>
        Showing ideas
        {filters.tag && (
          <>
            {" tagged "}
            <strong>{`#${filters.tag}`}</strong>
          </>
        )}
        {filters.q && (
          <>
            {" matching "}
            <strong>{`“${filters.q}”`}</strong>
          </>
        )}
      </span>
      <a href={boardHref(sort, {})} aria-current="false">Clear filters</a>
    </p>
  );
}

export function HomePage({ data }: PageProps<HomeData>) {
  const { sort, filters } = data;
  const filtering = Boolean(filters.tag || filters.q);
  return (
    <main class="board">
      <header class="board-header">
        <h1>Idea Board</h1>
        <p class="lede">Propose an idea. The newest come first.</p>
      </header>
      <section class="panel" aria-labelledby="new-idea">
        <h2 id="new-idea">New idea</h2>
        <NewIdeaForm values={data.values} error={data.error} />
      </section>
      <section aria-labelledby="ideas-heading">
        <div class="list-header">
          <h2 id="ideas-heading">Ideas</h2>
          <nav class="sort" aria-label="Sort ideas">
            {/* aria-current is always explicit: left undefined, Fresh marks any link to "/" as current or ancestor. */}
            <a href={boardHref("recent", filters)} aria-current={sort === "recent" ? "page" : "false"}>Newest</a>
            <a href={boardHref("votes", filters)} aria-current={sort === "votes" ? "page" : "false"}>Most voted</a>
          </nav>
        </div>
        <SearchForm sort={sort} filters={filters} />
        {filtering && <ActiveFilters sort={sort} filters={filters} />}
        {data.ideas.length === 0
          ? <p class="empty">{filtering ? "No ideas match these filters." : "No ideas yet."}</p>
          : (
            <ul class="ideas">
              {data.ideas.map((idea) => <IdeaItem key={idea.id} idea={idea} sort={sort} filters={filters} />)}
            </ul>
          )}
      </section>
    </main>
  );
}
