// Spec: knowledge/components/idea-board-api.md
// The Idea type and the one validation every entry point (API and form) shares.

export interface Idea {
  id: string;
  title: string;
  description: string;
  tags: string[];
  votes: number;
  createdAt: string;
}

export interface NewIdea {
  title: string;
  description: string;
  tags: string[];
}

export type Validation<T> =
  | { ok: true; value: T }
  | { ok: false; field: string; reason: string };

export const TAG_PATTERN = /^[a-z0-9-]{1,20}$/;
const KNOWN_FIELDS = new Set(["title", "description", "tags"]);

const refuse = (field: string, reason: string) => ({
  ok: false as const,
  field,
  reason,
});

export function validateNewIdea(input: unknown): Validation<NewIdea> {
  if (typeof input !== "object" || input === null || Array.isArray(input)) {
    return refuse("body", "not_object");
  }
  const body = input as Record<string, unknown>;

  // Fields are checked in the documented order; the first failure is the one reported.
  const title = typeof body.title === "string" ? body.title.trim() : "";
  if (!title) return refuse("title", "required");
  if (title.length < 3) return refuse("title", "too_short");
  if (title.length > 80) return refuse("title", "too_long");

  if (body.description !== undefined && typeof body.description !== "string") {
    return refuse("description", "not_string");
  }
  const description = (body.description ?? "").trim();
  if (description.length > 500) return refuse("description", "too_long");

  if (body.tags !== undefined && !Array.isArray(body.tags)) {
    return refuse("tags", "not_array");
  }
  const tags: unknown[] = body.tags ?? [];
  if (tags.length > 5) return refuse("tags", "too_many");
  if (!tags.every((tag) => typeof tag === "string" && TAG_PATTERN.test(tag))) {
    return refuse("tags", "bad_tag");
  }
  if (new Set(tags).size !== tags.length) return refuse("tags", "duplicate");

  const unknown = Object.keys(body).find((key) => !KNOWN_FIELDS.has(key));
  if (unknown) return refuse(unknown, "unknown_field");

  return { ok: true, value: { title, description, tags: tags as string[] } };
}
