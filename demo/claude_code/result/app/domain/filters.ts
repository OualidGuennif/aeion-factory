// Spec: knowledge/components/idea-board-api.md
// The list filters, parsed once for the API (which refuses) and the page (which drops what it refuses).
import { TAG_PATTERN, type Validation } from "./idea.ts";

export interface Filters {
  tag?: string;
  q?: string;
}

const Q_MAX = 50;

export function parseFilters(params: URLSearchParams): Validation<Filters> {
  const filters: Filters = {};
  const tag = params.get("tag");
  if (tag !== null) {
    if (!TAG_PATTERN.test(tag)) return { ok: false, field: "tag", reason: "bad_tag" };
    filters.tag = tag;
  }
  // A blank search box reads as no search, so an empty submit does not filter everything out.
  const q = params.get("q")?.trim();
  if (q) {
    if (q.length > Q_MAX) return { ok: false, field: "q", reason: "too_long" };
    filters.q = q;
  }
  return { ok: true, value: filters };
}
