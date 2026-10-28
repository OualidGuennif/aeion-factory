// Spec: knowledge/components/idea-board-page.md
// The HTML form's side of the domain: turn form fields into the API's shape, and reason codes into words.

export interface IdeaFormValues {
  title: string;
  description: string;
  tags: string[];
}

export interface FieldError {
  field: string;
  reason: string;
}

const text = (value: FormDataEntryValue | null) => typeof value === "string" ? value : "";

// Only reshapes the fields; validateNewIdea decides, so the form and the API refuse alike.
export function parseIdeaForm(data: FormData): IdeaFormValues {
  const tags = text(data.get("tags")).split(",").map((tag) => tag.trim().toLowerCase()).filter(Boolean);
  return { title: text(data.get("title")), description: text(data.get("description")), tags };
}

const messages: Record<string, string> = {
  required: "This field is required.",
  too_short: "Use at least 3 characters.",
  too_long: "This is too long.",
  not_string: "Use plain text.",
  not_array: "Give tags as a comma-separated list.",
  too_many: "Use at most 5 tags.",
  bad_tag: "Tags use a-z, 0-9 and dashes, 20 characters at most.",
  duplicate: "Each tag only once.",
  unknown_field: "This field is not expected.",
  not_object: "The form could not be read.",
  malformed_json: "The form could not be read.",
  too_large: "The idea is too large to send.",
  internal: "Something went wrong on the server. Try again.",
  network: "The server could not be reached. Try again.",
};

export const messageFor = (reason: string) => messages[reason] ?? `Unexpected error (${reason}).`;
